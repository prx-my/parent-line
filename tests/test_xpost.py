import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "clerk"))

import xpost  # noqa: E402


class XPostTest(unittest.TestCase):
    def test_signature_matches_the_published_oauth1_example(self):
        # The worked example from Twitter's "Creating a signature" guide.
        keys = {
            "X_API_KEY": "xvz1evFS4wEEPTGEFPHBog",
            "X_API_SECRET": "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
            "X_ACCESS_TOKEN": "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
            "X_ACCESS_SECRET": "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE",
        }
        header = xpost.oauth1_header(
            "POST",
            "https://api.twitter.com/1.1/statuses/update.json",
            {"include_entities": "true", "status": "Hello Ladies + Gentlemen, a signed OAuth request!"},
            keys,
            nonce="kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg",
            timestamp="1318622958",
        )
        self.assertIn('oauth_signature="hCtSmYh%2BiHYCEqBWrE7C7hYmtUk%3D"', header)

    def test_safe_draft_passes(self):
        draft = "@RideCo_Support A rider on booking CRN8841207 in Jaipur on 6 Nov, 21:10 was stopped and pressured by the driver. Please investigate and reply. #RiderSafety"
        self.assertEqual(xpost.problems(draft), [])

    def test_personal_details_are_refused(self):
        self.assertIn("it contains a phone number", xpost.problems("call her on +91 98765 43210"))
        self.assertIn("it contains a phone number", xpost.problems("call 9876543210"))
        self.assertIn("it contains an email address", xpost.problems("mail ramesh.sharma@example.com"))
        self.assertTrue(any("long number" in p for p in xpost.problems("UPI ref 431234567890")))
        self.assertEqual(xpost.problems("account XXXX1234"), [])

    def test_length_counts_links_and_wide_characters(self):
        self.assertEqual(xpost.weighted_length("hi https://example.com/a/very/long/path/that/goes/on"), 3 + 23)
        self.assertEqual(xpost.weighted_length("नमस्ते"), 6)  # Devanagari counts 1, like Latin
        self.assertEqual(xpost.weighted_length("🙏"), 2)
        self.assertTrue(any("X allows 280" in p for p in xpost.problems("a" * 281)))

    def test_post_without_keys_says_nothing_was_posted(self):
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {k: "" for k in xpost.KEYS}), mock.patch.object(xpost, "load_keys", return_value=None):
            self.assertEqual(xpost.main(["xpost.py", "post", "A safe post"]), 3)

    def test_intent_link_carries_the_exact_draft_and_needs_no_keys(self):
        import io
        from contextlib import redirect_stdout
        from urllib.parse import parse_qs, urlsplit

        draft = "@SBI_Support ₹7,55,000 taken in a scam & no reply. Please block XXXX1234?"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(xpost.main(["xpost.py", "intent", draft]), 0)
        url = urlsplit(out.getvalue().strip())
        self.assertEqual((url.scheme, url.netloc, url.path), ("https", "x.com", "/intent/post"))
        self.assertEqual(parse_qs(url.query)["text"], [draft])

    def test_intent_refuses_an_unsafe_draft(self):
        self.assertEqual(xpost.main(["xpost.py", "intent", "call 9876543210"]), 1)


if __name__ == "__main__":
    unittest.main()
