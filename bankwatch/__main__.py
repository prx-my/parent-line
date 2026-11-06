"""Bank watch: reads the parent's bank SMS and raises the alarm in the family's
Switch room when a rule fires.

    python -m bankwatch simulate "Rs 4,80,000 debited ..." [--at 23:40] [--dry-run]
    python -m bankwatch serve [--port 8787]
"""

from __future__ import annotations

import argparse
import hmac
import json
import logging
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from bankwatch.config import Config, ConfigError, load, switch_agent
from bankwatch.parse import parse
from bankwatch.rules import State, alarm_text, reasons
from bankwatch.switch import SwitchAgent, SwitchPostError

logger = logging.getLogger("bankwatch")


def handle(config: Config, agent: SwitchAgent | None, text: str, at: datetime) -> str | None:
    """Process one bank SMS. Returns the alarm posted, or None if there was none.

    With no agent (a dry run) the alarm is returned but not posted. The SMS is
    recorded only once the alarm is posted, so a failed post can be retried.
    """
    state = State.load(config.state_file, config.known_payees)
    event = parse(text)
    if state.already_handled(event.text, at):
        logger.info("Already handled this SMS in the last hour; skipping")
        return None
    why = reasons(config.rules, state, event, at)
    alarm = alarm_text(guardian=config.guardian, parent=config.parent_name, event=event, why=why, at=at) if why else None
    if alarm and agent:
        event_id = agent.post(config.room_id, alarm)
        logger.info("Alarm posted to room %s (event %s)", config.room_id, event_id)
    state.record(event, at, alarmed=bool(why))
    state.save(config.state_file)
    return alarm


def _sms_text(body: bytes, content_type: str) -> str:
    """Forwarder apps send either JSON or the bare SMS text."""
    raw = body.decode("utf-8", errors="replace").strip()
    if "json" in content_type or raw.startswith("{"):
        data = json.loads(raw)
        for key in ("text", "message", "body", "msg", "sms"):
            if isinstance(data.get(key), str) and data[key].strip():
                return data[key]
        raise ValueError(f"no SMS text in JSON keys {sorted(data)}; expected one of text, message, body, msg, sms")
    return raw


def serve(config: Config, agent: SwitchAgent, port: int) -> None:
    if not config.webhook_secret:
        raise ConfigError("'webhook_secret' (or BANKWATCH_SECRET) is required to serve: without it anyone could post fake alarms")

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            url = urlsplit(self.path)
            key = self.headers.get("X-Bankwatch-Key") or parse_qs(url.query).get("key", [""])[0]
            if url.path != "/sms":
                return self._reply(404, "POST bank SMS to /sms")
            if not hmac.compare_digest(key.encode(), config.webhook_secret.encode()):
                return self._reply(401, "wrong or missing key")
            try:
                length = int(self.headers.get("Content-Length") or 0)
                text = _sms_text(self.rfile.read(length), self.headers.get("Content-Type", ""))
                alarm = handle(config, agent, text, datetime.now())
            except (ValueError, json.JSONDecodeError) as exc:
                return self._reply(400, str(exc))
            except SwitchPostError as exc:
                logger.error("%s", exc)
                # 502 so the forwarder app retries; the SMS was not recorded.
                return self._reply(502, str(exc))
            self._reply(200, "alarm posted" if alarm else "no alarm")

        def _reply(self, status: int, message: str) -> None:
            body = message.encode()
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:  # noqa: A002
            logger.info("%s %s", self.address_string(), (format % args).replace(config.webhook_secret, "***"))

    server = HTTPServer(("0.0.0.0", port), Handler)
    logger.info("Bank watch listening on :%d, POST bank SMS to /sms", port)
    server.serve_forever()


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="bankwatch", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", type=Path, default=Path("family.toml"))
    sub = parser.add_subparsers(dest="command", required=True)
    sim = sub.add_parser("simulate", help="run one bank SMS through the rules (and post the alarm)")
    sim.add_argument("sms")
    sim.add_argument("--at", help="time the SMS arrived, HH:MM (default: now)")
    sim.add_argument("--dry-run", action="store_true", help="print the alarm instead of posting it")
    srv = sub.add_parser("serve", help="receive bank SMS from a forwarder app")
    srv.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    try:
        config = load(args.config)
        if args.command == "serve":
            serve(config, switch_agent(config), args.port)
            return 0
        at = datetime.now()
        if args.at:
            hh, mm = args.at.split(":")
            at = at.replace(hour=int(hh), minute=int(mm), second=0, microsecond=0)
        agent = None if args.dry_run else switch_agent(config)
        alarm = handle(config, agent, args.sms, at)
    except (ConfigError, SwitchPostError, FileNotFoundError) as exc:
        print(f"bankwatch: {exc}", file=sys.stderr)
        return 1
    if alarm is None:
        print("No alarm: this SMS matches no rule.")
    else:
        print(("Would post:\n" if args.dry_run else "Posted:\n") + alarm)
    return 0


if __name__ == "__main__":
    sys.exit(main())
