import re
from pathlib import Path
from typing import List

from ..models import Listing
from .base import Source

_FIELD_RE = re.compile(r"^(Title|URL|Budget)\s*:\s*(.*)$", re.IGNORECASE)


class ManualSource(Source):
    """Upwork, Fiverr, PeoplePerHour etc. don't offer a public search API, and
    scraping them would violate their terms of service. Instead, paste job
    posts you've copied by hand into a text file (see
    freelance_agent/manual_jobs.example.txt for the template) and this source
    parses + scores them alongside everything else.

    Entries are separated by a line containing only '---'. Recognized fields
    (case-insensitive, one per line): Title:, URL:, Budget:. Everything else
    in the entry becomes the description.
    """

    name = "manual"

    def __init__(self, path: str):
        self.path = path

    def fetch(self, keywords: List[str]) -> List[Listing]:
        text = Path(self.path).read_text(encoding="utf-8")
        listings: List[Listing] = []
        for block in text.split("\n---\n"):
            block = block.strip()
            if not block:
                continue
            title = ""
            url = ""
            budget = ""
            desc_lines = []
            for line in block.splitlines():
                m = _FIELD_RE.match(line.strip())
                if m:
                    field, value = m.group(1).lower(), m.group(2).strip()
                    if field == "title":
                        title = value
                    elif field == "url":
                        url = value
                    elif field == "budget":
                        budget = value
                    continue
                desc_lines.append(line)
            description = "\n".join(desc_lines).strip()
            if not title and not description:
                continue
            listings.append(
                Listing(
                    source="manual",
                    title=title or "(untitled pasted listing)",
                    url=url,
                    description=description,
                    budget_text=budget,
                )
            )
        return listings
