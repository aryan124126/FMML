"""Moves posts between the local store and the Team Hub page's shared database.

The Team Hub is a private claude.ai page. Claude (in chat) does the actual transfer with its
database tool; this module prepares and applies the files:
  push: writes one JSON file per post into data/hub_outbox/<collection>/<id>.json
  pull: reads the files Claude downloaded from the hub and applies reviewers' decisions and edits
"""

import json
import shutil
from pathlib import Path

from .claims import check_post, is_blocked
from .config import Config
from .store import TEXT_FIELDS, Store

HUB_FIELDS = [
    "id", "idea_id", "account", "account_name", "account_type", "approver", "platform", "date", "time",
    "slot_source", "slot_reason", "theme", "pillar", "format", "hook", "caption", "cta", "hashtags", "alt_text",
    "thread_parts", "personalise_prompt", "design_brief", "claims_notes", "uses_ai_media", "shows_children",
    "consent_confirmed", "collab_with", "key_date", "internal_notes", "issues", "blocked", "status", "review",
    "updated_at",
]
# What reviewers may change on the hub.
EDITABLE = [*TEXT_FIELDS, "personalise_prompt", "consent_confirmed"]


def push(store: Store, out_dir: Path, post_ids: list[str] | None = None) -> list[Path]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    files = []
    posts = [store.posts[i] for i in post_ids] if post_ids else list(store.posts.values())
    for post in posts:
        doc = {k: post.get(k) for k in HUB_FIELDS}
        doc["edits"] = post.get("edits", [])
        path = out_dir / "posts" / f"{post['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        files.append(path)
    for plan in store.plans.values():
        path = out_dir / "plans" / f"{plan['id']}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf-8")
        files.append(path)
    return files


def _load_doc(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc.get("data", doc) if isinstance(doc.get("data"), dict) else doc


def pull(store: Store, cfg: Config, in_dir: Path) -> list[str]:
    """Apply hub changes. Returns a plain-language list of what changed."""
    changes = []
    for path in sorted((in_dir / "posts").glob("*.json")):
        doc = _load_doc(path)
        post = store.posts.get(doc.get("id") or path.stem)
        if post is None:
            continue
        review = doc.get("review") or {}
        by = review.get("by_name") or review.get("by") or "hub"
        edited = False
        for field in EDITABLE:
            if field in doc and store.edit(post["id"], field, doc[field], by=by):
                edited = True
                changes.append(f"{post['id']}: {by} edited {field}")
        if edited:
            post["issues"] = check_post(post, cfg)
            post["blocked"] = is_blocked(post["issues"])
        new_status = doc.get("status")
        if new_status and new_status != post["status"]:
            try:
                store.set_status(post["id"], new_status, by=by, comment=review.get("comment", ""))
                changes.append(f"{post['id']}: {by} set status to {new_status}")
            except ValueError as e:
                changes.append(f"{post['id']}: NOT {new_status}: {e}")
        if doc.get("edits"):
            post["edits"] = doc["edits"]
    store.save()
    return changes
