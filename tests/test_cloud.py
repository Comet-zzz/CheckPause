import json
import unittest
from unittest import mock

import httpx

from checkpause.core import cloud


class FakeResponse:
    """Stands in for the object httpx returns."""

    def __init__(self, status_code=200, fragments=(), error=None, body=None):
        self.status_code = status_code
        self._fragments = list(fragments)
        self._error = error
        self._body = {} if body is None else body

    def iter_text(self):
        for fragment in self._fragments:
            yield fragment
        if self._error is not None:
            raise self._error

    def read(self):
        return b""

    def json(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


def patched_stream(response):
    return mock.patch.object(cloud.httpx, "stream", lambda *a, **k: response)


def patched_post(response):
    return mock.patch.object(cloud.httpx, "post", lambda *a, **k: response)


def patched_get(response):
    return mock.patch.object(cloud.httpx, "get", lambda *a, **k: response)


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
                cloud.stream_reply("http://server", "tok", "1. e4", "data")
            )
        self.assertEqual(text, "Nf3 is better.")

    def test_sends_the_session_token(self):
        seen = {}

        def capture(method, url, **kwargs):
            seen["headers"] = kwargs.get("headers")
            return FakeResponse(200, ["ok"])

        with mock.patch.object(cloud.httpx, "stream", capture):
            list(cloud.stream_reply("http://server", "tok", "1. e4", "data"))

        self.assertEqual(seen["headers"]["Authorization"], "Bearer tok")

    def test_sends_no_authorization_header_without_a_token(self):
        seen = {}

        def capture(method, url, **kwargs):
            seen["headers"] = kwargs.get("headers")
            return FakeResponse(200, ["ok"])

        with mock.patch.object(cloud.httpx, "stream", capture):
            list(cloud.stream_reply("http://server", "", "1. e4", "data"))

        self.assertEqual(seen["headers"], {})

    def test_reports_an_unreachable_server(self):
        response = FakeResponse(200, error=httpx.ConnectError("refused"))
        with patched_stream(response):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "tok", "1. e4", ""))

    def test_reports_a_timeout(self):
        response = FakeResponse(200, error=httpx.ReadTimeout("slow"))
        with patched_stream(response):
            with self.assertRaises(cloud.CloudRequestError):
                list(cloud.stream_reply("http://server", "tok", "1. e4", ""))

    def test_reports_missing_credit_with_the_numbers(self):
        body = {
            "detail": {
                "code": "no_credits",
                "message": "no",
                "balance": 3,
                "needed": 9,
            }
        }
        with patched_stream(FakeResponse(402, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                list(cloud.stream_reply("http://server", "tok", "1. e4", ""))
        self.assertEqual(caught.exception.code, "no_credits")
        self.assertIn("3", str(caught.exception))
        self.assertIn("9", str(caught.exception))

    def test_a_stale_session_asks_the_user_to_sign_in_again(self):
        body = {"detail": {"code": "unknown_token", "message": "gone"}}
        with patched_stream(FakeResponse(401, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                list(cloud.stream_reply("http://server", "tok", "1. e4", ""))
        self.assertEqual(caught.exception.code, "unknown_token")
        self.assertIn("登录", str(caught.exception))

    def test_reports_a_server_error_with_the_status_code(self):
        with patched_stream(FakeResponse(503)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                list(cloud.stream_reply("http://server", "tok", "1. e4", ""))
        self.assertIn("503", str(caught.exception))

    def test_posts_json_to_the_analyze_endpoint(self):
        seen = {}

        def capture(method, url, **kwargs):
            seen["method"] = method
            seen["url"] = url
            seen["json"] = kwargs.get("json")
            return FakeResponse(200, ["ok"])

        with mock.patch.object(cloud.httpx, "stream", capture):
            list(cloud.stream_reply("http://server/", "tok", "1. e4", "data"))

        self.assertEqual(seen["method"], "POST")
        self.assertEqual(seen["url"], "http://server/v1/analyze")
        self.assertEqual(json.dumps(seen["json"])[:1], "{")


class AccountTests(unittest.TestCase):
    def session(self, username="player", balance=0):
        return {
            "token": "tok",
            "account": {"username": username, "balance": balance},
        }

    def test_register_posts_the_credentials_and_returns_the_session(self):
        seen = {}

        def capture(url, **kwargs):
            seen["url"] = url
            seen["json"] = kwargs.get("json")
            return FakeResponse(200, body=self.session())

        with mock.patch.object(cloud.httpx, "post", capture):
            result = cloud.register("http://server/", "player", "hunter22")

        self.assertEqual(seen["url"], "http://server/v1/accounts/register")
        self.assertEqual(seen["json"]["username"], "player")
        self.assertEqual(seen["json"]["password"], "hunter22")
        self.assertEqual(result["token"], "tok")

    def test_a_taken_username_is_explained_in_the_users_language(self):
        body = {"detail": {"code": "username_taken", "message": "taken"}}
        with patched_post(FakeResponse(409, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                cloud.register("http://server", "player", "hunter22")
        self.assertEqual(caught.exception.code, "username_taken")
        self.assertIn("用户名", str(caught.exception))

    def test_a_short_password_is_explained(self):
        body = {"detail": {"code": "password_too_short", "message": "short"}}
        with patched_post(FakeResponse(400, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                cloud.register("http://server", "player", "abc")
        self.assertEqual(caught.exception.code, "password_too_short")

    def test_the_wrong_password_is_reported_readably(self):
        body = {"detail": {"code": "bad_credentials", "message": "no"}}
        with patched_post(FakeResponse(401, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                cloud.sign_in("http://server", "player", "wrong")
        self.assertEqual(caught.exception.code, "bad_credentials")
        self.assertIn("密码", str(caught.exception))

    def test_signing_in_posts_to_the_login_endpoint(self):
        seen = {}

        def capture(url, **kwargs):
            seen["url"] = url
            return FakeResponse(200, body=self.session())

        with mock.patch.object(cloud.httpx, "post", capture):
            cloud.sign_in("http://server/", "player", "hunter22")

        self.assertEqual(seen["url"], "http://server/v1/accounts/login")

    def test_the_balance_is_read_from_the_server_with_the_token(self):
        seen = {}

        def capture(url, **kwargs):
            seen["url"] = url
            seen["headers"] = kwargs.get("headers")
            return FakeResponse(
                200, body={"username": "player", "balance": 700}
            )

        with mock.patch.object(cloud.httpx, "get", capture):
            account = cloud.fetch_account("http://server", "tok")

        self.assertEqual(seen["url"], "http://server/v1/accounts/me")
        self.assertEqual(seen["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(account["balance"], 700)

    def test_a_dead_session_is_reported_as_a_dead_session(self):
        body = {"detail": {"code": "unknown_token", "message": "gone"}}
        with patched_get(FakeResponse(401, body=body)):
            with self.assertRaises(cloud.CloudRequestError) as caught:
                cloud.fetch_account("http://server", "stale")
        self.assertEqual(caught.exception.code, "unknown_token")

    def test_signing_out_does_not_raise_when_the_server_is_gone(self):
        with mock.patch.object(
            cloud.httpx, "post", side_effect=httpx.ConnectError("refused")
        ):
            cloud.sign_out("http://server", "tok")


if __name__ == "__main__":
    unittest.main()
