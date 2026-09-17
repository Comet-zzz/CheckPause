import json
import unittest

from checkpause.core.updater import (
    MANIFEST_URLS,
    UpdateCheckError,
    UpdateInfo,
    check_for_update,
    is_newer,
    parse_version,
)


def _is_url_map(value):
    """A {url: response} map is told apart from a manifest by its keys."""
    return isinstance(value, dict) and all(
        isinstance(key, str) and key.startswith("http") for key in value
    )


class FakeOpener:
    """Stands in for urllib so the tests never touch the network.

    `responses` is either a single response applied to every URL, or a
    {url: response} mapping. A response may be a dict (encoded as JSON),
    raw bytes, or an exception instance to raise.
    """

    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        response = self._responses
        if _is_url_map(response):
            response = self._responses.get(url)
        if isinstance(response, Exception):
            raise response
        if response is None:
            raise OSError("no response configured")
        if isinstance(response, bytes):
            return response
        return json.dumps(response).encode("utf-8")


class VersionTests(unittest.TestCase):
    def test_parse_version_splits_on_dots(self):
        self.assertEqual(parse_version("1.5.1"), (1, 5, 1))

    def test_parse_version_tolerates_junk(self):
        self.assertEqual(parse_version("1.5"), (1, 5))
        self.assertEqual(parse_version(""), (0,))

    def test_is_newer(self):
        self.assertTrue(is_newer("1.5.1", "1.5.0"))
        self.assertTrue(is_newer("1.6", "1.5.9"))
        self.assertTrue(is_newer("1.5.0.1", "1.5.0"))

    def test_is_not_newer(self):
        self.assertFalse(is_newer("1.5.0", "1.5.0"))
        self.assertFalse(is_newer("1.4.9", "1.5.0"))


class CheckForUpdateTests(unittest.TestCase):
    def test_reports_a_newer_release(self):
        opener = FakeOpener(
            {
                "latest": "1.5.1",
                "url": "https://example.com/CheckPause_Setup_1.5.1.exe",
                "notes": "fixes a crash",
            }
        )
        info = check_for_update(current="1.5.0", opener=opener)
        self.assertEqual(
            info,
            UpdateInfo(
                version="1.5.1",
                url="https://example.com/CheckPause_Setup_1.5.1.exe",
                notes="fixes a crash",
            ),
        )

    def test_stays_quiet_when_already_current(self):
        opener = FakeOpener(
            {"latest": "1.5.0", "url": "https://example.com/setup.exe"}
        )
        self.assertIsNone(check_for_update(current="1.5.0", opener=opener))

    def test_ignores_a_manifest_without_a_download_url(self):
        opener = FakeOpener({"latest": "1.5.1"})
        self.assertIsNone(check_for_update(current="1.5.0", opener=opener))

    def test_falls_back_to_the_next_mirror(self):
        opener = FakeOpener(
            {
                MANIFEST_URLS[0]: OSError("blocked"),
                MANIFEST_URLS[1]: {
                    "latest": "1.5.1",
                    "url": "https://example.com/setup.exe",
                },
            }
        )
        self.assertIsNotNone(check_for_update(current="1.5.0", opener=opener))
        self.assertEqual(opener.calls, list(MANIFEST_URLS))

    def test_survives_broken_json(self):
        opener = FakeOpener(b"{not json")
        self.assertIsNone(check_for_update(current="1.5.0", opener=opener))

    def test_survives_a_manifest_that_is_not_an_object(self):
        opener = FakeOpener(b"[1, 2, 3]")
        self.assertIsNone(check_for_update(current="1.5.0", opener=opener))

    def test_survives_being_offline(self):
        opener = FakeOpener(OSError("offline"))
        self.assertIsNone(check_for_update(current="1.5.0", opener=opener))

    def test_strict_mode_raises_when_offline(self):
        opener = FakeOpener(OSError("offline"))
        with self.assertRaises(UpdateCheckError):
            check_for_update(current="1.5.0", opener=opener, strict=True)

    def test_strict_mode_still_reports_being_current(self):
        opener = FakeOpener(
            {"latest": "1.5.0", "url": "https://example.com/setup.exe"}
        )
        self.assertIsNone(
            check_for_update(current="1.5.0", opener=opener, strict=True)
        )


if __name__ == "__main__":
    unittest.main()
