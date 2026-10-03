import unittest

import chess
import chess.engine

from checkpause.core.engine import (
    compact_analysis,
    eval_ratio,
    format_eval,
    read_score,
)


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


class ReadScoreTests(unittest.TestCase):
    def test_centipawns_are_read_in_whites_favour(self):
        info = {"score": chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE)}
        self.assertEqual(read_score(info), (50, None))

    def test_black_point_of_view_is_converted_for_white(self):
        info = {"score": chess.engine.PovScore(chess.engine.Cp(50), chess.BLACK)}
        self.assertEqual(read_score(info), (-50, None))

    def test_mate_is_reported_separately(self):
        info = {
            "score": chess.engine.PovScore(chess.engine.Mate(-3), chess.WHITE)
        }
        self.assertEqual(read_score(info), (None, -3))

    def test_missing_score_is_neutral(self):
        self.assertEqual(read_score({}), (None, None))
        self.assertEqual(read_score(None), (None, None))


class EvalRatioTests(unittest.TestCase):
    def test_dead_level_is_half(self):
        self.assertAlmostEqual(eval_ratio(0), 0.5)
        self.assertAlmostEqual(eval_ratio(None), 0.5)

    def test_white_advantage_tilts_the_bar(self):
        self.assertGreater(eval_ratio(200), 0.5)
        self.assertLess(eval_ratio(-200), 0.5)

    def test_mate_pins_the_bar(self):
        self.assertEqual(eval_ratio(None, mate=3), 1.0)
        self.assertEqual(eval_ratio(None, mate=-2), 0.0)


class FormatEvalTests(unittest.TestCase):
    def test_centipawns_are_signed_decimal(self):
        self.assertEqual(format_eval(124), "+1.24")
        self.assertEqual(format_eval(-30), "-0.30")

    def test_mate_is_rendered_as_distance(self):
        self.assertEqual(format_eval(None, mate=3), "+M3")
        self.assertEqual(format_eval(None, mate=-2), "-M2")

    def test_missing_score_shows_zero(self):
        self.assertEqual(format_eval(None), "0.00")


if __name__ == "__main__":
    unittest.main()
