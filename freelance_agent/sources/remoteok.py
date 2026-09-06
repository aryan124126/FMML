import sys
from typing import List

import requests

from ..models import Listing
from ..textutil import strip_html
from .base import Source

API_URL = "https://remoteok.com/api"


def _format_salary(lo, hi) -> str:
    if not lo and not hi:
        return ""
    if lo and hi and lo != hi:
        return f"${lo:,.0f}-${hi:,.0f}/yr"
    val = hi or lo
    return f"${val:,.0f}/yr"


class RemoteOKSource(Source):
    """RemoteOK's public JSON feed (no auth). First array element is a legal
    notice, not a job — skipped via the 'position' key check below."""

    name = "remoteok"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def fetch(self, keywords: List[str]) -> List[Listing]:
        try:
            resp = requests.get(
                API_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=self.timeout
            )
            resp.raise_for_status()
            jobs = resp.json()
        except (requests.RequestException, ValueError) as exc:
            print(f"[warn] remoteok: fetch failed: {exc}", file=sys.stderr)
            return []

        kw_lower = [k.lower() for k in keywords]
        listings: List[Listing] = []
        for job in jobs:
            if "position" not in job:
                continue
            haystack = " ".join(
                [
                    job.get("position", ""),
                    job.get("description", ""),
                    " ".join(job.get("tags", []) or []),
                ]
            ).lower()
            if not any(k in haystack for k in kw_lower):
                continue
            listings.append(
                Listing(
                    source=self.name,
                    title=job.get("position", ""),
                    url=job.get("url", ""),
                    description=strip_html(job.get("description", "")),
                    budget_text=_format_salary(job.get("salary_min"), job.get("salary_max")),
                    budget_usd_min=job.get("salary_min"),
                    budget_usd_max=job.get("salary_max"),
                    posted_at=job.get("date"),
                    tags=job.get("tags", []) or [],
                )
            )
        return listings
