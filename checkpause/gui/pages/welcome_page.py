from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from checkpause.i18n import t


class WelcomePage(QWidget):
    started = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"

        self._title = QLabel()
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = self._title.font()
        title_font.setPointSize(title_font.pointSize() + 6)
        title_font.setBold(True)
        self._title.setFont(title_font)

        self._intro = QLabel()
        self._intro.setWordWrap(False)
        self._intro.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._username_label = QLabel()
        self._username = QLineEdit()

        self._language_label = QLabel()
        self._language_combo = QComboBox()
        self._language_combo.addItem(t("lang_zh", self._language), "zh-CN")
        self._language_combo.addItem(t("lang_en", self._language), "en-US")

        self._start = QPushButton()
        self._start.clicked.connect(self._on_start)

        form = QFormLayout()
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)
        form.addRow(self._username_label, self._username)
        form.addRow(self._language_label, self._language_combo)

        content = QWidget()
        content.setMaximumWidth(440)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(10)
        content_layout.addStretch(1)
        content_layout.addWidget(self._title)
        content_layout.addWidget(self._intro)
        content_layout.addSpacing(14)
        content_layout.addLayout(form)
        content_layout.addSpacing(6)
        content_layout.addWidget(self._start)
        content_layout.addStretch(1)

        layout = QHBoxLayout(self)
        layout.addStretch(1)
        layout.addWidget(content)
        layout.addStretch(1)

        self.retranslate(self._language)

    def prepare(self, language="zh-CN", username=""):
        self._language = language
        self.retranslate(language)
        self._username.setText(username)
        self._language_combo.setCurrentIndex(1 if language == "en-US" else 0)

    def _on_start(self):
        username = self._username.text().strip()
        if not username:
            QMessageBox.warning(
                self,
                t("app_title", self._language),
                t("username_required", self._language),
            )
            return
        self.started.emit(username, self._language_combo.currentData())

    def retranslate(self, language):
        self._language = language
        self._title.setText(t("welcome_title", language))
        self._intro.setText(t("welcome_intro", language))
        self._username_label.setText(t("label_username", language))
        self._language_label.setText(t("label_language", language))
        self._start.setText(t("btn_start", language))
        self._language_combo.setItemText(0, t("lang_zh", language))
        self._language_combo.setItemText(1, t("lang_en", language))
