"""Performance data (Phase 2): CSV imports, manual entries, follower counts, audience hours, enquiries.

Everything is stored in data/analytics.json. Imported posts are matched to the posts we planned,
so results can be read by theme, pillar, format and time slot.
"""

import csv
import difflib
import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

import yaml

from .config import CONFIG_DIR
from .store import DATA_DIR, Store

IST = timedelta(hours=5, minutes=30)
DATE_FORMATS = {
    "mdy": ["%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y", "%m-%d-%Y %H:%M", "%m-%d-%Y"],
    "dmy": ["%d/%m/%Y %H:%M", "%d/%m/%Y %I:%M %p", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y", "%d-%m-%Y %H:%M", "%d-%m-%Y"],
    "iso": ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"],
}
NUMERIC = ["reach", "impressions", "likes", "comments", "shares", "saves", "follows", "profile_visits",
           "link_clicks", "avg_watch_seconds", "completion_rate", "non_follower_reach"]


class AnalyticsError(Exception):
    pass


def load_columns(base: Path = CONFIG_DIR) -> dict:
    return yaml.safe_load((base / "analytics_columns.yaml").read_text(encoding="utf-8"))


# ---------- parsing ----------

def _number(value):
    if value is None:
        return None
    s = str(value).strip().replace(",", "").replace("%", "")
    if s in {"", "-", "--", "n/a", "N/A"}:
        return None
    try:
        n = float(s)
    except ValueError:
        return None
    return int(n) if n.is_integer() else n


def detect_date_order(values: list[str]) -> str:
    """Work out whether slash dates are month/day or day/month by looking at every row."""
    first, second = set(), set()
    for v in values:
        m = re.match(r"\s*(\d{1,2})[/-](\d{1,2})[/-]\d{4}", v or "")
        if m:
            first.add(int(m.group(1)))
            second.add(int(m.group(2)))
        elif re.match(r"\s*\d{4}-\d{2}-\d{2}", v or ""):
            return "iso"
    if any(n > 12 for n in first):
        return "dmy"
    if any(n > 12 for n in second):
        return "mdy"
    if not first:
        return "iso"
    raise AnalyticsError("Can't tell whether dates are day/month or month/day. Re-run with --date-order dmy or mdy.")


def parse_datetime(value: str, order: str, file_offset_hours: float = 5.5) -> datetime:
    """Parse a timestamp and return it in IST (naive)."""
    v = (value or "").strip()
    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if dt.tzinfo:
            return (dt - dt.utcoffset() + IST).replace(tzinfo=None)
    except ValueError:
        dt = None
    if dt is None:
        for fmt in DATE_FORMATS[order] + DATE_FORMATS["iso"]:
            try:
                dt = datetime.strptime(v, fmt)
                break
            except ValueError:
                continue
    if dt is None:
        raise AnalyticsError(f"Couldn't read the date '{value}'.")
    return dt + (IST - timedelta(hours=file_offset_hours))


def normalise_format(value: str, mapping: dict) -> str:
    v = (value or "").strip().lower()
    for fmt, aliases in mapping.items():
        if v in aliases:
            return fmt
    return v or "unknown"


def read_export(path: Path, columns: dict, date_order: str = "auto", file_offset_hours: float = 5.5) -> list[dict]:
    """Read a CSV export into normalised rows (one per post)."""
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    # Some exports put a title or notes above the header row: start at the first line that has a date column.
    aliases = {a for names in columns["fields"].values() for a in names}
    start = next((i for i, line in enumerate(lines[:10])
                  if sum(cell.strip().lower() in aliases for cell in next(csv.reader([line]))) >= 2), 0)
    reader = csv.DictReader(lines[start:])
    headers = {h.strip().lower(): h for h in reader.fieldnames or []}
    found = {}
    for field, names in columns["fields"].items():
        for name in names:
            if name in headers:
                found[field] = headers[name]
                break
    if "posted_at" not in found:
        raise AnalyticsError(f"No date column found. Columns in the file: {', '.join(headers.values())}. "
                           "Add the date column's name to config/analytics_columns.yaml.")
    if "reach" not in found and "impressions" not in found:
        raise AnalyticsError("No reach or impressions column found; add its name to config/analytics_columns.yaml.")
    raw = [r for r in reader if any((v or "").strip() for v in r.values())]
    order = detect_date_order([r[found["posted_at"]] for r in raw]) if date_order == "auto" else date_order
    rows = []
    for r in raw:
        posted = parse_datetime(r[found["posted_at"]], order, file_offset_hours)
        row = {"posted_at": posted.strftime("%Y-%m-%dT%H:%M"),
               "external_id": (r.get(found.get("external_id", ""), "") or "").strip(),
               "text": (r.get(found.get("text", ""), "") or "").strip()[:300],
               "permalink": (r.get(found.get("permalink", ""), "") or "").strip(),
               "format": normalise_format(r.get(found.get("format", ""), ""), columns["formats"])}
        for field in NUMERIC:
            row[field] = _number(r.get(found[field])) if field in found else None
        rows.append(row)
    return rows


# ---------- storage ----------

def engagements(rec: dict) -> int:
    return sum(rec.get(k) or 0 for k in ("likes", "comments", "shares", "saves"))


def exposure(rec: dict):
    """Reach where the platform reports it; impressions otherwise (LinkedIn pages, personal posts)."""
    return rec.get("reach") or rec.get("impressions")


class Analytics:
    def __init__(self, data_dir: Path | None = None):
        self.dir = Path(data_dir or DATA_DIR)
        self.file = self.dir / "analytics.json"
        data = json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}
        self.posts: dict[str, dict] = data.get("posts", {})
        self.followers: list[dict] = data.get("followers", [])
        self.audience: dict = data.get("audience", {})
        self.enquiries: list[dict] = data.get("enquiries", [])
        self.experiments: dict[str, dict] = data.get("experiments", {})

    def save(self) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps({"posts": self.posts, "followers": self.followers, "audience": self.audience,
                                   "enquiries": self.enquiries, "experiments": self.experiments},
                                  indent=1, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.file)

    # --- posts ---
    def add_rows(self, rows: list[dict], account: str, platform: str, store: Store | None = None,
                 source: str = "") -> dict:
        added = updated = matched = 0
        for row in rows:
            rec = {**row, "account": account, "platform": platform, "source": source}
            dt = datetime.fromisoformat(rec["posted_at"])
            rec.update(date=dt.date().isoformat(), weekday=dt.weekday(), hour=dt.hour)
            slug = re.sub(r"\W+", "", rec.get("text", ""))[:24]
            key = (f"{platform}:{rec['external_id']}" if rec.get("external_id")
                   else f"{account}:{platform}:{rec['posted_at']}:{slug}")
            if store:
                plan = match_planned(rec, store)
                if plan:
                    matched += 1
                    rec.update(post_id=plan["id"], theme=plan["theme"], pillar=plan["pillar"],
                               idea_id=plan["idea_id"], planned_format=plan["format"])
                    if rec["format"] in {"unknown", ""}:
                        rec["format"] = plan["format"]
            if key in self.posts:
                updated += 1
            else:
                added += 1
            self.posts[key] = rec
        return {"added": added, "updated": updated, "matched": matched}

    def in_range(self, start: str, end: str, account: str | None = None, platform: str | None = None) -> list[dict]:
        return sorted((r for r in self.posts.values() if start <= r["date"] <= end
                       and (not account or r["account"] == account) and (not platform or r["platform"] == platform)),
                      key=lambda r: r["posted_at"])

    # --- followers, audience, enquiries ---
    def add_followers(self, account: str, platform: str, day: str, count: int) -> None:
        self.followers = [f for f in self.followers
                          if not (f["account"] == account and f["platform"] == platform and f["date"] == day)]
        self.followers.append({"account": account, "platform": platform, "date": day, "followers": count})
        self.followers.sort(key=lambda f: f["date"])

    def followers_at(self, account: str, platform: str, day: str):
        """Follower count on a day: the latest snapshot on or before it, else the earliest after it."""
        snaps = [f for f in self.followers if f["account"] == account and f["platform"] == platform]
        before = [f for f in snaps if f["date"] <= day]
        if before:
            return before[-1]["followers"]
        return snaps[0]["followers"] if snaps else None

    def set_audience(self, account: str, platform: str, hours: dict, as_of: str) -> None:
        self.audience.setdefault(account, {})[platform] = {"as_of": as_of, "hours": {str(int(h)): v for h, v in hours.items()}}

    def audience_data(self, today: str, max_age_days: int = 45) -> dict:
        """Online-follower hours that are recent enough to trust, in the slot engine's shape."""
        out = {}
        cutoff = (date.fromisoformat(today) - timedelta(days=max_age_days)).isoformat()
        for account, by_platform in self.audience.items():
            for platform, entry in by_platform.items():
                if entry["as_of"] >= cutoff and entry["hours"]:
                    out.setdefault(account, {})[platform] = entry["hours"]
        return out

    def add_enquiry(self, account: str, day: str, count: int, note: str = "") -> None:
        self.enquiries.append({"account": account, "date": day, "count": count, "note": note})

    def enquiries_in(self, start: str, end: str, account: str) -> int:
        return sum(e["count"] for e in self.enquiries if e["account"] == account and start <= e["date"] <= end)

    # --- for the slot engine ---
    def history(self) -> list[dict]:
        """Past posts in the shape slots.history_scores expects."""
        rows = []
        for rec in self.posts.values():
            base = exposure(rec)
            if not base:
                continue
            followers = self.followers_at(rec["account"], rec["platform"], rec["date"])
            has_any = any(f["account"] == rec["account"] and f["platform"] == rec["platform"] for f in self.followers)
            rows.append({"account": rec["account"], "platform": rec["platform"], "weekday": rec["weekday"],
                         "hour": rec["hour"], "reach": base, "engagements": engagements(rec),
                         # Without follower counts every post uses 1, so slots still compare fairly within an account.
                         "followers": followers if has_any and followers else 1, "format": rec["format"]})
        return rows


def match_planned(rec: dict, store: Store):
    """The planned post this result belongs to: same account, platform and day, closest in text and time."""
    candidates = [p for p in store.posts.values() if p["account"] == rec["account"]
                  and p["platform"] == rec["platform"] and p["date"] == rec["date"]]
    if not candidates:
        return None
    posted = datetime.fromisoformat(rec["posted_at"])

    def score(p):
        hook = (p.get("hook") or "").lower()[:80]
        text_sim = difflib.SequenceMatcher(None, hook, (rec.get("text") or "").lower()[:80]).ratio() if rec.get("text") else 0
        planned = datetime.fromisoformat(f"{p['date']}T{p.get('time') or '12:00'}")
        hours_off = abs((posted - planned).total_seconds()) / 3600
        return text_sim * 2 + max(0, 1 - hours_off / 6)

    best = max(candidates, key=score)
    return best if score(best) >= 0.6 else None
