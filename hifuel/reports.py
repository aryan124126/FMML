"""Weekly performance and monthly growth reports (CLAUDE.md §7.4).

Numbers come only from imported analytics. Takeaways are written by fixed rules, and only when
both sides of a comparison have at least MIN_POSTS posts, so a single lucky post can't drive a
conclusion.
"""

import calendar
from collections import defaultdict
from datetime import date, datetime, timedelta

from . import experiments as exps
from .analytics import Analytics, engagements, exposure
from .config import Config
from .store import Store

MIN_POSTS = 3
PLATFORM_NAMES = {"instagram": "Instagram", "linkedin": "LinkedIn", "facebook": "Facebook",
                  "whatsapp_channel": "WhatsApp Channel", "x": "X"}
FORMAT_NAMES = {"reel": "Reels", "carousel": "carousels", "single_image": "single images", "story": "Stories",
                "document": "document posts", "text": "text posts", "poll": "polls", "thread": "threads",
                "channel_message": "channel messages"}
BAND_NAMES = {"morning": "morning posts (before 12:00)", "afternoon": "afternoon posts (12:00-17:00)",
              "evening": "evening posts (17:00-21:00)", "night": "night posts (after 21:00)"}
THEME_NAMES = {"educational": "educational posts", "impact_story": "impact stories",
               "initiative_promo": "promotional posts", "behind_the_scenes": "behind-the-scenes posts",
               "founder_team_voice": "founder/team posts", "engagement": "engagement posts"}


def _rate(num, den):
    return num / den if den else None


def _pct_change(cur, prev):
    if cur is None or prev in (None, 0):
        return None
    return (cur - prev) / prev


def kpis(recs: list[dict], analytics: Analytics, account: str, platform: str, start: str, end: str) -> dict:
    base = sum(exposure(r) or 0 for r in recs)
    nf = [r for r in recs if r.get("non_follower_reach") is not None and r.get("reach")]
    reels = [r for r in recs if r["format"] == "reel"]
    f_start = analytics.followers_at(account, platform, (date.fromisoformat(start) - timedelta(days=1)).isoformat())
    f_end = analytics.followers_at(account, platform, end)
    in_range = [f for f in analytics.followers if f["account"] == account and f["platform"] == platform
                and start <= f["date"] <= end]
    return {
        "posts": len(recs),
        "exposure": base,
        "exposure_label": "reach" if any(r.get("reach") for r in recs) else "impressions",
        "engagement_rate": _rate(sum(engagements(r) for r in recs), base),
        "share_rate": _rate(sum(r.get("shares") or 0 for r in recs), base),
        "save_rate": _rate(sum(r.get("saves") or 0 for r in recs), base) if platform == "instagram" else None,
        "non_follower_share": _rate(sum(r["non_follower_reach"] for r in nf), sum(r["reach"] for r in nf)) if nf else None,
        "avg_watch_seconds": (sum(r["avg_watch_seconds"] for r in reels if r.get("avg_watch_seconds") is not None)
                              / len([r for r in reels if r.get("avg_watch_seconds") is not None]))
        if any(r.get("avg_watch_seconds") is not None for r in reels) else None,
        "profile_visits": sum(r.get("profile_visits") or 0 for r in recs),
        "link_clicks": sum(r.get("link_clicks") or 0 for r in recs),
        "followers": f_end,
        "follower_growth": (f_end - f_start) if (in_range and f_start is not None and f_end is not None) else None,
    }


def _compare_groups(recs, key, names, label):
    """Best vs worst group by engagement per reach, if both have enough posts and differ by 30%+."""
    groups = defaultdict(list)
    for r in recs:
        if r.get(key):
            groups[r[key]].append(r)
    rated = [(engagements_rate(v), k, len(v)) for k, v in groups.items() if len(v) >= MIN_POSTS]
    rated = [g for g in rated if g[0] is not None]
    if len(rated) < 2:
        return None
    rated.sort(reverse=True)
    (best, bk, bn), (worst, wk, wn) = rated[0], rated[-1]
    if not worst or best / worst < 1.3:
        return None
    return {"ratio": best / worst, "best": bk, "worst": wk,
            "text": f"On {label}, {names.get(bk, bk)} earned {best / worst:.1f}x the engagement per reach of "
                    f"{names.get(wk, wk)} ({bn} vs {wn} posts)."}


def engagements_rate(recs):
    base = sum(exposure(r) or 0 for r in recs)
    return _rate(sum(engagements(r) for r in recs), base)


