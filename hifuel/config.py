"""Loads the YAML files in config/ and prompts/."""

from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
PROMPTS_DIR = ROOT / "prompts"


@dataclass
class Config:
    accounts: dict
    global_rules: dict
    platforms: dict
    rules: dict
    slots: dict
    key_dates: dict

    def account(self, account_id: str) -> dict:
        if account_id not in self.accounts:
            raise KeyError(f"Unknown account '{account_id}'. Known: {', '.join(self.accounts)}")
        return self.accounts[account_id]

    def enabled_accounts(self) -> list[str]:
        return [a for a, v in self.accounts.items() if v.get("enabled")]

    def audience_for(self, account_id: str, platform: str) -> str:
        return self.account(account_id).get("audience", {}).get(platform, "business")


def _read(name: str, base: Path = CONFIG_DIR) -> dict:
    return yaml.safe_load((base / name).read_text(encoding="utf-8"))


def load_config(base: Path = CONFIG_DIR) -> Config:
    accounts = _read("accounts.yaml", base)
    return Config(
        accounts=accounts["accounts"],
        global_rules=accounts.get("global", {}),
        platforms=_read("platforms.yaml", base)["platforms"],
        rules=_read("claims_rules.yaml", base),
        slots=_read("time_slots.yaml", base),
        key_dates=_read("key_dates.yaml", base),
    )


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")
