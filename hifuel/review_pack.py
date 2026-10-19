"""A review pack people can read on their phone and answer over WhatsApp.

Each post gets a short code (P01, P02, ...). Reviewers reply with the code and OK / CHANGE / DROP,
and Claude applies the replies in chat. The pack is an HTML page that is printed to a PDF
(phone-sized pages) when Playwright is installed; the code-to-post mapping is saved next to it.
"""

import html
import json
from pathlib import Path

from .models import publish_text

PLATFORMS = {"instagram": "Instagram", "linkedin": "LinkedIn", "facebook": "Facebook",
             "whatsapp_channel": "WhatsApp Channel", "x": "X"}
FORMATS = {"text": "Text post", "single_image": "Image", "carousel": "Carousel", "reel": "Reel", "story": "Story",
           "document": "Document", "poll": "Poll", "channel_message": "Channel message", "thread": "Thread"}
APPROVER = {"founder": "the founder", "manager": "the manager", "self": "the post's author"}
VISUAL = {"single_image", "carousel", "reel", "story", "document"}
# Checks every post gets; listing them on every page only adds noise for reviewers.
QUIET_CHECKS = {"numbers", "hashtags", "alt_text"}

e = html.escape


def assign_codes(posts: list[dict], prefix: str) -> dict[str, str]:
    """Stable codes in date/time order: P01, P02, ..."""
    ordered = sorted(posts, key=lambda p: (p["date"], p.get("time") or "", p["id"]))
    width = max(2, len(str(len(ordered))))
    return {p["id"]: f"{prefix}{i:0{width}d}" for i, p in enumerate(ordered, 1)}


def _day(d: str) -> str:
    from datetime import date
    x = date.fromisoformat(d)
    return f"{x:%a} {x.day} {x:%b}"


def _visual(p: dict) -> str:
    if p["format"] not in VISUAL:
        return "", ""
    b = p.get("design_brief") or {}
    cs = [c for c in b.get("colours") or [] if isinstance(c, str) and c.startswith("#")]
    c1, c2 = (cs + ["#064e3b", "#0b3b2e"])[:2] if len(cs) != 1 else (cs[0], cs[0])
    reel = b.get("reel") or {}
    first = ((b.get("slides") or [{}])[0].get("text") or ((reel.get("shots") or [{}])[0].get("on_screen_text"))
             or p.get("hook", ""))
    tag = FORMATS.get(p["format"], p["format"]).upper()
    if p["format"] == "reel" and reel.get("duration_seconds"):
        tag += f" · {reel['duration_seconds']}s"
    if b.get("slides"):
        tag += f" · {len(b['slides'])} {'frames' if p['format'] == 'story' else 'slides'}"
    card = f'<div class="media" style="--c1:{e(c1)};--c2:{e(c2)}"><span class="tag">{e(tag)}</span><p>{e(first)}</p></div>'
    out = []
    rows = []
    for s in b.get("slides") or []:
        rows.append(f"<li><b>{e(str(s.get('number', '')))}.</b> {e(s.get('text', ''))} <span class=m>· {e(s.get('visual', ''))}</span></li>")
    for s in reel.get("shots") or []:
        vo = f" <span class=m>· says: “{e(s['voiceover'])}”</span>" if s.get("voiceover") else ""
        rows.append(f"<li><b>{e(s.get('seconds', ''))}s</b> {e(s.get('on_screen_text', ''))} <span class=m>· {e(s.get('shot', ''))}</span>{vo}</li>")
    if rows:
        label = "Reel, shot by shot" if reel.get("shots") else ("Frames" if p["format"] == "story" else "Slides")
        out.append(f'<div class="sec"><h3>{label}</h3><ol class="shots">{"".join(rows)}</ol></div>')
    return card, "".join(out)


def _checks(p: dict) -> str:
    items = []
    for i in p.get("issues") or []:
        if i.get("check") in QUIET_CHECKS:
            continue
        kind = "Must fix" if i["severity"] == "block" else "Check"
        items.append(f'<li class="{i["severity"]}"><b>{kind}:</b> {e(i["message"])}</li>')
    notes = p.get("internal_notes") or ""
    if "CONFIRM" in notes:
        items.append(f"<li class=flag><b>To confirm:</b> {e(notes)}</li>")
    if not items:
        return ""
    return f'<div class="sec"><h3>Please look at</h3><ul class="checks">{"".join(items)}</ul></div>'


