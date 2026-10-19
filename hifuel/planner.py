"""Plans a period of posts with Claude, then runs the slot engine and the claims check.

Accounts are planned one at a time (highest priority first). Each call sees the ideas already
planned this period, so it can repurpose an idea for its own audience instead of duplicating it.
"""

import json
from datetime import date, timedelta

import anthropic
import yaml

from .claims import check_post, is_blocked
from .config import Config, load_prompt
from .models import WeekPlan
from .slots import assign_slots
from .store import Store

MODEL = "claude-opus-5-5"
EFFORT = "high"  # content quality matters more than speed here
# Claude Opus 5.5 prices per million tokens (USD), for the cost estimate shown after each run.
PRICE_IN, PRICE_OUT, PRICE_CACHE_READ, PRICE_CACHE_WRITE = 4.00, 20.00, 0.20, 5.00


class PlanningError(Exception):
    pass


def _days(start: date, days: int) -> list[str]:
    return [(start + timedelta(days=i)).isoformat() for i in range(days)]


def _calendar_context(cfg: Config, account_id: str, start: str, end: str) -> dict:
    dates = [d for d in cfg.key_dates.get("dates", [])
             if start <= str(d["date"]) <= end or start <= str(d.get("until", "")) <= end]
    months = {int(start[5:7]), int(end[5:7])}
    seasons = [s for s in cfg.key_dates.get("seasons", [])
               if account_id in s["accounts"] and months & set(s["months"])]
    return {"key_dates": [{**d, "date": str(d["date"])} for d in dates], "seasons": seasons}


def build_request(cfg: Config, store: Store, account_id: str, start: str, end: str,
                  campaigns: list[str], notes: str, planned_ideas: list[dict]) -> str:
    """The user message for one account. Kept separate so it can be tested and inspected."""
    account = cfg.account(account_id)
    existing = store.in_range(start, end, accounts=[account_id])
    context = {
        "planning_period": {"start": start, "end": end, "days": _days(date.fromisoformat(start),
                                                                       (date.fromisoformat(end) - date.fromisoformat(start)).days + 1)},
        "account_id": account_id,
        "account": account,
        "platforms": {p: {"posts_this_period": n, **cfg.platforms[p]} for p, n in account.get("platforms", {}).items()},
        "campaigns_and_goals": campaigns,
        "notes_from_team": notes,
        "calendar": _calendar_context(cfg, account_id, start, end),
        "already_planned_for_this_account": [
            {"date": p["date"], "platform": p["platform"], "hook": p["hook"], "status": p["status"]} for p in existing],
        "ideas_already_planned_for_other_accounts": planned_ideas,
        "recent_human_edits_learn_from_these": store.recent_edits(account_id),
    }
    if account.get("parent"):
        context["parent_account"] = {"id": account["parent"], "name": cfg.account(account["parent"])["name"]}
    return (
        f"Plan posts for {account['name']} ({account_id}) from {start} to {end}.\n"
        "Write the number of posts per platform given in `platforms` (fewer if you can't make them correct). "
        "Don't repeat posts already planned. Reuse an idea_id from another account only when you adapt that "
        "idea for this audience.\n\n"
        "```yaml\n" + yaml.safe_dump(context, allow_unicode=True, sort_keys=False, width=110) + "```"
    )


def _call_claude(client, request: str):
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=64000,
        system=load_prompt("system.md"),
        messages=[{"role": "user", "content": request}],
        output_format=WeekPlan,
        output_config={"effort": EFFORT},
        cache_control={"type": "ephemeral"},
        # If Claude declines a request, retry on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        message = stream.get_final_message()
    if message.stop_reason == "refusal":
        raise PlanningError("Claude declined this request. Try rewording the campaign notes.")
    if message.stop_reason == "max_tokens":
        raise PlanningError("The plan was too long and got cut off. Plan fewer days or accounts at a time.")
    if message.parsed_output is None:
        raise PlanningError("Claude's reply couldn't be read as a plan. Try again.")
    return message.parsed_output, message.usage


def estimate_cost(usage) -> float:
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (usage.input_tokens * PRICE_IN + usage.output_tokens * PRICE_OUT
            + cache_read * PRICE_CACHE_READ + cache_write * PRICE_CACHE_WRITE) / 1_000_000


def finalise_posts(drafts: list[dict], cfg: Config, store: Store, start: str, end: str) -> list[dict]:
    """Give drafts ids and times, run the claims check, and save them."""
    valid = []
    for d in drafts:
        if not (start <= d["date"] <= end):
            continue  # outside the period: drop rather than guess a date
        if d["account"] not in cfg.accounts:
            continue
        d["id"] = store.new_id(d)
        valid.append(d)
    placed = [p for p in store.posts.values() if start <= p["date"] <= end]
    for post, slot in zip(valid, assign_slots(valid, cfg, already_placed=placed)):
        account = cfg.account(post["account"])
        post.update(slot)
        post["account_name"] = account["name"]
        post["account_type"] = account["type"]
        post["approver"] = account.get("approver", "manager")
        post["consent_confirmed"] = False
        post["issues"] = check_post(post, cfg)
        post["blocked"] = is_blocked(post["issues"])
        store.add(post)
    return valid


