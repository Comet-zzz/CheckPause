"""Tests for the ledger, the reservations and the accounts.

These cover the places where a mistake costs real money: spending the same
credits twice, giving an interrupted reply away, or charging after the balance
is already gone.
"""

import os
import pathlib
import tempfile
import unittest
from unittest import mock

from server import pricing, store


class StoreTestCase(unittest.TestCase):
    """Every test gets its own database file and a registered account."""

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
        self.user = store.create_user("player", "hunter22")

    def fund(self, credits):
        store.add_credits(
            self.user["id"], credits, reason="grant", reference="seed"
        )


class ReservationTests(StoreTestCase):
    def test_a_settlement_returns_the_unused_part_of_the_reservation(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 30)
        self.assertEqual(store.balance_of(self.user["id"]), 70)

        outcome = store.settle_hold(
            hold, input_tokens=10, output_tokens=5, cost=12, price_version="t"
        )
        self.assertEqual(outcome["charge"], 12)
        self.assertEqual(store.balance_of(self.user["id"]), 88)

    def test_a_reservation_is_refused_when_the_balance_is_short(self):
        self.fund(10)
        with self.assertRaises(store.NoCredits) as caught:
            store.open_hold(self.user["id"], 30)
        self.assertEqual(caught.exception.balance, 10)
        self.assertEqual(caught.exception.needed, 30)
        self.assertEqual(store.balance_of(self.user["id"]), 10)

    def test_the_same_credits_cannot_be_reserved_twice(self):
        self.fund(10)
        store.open_hold(self.user["id"], 10)
        with self.assertRaises(store.NoCredits):
            store.open_hold(self.user["id"], 10)

    def test_an_interrupted_request_pays_the_whole_reservation(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 25)

        outcome = store.settle_hold(hold, note="usage was never counted")

        self.assertEqual(outcome["charge"], 25)
        self.assertEqual(outcome["reason"], "analyze_interrupted")
        self.assertEqual(store.balance_of(self.user["id"]), 75)

    def test_an_underestimate_never_pushes_the_balance_below_zero(self):
        self.fund(10)
        hold = store.open_hold(self.user["id"], 10)

        outcome = store.settle_hold(
            hold, input_tokens=99_999, output_tokens=99_999, cost=500
        )

        self.assertEqual(store.balance_of(self.user["id"]), 0)
        self.assertEqual(outcome["charge"], 10)

    def test_one_request_leaves_exactly_one_ledger_row(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 20)

        store.settle_hold(
            hold, input_tokens=7, output_tokens=3, cost=9, price_version="t"
        )

        rows = [
            row
            for row in store.ledger_for(self.user["id"])
            if row["reason"] == "analyze"
        ]
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["delta"], -9)
        self.assertEqual(rows[0]["input_tokens"], 7)
        self.assertEqual(rows[0]["output_tokens"], 3)
        self.assertEqual(rows[0]["price_version"], "t")
        self.assertEqual(rows[0]["balance_after"], 91)

    def test_a_refunded_reservation_leaves_no_ledger_row(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 20)

        self.assertTrue(store.refund_hold(hold, note="upstream refused"))

        self.assertEqual(store.balance_of(self.user["id"]), 100)
        reasons = {row["reason"] for row in store.ledger_for(self.user["id"])}
        self.assertNotIn("analyze", reasons)

    def test_refunding_twice_is_harmless(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 20)

        self.assertTrue(store.refund_hold(hold))
        self.assertFalse(store.refund_hold(hold))

        self.assertEqual(store.balance_of(self.user["id"]), 100)

    def test_settling_twice_does_not_charge_twice(self):
        self.fund(100)
        hold = store.open_hold(self.user["id"], 20)
        store.settle_hold(hold, cost=20)

        with self.assertRaises(store.StoreError):
            store.settle_hold(hold, cost=20)

        self.assertEqual(store.balance_of(self.user["id"]), 80)

    def test_an_abandoned_reservation_is_charged_by_the_sweep(self):
        self.fund(100)
        store.open_hold(self.user["id"], 30)

        swept = store.sweep_stale_holds(older_than_seconds=-1)

        self.assertEqual(len(swept), 1)
        self.assertEqual(swept[0]["charge"], 30)
        self.assertEqual(store.balance_of(self.user["id"]), 70)

    def test_the_sweep_leaves_recent_reservations_alone(self):
        self.fund(100)
        store.open_hold(self.user["id"], 30)

        self.assertEqual(store.sweep_stale_holds(), [])
        self.assertEqual(store.balance_of(self.user["id"]), 70)


