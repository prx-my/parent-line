import json
import tempfile
import unittest
from datetime import datetime, time
from decimal import Decimal
from pathlib import Path

from bankwatch.__main__ import _sms_text, handle
from bankwatch.config import Config
from bankwatch.parse import parse
from bankwatch.rules import Rules, State, _rupees, reasons

RULES = Rules(
    large_debit=Decimal(50000),
    new_payee_min=Decimal(10000),
    burst_count=3,
    burst_minutes=60,
    burst_min_total=Decimal(25000),
    night_start=time(22, 0),
    night_end=time(6, 0),
    night_min=Decimal(5000),
)
NOON = datetime(2026, 11, 6, 12, 0)

SBI_UPI = "Dear UPI user A/C X1234 debited by 480000.00 on date 06Nov26 trf to RAKESH KUMAR Refno 431234567890. If not u? call 1800111109. -SBI"
HDFC_UPI = "Sent Rs.4800.00 From HDFC Bank A/C *1234 To SHARMA KIRANA STORE On 06/11/26 Ref 431234567891 Not You? Call 18002586161/SMS BLOCK UPI to 7308080808"
ICICI_UPI = "ICICI Bank Acct XX123 debited for Rs 1,20,000.00 on 06-Nov-26; MOHIT VERMA credited. UPI:431234567892. Call 18002662 for dispute."
RTGS = "INR 4,80,000.00 debited from A/c XX1234 on 06-Nov-26 for RTGS to SAFE CUSTODY ACCOUNT. Avl Bal INR 12,345.00"
CREDIT = "Rs 5000.00 credited to your A/c XX1234 on 06-Nov-26 by NEFT from PENSION OFFICE. Avl Bal Rs 25,000"
FD = "Your Fixed Deposit No XXXX5678 has been closed prematurely on 06-Nov-26. Proceeds Rs 9,00,000 credited to A/c XX1234."
LOAN = "Your Personal Loan of Rs 3,00,000 has been disbursed to A/c XX1234 on 06-Nov-26."
PAYEE = "Beneficiary RAKESH KUMAR has been added to your account XX1234. Not you? Call 1800111109"
OTP = "123456 is your OTP for login. Do not share it with anyone."


class ParseTest(unittest.TestCase):
    def test_banks(self):
        cases = [
            (SBI_UPI, "debit", Decimal("480000.00"), "RAKESH KUMAR"),
            (HDFC_UPI, "debit", Decimal("4800.00"), "SHARMA KIRANA STORE"),
            (ICICI_UPI, "debit", Decimal("120000.00"), "MOHIT VERMA"),
            (RTGS, "debit", Decimal("480000.00"), "SAFE CUSTODY ACCOUNT"),
            (CREDIT, "other", Decimal("5000.00"), None),
            (FD, "fd_break", Decimal("900000"), None),
            (LOAN, "loan", Decimal("300000"), None),
            (PAYEE, "payee_added", None, "RAKESH KUMAR"),
            (OTP, "other", None, None),
        ]
        for text, kind, amount, payee in cases:
            with self.subTest(text=text[:30]):
                event = parse(text)
                self.assertEqual(event.kind, kind)
                self.assertEqual(event.amount, amount)
                if kind != "other":
                    self.assertEqual(event.payee, payee)

    def test_reference_is_kept_for_the_complaint(self):
        self.assertEqual(parse(SBI_UPI).ref, "431234567890")