def build_report(cfg: Config, store: Store, analytics: Analytics, start: str, end: str, kind: str = "weekly") -> dict:
    days = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    prev_end = (date.fromisoformat(start) - timedelta(days=1)).isoformat()
    prev_start = (date.fromisoformat(start) - timedelta(days=days)).isoformat()
    recs = analytics.in_range(start, end)
    for r in recs:  # fill planning details for takeaways
        r["slot_source"] = (store.posts.get(r.get("post_id")) or {}).get("slot_source")
        r["hour_band"] = exps.hour_band(r["hour"])

    rows, worked, didnt, notes = [], [], [], []
    pairs = sorted({(r["account"], r["platform"]) for r in recs},
                   key=lambda p: (cfg.accounts.get(p[0], {}).get("priority", 9), p))
    for account, platform in pairs:
        cur = [r for r in recs if r["account"] == account and r["platform"] == platform]
        prev = analytics.in_range(prev_start, prev_end, account, platform)
        k = kpis(cur, analytics, account, platform, start, end)
        kp = kpis(prev, analytics, account, platform, prev_start, prev_end) if prev else None
        name = cfg.accounts.get(account, {}).get("name", account)
        k.update(account=account, account_name=name, platform=platform,
                 change={"exposure": _pct_change(k["exposure"], kp and kp["exposure"]),
                         "engagement_rate": _pct_change(k["engagement_rate"], kp and kp["engagement_rate"])}
                 if kp else {})
        rows.append(k)
        label = f"{name} {PLATFORM_NAMES.get(platform, platform)}"
        for key, names in (("format", FORMAT_NAMES), ("hour_band", BAND_NAMES), ("theme", THEME_NAMES)):
            c = _compare_groups(cur, key, names, label)
            if c:
                worked.append(c["text"])
        if kp and len(cur) >= MIN_POSTS and len(prev) >= MIN_POSTS:
            ch = k["change"]["engagement_rate"]
            if ch is not None and ch >= 0.2:
                worked.append(f"{label}: engagement per reach up {ch:.0%} on the previous period.")
            elif ch is not None and ch <= -0.2:
                didnt.append(f"{label}: engagement per reach down {-ch:.0%} on the previous period.")

    # Explore slots that beat the account's usual slots.
    for (account, platform) in pairs:
        cur = [r for r in recs if r["account"] == account and r["platform"] == platform]
        explore = [r for r in cur if r["slot_source"] == "explore"]
        usual = [r for r in cur if r["slot_source"] and r["slot_source"] != "explore"]
        if explore and len(usual) >= MIN_POSTS:
            e, u = engagements_rate(explore), engagements_rate(usual)
            if e and u and e / u >= 1.3:
                hours = ", ".join(sorted({f"{r['hour']:02d}:00" for r in explore}))
                worked.append(f"Test slot(s) {hours} on {cfg.accounts.get(account, {}).get('name', account)} "
                              f"{PLATFORM_NAMES.get(platform, platform)} did {e / u:.1f}x better than usual slots; worth repeating.")

    # LinkedIn advocacy: people vs company pages.
    li = [r for r in recs if r["platform"] == "linkedin"]
    people = [r for r in li if cfg.accounts.get(r["account"], {}).get("type") == "person"]
    pages = [r for r in li if cfg.accounts.get(r["account"], {}).get("type") in {"company", "initiative"}]
    advocacy = None
    if len(people) >= 2 and len(pages) >= 2:
        pp = sum(exposure(r) or 0 for r in people) / len(people)
        pg = sum(exposure(r) or 0 for r in pages) / len(pages)
        if pg:
            advocacy = {"people_avg": pp, "pages_avg": pg, "ratio": pp / pg}
            (worked if pp >= pg else didnt).append(
                f"LinkedIn: founder/team posts averaged {pp:,.0f} impressions per post vs {pg:,.0f} for company "
                f"pages ({pp / pg:.1f}x, {len(people)} vs {len(pages)} posts).")

    # Gaps: posts marked posted with no results.
    posted = [p for p in store.in_range(start, end) if p["status"] == "posted"]
    have = {r.get("post_id") for r in recs}
    missing = [p for p in posted if p["id"] not in have]
    if missing:
        notes.append(f"{len(missing)} posted post(s) have no results imported yet "
                     f"({', '.join(sorted({p['account_name'] for p in missing}))}).")
    if not recs:
        notes.append("No analytics imported for this period.")
    if not analytics.followers:
        notes.append("No follower counts recorded, so follower growth and reach normalisation are unavailable.")

    ranked = [r for r in recs if exposure(r)]
    if ranked:
        median = sorted(exposure(r) for r in ranked)[len(ranked) // 2]
        eligible = [r for r in ranked if exposure(r) >= median * 0.5]
        eligible.sort(key=lambda r: engagements(r) / exposure(r), reverse=True)
    else:
        eligible = []

    def brief(r):
        planned = store.posts.get(r.get("post_id")) or {}
        return {"account_name": cfg.accounts.get(r["account"], {}).get("name", r["account"]),
                "platform": r["platform"], "date": r["date"], "format": r["format"],
                "text": (planned.get("hook") or r.get("text") or "")[:120], "permalink": r.get("permalink", ""),
                "exposure": exposure(r), "engagement_rate": engagements(r) / exposure(r)}

    enquiries = {a: n for a in sorted({r["account"] for r in recs} | {e["account"] for e in analytics.enquiries})
                 if (n := analytics.enquiries_in(start, end, a))}
    experiments = []
    for exp in analytics.experiments.values():
        if exp["start"] <= end and exp["end"] >= start:
            res = exps.evaluate(analytics, exp, store.posts) if exp["status"] == "running" else \
                {"summary": exp.get("result", ""), "verdict": exp.get("verdict", "")}
            experiments.append({"id": exp["id"], "name": exp["name"], "account": exp["account"],
                                "hypothesis": exp["hypothesis"], "status": exp["status"],
                                "summary": res["summary"], "verdict": res.get("verdict", "")})

    priorities = _priorities(worked, didnt, notes, experiments) if kind == "monthly" else []
    report_id = f"{kind}_{start}_{end}"
    return {"id": report_id, "kind": kind, "start": start, "end": end,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "rows": rows, "enquiries": enquiries, "worked": worked, "didnt": didnt, "notes": notes,
            "priorities": priorities, "advocacy": advocacy, "experiments": experiments,
            "top_posts": [brief(r) for r in eligible[:3]], "bottom_posts": [brief(r) for r in eligible[-3:][::-1]]
            if len(eligible) > 3 else []}


def _priorities(worked, didnt, notes, experiments) -> list[str]:
    out = []
    if worked:
        out.append("Do more of what worked: " + worked[0])
    if didnt:
        out.append("Fix: " + didnt[0])
    if any("no results imported" in n.lower() or "no analytics" in n.lower() for n in notes):
        out.append("Import results for every posted post, so next month's report covers all accounts.")
    if not any(e["status"] == "running" for e in experiments):
        out.append("Start one experiment (one change at a time) on the highest-priority account.")
    pending = [e for e in experiments if e.get("verdict") == "pending"]
    if pending:
        out.append(f"Keep the '{pending[0]['name']}' experiment running until it has enough posts.")
    return out[:3]


def month_range(month: str) -> tuple[str, str]:
    y, m = map(int, month.split("-"))
    return f"{y:04d}-{m:02d}-01", f"{y:04d}-{m:02d}-{calendar.monthrange(y, m)[1]:02d}"


def _fmt_pct(x):
    return "–" if x is None else f"{x:.1%}"


def _fmt_change(x):
    return "" if x is None else f" ({'+' if x >= 0 else ''}{x:.0%})"


def render_markdown(r: dict) -> str:
    title = "Weekly performance report" if r["kind"] == "weekly" else "Monthly growth report"
    out = [f"# {title}: {r['start']} to {r['end']}", ""]
    if r["priorities"]:
        out += ["## Next month's three priorities", ""] + [f"{i + 1}. {p}" for i, p in enumerate(r["priorities"])] + [""]
    out += ["## What worked", ""] + ([f"- {w}" for w in r["worked"]] or ["- Not enough data for a clear conclusion yet."]) + [""]
    out += ["## What didn't", ""] + ([f"- {d}" for d in r["didnt"]] or ["- Nothing clearly underperformed."]) + [""]
    out += ["## Numbers by account", "",
            "| Account | Platform | Posts | Reach / impressions | Engagement per reach | Shares per reach | Saves per reach | Non-follower share | Follower growth |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for k in r["rows"]:
        ch = k.get("change") or {}
        growth = "–" if k["follower_growth"] is None else f"{k['follower_growth']:+,}"
        out.append(f"| {k['account_name']} | {PLATFORM_NAMES.get(k['platform'], k['platform'])} | {k['posts']} | "
                   f"{k['exposure']:,.0f} {k['exposure_label']}{_fmt_change(ch.get('exposure'))} | "
                   f"{_fmt_pct(k['engagement_rate'])}{_fmt_change(ch.get('engagement_rate'))} | {_fmt_pct(k['share_rate'])} | "
                   f"{_fmt_pct(k['save_rate'])} | {_fmt_pct(k['non_follower_share'])} | "
                   f"{growth} |")
    out.append("")
    if r["enquiries"]:
        out += ["## Inbound enquiries from social", ""] + [f"- {a}: {n}" for a, n in r["enquiries"].items()] + [""]
    if r["top_posts"]:
        out += ["## Top posts", ""] + [f"- {p['account_name']} {PLATFORM_NAMES.get(p['platform'], p['platform'])} "
                                       f"({p['date']}, {p['format']}): {_fmt_pct(p['engagement_rate'])} engagement per reach. {p['text']}"
                                       for p in r["top_posts"]] + [""]
    if r["experiments"]:
        out += ["## Experiments", ""] + [f"- **{e['name']}** ({e['status']}): {e['summary']}" for e in r["experiments"]] + [""]
    if r["notes"]:
        out += ["## Data notes", ""] + [f"- {n}" for n in r["notes"]] + [""]
    out.append("_Engagement = likes + comments + shares + saves. Comparisons need at least 3 posts on each side._")
    return "\n".join(out)


def account_insights(account: str, analytics: Analytics, store: Store, today: str, days: int = 90) -> dict:
    """What the planner should know from past results for one account (last `days` days)."""
    start = (date.fromisoformat(today) - timedelta(days=days)).isoformat()
    recs = analytics.in_range(start, today, account)
    if not recs:
        return {}
    out = {"posts_with_results": len(recs), "by_platform": {}}
    for platform in sorted({r["platform"] for r in recs}):
        cur = [r for r in recs if r["platform"] == platform]
        entry = {"posts": len(cur), "engagement_per_reach": round(engagements_rate(cur) or 0, 4)}
        for key in ("format", "theme"):
            groups = defaultdict(list)
            for r in cur:
                if r.get(key):
                    groups[r[key]].append(r)
            entry[f"by_{key}"] = {k: {"posts": len(v), "engagement_per_reach": round(engagements_rate(v) or 0, 4)}
                                  for k, v in groups.items() if len(v) >= MIN_POSTS}
        ranked = sorted((r for r in cur if exposure(r)), key=lambda r: engagements(r) / exposure(r), reverse=True)
        entry["best_posts"] = [{"text": ((store.posts.get(r.get("post_id")) or {}).get("hook") or r.get("text", ""))[:120],
                                "format": r["format"], "engagement_per_reach": round(engagements(r) / exposure(r), 4)}
                               for r in ranked[:3]]
        out["by_platform"][platform] = entry
    out["note"] = f"Groups with fewer than {MIN_POSTS} posts are left out; treat small differences as noise."
    return out


def hub_analytics(cfg: Config, store: Store, analytics: Analytics, today: str, weeks: int = 12) -> dict:
    """Weekly series and per-post rows for the hub's Analytics screen.

    The page sums these for whatever account/platform filter and week the viewer picks, so the
    numbers on screen always add up to the rows in the table.
    """
    this_monday = date.fromisoformat(today) - timedelta(days=date.fromisoformat(today).weekday())
    starts = [this_monday - timedelta(weeks=w) for w in range(weeks - 1, -1, -1)]
    series = []
    pairs = sorted({(r["account"], r["platform"]) for r in analytics.posts.values()} |
                   {(f["account"], f["platform"]) for f in analytics.followers})
    for ws in starts:
        start, end = ws.isoformat(), (ws + timedelta(days=6)).isoformat()
        for account, platform in pairs:
            recs = analytics.in_range(start, end, account, platform)
            in_week = [f for f in analytics.followers if f["account"] == account and f["platform"] == platform
                       and start <= f["date"] <= end]
            before = analytics.followers_at(account, platform, (ws - timedelta(days=1)).isoformat())
            after = analytics.followers_at(account, platform, end)
            change = (after - before) if (in_week and before is not None and after is not None) else None
            if not recs and change is None:
                continue
            with_clicks = [r for r in recs if r.get("link_clicks") is not None]
            series.append({
                "week": start, "account": account, "platform": platform, "posts": len(recs),
                "impressions": sum(exposure(r) or 0 for r in recs),
                "engagements": sum(engagements(r) for r in recs),
                "clicks": sum(r["link_clicks"] for r in with_clicks),
                "click_base": sum(exposure(r) or 0 for r in with_clicks),
                "follower_change": change,
            })
    rows = []
    for r in sorted(analytics.posts.values(), key=lambda r: r["posted_at"], reverse=True)[:400]:
        base = exposure(r) or 0
        planned = store.posts.get(r.get("post_id")) or {}
        rows.append({
            "date": r["date"], "time": r["posted_at"][11:16], "account": r["account"],
            "account_name": cfg.accounts.get(r["account"], {}).get("name", r["account"]),
            "platform": r["platform"], "format": r["format"], "post_id": r.get("post_id"),
            "text": (planned.get("hook") or r.get("text") or "")[:140], "permalink": r.get("permalink", ""),
            "impressions": base, "engagements": engagements(r),
            "er": engagements(r) / base if base else None,
            "clicks": r.get("link_clicks"), "ctr": (r["link_clicks"] / base) if base and r.get("link_clicks") is not None else None,
            "shares": r.get("shares"), "saves": r.get("saves"),
        })
    return {"generated_at": datetime.now().isoformat(timespec="seconds"), "has_data": bool(analytics.posts),
            "weeks": [ws.isoformat() for ws in starts], "series": series, "posts": rows,
            "note": "Reach is used where the platform reports it; impressions otherwise. CTR only counts posts whose export includes link clicks."}
