from datetime import date, datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.rating import rating_key
from checkpause.data.profile import get_avg_accuracy
from checkpause.i18n import t

_NO_VALUE = "—"


def _group_message_key(date_text):
    try:
        played = datetime.strptime(str(date_text)[:10], "%Y-%m-%d").date()
    except ValueError:
        return "hist_group_older"
    days = (date.today() - played).days
    if days <= 0:
        return "hist_group_today"
    if days == 1:
        return "hist_group_yesterday"
    if days <= 7:
        return "hist_group_week"
    if days <= 30:
        return "hist_group_month"
    return "hist_group_older"


class _HistoryRow(QFrame):
    toggled = Signal()

    def __init__(self, record, index, language, parent=None):
        super().__init__(parent)
        self.index = index
        self._language = language
        self._selecting = False
        self.setObjectName("historyRow")
        self.setProperty("selected", False)
        self.setProperty("selecting", False)
        self.setCursor(Qt.CursorShape.ArrowCursor)

        self._check = QCheckBox()
        self._check.setObjectName("historyCheck")
        self._check.setAccessibleName(str(record.get("date", "")))
        self._check.setVisible(False)

        self._date_label = QLabel(str(record.get("date", "")))
        self._date_label.setObjectName("historyDate")
        self._date_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self._performance_label = QLabel(self._performance_text(record.get("accuracy")))
        self._performance_label.setObjectName("historyPerformance")
        self._performance_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 7, 10, 7)
        layout.setSpacing(8)
        layout.addWidget(self._check)
        layout.addWidget(self._date_label, 1)
        layout.addWidget(self._performance_label)

        self._check.toggled.connect(self._on_toggled)

    def _performance_text(self, accuracy):
        key = rating_key(accuracy)
        if key is None:
            return ""
        return f"{t('rating_' + key, self._language)} ({accuracy}%)"

    def is_checked(self):
        return self._check.isChecked()

    def set_checked(self, checked):
        self._check.setChecked(checked)

    def set_selecting(self, selecting):
        self._selecting = selecting
        self._check.setVisible(selecting)
        if not selecting:
            self._check.setChecked(False)
        self.setCursor(
            Qt.CursorShape.PointingHandCursor if selecting else Qt.CursorShape.ArrowCursor
        )
        self.setProperty("selecting", selecting)
        self._refresh_style()

    def _refresh_style(self):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def _on_toggled(self, checked):
        self.setProperty("selected", checked)
        self._refresh_style()
        self.toggled.emit()

    def mousePressEvent(self, event):
        if self._selecting and event.button() == Qt.MouseButton.LeftButton:
            self._check.toggle()
            event.accept()
            return
        super().mousePressEvent(event)


