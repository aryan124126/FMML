from typing import List, Optional

from .config import Profile
from .models import Listing


def score_listing(listing: Listing, profile: Profile) -> Optional[Listing]:
    """Return the listing with .score/.match_reasons set, or None if it
    should be dropped (no keyword match, an excluded phrase, or a budget
    that's clearly too small to matter)."""
    haystack = " ".join([listing.title, listing.description, " ".join(listing.tags)]).lower()

    if any(bad.lower() in haystack for bad in profile.exclude_keywords):
        return None

    matched = [kw for kw in profile.keywords if kw.lower() in haystack]
    if not matched:
        return None

    score = len(matched) * 10.0

    top_budget = listing.budget_usd_max or listing.budget_usd_min
    if top_budget:
        if top_budget < profile.min_project_usd:
            return None
        score += min(top_budget, 5000.0) / 100.0

    listing.match_reasons = matched
    listing.score = round(score, 2)
    return listing


def rank(listings: List[Listing], profile: Profile) -> List[Listing]:
    scored = []
    for listing in listings:
        result = score_listing(listing, profile)
        if result is not None:
            scored.append(result)
    scored.sort(key=lambda l: l.score, reverse=True)
    return scored
