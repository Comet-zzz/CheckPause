"""Tests for the sign-up and sign-in endpoints."""

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from server import store
from server.app import app


class AccountEndpointTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        patcher = mock.patch.dict(
            os.environ,
            {
                "CHECKPAUSE_DB": str(
                    pathlib.Path(self._temp.name, "checkpause.db")
                )
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(store.close)
        self.client = TestClient(app)

    def sign_up(self, username="player", password="hunter22"):
        return self.client.post(
            "/v1/accounts/register",
            json={"username": username, "password": password},
        )

    def bearer(self, token):
        return {"Authorization": "Bearer " + token}

    def test_signing_up_returns_a_token_and_an_empty_balance(self):
        response = self.sign_up()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["token"])
        self.assertEqual(body["account"]["username"], "player")
        self.assertEqual(body["account"]["balance"], 0)

    def test_the_token_opens_the_account_endpoint(self):
        token = self.sign_up().json()["token"]
        response = self.client.get("/v1/accounts/me", headers=self.bearer(token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["balance"], 0)

    def test_the_account_endpoint_needs_a_token(self):
        self.assertEqual(self.client.get("/v1/accounts/me").status_code, 401)
        self.assertEqual(
            self.client.get(
                "/v1/accounts/me", headers=self.bearer("nonsense")
            ).status_code,
            401,
        )

    def test_a_taken_username_is_reported_as_a_conflict(self):
        self.sign_up()
        response = self.sign_up()
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "username_taken")

    def test_a_short_password_is_reported(self):
        response = self.sign_up(password="short")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json()["detail"]["code"], "password_too_short"
        )

    def test_signing_in_returns_a_fresh_token(self):
        self.sign_up()
        response = self.client.post(
            "/v1/accounts/login",
            json={"username": "player", "password": "hunter22"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["token"])

    def test_a_wrong_password_says_nothing_about_which_half_was_wrong(self):
        self.sign_up()
        response = self.client.post(
            "/v1/accounts/login",
            json={"username": "player", "password": "wrongone"},
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "bad_credentials")

    def test_signing_out_retires_the_token(self):
        token = self.sign_up().json()["token"]

        self.assertEqual(
            self.client.post(
                "/v1/accounts/logout", headers=self.bearer(token)
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                "/v1/accounts/me", headers=self.bearer(token)
            ).status_code,
            401,
        )

    def test_the_ledger_explains_the_balance(self):
        token = self.sign_up().json()["token"]
        user = store.find_user("player")
        store.add_credits(user["id"], 500, reason="grant", reference="seed")
        store.top_up(user["id"], 1000, reference="order-1", bonus_percent=10)

        response = self.client.get(
            "/v1/accounts/ledger", headers=self.bearer(token)
        )

        self.assertEqual(response.status_code, 200)
        rows = response.json()
        self.assertEqual([row["delta"] for row in rows], [100, 1000, 500])
        self.assertEqual(rows[0]["reason"], "topup_bonus")
        self.assertEqual(rows[-1]["balance_after"], 500)


if __name__ == "__main__":
    unittest.main()
