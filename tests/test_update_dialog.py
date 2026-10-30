import os
import unittest
from types import SimpleNamespace
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton

    from checkpause.gui import dialogs
    from checkpause.i18n import t

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class UpdateDialogTests(unittest.TestCase):
    def setUp(self):
        self.info = SimpleNamespace(
            version="2.0.5",
            url="https://example.com/CheckPause_Setup_2.0.5.zip",
            notes="",
        )

    def test_in_app_update_does_not_open_a_browser(self):
        download_button = QPushButton()
        with (
            mock.patch.object(QMessageBox, "exec"),
            mock.patch.object(
                QMessageBox, "addButton", side_effect=[download_button, QPushButton()]
            ) as add_button,
            mock.patch.object(QMessageBox, "clickedButton", return_value=download_button),
            mock.patch.object(dialogs.QDesktopServices, "openUrl") as open_url,
        ):
            accepted = dialogs.show_update_dialog(None, "zh-CN", self.info, in_app=True)

        self.assertTrue(accepted)
        self.assertEqual(
            add_button.call_args_list[0].args[0],
            t("update_download_install", "zh-CN"),
        )
        open_url.assert_not_called()

    def test_external_update_keeps_the_browser_download_flow(self):
        download_button = QPushButton()
        with (
            mock.patch.object(QMessageBox, "exec"),
            mock.patch.object(
                QMessageBox,
                "addButton",
                side_effect=[download_button, QPushButton()],
            ),
            mock.patch.object(QMessageBox, "clickedButton", return_value=download_button),
            mock.patch.object(dialogs.QDesktopServices, "openUrl") as open_url,
        ):
            accepted = dialogs.show_update_dialog(None, "zh-CN", self.info)

        self.assertTrue(accepted)
        open_url.assert_called_once()


if __name__ == "__main__":
    unittest.main()
