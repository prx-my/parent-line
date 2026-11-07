import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from ridewatch.__main__ import is_for_me, settings
from ridewatch.rides import Rides, Settings, arrival, on_message, tick, trip_details

SHOT = "mxc://switch.local/screenshot1"

S = Settings(me="@ride-watch", guardian="@guardian", grace_minutes=10, answer_minutes=5, code_word="pizza")
NIGHT = datetime(2026, 11, 6, 23, 10)
UBER = "I'm riding with Uber. Track my trip: https://m.uber.com/looking/example · White Dzire KA 20 AB 1234"


def at(hh: int, mm: int, day: int = 6) -> datetime:
    return datetime(2026, 11, day, hh, mm)


class ArrivalTest(unittest.TestCase):
    def test_times(self):
        cases = [
            ("25 min", at(23, 35)),
            ("25", at(23, 35)),
            ("1.5 hr", at(0, 40, 7)),
            ("23:40", at(23, 40)),
            ("11:40", at(23, 40)),  # at night, "11:40" means 23:40
            ("11:40 pm", at(23, 40)),
            ("12.20 am", at(0, 20, 7)),
            ("00:20", at(0, 20, 7)),
            ("23:05", at(23, 5)),  # a few minutes ago still counts as tonight
            ("going home", None),
            ("Rs 245.00", None),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                self.assertEqual(arrival(text, NIGHT), want)


class TripDetailsTest(unittest.TestCase):
    def test_share_messages(self):
        cases = [
            (
                "Ramesh Kumar is driving a White Swift Dzire KA 20 AB 1234. Track my Uber: https://m.uber.com/ul/?id=abc123.",
                {"vehicle": "KA 20 AB 1234", "driver": "Ramesh Kumar", "app": "Uber", "link": "https://m.uber.com/ul/?id=abc123"},
            ),
            (
                "Rapido Captain: Suresh Yadav ★ 4.8, 98765 43210, bike KA05HX4321",
                {"vehicle": "KA 05 HX 4321", "driver": "Suresh Yadav", "rating": "4.8", "phone": "98765 43210", "app": "Rapido"},
            ),
            (
                "Ola cab MH-12-QW-9876 driver name Imran Khan rating 4.55 +91 91234 56789",
                {"vehicle": "MH 12 QW 9876", "driver": "Imran Khan", "rating": "4.55", "phone": "91234 56789", "app": "Ola"},
            ),
            ("Driver arriving in 3 mins. 22 BH 1234 AA", {"vehicle": "22 BH 1234 AA"}),
            ("Refno 431234567890, see you soon", {}),
        ]
        for text, want in cases:
            with self.subTest(text=text):
                self.assertEqual(trip_details(text), want)

    def test_a_correction_wins(self):
        self.assertEqual(trip_details("KA 20 AB 1234\nsorry, it's KA 20 AB 4321")["vehicle"], "KA 20 AB 4321")


class ScreenshotTest(unittest.TestCase):
    def test_screenshot_with_the_time_as_caption(self):
        rides = Rides({})
        [reply] = on_message(rides, S, "Riya", "@ride-watch 25 min", [SHOT], NIGHT)
        self.assertIn("📎 Kept your screenshot", reply)
        self.assertEqual(rides.by_rider["Riya"].screenshots, [SHOT])
        self.assertEqual(rides.by_rider["Riya"].eta, at(23, 35))

    def test_screenshot_after_the_start_reaches_the_guardian(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 25 min", [], NIGHT)
        [added] = on_message(rides, S, "Riya", "@ride-watch", [SHOT], at(23, 12))
        self.assertIn("📝 Added to your ride, Riya. 📎 Kept your screenshot", added)
        self.assertEqual(rides.by_rider["Riya"].eta, at(23, 35))
        tick(rides, S, at(23, 45))
        [alarm] = tick(rides, S, at(23, 50))
        self.assertIn("📎 **Riya sent 1 screenshot of the ride.** Guardian: download and read them", alarm)
        self.assertIn(SHOT, alarm)
        self.assertTrue(alarm.endswith("@guardian over to you."))

    def test_screenshot_alone_does_not_start_a_ride(self):
        rides = Rides({})
        [reply] = on_message(rides, S, "Riya", "@ride-watch", [SHOT], NIGHT)
        self.assertIn("when you expect to arrive", reply)
        self.assertEqual(rides.by_rider, {})

    def test_a_screenshot_never_closes_a_ride(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 25 min", [], NIGHT)
        on_message(rides, S, "Riya", "@ride-watch safe trip", [SHOT], at(23, 12))
        self.assertIn("Riya", rides.by_rider)

    def test_an_otp_typed_by_hand_is_blanked(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 25 min, OTP: 4821, KA 20 AB 1234", [], NIGHT)
        self.assertNotIn("4821", rides.by_rider["Riya"].details)

    def test_old_state_files_still_load(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rides.json"
            path.write_text('{"Riya": {"rider": "Riya", "started": "2026-11-06T23:10:00", "eta": "2026-11-06T23:35:00", "details": "", "asked_at": null, "alarmed_at": null, "code_word": false}}')
            self.assertEqual(Rides.load(path).by_rider["Riya"].screenshots, [])


class RideTest(unittest.TestCase):
    def test_details_sent_after_the_start(self):
        rides = Rides({})
        [start] = on_message(rides, S, "Riya", "@ride-watch 25 min", [], NIGHT)
        self.assertIn("Send the ride app's share-trip message", start)
        # A share message with its own times and "stay safe" adds details; it doesn't move the check-in or close the ride.
        [added] = on_message(rides, S, "Riya", "@ride-watch Rapido Captain: Suresh Yadav ★ 4.8, 98765 43210, KA05HX4321. Arriving in 3 mins, stay safe!", [], at(23, 12))
        self.assertIn("📝 Added to your ride", added)
        self.assertIn("Rapido · KA 05 HX 4321 · Suresh Yadav · ★4.8 · 98765 43210", added)
        self.assertIn("23:45", added)
        self.assertEqual(rides.by_rider["Riya"].eta, at(23, 35))
        [note] = on_message(rides, S, "Riya", "@ride-watch white bike, going via the highway", [], at(23, 13))
        self.assertTrue(note.startswith("📝 Added to your ride, Riya."))
        tick(rides, S, at(23, 45))
        [alarm] = tick(rides, S, at(23, 50))
        self.assertIn("- Vehicle: KA 05 HX 4321", alarm)
        self.assertIn("- Driver: Suresh Yadav · ★4.8 · 98765 43210", alarm)
        self.assertIn("- App: Rapido", alarm)
        self.assertIn("going via the highway", alarm)

    def test_start_reply_says_what_it_got(self):
        rides = Rides({})
        [reply] = on_message(rides, S, "Riya", f"@ride-watch 25 min {UBER}", [], NIGHT)
        self.assertIn("Got: Uber · KA 20 AB 1234 · trip link.", reply)

    def test_a_rating_is_not_a_time(self):
        rides = Rides({})
        [usage] = on_message(rides, S, "Riya", "@ride-watch driver Imran Khan rating 4.55", [], NIGHT)
        self.assertIn("start with when you expect to arrive", usage)
        self.assertEqual(rides.by_rider, {})

    def test_reached_in_time(self):
        rides = Rides({})
        [reply] = on_message(rides, S, "Riya", f"@ride-watch 25 min {UBER}", [], NIGHT)
        self.assertIn("23:35", reply)
        self.assertIn("23:45", reply)  # 25 min + 10 min grace
        self.assertEqual(rides.by_rider["Riya"].details, f"25 min {UBER}")
        self.assertEqual(tick(rides, S, at(23, 44)), [])
        [done] = on_message(rides, S, "Riya", "@ride-watch reached", [], at(23, 40))
        self.assertIn("Stopped watching", done)
        self.assertEqual(rides.by_rider, {})
        self.assertEqual(tick(rides, S, at(23, 59)), [])

    def test_no_answer_raises_alarm_once(self):
        rides = Rides({})
        on_message(rides, S, "Riya", f"@ride-watch 25 min {UBER}", [], NIGHT)
        [ask] = tick(rides, S, at(23, 45))
        self.assertIn("have you reached", ask)
        self.assertIn("23:50", ask)
        self.assertEqual(tick(rides, S, at(23, 49)), [])
        [alarm] = tick(rides, S, at(23, 50))
        self.assertTrue(alarm.startswith("🚨 **Ride alarm: Riya** · 23:50"))
        self.assertIn("KA 20 AB 1234", alarm)
        self.assertIn("https://m.uber.com/looking/example", alarm)
        self.assertTrue(alarm.endswith("@guardian over to you."))
        self.assertEqual(tick(rides, S, at(23, 59)), [])
        [closed] = on_message(rides, S, "Riya", "@ride-watch pahunch gayi", [], at(0, 2, 7))
        self.assertIn("@guardian close the ride alarm", closed)

    def test_code_word_alarms_at_once_without_a_ride(self):
        rides = Rides({})
        [alarm] = on_message(rides, S, "Riya", "@ride-watch pizza", [], NIGHT)
        self.assertIn("code word", alarm)
        self.assertIn("No ride details", alarm)
        self.assertEqual(tick(rides, S, at(23, 59)), [])

    def test_family_closes_by_name(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 10 min", [], NIGHT)
        [closed] = on_message(rides, S, "Arjun", "@ride-watch Riya reached, I called her", [], at(23, 30))
        self.assertIn("Riya", closed)
        self.assertEqual(rides.by_rider, {})

    def test_safe_in_a_pasted_trip_starts_a_ride(self):
        rides = Rides({})
        [reply] = on_message(rides, S, "Riya", "@ride-watch 20 min. Ola: ride safe with us, CRN 123", [], NIGHT)
        self.assertIn("Watching your ride", reply)

    def test_new_time_resets_the_question(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 10 min", [], NIGHT)
        tick(rides, S, at(23, 30))
        on_message(rides, S, "Riya", "@ride-watch traffic, 15 min more", [], at(23, 32))
        self.assertIsNone(rides.by_rider["Riya"].asked_at)
        self.assertEqual(tick(rides, S, at(23, 50)), [])

    def test_unclear_and_too_far(self):
        rides = Rides({})
        [usage] = on_message(rides, S, "Riya", "@ride-watch hi", [], NIGHT)
        self.assertIn("@ride-watch 25 min", usage)
        [far] = on_message(rides, S, "Riya", "@ride-watch 500 min", [], NIGHT)
        self.assertIn("more than 6 hours", far)
        self.assertEqual(rides.by_rider, {})

    def test_state_round_trip(self):
        rides = Rides({})
        on_message(rides, S, "Riya", "@ride-watch 25 min", [], NIGHT)
        tick(rides, S, at(23, 45))
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "rides.json"
            rides.save(path)
            again = Rides.load(path)
        self.assertEqual(again.by_rider, rides.by_rider)
        self.assertEqual(len(tick(again, S, at(23, 50))), 1)


class ServeTest(unittest.TestCase):
    def test_only_people_addressing_it_in_the_room(self):
        msg = {"type": "message", "room_id": "r1", "payload": {"addressed": True, "sender_kind": "user", "sender_name": "Riya", "body": "25 min"}}
        self.assertTrue(is_for_me(msg, "r1"))
        self.assertFalse(is_for_me({**msg, "room_id": "r2"}, "r1"))
        self.assertFalse(is_for_me({**msg, "payload": {**msg["payload"], "addressed": False}}, "r1"))
        self.assertFalse(is_for_me({**msg, "payload": {**msg["payload"], "sender_kind": "agent"}}, "r1"))

    def test_settings_from_example(self):
        example = Path(__file__).resolve().parent.parent / "family.example.toml"
        config, s, state = settings(example)
        self.assertEqual(config.credentials.name, "ride-watch.json")
        self.assertEqual((s.grace_minutes, s.answer_minutes, s.code_word), (10, 5, "pizza"))
        self.assertEqual(state.name, "ridewatch-state.json")


if __name__ == "__main__":
    unittest.main()
