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
        response = self.client.get("/")
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


if __name__ == "__main__":
    unittest.main()
