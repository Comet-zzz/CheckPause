from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.rating import rating_key
from checkpause.data.profile import get_avg_accuracy
from checkpause.i18n import t

_NO_VALUE = "—"


class StatsPage(QWidget):
    COLUMNS = ("hist_date", "hist_performance")

    history_cleared = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"

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

        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setHighlightSections(False)

        self._clear_button = QPushButton()
        self._clear_button.setEnabled(False)
        self._clear_button.clicked.connect(self.history_cleared.emit)
        footer = QHBoxLayout()
        footer.addStretch(1)
        footer.addWidget(self._clear_button)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self._username_label)
        layout.addLayout(cards)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)
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
        if not profile:
            self._set_values(None, None, None)
            self._table.setRowCount(0)
            self._empty_label.setVisible(True)
            self._clear_button.setEnabled(False)
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
        self._table.setRowCount(len(history))
        for row, record in enumerate(reversed(history)):
            date_item = QTableWidgetItem(str(record.get("date", "")))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rating_item = QTableWidgetItem(self._rating_text(record.get("accuracy")))
            rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, date_item)
            self._table.setItem(row, 1, rating_item)
        self._empty_label.setVisible(not history)
        self._clear_button.setEnabled(bool(history))

    def _set_values(self, total, avg, latest):
        self._games_value.setText(_NO_VALUE if total is None else str(total))
        self._avg_value.setText(_NO_VALUE if avg is None else f"{avg:.1f}%")
        self._latest_value.setText(_NO_VALUE if latest is None else f"{latest}%")

    def _rating_text(self, accuracy):
        key = rating_key(accuracy)
        if key is None:
            return ""
        return f"{t('rating_' + key, self._language)} ({accuracy}%)"

    def retranslate(self, language):
        self._language = language
        self._games_caption.setText(t("stat_games_caption", language))
        self._avg_caption.setText(t("stat_avg_caption", language))
        self._latest_caption.setText(t("stat_latest_caption", language))
        self._empty_label.setText(t("stat_no_data", language))
        self._table.setHorizontalHeaderLabels([t(key, language) for key in self.COLUMNS])
        self._table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self._clear_button.setText(t("stat_clear_history", language))