def _post_page(p: dict, code: str, total: int) -> str:
    parts = p.get("thread_parts") or []
    if parts:
        body = "".join(f'<div class="text"><span class=m>Part {n} of {len(parts)}</span>\n{e(t)}</div>' for n, t in enumerate(parts, 1))
    else:
        body = f'<div class="text">{e(publish_text(p))}</div>'
    mine = (f'<div class="sec mine"><b>Make it yours:</b> {e(p["personalise_prompt"])}</div>'
            if p.get("personalise_prompt") else "")
    status = {"draft": "Draft", "needs_changes": "Needs changes", "approved": "Approved", "scheduled": "Scheduled",
              "posted": "Posted", "shell": "Brief (not written yet)"}.get(p["status"], p["status"])
    card, shots = _visual(p)
    return f"""
<section class="post">
  <header>
    <div class="code">{code}</div>
    <div class="when"><b>{_day(p['date'])} · {e(p.get('time') or '--:--')} IST</b>
      <span>{e(p['account_name'])} · {PLATFORMS.get(p['platform'], p['platform'])} · {FORMATS.get(p['format'], p['format'])}</span>
      <span class=m>{status} · approved by {APPROVER.get(p.get('approver'), 'the manager')}</span></div>
  </header>
  {card}
  <div class="sec"><h3>{'Thread' if parts else 'Post text'}</h3>{body}</div>
  {shots}
  {mine}
  {_checks(p)}
  <footer>Reply on WhatsApp: <b>{code} OK</b> · <b>{code} CHANGE</b> + what to change · <b>{code} DROP</b> + why</footer>
</section>"""


