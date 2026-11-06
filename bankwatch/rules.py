"""The rules that decide whether a bank SMS wakes the family.

Plain code on purpose: whether money raises an alarm has to be predictable and
testable, not an AI's judgement.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

from bankwatch.parse import BankEvent


@dataclass(frozen=True)
class Rules:
    large_debit: Decimal
    new_payee_min: Decimal
    burst_count: int
    burst_minutes: int
    burst_min_total: Decimal
    night_start: time
    night_end: time
    night_min: Decimal


def _rupees(amount: Decimal) -> str:
    """Indian digit grouping: 480000 -> ₹4,80,000."""
    whole = str(int(amount))
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups) + "," + tail
    paise = amount - int(amount)
    return f"₹{whole}" + (f"{paise:.2f}"[1:] if paise else "")


def _norm(payee: str) -> str:
    return " ".join(payee.upper().split())


def report_by(at: datetime) -> date:
    """The last day to report an unauthorised debit to the bank and owe nothing.

    RBI's 2017 customer-liability circular: zero liability when a third party's
    fraud is reported within three working days of the bank's message.
    """
    # shortcut: counts every day but Sunday as a working day; bank holidays and 2nd/4th Saturdays only push the real deadline later, so this date is never too late. Use a bank-holiday calendar if families need the exact date.
    day, counted = at.date(), 0
    while counted < 3:
        day += timedelta(days=1)
        if day.weekday() != 6:
            counted += 1
    return day


@dataclass
class Case:
    """A debit the family was alarmed about, open until its reporting deadline passes."""

    opened: datetime
    report_by: date
    summary: str
    reminded: bool = False


def _at_night(rules: Rules, at: datetime) -> bool:
    now = at.time()
    if rules.night_start <= rules.night_end:
        return rules.night_start <= now < rules.night_end
    return now >= rules.night_start or now < rules.night_end


@dataclass
class State:
    """What Bank watch remembers between SMS: payees seen before, recent debits,
    and which SMS it already handled (forwarder apps resend)."""

    known_payees: set[str] = field(default_factory=set)
    recent_debits: list[tuple[datetime, Decimal]] = field(default_factory=list)
    handled: dict[str, datetime] = field(default_factory=dict)
    cases: list[Case] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path, seed_payees: list[str]) -> State:
        state = cls(known_payees={_norm(p) for p in seed_payees})
        if path.exists():
            raw = json.loads(path.read_text())
            state.known_payees |= set(raw["known_payees"])
            state.recent_debits = [(datetime.fromisoformat(t), Decimal(a)) for t, a in raw["recent_debits"]]
            state.handled = {k: datetime.fromisoformat(v) for k, v in raw["handled"].items()}
            state.cases = [
                Case(datetime.fromisoformat(c["opened"]), date.fromisoformat(c["report_by"]), c["summary"], c["reminded"])
                for c in raw.get("cases", [])
            ]
        return state

    def save(self, path: Path) -> None:
        raw = {
            "known_payees": sorted(self.known_payees),
            "recent_debits": [[t.isoformat(), str(a)] for t, a in self.recent_debits],
            "handled": {k: v.isoformat() for k, v in self.handled.items()},
            "cases": [
                {"opened": c.opened.isoformat(), "report_by": c.report_by.isoformat(), "summary": c.summary, "reminded": c.reminded}
                for c in self.cases
            ],
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(raw, indent=2))
        tmp.replace(path)

    def already_handled(self, text: str, at: datetime) -> bool:
        seen = self.handled.get(text)
        return seen is not None and at - seen < timedelta(hours=1)

    def record(self, event: BankEvent, at: datetime, alarmed: bool) -> None:
        """Remember an SMS once it has been dealt with (alarm posted, or none needed)."""
        self.handled[event.text] = at
        self.handled = {k: v for k, v in self.handled.items() if at - v < timedelta(hours=1)}
        if event.kind == "debit" and event.amount is not None:
            self.recent_debits.append((at, event.amount))
            self.recent_debits = [(t, a) for t, a in self.recent_debits if at - t < timedelta(days=1)]
        # A payee is learnt only from a debit that raised no alarm, so a
        # scammer's account stays "new" for every later transfer to it.
        if event.kind == "debit" and event.payee and not alarmed:
            self.known_payees.add(_norm(event.payee))
        if event.kind == "debit" and alarmed:
            what = _rupees(event.amount) if event.amount is not None else "Money"
            to = f" to {event.payee}" if event.payee else ""
            self.cases.append(Case(at, report_by(at), f"{what}{to} at {at:%H:%M} on {at:%a %-d %b}"))

    def due_reminders(self, now: datetime) -> list[Case]:
        """Cases whose deadline ends within the next 24 hours, each returned once.
        Cases past their deadline are dropped."""
        due = []
        for case in self.cases:
            end = datetime.combine(case.report_by, time.max)
            if not case.reminded and end - timedelta(hours=24) <= now <= end:
                case.reminded = True
                due.append(case)
        self.cases = [c for c in self.cases if now <= datetime.combine(c.report_by, time.max)]
        return due


def reminder_text(*, clerk: str, parent: str, case: Case) -> str:
    return "\n".join([
        f"⏰ **Report {parent}'s debit to the bank by {case.report_by:%a %-d %b}**",
        case.summary,
        f"If {parent} didn't make this payment, reporting it by then means {parent} shouldn't bear the loss (RBI rules).",
        "If they were tricked into paying, report anyway: fast reports are how money gets frozen.",
        "",
        f"{clerk} has it been reported? Post the bank's complaint number.",
    ])


def reasons(rules: Rules, state: State, event: BankEvent, at: datetime) -> list[str]:
    """Why this SMS should wake the family. Empty means it shouldn't."""
    if event.kind == "fd_break":
        return ["breaking an FD early is how these scams raise a big \"security deposit\""]
    if event.kind == "loan":
        return ["a sudden loan or overdraft often follows once the savings are gone"]
    if event.kind == "payee_added":
        return ["a new payee is usually added just before a large transfer"]
    if event.kind != "debit" or event.amount is None:
        return []

    found = []
    amount = event.amount
    if amount >= rules.large_debit:
        found.append(f"over the {_rupees(rules.large_debit)} limit")
    if event.payee and _norm(event.payee) not in state.known_payees and amount >= rules.new_payee_min:
        found.append("sent to a payee never paid before")
    window = at - timedelta(minutes=rules.burst_minutes)
    burst = [a for t, a in state.recent_debits if window <= t <= at] + [amount]
    # The debit that trips the burst must carry its share of the total, so a
    # small shop payment inside the hour doesn't raise the alarm on its own.
    fair_share = rules.burst_min_total / rules.burst_count
    if len(burst) >= rules.burst_count and sum(burst) >= rules.burst_min_total and amount >= fair_share:
        found.append(f"{len(burst)} debits within {rules.burst_minutes} minutes, {_rupees(sum(burst, Decimal(0)))} in all")
    if _at_night(rules, at) and amount >= rules.night_min:
        found.append(f"late at night ({at:%H:%M})")
    return found


