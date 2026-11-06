"""Talking to the family's Switch room, as the Bank watch agent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit


class SwitchPostError(Exception):
    pass


@dataclass(frozen=True)
class SwitchAgent:
    endpoint: str
    token: str
    agent_id: str

    def _call(self, path: str, body: dict[str, Any] | None, what: str, timeout: float = 15) -> Any:
        """POST `body`, or GET when it is None. Returns the JSON reply, or None for 204."""
        # shortcut: calls the endpoint's origin, so a server behind a path prefix needs the full URL here.
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(self.endpoint))
        request = urllib.request.Request(
            f"{origin}/agents/{self.agent_id}/{path}",
            data=None if body is None else json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return None if response.status == 204 else json.load(response)
        except urllib.error.HTTPError as exc:
            raise SwitchPostError(f"Switch refused {what} (HTTP {exc.code}): {exc.read().decode(errors='replace')}") from exc
        except urllib.error.URLError as exc:
            raise SwitchPostError(f"Could not reach Switch at {origin}: {exc.reason}") from exc

    def post(self, room_id: str, content: str) -> str:
        """Send one message to the room; return Switch's event id."""
        return str(self._call("message", {"room_id": room_id, "content": content}, "the alarm")["event_id"])

    def op(self, operation: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Run one Switch agent operation (the same ones agents get as MCP tools)."""
        return dict(self._call(f"ops/{operation}", arguments, operation)["result"])

    def renew(self, room_id: str) -> None:
        """Tell Switch this agent is live in the room. Switch forgets it after 6 seconds."""
        self._call("connection/renew", {"room_id": room_id}, "the liveness heartbeat")

    def events(self, wait_seconds: int) -> list[dict[str, Any]]:
        """Long-poll the agent's events (messages in its rooms); [] when none arrived in time."""
        reply = self._call(f"events?timeout={wait_seconds}", None, "the event poll", timeout=wait_seconds + 15)
        return list(reply["events"]) if reply else []
