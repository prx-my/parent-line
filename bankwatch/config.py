"""Bank watch's settings: one TOML file per family, plus the agent's Switch credentials."""

from __future__ import annotations

import json
import os
import tomllib
from dataclasses import dataclass
from datetime import time
from decimal import Decimal
from pathlib import Path

from bankwatch.rules import Rules
from bankwatch.switch import SwitchAgent


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    parent_name: str
    guardian: str
    room_id: str
    webhook_secret: str
    state_file: Path
    known_payees: list[str]
    rules: Rules
    credentials: Path | None


def _need(table: dict, key: str, where: str) -> object:
    if key not in table or table[key] in ("", None):
        raise ConfigError(f"{where}: '{key}' is missing")
    return table[key]


def load(path: Path) -> Config:
    raw = tomllib.loads(path.read_text())
    r = _need(raw, "rules", str(path))
    assert isinstance(r, dict)
    where = f"{path} [rules]"
    rules = Rules(
        large_debit=Decimal(str(_need(r, "large_debit", where))),
        new_payee_min=Decimal(str(_need(r, "new_payee_min", where))),
        burst_count=int(_need(r, "burst_count", where)),  # type: ignore[arg-type]
        burst_minutes=int(_need(r, "burst_minutes", where)),  # type: ignore[arg-type]
        burst_min_total=Decimal(str(_need(r, "burst_min_total", where))),
        night_start=time.fromisoformat(str(_need(r, "night_start", where))),
        night_end=time.fromisoformat(str(_need(r, "night_end", where))),
        night_min=Decimal(str(_need(r, "night_min", where))),
    )
    base = path.parent
    credentials = raw.get("credentials")
    return Config(
        parent_name=str(_need(raw, "parent_name", str(path))),
        guardian=str(_need(raw, "guardian", str(path))),
        room_id=str(raw.get("room_id", "")),
        webhook_secret=os.environ.get("BANKWATCH_SECRET") or str(raw.get("webhook_secret", "")),
        state_file=base / str(raw.get("state_file", "bankwatch-state.json")),
        known_payees=[str(p) for p in raw.get("known_payees", [])],
        rules=rules,
        credentials=(base / str(credentials)) if credentials else None,
    )


def switch_agent(config: Config) -> SwitchAgent:
    """The Bank watch agent's credentials: from the environment, else from the
    credentials file Switch Console wrote for the agent."""
    keys = ("SWITCH_API_ENDPOINT", "SWITCH_API_TOKEN", "SWITCH_AGENT_ID")
    env = {k: os.environ.get(k, "") for k in keys}
    if not all(env.values()) and config.credentials:
        if not config.credentials.exists():
            raise ConfigError(f"credentials file {config.credentials} does not exist")
        on_disk = json.loads(config.credentials.read_text())["env"]
        env = {k: env[k] or str(on_disk.get(k, "")) for k in keys}
    missing = [k for k in keys if not env[k]]
    if missing:
        raise ConfigError(
            "Switch credentials missing: " + ", ".join(missing)
            + ". Set them in the environment or point 'credentials' at the agent's .switch/agents/<name>.json."
        )
    if not config.room_id:
        raise ConfigError("'room_id' is missing: the family group's Switch room id")
    return SwitchAgent(endpoint=env["SWITCH_API_ENDPOINT"], token=env["SWITCH_API_TOKEN"], agent_id=env["SWITCH_AGENT_ID"])