def alarm_text(*, guardian: str, parent: str, event: BankEvent, why: list[str], at: datetime) -> str:
    """The message posted in the family group, in the Markdown Switch renders
    on every chat platform (bold, bullets, italics)."""
    amount = f"**{_rupees(event.amount)}**" if event.amount is not None else None
    payee = f"**{event.payee}**" if event.payee else None
    headline = {
        "debit": f"{amount or 'Money'} left the account" + (f" to {payee}" if payee else ""),
        "fd_break": "A fixed deposit was broken early" + (f", {amount}" if amount else ""),
        "loan": "A loan was taken" + (f", {amount}" if amount else ""),
        "payee_added": "A new payee was added" + (f": {payee}" if payee else ""),
    }[event.kind]
    lines = [
        f"🚨 **Bank alarm: {parent}** · {at:%H:%M}",
        f"{headline}.",
        "",
        "**Why it looks wrong**",
        *(f"- {reason[0].upper()}{reason[1:]}" for reason in why),
        "",
        # Italic marks would show literally around text that has its own underscores.
        "**Bank SMS**\n" + (event.text if "_" in event.text else f"_{event.text}_"),
        "",
        *(
            [f"**Report to the bank by {report_by(at):%a %-d %b}.** If {parent} didn't make this payment, reporting by then means {parent} shouldn't bear the loss (RBI rules).", ""]
            if event.kind == "debit"
            else []
        ),
        f"{guardian} over to you.",
    ]
    return "\n".join(lines)