class TopUpTests(StoreTestCase):
    def test_the_bonus_lands_only_on_the_first_purchase(self):
        added = store.top_up(
            self.user["id"], 1000, reference="order-1", bonus_percent=10
        )
        self.assertEqual(added, 1100)
        self.assertEqual(store.balance_of(self.user["id"]), 1100)

        again = store.top_up(
            self.user["id"], 1000, reference="order-2", bonus_percent=10
        )
        self.assertEqual(again, 1000)
        self.assertEqual(store.balance_of(self.user["id"]), 2100)

    def test_the_first_purchase_is_remembered(self):
        self.assertIsNone(store.get_user(self.user["id"])["first_topup_at"])
        store.top_up(
            self.user["id"], 100, reference="order-1", bonus_percent=0
        )
        self.assertIsNotNone(store.get_user(self.user["id"])["first_topup_at"])

    def test_a_grant_does_not_consume_the_first_purchase_bonus(self):
        store.add_credits(
            self.user["id"], 100, reason="grant", reference="gift-1"
        )
        self.assertIsNone(store.get_user(self.user["id"])["first_topup_at"])

        added = store.top_up(
            self.user["id"], 200, reference="order-1", bonus_percent=10
        )
        self.assertEqual(added, 220)

    def test_a_repeated_reference_is_refused_rather_than_credited_twice(self):
        store.top_up(self.user["id"], 500, reference="order-1")

        with self.assertRaises(store.StoreError) as caught:
            store.top_up(self.user["id"], 500, reference="order-1")

        self.assertEqual(caught.exception.code, "duplicate_reference")
        self.assertEqual(store.balance_of(self.user["id"]), 500)

    def test_a_manual_correction_can_take_credits_back(self):
        self.fund(100)
        store.add_credits(
            self.user["id"], -40, reason="adjustment", reference="fix-1"
        )
        self.assertEqual(store.balance_of(self.user["id"]), 60)

    def test_a_correction_cannot_overdraw_the_account(self):
        self.fund(10)
        with self.assertRaises(store.StoreError):
            store.add_credits(
                self.user["id"], -40, reason="adjustment", reference="fix-1"
            )
        self.assertEqual(store.balance_of(self.user["id"]), 10)


class AccountTests(StoreTestCase):
    def test_the_password_is_not_stored_in_the_clear(self):
        row = store.connection().execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (self.user["id"],),
        ).fetchone()
        self.assertTrue(row["password_hash"].startswith("scrypt$"))
        self.assertNotIn("hunter22", row["password_hash"])

    def test_login_accepts_the_right_password_and_refuses_the_wrong_one(self):
        self.assertIsNotNone(store.verify_login("player", "hunter22"))
        self.assertIsNotNone(store.verify_login("PLAYER", "hunter22"))
        self.assertIsNone(store.verify_login("player", "hunter23"))
        self.assertIsNone(store.verify_login("nobody", "hunter22"))

    def test_a_duplicate_username_is_refused_whatever_its_case(self):
        with self.assertRaises(store.StoreError) as caught:
            store.create_user("PLAYER", "another22")
        self.assertEqual(caught.exception.code, "username_taken")

    def test_a_short_password_is_refused(self):
        with self.assertRaises(store.StoreError) as caught:
            store.create_user("newcomer", "short")
        self.assertEqual(caught.exception.code, "password_too_short")

    def test_a_username_with_spaces_is_refused(self):
        with self.assertRaises(store.StoreError) as caught:
            store.create_user("no spaces", "hunter22")
        self.assertEqual(caught.exception.code, "username_invalid")

    def test_a_token_identifies_its_user_until_it_is_revoked(self):
        token = store.issue_token(self.user["id"])
        self.assertEqual(store.user_for_token(token)["username"], "player")

        store.revoke_token(token)

        self.assertIsNone(store.user_for_token(token))
        self.assertIsNone(store.user_for_token("nonsense"))
        self.assertIsNone(store.user_for_token(""))

    def test_resetting_a_password_signs_every_session_out(self):
        token = store.issue_token(self.user["id"])

        store.set_password(self.user["id"], "brandnew1")

        self.assertIsNone(store.user_for_token(token))
        self.assertIsNotNone(store.verify_login("player", "brandnew1"))
        self.assertIsNone(store.verify_login("player", "hunter22"))

    def test_a_disabled_account_cannot_sign_in_or_use_a_token(self):
        token = store.issue_token(self.user["id"])
        store.connection().execute(
            "UPDATE users SET is_active = 0 WHERE id = ?", (self.user["id"],)
        )

        self.assertIsNone(store.verify_login("player", "hunter22"))
        self.assertIsNone(store.user_for_token(token))


class PriceTests(unittest.TestCase):
    def test_a_request_is_never_free(self):
        self.assertGreaterEqual(
            pricing.credits_for(0, 0), pricing.MINIMUM_CHARGE
        )

    def test_the_price_follows_the_published_rates(self):
        # 15000 in at 400/M plus 1000 out at 1600/M is 7.6 credits, rounded up.
        self.assertEqual(pricing.credits_for(15_000, 1000), 8)

    def test_the_reservation_is_built_from_the_input_and_the_output_cap(self):
        messages = [{"role": "user", "content": "x" * 2000}]
        # 2000 characters is estimated at 1000 input tokens, plus the whole cap.
        self.assertEqual(
            pricing.estimate_hold(messages, 3000),
            pricing.credits_for(1000, 3000),
        )

    def test_a_larger_output_cap_reserves_more(self):
        messages = [{"role": "user", "content": "x" * 100}]
        self.assertGreater(
            pricing.estimate_hold(messages, 3000),
            pricing.estimate_hold(messages, 500),
        )

    def test_a_longer_prompt_reserves_more(self):
        short = pricing.estimate_hold([{"role": "user", "content": "x" * 100}])
        long = pricing.estimate_hold(
            [{"role": "user", "content": "x" * 100_000}]
        )
        self.assertGreater(long, short)


if __name__ == "__main__":
    unittest.main()
