import os
import sys
from typing import List

import requests

from ..models import Listing
from ..textutil import strip_html
from .base import Source

API_URL = "https://www.freelancer.com/api/projects/0.1/projects/active/"


class FreelancerComSource(Source):
    """Freelancer.com's project-search API. Most endpoints require an OAuth
    token even for read-only queries — generate a personal token at
    https://developers.freelancer.com (Manage Apps) and set
    FREELANCER_OAUTH_TOKEN. Without it, this source logs a notice and
    contributes nothing rather than failing the whole run.

    NOTE: this integration could not be exercised against the live API while
    building it (this build environment's network egress is restricted), so
    treat the response parsing below as best-effort against Freelancer's
    documented schema and adjust field names if their API has since changed.
    """

    name = "freelancer_com"

    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.token = os.environ.get("FREELANCER_OAUTH_TOKEN")

    def fetch(self, keywords: List[str]) -> List[Listing]:
        if not self.token:
            print(
                "[info] freelancer_com: no FREELANCER_OAUTH_TOKEN set, skipping source",
                file=sys.stderr,
            )
            return []

        headers = {"freelancer-oauth-v1": self.token}
        listings: List[Listing] = []
        seen_ids = set()
        for kw in keywords:
            params = {
                "query": kw,
                "limit": 20,
                "job_details": "true",
                "full_description": "true",
            }
            try:
                resp = requests.get(API_URL, params=params, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[warn] freelancer_com: query '{kw}' failed: {exc}", file=sys.stderr)
                continue

            projects = (data.get("result") or {}).get("projects") or []
            for proj in projects:
                pid = proj.get("id")
                if pid is None or pid in seen_ids:
                    continue
                seen_ids.add(pid)

                seo_url = proj.get("seo_url")
                url = f"https://www.freelancer.com/projects/{seo_url}" if seo_url else ""
                budget = proj.get("budget") or {}
                lo, hi = budget.get("minimum"), budget.get("maximum")
                currency = (proj.get("currency") or {}).get("code", "")
                budget_text = ""
                if lo or hi:
                    budget_text = f"{currency} {lo or ''}-{hi or ''}".strip()

                listings.append(
                    Listing(
                        source=self.name,
                        title=proj.get("title", ""),
                        url=url,
                        description=strip_html(proj.get("preview_description", "")),
                        budget_text=budget_text,
                        budget_usd_min=lo if currency == "USD" else None,
                        budget_usd_max=hi if currency == "USD" else None,
                        posted_at=str(proj.get("time_submitted", "")),
                        tags=[j.get("name", "") for j in (proj.get("jobs") or [])],
                    )
                )
        return listings