class StatsPage(QWidget):
    history_cleared = Signal()
    history_delete_requested = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._history = []
        self._history_rows = []
        self._selecting = False

        self._username_label = QLabel()
        self._username_label.setObjectName("mutedLabel")

        self._games_value = QLabel()
        self._avg_value = QLabel()
        self._latest_value = QLabel()
        cards = QHBoxLayout()
        cards.setSpacing(10)
        self._games_caption = self._build_card(cards, self._games_value)
        self._avg_caption = self._build_card(cards, self._avg_value)
        self._latest_caption = self._build_card(cards, self._latest_value)

        self._empty_label = QLabel()
        self._empty_label.setObjectName("mutedLabel")
        self._empty_label.setVisible(False)

        self._history_container = QWidget()
        self._history_layout = QVBoxLayout(self._history_container)
        self._history_layout.setContentsMargins(2, 0, 2, 2)
        self._history_layout.setSpacing(2)

        self._history_area = QScrollArea()
        self._history_area.setObjectName("historyScroll")
        self._history_area.setWidgetResizable(True)
        self._history_area.setFrameShape(QFrame.Shape.NoFrame)
        self._history_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._history_area.setWidget(self._history_container)

        self._select_button = QPushButton()
        self._select_button.clicked.connect(self._toggle_selection)

        self._delete_selected_button = QPushButton()
        self._delete_selected_button.setObjectName("dangerButton")
        self._delete_selected_button.setVisible(False)
        self._delete_selected_button.clicked.connect(self._emit_delete_selected)

        self._clear_button = QPushButton()
        self._clear_button.setEnabled(False)
        self._clear_button.clicked.connect(self.history_cleared.emit)
        footer = QHBoxLayout()
        footer.addWidget(self._select_button)
        footer.addStretch(1)
        footer.addWidget(self._delete_selected_button)
        footer.addWidget(self._clear_button)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self._username_label)
        layout.addLayout(cards)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._history_area, 1)
        layout.addLayout(footer)

        self.retranslate(self._language)

    def _build_card(self, row, value_label):
        card = QFrame()
        card.setObjectName("statCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(2)
        value_label.setObjectName("statValue")
        caption = QLabel()
        caption.setObjectName("statCaption")
        card_layout.addWidget(value_label)
        card_layout.addWidget(caption)
        row.addWidget(card, 1)
        return caption

    def refresh(self, profile):
        self._selecting = False
        self._clear_rows()
        if not profile:
            self._history = []
            self._set_values(None, None, None)
            self._empty_label.setVisible(True)
            self._history_area.setVisible(False)
            self._sync_selection_mode()
            return

        self._username_label.setText(
            t("stat_username", self._language, username=profile.get("username", ""))
        )
        self._set_values(
            profile.get("total_games", 0),
            get_avg_accuracy(profile),
            profile.get("latest_accuracy"),
        )

        history = profile.get("history", [])
        self._history = list(history)
        self._build_rows(history)
        self._empty_label.setVisible(not history)
        self._history_area.setVisible(bool(history))
        self._sync_selection_mode()
        self._history_area.verticalScrollBar().setValue(0)

    def _build_rows(self, history):
        last_group = None
        for row, record in enumerate(reversed(history)):
            history_index = len(history) - 1 - row
            group = _group_message_key(record.get("date", ""))
            if group != last_group:
                self._history_layout.addWidget(self._group_label(group))
                last_group = group
            widget = _HistoryRow(record, history_index, self._language)
            widget.toggled.connect(self._update_delete_selected)
            self._history_rows.append(widget)
            self._history_layout.addWidget(widget)
        self._history_layout.addStretch(1)

    def _group_label(self, key):
        label = QLabel(t(key, self._language))
        label.setObjectName("historyGroupLabel")
        return label

    def _clear_rows(self):
        self._history_rows = []
        while self._history_layout.count():
            item = self._history_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _selected_history_indices(self):
        return [row.index for row in self._history_rows if row.is_checked()]

    def _toggle_selection(self):
        self._selecting = not self._selecting
        self._sync_selection_mode()

    def _sync_selection_mode(self):
        has_history = bool(self._history_rows)
        for row in self._history_rows:
            row.set_selecting(self._selecting)
        self._select_button.setText(
            t("btn_no" if self._selecting else "stat_select", self._language)
        )
        self._select_button.setEnabled(has_history)
        self._delete_selected_button.setText(t("stat_delete_selected", self._language))
        self._delete_selected_button.setVisible(self._selecting)
        self._delete_selected_button.setEnabled(
            bool(self._selected_history_indices()) if self._selecting else False
        )
        self._clear_button.setText(t("stat_clear_history", self._language))
        self._clear_button.setVisible(not self._selecting)
        self._clear_button.setEnabled(has_history)

    def _update_delete_selected(self):
        self._delete_selected_button.setEnabled(
            self._selecting and bool(self._selected_history_indices())
        )

    def _emit_delete_selected(self):
        if not self._selecting:
            return
        indices = self._selected_history_indices()
        if indices:
            self.history_delete_requested.emit(indices)

    def _set_values(self, total, avg, latest):
        self._games_value.setText(_NO_VALUE if total is None else str(total))
        self._avg_value.setText(_NO_VALUE if avg is None else f"{avg:.1f}%")
        self._latest_value.setText(_NO_VALUE if latest is None else f"{latest}%")

    def retranslate(self, language):
        self._language = language
        self._games_caption.setText(t("stat_games_caption", language))
        self._avg_caption.setText(t("stat_avg_caption", language))
        self._latest_caption.setText(t("stat_latest_caption", language))
        self._empty_label.setText(t("stat_no_data", language))
        self._sync_selection_mode()
