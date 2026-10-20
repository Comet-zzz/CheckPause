import os
import unittest

import chess

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.core.openings import load_openings
    from checkpause.gui.opening_picker import OpeningPicker

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class OpeningPickerTests(unittest.TestCase):
    def setUp(self):
        self.openings = load_openings()
        if not self.openings:
            self.skipTest("bundled openings file is not present")
        self.dialog = OpeningPicker(None, self.openings, "zh-CN")

    def test_tree_keeps_categories_and_every_opening(self):
        self.assertEqual(self.dialog._tree.topLevelItemCount(), 4)
        self.assertEqual(len(self.dialog._leaf_items), len(self.openings))

    def test_initial_selection_previews_the_first_opening(self):
        self.assertIsNotNone(self.dialog.selected_opening)
        self.assertEqual(self.dialog.selected_opening["name"], self.openings[0]["name"])
        self.assertTrue(self.dialog._moves_label.text())
        self.assertTrue(self.dialog._ok_button.isEnabled())

    def test_english_search_filters_the_list(self):
        self.dialog._search.setText("sicilian")
        visible = [item for item in self.dialog._leaf_items if not item.isHidden()]
        self.assertEqual(len(visible), 7)
        self.assertTrue(self.dialog.selected_opening["name"].startswith("Sicilian Defense"))

    def test_chinese_search_filters_the_list(self):
        self.dialog._search.setText("柏林")
        visible = [item for item in self.dialog._leaf_items if not item.isHidden()]
        self.assertEqual(len(visible), 1)
        self.assertEqual(self.dialog.selected_opening["name"], "Ruy Lopez: Berlin Defense")

    def test_no_match_disables_confirmation(self):
        self.dialog._search.setText("no-such-opening")
        self.assertIsNone(self.dialog.selected_opening)
        self.assertFalse(self.dialog._ok_button.isEnabled())

    def test_clearing_the_search_restores_a_selection(self):
        self.dialog._search.setText("no-such-opening")
        self.dialog._search.clear()
        self.assertIsNotNone(self.dialog.selected_opening)
        self.assertTrue(self.dialog._ok_button.isEnabled())

    def test_choose_a_specific_opening(self):
        target = next(
            opening for opening in self.openings if opening["name"] == "Queen's Gambit Declined"
        )
        index = self.openings.index(target)
        self.dialog._select_index(index)
        self.assertEqual(self.dialog.selected_opening["name"], target["name"])
        self.assertEqual(self.dialog._preview._board.fen(), _end_fen(target))

    def test_english_mode_uses_english_labels(self):
        dialog = OpeningPicker(None, self.openings[:1], "en-US")
        labels = [
            dialog._tree.topLevelItem(row).text(0)
            for row in range(dialog._tree.topLevelItemCount())
        ]
        self.assertIn("Open games", labels)


def _end_fen(opening):
    board = chess.Board()
    for move in opening["moves"]:
        board.push(move)
    return board.fen()


if __name__ == "__main__":
    unittest.main()
