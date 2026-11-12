import json
import os
import tempfile
import unittest
from unittest import mock

import chess

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtTest import QTest
    from PySide6.QtWidgets import QApplication

    from checkpause.data import puzzles
    from checkpause.gui.pages import puzzle_page as puzzle_page_module
    from checkpause.gui.pages.puzzle_page import (
        PuzzlePage,
        _profile_axis_label,
        _solution_text,
    )

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


def _mate_in_one_fen():
    board = chess.Board()
    for san in ("f3", "e5", "g4"):
        board.push_san(san)
    return board.fen()


def _puzzle():
    return {
        "id": "p-good",
        "fen": _mate_in_one_fen(),
        "moves": ["d8h4"],
        "rating": 800,
        "themes": ["mate"],
        "opponent_first": False,
    }


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PuzzlePageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name
        self._patch = mock.patch.object(puzzles, "PUZZLE_DIR", self.base)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        self._account = mock.patch.object(puzzle_page_module, "get_account", return_value={})
        self._account.start()
        self.addCleanup(self._account.stop)
        self._server = mock.patch.object(puzzle_page_module, "get_server_url", return_value="")
        self._server.start()
        self.addCleanup(self._server.stop)
        self.page = PuzzlePage()
        self.addCleanup(self.page.deleteLater)

    def _write_collection(self, collection_id, rows):
        path = os.path.join(self.base, collection_id + ".jsonl")
        with open(path, "w", encoding="utf-8") as handle:
            for row in rows:
                if isinstance(row, str):
                    handle.write(row + "\n")
                else:
                    handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        entries = puzzles.load_index(self.base)
        entries = [item for item in entries if item.get("id") != collection_id]
        entries.append(
            {
                "id": collection_id,
                "name": collection_id,
                "file": path,
                "format": "jsonl",
                "count": len(rows),
            }
        )
        puzzles.save_index(entries, self.base)
        self.page.refresh_collections()

    def _standard_collection(self):
        self._write_collection("test", [_puzzle(), "{not json", _puzzle()])

    def test_bad_row_is_skipped_instead_of_blocking_next(self):
        self._standard_collection()
        self.page._start_collection("test")
        self.page._on_move_requested(chess.D8, chess.H4)
        self.assertTrue(self.page._session.solved)

        self.page._next()

        self.assertEqual(self.page._index, 2)
        self.assertIsNotNone(self.page._session)
        self.assertIn("跳过", self.page._train._notice.text())

    def test_a_bad_first_row_is_skipped(self):
        self._write_collection("badfirst", ["{not json", _puzzle()])
        self.page._start_collection("badfirst")

        self.assertEqual(self.page._index, 1)
        self.assertIsNotNone(self.page._session)

    def test_bad_collection_clears_the_old_board(self):
        self._standard_collection()
        self.page._start_collection("test")
        self.page._on_move_requested(chess.D8, chess.H4)
        self.assertEqual(self.page._train.board.index, 1)

        self._write_collection("broken", ["{not json"])
        self.page._start_collection("broken")

        self.assertIsNone(self.page._session)
        self.assertEqual(self.page._train.board.index, 0)
        self.assertIn("无效", self.page._train._prompt.text())

    def test_wrong_move_reverts_and_revealed_result_offers_next(self):
        self._standard_collection()
        self.page._start_collection("test")
        self.page._on_move_requested(chess.F8, chess.C5)
        self.assertEqual(self.page._train.board.index, 1)
        self.assertEqual(self.page._train._play_card.property("state"), "wrong")
        self.assertTrue(self.page._train._btn_next.isHidden())

        QTest.qWait(900)
        self.assertEqual(self.page._train.board.index, 0)

        self.page._start_collection("test", 0)
        self.page._reveal_solution()
        self.assertEqual(self.page._train._play_card.property("state"), "revealed")
        self.assertFalse(self.page._train._btn_next.isHidden())

    def test_back_after_online_puzzle_returns_to_the_hub(self):
        self.page._train_origin = "library"

        self.page._load_online_puzzle(
            {"puzzle": dict(_puzzle(), id=""), "rating": 1500, "rd": 80},
            rated=True,
        )
        self.assertEqual(self.page._train_origin, "hub")

        self.page._back_from_train()
        self.assertIs(self.page._stack.currentWidget(), self.page._hub)

    def test_local_puzzles_do_not_request_lichess_history(self):
        self._standard_collection()
        with mock.patch.object(self.page, "_load_game_history") as history:
            self.page._start_collection("test")
        self.assertFalse(history.called)

    def test_online_puzzles_still_load_history(self):
        self.page._online = True
        with mock.patch.object(self.page, "_load_game_history") as history:
            self.page._activate_puzzle(_puzzle())
        self.assertTrue(history.called)

    def test_a_matching_history_is_applied(self):
        self.page._activate_puzzle(_puzzle())
        moves = [
            chess.Move.from_uci("f2f3"),
            chess.Move.from_uci("e7e5"),
            chess.Move.from_uci("g2g4"),
        ]

        self.page._on_game_history("p-good", moves, None)

        self.assertTrue(self.page._history_applied)
        self.assertEqual(self.page._train.board.index, 3)

    def test_an_inconsistent_history_is_ignored(self):
        self.page._activate_puzzle(_puzzle())

        self.page._on_game_history(
            "p-good",
            [chess.Move.from_uci("e2e4")],
            None,
        )

        self.assertFalse(self.page._history_applied)
        self.assertEqual(self.page._train.board.index, 0)

    def test_challenge_timer_pauses_while_the_page_is_hidden(self):
        self.page.show()
        _APP.processEvents()
        self._standard_collection()
        self.page._start_collection("test")
        self.page._set_challenge("storm")
        self.assertTrue(self.page._challenge_timer.isActive())

        self.page.hide()
        _APP.processEvents()
        self.assertTrue(self.page._challenge_paused)
        self.assertFalse(self.page._challenge_timer.isActive())

        self.page.show()
        _APP.processEvents()
        self.assertFalse(self.page._challenge_paused)
        self.assertTrue(self.page._challenge_timer.isActive())

    def test_online_result_does_not_steal_focus_from_the_library(self):
        self.page.show_library()
        self.page._next_request_id = 7
        self.page._on_online_next_done(
            "next",
            {"puzzle": dict(_puzzle(), id=""), "rating": 1500},
            7,
        )
        self.assertIs(self.page._stack.currentWidget(), self.page._library)

    def test_solution_text_omits_the_opponent_setup(self):
        text = _solution_text(
            chess.STARTING_FEN,
            ["e2e4", "e7e5", "g1f3"],
            opponent_first=True,
        )
        self.assertNotIn("e4", text)
        self.assertIn("2.Nf3", text)

    def test_local_mistakes_are_derived_from_attempts(self):
        puzzles.record_attempt(_puzzle(), "failed", base_dir=self.base)
        self.page._start_local_mistakes()

        self.assertEqual(self.page._collection.id, puzzles.MISTAKES_ID)
        self.assertEqual(self.page._collection.count, 1)
        self.assertEqual(self.page._train_origin, "hub")
        self.assertIsNotNone(self.page._session)

    def test_an_expired_session_still_queues_the_attempt(self):
        self.page._online = True
        self.page._online_rated = True
        self.page._auth_expired = True
        self.page._token = "token"
        self.page._server_url = "https://server"
        self.page._account_username = "player"
        self.page._puzzle = _puzzle()
        self.page._client_attempt_id = "attempt-1"
        self.page._started_at = 0
        with mock.patch.object(puzzle_page_module, "append_outbox") as append:
            self.page._queue_online_attempt("failed")

        self.assertTrue(append.called)
        self.assertIn("created_at", append.call_args.args[0])

    def test_rating_area_shows_the_ladder_delta(self):
        self.page._train.set_rating(1046, 30.3)
        self.assertEqual(self.page._train._rating_value.text(), "1046")
        self.assertEqual(self.page._train._rating_delta.text(), "+30")

        self.page._train.set_rating(1030, -22)
        self.assertEqual(self.page._train._rating_value.text(), "1030")
        self.assertEqual(self.page._train._rating_delta.text(), "-22")

        self.page._train.set_rating(None)
        self.assertTrue(self.page._train._rating_value.isHidden())

    def test_hub_offers_ladder_and_practice_when_online(self):
        self.page._hub.set_online(True, 1000)
        self.assertEqual(self.page._hub._btn_train.text(), "天梯模式")
        self.assertEqual(self.page._hub._btn_practice.text(), "练习模式")
        self.assertFalse(self.page._hub._btn_practice.isHidden())

        self.page._hub.set_online(False, None)
        self.assertEqual(self.page._hub._btn_train.text(), "开始答题")
        self.assertTrue(self.page._hub._btn_practice.isHidden())

    def test_practice_mode_requests_unrated_puzzles(self):
        self.page._token = "token"
        self.page._server_url = "https://server"
        self.page._auth_expired = False
        with (
            mock.patch.object(self.page, "_refresh_account"),
            mock.patch.object(self.page, "_start_online_request") as request,
        ):
            self.page._start_practice()

        self.assertTrue(self.page._practice_mode)
        self.assertEqual(request.call_args.args[0], "practice")

    def test_next_keeps_practice_mode(self):
        self.page._online = True
        self.page._practice_mode = True
        self.page._review_puzzles = []
        with (
            mock.patch.object(self.page, "_start_practice") as practice,
            mock.patch.object(self.page, "_start_online_training") as ladder,
        ):
            self.page._next()

        practice.assert_called_once()
        ladder.assert_not_called()

    def test_user_imports_beat_the_builtin_sample(self):
        self._write_collection("test", [_puzzle()])
        preferred = self.page._preferred_collection()
        self.assertEqual(preferred.id, "test")

    def test_profile_labels_local_and_rated_scope(self):
        self.assertIn("本机", self.page._profile._scope_note.text())

        self.page._profile.refresh(
            {
                "rating": 1500,
                "rd": 80,
                "attempts": 1,
                "accuracy": 100,
                "recent": [],
                "themes": [],
            },
            "zh-CN",
        )
        self.assertIn("连对只统计计分题", self.page._profile._scope_note.text())

    def test_profile_theme_radar_only_shows_for_rated_profiles(self):
        axes = [
            {"theme": "mate", "attempts": 6, "solved": 3, "accuracy": 50, "rating": 1520},
            {"theme": "fork", "attempts": 5, "solved": 3, "accuracy": 60, "rating": 1480},
            {"theme": "rookEndgame", "attempts": 1, "solved": 1, "accuracy": 100, "rating": None},
        ]
        self.page._profile.refresh({"rating": 1500, "attempts": 3, "theme_axes": axes}, "zh-CN")
        self.assertFalse(self.page._profile._themes_box.isHidden())
        self.assertFalse(self.page._profile._radar.is_placeholder())
        self.assertFalse(self.page._profile._radar.grab().isNull())

        self.page._profile.refresh({"attempts": 3, "theme_axes": axes}, "zh-CN")
        self.assertTrue(self.page._profile._themes_box.isHidden())

    def test_profile_radar_keeps_a_placeholder_for_short_samples(self):
        axes = [
            {"theme": axis, "attempts": 2, "solved": 1, "accuracy": 50, "rating": None}
            for axis in puzzle_page_module._PROFILE_AXIS_KEYS
        ]
        self.page._profile.refresh({"rating": 1500, "attempts": 2, "theme_axes": axes}, "zh-CN")
        self.assertFalse(self.page._profile._themes_box.isHidden())
        self.assertTrue(self.page._profile._radar.is_placeholder())
        self.assertFalse(self.page._profile._radar.grab().isNull())
        self.assertIn("同一主题", self.page._profile._themes_hint.text())

    def test_profile_axis_labels_are_localised(self):
        self.assertEqual(_profile_axis_label("rookEndgame", "zh-CN"), "车残局")
        self.assertEqual(_profile_axis_label("defensiveMove", "en-US"), "Defensive move")

    def test_records_card_merges_stats_and_mistake_practice(self):
        self.assertEqual(self.page._hub._records_card.title.text(), "记录")
        self.assertEqual(self.page._hub._records_card.button.text(), "查看")

    def test_records_card_opens_the_profile(self):
        self.page._hub._records_card.button.click()
        self.assertIs(self.page._stack.currentWidget(), self.page._profile)

    def test_profile_range_uses_segmented_buttons(self):
        self.assertFalse(hasattr(self.page._profile, "_range"))
        self.page._profile._range_buttons[2][1].click()
        self.assertEqual(self.page._profile._range_days, 90)
        self.assertEqual(self.page._profile_days, 90)

    def test_retry_button_waits_for_retryable_mistakes(self):
        self.page._profile.refresh({"attempts": 1, "retryable": 0}, "zh-CN")
        self.assertTrue(self.page._profile._btn_mistakes.isHidden())

        self.page._profile.refresh({"attempts": 1, "retryable": 2}, "zh-CN")
        self.assertFalse(self.page._profile._btn_mistakes.isHidden())


if __name__ == "__main__":
    unittest.main()
