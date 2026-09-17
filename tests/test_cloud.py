import json
import unittest
from unittest import mock

import httpx

from checkpause.core import cloud


class FakeResponse:
    """Stands in for the object httpx.stream returns."""

    def __init__(self, status_code=200, fragments=(), error=None):
        self.status_code = status_code
        self._fragments = list(fragments)
        self._error = error

    def iter_text(self):
        for fragment in self._fragments:
            yield fragment
        if self._error is not None:
            raise self._error

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def patched_stream(response):
    return mock.patch.object(cloud.httpx, "stream", lambda *a, **k: response)


class BuildPayloadTests(unittest.TestCase):
    def test_sends_raw_material_only(self):
        payload = cloud.build_payload("1. e4", "e4: +0.3", [])
        self.assertEqual(
            sorted(payload), ["analysis", "history", "language", "pgn"]
        )

    def test_carries_the_interface_language(self):
        payload = cloud.build_payload("1. e4", "", [], "zh-CN")
        self.assertEqual(payload["language"], "zh-CN")

    def test_keeps_only_real_conversation_entries(self):
        history = [
            {"role": "system", "content": "should not travel"},
            {"role": "user", "content": "why?"},
            {"role": "assistant", "content": "because"},
            {"role": "tool", "content": "nope"},
        ]
        payload = cloud.build_payload("1. e4", "", history)
        self.assertEqual(
            [entry["role"] for entry in payload["history"]],
            ["user", "assistant"],
        )

    def test_ignores_entries_that_are_not_objects(self):
        payload = cloud.build_payload("1. e4", "", ["nonsense", None])
        self.assertEqual(payload["history"], [])


class StreamReplyTests(unittest.TestCase):
    def test_yields_the_reply_fragments(self):
        response = FakeResponse(200, ["Nf3 ", "is better."])
        with patched_stream(response):
            text = "".join(
                cloud.stream_reply("http://server", "1. e4", "data")
            )
        self.assertEqual(text, "Nf3 is better.")

    def test_reports_an_unreachable_server(self):
        response = FakeResponse(200, error=httpx.ConnectError("refused"))
        with patched_stream(response):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "1. e4", ""))

    def test_reports_a_timeout(self):
        response = FakeResponse(200, error=httpx.ReadTimeout("slow"))
        with patched_stream(response):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "1. e4", ""))

    def test_reports_missing_credit(self):
        with patched_stream(FakeResponse(402)):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "1. e4", ""))

    def test_reports_a_rejected_client(self):
        with patched_stream(FakeResponse(401)):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "1. e4", ""))

    def test_reports_a_server_error_with_the_status_code(self):
        with patched_stream(FakeResponse(503)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                list(cloud.stream_reply("http://server", "1. e4", ""))
        self.assertIn("503", str(caught.exception))

    def test_posts_json_to_the_analyze_endpoint(self):
        seen = {}

        def capture(method, url, **kwargs):
            seen["method"] = method
            seen["url"] = url
            seen["json"] = kwargs.get("json")
            return FakeResponse(200, ["ok"])

        with mock.patch.object(cloud.httpx, "stream", capture):
            list(cloud.stream_reply("http://server/", "1. e4", "data"))

        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["url"], "http://server/v1/analyze")
        self.assertEqual(json.dumps(seen["json"])[:1], "{")


if __name__ == "__main__":
    unittest.main()
