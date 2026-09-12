import unittest

from checkpause.core.engine import compact_analysis


class CompactAnalysisTests(unittest.TestCase):
    def test_book_best_and_plain_moves(self):
        results = [
            {"move": "e4", "book": True},
            {"move": "Nf3", "engine_score": 20, "best_move": "d4"},
            {"move": "Bb5", "engine_score": 15, "best_move": "Bb5"},
        ]
        self.assertEqual(
            compact_analysis(results),
            "e4(book); Nf3(score:20, best:d4); Bb5(score:15)",
        )

    def test_empty_results(self):
        self.assertEqual(compact_analysis([]), "")


if __name__ == "__main__":
    unittest.main()
