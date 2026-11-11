import json
import os
import sys
import tempfile
import unittest
from unittest import mock

from checkpause.data import secrets as secret_store
from checkpause.data import settings


class ServerUrlTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "settings.json")
        self.secrets_path = os.path.join(self._tmp.name, "secrets.dat")
        patches = [
            mock.patch.object(settings, "SETTINGS_FILE", self.path),
            mock.patch.object(secret_store, "SECRETS_FILE", self.secrets_path),
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
        self.secrets_path = os.path.join(self._tmp.name, "secrets.dat")
        patches = [
            mock.patch.object(settings, "SETTINGS_FILE", self.path),
            mock.patch.object(secret_store, "SECRETS_FILE", self.secrets_path),
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


class AccountSettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "settings.json")
        self.secrets_path = os.path.join(self._tmp.name, "secrets.dat")
        patches = [
            mock.patch.object(settings, "SETTINGS_FILE", self.path),
            mock.patch.object(secret_store, "SECRETS_FILE", self.secrets_path),
            mock.patch.object(settings, "ensure_data_dir", lambda: self._tmp.name),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def _write(self, data):
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)

    def _raw(self):
        with open(self.path, encoding="utf-8") as handle:
            return handle.read()

    def test_the_account_id_round_trips(self):
        settings.save_account("Player", "tok", 10, 7)
        account = settings.get_account()
        self.assertEqual(account["id"], 7)
        self.assertEqual(account["username"], "Player")
        self.assertEqual(account["balance"], 10)

    def test_the_token_is_not_written_to_settings_json(self):
        settings.save_account("Player", "tok", 10, 7)
        self.assertNotIn("tok", self._raw())
        self.assertEqual(settings.get_account()["token"], "tok")
        if sys.platform == "win32":
            with open(self.secrets_path, "rb") as handle:
                self.assertNotIn(b"tok", handle.read())

    def test_legacy_plaintext_secrets_are_migrated(self):
        self._write(
            {
                "account_username": "Player",
                "account_token": "legacy-token",
                "account_id": 7,
                "api_key": "legacy-key",
            }
        )
        self.assertEqual(settings.get_account()["token"], "legacy-token")
        self.assertEqual(settings.get_api_key(), "legacy-key")
        raw = self._raw()
        self.assertNotIn("legacy-token", raw)
        self.assertNotIn("legacy-key", raw)

    def test_saving_without_an_id_drops_the_old_one(self):
        settings.save_account("Player", "tok", 10, 7)
        settings.save_account("Player", "tok", 10)
        self.assertIsNone(settings.get_account()["id"])

    def test_clearing_removes_the_id_and_token(self):
        settings.save_account("Player", "tok", 10, 7)
        settings.clear_account()
        self.assertIsNone(settings.get_account()["id"])
        self.assertEqual(settings.get_account()["token"], "")


class ApiKeySettingsTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "settings.json")
        self.secrets_path = os.path.join(self._tmp.name, "secrets.dat")
        patches = [
            mock.patch.object(settings, "SETTINGS_FILE", self.path),
            mock.patch.object(secret_store, "SECRETS_FILE", self.secrets_path),
            mock.patch.object(settings, "ensure_data_dir", lambda: self._tmp.name),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_the_api_key_round_trips_without_plaintext(self):
        settings.save_api_config("sk-secret", "https://example.test", "model")
        self.assertEqual(settings.get_api_key(), "sk-secret")
        with open(self.path, encoding="utf-8") as handle:
            raw = handle.read()
        self.assertNotIn("sk-secret", raw)


if __name__ == "__main__":
    unittest.main()
