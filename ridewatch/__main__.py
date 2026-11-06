"""Ride watch: a check-in timer in the family group for a ride alone at night.

    python -m ridewatch serve

The rider writes "@ride-watch 25 min" (and pastes the ride app's share-trip
message). Past that time Ride watch asks if they reached; with no answer it
raises the alarm for the Guardian. Settings are in family.toml under [ride].
"""

from __future__ import annotations

import argparse
import logging
import sys
import threading
import time
import tomllib
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Any

from bankwatch.config import Config, ConfigError, load, switch_agent
from bankwatch.switch import SwitchAgent, SwitchPostError
from ridewatch.rides import Rides, Settings, on_message, tick

logger = logging.getLogger("ridewatch")


def settings(config_path: Path) -> tuple[Config, Settings, Path]:
    """The family config with Ride watch's own credentials, its settings, and its state file."""
    config = load(config_path)
    raw = tomllib.loads(config_path.read_text()).get("ride")
    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path}: [ride] is missing; copy it from family.example.toml")
    base = config_path.parent
    if "credentials" not in raw:
        raise ConfigError(f"{config_path} [ride]: 'credentials' is missing")
    s = Settings(
        me=str(raw.get("name", "@ride-watch")),
        guardian=config.guardian,
        grace_minutes=int(raw.get("grace_minutes", 10)),
        answer_minutes=int(raw.get("answer_minutes", 5)),
        code_word=str(raw.get("code_word", "")),
    )
    return replace(config, credentials=base / str(raw["credentials"])), s, base / str(raw.get("state_file", "ridewatch-state.json"))


def is_for_me(event: dict[str, Any], room_id: str) -> bool:
    """A person's message addressed to Ride watch in the family room."""
    p = event.get("payload") or {}
    if event.get("type") != "message" or not p.get("addressed") or p.get("sender_kind") not in ("user", None):
        return False
    if event.get("room_id") != room_id:
        logger.warning("Ignoring a message from room %s; Ride watch only works in room_id %s", event.get("room_id"), room_id)
        return False
    return True


def serve(config: Config, s: Settings, state_file: Path, agent: SwitchAgent) -> None:
    lock = threading.Lock()  # the message loop and the timer share the state file

    def step(work) -> None:  # type: ignore[no-untyped-def]
        """Load, change, post, save: a failed post leaves the state on disk as it was, so the timer retries."""
        with lock:
            rides = Rides.load(state_file)
            for text in work(rides):
                agent.post(config.room_id, text)
                logger.info("Posted: %s", text.splitlines()[0])
            rides.save(state_file)

    def check_every_30_seconds() -> None:
        while True:
            try:
                step(lambda rides: tick(rides, s, datetime.now()))
            except SwitchPostError as exc:
                logger.error("Check-in not posted, retrying: %s", exc)
            time.sleep(30)

    def stay_live() -> None:
        # Without this Switch thinks nobody is in the room and offers to start an AI session for ride-watch.
        while True:
            try:
                agent.renew(config.room_id)
            except SwitchPostError as exc:
                logger.error("Liveness heartbeat failed: %s", exc)
            time.sleep(2)

    threading.Thread(target=check_every_30_seconds, daemon=True).start()
    threading.Thread(target=stay_live, daemon=True).start()
    logger.info("Ride watch is listening in room %s", config.room_id)
    while True:
        try:
            events = agent.events(25)
        except SwitchPostError as exc:
            logger.error("%s", exc)
            time.sleep(5)
            continue
        for event in events:
            if not is_for_me(event, config.room_id):
                continue
            p = event["payload"]
            try:
                step(lambda rides, p=p: on_message(rides, s, p["sender_name"], p["body"], datetime.now()))
            except SwitchPostError as exc:
                # The rider sees no 👀 reply, so they know to send it again.
                logger.error("Reply to %s not posted: %s", p["sender_name"], exc)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    parser = argparse.ArgumentParser(prog="ridewatch", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("family.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="watch rides in the family group")
    args = parser.parse_args()
    try:
        config, s, state_file = settings(args.config)
        serve(config, s, state_file, switch_agent(config))
    except (ConfigError, SwitchPostError, FileNotFoundError) as exc:
        print(f"ridewatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
