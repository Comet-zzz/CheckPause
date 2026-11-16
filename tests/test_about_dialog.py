import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton

    from checkpause.gui.dialogs import _SettingsDialog
    from checkpause.gui.theme import LIGHT

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class SettingsAboutPageTests(unittest.TestCase):
    def _about_page(self):
        current = {
            "theme": LIGHT,
            "language": "zh-CN",
            "piece_set": "kiwen-suwi",
            "board_theme": "blue",
            "sound_set": "digital",
        }
        handlers = {key: (lambda value: None) for key in current}
        handlers.update(
            {
                "open_api": lambda: None,
                "open_account": lambda: None,
                "check_update": lambda: None,
            }
        )
        dialog = _SettingsDialog(None, "zh-CN", current, handlers)
        self.addCleanup(dialog.close)
        dialog.show()
        _APP.processEvents()
        dialog._show_page(dialog._stack.count() - 1)
        _APP.processEvents()
        return dialog._stack.currentWidget().widget()

    def test_about_page_does_not_repeat_an_about_button(self):
        page = self._about_page()
        texts = [button.text() for button in page.findChildren(QPushButton)]
        self.assertNotIn("关于", texts)
        self.assertIn("检查更新", texts)

    def test_about_page_has_links_with_icons_and_no_author_or_alpha_line(self):
        page = self._about_page()
        labels = page.findChildren(QLabel)
        text = "\n".join(label.text() for label in labels)
        self.assertIn("https://github.com/Comet-zzz/CheckPause", text)
        self.assertIn("https://checkpause.com", text)
        self.assertIn("support@checkpause.com", text)
        self.assertNotIn("作者", text)
        self.assertNotIn("CheckPause Alpha", text)
        self.assertNotIn("关于 CheckPause", text)

        icon_labels = [label for label in labels if not label.pixmap().isNull()]
        self.assertEqual(len(icon_labels), 3)
        self.assertEqual(
            {(label.pixmap().width(), label.pixmap().height()) for label in icon_labels},
            {(16, 16)},
        )


if __name__ == "__main__":
    unittest.main()
