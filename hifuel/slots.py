"""Best-time-to-post engine (CLAUDE.md §6). All times IST.

Source order, and every recommendation says which one it used:
  1. own_audience - hours when the account's followers are online (Instagram online_followers)
  2. own_history  - the account's past posts, scored by weekday x hour
  3. benchmark    - starting hypotheses from config/time_slots.yaml
  plus explore    - ~20% of posts go to an untested hour so the data keeps improving
Spacing rules then pick the first candidate that doesn't clash with other posts.
"""

import hashlib
from collections import defaultdict
from datetime import date, datetime, timedelta

from .config import Config

SOURCE_LABELS = {
    "own_audience": "Own audience (when followers are online)",
    "own_history": "Own past performance",
    "benchmark": "Benchmark (starting hypothesis, replace after 4-6 weeks of data)",
    "explore": "Experiment (untested slot, so we keep learning)",
}


def _hhmm(hour: int, minute: int = 0) -> str:
    return f"{hour:02d}:{minute:02d}"


def _to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _stable_fraction(key: str) -> float:
    """A repeatable number in [0, 1) for a post, so plans don't change on every run."""
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) / 0x100000000


def benchmark_slots(cfg: Config, audience: str, weekday: int) -> list[str]:
    spec = cfg.slots["audiences"][audience]
    for group in spec["benchmark"]:
        if weekday in group["weekdays"]:
            return list(group["slots"])
    return []


def history_scores(history: list[dict], account: str, platform: str, min_posts: int) -> dict:
    """Score each (weekday, hour) slot from past posts.

    Each post's reach is divided by followers at the time, and its engagement by reach; both
    are then compared with the average for that format (Reel vs carousel vs image...), so a
    slot isn't favoured just because it happened to get more Reels.
    Returns {(weekday, hour): score} for slots with at least `min_posts` posts. 1.0 = average.
    """
    rows = [r for r in history if r["account"] == account and r["platform"] == platform
            and r.get("reach") and r.get("followers")]
    if not rows:
        return {}
    by_format = defaultdict(list)
    for r in rows:
        by_format[r["format"]].append(r)
    format_avg = {}
    for fmt, items in by_format.items():
        format_avg[fmt] = (
            sum(r["reach"] / r["followers"] for r in items) / len(items),
            sum(r["engagements"] / r["reach"] for r in items) / len(items),
        )
    slot_scores = defaultdict(list)
    for r in rows:
        reach_avg, eng_avg = format_avg[r["format"]]
        reach_score = (r["reach"] / r["followers"]) / reach_avg if reach_avg else 0
        eng_score = (r["engagements"] / r["reach"]) / eng_avg if eng_avg else 0
        slot_scores[(r["weekday"], r["hour"])].append((reach_score + eng_score) / 2)
    return {slot: sum(v) / len(v) for slot, v in slot_scores.items() if len(v) >= min_posts}


