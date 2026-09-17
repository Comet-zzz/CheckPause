"""Tests for the analyse endpoint and the prompt it builds.

The upstream model is always faked, so nothing here touches the network.
"""

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server import config, deepseek, prompting
from server.app import app


def fake_body(chunks):
    async def generator():
        for chunk in chunks:
            yield chunk

    return generator()


class PromptLoadingTests(unittest.TestCase):
    def test_uses_a_placeholder_when_no_prompt_is_installed(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.dict(os.environ, {"CHECKPAUSE_CONFIG_DIR": folder}):
                self.assertTrue(config.using_placeholder_prompt())
                self.assertEqual(
                    config.system_prompt(), config.FALLBACK_SYSTEM_PROMPT
                )

    def test_reads_the_tuned_prompt_from_the_config_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            pathlib.Path(folder, "system_prompt.txt").write_text(
                "You are a grandmaster coach.", encoding="utf-8"
            )
            with mock.patch.dict(os.environ, {"CHECKPAUSE_CONFIG_DIR": folder}):
                self.assertFalse(config.using_placeholder_prompt())
                self.assertEqual(
                    config.system_prompt(), "You are a grandmaster coach."
                )

    def test_the_access_token_is_optional(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHECKPAUSE_ACCESS_TOKEN", None)
            self.assertEqual(config.access_token(), "")


class BuildMessagesTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        pathlib.Path(self._temp.name, "system_prompt.txt").write_text(
            "TUNED PROMPT", encoding="utf-8"
        )
        pathlib.Path(self._temp.name, "user_template.txt").write_text(
            "GAME:\n{pgn}\nDATA:\n{analysis}", encoding="utf-8"
        )
        patcher = mock.patch.dict(
            os.environ, {"CHECKPAUSE_CONFIG_DIR": self._temp.name}
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_puts_the_tuned_prompt_first_and_the_game_second(self):
        messages = prompting.build_messages("1. e4", "e4: +0.3")
        self.assertEqual(messages[0], {"role": "system", "content": "TUNED PROMPT"})
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("1. e4", messages[1]["content"])
        self.assertIn("e4: +0.3", messages[1]["content"])

    def test_appends_the_conversation(self):
        history = [
            {"role": "assistant", "content": "Nf3 is more accurate."},
            {"role": "user", "content": "Why?"},
        ]
        messages = prompting.build_messages("1. e4", "", history)
        self.assertEqual(
            [message["role"] for message in messages],
            ["system", "user", "assistant", "user"],
        )
        self.assertEqual(messages[-1]["content"], "Why?")

    def test_keeps_only_the_tail_of_a_long_conversation(self):
        history = [
            {"role": "user", "content": f"question {index}"}
            for index in range(prompting.MAX_HISTORY_MESSAGES + 8)
        ]
        messages = prompting.build_messages("1. e4", "", history)
        # system + context + the trimmed tail
        self.assertEqual(len(messages), 2 + prompting.MAX_HISTORY_MESSAGES)
        self.assertEqual(messages[-1]["content"], "question 19")

    def test_drops_entries_with_an_unexpected_role_or_no_text(self):
        history = [
            {"role": "system", "content": "sneaky"},
            {"role": "user", "content": "   "},
            {"role": "assistant", "content": "kept"},
        ]
        messages = prompting.build_messages("1. e4", "", history)
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[-1]["content"], "kept")

    def test_a_broken_template_falls_back_instead_of_failing(self):
        pathlib.Path(self._temp.name, "user_template.txt").write_text(
            "GAME:\n{pgn}\n{unknown_placeholder}", encoding="utf-8"
        )
        messages = prompting.build_messages("1. e4", "data")
        self.assertIn("1. e4", messages[1]["content"])


class AnalyzeEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_streams_the_reply(self):
        with mock.patch.object(
            deepseek, "open_stream", mock.AsyncMock(return_value=object())
        ), mock.patch.object(
            deepseek, "iter_text", lambda stream: fake_body(["Nf3 ", "is better."])
        ):
            response = self.client.post(
                "/v1/analyze", json={"pgn": "1. e4", "analysis": "e4: +0.3"}
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Nf3 is better.")

    def test_reports_an_upstream_failure_as_502(self):
        with mock.patch.object(
            deepseek,
            "open_stream",
            mock.AsyncMock(side_effect=deepseek.UpstreamError("no API key")),
        ):
            response = self.client.post("/v1/analyze", json={"pgn": "1. e4"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("no API key", response.json()["detail"])

    def test_rejects_an_empty_pgn(self):
        response = self.client.post("/v1/analyze", json={"pgn": ""})
        self.assertEqual(response.status_code, 422)

    def test_requires_the_token_when_one_is_configured(self):
        with mock.patch.dict(os.environ, {"CHECKPAUSE_ACCESS_TOKEN": "secret"}):
            denied = self.client.post("/v1/analyze", json={"pgn": "1. e4"})
            self.assertEqual(denied.status_code, 401)

            with mock.patch.object(
                deepseek, "open_stream", mock.AsyncMock(return_value=object())
            ), mock.patch.object(
                deepseek, "iter_text", lambda stream: fake_body(["ok"])
            ):
                allowed = self.client.post(
                    "/v1/analyze",
                    json={"pgn": "1. e4"},
                    headers={"X-CheckPause-Token": "secret"},
                )
        self.assertEqual(allowed.status_code, 200)


if __name__ == "__main__":
    unittest.main()
