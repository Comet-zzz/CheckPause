import os
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QTabWidget

    from checkpause.gui.main_window import MainWindow
    from checkpause.gui.pages.analysis_page import AnalysisPage
    from checkpause.gui.widgets.board import BoardWidget

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None

GAME_ONE = '[Event "One"]\n[White "Alice"]\n[Black "Bob"]\n\n1. e4 e5 2. Nf3 *'
GAME_TWO = '[Event "Two"]\n[White "Carol"]\n[Black "Dave"]\n\n1. d4 d5 *'


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PgnImportTests(unittest.TestCase):
    def setUp(self):
        window = SimpleNamespace(
            _language="zh-CN",
            _results=[],
            _current_pgn="",
            _current_analysis="",
            _messages=[],
            _user_side="",
            profile=None,
            analysis_page=AnalysisPage(),
            board=BoardWidget(),
            tabs=QTabWidget(),
            chat_page=mock.Mock(),
        )
        window.tabs.addTab(window.analysis_page, "")
        window._clear_analysis_results = MainWindow._clear_analysis_results.__get__(window)
        self.window = window
        self.load = MainWindow._load_pgn_text.__get__(window)

    def test_a_single_game_loads_without_a_choice(self):
        with mock.patch("checkpause.gui.main_window.choose_pgn_game_dialog") as choose:
            loaded = self.load(GAME_ONE)

        self.assertTrue(loaded)
        choose.assert_not_called()
        self.assertIn("1. e4 e5", self.window._current_pgn)
        self.window.chat_page.clear_history.assert_called_once()

    def test_a_multi_game_document_loads_the_chosen_game(self):
        text = f"{GAME_ONE}\n\n{GAME_TWO}\n"
        with mock.patch("checkpause.gui.main_window.choose_pgn_game_dialog", return_value=1):
            loaded = self.load(text)

        self.assertTrue(loaded)
        self.assertIn("1. d4 d5", self.window._current_pgn)
        self.assertNotIn("Alice", self.window._current_pgn)
        self.assertEqual(len(self.window.board._moves), 2)

    def test_cancelling_the_choice_keeps_the_current_game(self):
        with mock.patch("checkpause.gui.main_window.choose_pgn_game_dialog", return_value=None):
            loaded = self.load(f"{GAME_ONE}\n\n{GAME_TWO}\n")

        self.assertFalse(loaded)

    def test_invalid_text_reports_an_error(self):
        loaded = self.load("garbage")

        self.assertFalse(loaded)
        self.assertFalse(self.window.analysis_page._status_label.isHidden())


if __name__ == "__main__":
    unittest.main()
