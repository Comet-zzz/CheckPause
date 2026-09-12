import os
import tempfile
import unittest
from unittest import mock

from checkpause.assets import DEFAULT_BOARD_THEME, DEFAULT_PIECE_SET
from checkpause.data import profile


class ProfileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = os.path.join(self._tmp.name, "profile.json")
        patches = [
            mock.patch.object(profile, "PROFILE_FILE", self.path),
            mock.patch.object(
                profile,
                "LEGACY_PROFILE_FILE",
                os.path.join(self._tmp.name, "legacy.json"),
            ),
            mock.patch.object(profile, "ensure_data_dir", lambda: self._tmp.name),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)

    def test_missing_profile_returns_none(self):
        self.assertIsNone(profile.load_profile())

    def test_create_and_load_profile(self):
        profile.create_profile("Tester", "en-US")
        loaded = profile.load_profile()
        self.assertEqual(loaded["username"], "Tester")
        self.assertEqual(loaded["language"], "en-US")
        self.assertEqual(loaded["piece_set"], DEFAULT_PIECE_SET)
        self.assertEqual(loaded["board_theme"], DEFAULT_BOARD_THEME)

    def test_update_profile_records_history(self):
        created = profile.create_profile("Tester")
        updated = profile.update_profile(created, 88.0, "1. e4 e5")
        self.assertEqual(updated["total_games"], 1)
        self.assertEqual(updated["latest_accuracy"], 88.0)
        self.assertEqual(len(updated["history"]), 1)
        self.assertEqual(updated["history"][0]["accuracy"], 88.0)

    def test_delete_profile(self):
        profile.create_profile("Tester")
        self.assertTrue(profile.delete_profile())
        self.assertFalse(profile.delete_profile())

    def test_legacy_profile_is_migrated(self):
        legacy = os.path.join(self._tmp.name, "legacy.json")
        with open(legacy, "w", encoding="utf-8") as handle:
            handle.write('{"username": "Legacy"}')
        loaded = profile.load_profile()
        self.assertEqual(loaded["username"], "Legacy")
        self.assertTrue(os.path.exists(self.path))
        self.assertFalse(os.path.exists(legacy))


if __name__ == "__main__":
    unittest.main()
