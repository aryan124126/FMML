import csv
from datetime import date
from typing import List

from .config import Profile
from .models import Listing


def to_markdown(listings: List[Listing], profile: Profile) -> str:
    lo, hi = profile.target_income_inr_month
    lines = [
        f"# Freelance digest — {date.today().isoformat()}",
        "",
        f"Target: ₹{lo:,}–₹{hi:,}/month · {len(listings)} matches",
        "",
    ]
    if not listings:
        lines.append("No matches this run. Try widening keywords in config.yaml.")
        return "\n".join(lines)

    for i, listing in enumerate(listings, 1):
        lines.append(f"## {i}. {listing.title} (score {listing.score})")
        lines.append(f"- Source: {listing.source}")
        lines.append(f"- Budget: {listing.budget_text or 'n/a'}")
        lines.append(f"- Matched: {', '.join(listing.match_reasons) or 'n/a'}")
        if listing.url:
            lines.append(f"- Link: {listing.url}")
        if listing.description:
            snippet = listing.description[:280]
            lines.append(f"- {snippet}{'...' if len(listing.description) > 280 else ''}")
        lines.append("")
    return "\n".join(lines)


def to_csv(listings: List[Listing], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["score", "source", "title", "budget", "url", "matched_keywords"])
        for listing in listings:
            writer.writerow(
                [
                    listing.score,
                    listing.source,
                    listing.title,
                    listing.budget_text,
                    listing.url,
                    "; ".join(listing.match_reasons),
                ]
            )
