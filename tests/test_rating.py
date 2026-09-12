import unittest

from checkpause.core.rating import rating_key


class RatingKeyTests(unittest.TestCase):
    def test_rating_thresholds(self):
        self.assertEqual(rating_key(100.0), "optimal")
        self.assertEqual(rating_key(85.0), "optimal")
        self.assertEqual(rating_key(84.9), "precise")
        self.assertEqual(rating_key(75.0), "precise")
        self.assertEqual(rating_key(74.9), "competent")
        self.assertEqual(rating_key(65.0), "competent")
        self.assertEqual(rating_key(64.9), "steady")
        self.assertEqual(rating_key(50.0), "steady")
        self.assertEqual(rating_key(49.9), "volatile")
        self.assertEqual(rating_key(0.0), "volatile")

    def test_rating_none(self):
        self.assertIsNone(rating_key(None))


if __name__ == "__main__":
    unittest.main()
