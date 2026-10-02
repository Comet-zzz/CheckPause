import json
import os
import tempfile
import unittest
from unittest import mock

from checkpause.data import settings


class ServerUrlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "settings.json")
        patches = [
            mock.patch.object(settings, "SETTINGS_FILE", self.path),
            mock.patch.object(settings, "ensure_data_dir", lambda: self._tmp.name),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _write(self, data):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)

    def test_default_server_url_is_the_https_domain(self):
        self.assertEqual(settings.get_server_url(), "https://checkpause.com")

    def test_saved_legacy_ip_migrates_to_the_domain(self):
        self._write({"server_url": "http://43.108.99.244"})
        self.assertEqual(settings.get_server_url(), "https://checkpause.com")

    def test_a_custom_server_url_is_kept(self):
        self._write({"server_url": "https://example.test"})
        self.assertEqual(settings.get_server_url(), "https://example.test")


if __name__ == "__main__":
    unittest.main()
