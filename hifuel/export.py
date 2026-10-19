"""Exports for scheduling: a CSV calendar (opens in Google Sheets/Excel), an .ics calendar file
(reminders in Google/Outlook calendar) and a copy-ready caption document."""

import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .models import publish_text

PLATFORM_NAMES = {"instagram": "Instagram", "linkedin": "LinkedIn", "facebook": "Facebook",
                  "whatsapp_channel": "WhatsApp Channel", "x": "X"}


def _where_to_post(post: dict) -> str:
    if post["account_type"] == "person":
        return f"{post['account_name']} posts from their own profile"
    if post.get("collab_with"):
        return "Post manually (Instagram Collab)"
    if post["platform"] in {"instagram", "facebook"}:
        return "Meta Business Suite"
    if post["platform"] == "linkedin":
        return "LinkedIn Page scheduler"
    return "Post manually"


def write_csv(posts: list[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:  # BOM so Excel reads ₹ correctly
        w = csv.writer(f)
        w.writerow(["Date", "Time (IST)", "Account", "Platform", "Format", "Theme", "Pillar", "Status",
                    "Post text", "Alt text", "Where to post", "Time source", "Blocking issues", "Reviewer flags", "Post ID"])
        for p in posts:
            blocks = [i["message"] for i in p.get("issues", []) if i["severity"] == "block"]
            flags = [i["message"] for i in p.get("issues", []) if i["severity"] == "flag"]
            text = "\n\n---\n\n".join(p["thread_parts"]) if p.get("thread_parts") else publish_text(p)
            w.writerow([p["date"], p.get("time", ""), p["account_name"], PLATFORM_NAMES[p["platform"]], p["format"],
                        p["theme"], p["pillar"], p["status"], text, p.get("alt_text", ""), _where_to_post(p),
                        p.get("slot_reason", ""), "\n".join(blocks), "\n".join(flags), p["id"]])
    return path


def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _fold(line: str) -> str:
    """iCalendar lines must be folded at 75 octets."""
    out, current = [], b""
    for ch in line:
        b = ch.encode("utf-8")
        if len(current) + len(b) > 74:
            out.append(current.decode("utf-8"))
            current = b" " + b
        else:
            current += b
    out.append(current.decode("utf-8"))
    return "\r\n".join(out)


def write_ics(posts: list[dict], path: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Hi Fuel group//Social Planner//EN", "CALSCALE:GREGORIAN",
             "BEGIN:VTIMEZONE", "TZID:Asia/Kolkata", "BEGIN:STANDARD", "DTSTART:19700101T000000",
             "TZOFFSETFROM:+0530", "TZOFFSETTO:+0530", "TZNAME:IST", "END:STANDARD", "END:VTIMEZONE"]
    for p in posts:
        start = datetime.fromisoformat(f"{p['date']}T{p.get('time') or '10:00'}")
        end = start + timedelta(minutes=15)
        summary = f"[{p['account_name']}] {PLATFORM_NAMES[p['platform']]} {p['format']}: {p['hook'][:60]}"
        desc = f"{publish_text(p)}\n\nWhere: {_where_to_post(p)}\nStatus: {p['status']}\nID: {p['id']}"
        lines += ["BEGIN:VEVENT", f"UID:{p['id']}@hifuel-planner", f"DTSTAMP:{stamp}",
                  f"DTSTART;TZID=Asia/Kolkata:{start:%Y%m%dT%H%M%S}", f"DTEND;TZID=Asia/Kolkata:{end:%Y%m%dT%H%M%S}",
                  f"SUMMARY:{_ics_escape(summary)}", f"DESCRIPTION:{_ics_escape(desc)}",
                  "BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:Time to post", "TRIGGER:-PT15M", "END:VALARM",
                  "END:VEVENT"]
    lines.append("END:VCALENDAR")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\r\n".join(_fold(l) for l in lines) + "\r\n", encoding="utf-8")
    return path


def write_captions(posts: list[dict], path: Path) -> Path:
    out = ["# Copy-ready posts", ""]
    current = None
    for p in posts:
        if p["date"] != current:
            current = p["date"]
            out += [f"## {datetime.fromisoformat(current):%A %d %B %Y}", ""]
        out += [f"### {p.get('time', '')} IST · {p['account_name']} · {PLATFORM_NAMES[p['platform']]} · {p['format']}",
                f"_Where: {_where_to_post(p)} · Status: {p['status']}_", ""]
        if p.get("personalise_prompt"):
            out += [f"> **Make it yours:** {p['personalise_prompt']}", ""]
        if p.get("thread_parts"):
            out += [f"**{i + 1}/{len(p['thread_parts'])}** {part}\n" for i, part in enumerate(p["thread_parts"])]
        else:
            out += ["```", publish_text(p), "```", ""]
        if p.get("alt_text"):
            out += [f"**Alt text:** {p['alt_text']}", ""]
        brief = p.get("design_brief") or {}
        if brief.get("slides"):
            out += ["**Slides:**"] + [f"{s['number']}. {s['text']} _(visual: {s['visual']})_" for s in brief["slides"]] + [""]
        reel = brief.get("reel") or {}
        if reel.get("shots"):
            out += [f"**Reel ({reel['duration_seconds']} s). Opening hook:** {reel['opening_hook']}"]
            out += [f"- {s['seconds']}s: {s['shot']} | on screen: {s['on_screen_text']} | VO: {s['voiceover']}"
                    for s in reel["shots"]] + [""]
        if brief.get("layout_notes") or brief.get("colours"):
            out += [f"**Design:** {brief.get('layout_notes', '')} Colours: {', '.join(brief.get('colours') or []) or 'n/a'}", ""]
        out += ["---", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out), encoding="utf-8")
    return path
