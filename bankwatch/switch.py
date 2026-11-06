"""Posting the alarm into the family's Switch room, as the Bank watch agent."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlsplit


class SwitchPostError(Exception):
    pass


@dataclass(frozen=True)
class SwitchAgent:
    endpoint: str
    token: str
    agent_id: str

    def post(self, room_id: str, content: str) -> str:
        """Send one message to the room; return Switch's event id."""
        # shortcut: posts to the endpoint's origin, so a server behind a path prefix needs the full URL here.
        origin = "{0.scheme}://{0.netloc}".format(urlsplit(self.endpoint))
        request = urllib.request.Request(
            f"{origin}/agents/{self.agent_id}/message",
            data=json.dumps({"room_id": room_id, "content": content}).encode(),
            headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                return str(json.load(response)["event_id"])
        except urllib.error.HTTPError as exc:
            raise SwitchPostError(f"Switch refused the alarm (HTTP {exc.code}): {exc.read().decode(errors='replace')}") from exc
        except urllib.error.URLError as exc:
            raise SwitchPostError(f"Could not reach Switch at {origin}: {exc.reason}") from exc
