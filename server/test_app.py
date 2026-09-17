"""Smoke tests for the server app.

Run from the repository root:

    .venv\\Scripts\\python.exe -m unittest server.test_app -v
"""

import unittest

from fastapi.testclient import TestClient

from server.app import app


class StatusTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_status_page_reports_ok(self):
        response = self.client.get("/status")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["service"], "CheckPause Server")

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_unknown_path_returns_404(self):
        self.assertEqual(self.client.get("/nope").status_code, 404)


class PublicPageTests(unittest.TestCase):
    """What a reviewer, or anybody following a link, actually sees."""

    def setUp(self):
        self.client = TestClient(app)

    def test_the_front_page_is_a_page_not_a_status_blob(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("CheckPause", response.text)

    def test_the_shop_page_lists_every_pack_with_its_price(self):
        from server import config

        response = self.client.get("/shop")
        self.assertEqual(response.status_code, 200)
        for yuan in config.topup_packs():
            self.assertIn("¥{}".format(yuan), response.text)
            self.assertIn(
                "{} CP积分".format(yuan * config.CREDITS_PER_YUAN),
                response.text,
            )

    def test_the_shop_page_does_not_claim_a_price_it_does_not_sell(self):
        from server import config

        response = self.client.get("/shop")
        self.assertNotIn("¥100", response.text)
        self.assertIn("¥{}".format(max(config.topup_packs())), response.text)


if __name__ == "__main__":
    unittest.main()
