import sys
import xml.etree.ElementTree as ET
from typing import List

import requests

from ..models import Listing
from ..textutil import strip_html
from .base import Source


class WeWorkRemotelySource(Source):
    """Parses WeWorkRemotely's public per-category RSS feeds (no auth).
    Feed URLs come from Profile.wwr_feeds since category slugs occasionally
    change; a feed that 404s is logged and skipped, not fatal."""

    name = "weworkremotely"

    def __init__(self, feed_urls: List[str], timeout: int = 15):
        self.feed_urls = feed_urls
        self.timeout = timeout

    def fetch(self, keywords: List[str]) -> List[Listing]:
        kw_lower = [k.lower() for k in keywords]
        listings: List[Listing] = []
        for feed_url in self.feed_urls:
            try:
                resp = requests.get(feed_url, timeout=self.timeout)
                resp.raise_for_status()
                root = ET.fromstring(resp.content)
            except (requests.RequestException, ET.ParseError) as exc:
                print(f"[warn] weworkremotely: feed {feed_url} failed: {exc}", file=sys.stderr)
                continue

            for item in root.findall("./channel/item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                description = strip_html(item.findtext("description") or "")
                pub_date = item.findtext("pubDate")

                haystack = f"{title} {description}".lower()
                if kw_lower and not any(k in haystack for k in kw_lower):
                    continue

                listings.append(
                    Listing(
                        source=self.name,
                        title=title,
                        url=link,
                        description=description,
                        posted_at=pub_date,
                    )
                )
        return listings