def plan_period(cfg: Config, store: Store, start: date, days: int = 7, accounts: list[str] | None = None,
                campaigns: list[str] | None = None, notes: str = "", client=None, on_progress=print) -> dict:
    client = client or anthropic.Anthropic()
    start_s, end_s = start.isoformat(), (start + timedelta(days=days - 1)).isoformat()
    accounts = accounts or cfg.enabled_accounts()
    accounts = sorted(accounts, key=lambda a: cfg.account(a).get("priority", 9))
    planned_ideas, summaries, questions, created, cost = [], {}, [], [], 0.0

    for account_id in accounts:
        if not cfg.account(account_id).get("platforms"):
            on_progress(f"Skipping {account_id}: no platforms configured.")
            continue
        on_progress(f"Planning {cfg.account(account_id)['name']}...")
        request = build_request(cfg, store, account_id, start_s, end_s, campaigns or [], notes, planned_ideas)
        plan, usage = _call_claude(client, request)
        cost += estimate_cost(usage)
        drafts = [p.model_dump() for p in plan.posts if p.account == account_id]
        posts = finalise_posts(drafts, cfg, store, start_s, end_s)
        store.save()  # save after each account so a later failure doesn't lose work
        created += posts
        summaries[account_id] = plan.summary
        questions += [f"[{account_id}] {q}" for q in plan.questions_for_team]
        planned_ideas += [{"idea_id": p["idea_id"], "account": account_id, "platform": p["platform"],
                           "date": p["date"], "hook": p["hook"]} for p in posts]
        on_progress(f"  {len(posts)} posts, {sum(p['blocked'] for p in posts)} blocked by the claims check.")

    plan_id = f"{start_s}_{end_s}"
    store.plans[plan_id] = {"id": plan_id, "start": start_s, "end": end_s, "summaries": summaries,
                            "questions_for_team": questions, "campaigns": campaigns or [], "notes": notes,
                            "post_ids": [p["id"] for p in created], "cost_usd": round(cost, 2)}
    store.log("plan", plan_id=plan_id, posts=len(created), cost_usd=round(cost, 2))
    store.save()
    return store.plans[plan_id]


def _with_defaults(post: dict) -> dict:
    """Fill fields a hand-written draft may leave out."""
    empty_brief = {"format_notes": "", "slides": [], "reel": {"duration_seconds": 0, "opening_hook": "", "shots": []},
                   "layout_notes": "", "colours": [], "image_prompt": ""}
    defaults = {"cta": "", "hashtags": [], "alt_text": "", "thread_parts": [], "personalise_prompt": "",
                "claims_notes": [], "uses_ai_media": False, "shows_children": False, "collab_with": "",
                "key_date": "", "internal_notes": "", "pillar": ""}
    out = {**defaults, **post}
    out["design_brief"] = {**empty_brief, **(post.get("design_brief") or {})}
    out["design_brief"]["reel"] = {**empty_brief["reel"], **out["design_brief"]["reel"]}
    return out


def import_plan(cfg: Config, store: Store, data: dict, sample: bool = False) -> dict:
    """Load a plan written outside the API (e.g. drafted by Claude in chat) through the same checks."""
    plan = WeekPlan(summary=data.get("summary", ""), questions_for_team=data.get("questions_for_team", []),
                    posts=[_with_defaults(p) for p in data["posts"]])
    drafts = [p.model_dump() for p in plan.posts]
    unknown = sorted({d["account"] for d in drafts} - set(cfg.accounts))
    if unknown:
        raise PlanningError(f"Unknown account(s): {', '.join(unknown)}")
    start = str(data.get("start") or min(d["date"] for d in drafts))
    end = str(data.get("end") or max(d["date"] for d in drafts))
    for d in drafts:
        d["sample"] = sample
    posts = finalise_posts(drafts, cfg, store, start, end)
    plan_id = f"{start}_{end}"
    previous = store.plans.get(plan_id, {})
    store.plans[plan_id] = {"id": plan_id, "start": start, "end": end,
                            "summaries": {**previous.get("summaries", {}), "_overview": plan.summary},
                            "questions_for_team": previous.get("questions_for_team", []) + plan.questions_for_team,
                            "campaigns": previous.get("campaigns", []), "notes": previous.get("notes", ""),
                            "post_ids": previous.get("post_ids", []) + [p["id"] for p in posts],
                            "cost_usd": previous.get("cost_usd", 0.0)}
    store.log("import", plan_id=plan_id, posts=len(posts), sample=sample)
    store.save()
    return store.plans[plan_id]


def recheck_all(cfg: Config, store: Store) -> int:
    """Re-run the claims check on every post (e.g. after editing rules or confirming facts)."""
    changed = 0
    for post in store.posts.values():
        issues = check_post(post, cfg)
        if issues != post.get("issues"):
            post["issues"], post["blocked"] = issues, is_blocked(issues)
            changed += 1
    store.save()
    return changed


def dump_request(cfg: Config, store: Store, account_id: str, start: date, days: int = 7) -> str:
    """For debugging: show exactly what Claude would be sent for one account."""
    end = start + timedelta(days=days - 1)
    return json.dumps({"system": load_prompt("system.md"),
                       "user": build_request(cfg, store, account_id, start.isoformat(), end.isoformat(), [], "", [])},
                      indent=2, ensure_ascii=False)
