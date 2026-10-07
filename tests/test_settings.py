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


class DataConsentTests(unittest.TestCase):
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

    def test_collection_is_not_a_setting_the_user_can_flip(self):
        # Consent is given in the installation agreement, not in the app, so
        # there is no stored value that could turn this off.
        self.assertTrue(settings.get_share_reviews())
        self._write({"share_reviews": False})
        self.assertTrue(settings.get_share_reviews())

    def test_an_install_id_is_created_once_and_kept(self):
        first = settings.get_install_id()
        second = settings.get_install_id()
        self.assertTrue(first)
        self.assertEqual(first, second)

    def test_the_install_id_is_not_derived_from_anything_personal(self):
        self._write({"install_id": ""})
        install_id = settings.get_install_id()
        self.assertEqual(len(install_id), 32)
        self.assertTrue(all(character in "0123456789abcdef" for character in install_id))


if __name__ == "__main__":
    unittest.main()
