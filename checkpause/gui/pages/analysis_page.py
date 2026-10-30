from PySide6.QtCore import QSize, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QButtonGroup,
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
from checkpause.gui.theme import LIGHT, danger_color
from checkpause.gui.widgets.move_list import MoveListWidget
from checkpause.i18n import t

REVIEW_SIDES = ("all", "white", "black")


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
        self._busy = False

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

        self._btn_open = self._tool_button("open")
        self._btn_open.clicked.connect(self.open_file_requested.emit)
        self._btn_image = self._tool_button("image")
        self._btn_image.setEnabled(IMAGE_RECOGNITION_ENABLED)
        self._btn_image.clicked.connect(self.image_requested.emit)
        self._btn_clear = self._tool_button("trash")
        self._btn_clear.clicked.connect(self.clear)

        tools = QWidget()
        tools.setObjectName("analysisTools")
        tools_row = QHBoxLayout(tools)
        tools_row.setContentsMargins(0, 0, 0, 0)
        tools_row.setSpacing(4)
        for button in (self._btn_open, self._btn_image, self._btn_clear):
            tools_row.addWidget(button)
        tools_row.addStretch(1)

        self._btn_analyze = QPushButton()
        self._btn_analyze.setObjectName("primaryButton")
        self._btn_analyze.clicked.connect(self._on_primary_action)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedWidth(110)
        self._progress.setVisible(False)

        self._status_label = QLabel()
        self._status_label.setObjectName("mutedLabel")
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)

        self._accuracy_label = QLabel()
        self._accuracy_label.setObjectName("accuracyLabel")
        self._accuracy_label.setWordWrap(True)
        self._accuracy_label.setVisible(False)
        self._classification_label = QLabel()
        self._classification_label.setObjectName("mutedLabel")
        self._classification_label.setWordWrap(True)
        self._classification_label.setVisible(False)

        self._side_label = QLabel()
        self._side_label.setObjectName("mutedLabel")
        self._review_group = QButtonGroup(self)
        self._review_group.setExclusive(True)
        self._review_buttons = {}
        review_segments = QWidget()
        review_segments.setObjectName("segmentedControl")
        review_layout = QHBoxLayout(review_segments)
        review_layout.setContentsMargins(3, 3, 3, 3)
        review_layout.setSpacing(3)
        for index, side in enumerate(REVIEW_SIDES):
            button = QPushButton()
            button.setCheckable(True)
            button.setObjectName("segmentButton")
            self._review_group.addButton(button, index)
            review_layout.addWidget(button)
            self._review_buttons[side] = button
        self._review_buttons["all"].setChecked(True)
        self._review_group.idClicked.connect(self._on_review_side_clicked)

        self._review_filter = QWidget()
        filter_row = QHBoxLayout(self._review_filter)
        filter_row.setContentsMargins(0, 0, 0, 0)
        filter_row.setSpacing(8)
        filter_row.addWidget(self._side_label)
        filter_row.addWidget(review_segments)
        filter_row.addStretch(1)
        self._review_filter.setVisible(False)

        self._summary_card = QFrame()
        self._summary_card.setObjectName("summaryCard")
        summary_layout = QVBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(14, 12, 14, 12)
        summary_layout.setSpacing(6)
        summary_layout.addWidget(self._accuracy_label)
        summary_layout.addWidget(self._review_filter)
        summary_layout.addWidget(self._classification_label)
        self._summary_card.setVisible(False)

        action_row = QHBoxLayout()
        action_row.setContentsMargins(2, 0, 2, 0)
        action_row.setSpacing(10)
        action_row.addWidget(self._status_label)
        action_row.addStretch(1)
        action_row.addWidget(self._progress)
        action_row.addWidget(self._btn_analyze)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.addWidget(tools)
        layout.addWidget(self._stack, 1)
        layout.addWidget(self._summary_card)
        layout.addLayout(action_row)

        self._apply_icons()
        self.retranslate(self._language)

    def _tool_button(self, icon_name):
        button = QPushButton()
        button.setIcon(action_icon(self._theme, icon_name))
        button.setIconSize(QSize(16, 16))
        return button

    def pgn_text(self):
        return self._editor.toPlainText().strip()

    def set_pgn(self, text):
        self._editor.setPlainText(text)

    def show_moves(self, pgn_text):
        if self._move_list.set_moves(pgn_text):
            self._stack.setCurrentIndex(1)
            self.moves_shown.emit(pgn_text)
            return True
        self._move_list.clear()
        self.show_editor()
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
        ):
            button.setIcon(action_icon(self._theme, name))
            button.setIconSize(QSize(16, 16))
        self._sync_primary_action()

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
        self._sync_primary_action()

    def _refresh_review(self):
        self._review_filter.setVisible(bool(self._annotated))
        self.set_move_labels(labels_for(self._annotated, self._review_side))
        if not self._annotated:
            self.set_classification(None)
            return
        self.set_classification(summary_for(self._annotated, self._review_side))

    def _on_review_side_clicked(self, index):
        self._review_side = REVIEW_SIDES[index]
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

    def _sync_summary(self):
        widgets = (self._accuracy_label, self._classification_label)
        self._summary_card.setVisible(any(not widget.isHidden() for widget in widgets))

    def set_busy(self, busy):
        self._busy = busy
        self._editor.setReadOnly(busy)
        self._btn_open.setEnabled(not busy)
        self._btn_image.setEnabled(not busy and IMAGE_RECOGNITION_ENABLED)
        self._btn_clear.setEnabled(not busy)
        self._sync_primary_action()
        self._progress.setVisible(busy)
        if not busy:
            self._progress.setValue(0)

    def _on_primary_action(self):
        if self._busy:
            self.stop_requested.emit()
            return
        self._on_analyze()

    def _on_analyze(self):
        text = self.pgn_text()
        if not text:
            self.set_status(t("empty_pgn_error", self._language))
            return
        self.analyze_requested.emit(text)

    def _sync_primary_action(self):
        if self._busy:
            key = "btn_stop"
        elif self._annotated:
            key = "btn_reanalyze"
        else:
            key = "btn_analyze"
        self._btn_analyze.setText(t(key, self._language))
        self._btn_analyze.setObjectName("dangerButton" if self._busy else "primaryButton")
        if self._busy:
            icon = action_icon(self._theme, "stop", color=danger_color(self._theme))
        else:
            icon = action_icon(self._theme, "analyze", on_accent=True)
        self._btn_analyze.setIcon(icon)
        self._btn_analyze.setIconSize(QSize(16, 16))
        self._btn_analyze.style().unpolish(self._btn_analyze)
        self._btn_analyze.style().polish(self._btn_analyze)
        self._fit_action_buttons()

    def retranslate(self, language):
        self._language = language
        self._editor.setPlaceholderText(t("placeholder_pgn", language))
        for button, name_key in (
            (self._btn_open, "btn_open_pgn"),
            (self._btn_image, "btn_image"),
            (self._btn_clear, "btn_clear_pgn"),
        ):
            button.setText(t(name_key, language))
            button.setAccessibleName(t(name_key, language))
        self._side_label.setText(t("review_side_label", language))
        for side in REVIEW_SIDES:
            self._review_buttons[side].setText(t("review_side_" + side, language))
        self._sync_primary_action()
        self.set_status("")

    def _fit_action_buttons(self):
        current = self._btn_analyze.text()
        widest = 0
        for key in ("btn_analyze", "btn_reanalyze", "btn_stop"):
            self._btn_analyze.setText(t(key, self._language))
            self._btn_analyze.ensurePolished()
            widest = max(widest, self._btn_analyze.sizeHint().width())
        self._btn_analyze.setText(current)
        self._btn_analyze.setMinimumWidth(widest + 4)