def _candidates(post, cfg, history, audience_data):
    """Ordered (time, source, reason) candidates for one post."""
    account, platform = post["account"], post["platform"]
    audience = post.get("audience") or cfg.audience_for(account, platform)
    weekday = date.fromisoformat(post["date"]).weekday()
    lo, hi = cfg.slots["audiences"][audience]["active_hours"]
    spacing = cfg.slots["spacing"]
    out = []

    online = (audience_data or {}).get(account, {}).get(platform) or {}
    if online:
        ranked = sorted((h for h in online if lo <= int(h) <= hi), key=lambda h: -online[h])
        for h in ranked[:4]:
            out.append((_hhmm(int(h)), "own_audience", f"followers most online around {int(h):02d}:00 (last 30 days)"))

    scores = history_scores(history or [], account, platform, spacing["min_posts_per_slot_for_history"])
    tested_hours = {h for (_, h) in scores}
    day_scores = sorted(((s, h) for (wd, h), s in scores.items() if wd == weekday), reverse=True)
    for s, h in day_scores[:3]:
        out.append((_hhmm(h), "own_history", f"past posts in this slot scored {s:.2f}x the account average"))

    bench = benchmark_slots(cfg, audience, weekday)
    for t in bench:
        out.append((t, "benchmark", f"{audience} audience benchmark for this weekday"))
    if not bench:
        out.append((_hhmm((lo + hi) // 2), "benchmark",
                    f"no {audience} benchmark for this weekday; consider moving the post"))

    if _stable_fraction(post["id"]) < spacing["explore_share"]:
        known = tested_hours | {_to_minutes(t) // 60 for t, _, _ in out}
        untested = [h for h in range(lo, hi + 1) if h not in known]
        if untested:
            h = untested[int(_stable_fraction(post["id"] + "h") * len(untested))]
            out.insert(0, (_hhmm(h), "explore", f"testing {h:02d}:00, a slot we have no data for yet"))
    return out, (lo, hi)


def _fits(when: datetime, post, placed, spacing) -> bool:
    same_account = [p for p in placed if p["account"] == post["account"] and p["dt"].date() == when.date()]
    same_platform = [p for p in same_account if p.get("platform") == post.get("platform")]
    if len(same_platform) >= spacing["max_posts_per_platform_per_day"]:
        return False
    gap = timedelta(hours=spacing["min_gap_hours_same_platform"])
    if any(abs(p["dt"] - when) < gap for p in same_platform):
        return False
    account_gap = timedelta(minutes=spacing["min_gap_minutes_same_account"])
    if any(abs(p["dt"] - when) < account_gap for p in same_account):
        return False
    idea_gap = timedelta(hours=spacing["min_gap_hours_same_idea"])
    return not any(p["idea_id"] == post.get("idea_id") and p["account"] != post["account"]
                   and abs(p["dt"] - when) < idea_gap for p in placed)


def assign_slots(posts: list[dict], cfg: Config, history=None, audience_data=None, already_placed=None) -> list[dict]:
    """Give every post a time. Returns {"time", "slot_source", "slot_reason"} per post, in input order.

    Posts must have id, account, platform, date and idea_id. Higher-priority accounts pick first.
    `already_placed` lists posts that already have a time ({account, platform, idea_id, date, time}).
    """
    spacing = cfg.slots["spacing"]
    placed = [
        {"account": p["account"], "platform": p.get("platform"), "idea_id": p.get("idea_id"),
         "dt": datetime.fromisoformat(f"{p['date']}T{p['time']}")}
        for p in already_placed or [] if p.get("time")
    ]
    order = sorted(range(len(posts)), key=lambda i: (cfg.account(posts[i]["account"]).get("priority", 9), i))
    results = [None] * len(posts)
    for i in order:
        post = posts[i]
        candidates, (lo, hi) = _candidates(post, cfg, history, audience_data)
        choice = None
        for t, source, reason in candidates:
            when = datetime.fromisoformat(f"{post['date']}T{t}")
            if _fits(when, post, placed, spacing):
                choice = (when, source, reason)
                break
        if choice is None:  # shift the best candidate hour by hour inside the active window
            t, source, reason = candidates[0]
            base = datetime.fromisoformat(f"{post['date']}T{t}")
            for step in range(1, 24):
                for when in (base + timedelta(hours=step), base - timedelta(hours=step)):
                    if when.date() == base.date() and lo <= when.hour <= hi and _fits(when, post, placed, spacing):
                        choice = (when, source, reason + f" (moved {when.hour - base.hour:+d}h for spacing)")
                        break
                if choice:
                    break
        if choice is None:
            when = datetime.fromisoformat(f"{post['date']}T{candidates[0][0]}")
            choice = (when, candidates[0][1], candidates[0][2] + " - WARNING: breaks spacing rules; move to another day")
        when, source, reason = choice
        placed.append({"account": post["account"], "platform": post.get("platform"), "idea_id": post.get("idea_id"), "dt": when})
        results[i] = {"time": when.strftime("%H:%M"), "slot_source": source,
                      "slot_reason": f"{SOURCE_LABELS[source]}: {reason}"}
    return results
