"""Call watch: the parent's missed call to the family's Twilio number is an SOS.

    python -m callwatch serve [--port 8788]

Twilio sends each call to the number to POST /voice. Call watch rejects it, so
the call is never answered and the parent pays nothing, and posts to the family
room for the Guardian. Settings are in family.toml under [call]; the Twilio
Auth Token comes from TWILIO_AUTH_TOKEN.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import logging
import os
import re
import sys
import threading
import time
import tomllib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

from bankwatch.config import Config, ConfigError, load, switch_agent
from bankwatch.switch import SwitchAgent, SwitchPostError

logger = logging.getLogger("callwatch")

# Busy, not answered: Twilio doesn't bill a rejected call and the caller's operator doesn't charge for an unanswered one.
REJECT = '<?xml version="1.0" encoding="UTF-8"?><Response><Reject reason="busy"/></Response>'


@dataclass(frozen=True)
class Settings:
    parent: str
    guardian: str
    voice_url: str  # the exact address set in Twilio, which its signature covers
    numbers: frozenset[str]
    auth_token: str


def phone(number: str) -> str:
    """'+91 98765 43210' and '+919876543210' are the same number."""
    return re.sub(r"[^\d+]", "", number)


def settings(config_path: Path) -> tuple[Config, Settings]:
    """The family config with Call watch's own credentials, and its settings."""
    config = load(config_path)
    raw = tomllib.loads(config_path.read_text()).get("call")
    if not isinstance(raw, dict):
        raise ConfigError(f"{config_path}: [call] is missing; copy it from family.example.toml")
    for key in ("credentials", "public_url", "parent_numbers"):
        if not raw.get(key):
            raise ConfigError(f"{config_path} [call]: '{key}' is missing")
    token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    if not token:
        raise ConfigError("TWILIO_AUTH_TOKEN is not set: without it Call watch can't tell Twilio's calls from fake ones")
    s = Settings(
        parent=config.parent_name,
        guardian=config.guardian,
        voice_url=str(raw["public_url"]).rstrip("/") + "/voice",
        numbers=frozenset(phone(str(n)) for n in raw["parent_numbers"]),
        auth_token=token,
    )
    return replace(config, credentials=config_path.parent / str(raw["credentials"])), s


def signature(auth_token: str, url: str, fields: Sequence[tuple[str, str]]) -> str:
    """What Twilio puts in X-Twilio-Signature: the URL, then each field's name and value sorted by name."""
    signed = url + "".join(name + value for name, value in sorted(set(fields)))
    return base64.b64encode(hmac.new(auth_token.encode(), signed.encode(), hashlib.sha1).digest()).decode()


def missed_call_text(parent: str, guardian: str, at: datetime) -> str:
    return f"📞 **{parent} gave a missed call at {at:%H:%M}. Who's calling {parent}?**\n{guardian} over to you."


def handle(s: Settings, body: bytes, given: str, at: datetime) -> tuple[int, str, str | None]:
    """One webhook from Twilio: (HTTP status, reply, the post for the family room or None)."""
    try:
        fields = parse_qsl(body.decode("utf-8"), keep_blank_values=True, max_num_fields=200)
    except ValueError:
        return 400, "not a form", None
    if not given or not hmac.compare_digest(given.encode(), signature(s.auth_token, s.voice_url, fields).encode()):
        return 403, "bad Twilio signature", None
    caller = phone(dict(fields).get("From", ""))
    if caller not in s.numbers:
        logger.warning("Rejected a call from %s: not one of the parent's numbers", caller or "a hidden number")
        return 200, REJECT, None
    return 200, REJECT, missed_call_text(s.parent, s.guardian, at)


def post_with_retry(post: Callable[[], object], tries: int = 3, wait: float = 5) -> None:
    for attempt in range(1, tries + 1):
        try:
            post()
            logger.info("Missed-call SOS posted")
            return
        except SwitchPostError as exc:
            logger.error("Missed-call SOS not posted (try %d of %d): %s", attempt, tries, exc)
            if attempt < tries:
                time.sleep(wait)
    # shortcut: Twilio doesn't retry a voice webhook, so after 3 failed tries this SOS is lost; add a durable queue if that happens in practice.
    logger.error("GAVE UP: this missed-call SOS never reached the family room")


def serve(config: Config, s: Settings, agent: SwitchAgent, port: int) -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            if urlsplit(self.path).path != "/voice":
                return self._reply(404, "text/plain", "Twilio's call webhook is POST /voice")
            length = int(self.headers.get("Content-Length") or 0)
            status, reply, text = handle(s, self.rfile.read(length), self.headers.get("X-Twilio-Signature", ""), datetime.now())
            # Answer Twilio first: a slow reply makes it play an error message, which answers the call and charges the parent.
            self._reply(status, "text/xml" if status == 200 else "text/plain", reply)
            if text:
                threading.Thread(target=post_with_retry, args=(lambda: agent.post(config.room_id, text),)).start()

        def _reply(self, status: int, content_type: str, message: str) -> None:
            body = message.encode()
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = HTTPServer(("0.0.0.0", port), Handler)
    logger.info("Call watch listening on :%d; set Twilio's 'A call comes in' webhook to %s (HTTP POST)", port, s.voice_url)
    server.serve_forever()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", force=True)
    parser = argparse.ArgumentParser(prog="callwatch", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("family.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    srv = sub.add_parser("serve", help="receive Twilio's call webhook")
    srv.add_argument("--port", type=int, default=8788)
    args = parser.parse_args()
    try:
        config, s = settings(args.config)
        serve(config, s, switch_agent(config), args.port)
    except (ConfigError, SwitchPostError, FileNotFoundError) as exc:
        print(f"callwatch: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
