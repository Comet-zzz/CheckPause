import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QWidget

from checkpause.gui.layouts import (
    LESSON_BOARD_MAX_WIDTH,
    SIDE_PANEL_WIDTH,
    BoardWorkspace,
)
from checkpause.gui.widgets.board import BoardWidget

_APP = QApplication.instance() or QApplication([])


class BoardWorkspaceTest(unittest.TestCase):
    def test_right_panel_width_is_fixed_and_the_board_grows(self):
        board = BoardWidget()
        panel = QWidget()
        workspace = BoardWorkspace(board, panel)
        workspace.resize(903, 726)
        workspace.show()
        _APP.processEvents()

        self.assertEqual(panel.width(), SIDE_PANEL_WIDTH)
        self.assertEqual(board.width(), 903 - SIDE_PANEL_WIDTH)
        self.assertEqual(board._canvas._geometry()[2], 467)

        workspace.resize(1600, 900)
        _APP.processEvents()
        self.assertEqual(panel.width(), SIDE_PANEL_WIDTH)
        self.assertGreater(board.width(), 900)
        self.assertGreater(board._canvas._geometry()[2], 700)

    def test_bottom_panel_shares_the_board_column(self):
        board = BoardWidget()
        board.set_lesson_mode(True)
        panel = QWidget()
        workspace = BoardWorkspace(board, panel, panel_position="bottom")
        workspace.resize(847, 900)
        workspace.show()
        _APP.processEvents()

        self.assertLessEqual(board.width(), LESSON_BOARD_MAX_WIDTH)
        self.assertLessEqual(panel.width(), LESSON_BOARD_MAX_WIDTH)


if __name__ == "__main__":
    unittest.main()
