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

    def test_primary_action_leaves_room_for_its_label(self):
        page = AnalysisPage()
        self.assertGreaterEqual(
            page._btn_analyze.minimumWidth(),
            page._btn_analyze.sizeHint().width() + 4,
        )

    def test_input_tools_show_an_icon_and_label(self):
        page = AnalysisPage()
        for button in (page._btn_open, page._btn_image, page._btn_clear):
            self.assertTrue(button.text())
            self.assertFalse(button.icon().isNull())

    def test_input_tools_have_no_tooltips(self):
        page = AnalysisPage()
        for button in (page._btn_open, page._btn_image, page._btn_clear):
            self.assertEqual(button.toolTip(), "")

    def test_primary_action_turns_into_stop_while_busy(self):
        page = AnalysisPage()
        page.set_pgn("1. e4 *")
        seen = []
        page.analyze_requested.connect(lambda text: seen.append("analyze"))
        page.stop_requested.connect(lambda: seen.append("stop"))

        page.set_busy(True)
        page._btn_analyze.click()
        self.assertEqual(seen, ["stop"])

        page.set_busy(False)
        page._btn_analyze.click()
        self.assertEqual(seen, ["stop", "analyze"])

    def test_primary_action_offers_reanalysis_after_results(self):
        from checkpause.i18n import t

        page = AnalysisPage()
        page.set_review([{"side": "white", "label": "Best"}])
        self.assertEqual(page._btn_analyze.text(), t("btn_reanalyze", "zh-CN"))
        self.assertFalse(page._review_filter.isHidden())

        page.set_review([])
        self.assertEqual(page._btn_analyze.text(), t("btn_analyze", "zh-CN"))
        self.assertTrue(page._review_filter.isHidden())

    def test_english_action_labels_fit_the_side_panel_width(self):
        from checkpause.gui.main_window import SIDE_PANEL_MIN_WIDTH

        page = AnalysisPage()
        page.retranslate("en-US")
        self.assertLessEqual(page.minimumSizeHint().width(), SIDE_PANEL_MIN_WIDTH)
        self.assertLessEqual(page._review_filter.sizeHint().width(), SIDE_PANEL_MIN_WIDTH)

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
