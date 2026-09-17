"""Tests for the analyse endpoint and the prompt it builds.

The upstream model is always faked, so nothing here touches the network.
"""

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server import config, deepseek, pricing, prompting, store
from server.app import app


def fake_body(chunks):
    async def generator():
        for chunk in chunks:
            yield chunk

    return generator()


def fake_usage(chunks, input_tokens=0, output_tokens=0):
    """Stand in for the upstream stream, reporting usage as DeepSeek does."""

    def factory(stream, usage=None):
        async def generator():
            for chunk in chunks:
                yield chunk
            if usage is not None:
                usage.input_tokens = input_tokens
                usage.output_tokens = output_tokens
                usage.counted = True
                usage.finished = True

        return generator()

    return factory


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

    def test_the_billing_knobs_have_workable_defaults(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHECKPAUSE_MAX_ANSWER_TOKENS", None)
            os.environ.pop("CHECKPAUSE_FIRST_TOPUP_BONUS_PERCENT", None)
            self.assertEqual(
                config.max_answer_tokens(), config.DEFAULT_MAX_ANSWER_TOKENS
            )
            self.assertEqual(
                config.first_topup_bonus_percent(),
                config.DEFAULT_FIRST_TOPUP_BONUS_PERCENT,
            )

    def test_the_first_purchase_offer_can_be_switched_off(self):
        with mock.patch.dict(
            os.environ, {"CHECKPAUSE_FIRST_TOPUP_BONUS_PERCENT": "0"}
        ):
            self.assertEqual(config.first_topup_bonus_percent(), 0)


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
        self.assertEqual(messages[0]["role"], "system")
        self.assertTrue(messages[0]["content"].startswith("TUNED PROMPT"))
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("1. e4", messages[1]["content"])
        self.assertIn("e4: +0.3", messages[1]["content"])

    def test_always_carries_the_rule_about_what_model_it_is(self):
        system = prompting.build_messages("1. e4")[0]["content"]
        self.assertIn(prompting.IDENTITY_POLICY, system)

    def test_the_rule_survives_the_tuned_prompt_being_replaced(self):
        # The reason it is not in the prompt file: swapping the tuned prompt
        # must not be able to quietly drop it.
        (pathlib.Path(self._temp.name) / "system_prompt.txt").write_text(
            "A completely different prompt.", encoding="utf-8"
        )

        system = prompting.build_messages("1. e4")[0]["content"]

        self.assertIn("A completely different prompt.", system)
        self.assertIn(prompting.IDENTITY_POLICY, system)

    def test_a_deployment_can_supply_its_own_wording(self):
        (pathlib.Path(self._temp.name) / "identity_policy.txt").write_text(
            "DEFLECT", encoding="utf-8"
        )
        system = prompting.build_messages("1. e4")[0]["content"]
        self.assertIn("DEFLECT", system)
        self.assertNotIn(prompting.IDENTITY_POLICY, system)

    def test_the_language_instruction_comes_after_everything_else(self):
        system = prompting.build_messages("1. e4", language="zh-CN")[0]["content"]
        self.assertTrue(
            system.endswith(prompting.LANGUAGE_INSTRUCTIONS["zh-CN"])
        )

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

    def test_pins_the_answer_language(self):
        messages = prompting.build_messages("1. e4", "", [], "zh-CN")
        self.assertIn("Simplified Chinese", messages[0]["content"])

    def test_adds_no_language_instruction_for_an_unknown_language(self):
        system = prompting.build_messages("1. e4", "", [], "fr-FR")[0]["content"]
        for instruction in prompting.LANGUAGE_INSTRUCTIONS.values():
            self.assertNotIn(instruction, system)


class AnalyzeEndpointTests(unittest.TestCase):
    """Every case here is about money: the endpoint spends real credits."""

    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        patcher = mock.patch.dict(
            os.environ,
            {
                "CHECKPAUSE_DB": str(
                    pathlib.Path(self._temp.name, "checkpause.db")
                ),
                "CHECKPAUSE_CONFIG_DIR": self._temp.name,
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(store.close)

        self.client = TestClient(app)
        self.user = store.create_user("player", "hunter22")
        self.headers = {
            "Authorization": "Bearer {}".format(
                store.issue_token(self.user["id"])
            )
        }

    def fund(self, credits):
        store.add_credits(
            self.user["id"], credits, reason="grant", reference="seed"
        )

    def balance(self):
        return store.balance_of(self.user["id"])

    def reservation(self):
        """What the endpoint will reserve for the payload used below."""
        return pricing.estimate_hold(prompting.build_messages("1. e4", ""))

    def post(self, payload=None, headers=None):
        return self.client.post(
            "/v1/analyze",
            json={"pgn": "1. e4"} if payload is None else payload,
            headers=self.headers if headers is None else headers,
        )

    def stream(self, chunks, input_tokens=0, output_tokens=0):
        return mock.patch.object(
            deepseek, "open_stream", mock.AsyncMock(return_value=object())
        ), mock.patch.object(
            deepseek,
            "iter_text",
            fake_usage(chunks, input_tokens, output_tokens),
        )

    def test_streams_the_reply(self):
        self.fund(100)
        opened, text = self.stream(["Nf3 ", "is better."], 100, 20)
        with opened, text:
            response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "Nf3 is better.")

    def test_requires_a_signed_in_account(self):
        self.assertEqual(self.post(headers={}).status_code, 401)
        self.assertEqual(
            self.post(
                headers={"Authorization": "Bearer nonsense"}
            ).status_code,
            401,
        )

    def test_a_blank_balance_cannot_start_a_request(self):
        response = self.post()
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.json()["detail"]["code"], "no_credits")
        self.assertEqual(response.json()["detail"]["balance"], 0)

    def test_a_request_that_costs_more_than_the_balance_is_refused(self):
        self.fund(1)
        response = self.post()
        self.assertEqual(response.status_code, 402)
        self.assertGreater(response.json()["detail"]["needed"], 1)
        self.assertEqual(self.balance(), 1)

    def test_the_charge_follows_the_usage_the_upstream_reports(self):
        self.fund(100)
        opened, text = self.stream(["ok"], 5000, 400)
        with opened, text:
            response = self.post()
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.balance(), 100 - pricing.credits_for(5000, 400))
        row = store.ledger_for(self.user["id"])[0]
        self.assertEqual(row["reason"], "analyze")
        self.assertEqual(row["input_tokens"], 5000)
        self.assertEqual(row["output_tokens"], 400)
        self.assertEqual(row["price_version"], pricing.PRICE_VERSION)

    def test_a_reply_with_no_usage_still_pays_the_reservation(self):
        self.fund(100)
        reserved = self.reservation()
        with mock.patch.object(
            deepseek, "open_stream", mock.AsyncMock(return_value=object())
        ), mock.patch.object(
            deepseek,
            "iter_text",
            lambda stream, usage=None: fake_body(["half an answer"]),
        ):
            response = self.post()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "half an answer")
        self.assertEqual(self.balance(), 100 - reserved)
        self.assertEqual(
            store.ledger_for(self.user["id"])[0]["reason"],
            "analyze_interrupted",
        )

    def test_a_refused_upstream_costs_nothing(self):
        self.fund(100)
        with mock.patch.object(
            deepseek,
            "open_stream",
            mock.AsyncMock(side_effect=deepseek.UpstreamError("no API key")),
        ):
            response = self.post()

        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["detail"]["code"], "upstream_error")
        self.assertEqual(self.balance(), 100)

    def test_rejects_an_empty_pgn(self):
        self.assertEqual(self.post({"pgn": ""}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
