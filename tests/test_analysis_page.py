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


if __name__ == "__main__":
    unittest.main()
