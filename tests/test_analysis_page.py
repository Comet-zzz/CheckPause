import os
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.gui.pages import analysis_page
    from checkpause.gui.pages.analysis_page import AnalysisPage

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class ImageRecognitionGateTests(unittest.TestCase):
    def test_image_button_is_disabled_when_recognition_is_off(self):
        with mock.patch.object(analysis_page, "IMAGE_RECOGNITION_ENABLED", False):
            page = AnalysisPage()
        self.assertFalse(page._btn_image.isEnabled())

    def test_image_button_is_enabled_when_recognition_is_on(self):
        with mock.patch.object(analysis_page, "IMAGE_RECOGNITION_ENABLED", True):
            page = AnalysisPage()
        self.assertTrue(page._btn_image.isEnabled())

    def test_busy_never_enables_the_image_button_when_recognition_is_off(self):
        with mock.patch.object(analysis_page, "IMAGE_RECOGNITION_ENABLED", False):
            page = AnalysisPage()
            page.set_busy(False)
        self.assertFalse(page._btn_image.isEnabled())

    def test_busy_toggles_the_image_button_when_recognition_is_on(self):
        with mock.patch.object(analysis_page, "IMAGE_RECOGNITION_ENABLED", True):
            page = AnalysisPage()
            page.set_busy(True)
            self.assertFalse(page._btn_image.isEnabled())
            page.set_busy(False)
        self.assertTrue(page._btn_image.isEnabled())

    def test_action_buttons_leave_room_for_the_icon_and_text(self):
        page = AnalysisPage()
        for button in (
            page._btn_open,
            page._btn_image,
            page._btn_clear,
            page._btn_stop,
            page._btn_analyze,
        ):
            self.assertGreaterEqual(button.minimumWidth(), button.sizeHint().width() + 4)

    def test_show_moves_clears_the_list_when_the_line_becomes_empty(self):
        page = AnalysisPage()
        self.assertTrue(page.show_moves("1. e4 *"))
        self.assertEqual(page._stack.currentIndex(), 1)
        self.assertEqual(page._move_list._ply_count, 1)

        self.assertFalse(page.show_moves(""))

        self.assertEqual(page._stack.currentIndex(), 0)
        self.assertEqual(page._move_list._ply_count, 0)


if __name__ == "__main__":
    unittest.main()
