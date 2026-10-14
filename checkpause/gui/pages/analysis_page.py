from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
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
from checkpause.core.review import format_summary, labels_for, summary_for
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
        self._annotated = []
        self._review_side = "all"

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
        self._classification_label = QLabel()
        self._classification_label.setObjectName("mutedLabel")
        self._classification_label.setWordWrap(True)
        self._classification_label.setVisible(False)
        self._side_label = QLabel()
        self._side_label.setObjectName("mutedLabel")
        self._side_combo = QComboBox()
        self._side_combo.addItem("", "all")
        self._side_combo.addItem("", "white")
        self._side_combo.addItem("", "black")
        self._side_combo.currentIndexChanged.connect(self._on_review_side_changed)
        review_row = QHBoxLayout()
        review_row.setSpacing(6)
        review_row.addWidget(self._side_label)
        review_row.addWidget(self._side_combo)
        review_row.addStretch(1)
        self._status_label = QLabel()
        self._status_label.setObjectName("mutedLabel")
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)

        action_bar = QFrame()
        action_bar.setObjectName("actionBar")
        action_layout = QVBoxLayout(action_bar)
        action_layout.setContentsMargins(12, 10, 12, 10)
        action_layout.setSpacing(8)
        action_layout.addLayout(review_row)
        action_layout.addLayout(button_row)

        self._summary_card = QFrame()
        self._summary_card.setObjectName("summaryCard")
        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setSpacing(4)
        summary_layout.addWidget(self._accuracy_label)
        summary_layout.addWidget(self._classification_label)
        summary_layout.addWidget(self._status_label)
        self._summary_card.setVisible(False)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self._stack, 1)
        layout.addWidget(self._progress)
        layout.addWidget(action_bar)
        layout.addWidget(self._summary_card)

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
        self.set_review([])
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
            self._sync_summary()
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
        self._sync_summary()

    def set_review(self, annotated):
        """Show the review labels and stats, honouring the current side filter."""
        self._annotated = list(annotated or [])
        self._refresh_review()

    def _refresh_review(self):
        self.set_move_labels(labels_for(self._annotated, self._review_side))
        if not self._annotated:
            self.set_classification(None)
            return
        self.set_classification(summary_for(self._annotated, self._review_side))

    def _on_review_side_changed(self, index):
        self._review_side = self._side_combo.itemData(index) or "all"
        self._refresh_review()

    def set_move_labels(self, labels):
        self._move_list.set_labels(labels)

    def set_classification(self, summary):
        text = format_summary(summary) if summary else ""
        self._classification_label.setText(text)
        self._classification_label.setVisible(bool(text))
        self._sync_summary()

    def set_status(self, text):
        self._status_label.setText(text)
        self._status_label.setVisible(bool(text))
        self._sync_summary()

    def _sync_summary(self):
        widgets = (self._accuracy_label, self._classification_label, self._status_label)
        self._summary_card.setVisible(any(not widget.isHidden() for widget in widgets))

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
        self._side_label.setText(t("review_side_label", language))
        self._side_combo.blockSignals(True)
        for index, key in enumerate(("review_side_all", "review_side_white", "review_side_black")):
            self._side_combo.setItemText(index, t(key, language))
        self._side_combo.blockSignals(False)
        self.set_status("")
