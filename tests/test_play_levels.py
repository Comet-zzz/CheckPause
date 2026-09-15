import unittest

from checkpause.config import (
    PLAY_ELO_FLOOR,
    PLAY_RATING_MAX,
    PLAY_RATING_MIN,
    clamp_play_rating,
    play_engine_settings,
    play_rating_tier,
)

RATINGS = list(range(PLAY_RATING_MIN, PLAY_RATING_MAX + 1, 50))


class PlayRatingTests(unittest.TestCase):
    def test_clamp_play_rating(self):
        self.assertEqual(clamp_play_rating(0), PLAY_RATING_MIN)
        self.assertEqual(clamp_play_rating(99999), PLAY_RATING_MAX)
        self.assertEqual(clamp_play_rating(1500), 1500)

    def test_floor_rating_uses_calibrated_elo(self):
        settings = play_engine_settings(PLAY_ELO_FLOOR)
        self.assertEqual(
            settings["options"],
            {"UCI_LimitStrength": True, "UCI_Elo": PLAY_ELO_FLOOR},
        )
        self.assertFalse(settings["approximate"])

    def test_below_floor_uses_skill_level(self):
        settings = play_engine_settings(PLAY_RATING_MIN)
        self.assertEqual(settings["options"], {"Skill Level": 0})
        self.assertTrue(settings["approximate"])

    def test_nodes_grow_with_rating(self):
        nodes = [play_engine_settings(r)["nodes"] for r in RATINGS]
        self.assertEqual(nodes, sorted(nodes))

    def test_nodes_never_drop_across_the_floor(self):
        below = play_engine_settings(PLAY_ELO_FLOOR - 20)
        above = play_engine_settings(PLAY_ELO_FLOOR + 30)
        self.assertTrue(below["approximate"])
        self.assertFalse(above["approximate"])
        self.assertLessEqual(below["nodes"], above["nodes"])

    def test_elo_is_clamped_to_the_engines_own_floor(self):
        below = play_engine_settings(1320, elo_floor=1400)
        above = play_engine_settings(1400, elo_floor=1400)
        self.assertIn("Skill Level", below["options"])
        self.assertEqual(above["options"]["UCI_Elo"], 1400)

    def test_engine_without_uci_elo_always_falls_back(self):
        for rating in RATINGS:
            settings = play_engine_settings(rating, supports_elo=False)
            self.assertIn("Skill Level", settings["options"])
            self.assertTrue(settings["approximate"])

    def test_engines_receive_only_one_strength_mechanism(self):
        for rating in RATINGS:
            options = play_engine_settings(rating)["options"]
            uses_elo = "UCI_LimitStrength" in options
            uses_skill = "Skill Level" in options
            self.assertNotEqual(uses_elo, uses_skill)

    def test_tier_lookup_picks_the_closest_landmark(self):
        self.assertEqual(play_rating_tier(PLAY_RATING_MIN), "beginner")
        self.assertEqual(play_rating_tier(1500), "medium")
        self.assertEqual(play_rating_tier(PLAY_RATING_MAX), "master")
        self.assertEqual(play_rating_tier(2400), "hard")


if __name__ == "__main__":
    unittest.main()
