"""Ride watch's rules: a check-in timer for someone riding alone at night.

The rider tells Ride watch roughly when they'll arrive. If they haven't said
they reached by then, it asks once; if they still don't answer, it raises the
alarm for the Guardian. A code word raises it at once. Like Bank watch's rules,
this is plain code, not an AI judgement, so it is predictable and tested.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    me: str  # how riders address Ride watch, e.g. "@ride-watch"
    guardian: str
    grace_minutes: int  # after the expected arrival, before asking
    answer_minutes: int  # after asking, before the alarm
    code_word: str  # "" for none


@dataclass
class Ride:
    rider: str
    started: datetime
    eta: datetime
    details: str  # what the rider sent: the app's share-trip text, vehicle, where to
    asked_at: datetime | None = None
    alarmed_at: datetime | None = None
    code_word: bool = False


_DATES = ("started", "eta", "asked_at", "alarmed_at")


class Rides:
    """The rides being watched, one per rider, kept in a JSON file."""

    def __init__(self, by_rider: dict[str, Ride]) -> None:
        self.by_rider = by_rider

    @classmethod
    def load(cls, path: Path) -> Rides:
        if not path.exists():
            return cls({})
        raw = json.loads(path.read_text())
        return cls({
            name: Ride(**{k: datetime.fromisoformat(v) if k in _DATES and v else v for k, v in r.items()})
            for name, r in raw.items()
        })

    def save(self, path: Path) -> None:
        out = {
            name: {k: v.isoformat() if isinstance(v, datetime) else v for k, v in asdict(r).items()}
            for name, r in self.by_rider.items()
        }
        path.write_text(json.dumps(out, indent=2, ensure_ascii=False))


_MENTIONS = re.compile(r"^(\s*@\S+)+")
_DONE = re.compile(r"\b(reached|safe|pahunch\w*|pahuch\w*|done|stop|cancel)\b", re.I)
_MINUTES = re.compile(r"\b(\d{1,3})\s*(?:m|min|mins|minute|minutes)\b", re.I)
_HOURS = re.compile(r"\b(\d{1,2}(?:\.\d)?)\s*(?:h|hr|hrs|hour|hours)\b", re.I)
_CLOCK = re.compile(r"\b(\d{1,2})[:.](\d{2})\s*([ap])?\.?m?\b", re.I)
_MAX_RIDE = timedelta(hours=6)


def arrival(text: str, now: datetime) -> datetime | None:
    """When the rider expects to arrive: "25 min", "1.5 hr", "23:40", "11:40 pm", or a bare "25"."""
    if m := _MINUTES.search(text) or re.fullmatch(r"\s*(\d{1,3})\s*", text):
        return now + timedelta(minutes=int(m[1]))
    if m := _HOURS.search(text):
        return now + timedelta(hours=float(m[1]))
    m = _CLOCK.search(text)
    if not m or int(m[1]) > 23 or int(m[2]) > 59:
        return None
    hour, minute, half = int(m[1]), int(m[2]), (m[3] or "").lower()
    if half:
        hours = [hour % 12 + (12 if half == "p" else 0)]
    else:
        hours = [hour, hour + 12] if 1 <= hour < 12 else [hour]  # "11:40" at night means 23:40
    times = []
    for h in hours:
        t = now.replace(hour=h, minute=minute, second=0, microsecond=0)
        times.append(t + timedelta(days=1) if t < now - timedelta(minutes=30) else t)
    return min(times)


def alarm_text(s: Settings, ride: Ride, now: datetime) -> str:
    if ride.code_word:
        why = f"{ride.rider} sent the code word. They need help and may not be able to talk."
    else:
        asked = ride.asked_at.strftime("%H:%M") if ride.asked_at else "?"
        why = f"{ride.rider} hasn't said they reached. Ride watch asked at {asked} and got no answer."
    lines = [f"🚨 **Ride alarm: {ride.rider}** · {now:%H:%M}", why, ""]
    if ride.details:
        lines += [f"Ride started {ride.started:%H:%M}, expected by {ride.eta:%H:%M}.", "", f"**What {ride.rider} shared**", f"_{ride.details}_"]
    else:
        lines += ["No ride details were shared."]
    return "\n".join(lines + ["", f"{s.guardian} over to you."])


def on_message(rides: Rides, s: Settings, sender: str, body: str, now: datetime) -> list[str]:
    """One message addressed to Ride watch. Returns what to post."""
    text = _MENTIONS.sub("", body).strip()
    ride = rides.by_rider.get(sender)

    if s.code_word and re.search(rf"\b{re.escape(s.code_word)}\b", text, re.I):
        ride = ride or Ride(rider=sender, started=now, eta=now, details="")
        ride.code_word, ride.alarmed_at = True, now
        rides.by_rider[sender] = ride
        return [alarm_text(s, ride, now)]

    eta = arrival(text, now)
    # A start message with a pasted share-trip text may say "safe"; a time with no ride yet means start.
    # A family member can close someone else's ride by naming them: "@ride-watch Riya reached".
    named = [n for n in rides.by_rider if n != sender and re.search(rf"\b{re.escape(n)}\b", text, re.I)]
    if _DONE.search(text) and (eta is None or ride or named):
        rider = named[0] if named else sender
        closed = rides.by_rider.pop(rider, None)
        if closed is None:
            return [f"{sender}, I'm not watching a ride for you. To start one: {s.me} 25 min, or the time you expect to arrive."]
        if closed.alarmed_at:
            return [f"✅ **{rider} has reached.** {s.guardian} close the ride alarm."]
        return [f"✅ Glad you're in, {rider}. Stopped watching."]

    if eta is None:
        if ride:
            return [f"Still watching, {sender}. I'll check on you at {ride.eta + timedelta(minutes=s.grace_minutes):%H:%M}. Send {s.me} reached when you're in."]
        return [
            f"{sender}, tell me when you expect to arrive and I'll check on you: {s.me} 25 min, or {s.me} 23:40. "
            "Paste the ride app's share-trip message in the same line so the family has the vehicle and the link."
        ]
    if eta > now + _MAX_RIDE:
        return [f"{sender}, that's more than 6 hours away ({eta:%a %H:%M}). Send the time again, like {s.me} 40 min."]

    if ride:
        ride.eta, ride.asked_at = eta, None
    else:
        ride = Ride(rider=sender, started=now, eta=eta, details=text)
        rides.by_rider[sender] = ride
    check = eta + timedelta(minutes=s.grace_minutes)
    reply = f"👀 Watching your ride, {sender}. Arriving around {eta:%H:%M}; I'll check on you at {check:%H:%M}. Send {s.me} reached when you're in."
    if ride.alarmed_at:
        reply += f"\n{s.guardian} {sender} is answering now, new arrival {eta:%H:%M}. Keep the alarm open until they say reached."
    return [reply]


def tick(rides: Rides, s: Settings, now: datetime) -> list[str]:
    """Ask riders who are past their time; raise the alarm for those who didn't answer. Returns what to post."""
    out = []
    for ride in rides.by_rider.values():
        if ride.alarmed_at:
            continue
        if ride.asked_at is None and now >= ride.eta + timedelta(minutes=s.grace_minutes):
            ride.asked_at = now
            deadline = now + timedelta(minutes=s.answer_minutes)
            out.append(f"{ride.rider}, have you reached? Send {s.me} reached. If I don't hear from you by {deadline:%H:%M}, I'll alert the family.")
        elif ride.asked_at and now >= ride.asked_at + timedelta(minutes=s.answer_minutes):
            ride.alarmed_at = now
            out.append(alarm_text(s, ride, now))
    return out
