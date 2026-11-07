import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock
from urllib.parse import urlencode

from bankwatch.config import ConfigError
from callwatch.__main__ import REJECT, Settings, handle, settings, signature

S = Settings(
    parent="Nani",
    guardian="@guardian",
    voice_url="https://sos.example.com/voice",
    numbers=frozenset({"+919876543210"}),
    auth_token="test-token",
)
AT = datetime(2026, 11, 7, 14, 5)


def call_from(number: str) -> tuple[bytes, str]:
    fields = [("CallSid", "CA1"), ("From", number), ("To", "+15005550006"), ("CallStatus", "ringing")]
    return urlencode(fields).encode(), signature(S.auth_token, S.voice_url, fields)


class SignatureTest(unittest.TestCase):
    def test_matches_twilios_published_example(self):
        fields = [("CallSid", "CA1234567890ABCDE"), ("Caller", "+14158675310"), ("Digits", "1234"), ("From", "+14158675310"), ("To", "+18005551212")]
        self.assertEqual(signature("12345", "https://example.com/myapp.php?foo=1&bar=2", fields), "L/OH5YylLD5NRKLltdqwSvS0BnU=")


class HandleTest(unittest.TestCase):
    def test_parents_call_is_rejected_and_posted(self):
        body, sig = call_from("+919876543210")
        status, reply, text = handle(S, body, sig, AT)
        self.assertEqual((status, reply), (200, REJECT))
        self.assertEqual(text, "📞 **Nani gave a missed call at 14:05. Who's calling Nani?**\n@guardian over to you.")

    def test_unknown_caller_is_rejected_without_a_post(self):
        body, sig = call_from("+911111111111")
        self.assertEqual(handle(S, body, sig, AT), (200, REJECT, None))

    def test_forged_or_unsigned_call_is_refused(self):
        body, sig = call_from("+919876543210")
        self.assertEqual(handle(S, body, "", AT)[0], 403)
        self.assertEqual(handle(S, body.replace(b"CA1", b"CA2"), sig, AT)[0], 403)

    def test_body_that_is_not_a_form(self):
        self.assertEqual(handle(S, b"\xff\xfe", "x", AT)[0], 400)


class SettingsTest(unittest.TestCase):
    def config(self, call: str) -> Path:
        example = (Path(__file__).resolve().parent.parent / "family.example.toml").read_text()
        path = Path(tempfile.mkdtemp()) / "family.toml"
        path.write_text('parent_name = "Nani"\nguardian = "@guardian"\n' + call + "\n" + example[example.index("[rules]"):])
        return path

    def test_numbers_written_with_spaces_match_twilios(self):
        path = self.config('\n[call]\ncredentials = "call-watch/x.json"\npublic_url = "https://sos.example.com/"\nparent_numbers = ["+91 98765 43210"]\n')
        with mock.patch.dict("os.environ", {"TWILIO_AUTH_TOKEN": "t"}):
            _, s = settings(path)
        self.assertEqual(s.voice_url, "https://sos.example.com/voice")
        self.assertEqual(s.numbers, frozenset({"+919876543210"}))

    def test_auth_token_is_required(self):
        path = self.config('\n[call]\ncredentials = "c.json"\npublic_url = "https://x"\nparent_numbers = ["+1"]\n')
        with mock.patch.dict("os.environ", {}, clear=True), self.assertRaises(ConfigError):
            settings(path)


if __name__ == "__main__":
    unittest.main()
