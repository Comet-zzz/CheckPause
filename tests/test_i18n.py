import unittest

from checkpause.i18n import MESSAGES, t


class I18nTests(unittest.TestCase):
    def test_locales_share_the_same_keys(self):
        self.assertEqual(set(MESSAGES["zh-CN"]), set(MESSAGES["en-US"]))

    def test_translate_with_values(self):
        self.assertEqual(t("puzzle_profile_best_streak_value", "zh-CN", count=3), "最高连对 3")

    def test_unknown_language_falls_back_to_chinese(self):
        self.assertEqual(t("app_title", "xx-XX"), "CheckPause")

    def test_unknown_key_returns_key(self):
        self.assertEqual(t("no_such_key"), "no_such_key")


if __name__ == "__main__":
    unittest.main()