class RulesTest(unittest.TestCase):
    def state(self, *payees):
        return State(known_payees=set(payees))

    def test_small_known_debit_is_quiet(self):
        self.assertEqual(reasons(RULES, self.state("SHARMA KIRANA STORE"), parse(HDFC_UPI), NOON), [])

    def test_large_debit_to_new_payee(self):
        why = reasons(RULES, self.state(), parse(SBI_UPI), NOON)
        self.assertEqual(why, ["over the ₹50,000 limit", "sent to a payee never paid before"])

    def test_credit_never_alarms(self):
        self.assertEqual(reasons(RULES, self.state(), parse(CREDIT), datetime(2026, 11, 6, 23, 30)), [])

    def test_fd_loan_and_payee_always_alarm(self):
        for text in (FD, LOAN, PAYEE):
            self.assertTrue(reasons(RULES, self.state(), parse(text), NOON))

    def test_night(self):
        small = parse("Rs 6,000 debited from A/c XX1 to SHARMA KIRANA STORE")
        self.assertEqual(reasons(RULES, self.state("SHARMA KIRANA STORE"), small, datetime(2026, 11, 6, 23, 40)), ["late at night (23:40)"])
        self.assertEqual(reasons(RULES, self.state("SHARMA KIRANA STORE"), small, NOON), [])

    def test_split_transfers_add_up(self):
        state = self.state("MOHIT VERMA")
        piece = parse("Rs 9,000 debited from A/c XX1 trf to MOHIT VERMA")
        for minute in (0, 20):
            self.assertEqual(reasons(RULES, state, piece, NOON.replace(minute=minute)), [])
            state.record(piece, NOON.replace(minute=minute), alarmed=False)
        self.assertEqual(reasons(RULES, state, piece, NOON.replace(minute=40)), ["3 debits within 60 minutes, ₹27,000 in all"])
        state.record(piece, NOON.replace(minute=40), alarmed=True)
        shop = parse("Sent Rs.480.00 From HDFC Bank A/C *1 To SHARMA KIRANA STORE On 06/11/26")
        self.assertEqual(reasons(RULES, state, shop, NOON.replace(minute=50)), [])

    def test_burst_ignores_debits_outside_the_window(self):
        state = self.state("MOHIT VERMA")
        big = parse("Rs 4,80,000 debited from A/c XX1 trf to MOHIT VERMA")
        state.record(big, NOON.replace(hour=23, minute=40), alarmed=True)
        state.record(big, NOON.replace(hour=10), alarmed=True)
        piece = parse("Rs 9,000 debited from A/c XX1 trf to MOHIT VERMA")
        self.assertEqual(reasons(RULES, state, piece, NOON), [])

    def test_scammer_payee_is_never_learnt(self):
        state = self.state()
        event = parse(SBI_UPI)
        state.record(event, NOON, alarmed=True)
        self.assertNotIn("RAKESH KUMAR", state.known_payees)
        state.record(parse(HDFC_UPI), NOON, alarmed=False)
        self.assertIn("SHARMA KIRANA STORE", state.known_payees)

    def test_rupees(self):
        self.assertEqual(_rupees(Decimal("480000")), "₹4,80,000")
        self.assertEqual(_rupees(Decimal("12345678.50")), "₹1,23,45,678.50")
        self.assertEqual(_rupees(Decimal("999")), "₹999")


class FakeAgent:
    def __init__(self, fail=False):
        self.posts, self.fail = [], fail

    def post(self, room_id, content):
        from bankwatch.switch import SwitchPostError

        if self.fail:
            raise SwitchPostError("down")
        self.posts.append((room_id, content))
        return "event-1"


class HandleTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.config = Config(
            parent_name="Mom",
            guardian="@guardian",
            room_id="room-1",
            webhook_secret="s",
            state_file=Path(self.dir.name) / "state.json",
            known_payees=["SHARMA KIRANA STORE"],
            rules=RULES,
            credentials=None,
        )

    def tearDown(self):
        self.dir.cleanup()

    def test_alarm_is_posted_once(self):
        agent = FakeAgent()
        alarm = handle(self.config, agent, SBI_UPI, datetime(2026, 11, 6, 23, 40))
        self.assertEqual(len(agent.posts), 1)
        self.assertEqual(agent.posts[0][0], "room-1")
        self.assertEqual(
            alarm,
            "🚨 **Bank alarm: Mom** · 23:40\n"
            "**₹4,80,000** left the account to **RAKESH KUMAR**.\n"
            "\n"
            "**Why it looks wrong**\n"
            "- Over the ₹50,000 limit\n"
            "- Sent to a payee never paid before\n"
            "- Late at night (23:40)\n"
            "\n"
            "**Bank SMS**\n"
            f"_{SBI_UPI}_\n"
            "\n"
            "@guardian over to you.",
        )
        # The forwarder resends: no second alarm.
        self.assertIsNone(handle(self.config, agent, SBI_UPI, datetime(2026, 11, 6, 23, 41)))
        self.assertEqual(len(agent.posts), 1)

    def test_failed_post_is_not_recorded_so_a_retry_alarms(self):
        from bankwatch.switch import SwitchPostError

        with self.assertRaises(SwitchPostError):
            handle(self.config, FakeAgent(fail=True), SBI_UPI, NOON)
        agent = FakeAgent()
        handle(self.config, agent, SBI_UPI, NOON.replace(minute=1))
        self.assertEqual(len(agent.posts), 1)

    def test_quiet_sms_posts_nothing(self):
        agent = FakeAgent()
        self.assertIsNone(handle(self.config, agent, HDFC_UPI, NOON))
        self.assertEqual(agent.posts, [])

    def test_forwarder_bodies(self):
        self.assertEqual(_sms_text(json.dumps({"message": "hi"}).encode(), "application/json"), "hi")
        self.assertEqual(_sms_text(b"plain sms", "text/plain"), "plain sms")
        with self.assertRaises(ValueError):
            _sms_text(b'{"from": "x"}', "application/json")


if __name__ == "__main__":
    unittest.main()
