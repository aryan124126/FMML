from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).parent / "config.yaml"


@dataclass
class Profile:
    keywords: List[str] = field(default_factory=list)
    exclude_keywords: List[str] = field(default_factory=list)
    target_income_inr_month: Tuple[int, int] = (300000, 400000)
    inr_per_usd: float = 89.0
    min_project_usd: float = 150.0
    min_hourly_usd: float = 20.0
    sources_enabled: List[str] = field(default_factory=list)
    wwr_feeds: List[str] = field(default_factory=list)
    top_n: int = 25


def load_profile(path=None) -> Profile:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    target = raw.get("target_income_inr_month", [300000, 400000])
    return Profile(
        keywords=raw.get("keywords", []),
        exclude_keywords=raw.get("exclude_keywords", []),
        target_income_inr_month=(target[0], target[1]),
        inr_per_usd=float(raw.get("inr_per_usd", 89.0)),
        min_project_usd=float(raw.get("min_project_usd", 150.0)),
        min_hourly_usd=float(raw.get("min_hourly_usd", 20.0)),
        sources_enabled=raw.get("sources_enabled", []),
        wwr_feeds=raw.get("wwr_feeds", []),
        top_n=int(raw.get("top_n", 25)),
    )
