"""Experiment log (CLAUDE.md §7.4): change one thing at a time and compare it with everything else.

An experiment names an account (and optionally a platform), one variable on the post (format, theme,
pillar, hour band, or time-slot source) and the value being tested. Evaluation compares the metric
for posts with that value against the account's other posts in the same window.
"""

import re
from datetime import date, datetime, timedelta

from .analytics import Analytics, engagements, exposure

VARIABLES = {"format", "theme", "pillar", "hour_band", "slot_source"}
METRICS = {
    "engagement_rate": "engagement per reach",
    "share_rate": "shares per reach",
    "save_rate": "saves per reach",
    "reach_per_post": "reach per post",
}
MIN_POSTS = 3


def hour_band(hour: int) -> str:
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"


def metric_value(recs: list[dict], metric: str):
    base = sum(exposure(r) or 0 for r in recs)
    if not recs or not base:
        return None
    if metric == "engagement_rate":
        return sum(engagements(r) for r in recs) / base
    if metric == "share_rate":
        return sum(r.get("shares") or 0 for r in recs) / base
    if metric == "save_rate":
        return sum(r.get("saves") or 0 for r in recs) / base
    if metric == "reach_per_post":
        return base / len(recs)
    raise ValueError(f"Unknown metric {metric}")


def field_value(rec: dict, variable: str, store_posts: dict):
    if variable == "hour_band":
        return hour_band(rec["hour"])
    if variable == "slot_source":
        return (store_posts.get(rec.get("post_id")) or {}).get("slot_source")
    return rec.get(variable)


def add(analytics: Analytics, name: str, hypothesis: str, account: str, variable: str, value: str,
        metric: str = "engagement_rate", platform: str = "", start: str = "", weeks: int = 4) -> dict:
    if variable not in VARIABLES:
        raise ValueError(f"Variable must be one of: {', '.join(sorted(VARIABLES))}")
    if metric not in METRICS:
        raise ValueError(f"Metric must be one of: {', '.join(METRICS)}")
    start = start or date.today().isoformat()
    exp_id = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "experiment"
    base, n = exp_id, 2
    while exp_id in analytics.experiments:
        exp_id, n = f"{base}-{n}", n + 1
    exp = {"id": exp_id, "name": name, "hypothesis": hypothesis, "account": account, "platform": platform,
           "variable": variable, "value": value, "metric": metric, "start": start,
           "end": (date.fromisoformat(start) + timedelta(weeks=weeks) - timedelta(days=1)).isoformat(),
           "status": "running", "result": "", "created_at": datetime.now().isoformat(timespec="seconds")}
    analytics.experiments[exp_id] = exp
    return exp


def evaluate(analytics: Analytics, exp: dict, store_posts: dict) -> dict:
    """Compare the tested value against the account's other posts. Returns numbers and a plain sentence."""
    recs = analytics.in_range(exp["start"], exp["end"], exp["account"], exp.get("platform") or None)
    variant = [r for r in recs if str(field_value(r, exp["variable"], store_posts)) == str(exp["value"])]
    control = [r for r in recs if r not in variant]
    v, c = metric_value(variant, exp["metric"]), metric_value(control, exp["metric"])
    label = METRICS[exp["metric"]]
    out = {"variant_posts": len(variant), "control_posts": len(control), "variant": v, "control": c}
    if len(variant) < MIN_POSTS or len(control) < MIN_POSTS or v is None or c is None:
        out["summary"] = (f"Not enough data yet: {len(variant)} test post(s) and {len(control)} other post(s); "
                          f"need at least {MIN_POSTS} of each.")
        out["verdict"] = "pending"
        return out
    ratio = v / c if c else None
    fmt = (lambda x: f"{x:.1%}") if exp["metric"] != "reach_per_post" else (lambda x: f"{x:,.0f}")
    if ratio and ratio >= 1.15:
        out["verdict"] = "better"
        out["summary"] = f"{exp['variable']} = {exp['value']} did better: {label} {fmt(v)} vs {fmt(c)} ({ratio:.1f}x), {len(variant)} vs {len(control)} posts."
    elif ratio and ratio <= 0.87:
        out["verdict"] = "worse"
        out["summary"] = f"{exp['variable']} = {exp['value']} did worse: {label} {fmt(v)} vs {fmt(c)} ({ratio:.1f}x), {len(variant)} vs {len(control)} posts."
    else:
        out["verdict"] = "no_difference"
        out["summary"] = f"No clear difference: {label} {fmt(v)} vs {fmt(c)}, {len(variant)} vs {len(control)} posts."
    return out


def close(analytics: Analytics, exp_id: str, store_posts: dict, note: str = "") -> dict:
    exp = analytics.experiments[exp_id]
    result = evaluate(analytics, exp, store_posts)
    exp.update(status="done", result=(result["summary"] + (f" Note: {note}" if note else "")).strip(),
               verdict=result["verdict"])
    return exp
