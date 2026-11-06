import os
import tempfile
import unittest

import chess

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.data.learn import load_progress
    from checkpause.data.lessons import load_lessons
    from checkpause.gui.pages.learn_page import LearnPage
    from checkpause.i18n import t

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class LearnPageTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name
        self.page = LearnPage(progress_base_dir=self.base)
        self.addCleanup(self.page.deleteLater)

    def test_grid_lists_every_lesson(self):
        self.assertEqual(len(self.page._cards), len(load_lessons()))
        self.assertIs(self.page._stack.currentWidget(), self.page._grid_view)

    def test_header_ignores_progress_for_removed_lessons(self):
        # Old installs still carry progress for lessons that were replaced.
        self.page._progress = {
            "basics_check": {"step": 1, "completed": True},
            "piece_rook": {"step": 1, "completed": True},
        }
        self.page._refresh_header_progress()
        self.assertEqual(
            self.page._header_progress.text(),
            t(
                "learn_progress",
                self.page._language,
                done=1,
                total=len(load_lessons()),
            ),
        )

    def test_first_lesson_completes_and_saves(self):
        self.page.show_lesson("piece_rook")
        self.assertIs(self.page._stack.currentWidget(), self.page._detail_view)
        self.assertFalse(self.page._session.is_info)
        self.assertIn(chess.A8, self.page._board._lesson_marks)

        self.page._on_move_requested(chess.A1, chess.A8)
        self.assertTrue(self.page._session.solved)
        self.assertEqual(self.page._board._lesson_marks, set())
        self.assertTrue(self.page._advance_timer.isActive())

        self.page._advance_after_solve()
        self.assertFalse(self.page._session.completed)
        self.assertEqual(self.page._session.index, 1)

        self.page._on_move_requested(chess.A1, chess.H1)
        self.page._advance_after_solve()
        self.assertEqual(self.page._session.index, 2)

        self.page._on_move_requested(chess.A1, chess.A4)
        self.page._advance_after_solve()
        self.assertTrue(self.page._session.completed)
        self.assertEqual(
            load_progress(self.base)["piece_rook"],
            {"step": 3, "completed": True},
        )
        self.assertEqual(
            self.page._cards["piece_rook"]._badge.property("status"),
            "done",
        )

        self.page._btn_primary.click()
        self.assertIs(self.page._stack.currentWidget(), self.page._grid_view)

    def test_sparse_positions_can_still_move(self):
        # K vs K, K+B vs K and K+N vs K are "insufficient material" to chess,
        # but lessons must keep the pieces pickable anyway.
        for lesson_id, square in (
            ("piece_king", chess.E1),
            ("piece_bishop", chess.C1),
            ("piece_knight", chess.B1),
        ):
            self.page.show_lesson(lesson_id)
            self.assertTrue(
                self.page._board.can_pick(square),
                lesson_id,
            )

    def test_lesson_opens_on_an_interactive_step(self):
        self.page.show_lesson("piece_bishop")
        self.assertTrue(self.page._board._interactive)
        self.assertTrue(self.page._board._lesson_arrows)  # teaching hint is visible
        self.assertTrue(self.page._btn_primary.isHidden())  # nothing to confirm first
        self.assertFalse(self.page._step_progress.isHidden())

    def test_wrong_move_keeps_the_step_open(self):
        self.page.show_lesson("piece_rook")
        self.page._on_move_requested(chess.A1, chess.A2)
        self.assertFalse(self.page._session.solved)
        self.assertEqual(self.page._session.last_status, "wrong")
        self.assertEqual(self.page._feedback.property("state"), "error")
        self.assertFalse(self.page._advance_timer.isActive())

    def test_completed_lesson_replays_without_losing_progress(self):
        self.page.show_lesson("piece_rook")
        for origin, target in (
            (chess.A1, chess.A8),
            (chess.A1, chess.H1),
            (chess.A1, chess.A4),
        ):
            self.page._on_move_requested(origin, target)
            self.page._advance_after_solve()
        self.page._btn_primary.click()

        self.page.show_lesson("piece_rook")
        self.assertTrue(self.page._replaying)
        self.assertEqual(self.page._session.index, 0)
        self.page._back_to_grid()
        self.assertEqual(
            load_progress(self.base)["piece_rook"],
            {"step": 3, "completed": True},
        )


if __name__ == "__main__":
    unittest.main()
