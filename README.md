# Social Media Assistant

A command-line AI agent, powered by Claude, that helps you write and plan social media posts.

It can:
- Draft posts for X, Threads, Bluesky, LinkedIn, Instagram, Facebook and TikTok, fitted to each platform's style
- Check posts against each platform's character limit
- Search the web for trends and news
- Save drafts and schedule them on a simple content calendar (stored in `data/drafts.json`)

It does **not** publish posts. You copy the finished text to the platform yourself.

## Setup

1. Install Python 3.10 or newer.
2. Install the dependency:
   ```bash
   pip install -r requirements.txt
   ```
3. Get an API key at https://console.anthropic.com and set it:
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```

## Run

```bash
python -m social_agent.agent
```

Example requests:
- `Write a LinkedIn post announcing I finished my ML course`
- `Turn that into a tweet and a Threads post`
- `What's trending in AI this week? Suggest 3 post ideas`
- `Save the tweet for next Monday`
- `Show my content calendar`

Type `quit` to exit.

## Project layout

- `social_agent/agent.py` – the chat loop that talks to Claude and runs tools
- `social_agent/tools.py` – the tools Claude can use (length check, save/list/delete drafts)
- `tests/` – tests that use a fake Claude client, so no API key is needed: `pip install pytest && pytest`

## Adding a new tool

1. Write a Python function in `tools.py`.
2. Add its description and input schema to `TOOL_DEFINITIONS`.
3. Add it to `_FUNCTIONS`.

Claude will start using it when it fits the request.
