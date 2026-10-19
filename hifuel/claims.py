"""Claims check (CLAUDE.md §3).

Runs on every draft. Returns a list of issues:
  - "block": the post can't be approved until it's fixed
  - "flag":  listed for the reviewer to check
Pattern rules live in config/claims_rules.yaml; checks that need logic are below.
"""

import re

from .config import Config
from .models import publish_text

PRICE_RE = re.compile(r"(?:₹|\brs\.?|\binr)\s*([\d,]+(?:\.\d+)?)|([\d,]+)\s*(?:/-|rupees)", re.I)
NUMBER_RE = re.compile(r"\d[\d,.]*")
CO2_PER_TREE_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(kg|kgs|kilograms?|t|tonnes?|tons?)\b[^.\n]{0,40}?\b(?:per|each|every|a|/)\s*(\d+\s+)?trees?\b",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def _issue(severity, rule, check, message, excerpt=""):
    return {"severity": severity, "rule": rule, "check": check, "message": message, "excerpt": excerpt[:160]}


def public_texts(post: dict) -> list[str]:
    """Every piece of text that will be seen publicly (not hashtags)."""
    brief = post.get("design_brief") or {}
    reel = brief.get("reel") or {}
    texts = [post.get("hook", ""), post.get("caption", ""), post.get("cta", ""), post.get("alt_text", "")]
    texts += post.get("thread_parts") or []
    texts += [s.get("text", "") for s in brief.get("slides") or []]
    texts.append(reel.get("opening_hook", ""))
    for shot in reel.get("shots") or []:
        texts += [shot.get("on_screen_text", ""), shot.get("voiceover", "")]
    return [t for t in texts if t and t.strip()]


def _sentences(texts: list[str]) -> list[str]:
    out = []
    for t in texts:
        out += [s for s in SENTENCE_SPLIT.split(t) if s.strip()]
    return out


def _applies(rule_accounts, account_id: str, groups: dict) -> bool:
    if rule_accounts == "all":
        return True
    if isinstance(rule_accounts, str):
        return account_id in groups.get(rule_accounts, [])
    return account_id in rule_accounts


def _pattern_rules(post, cfg: Config, sentences) -> list[dict]:
    issues = []
    groups = cfg.rules.get("groups", {})
    for rule in cfg.rules.get("rules", []):
        if not _applies(rule["accounts"], post["account"], groups):
            continue
        flags = 0 if rule.get("case_sensitive") else re.I
        patterns = [re.compile(p, flags) for p in rule["patterns"]]
        required = re.compile(rule["require_in_sentence"], re.I) if rule.get("require_in_sentence") else None
        downgrade = re.compile(rule["downgrade_if"], re.I) if rule.get("downgrade_if") else None
        for sentence in sentences:
            if not any(p.search(sentence) for p in patterns):
                continue
            if required and not required.search(sentence):
                continue
            severity = rule["severity"]
            if severity == "block" and downgrade and downgrade.search(sentence):
                severity = "flag"
            issues.append(_issue(severity, rule["rule"], rule["id"], rule["message"].strip(), sentence))
            break  # one issue per rule is enough
    return issues


def _co2_per_tree(sentences) -> list[dict]:
    issues = []
    for s in sentences:
        for m in CO2_PER_TREE_RE.finditer(s):
            value, unit, trees = float(m.group(1)), m.group(2).lower(), m.group(3)
            kg = value * (1000 if unit.startswith("t") else 1)
            if trees:  # e.g. "2 t per 10 trees"
                kg /= int(trees)
            if abs(kg - 22) > 0.5:
                issues.append(_issue("block", 1, "co2_per_tree",
                                     f"Use ~22 kg CO2 per tree per year (estimated sequestration); this says ~{kg:g} kg.", s))
            elif "estimat" not in s.lower():
                issues.append(_issue("block", 1, "co2_per_tree",
                                     'Label the 22 kg figure as "estimated sequestration".', s))
    return issues


def _statistics(post, cfg: Config, sentences) -> list[dict]:
    patterns = [re.compile(p, re.I) for p in cfg.rules.get("statistic_patterns", [])]
    stats = [s for s in sentences if any(p.search(s) for p in patterns)]
    if not stats:
        return []
    if not post.get("claims_notes"):
        return [_issue("block", 7, "statistic_source",
                       "Statistics need a source and year in the claims notes.", stats[0])]
    return [_issue("flag", 7, "statistic_source",
                   f"{len(stats)} statistic(s) to verify against the claims notes.", stats[0])]


def _numbers_and_prices(post, cfg: Config, texts) -> list[dict]:
    issues = []
    allowed = {p.replace(",", "") for p in cfg.account(post["account"]).get("allowed_prices", [])}
    for t in texts:
        for m in PRICE_RE.finditer(t):
            amount = (m.group(1) or m.group(2)).replace(",", "").split(".")[0]
            if amount not in allowed:
                issues.append(_issue("block", 10, "price",
                                     f"Price {m.group(0).strip()} isn't a confirmed price for this account. "
                                     "Confirm it before posting.", t))
            else:
                issues.append(_issue("flag", 10, "price", f"Price mentioned: {m.group(0).strip()}.", t))
    numbers = sorted({n.strip(".,") for t in texts for n in NUMBER_RE.findall(t)})
    if numbers:
        issues.append(_issue("flag", 7, "numbers", "Numbers to check: " + ", ".join(numbers[:12])))
    return issues


