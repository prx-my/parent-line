"""Post a public complaint on X, for the Clerk.

    python3 xpost.py check "text"   # is this draft safe and short enough?
    python3 xpost.py post "text"    # post it (a family member approves this in the room first)

The Clerk runs these from its working directory. `.claude/settings.json` there
makes every `post` wait for a family member to approve it on Switch's approval
card, even when the agent is in auto mode.

Keys: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET in the environment,
or [x] api_key / api_secret / access_token / access_secret in ../family.toml.
Without them `post` refuses and says nothing was posted.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import time
import tomllib
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import quote

ENDPOINT = "https://api.x.com/2/tweets"
LIMIT = 280
KEYS = ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")

_PHONE = re.compile(r"(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_LONG_NUMBER = re.compile(r"\d{10,}")
_URL = re.compile(r"https?://\S+")


def weighted_length(text: str) -> int:
    """X's count: links count 23, most Latin text 1 per character, everything else 2."""
    # shortcut: X's own counter has a few more ranges and counts some emoji sequences as one; this errs on the long side.
    text = _URL.sub("x" * 23, text)
    return sum(
        1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D or 0x2010 <= ord(c) <= 0x201F or 0x2032 <= ord(c) <= 0x2037 else 2
        for c in text
    )


def problems(text: str) -> list[str]:
    """Why this draft must not go out as it is. Empty means it may."""
    found = []
    if not text.strip():
        found.append("the post is empty")
    if (n := weighted_length(text)) > LIMIT:
        found.append(f"it is {n} characters; X allows {LIMIT}")
    if _PHONE.search(text):
        found.append("it contains a phone number")
    if _EMAIL.search(text):
        found.append("it contains an email address")
    if _LONG_NUMBER.search(_PHONE.sub("", text)):
        found.append("it contains a long number (account, card, PNR or UPI reference?); mask it like XXXX1234 or leave it out")
    return found


def _pct(value: str) -> str:
    return quote(value, safe="-._~")


def oauth1_header(method: str, url: str, params: dict[str, str], keys: dict[str, str], *, nonce: str, timestamp: str) -> str:
    """The OAuth 1.0a Authorization header X needs to post as the account. `params`
    are the query or form parameters that are signed; a JSON body is not."""
    oauth = {
        "oauth_consumer_key": keys["X_API_KEY"],
        "oauth_nonce": nonce,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": timestamp,
        "oauth_token": keys["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    pairs = sorted((_pct(k), _pct(v)) for k, v in {**params, **oauth}.items())
    base = "&".join([method.upper(), _pct(url), _pct("&".join(f"{k}={v}" for k, v in pairs))])
    signing_key = f"{_pct(keys['X_API_SECRET'])}&{_pct(keys['X_ACCESS_SECRET'])}"
    oauth["oauth_signature"] = base64.b64encode(hmac.new(signing_key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    return "OAuth " + ", ".join(f'{_pct(k)}="{_pct(v)}"' for k, v in sorted(oauth.items()))


def load_keys(family_toml: Path) -> dict[str, str] | None:
    keys = {k: os.environ.get(k, "") for k in KEYS}
    if not all(keys.values()) and family_toml.exists():
        x = tomllib.loads(family_toml.read_text()).get("x", {})
        on_disk = {"X_API_KEY": "api_key", "X_API_SECRET": "api_secret", "X_ACCESS_TOKEN": "access_token", "X_ACCESS_SECRET": "access_secret"}
        keys = {k: keys[k] or str(x.get(field, "")) for k, field in on_disk.items()}
    return keys if all(keys.values()) else None


def post(text: str, keys: dict[str, str]) -> str:
    """Post and return the post's URL."""
    header = oauth1_header("POST", ENDPOINT, {}, keys, nonce=secrets.token_hex(16), timestamp=str(int(time.time())))
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps({"text": text}).encode(),
        headers={"Authorization": header, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            post_id = json.load(response)["data"]["id"]
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"NOT POSTED: X refused it (HTTP {exc.code}): {exc.read().decode(errors='replace')}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"NOT POSTED: could not reach X: {exc.reason}") from exc
    return f"https://x.com/i/web/status/{post_id}"


def main(argv: list[str]) -> int:
    if len(argv) != 3 or argv[1] not in ("check", "post"):
        print(__doc__, file=sys.stderr)
        return 2
    command, text = argv[1], argv[2]
    found = problems(text)
    if found:
        print("NOT SAFE TO POST: " + "; ".join(found), file=sys.stderr)
        return 1
    if command == "check":
        print(f"OK to post ({weighted_length(text)}/{LIMIT} characters)")
        return 0
    keys = load_keys(Path(__file__).resolve().parent.parent / "family.toml")
    if keys is None:
        print("NOT POSTED: no X keys are set (see the top of xpost.py). The draft is fine; tell the family it was not published.", file=sys.stderr)
        return 3
    print(f"Posted: {post(text, keys)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
