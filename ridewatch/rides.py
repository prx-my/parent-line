"""Ride watch's rules: a check-in timer for someone riding alone at night.

The rider tells Ride watch roughly when they'll arrive. If they haven't said
they reached by then, it asks once; if they still don't answer, it raises the
alarm for the Guardian. A code word raises it at once. Like Bank watch's rules,
this is plain code, not an AI judgement, so it is predictable and tested.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
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
    screenshots: list[str] = field(default_factory=list)  # Switch media ids (mxc://…) of images the rider sent


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

# What a ride app's share message or the rider's own words say about the ride.
_LINK = re.compile(r"https?://[^\s<>\"]+[^\s<>\".,;:!?)]")
_PHONE = re.compile(r"(?<![\d+])(?:\+?91[\s-]?|0)?([6-9]\d{4})[\s-]?(\d{5})(?!\d)")
_PLATE = re.compile(r"\b([A-Z]{2})[\s-]?(\d{1,2})[\s-]?([A-Z]{1,3})[\s-]?(\d{4})\b|\b(\d{2})[\s-]?BH[\s-]?(\d{4})[\s-]?([A-Z]{1,2})\b", re.I)
_RATING = re.compile(r"(?:★|⭐|\brat(?:ing|ed)\b[\s:]*)\s*([1-5](?:\.\d{1,2})?)\b|\b([1-5]\.\d{1,2})\s*(?:★|⭐|stars?\b)", re.I)
_DRIVER = re.compile(
    r"(?i:\b(?:driver|captain)(?:'s)?(?:\s+name)?)\s*(?:is\b|:|-)?\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})"
    r"|\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+is\s+(?:driving|your\s+(?:driver|captain))"
    r"|\b([A-Z][a-z]+(?:\s[A-Z][a-z]+){0,2})\s*[★⭐]\s*[1-5]\.\d"  # a ride app shows the driver's name beside their rating
)
_OTP = re.compile(r"\b(OTP|PIN)\b[\s:#-]*\d{3,6}\b", re.I)
_MAX_SHOWN = 1500  # characters of what the rider sent, in the alarm
_NOT_NAMES = {"Arriving", "Arrived", "Is", "Will", "Has", "Details", "Number", "On", "Here", "Name", "Rating"}
_APP = re.compile(r"\b(ola|uber|rapido|namma\s?yatri|blusmart|indrive|meru|quick\s?ride)\b", re.I)
_APP_NAMES = {"ola": "Ola", "uber": "Uber", "rapido": "Rapido", "nammayatri": "Namma Yatri", "blusmart": "BluSmart", "indrive": "inDrive", "meru": "Meru", "quickride": "Quick Ride"}


def _last(pattern: re.Pattern[str], text: str) -> re.Match[str] | None:
    """The last match: details arrive in order, so a correction wins."""
    found = list(pattern.finditer(text))
    return found[-1] if found else None


def trip_details(text: str) -> dict[str, str]:
    """Vehicle, driver, rating, phone, app and trip link, where the text has them. Empty when it has none."""
    out: dict[str, str] = {}
    if m := _last(_PLATE, text):
        out["vehicle"] = (" ".join(m.group(1, 2, 3, 4)) if m[1] else f"{m[5]} BH {m[6]} {m[7]}").upper()
    names = [n for m in _DRIVER.finditer(text) if (n := m[1] or m[2] or m[3]) and n.split()[0] not in _NOT_NAMES]
    if names:
        out["driver"] = names[-1]
    if m := _last(_RATING, text):
        out["rating"] = m[1] or m[2]
    if m := _last(_PHONE, text):
        out["phone"] = f"{m[1]} {m[2]}"
    if m := _last(_APP, text):
        out["app"] = _APP_NAMES[re.sub(r"\s", "", m[1].lower())]
    if m := _last(_LINK, text):
        out["link"] = m[0]
    return out


def _summary(d: dict[str, str]) -> str:
    driver = " · ".join(x for x in (d.get("driver"), d.get("rating") and f"★{d['rating']}", d.get("phone")) if x)
    return " · ".join(x for x in (d.get("app"), d.get("vehicle"), driver, d.get("link") and "trip link") if x)


def _without_details(text: str) -> str:
    """The text with links, phone numbers, plates and ratings blanked, so none of them reads as a time."""
    for pattern in (_LINK, _PHONE, _PLATE, _RATING):
        text = pattern.sub(" ", text)
    return text


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
    if not ride.details and not ride.screenshots:
        return "\n".join(lines + ["No ride details were shared.", "", f"{s.guardian} over to you."])
    lines.append(f"Ride started {ride.started:%H:%M}, expected by {ride.eta:%H:%M}.")
    if ride.details:
        d = trip_details(ride.details)
        driver = " · ".join(x for x in (d.get("driver"), d.get("rating") and f"★{d['rating']}", d.get("phone")) if x)
        for label, value in (("Vehicle", d.get("vehicle")), ("Driver", driver), ("App", d.get("app")), ("Trip link", d.get("link"))):
            if value:
                lines.append(f"- {label}: {value}")
        sent = ride.details if len(ride.details) <= _MAX_SHOWN else ride.details[:_MAX_SHOWN] + "…"
        lines += ["", f"**Everything {ride.rider} sent**", f"_{sent}_"]
    if ride.screenshots:
        n = len(ride.screenshots)
        lines += [
            "",
            f"📎 **{ride.rider} sent {n} screenshot{'s' if n > 1 else ''} of the ride.** "
            "Guardian: download and read them, and put the vehicle, driver and phone in your message:",
            *ride.screenshots,
        ]
    return "\n".join(lines + ["", f"{s.guardian} over to you."])


def on_message(rides: Rides, s: Settings, sender: str, body: str, screenshots: list[str], now: datetime) -> list[str]:
    """One message addressed to Ride watch, with the media ids of any images on it. Returns what to post.

    Ride watch never reads a screenshot: it keeps the id, and the Guardian reads it if the alarm fires.
    Typed ride OTPs are blanked before anything is kept or posted.
    """
    text = _OTP.sub(r"\1 ••••", _MENTIONS.sub("", body).strip())
    ride = rides.by_rider.get(sender)
    kept = " 📎 Kept your screenshot: if I raise the alarm, the Guardian reads it for the family." if screenshots else ""

    if s.code_word and re.search(rf"\b{re.escape(s.code_word)}\b", text, re.I):
        ride = ride or Ride(rider=sender, started=now, eta=now, details="")
        ride.code_word, ride.alarmed_at = True, now
        rides.by_rider[sender] = ride
        return [alarm_text(s, ride, now)]

    found = trip_details(text)
    eta = arrival(_without_details(text), now)
    # A family member can close someone else's ride by naming them: "@ride-watch Riya reached".
    named = [n for n in rides.by_rider if n != sender and re.search(rf"\b{re.escape(n)}\b", text, re.I)]
    # A pasted share message may say "stay safe", so a message carrying trip details never closes a ride,
    # and a time with no ride yet means start.
    if not found and not screenshots and _DONE.search(text) and (eta is None or ride or named):
        rider = named[0] if named else sender
        closed = rides.by_rider.pop(rider, None)
        if closed is None:
            return [f"{sender}, I'm not watching a ride for you. To start one: {s.me} 25 min, or the time you expect to arrive."]
        if closed.alarmed_at:
            return [f"✅ **{rider} has reached.** {s.guardian} close the ride alarm."]
        return [f"✅ Glad you're in, {rider}. Stopped watching."]

    if ride and (found or screenshots or (eta is None and text)):
        # More about the ride being watched. A share message's own times ("driver 3 mins away") don't move the check-in;
        # to change it, send just the time.
        ride.details = f"{ride.details}\n{text}".strip()
        ride.screenshots += screenshots
        got = _summary(trip_details(ride.details))
        check = ride.eta + timedelta(minutes=s.grace_minutes)
        return [f"📝 Added to your ride, {sender}." + (f" Got: {got}." if got else "") + kept + f" I'll check on you at {check:%H:%M}."]
    if eta is None:
        if ride:
            return [f"Still watching, {sender}. I'll check on you at {ride.eta + timedelta(minutes=s.grace_minutes):%H:%M}. Send {s.me} reached when you're in."]
        if screenshots:
            return [
                f"{sender}, I need to know when you expect to arrive before I can keep your screenshot. "
                f"Send it again with the caption {s.me} 25 min, or send {s.me} 25 min first and then the screenshot."
            ]
        return [
            f"{sender}, start with when you expect to arrive and I'll check on you: {s.me} 25 min, or {s.me} 23:40. "
            "Then send the ride app's share-trip message, a screenshot of the driver's details, or the vehicle number and driver's name, so the family has them."
        ]
    if eta > now + _MAX_RIDE:
        return [f"{sender}, that's more than 6 hours away ({eta:%a %H:%M}). Send the time again, like {s.me} 40 min."]

    if ride:
        ride.eta, ride.asked_at = eta, None
        ride.details = f"{ride.details}\n{text}".strip()
    else:
        ride = Ride(rider=sender, started=now, eta=eta, details=text, screenshots=list(screenshots))
        rides.by_rider[sender] = ride
    check = eta + timedelta(minutes=s.grace_minutes)
    reply = f"👀 Watching your ride, {sender}. Arriving around {eta:%H:%M}; I'll check on you at {check:%H:%M}. Send {s.me} reached when you're in."
    if got := _summary(trip_details(ride.details)):
        reply += f"\nGot: {got}."
    if kept:
        reply += "\n" + kept.strip()
    elif not got:
        reply += f"\nSend the ride app's share-trip message, a screenshot of the driver's details, or the vehicle number and driver's name, with {s.me} so the family has them."
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
