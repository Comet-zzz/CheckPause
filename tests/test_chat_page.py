import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from checkpause.gui.pages.chat_page import ChatPage

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class MarkdownBubbleTests(unittest.TestCase):
    def setUp(self):
        self.page = ChatPage()

    def test_assistant_bubbles_render_markdown(self):
        self.page.begin_assistant()
        self.page.append_chunk("**bold** text")
        self.assertEqual(self.page._current_bubble.textFormat(), Qt.TextFormat.MarkdownText)

    def test_streamed_fragments_keep_the_markdown_source(self):
        self.page.begin_assistant()
        self.page.append_chunk("**bo")
        self.page.append_chunk("ld**")
        self.assertEqual(self.page._current_markdown, "**bold**")

    def test_an_unfinished_marker_is_still_kept_for_the_final_render(self):
        self.page.begin_assistant()
        self.page.append_chunk("a **b")
        self.assertEqual(self.page._current_markdown, "a **b")

    def test_user_bubbles_stay_plain_text(self):
        self.page.append_user("player", "<b>not markup</b>")
        bubble, role = self.page._bubbles[-1]
        self.assertEqual(role, "user")
        self.assertEqual(bubble.textFormat(), Qt.TextFormat.PlainText)

    def test_clear_history_resets_the_streaming_buffer(self):
        self.page.begin_assistant()
        self.page.append_chunk("**a**")
        self.page.clear_history()
        self.page.append_chunk("plain")
        self.assertEqual(self.page._current_markdown, "plain")


if __name__ == "__main__":
    unittest.main()
