import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from checkpause.gui.theme import CHAT_COLORS, DARK, LIGHT
from checkpause.i18n import t


class ChatPage(QWidget):
    send_requested = Signal(str)
    reset_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = "light"
        self._busy = False
        self._start_time = 0.0
        self._current_bubble = None
        self._bubbles = []

        self._container = QWidget()
        self._messages_layout = QVBoxLayout(self._container)
        self._messages_layout.setContentsMargins(4, 4, 4, 4)
        self._messages_layout.setSpacing(8)
        self._messages_layout.addStretch(1)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._scroll.setWidget(self._container)

        self._input = QLineEdit()
        self._input.returnPressed.connect(self._on_send)

        self._btn_send = QPushButton()
        self._btn_send.clicked.connect(self._on_send)
        self._btn_reset = QPushButton()
        self._btn_reset.clicked.connect(self.reset_requested.emit)

        self._status = QLabel()
        self._status.setVisible(False)

        input_row = QHBoxLayout()
        input_row.addWidget(self._input, 1)
        input_row.addWidget(self._btn_send)

        button_row = QHBoxLayout()
        button_row.addWidget(self._status, 1)
        button_row.addWidget(self._btn_reset)

        layout = QVBoxLayout(self)
        layout.addWidget(self._scroll, 1)
        layout.addLayout(input_row)
        layout.addLayout(button_row)

        self._timer = QTimer(self)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._update_timer)

        self.retranslate(self._language)

    def _colors(self):
        return CHAT_COLORS[DARK] if self._theme == DARK else CHAT_COLORS[LIGHT]

    def _bubble_style(self, role):
        colors = self._colors()
        if role == "user":
            bg, fg = colors["user_bg"], colors["user_fg"]
        else:
            bg, fg = colors["ai_bg"], colors["ai_fg"]
        return (
            f"background-color: {bg}; color: {fg};"
            " border-radius: 10px; padding: 8px 12px;"
        )

    def _max_bubble_width(self):
        width = self._scroll.viewport().width()
        if width <= 0:
            width = 480
        return max(240, int(width * 0.72))

    def _add_row(self, widget, right=False):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        if right:
            row_layout.addStretch(1)
            row_layout.addWidget(widget)
        else:
            row_layout.addWidget(widget)
            row_layout.addStretch(1)
        self._messages_layout.insertWidget(
            self._messages_layout.count() - 1, row
        )

    def _scroll_to_bottom(self):
        bar = self._scroll.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _append_bubble(self, role, text):
        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        bubble.setMaximumWidth(self._max_bubble_width())
        bubble.setStyleSheet(self._bubble_style(role))
        self._bubbles.append((bubble, role))
        self._add_row(bubble, right=(role == "user"))
        self._scroll_to_bottom()
        return bubble

    def _append_notice(self, text, error=False):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color = self._colors()["error" if error else "notice"]
        label.setStyleSheet(f"color: {color}; background: transparent;")
        label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self._bubbles.append((label, "error" if error else "notice"))
        self._add_row(label)
        self._scroll_to_bottom()

    def append_user(self, username, text):
        self._append_bubble("user", text)

    def begin_assistant(self):
        self._current_bubble = self._append_bubble("assistant", "")

    def append_chunk(self, text):
        if self._current_bubble is None:
            self._current_bubble = self._append_bubble("assistant", "")
        self._current_bubble.setText(self._current_bubble.text() + text)
        self._scroll_to_bottom()

    def append_notice(self, text):
        self._append_notice(text)

    def show_error(self, text):
        self._append_notice(t("chat_error", self._language, error=text), error=True)

    def clear_history(self):
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._bubbles = []
        self._current_bubble = None

    def set_busy(self, busy):
        self._busy = busy
        self._btn_send.setEnabled(not busy)
        self._input.setEnabled(not busy)
        if busy:
            self._start_time = time.time()
            self._status.setVisible(True)
            self._timer.start()
        else:
            self._timer.stop()
            self._status.setVisible(False)

    def _update_timer(self):
        elapsed = time.time() - self._start_time
        self._status.setText(t("chat_thinking", self._language, seconds=elapsed))

    def _on_send(self):
        if self._busy:
            return
        text = self._input.text().strip()
        if not text:
            return
        self._input.clear()
        self.send_requested.emit(text)

    def set_theme(self, theme):
        self._theme = theme
        for bubble, role in self._bubbles:
            if role in ("user", "assistant"):
                bubble.setStyleSheet(self._bubble_style(role))
            else:
                color = self._colors()["error" if role == "error" else "notice"]
                bubble.setStyleSheet(f"color: {color}; background: transparent;")

    def retranslate(self, language):
        self._language = language
        self._input.setPlaceholderText(t("chat_placeholder", language))
        self._btn_send.setText(t("btn_send", language))
        self._btn_reset.setText(t("btn_reset_chat", language))
        self._status.setText(t("chat_thinking", language, seconds=0.0))
