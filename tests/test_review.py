import unittest

import chess

from checkpause.core.review import (
    MOVE_LABELS,
    classify,
    classify_move,
    format_summary,
    labels_for,
    summary_for,
    win_percent,
)


def _record(**overrides):
    record = {
        "book": False,
        "move_uci": "e2e4",
        "best_move": "e2e4",
        "legal_count": 20,
        "eval_before": {"cp": 0, "mate": None},
        "eval_after": {"cp": 0, "mate": None},
        "alts": [],
    }
    record.update(overrides)
    return record


class WinPercentTests(unittest.TestCase):
    def test_dead_level_is_half(self):
        self.assertAlmostEqual(win_percent(0), 50.0)

    def test_advantage_tilts_upwards(self):
        self.assertGreater(win_percent(300), 50.0)
        self.assertLess(win_percent(-300), 50.0)

    def test_mate_is_pinned(self):
        self.assertEqual(win_percent(None, mate=3), 100.0)
        self.assertEqual(win_percent(None, mate=-2), 0.0)

    def test_missing_score_is_none(self):
        self.assertIsNone(win_percent(None))


class ClassifyMoveTests(unittest.TestCase):
    def setUp(self):
        self.board = chess.Board()
        self.move = chess.Move.from_uci("e2e4")

    def test_book_move(self):
        self.assertEqual(classify_move(self.board, self.move, _record(book=True)), "Book")

    def test_forced_move(self):
        record = _record(legal_count=1)
        self.assertEqual(classify_move(self.board, self.move, record), "Forced")

    def test_engine_best(self):
        self.assertEqual(classify_move(self.board, self.move, _record()), "Best")

    def test_win_percentage_thresholds(self):
        cases = (
            (-10, "Excellent"),
            (-40, "Good"),
            (-100, "Inaccuracy"),
            (-200, "Mistake"),
            (-450, "Blunder"),
        )
        for cp, expected in cases:
            record = _record(best_move="d2d4", eval_after={"cp": cp, "mate": None})
            self.assertEqual(classify_move(self.board, self.move, record), expected, msg=str(cp))

    def test_miss_when_a_mate_is_thrown_away(self):
        record = _record(
            best_move="d2d4",
            eval_before={"cp": None, "mate": 2},
            eval_after={"cp": -50, "mate": None},
        )
        self.assertEqual(classify_move(self.board, self.move, record), "Miss")

    def test_delivering_checkmate_is_best_not_miss(self):
        board = chess.Board("6k1/5ppp/8/8/8/8/8/4Q1K1 w - - 0 1")
        move = chess.Move.from_uci("e1e8")
        record = _record(
            move_uci="e1e8",
            best_move="e1e8",
            eval_before={"cp": None, "mate": 1},
            eval_after={"cp": None, "mate": 0},
        )
        self.assertEqual(classify_move(board, move, record), "Best")

    def test_great_keeps_a_clear_advantage(self):
        record = _record(
            eval_before={"cp": 200, "mate": None},
            eval_after={"cp": 200, "mate": None},
            alts=[
                {"uci": "e2e4", "cp": 200, "mate": None},
                {"uci": "d2d4", "cp": -30, "mate": None},
            ],
        )
        self.assertEqual(classify_move(self.board, self.move, record), "Great")

    def test_only_move_saves_the_game(self):
        record = _record(
            alts=[{"uci": "e2e4", "cp": 0, "mate": None}, {"uci": "d2d4", "cp": -400, "mate": None}]
        )
        self.assertEqual(classify_move(self.board, self.move, record), "Only move")

    def test_brilliant_marks_a_sound_sacrifice(self):
        board = chess.Board("4k3/8/7p/8/5B2/8/8/4K3 w - - 0 1")
        move = chess.Move.from_uci("f4g5")
        record = _record(move_uci="f4g5", best_move="f4g5")
        self.assertEqual(classify_move(board, move, record), "Brilliant")

    def test_missing_evaluations_fall_back_to_move_score(self):
        record = _record(eval_before=None, eval_after=None, move_score=0.75)
        self.assertEqual(classify_move(self.board, self.move, record), "Excellent")


class ClassifyTests(unittest.TestCase):
    def test_each_ply_is_labelled_and_counted(self):
        results = [
            _record(move_uci="e2e4"),
            _record(book=True, move_uci="e7e5"),
        ]
        annotated, summary = classify(results, "1. e4 e5")
        self.assertEqual([record["label"] for record in annotated], ["Best", "Book"])
        self.assertEqual([record["side"] for record in annotated], ["white", "black"])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["counts"]["Best"], 1)
        self.assertEqual(summary["counts"]["Book"], 1)
        self.assertEqual(len(summary["counts"]), len(MOVE_LABELS))

    def test_original_records_are_not_modified(self):
        results = [_record()]
        classify(results, "1. e4")
        self.assertNotIn("label", results[0])

    def test_unreadable_pgn_leaves_labels_empty(self):
        annotated, summary = classify([_record()], "")
        self.assertIsNone(annotated[0]["label"])
        self.assertEqual(summary["total"], 1)

    def test_no_results(self):
        self.assertEqual(
            classify([], "1. e4"), ([], {"counts": {label: 0 for label in MOVE_LABELS}, "total": 0})
        )


class SideFilterTests(unittest.TestCase):
    def setUp(self):
        self.annotated = [
            {"label": "Best", "side": "white"},
            {"label": "Book", "side": "black"},
            {"label": "Blunder", "side": "white"},
        ]

    def test_labels_for_all(self):
        self.assertEqual(labels_for(self.annotated), ["Best", "Book", "Blunder"])

    def test_labels_for_one_side(self):
        self.assertEqual(labels_for(self.annotated, "white"), ["Best", None, "Blunder"])
        self.assertEqual(labels_for(self.annotated, "black"), [None, "Book", None])

    def test_summary_for_one_side(self):
        summary = summary_for(self.annotated, "white")
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["counts"]["Best"], 1)
        self.assertEqual(summary["counts"]["Blunder"], 1)
        self.assertEqual(summary["counts"]["Book"], 0)


class FormatSummaryTests(unittest.TestCase):
    def test_counts_are_listed_in_report_order(self):
        summary = {"counts": dict.fromkeys(MOVE_LABELS, 0), "total": 5}
        summary["counts"]["Best"] = 3
        summary["counts"]["Blunder"] = 1
        self.assertEqual(format_summary(summary), "Best 3 \u00b7 Blunder 1")

    def test_empty_summary_is_blank(self):
        self.assertEqual(format_summary(None), "")
        self.assertEqual(format_summary({"counts": {}}), "")


if __name__ == "__main__":
    unittest.main()