def _names_and_internal(post, cfg: Config, texts, hashtags) -> list[dict]:
    issues = []
    joined = "\n".join([*texts, " ".join(hashtags)])
    account = cfg.account(post["account"])
    confirmed = {p.lower() for p in account.get("confirmed_partners", [])}
    for partner in cfg.global_rules.get("unconfirmed_partners", []):
        if partner.lower() not in confirmed and re.search(rf"\b{re.escape(partner)}\b", joined, re.I):
            issues.append(_issue("block", 4, "unconfirmed_partner",
                                 f'"{partner}" is not a confirmed partner. Confirm the association first.'))
    internal_terms = {t for a in cfg.accounts.values() for t in a.get("internal", [])}
    internal_terms |= set(account.get("internal_in_own_posts", []))
    for term in sorted(internal_terms):
        if re.search(rf"\b{re.escape(term)}\b", joined, re.I):
            issues.append(_issue("block", 0, "internal_term",
                                 f'"{term}" is internal or outdated and must not appear in public posts.'))
    return issues


def _platform(post, cfg: Config) -> list[dict]:
    issues = []
    plat = cfg.platforms.get(post["platform"])
    if not plat:
        return [_issue("block", 0, "platform", f"Unknown platform {post['platform']}.")]
    parts = post.get("thread_parts") or []
    texts = parts if (post["platform"] == "x" and parts) else [publish_text(post)]
    for i, text in enumerate(texts):
        label = f"Part {i + 1}" if len(texts) > 1 else "Post"
        n = len(text)
        if n > plat["max_chars"]:
            issues.append(_issue("block", 0, "length",
                                 f"{label} is {n} characters; {plat['name']} allows {plat['max_chars']}."))
        elif n > plat["soft_chars"]:
            issues.append(_issue("flag", 0, "length",
                                 f"{label} is {n} characters; aim for under {plat['soft_chars']} on {plat['name']}."))
    low, high = plat["hashtags"]
    count = len(post.get("hashtags") or [])
    if not low <= count <= high:
        issues.append(_issue("flag", 0, "hashtags", f"{count} hashtags; use {low}-{high} on {plat['name']}."))
    return issues


def _media_and_people(post) -> list[dict]:
    issues = []
    all_text = publish_text(post)
    if post.get("shows_children") and not post.get("consent_confirmed"):
        issues.append(_issue("block", 13, "children",
                             "Shows or identifies children. Needs verifiable parental consent, or switch to "
                             "backs-of-heads, hands, distant group shots, illustrations or anonymised handles."))
    if post.get("uses_ai_media"):
        if "ai-assisted" not in all_text.lower():
            issues.append(_issue("block", 15, "ai_label",
                                 'Uses AI-generated/edited media: add "AI-assisted" to the caption.'))
        else:
            issues.append(_issue("flag", 15, "ai_label", "Also switch on the platform's AI label when posting."))
    if post.get("collab_with"):
        issues.append(_issue("flag", 0, "collab",
                             "Instagram Collab post: post manually (the native scheduler doesn't support Collabs)."))
    if post.get("format") in {"single_image", "carousel", "document", "story", "reel"} and not post.get("alt_text"):
        issues.append(_issue("flag", 0, "alt_text", "Add alt text for the visual."))
    if post.get("format") == "reel" and not (post.get("design_brief") or {}).get("reel", {}).get("opening_hook"):
        issues.append(_issue("flag", 0, "reel_hook", "Reel needs an opening hook for the first 1-2 seconds."))
    return issues


def _calendar(post, cfg: Config) -> list[dict]:
    issues = []
    day = post.get("date", "")
    for d in cfg.key_dates.get("dates", []):
        start, end = str(d["date"]), str(d.get("until", d["date"]))
        if d["kind"] == "sensitive" and start <= day <= end and post.get("theme") in {"initiative_promo", "engagement"}:
            issues.append(_issue("block", 0, "sensitive_day",
                                 f"{d['name']} is a sensitive day: no promotional or engagement posts."))
    month = int(day[5:7]) if len(day) >= 7 else 0
    for season in cfg.key_dates.get("seasons", []):
        if "exam" in season["name"].lower() and post["account"] in season["accounts"] and month in season["months"]:
            if post.get("theme") == "initiative_promo":
                issues.append(_issue("flag", 0, "season",
                                     f"Falls in '{season['name']}'. Avoid launches now. {season.get('note', '')}"))
    return issues


def check_post(post: dict, cfg: Config) -> list[dict]:
    """Run every check on one post. Blocks are listed first."""
    texts = public_texts(post)
    sentences = _sentences(texts)
    hashtags = post.get("hashtags") or []
    issues = (
        _pattern_rules(post, cfg, sentences)
        + _co2_per_tree(sentences)
        + _statistics(post, cfg, sentences)
        + _numbers_and_prices(post, cfg, texts)
        + _names_and_internal(post, cfg, texts, hashtags)
        + _platform(post, cfg)
        + _media_and_people(post)
        + _calendar(post, cfg)
    )
    return sorted(issues, key=lambda i: i["severity"] != "block")


def is_blocked(issues: list[dict]) -> bool:
    return any(i["severity"] == "block" for i in issues)