def build_html(posts: list[dict], codes: dict[str, str], title: str, subtitle: str, intro: str) -> str:
    ordered = sorted(posts, key=lambda p: codes[p["id"]])
    first = ordered[0]
    ex = codes[ordered[min(6, len(ordered) - 1)]["id"]]
    rows, day = [], None
    for p in ordered:
        if p["date"] != day:
            day = p["date"]
            rows.append(f'<tr class=dayrow><td colspan=3>{_day(day)}</td></tr>')
        who = "" if p["account_name"] == "Pathvik" and len({x["account"] for x in ordered}) == 1 else f" · {e(p['account_name'])}"
        rows.append(f"<tr><td class=c>{codes[p['id']]}</td><td class=t>{e(p.get('time') or '')}<br><span class=m>{PLATFORMS.get(p['platform'], p['platform'])}</span></td>"
                    f"<td>{e(p['hook'][:80])}<span class=m>{who}</span></td></tr>")
    rows = "".join(rows)
    pages = "".join(_post_page(p, codes[p["id"]], len(ordered)) for p in ordered)
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{e(title)}</title><style>
@page {{ size: 110mm 196mm; margin: 7mm 6.5mm 8mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: Inter, "DejaVu Sans", sans-serif; font-size: 8.6pt; line-height: 1.42; color: #101a15; margin: 0; }}
h1 {{ font-size: 16pt; line-height: 1.15; margin: 0 0 2mm; letter-spacing: -0.01em; }}
h2 {{ font-size: 10pt; margin: 4mm 0 2mm; }}
h3 {{ font-size: 7pt; text-transform: uppercase; letter-spacing: .08em; color: #55645b; margin: 0 0 1.2mm; }}
.m {{ color: #55645b; }}
.cover .brand {{ display: inline-block; background: #064e3b; color: #fff; font-weight: 700; border-radius: 2.5mm; padding: 1.2mm 2.4mm; font-size: 8pt; margin-bottom: 4mm; }}
.cover p {{ margin: 0 0 2mm; }}
.how {{ background: #dcefe6; border-radius: 2.5mm; padding: 3mm; margin: 3mm 0; }}
.how div {{ margin: 0.8mm 0; }}
.warn {{ background: #fef3c7; color: #6b3a07; border-radius: 2.5mm; padding: 2.4mm 3mm; margin: 2mm 0; }}
table {{ width: 100%; border-collapse: collapse; font-size: 7.4pt; }}
td {{ border-bottom: 0.2mm solid #dde4e0; padding: 1mm 1mm; vertical-align: top; }}
td.c {{ font-weight: 700; white-space: nowrap; }}
td.t {{ white-space: nowrap; }}
tr.dayrow td {{ font-weight: 700; background: #eef2f0; padding: 1mm 1.5mm; border-bottom: 0; }}
tr {{ break-inside: avoid; }}
.post {{ break-before: page; }}
header {{ display: flex; gap: 3mm; align-items: center; margin-bottom: 3mm; }}
.code {{ background: #064e3b; color: #fff; font-weight: 700; font-size: 13pt; border-radius: 2.5mm; padding: 1.5mm 2.6mm; }}
.when {{ display: grid; gap: 0.3mm; }}
.when b {{ font-size: 10pt; }}
.media {{ position: relative; border-radius: 3mm; background: linear-gradient(150deg, var(--c1), var(--c2)); color: #fff; height: 38mm;
  display: grid; place-items: center; padding: 6mm; text-align: center; margin-bottom: 3mm; }}
.media p {{ margin: 0; font-weight: 700; font-size: 11pt; line-height: 1.2; }}
.media .tag {{ position: absolute; top: 2mm; right: 2mm; background: rgba(0,0,0,.4); border-radius: 9mm; font-size: 6.4pt; font-weight: 700; padding: 0.6mm 2mm; }}
.sec {{ margin: 0 0 3mm; }}
.text {{ white-space: pre-wrap; background: #f4f6f5; border: 0.2mm solid #dde4e0; border-radius: 2.5mm; padding: 2.6mm 3mm; margin-bottom: 1.5mm; overflow-wrap: anywhere; }}
.shots {{ margin: 0; padding-left: 4mm; }}
.shots li {{ margin-bottom: 1mm; break-inside: avoid; }}
.mine {{ background: #d1fae5; border-radius: 2.5mm; padding: 2.4mm 3mm; }}
.checks {{ margin: 0; padding: 0; list-style: none; }}
.checks li {{ border-radius: 2mm; padding: 1.6mm 2.4mm; margin-bottom: 1.2mm; break-inside: avoid; }}
.checks li.flag {{ background: #fef3c7; color: #6b3a07; }}
.checks li.block {{ background: #ffe4e6; color: #9f1239; }}
footer {{ border-top: 0.2mm solid #dde4e0; padding-top: 2mm; margin-top: 3mm; font-size: 7.4pt; color: #2e3c35; break-inside: avoid; }}
</style></head><body>
<section class="cover">
  <span class="brand">Hi Fuel · Team review</span>
  <h1>{e(title)}</h1>
  <p class="m">{e(subtitle)}</p>
  <p>{e(intro)}</p>
  <div class="how"><b>How to reply (on WhatsApp)</b>
    <div><b>{ex} OK</b>: good to go</div>
    <div><b>{ex} CHANGE</b> + what to change: e.g. “{ex} CHANGE make the hook shorter”</div>
    <div><b>{ex} DROP</b> + why</div>
    <div class="m">One message can cover many posts. Silence on a post means no comment, not approval.</div></div>
  <div class="warn"><b>First post goes out {_day(first['date'])}, {e(first.get('time') or '')} IST.</b> Earliest posts first, please. Internal drafts: please don't forward outside the team.</div>
  <h2>All {len(ordered)} posts</h2>
  <table>{rows}</table>
</section>
{pages}
</body></html>"""


def whatsapp_message(title: str, posts: list[dict], codes: dict[str, str], deadline: str) -> str:
    ordered = sorted(posts, key=lambda p: codes[p["id"]])
    first = ordered[0]
    last = codes[ordered[-1]["id"]]
    ex = codes[ordered[min(6, len(ordered) - 1)]["id"]]
    return (f"Hi team! 👋 Please review the attached *{title}* ({len(ordered)} posts, {codes[first['id']]}–{last}).\n\n"
            f"Each post has a number. Reply here with:\n"
            f"✅ *{ex} OK*: good to go\n"
            f"✏️ *{ex} CHANGE* + what to change\n"
            f"❌ *{ex} DROP* + why\n\n"
            f"The first post goes out *{_day(first['date'])}, {first.get('time', '')} IST*, so please start with the earliest ones. "
            f"{deadline}\n\n"
            f"These are internal drafts, so please don't forward them outside the team. Thank you! 🙏")


def write_pack(posts: list[dict], out_dir: Path, name: str, title: str, subtitle: str, intro: str,
               prefix: str, deadline: str) -> dict[str, Path]:
    codes = assign_codes(posts, prefix)
    out_dir.mkdir(parents=True, exist_ok=True)
    files = {"html": out_dir / f"{name}.html", "codes": out_dir / f"{name}.codes.json", "message": out_dir / f"{name}.whatsapp.txt"}
    files["html"].write_text(build_html(posts, codes, title, subtitle, intro), encoding="utf-8")
    files["codes"].write_text(json.dumps({c: pid for pid, c in sorted(codes.items(), key=lambda kv: kv[1])}, indent=1), encoding="utf-8")
    files["message"].write_text(whatsapp_message(title, posts, codes, deadline), encoding="utf-8")
    pdf = out_dir / f"{name}.pdf"
    if _print_pdf(files["html"], pdf):
        files["pdf"] = pdf
    return files


def _print_pdf(src: Path, dest: Path) -> bool:
    """Print the HTML to PDF with Playwright's Chromium, if it's installed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    import glob
    import os
    exe = os.environ.get("CHROMIUM_PATH") or next(iter(sorted(glob.glob("/opt/pw-browsers/chromium-*/chrome-linux/chrome"))), None)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(**({"executable_path": exe} if exe else {}))
        page = browser.new_page()
        page.goto(src.resolve().as_uri())
        page.pdf(path=str(dest), prefer_css_page_size=True, print_background=True)
        browser.close()
    return True
