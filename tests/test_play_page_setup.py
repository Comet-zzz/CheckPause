import os
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.gui.pages import play_page as play_page_module
    from checkpause.gui.pages.play_page import PlayPage

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PlaySetupTests(unittest.TestCase):
    def setUp(self):
        self.page = PlayPage()
        if not self.page._openings or not self.page._endgames:
            self.skipTest("bundled openings or endgames are not present")

    def test_standard_mode_hides_the_extra_selectors(self):
        self.assertEqual(self.page._start_mode, "standard")
        self.assertTrue(self.page._opening_card.isHidden())
        self.assertTrue(self.page._endgame_combo.isHidden())

    def test_cancelling_the_opening_picker_keeps_standard_mode(self):
        with mock.patch.object(play_page_module, "choose_opening_dialog", return_value=None):
            self.page._mode_buttons["opening"].click()
        self.assertEqual(self.page._start_mode, "standard")
        self.assertTrue(self.page._mode_buttons["standard"].isChecked())

    def test_choosing_an_opening_applies_its_moves(self):
        opening = self.page._openings[0]
        with mock.patch.object(play_page_module, "choose_opening_dialog", return_value=opening):
            self.page._mode_buttons["opening"].click()
        self.assertEqual(self.page._start_mode, "opening")
        self.assertEqual(len(self.page._session.moves), len(opening["moves"]))
        self.assertEqual(self.page._opening_name.text(), opening["name_zh"])
        self.assertFalse(self.page._opening_card.isHidden())

    def test_endgame_mode_selects_the_first_endgame(self):
        endgame = self.page._endgames[0]
        self.page._mode_buttons["endgame"].click()
        self.assertEqual(self.page._start_mode, "endgame")
        self.assertEqual(self.page._session.start_fen, endgame["fen"])
        self.assertFalse(self.page._endgame_combo.isHidden())

    def test_switching_back_to_opening_keeps_the_previous_choice(self):
        opening = self.page._openings[0]
        with mock.patch.object(play_page_module, "choose_opening_dialog", return_value=opening):
            self.page._mode_buttons["opening"].click()
        self.page._mode_buttons["standard"].click()
        with mock.patch.object(
            play_page_module,
            "choose_opening_dialog",
            side_effect=AssertionError("the picker should not reopen"),
        ):
            self.page._mode_buttons["opening"].click()
        self.assertEqual(self.page._start_mode, "opening")
        self.assertEqual(self.page._opening_index, 0)


if __name__ == "__main__":
    unittest.main()
