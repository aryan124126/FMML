"""Saved posts (data/posts.json) and the change log (data/log.jsonl).

Every generated draft and every human change is logged; the edits are training signal for voice.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

from .models import STATUSES

DATA_DIR = Path(os.environ.get("HIFUEL_DATA", "data"))
TEXT_FIELDS = ["hook", "caption", "cta", "hashtags", "alt_text", "thread_parts"]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Store:
    def __init__(self, data_dir: Path | None = None):
        self.dir = Path(data_dir or DATA_DIR)
        self.posts_file = self.dir / "posts.json"
        self.log_file = self.dir / "log.jsonl"
        self.posts: dict[str, dict] = {}
        self.plans: dict[str, dict] = {}
        if self.posts_file.exists():
            saved = json.loads(self.posts_file.read_text(encoding="utf-8"))
            self.posts, self.plans = saved.get("posts", {}), saved.get("plans", {})

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.posts_file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"posts": self.posts, "plans": self.plans}, indent=2, ensure_ascii=False),
                       encoding="utf-8")
        tmp.replace(self.posts_file)

    def log(self, event: str, **fields) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"at": _now(), "event": event, **fields}, ensure_ascii=False) + "\n")

    def new_id(self, post: dict) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", post.get("idea_id", "post").lower()).strip("-")[:30] or "post"
        base = f"{post['date']}-{post['account']}-{post['platform']}-{slug}"
        pid, n = base, 2
        while pid in self.posts:
            pid, n = f"{base}-{n}", n + 1
        return pid

    def add(self, post: dict) -> dict:
        post = {**post, "status": "draft", "created_at": _now(), "updated_at": _now(), "review": {}}
        self.posts[post["id"]] = post
        self.log("generated", post_id=post["id"], account=post["account"], platform=post["platform"])
        return post

    def set_status(self, post_id: str, status: str, by: str, comment: str = "") -> dict:
        if status not in STATUSES:
            raise ValueError(f"Status must be one of: {', '.join(STATUSES)}")
        post = self.posts[post_id]
        if status in {"approved", "scheduled", "posted"} and post.get("blocked"):
            raise ValueError(f"{post_id} has blocking issues; fix them before approving.")
        old = post["status"]
        post["status"] = status
        post["review"] = {"by": by, "at": _now(), "comment": comment}
        post["updated_at"] = _now()
        self.log("status", post_id=post_id, by=by, old=old, new=status, comment=comment)
        return post

    def edit(self, post_id: str, field: str, value, by: str) -> bool:
        post = self.posts[post_id]
        old = post.get(field)
        if old == value:
            return False
        post[field] = value
        post["updated_at"] = _now()
        self.log("edit", post_id=post_id, account=post["account"], by=by, field=field, old=old, new=value)
        return True

    def remove(self, post_ids: list[str], by: str) -> None:
        for pid in post_ids:
            post = self.posts.pop(pid)
            self.log("removed", post_id=pid, account=post["account"], by=by)
        for plan in self.plans.values():
            plan["post_ids"] = [i for i in plan.get("post_ids", []) if i not in post_ids]
        self.plans = {k: v for k, v in self.plans.items() if v.get("post_ids")}

    def in_range(self, start: str, end: str, accounts=None, statuses=None) -> list[dict]:
        out = [p for p in self.posts.values() if start <= p["date"] <= end
               and (not accounts or p["account"] in accounts)
               and (not statuses or p["status"] in statuses)]
        return sorted(out, key=lambda p: (p["date"], p.get("time", ""), p["account"]))

    def recent_edits(self, account: str, limit: int = 5) -> list[dict]:
        """The latest human text edits for an account, oldest first: examples of the team's voice."""
        if not self.log_file.exists():
            return []
        edits = []
        for line in self.log_file.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            if e["event"] == "edit" and e.get("account") == account and e.get("field") in TEXT_FIELDS:
                edits.append({"field": e["field"], "before": e["old"], "after": e["new"]})
        return edits[-limit:]
