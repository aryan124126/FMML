"""Local tools the agent can call. Drafts are stored in a JSON file."""

import json
import os
import uuid
from datetime import date, datetime
from pathlib import Path

# Character limits for post text on each platform.
PLATFORM_LIMITS = {
    "x": 280,
    "threads": 500,
    "bluesky": 300,
    "linkedin": 3000,
    "instagram": 2200,
    "facebook": 63206,
    "tiktok": 4000,
}

DRAFTS_FILE = Path(os.environ.get("SOCIAL_AGENT_DRAFTS", "data/drafts.json"))


def _load() -> list[dict]:
    if not DRAFTS_FILE.exists():
        return []
    return json.loads(DRAFTS_FILE.read_text())


def _save(drafts: list[dict]) -> None:
    DRAFTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DRAFTS_FILE.write_text(json.dumps(drafts, indent=2))


def check_post_length(platform: str, text: str) -> str:
    limit = PLATFORM_LIMITS[platform]
    n = len(text)
    if n <= limit:
        return f"OK: {n}/{limit} characters for {platform}."
    return f"TOO LONG: {n}/{limit} characters for {platform}. Cut {n - limit} characters."


def save_draft(platform: str, text: str, scheduled_for: str = "") -> str:
    scheduled_for = scheduled_for or None
    if scheduled_for:
        date.fromisoformat(scheduled_for)  # raises ValueError if not YYYY-MM-DD
    limit = PLATFORM_LIMITS[platform]
    if len(text) > limit:
        return f"Not saved: {len(text)} characters is over the {platform} limit of {limit}."
    drafts = _load()
    draft = {
        "id": uuid.uuid4().hex[:8],
        "platform": platform,
        "text": text,
        "scheduled_for": scheduled_for,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    drafts.append(draft)
    _save(drafts)
    return f"Saved draft {draft['id']} for {platform}" + (
        f", scheduled for {scheduled_for}." if scheduled_for else "."
    )


def list_drafts(platform: str = "all") -> str:
    drafts = _load()
    if platform != "all":
        drafts = [d for d in drafts if d["platform"] == platform]
    if not drafts:
        return "No drafts saved."
    # Scheduled posts first, in date order; unscheduled ones after.
    drafts.sort(key=lambda d: (d["scheduled_for"] is None, d["scheduled_for"] or ""))
    return json.dumps(drafts, indent=2)


def delete_draft(draft_id: str) -> str:
    drafts = _load()
    kept = [d for d in drafts if d["id"] != draft_id]
    if len(kept) == len(drafts):
        return f"No draft with id {draft_id}."
    _save(kept)
    return f"Deleted draft {draft_id}."


PLATFORM_ENUM = {"type": "string", "enum": sorted(PLATFORM_LIMITS)}

TOOL_DEFINITIONS = [
    {
        "name": "check_post_length",
        "description": "Check whether post text fits the character limit of a platform. "
        "Use before showing or saving a final post.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"platform": PLATFORM_ENUM, "text": {"type": "string"}},
            "required": ["platform", "text"],
            "additionalProperties": False,
        },
    },
    {
        "name": "save_draft",
        "description": "Save a finished post to the user's local drafts. Only call this when "
        "the user asks to save or schedule a post. scheduled_for is an optional date (YYYY-MM-DD) "
        "for the content calendar.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": PLATFORM_ENUM,
                "text": {"type": "string"},
                "scheduled_for": {
                    "type": "string",
                    "description": "YYYY-MM-DD, or an empty string if not scheduled",
                },
            },
            "required": ["platform", "text", "scheduled_for"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_drafts",
        "description": "List saved drafts (the content calendar), optionally for one platform.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": sorted(PLATFORM_LIMITS) + ["all"]},
            },
            "required": ["platform"],
            "additionalProperties": False,
        },
    },
    {
        "name": "delete_draft",
        "description": "Delete a saved draft by its id. Only call this when the user asks.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"draft_id": {"type": "string"}},
            "required": ["draft_id"],
            "additionalProperties": False,
        },
    },
]

_FUNCTIONS = {
    "check_post_length": check_post_length,
    "save_draft": save_draft,
    "list_drafts": list_drafts,
    "delete_draft": delete_draft,
}


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run a tool. Returns (result_text, is_error)."""
    func = _FUNCTIONS.get(name)
    if func is None:
        return f"Unknown tool: {name}", True
    try:
        return func(**tool_input), False
    except (KeyError, TypeError, ValueError) as e:
        return f"Error running {name}: {e}", True
