from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.rating import rating_key
from checkpause.data.profile import get_avg_accuracy
from checkpause.i18n import t


class StatsPage(QWidget):
    COLUMNS = ("hist_date", "hist_performance")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"

        self._username_label = QLabel()
        self._total_label = QLabel()
        self._avg_label = QLabel()
        self._latest_label = QLabel()
        self._empty_label = QLabel()
        self._empty_label.setVisible(False)

        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout = QVBoxLayout(self)
        layout.addWidget(self._username_label)
        layout.addWidget(self._total_label)
        layout.addWidget(self._avg_label)
        layout.addWidget(self._latest_label)
        layout.addWidget(self._empty_label)
        layout.addWidget(self._table, 1)

        self.retranslate(self._language)

    def refresh(self, profile):
        if not profile:
            self._table.setRowCount(0)
            self._empty_label.setVisible(True)
            return

        self._username_label.setText(
            t("stat_username", self._language, username=profile.get("username", ""))
        )
        self._total_label.setText(
            t("stat_total_games", self._language, total=profile.get("total_games", 0))
        )

        avg = get_avg_accuracy(profile)
        self._avg_label.setText(
            t("stat_avg_accuracy", self._language, accuracy=avg)
            if avg is not None
            else t("stat_no_data", self._language)
        )

        latest = profile.get("latest_accuracy")
        self._latest_label.setText(
            t("stat_latest_accuracy", self._language, accuracy=latest)
            if latest is not None
            else ""
        )

        history = profile.get("history", [])
        self._table.setRowCount(len(history))
        for row, record in enumerate(reversed(history)):
            date_item = QTableWidgetItem(str(record.get("date", "")))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rating_item = QTableWidgetItem(
                self._rating_text(record.get("accuracy"))
            )
            rating_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 0, date_item)
            self._table.setItem(row, 1, rating_item)
        self._empty_label.setVisible(not history)

    def _rating_text(self, accuracy):
        key = rating_key(accuracy)
        if key is None:
            return ""
        return f"{t('rating_' + key, self._language)} ({accuracy}%)"

    def retranslate(self, language):
        self._language = language
        self._table.setHorizontalHeaderLabels(
            [t(key, language) for key in self.COLUMNS]
        )
        self._table.horizontalHeader().setDefaultAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
