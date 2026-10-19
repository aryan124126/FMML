"""Moves posts between the local store and the Team Hub page's shared database.

The Team Hub is a private claude.ai page. Claude (in chat) does the actual transfer with its
database tool; this module prepares and applies the files:
  push: writes one JSON file per post into data/hub_outbox/<collection>/<id>.json
  pull: reads the files Claude downloaded from the hub and applies reviewers' decisions and edits
"""

import json
import shutil
from pathlib import Path

from .analytics import Analytics
from .claims import check_post, is_blocked
from .config import Config
from .store import TEXT_FIELDS, Store

HUB_FIELDS = [
    "id", "idea_id", "account", "account_name", "account_type", "approver", "platform", "date", "time",
    "slot_source", "slot_reason", "theme", "pillar", "format", "hook", "caption", "cta", "hashtags", "alt_text",
    "thread_parts", "personalise_prompt", "design_brief", "claims_notes", "uses_ai_media", "shows_children",
    "consent_confirmed", "collab_with", "key_date", "internal_notes", "issues", "blocked", "status", "review",
    "updated_at", "sample", "edited_since_check", "campaign",
]
# What reviewers may change on the hub.
EDITABLE = [*TEXT_FIELDS, "personalise_prompt", "consent_confirmed"]


def _write(out_dir: Path, collection: str, doc_id: str, doc: dict) -> Path:
    path = out_dir / collection / f"{doc_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def push_reports(analytics: Analytics, reports_dir: Path, out_dir: Path) -> list[Path]:
    """Reports and experiments for the hub's Growth tab."""
    files = [_write(out_dir, "reports", p.stem, json.loads(p.read_text(encoding="utf-8")))
             for p in sorted(reports_dir.glob("*.json"))] if reports_dir.exists() else []
    files += [_write(out_dir, "experiments", e["id"], e) for e in analytics.experiments.values()]
    return files


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
    """Apply what reviewers did on the hub. Returns a plain-language list of what changed.

    Only real actions are applied: text edits the hub recorded in a post's `edits` list, and
    status decisions newer than the one we already have. A hub copy that is merely out of date
    (for example, before a fresh push) changes nothing.
    """
    changes = []
    for path in sorted((in_dir / "posts").glob("*.json")):
        doc = _load_doc(path)
        post = store.posts.get(doc.get("id") or path.stem)
        if post is None:
            continue
        known = {(e.get("field"), e.get("at"), e.get("by")) for e in post.get("edits", [])}
        new_edits = [e for e in doc.get("edits") or [] if (e.get("field"), e.get("at"), e.get("by")) not in known]
        edited = False
        for e in sorted(new_edits, key=lambda e: e.get("at") or ""):
            if e.get("field") in EDITABLE and store.edit(post["id"], e["field"], e.get("new"), by=e.get("by") or "hub"):
                edited = True
                changes.append(f"{post['id']}: edited {e['field']} on the hub")
        post["edits"] = post.get("edits", []) + new_edits
        if doc.get("edited_since_check") and doc.get("consent_confirmed") != post.get("consent_confirmed"):
            store.edit(post["id"], "consent_confirmed", bool(doc.get("consent_confirmed")), by="hub")
            edited = True
            changes.append(f"{post['id']}: parental consent {'recorded' if doc.get('consent_confirmed') else 'removed'}")
        if edited or doc.get("edited_since_check"):
            post["issues"] = check_post(post, cfg)
            post["blocked"] = is_blocked(post["issues"])
            post["edited_since_check"] = False
        review = doc.get("review") or {}
        seen = max((post.get("review") or {}).get("at") or "", post.get("hub_review_seen_at") or "")
        newer = review.get("at") and review["at"] > seen
        new_status = doc.get("status")
        if newer and new_status and new_status != post["status"]:
            by = review.get("by_name") or review.get("by") or "hub"
            try:
                store.set_status(post["id"], new_status, by=by, comment=review.get("comment", ""))
                post["review"] = {**post["review"], "at": review["at"], "by": review.get("by")}
                changes.append(f"{post['id']}: {by} set status to {new_status}")
            except ValueError as e:
                changes.append(f"{post['id']}: NOT {new_status}: {e}")
            post["hub_review_seen_at"] = review["at"]  # handled; don't re-apply on the next pull
    store.save()
    return changes


def pull_extras(store: Store, analytics: Analytics, in_dir: Path) -> list[str]:
    """Ideas from the ideas box, and results people logged for their own LinkedIn posts."""
    changes = []
    for path in sorted((in_dir / "ideas").glob("*.json")):
        doc = _load_doc(path)
        if path.stem not in store.ideas:
            changes.append(f"New idea: {doc.get('text', '')[:80]}")
        store.ideas[path.stem] = {"text": doc.get("text", ""), "account": doc.get("account", ""),
                                  "by": doc.get("by"), "at": doc.get("at"), "status": doc.get("status", "new")}
    for path in sorted((in_dir / "results").glob("*.json")):
        doc = _load_doc(path)
        post = store.posts.get(doc.get("post_id"))
        if not post or not doc.get("posted_at"):
            continue
        row = {"posted_at": doc["posted_at"][:16], "external_id": f"hub-{path.stem}", "text": post["hook"],
               "permalink": doc.get("link", ""), "format": post["format"], "reach": None,
               "impressions": doc.get("impressions"), "likes": doc.get("reactions"), "comments": doc.get("comments"),
               "shares": doc.get("reposts"), "saves": None, "follows": None, "profile_visits": None,
               "link_clicks": None, "avg_watch_seconds": None, "completion_rate": None, "non_follower_reach": None}
        analytics.add_rows([row], post["account"], post["platform"], source="hub")
        # We know exactly which planned post this is, even if it went out on a different day.
        analytics.posts[f"{post['platform']}:{row['external_id']}"].update(
            post_id=post["id"], theme=post["theme"], pillar=post["pillar"], idea_id=post["idea_id"])
        changes.append(f"Results logged for {post['id']}")
    store.save()
    analytics.save()
    return changes
