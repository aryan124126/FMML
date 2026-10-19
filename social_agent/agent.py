"""Social media assistant: a command-line chat agent powered by Claude.

Run with:  python -m social_agent.agent
"""

from datetime import date

import anthropic

from .tools import PLATFORM_LIMITS, TOOL_DEFINITIONS, run_tool

MODEL = "claude-opus-5-5"
MAX_TOOL_ROUNDS = 20  # safety cap on tool calls per user message

SYSTEM_PROMPT = f"""You are a social media assistant. You help the user write, improve and \
plan posts for these platforms: {", ".join(sorted(PLATFORM_LIMITS))}.

How to work:
- Write in the user's voice. If you don't know their brand, audience or tone yet, ask briefly.
- Fit each post to its platform: length, tone, hashtag habits, and formatting \
(e.g. short and punchy for X, more professional for LinkedIn).
- Before presenting a final post, call check_post_length and fix anything over the limit.
- Use web search when the user asks about trends, news, or facts you're not sure about, \
and mention your sources.
- Only save or delete drafts when the user asks. You cannot publish posts; the user \
copies them to the platform.
- Keep replies short. Show the post text clearly so it is easy to copy."""

TOOLS = [
    *TOOL_DEFINITIONS,
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
]


class SocialAgent:
    def __init__(self, client: anthropic.Anthropic | None = None):
        self.client = client or anthropic.Anthropic()
        self.messages: list[dict] = []  # the whole conversation; only ever appended to

    def _call_model(self):
        return self.client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=self.messages,
            output_config={"effort": "medium"},
            cache_control={"type": "ephemeral"},  # reuse the cached conversation each turn
            # If Claude declines a request, retry on Anthropic's recommended fallback model.
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )

    def send(self, user_text: str) -> str:
        """Send one user message, run any tools Claude asks for, and return its reply.

        If anything goes wrong, this turn is removed from the history so the chat can go on.
        """
        start = len(self.messages)
        try:
            return self._run_turn(user_text, start)
        except BaseException:
            del self.messages[start:]
            raise

    def _run_turn(self, user_text: str, start: int) -> str:
        # Today's date goes in the message (not the system prompt) so caching keeps working.
        self.messages.append(
            {"role": "user", "content": f"[Today is {date.today().isoformat()}]\n{user_text}"}
        )

        for _ in range(MAX_TOOL_ROUNDS):
            response = self._call_model()

            if response.stop_reason == "refusal":
                del self.messages[start:]
                return "Sorry, I can't help with that request."

            self.messages.append({"role": "assistant", "content": response.content})

            if response.stop_reason == "pause_turn":
                continue  # a long web search paused; re-send to let it finish

            if response.stop_reason == "max_tokens":
                return _text_of(response) + "\n[Reply was cut off. Ask me to continue.]"

            if response.stop_reason != "tool_use":
                return _text_of(response)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result, is_error = run_tool(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                            "is_error": is_error,
                        }
                    )
            self.messages.append({"role": "user", "content": tool_results})

        del self.messages[start:]
        return "[Stopped: too many tool calls in one turn. Try a simpler request.]"


def _text_of(response) -> str:
    return "\n".join(b.text for b in response.content if b.type == "text").strip()


def main() -> None:
    agent = SocialAgent()
    print("Social media assistant. Type your request, or 'quit' to exit.\n")
    while True:
        try:
            user_text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_text.lower() in {"quit", "exit"}:
            break
        if not user_text:
            continue
        print("(thinking...)")
        try:
            reply = agent.send(user_text)
        except anthropic.AuthenticationError:
            print("Invalid API key. Set ANTHROPIC_API_KEY and try again.")
            break
        except anthropic.RateLimitError:
            print("Rate limited. Wait a minute and try again.")
            continue
        except anthropic.APIStatusError as e:
            print(f"API error ({e.status_code}): {e.message}")
            continue
        except anthropic.APIConnectionError:
            print("Network error. Check your connection and try again.")
            continue
        print(f"\nassistant> {reply}\n")


if __name__ == "__main__":
    main()
