import os
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QDialog

    from checkpause.core.pgn import PgnGame
    from checkpause.gui import dialogs

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None

GAME_ONE = '[Event "One"]\n[White "Alice"]\n[Black "Bob"]\n\n1. e4 e5 *'
GAME_TWO = '[Event "Two"]\n[White "Carol"]\n[Black "Dave"]\n\n1. d4 d5 *'


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PgnGameDialogTests(unittest.TestCase):
    def _games(self):
        return [
            PgnGame(
                offset=0,
                end=1,
                headers={
                    "White": "Alice",
                    "Black": "Bob",
                    "Result": "1-0",
                    "Date": "2024.01.02",
                    "Event": "Club",
                    "Round": "3",
                    "ECO": "C50",
                },
            ),
            PgnGame(offset=1, end=2, headers={"White": "Carol", "Black": "Dave"}),
        ]

    def test_label_shows_players_and_metadata(self):
        label = dialogs._pgn_game_label(1, self._games()[0].headers)

        self.assertIn("1. Alice — Bob", label)
        self.assertIn("1-0", label)
        self.assertIn("2024.01.02", label)
        self.assertIn("Club", label)
        self.assertIn("R3", label)
        self.assertIn("C50", label)

    def test_label_falls_back_for_missing_headers(self):
        label = dialogs._pgn_game_label(2, self._games()[1].headers)

        self.assertIn("2. Carol — Dave", label)
        self.assertIn("* · ?", label)

    def test_dialog_lists_every_game_and_selects_the_first(self):
        dialog = dialogs._PgnGameDialog(None, "zh-CN", self._games())
        self.addCleanup(dialog.close)

        self.assertEqual(dialog._list.count(), 2)
        self.assertEqual(dialog._list.currentRow(), 0)
        self.assertEqual(dialog.selected_index(), 0)

        dialog._list.setCurrentRow(1)
        self.assertEqual(dialog.selected_index(), 1)

    def test_single_game_needs_no_choice(self):
        self.assertEqual(dialogs.choose_pgn_game_dialog(None, "zh-CN", self._games()[:1]), 0)
        self.assertIsNone(dialogs.choose_pgn_game_dialog(None, "zh-CN", []))

    def test_choosing_a_game_returns_its_index(self):
        with (
            mock.patch.object(
                dialogs._PgnGameDialog,
                "exec",
                return_value=QDialog.DialogCode.Accepted,
            ),
            mock.patch.object(dialogs._PgnGameDialog, "selected_index", return_value=1),
        ):
            index = dialogs.choose_pgn_game_dialog(None, "zh-CN", self._games())

        self.assertEqual(index, 1)

    def test_cancelling_returns_none(self):
        with (
            mock.patch.object(
                dialogs._PgnGameDialog,
                "exec",
                return_value=QDialog.DialogCode.Rejected,
            ),
            mock.patch.object(dialogs._PgnGameDialog, "selected_index", return_value=0),
        ):
            index = dialogs.choose_pgn_game_dialog(None, "zh-CN", self._games())

        self.assertIsNone(index)


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PgnPasteDialogTests(unittest.TestCase):
    def _dialog(self):
        dialog = dialogs._PgnPasteDialog(None, "zh-CN")
        self.addCleanup(dialog.close)
        return dialog

    def test_empty_text_stays_open_with_an_error(self):
        dialog = self._dialog()

        dialog._accept()

        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertFalse(dialog._error.isHidden())
        self.assertIsNone(dialog.text())

    def test_a_valid_single_game_is_accepted(self):
        dialog = self._dialog()
        dialog._edit.setPlainText("1. e4 e5 *")

        dialog._accept()

        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertIn("1. e4 e5", dialog.text())

    def test_a_multi_game_paste_keeps_the_selected_game(self):
        dialog = self._dialog()
        dialog._edit.setPlainText(f"{GAME_ONE}\n\n{GAME_TWO}\n")
        with mock.patch.object(dialogs, "choose_pgn_game_dialog", return_value=1):
            dialog._accept()

        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertIn("1. d4 d5", dialog.text())
        self.assertNotIn("Alice", dialog.text())

    def test_cancelling_the_game_chooser_keeps_the_paste_open(self):
        dialog = self._dialog()
        dialog._edit.setPlainText(f"{GAME_ONE}\n\n{GAME_TWO}\n")
        with mock.patch.object(dialogs, "choose_pgn_game_dialog", return_value=None):
            dialog._accept()

        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertIsNone(dialog.text())

    def test_a_game_without_moves_is_rejected(self):
        dialog = self._dialog()
        dialog._edit.setPlainText('[White "Alice"]\n\n*')

        dialog._accept()

        self.assertNotEqual(dialog.result(), QDialog.DialogCode.Accepted)
        self.assertFalse(dialog._error.isHidden())
        self.assertIsNone(dialog.text())


if __name__ == "__main__":
    unittest.main()
