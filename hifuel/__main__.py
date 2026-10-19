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
  python -m hifuel remove-samples                delete sample posts

Phase 2 (results):
  python -m hifuel analytics import <export.csv> --account pathvik --platform instagram [--date-order dmy]
  python -m hifuel analytics followers --account pathvik --platform instagram --date 2026-11-02 --count 1840
  python -m hifuel analytics audience --account pathvik --platform instagram --file online_followers.csv
  python -m hifuel analytics enquiry --account iclc --date 2026-11-02 --count 2 --note "two schools via LinkedIn"
  python -m hifuel analytics list [--start ...] [--days ...]
  python -m hifuel report weekly [--start ...]      python -m hifuel report monthly --month 2026-11
  python -m hifuel experiment add --name ... --hypothesis ... --account ... --variable format --value carousel
  python -m hifuel experiment list | experiment close <id> [--note ...]
  python -m hifuel request <account> --start ...   show what would be sent to Claude
"""

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import yaml

from . import experiments as exps
from . import export, hub, reports
from .analytics import Analytics, AnalyticsError, read_export, load_columns
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

    p = sub.add_parser("remove-samples", help="delete all sample posts")

    an = sub.add_parser("analytics", help="import and record results").add_subparsers(dest="sub", required=True)
    p = an.add_parser("import", help="import a CSV export of post results")
    p.add_argument("file")
    p.add_argument("--account", required=True)
    p.add_argument("--platform", required=True)
    p.add_argument("--date-order", default="auto", choices=["auto", "mdy", "dmy", "iso"])
    p.add_argument("--tz-offset", type=float, default=5.5, help="hours from UTC of the times in the file (IST = 5.5)")
    p = an.add_parser("followers", help="record a follower count")
    for a in ("--account", "--platform", "--date"):
        p.add_argument(a, required=True)
    p.add_argument("--count", type=int, required=True)
    p = an.add_parser("audience", help="when followers are online: CSV with hour,followers")
    p.add_argument("--account", required=True)
    p.add_argument("--platform", required=True)
    p.add_argument("--file", required=True)
    p.add_argument("--as-of", default=date.today().isoformat())
    p = an.add_parser("enquiry", help="record inbound enquiries that came from social")
    p.add_argument("--account", required=True)
    p.add_argument("--date", required=True)
    p.add_argument("--count", type=int, required=True)
    p.add_argument("--note", default="")
    p = an.add_parser("list", help="list imported results")
    with_range(p, days=28)

    rp = sub.add_parser("report", help="weekly or monthly report").add_subparsers(dest="sub", required=True)
    p = rp.add_parser("weekly")
    p.add_argument("--start", help="Monday YYYY-MM-DD (default: last week)")
    p = rp.add_parser("monthly")
    p.add_argument("--month", help="YYYY-MM (default: last month)")

    ex = sub.add_parser("experiment", help="experiment log").add_subparsers(dest="sub", required=True)
    p = ex.add_parser("add")
    p.add_argument("--name", required=True)
    p.add_argument("--hypothesis", required=True)
    p.add_argument("--account", required=True)
    p.add_argument("--variable", required=True, choices=sorted(exps.VARIABLES))
    p.add_argument("--value", required=True)
    p.add_argument("--metric", default="engagement_rate", choices=list(exps.METRICS))
    p.add_argument("--platform", default="")
    p.add_argument("--start", default="")
    p.add_argument("--weeks", type=int, default=4)
    ex.add_parser("list")
    p = ex.add_parser("close")
    p.add_argument("id")
    p.add_argument("--note", default="")

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
        out = Path("data/hub_outbox")
        files = hub.push(store, out, ids) + hub.push_reports(Analytics(), Path("data/reports"), out)
        print(f"Wrote {len(files)} files to data/hub_outbox/")
    elif args.cmd == "hub-pull":
        changes = hub.pull(store, cfg, Path(args.folder))
        changes += hub.pull_extras(store, Analytics(), Path(args.folder))
        print("\n".join(changes) or "No changes from the hub.")
    elif args.cmd == "analytics":
        return _analytics(args, cfg, store)
    elif args.cmd == "report":
        return _report(args, cfg, store)
    elif args.cmd == "experiment":
        return _experiment(args, store)
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
    elif args.cmd == "remove-samples":
        ids = [pid for pid, p in store.posts.items() if p.get("sample")]
        plan_ids = set(store.plans)
        store.remove(ids, by="cli")
        store.save()
        print(f"Removed {len(ids)} sample posts. Delete these from the Team Hub too:")
        print("\n".join([f"posts/{i}" for i in ids] + [f"plans/{p}" for p in plan_ids - set(store.plans)]))
    elif args.cmd == "request":
        start = date.fromisoformat(args.start) if args.start else _next_monday()
        print(dump_request(cfg, store, args.account, start, args.days))
    return 0


def _analytics(args, cfg, store) -> int:
    an = Analytics()
    if args.sub != "list" and args.account not in cfg.accounts:
        print(f"Unknown account {args.account}. Known: {', '.join(cfg.accounts)}")
        return 1
    if args.sub == "import":
        try:
            rows = read_export(Path(args.file), load_columns(), args.date_order, args.tz_offset)
        except AnalyticsError as e:
            print(e)
            return 1
        result = an.add_rows(rows, args.account, args.platform, store, source=Path(args.file).name)
        print(f"{result['added']} new, {result['updated']} updated, {result['matched']} matched to planned posts.")
    elif args.sub == "followers":
        an.add_followers(args.account, args.platform, args.date, args.count)
        print(f"Recorded {args.count:,} followers for {args.account} {args.platform} on {args.date}.")
    elif args.sub == "audience":
        import csv
        with open(args.file, encoding="utf-8-sig") as f:
            hours = {int(r[0]): float(r[1]) for r in csv.reader(f) if r and r[0].strip().isdigit()}
        an.set_audience(args.account, args.platform, hours, args.as_of)
        print(f"Recorded online-follower hours for {args.account} {args.platform} ({len(hours)} hours).")
    elif args.sub == "enquiry":
        an.add_enquiry(args.account, args.date, args.count, args.note)
        print("Recorded.")
    elif args.sub == "list":
        start, end = _range(args)
        for r in an.in_range(start, end):
            base = r.get("reach") or r.get("impressions") or 0
            eng = sum(r.get(k) or 0 for k in ("likes", "comments", "shares", "saves"))
            print(f"{r['posted_at']} {r['account']:20} {r['platform']:10} {r['format']:13} "
                  f"{base:>8,} {eng / base if base else 0:6.1%}  {'planned' if r.get('post_id') else 'unmatched'}")
        return 0
    an.save()
    return 0


def _report(args, cfg, store) -> int:
    today = date.today()
    if args.sub == "weekly":
        start = date.fromisoformat(args.start) if args.start else today - timedelta(days=today.weekday() + 7)
        start_s, end_s = start.isoformat(), (start + timedelta(days=6)).isoformat()
    else:
        month = args.month or (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")
        start_s, end_s = reports.month_range(month)
    report = reports.build_report(cfg, store, Analytics(), start_s, end_s, args.sub)
    out = Path("data/reports")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{report['id']}.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    md = out / f"{report['id']}.md"
    md.write_text(reports.render_markdown(report), encoding="utf-8")
    print(reports.render_markdown(report))
    print(f"\nSaved {md}")
    return 0


def _experiment(args, store) -> int:
    an = Analytics()
    if args.sub == "add":
        try:
            e = exps.add(an, args.name, args.hypothesis, args.account, args.variable, args.value,
                         args.metric, args.platform, args.start, args.weeks)
        except ValueError as err:
            print(err)
            return 1
        print(f"Started '{e['name']}' ({e['id']}), {e['start']} to {e['end']}.")
    elif args.sub == "list":
        for e in an.experiments.values():
            res = exps.evaluate(an, e, store.posts)["summary"] if e["status"] == "running" else e["result"]
            print(f"[{e['status']}] {e['id']}: {e['name']} ({e['account']}, {e['start']} to {e['end']})\n    {res}")
        return 0
    elif args.sub == "close":
        if args.id not in an.experiments:
            print(f"No experiment {args.id}.")
            return 1
        e = exps.close(an, args.id, store.posts, args.note)
        print(f"Closed: {e['result']}")
    an.save()
    return 0


if __name__ == "__main__":
    sys.exit(main())
