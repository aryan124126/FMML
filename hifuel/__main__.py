"""Command line for the Hi Fuel social planner.

  python -m hifuel plan --start 2026-10-26 [--days 7] [--accounts pathvik,iclc] [--campaign "..."] [--notes "..."]
  python -m hifuel list [--start ...] [--days ...] [--status draft]
  python -m hifuel show <post-id>
  python -m hifuel status <post-id> approved --by "Manager" [--comment "..."]
  python -m hifuel check                      re-run the claims check on every post
  python -m hifuel export --start ... [--days ...] [--status approved,scheduled]
  python -m hifuel hub-push [--start ... --days ...]
  python -m hifuel hub-pull <folder>
  python -m hifuel import <plan.yaml|plan.json> [--sample]   load drafts written outside the API
  python -m hifuel request <account> --start ...   show what would be sent to Claude
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from . import export, hub
from .config import load_config
from .models import publish_text
from .planner import PlanningError, dump_request, import_plan, plan_period, recheck_all
from .store import Store


def _next_monday() -> date:
    today = date.today()
    return today + timedelta(days=(7 - today.weekday()) % 7 or 7)


def _range(args) -> tuple[str, str]:
    start = date.fromisoformat(args.start) if args.start else _next_monday()
    return start.isoformat(), (start + timedelta(days=args.days - 1)).isoformat()


def _summary_line(p: dict) -> str:
    blocks = sum(i["severity"] == "block" for i in p.get("issues", []))
    flags = sum(i["severity"] == "flag" for i in p.get("issues", []))
    mark = f"BLOCKED({blocks})" if blocks else f"flags:{flags}"
    return f"{p['date']} {p.get('time', ''):5} {p['account']:20} {p['platform']:16} {p['status']:13} {mark:11} {p['hook'][:60]}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m hifuel", description="Hi Fuel group social media planner")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def with_range(p, days=7):
        p.add_argument("--start", help="YYYY-MM-DD (default: next Monday)")
        p.add_argument("--days", type=int, default=days)

    p = sub.add_parser("plan", help="draft posts with Claude")
    with_range(p)
    p.add_argument("--accounts", help="comma-separated account ids (default: all enabled)")
    p.add_argument("--campaign", action="append", default=[], help="a goal or campaign; repeat for more")
    p.add_argument("--notes", default="", help="anything else the planner should know")

    p = sub.add_parser("list", help="list posts")
    with_range(p)
    p.add_argument("--status")

    p = sub.add_parser("show", help="show one post in full")
    p.add_argument("id")

    p = sub.add_parser("status", help="change a post's status")
    p.add_argument("id")
    p.add_argument("status")
    p.add_argument("--by", required=True)
    p.add_argument("--comment", default="")

    sub.add_parser("check", help="re-run the claims check on every post")

    p = sub.add_parser("export", help="CSV, .ics and caption doc for scheduling")
    with_range(p)
    p.add_argument("--status", default="approved", help="comma-separated statuses to include")

    p = sub.add_parser("hub-push", help="prepare files to load into the Team Hub")
    p.add_argument("--start")
    p.add_argument("--days", type=int, default=0, help="0 = all posts")

    p = sub.add_parser("hub-pull", help="apply reviewers' changes downloaded from the Team Hub")
    p.add_argument("folder")

    p = sub.add_parser("import", help="load a plan file (YAML or JSON) through the same checks")
    p.add_argument("file")
    p.add_argument("--sample", action="store_true", help="mark the posts as samples")

    p = sub.add_parser("request", help="show what would be sent to Claude for one account")
    p.add_argument("account")
    with_range(p)

    args = ap.parse_args(argv)
    cfg, store = load_config(), Store()

    if args.cmd == "plan":
        start = date.fromisoformat(args.start) if args.start else _next_monday()
        accounts = args.accounts.split(",") if args.accounts else None
        try:
            plan = plan_period(cfg, store, start, args.days, accounts, args.campaign, args.notes)
        except PlanningError as e:
            print(f"Planning stopped: {e}")
            return 1
        print(f"\nPlanned {len(plan['post_ids'])} posts for {plan['start']} to {plan['end']} "
              f"(estimated API cost ${plan['cost_usd']:.2f}).")
        for q in plan["questions_for_team"]:
            print(f"  ? {q}")
    elif args.cmd == "list":
        start, end = _range(args)
        statuses = args.status.split(",") if args.status else None
        for p in store.in_range(start, end, statuses=statuses):
            print(_summary_line(p))
    elif args.cmd == "show":
        p = store.posts[args.id]
        print(_summary_line(p), "\n")
        print("\n\n".join(p["thread_parts"]) if p.get("thread_parts") else publish_text(p))
        print(f"\nTime: {p.get('slot_reason', '')}")
        for i in p.get("issues", []):
            print(f"  [{i['severity'].upper()}] rule {i['rule']}: {i['message']}")
    elif args.cmd == "status":
        try:
            store.set_status(args.id, args.status, args.by, args.comment)
        except ValueError as e:
            print(e)
            return 1
        store.save()
        print(f"{args.id} -> {args.status}")
    elif args.cmd == "check":
        print(f"Re-checked; {recheck_all(cfg, store)} post(s) changed.")
    elif args.cmd == "export":
        start, end = _range(args)
        posts = store.in_range(start, end, statuses=args.status.split(","))
        if not posts:
            print(f"No posts with status {args.status} between {start} and {end}.")
            return 1
        out = Path("data/exports")
        for path in (export.write_csv(posts, out / f"calendar_{start}_{end}.csv"),
                     export.write_ics(posts, out / f"calendar_{start}_{end}.ics"),
                     export.write_captions(posts, out / f"captions_{start}_{end}.md")):
            print(f"Wrote {path}")
    elif args.cmd == "hub-push":
        ids = None
        if args.start and args.days:
            start, end = _range(args)
            ids = [p["id"] for p in store.in_range(start, end)]
        files = hub.push(store, Path("data/hub_outbox"), ids)
        print(f"Wrote {len(files)} files to data/hub_outbox/")
    elif args.cmd == "hub-pull":
        changes = hub.pull(store, cfg, Path(args.folder))
        print("\n".join(changes) or "No changes from the hub.")
    elif args.cmd == "import":
        text = Path(args.file).read_text(encoding="utf-8")
        data = yaml.safe_load(text) if args.file.endswith((".yaml", ".yml")) else json.loads(text)
        try:
            plan = import_plan(cfg, store, data, sample=args.sample)
        except PlanningError as e:
            print(e)
            return 1
        for pid in plan["post_ids"]:
            print(_summary_line(store.posts[pid]))
    elif args.cmd == "request":
        start = date.fromisoformat(args.start) if args.start else _next_monday()
        print(dump_request(cfg, store, args.account, start, args.days))
    return 0


if __name__ == "__main__":
    sys.exit(main())
