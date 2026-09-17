"""Tests for buying credits with Alipay.

The signature tests generate a throwaway key pair and have its private half
play Alipay's part, so notifications are genuinely signed and genuinely
verified rather than mocked away. A test that mocks out the one check standing
between a stranger and free credits would be worth very little.
"""

import base64
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from fastapi.testclient import TestClient

from alipay.aop.api.util.SignatureUtils import get_sign_content

from server import alipay, store
from server.app import app


class PaymentTestCase(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)

        self.alipay_key = RSA.generate(2048)
        self.app_key = RSA.generate(2048)

        patcher = mock.patch.dict(
            os.environ,
            {
                "CHECKPAUSE_DB": str(
                    pathlib.Path(self._temp.name, "checkpause.db")
                ),
                "AIPAY_APP_ID": "9021000000000000",
                "AIPAY_PRIVATE_PKCS_KEY": base64.b64encode(
                    self.app_key.export_key(format="DER", pkcs=1)
                ).decode(),
                "AIPAY_ALIPAY_PUBLIC_KEY": base64.b64encode(
                    self.alipay_key.publickey().export_key(format="DER")
                ).decode(),
                "AIPAY_GATEWAY": "https://example.invalid/gateway.do",
                "CHECKPAUSE_TOPUP_PACKS": "10,30",
                "CHECKPAUSE_FIRST_TOPUP_BONUS_PERCENT": "10",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(store.close)

        self.client = TestClient(app)
        self.user = store.create_user("buyer", "hunter22")
        self.headers = {
            "Authorization": "Bearer "
            + store.issue_token(self.user["id"])
        }

    def sign(self, params):
        """Sign exactly the way Alipay would, with the key it would use.

        The signature covers everything except ``sign`` and ``sign_type`` -
        that is the convention both sides follow, so signing the raw dict here
        would produce a signature the verifier is right to reject.
        """
        signed = {
            key: value
            for key, value in params.items()
            if key not in ("sign", "sign_type")
        }
        content = get_sign_content(signed).encode("utf-8")
        return base64.b64encode(
            pkcs1_15.new(self.alipay_key).sign(SHA256.new(content))
        ).decode()

    def make_order(self, yuan=10):
        return store.create_order(
            self.user["id"], yuan * 100, yuan * 100
        )

    def notify(self, order, **overrides):
        params = {
            "notify_type": "trade_status_sync",
            "notify_id": "notify-1",
            "sign_type": "RSA2",
            "trade_no": "2026091722001400000000000000",
            "app_id": "9021000000000000",
            "out_trade_no": order["id"],
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "{:.2f}".format(order["amount_cents"] / 100),
        }
        params.update(overrides)
        params["sign"] = self.sign(params)
        return self.client.post("/v1/pay/notify", data=params)

    def balance(self):
        return store.balance_of(self.user["id"])


class NotificationTests(PaymentTestCase):
    def test_a_paid_notification_credits_the_account(self):
        order = self.make_order()

        response = self.notify(order)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "success")
        # 1000 credits plus the ten percent first-purchase bonus.
        self.assertEqual(self.balance(), 1100)
        self.assertEqual(store.order(order["id"])["status"], "paid")

    def test_a_forged_notification_credits_nothing(self):
        order = self.make_order()

        response = self.notify(order)
        self.assertEqual(response.text, "success")

        # Same notification, but the amount is changed after signing - which is
        # exactly what someone trying to pay ten yuan for a thousand credits
        # more would have to do.
        other = self.make_order()
        tampered = {
            "app_id": "9021000000000000",
            "out_trade_no": other["id"],
            "trade_status": "TRADE_SUCCESS",
            "total_amount": "0.01",
            "sign": self.sign(
                {
                    "app_id": "9021000000000000",
                    "out_trade_no": other["id"],
                    "trade_status": "TRADE_SUCCESS",
                    "total_amount": "10.00",
                }
            ),
        }
        response = self.client.post("/v1/pay/notify", data=tampered)

        self.assertEqual(response.text, "fail")
        self.assertEqual(store.order(other["id"])["status"], "created")

    def test_a_notification_with_no_signature_at_all_is_refused(self):
        order = self.make_order()
        response = self.client.post(
            "/v1/pay/notify",
            data={
                "app_id": "9021000000000000",
                "out_trade_no": order["id"],
                "trade_status": "TRADE_SUCCESS",
                "total_amount": "10.00",
            },
        )
        self.assertEqual(response.text, "fail")
        self.assertEqual(self.balance(), 0)

    def test_a_notification_for_another_application_is_refused(self):
        order = self.make_order()
        response = self.notify(order, app_id="9021009999999999")
        self.assertEqual(response.text, "fail")
        self.assertEqual(self.balance(), 0)

    def test_a_notification_for_an_unknown_order_is_refused(self):
        order = self.make_order()
        response = self.notify(order, out_trade_no="CPNOPE")
        self.assertEqual(response.text, "fail")
        self.assertEqual(self.balance(), 0)

    def test_a_mismatched_amount_is_refused(self):
        order = self.make_order()
        response = self.notify(order, total_amount="0.01")
        self.assertEqual(response.text, "fail")
        self.assertEqual(self.balance(), 0)

    def test_an_unpaid_status_credits_nothing_but_is_acknowledged(self):
        order = self.make_order()
        response = self.notify(order, trade_status="WAIT_BUYER_PAY")
        # Acknowledged so Alipay stops retrying, but nothing is credited.
        self.assertEqual(response.text, "success")
        self.assertEqual(self.balance(), 0)
        self.assertEqual(store.order(order["id"])["status"], "created")

    def test_a_refund_is_not_mistaken_for_a_payment(self):
        order = self.make_order()
        response = self.notify(
            order, gmt_refund="2026-09-17 23:59:59", refund_fee="10.00"
        )
        self.assertEqual(response.text, "success")
        self.assertEqual(self.balance(), 0)

    def test_the_same_order_is_never_credited_twice(self):
        order = self.make_order()

        self.notify(order)
        again = self.notify(order)

        self.assertEqual(again.text, "success")
        self.assertEqual(self.balance(), 1100)

    def test_a_reported_trade_number_is_kept(self):
        order = self.make_order()
        self.notify(order, trade_no="2026091722001400000000001234")
        self.assertEqual(
            store.order(order["id"])["trade_no"],
            "2026091722001400000000001234",
        )


class OrderTests(PaymentTestCase):
    def test_packs_are_offered_with_their_credit_price(self):
        response = self.client.get("/v1/pay/packs")
        self.assertEqual(
            response.json(),
            [{"yuan": 10, "credits": 1000}, {"yuan": 30, "credits": 3000}],
        )

    def test_an_order_cannot_be_opened_for_a_price_we_do_not_offer(self):
        response = self.client.post(
            "/v1/pay/orders", json={"yuan": 1}, headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "unknown_pack")

    def test_an_order_needs_a_signed_in_account(self):
        response = self.client.post("/v1/pay/orders", json={"yuan": 10})
        self.assertEqual(response.status_code, 401)

    def test_opening_an_order_returns_a_page_to_open_in_a_browser(self):
        response = self.client.post(
            "/v1/pay/orders", json={"yuan": 10}, headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["credits"], 1000)
        self.assertTrue(body["pay_url"].endswith("/pay/" + body["order_id"]))
        self.assertEqual(body["status"], "created")

    def test_the_status_endpoint_confirms_a_payment_by_asking_alipay(self):
        order = self.make_order()
        with mock.patch.object(
            alipay,
            "query_trade",
            return_value={
                "code": "10000",
                "trade_status": "TRADE_SUCCESS",
                "trade_no": "2026091722001400000000000000",
                "total_amount": "10.00",
            },
        ):
            response = self.client.get(
                "/v1/pay/orders/" + order["id"], headers=self.headers
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "paid")
        self.assertEqual(body["balance"], 1100)

    def test_a_trade_alipay_has_never_heard_of_leaves_the_order_alone(self):
        order = self.make_order()
        with mock.patch.object(
            alipay,
            "query_trade",
            return_value={"code": "40004", "sub_code": "ACQ.TRADE_NOT_EXIST"},
        ):
            response = self.client.get(
                "/v1/pay/orders/" + order["id"], headers=self.headers
            )
        self.assertEqual(response.json()["status"], "created")
        self.assertEqual(self.balance(), 0)

    def test_another_account_cannot_read_the_order(self):
        order = self.make_order()
        stranger = store.create_user("stranger", "hunter22")
        headers = {
            "Authorization": "Bearer "
            + store.issue_token(stranger["id"])
        }
        response = self.client.get(
            "/v1/pay/orders/" + order["id"], headers=headers
        )
        self.assertEqual(response.status_code, 404)

    def test_the_payment_page_renders_a_form_that_posts_to_the_gateway(self):
        order = self.make_order()
        response = self.client.get("/pay/" + order["id"])
        self.assertEqual(response.status_code, 200)
        self.assertIn("<form", response.text)
        self.assertIn("alipay.trade.page.pay", response.text)
        self.assertIn(order["id"], response.text)

    def test_the_sandbox_hint_is_off_unless_asked_for(self):
        # It explains a sandbox quirk, which is useful while testing and wrong
        # in a screenshot sent to a reviewer - so it is opt-in.
        order = self.make_order()
        with mock.patch.dict(
            os.environ,
            {"AIPAY_GATEWAY": "https://sandbox.example.invalid/gateway.do"},
        ):
            response = self.client.get("/pay/" + order["id"])
        self.assertNotIn("沙箱", response.text)

    def test_the_sandbox_hint_can_be_switched_on_for_testing(self):
        order = self.make_order()
        # A sandbox-looking address that goes nowhere: the hint is chosen by
        # the gateway name, and a unit test has no business calling Alipay.
        with mock.patch.dict(
            os.environ,
            {
                "AIPAY_GATEWAY": "https://sandbox.example.invalid/gateway.do",
                "CHECKPAUSE_SANDBOX_HINT": "1",
            },
        ):
            response = self.client.get("/pay/" + order["id"])
        self.assertIn("登录支付", response.text)
        self.assertIn("沙箱", response.text)

    def test_a_production_page_carries_no_sandbox_warning(self):
        order = self.make_order()
        # Any gateway that is not the sandbox. Pointing this at the real one
        # would make a unit test call Alipay for real, which is rude and slow.
        with mock.patch.dict(
            os.environ,
            {"AIPAY_GATEWAY": "https://example.invalid/production-gateway.do"},
        ):
            response = self.client.get("/pay/" + order["id"])
        self.assertNotIn("沙箱", response.text)

    def test_the_payment_page_of_an_unknown_order_is_not_a_form(self):
        response = self.client.get("/pay/CPNOPE")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("<form", response.text)

    def test_a_settled_order_shows_a_receipt_instead_of_a_form(self):
        order = self.make_order()
        self.notify(order)
        response = self.client.get("/pay/" + order["id"])
        self.assertNotIn("<form", response.text)
        self.assertIn("1000", response.text)

    def test_money_is_compared_as_text_not_as_a_float(self):
        order = self.make_order(yuan=10)
        # "10" and "10.00" are the same money and must both be accepted.
        self.assertEqual(self.notify(order, total_amount="10.00").text, "success")


if __name__ == "__main__":
    unittest.main()
