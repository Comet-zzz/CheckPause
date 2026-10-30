import os
import unittest
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QDialog, QLabel

    from checkpause.gui.dialogs import show_about

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class AboutDialogTests(unittest.TestCase):
    def test_about_dialog_omits_the_repeated_app_logo(self):
        dialog_holder = {}

        def capture_dialog(dialog):
            dialog_holder["dialog"] = dialog
            return QDialog.DialogCode.Rejected

        with mock.patch.object(QDialog, "exec", capture_dialog):
            show_about(None, "zh-CN")

        image_labels = [
            label
            for label in dialog_holder["dialog"].findChildren(QLabel)
            if not label.pixmap().isNull()
        ]
        self.assertEqual(len(image_labels), 2)
        self.assertEqual(
            {(label.pixmap().width(), label.pixmap().height()) for label in image_labels},
            {(16, 16)},
        )


if __name__ == "__main__":
    unittest.main()
