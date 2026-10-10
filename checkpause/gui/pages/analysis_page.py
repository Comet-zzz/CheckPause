from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from checkpause.config import IMAGE_RECOGNITION_ENABLED
from checkpause.core.rating import rating_key
from checkpause.gui.icons import action_icon
from checkpause.gui.theme import LIGHT
from checkpause.gui.widgets.move_list import MoveListWidget
from checkpause.i18n import t


class AnalysisPage(QWidget):
    analyze_requested = Signal(str)
    stop_requested = Signal()
    open_file_requested = Signal()
    image_requested = Signal()
    clear_requested = Signal()
    ply_selected = Signal(int)
    moves_shown = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT

        self._editor = QPlainTextEdit()
        self._editor.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))

        editor_page = QWidget()
        editor_layout = QVBoxLayout(editor_page)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.addWidget(self._editor, 1)

        self._move_list = MoveListWidget()
        self._move_list.ply_selected.connect(self.ply_selected.emit)

        self._stack = QStackedWidget()
        self._stack.addWidget(editor_page)
        self._stack.addWidget(self._move_list)

        self._btn_open = QPushButton()
        self._btn_open.clicked.connect(self.open_file_requested.emit)
        self._btn_image = QPushButton()
        self._btn_image.setEnabled(IMAGE_RECOGNITION_ENABLED)
        self._btn_image.clicked.connect(self.image_requested.emit)
        self._btn_clear = QPushButton()
        self._btn_clear.clicked.connect(self.clear)
        self._btn_analyze = QPushButton()
        self._btn_analyze.setObjectName("primaryButton")
        self._btn_analyze.clicked.connect(self._on_analyze)
        self._btn_stop = QPushButton()
        self._btn_stop.setEnabled(False)
        self._btn_stop.clicked.connect(self.stop_requested.emit)

        button_row = QHBoxLayout()
        button_row.setSpacing(6)
        button_row.addWidget(self._btn_open)
        button_row.addWidget(self._btn_image)
        button_row.addWidget(self._btn_clear)
        button_row.addStretch(1)
        button_row.addWidget(self._btn_stop)
        button_row.addWidget(self._btn_analyze)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)

        self._accuracy_label = QLabel()
        self._accuracy_label.setObjectName("accuracyLabel")
        self._accuracy_label.setVisible(False)
        self._status_label = QLabel()
        self._status_label.setObjectName("mutedLabel")
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self._stack, 1)
        layout.addLayout(button_row)
        layout.addWidget(self._progress)
        layout.addWidget(self._accuracy_label)
        layout.addWidget(self._status_label)

        self._apply_icons()
        self.retranslate(self._language)

    def pgn_text(self):
        return self._editor.toPlainText().strip()

    def set_pgn(self, text):
        self._editor.setPlainText(text)

    def show_moves(self, pgn_text):
        if self._move_list.set_moves(pgn_text):
            self._stack.setCurrentIndex(1)
            self.moves_shown.emit(pgn_text)
            return True
        return False

    def show_editor(self):
        self._stack.setCurrentIndex(0)

    def set_current_ply(self, ply):
        self._move_list.set_current_ply(ply)

    def clear(self):
        self._editor.clear()
        self._move_list.clear()
        self.show_editor()
        self.clear_requested.emit()

    def set_theme(self, theme):
        self._theme = theme
        self._move_list.set_theme(theme)
        self._apply_icons()

    def _apply_icons(self):
        for button, name in (
            (self._btn_open, "open"),
            (self._btn_image, "image"),
            (self._btn_clear, "trash"),
            (self._btn_stop, "stop"),
        ):
            button.setIcon(action_icon(self._theme, name))
            button.setIconSize(QSize(16, 16))
        self._btn_analyze.setIcon(action_icon(self._theme, "analyze", on_accent=True))
        self._btn_analyze.setIconSize(QSize(16, 16))

    def set_progress(self, percent):
        self._progress.setValue(percent)

    def set_accuracy(self, accuracy):
        if accuracy is None:
            self._accuracy_label.setVisible(False)
            return
        key = rating_key(accuracy)
        self._accuracy_label.setText(
            t(
                "label_performance",
                self._language,
                rating=t("rating_" + key, self._language),
                accuracy=accuracy,
            )
        )
        self._accuracy_label.setVisible(True)

    def set_status(self, text):
        self._status_label.setText(text)
        self._status_label.setVisible(bool(text))

    def set_busy(self, busy):
        self._btn_analyze.setEnabled(not busy)
        self._btn_stop.setEnabled(busy)
        self._btn_open.setEnabled(not busy)
        self._btn_image.setEnabled(not busy and IMAGE_RECOGNITION_ENABLED)
        self._editor.setReadOnly(busy)
        self._progress.setVisible(busy)

    def _on_analyze(self):
        text = self.pgn_text()
        if not text:
            self.set_status(t("empty_pgn_error", self._language))
            return
        self.analyze_requested.emit(text)

    def retranslate(self, language):
        self._language = language
        self._editor.setPlaceholderText(t("placeholder_pgn", language))
        self._btn_open.setText(t("btn_open_pgn", language))
        self._btn_image.setText(t("btn_image", language))
        self._btn_clear.setText(t("btn_clear_pgn", language))
        self._btn_analyze.setText(t("btn_analyze", language))
        self._btn_stop.setText(t("btn_stop", language))
        self.set_status("")
