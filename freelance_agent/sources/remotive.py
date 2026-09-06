import sys
from typing import List

import requests

from ..models import Listing
from ..textutil import strip_html
from .base import Source

API_URL = "https://remotive.com/api/remote-jobs"


class RemotiveSource(Source):
    """Remotive's public JSON API (no auth). Docs: https://remotive.com/api-documentation"""

    name = "remotive"

    def __init__(self, per_keyword_limit: int = 20, timeout: int = 15):
        self.per_keyword_limit = per_keyword_limit
        self.timeout = timeout

    def fetch(self, keywords: List[str]) -> List[Listing]:
        listings: List[Listing] = []
        seen_urls = set()
        for kw in keywords:
            try:
                resp = requests.get(API_URL, params={"search": kw}, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[warn] remotive: query '{kw}' failed: {exc}", file=sys.stderr)
                continue

            for job in data.get("jobs", [])[: self.per_keyword_limit]:
                url = job.get("url")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                listings.append(
                    Listing(
                        source=self.name,
                        title=job.get("title", ""),
                        url=url,
                        description=strip_html(job.get("description", "")),
                        budget_text=job.get("salary", "") or "",
                        posted_at=job.get("publication_date"),
                        tags=[t for t in [job.get("category", "")] if t],
                    )
                )
        return listings
