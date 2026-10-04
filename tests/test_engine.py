import unittest

import chess
import chess.engine

from checkpause.core.engine import (
    compact_analysis,
    eval_ratio,
    format_eval,
    read_lines,
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


class ReadLinesTests(unittest.TestCase):
    def test_lines_are_ranked_best_first(self):
        infos = {
            2: {
                "score": chess.engine.PovScore(chess.engine.Cp(120), chess.WHITE),
                "pv": [chess.Move.from_uci("d2d4")],
            },
            1: {
                "score": chess.engine.PovScore(chess.engine.Cp(50), chess.WHITE),
                "pv": [chess.Move.from_uci("e2e4")],
            },
        }
        self.assertEqual(
            read_lines(infos),
            [
                {"uci": "e2e4", "margin": 50, "mate": None},
                {"uci": "d2d4", "margin": 120, "mate": None},
            ],
        )

    def test_lines_without_a_continuation_are_skipped(self):
        infos = {
            1: {
                "score": chess.engine.PovScore(chess.engine.Cp(0), chess.WHITE),
                "pv": [],
            }
        }
        self.assertEqual(read_lines(infos), [])

    def test_mate_lines_report_the_mate_count(self):
        infos = {
            1: {
                "score": chess.engine.PovScore(chess.engine.Mate(3), chess.WHITE),
                "pv": [chess.Move.from_uci("e2e4")],
            }
        }
        self.assertEqual(
            read_lines(infos), [{"uci": "e2e4", "margin": None, "mate": 3}]
        )


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
