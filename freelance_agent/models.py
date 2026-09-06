from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Listing:
    source: str
    title: str
    url: str
    description: str = ""
    budget_text: str = ""
    budget_usd_min: Optional[float] = None
    budget_usd_max: Optional[float] = None
    posted_at: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    score: float = 0.0
    match_reasons: List[str] = field(default_factory=list)
