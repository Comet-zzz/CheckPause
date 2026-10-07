import unittest
from unittest import mock

import httpx

from checkpause.core import collect


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code


class BuildSampleTests(unittest.TestCase):
    def test_keeps_only_the_conversation(self):
        messages = [
            {"role": "system", "content": "frozen client prompt"},
            {"role": "user", "content": "why?"},
            {"role": "assistant", "content": "because"},
            {"role": "tool", "content": "drop me"},
        ]
        sample = collect.build_sample("1. e4", "data", messages, "answer")
        self.assertEqual(
            [entry["role"] for entry in sample["history"]],
            ["user", "assistant"],
        )
        self.assertNotIn("frozen client prompt", str(sample))

    def test_ignores_entries_that_are_not_objects(self):
        sample = collect.build_sample("1. e4", "data", ["nonsense", None], "answer")
        self.assertEqual(sample["history"], [])

    def test_keeps_only_the_most_recent_turns(self):
        messages = [
            {"role": "user", "content": f"m{index}"} for index in range(collect.MAX_MESSAGES + 10)
        ]
        sample = collect.build_sample("1. e4", "", messages, "answer")
        self.assertEqual(len(sample["history"]), collect.MAX_MESSAGES)
        self.assertEqual(sample["history"][-1]["content"], f"m{collect.MAX_MESSAGES + 9}")

    def test_carries_the_identity_that_is_meant_to_travel(self):
        sample = collect.build_sample(
            "1. e4",
            "data",
            [],
            "answer",
            language="zh-CN",
            client_version="1.9.1",
            install_id="abc",
        )
        self.assertEqual(sample["source"], "local")
        self.assertEqual(sample["install_id"], "abc")
        self.assertEqual(sample["client_version"], "1.9.1")
        self.assertEqual(sample["reply"], "answer")


class StripPgnHeadersTests(unittest.TestCase):
    def test_drops_the_tag_pairs_that_name_people(self):
        pgn = (
            '[Event "Casual game"]\n'
            '[Site "Lichess"]\n'
            '[Date "2026.01.02"]\n'
            '[White "Magnus Carlsen"]\n'
            '[Black "Hikaru Nakamura"]\n'
            '[Result "1-0"]\n'
            "\n"
            "1. e4 e5 2. Nf3 1-0\n"
        )
        cleaned = collect.strip_pgn_headers(pgn)
        self.assertNotIn("Magnus", cleaned)
        self.assertNotIn("Hikaru", cleaned)
        self.assertNotIn("[White", cleaned)
        self.assertNotIn("[Site", cleaned)
        self.assertIn("1. e4 e5 2. Nf3 1-0", cleaned)

    def test_keeps_the_position_tags_that_name_nobody(self):
        pgn = '[SetUp "1"]\n[FEN "8/8/8/8/8/8/8/K6k w - - 0 1"]\n\n1. Ka2\n'
        cleaned = collect.strip_pgn_headers(pgn)
        self.assertIn('[FEN "8/8/8/8/8/8/8/K6k w - - 0 1"]', cleaned)
        self.assertIn('[SetUp "1"]', cleaned)

    def test_tag_matching_is_case_insensitive(self):
        pgn = '[white "Someone"]\n\n1. e4\n'
        self.assertNotIn("Someone", collect.strip_pgn_headers(pgn))

    def test_a_pgn_without_headers_is_unchanged(self):
        self.assertEqual(collect.strip_pgn_headers("1. e4 e5"), "1. e4 e5")

    def test_a_sample_built_from_a_named_game_carries_no_name(self):
        pgn = '[White "Magnus Carlsen"]\n[Black "Hikaru Nakamura"]\n\n1. e4\n'
        sample = collect.build_sample(pgn, "", [], "answer")
        self.assertNotIn("Magnus", sample["pgn"])
        self.assertNotIn("Hikaru", sample["pgn"])


class SendSampleTests(unittest.TestCase):
    def test_posts_to_the_sample_endpoint(self):
        seen = {}

        def capture(url, **kwargs):
            seen["url"] = url
            seen["json"] = kwargs.get("json")
            return FakeResponse(200)

        with mock.patch.object(collect.httpx, "post", capture):
            sent = collect.send_sample("http://server/", {"pgn": "1. e4"})

        self.assertTrue(sent)
        self.assertEqual(seen["url"], "http://server/v1/dataset/samples")
        self.assertEqual(seen["json"]["pgn"], "1. e4")

    def test_a_server_error_is_a_failed_send_not_an_exception(self):
        with mock.patch.object(collect.httpx, "post", lambda *a, **k: FakeResponse(500)):
            self.assertFalse(collect.send_sample("http://server", {"pgn": "1. e4"}))

    def test_a_network_error_is_swallowed(self):
        def boom(*args, **kwargs):
            raise httpx.ConnectError("refused")

        with mock.patch.object(collect.httpx, "post", boom):
            self.assertFalse(collect.send_sample("http://server", {"pgn": "1. e4"}))

    def test_an_empty_pgn_is_not_sent(self):
        with mock.patch.object(collect.httpx, "post") as post:
            self.assertFalse(collect.send_sample("http://server", {"pgn": "  "}))
        post.assert_not_called()


class MaybeSendTests(unittest.TestCase):
    def test_a_sample_is_sent_for_a_local_review(self):
        with (
            mock.patch.object(collect, "get_install_id", lambda: "install-1"),
            mock.patch.object(collect, "send_sample_async") as send,
        ):
            sample = collect.maybe_send_local_sample(
                "http://server",
                "1. e4",
                "data",
                [{"role": "user", "content": "why?"}],
                "answer",
                "zh-CN",
                "1.9.1",
            )
        send.assert_called_once()
        self.assertEqual(sample["install_id"], "install-1")
        self.assertEqual(sample["language"], "zh-CN")

    def test_a_missing_game_is_not_sent(self):
        with mock.patch.object(collect, "send_sample_async") as send:
            result = collect.maybe_send_local_sample(
                "http://server", "", "", [], "answer", "zh-CN", "1.9.1"
            )
        self.assertIsNone(result)
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
