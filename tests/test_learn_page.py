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

    def test_first_lesson_completes_and_saves(self):
        self.page.show_lesson("piece_rook")
        self.assertIs(self.page._stack.currentWidget(), self.page._detail_view)
        self.assertTrue(self.page._session.is_info)

        self.page._btn_primary.click()
        self.assertEqual(self.page._session.index, 1)
        self.assertFalse(self.page._session.is_info)
        self.assertIn(chess.A8, self.page._board._lesson_marks)

        self.page._on_move_requested(chess.A1, chess.A8)
        self.assertTrue(self.page._session.solved)
        self.assertEqual(self.page._board._lesson_marks, set())

        self.page._btn_primary.click()
        self.assertTrue(self.page._session.completed)
        self.assertEqual(
            load_progress(self.base)["piece_rook"],
            {"step": 2, "completed": True},
        )
        self.assertEqual(
            self.page._cards["piece_rook"]._badge.property("status"),
            "done",
        )

        self.page._btn_primary.click()
        self.assertIs(self.page._stack.currentWidget(), self.page._grid_view)

    def test_wrong_move_keeps_the_step_open(self):
        self.page.show_lesson("piece_rook")
        self.page._btn_primary.click()
        self.page._on_move_requested(chess.A1, chess.A2)
        self.assertFalse(self.page._session.solved)
        self.assertEqual(self.page._session.last_status, "wrong")
        self.assertEqual(self.page._feedback.property("state"), "error")

    def test_completed_lesson_replays_without_losing_progress(self):
        self.page.show_lesson("piece_rook")
        self.page._btn_primary.click()
        self.page._on_move_requested(chess.A1, chess.A8)
        self.page._btn_primary.click()
        self.page._btn_primary.click()

        self.page.show_lesson("piece_rook")
        self.assertTrue(self.page._replaying)
        self.assertEqual(self.page._session.index, 0)
        self.page._back_to_grid()
        self.assertEqual(
            load_progress(self.base)["piece_rook"],
            {"step": 2, "completed": True},
        )


if __name__ == "__main__":
    unittest.main()
