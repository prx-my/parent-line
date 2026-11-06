"""Read an Indian bank SMS into what Bank watch needs: what kind of event, how
much, and to whom.

Every bank words its SMS differently, so this reads the parts most of them
share (a currency amount, "debited"/"sent", "to <name>") rather than one bank's
template. Anything it can't place is kind "other" and raises no alarm.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal

_AMOUNT = r"(\d[\d,]*(?:\.\d{1,2})?)"
_CURRENCY_AMOUNT = re.compile(rf"(?:rs\.?|inr|₹)\s*{_AMOUNT}", re.IGNORECASE)
_BARE_DEBIT_AMOUNT = re.compile(rf"debited\s+(?:by|for|with)\s+{_AMOUNT}", re.IGNORECASE)

_DEBIT = re.compile(r"\b(debited|sent|paid|spent|withdrawn|transferred|trf)\b", re.IGNORECASE)
_CREDIT_ONLY = re.compile(r"\bcredited to your\b|\bhas been credited\b|\breceived\b", re.IGNORECASE)
_FD_BREAK = re.compile(
    r"\b(fixed deposit|fd|term deposit)\b.*\b(closed|pre-?closed|premature|broken|liquidated)\b"
    r"|\b(premature|pre-?mature)\s+(closure|withdrawal)\b",
    re.IGNORECASE,
)
_LOAN = re.compile(r"\b(loan|overdraft|od)\b.*\b(disbursed|sanctioned|credited|availed)\b", re.IGNORECASE)
_PAYEE_ADDED = re.compile(r"\b(beneficiary|payee)\b.*\b(added|registered|activated)\b", re.IGNORECASE)

# Where a payee name usually sits.
# shortcut: banks write payee names in capitals, so only all-caps words are read as a name; a bank that writes "Rakesh Kumar" gives no payee.
_NAME = r"([A-Z][A-Z.&']*\b(?:\s+[A-Z][A-Z.&']*\b){0,4})"
_PAYEE_PATTERNS = [
    re.compile(rf"\b(?:trf|transfer(?:red)?|sent|paid)\s+to\s+{_NAME}"),
    re.compile(rf"\b(?:RTGS|NEFT|IMPS|UPI)\s+to\s+{_NAME}"),
    re.compile(rf"\bTo\s+{_NAME}\s+(?:On|on|Ref|ref)\b"),
    re.compile(rf";\s*{_NAME}\s+credited\b"),
    re.compile(rf"\b(?i:beneficiary|payee)\s+{_NAME}\s+(?i:has been\s+)?(?i:added|registered)"),
]
_REF = re.compile(r"\b(?:ref(?:\s*no)?|refno|utr|upi)[\s.:#-]*([A-Z0-9]{6,})", re.IGNORECASE)
# Words a payee pattern can catch that are never a payee.
_NOT_A_NAME = {"your", "you", "a/c", "ac", "account", "on", "ref", "not", "call", "the"}


@dataclass(frozen=True)
class BankEvent:
    kind: str  # "debit", "fd_break", "loan", "payee_added" or "other"
    amount: Decimal | None
    payee: str | None
    ref: str | None
    text: str


def _amount(text: str) -> Decimal | None:
    match = _CURRENCY_AMOUNT.search(text) or _BARE_DEBIT_AMOUNT.search(text)
    if not match:
        return None
    return Decimal(match.group(1).replace(",", ""))


def _payee(text: str) -> str | None:
    for pattern in _PAYEE_PATTERNS:
        match = pattern.search(text)
        if match:
            name = match.group(1).strip(" .")
            if name.lower() not in _NOT_A_NAME:
                return name
    return None


def _ref(text: str) -> str | None:
    match = _REF.search(text)
    return match.group(1) if match else None


def parse(text: str) -> BankEvent:
    text = " ".join(text.split())
    if _FD_BREAK.search(text):
        kind = "fd_break"
    elif _LOAN.search(text):
        kind = "loan"
    elif _PAYEE_ADDED.search(text):
        kind = "payee_added"
    elif _DEBIT.search(text) and not _CREDIT_ONLY.search(text):
        kind = "debit"
    else:
        kind = "other"
    return BankEvent(kind=kind, amount=_amount(text), payee=_payee(text), ref=_ref(text), text=text)
