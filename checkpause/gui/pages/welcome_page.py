from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from checkpause.data.settings import DEFAULT_SERVER_URL, MODE_CLOUD, MODE_LOCAL
from checkpause.gui.icons import app_logo
from checkpause.gui.workers import AccountWorker
from checkpause.i18n import t

CARD_WIDTH = 400


class WelcomePage(QWidget):
    """First launch: sign in to the cloud account, or step in offline.

    The cloud account is the only identity the app has, so this is where it is
    created or restored. A user with no network can continue as a local profile
    named ``player`` and sign in later from the settings - the account is the
    same either way, only what is available changes.

    The page does no persistence itself: it reports what was chosen and the
    window writes the profile and the account.
    """

    started = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("welcomePage")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._language = "zh-CN"
        self._worker = None

        self._logo = QLabel()
        self._logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo = app_logo(64)
        if logo is not None:
            self._logo.setPixmap(logo)

        self._title = QLabel()
        self._title.setObjectName("welcomeTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitle = QLabel()
        self._subtitle.setObjectName("welcomeSubtitle")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._username_label = QLabel()
        self._username_label.setObjectName("welcomeFieldLabel")
        self._password_label = QLabel()
        self._password_label.setObjectName("welcomeFieldLabel")
        self._language_label = QLabel()
        self._language_label.setObjectName("welcomeFieldLabel")

        self._username = QLineEdit()
        self._password = QLineEdit()
        self._password.setEchoMode(QLineEdit.EchoMode.Password)
        self._show_password = QCheckBox()
        self._show_password.toggled.connect(
            lambda checked: self._password.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )

        self._language_combo = QComboBox()
        self._language_combo.addItem(t("lang_zh", self._language), "zh-CN")
        self._language_combo.addItem(t("lang_en", self._language), "en-US")
        self._language_combo.currentIndexChanged.connect(
            lambda _index: self.retranslate(self._language_combo.currentData())
        )

        self._status = QLabel()
        self._status.setWordWrap(True)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status.setVisible(False)

        self._register = QPushButton()
        self._register.setObjectName("welcomePrimary")
        self._register.setDefault(True)
        self._register.clicked.connect(lambda: self._submit("register"))
        self._sign_in = QPushButton()
        self._sign_in.setObjectName("welcomeSecondary")
        self._sign_in.clicked.connect(lambda: self._submit("sign_in"))
        self._offline = QPushButton()
        self._offline.setObjectName("welcomeSecondary")
        self._offline.clicked.connect(self._go_offline)

        card = QFrame()
        card.setObjectName("welcomeCard")
        card.setFixedWidth(CARD_WIDTH)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(34, 32, 34, 30)
        card_layout.setSpacing(6)
        card_layout.addWidget(self._logo)
        card_layout.addSpacing(4)
        card_layout.addWidget(self._title)
        card_layout.addWidget(self._subtitle)
        card_layout.addSpacing(18)
        card_layout.addWidget(self._username_label)
        card_layout.addWidget(self._username)
        card_layout.addSpacing(6)
        card_layout.addWidget(self._password_label)
        card_layout.addWidget(self._password)
        card_layout.addWidget(self._show_password)
        card_layout.addSpacing(6)
        card_layout.addWidget(self._language_label)
        card_layout.addWidget(self._language_combo)
        card_layout.addSpacing(4)
        card_layout.addWidget(self._status)
        card_layout.addSpacing(10)

        self._register.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        card_layout.addWidget(self._register)

        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        for button in (self._sign_in, self._offline):
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            buttons.addWidget(button)
        card_layout.addLayout(buttons)

        row = QHBoxLayout()
        row.addStretch(1)
        row.addWidget(card)
        row.addStretch(1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addStretch(1)
        layout.addLayout(row)
        layout.addStretch(1)

        self.retranslate(self._language)

    def prepare(self, language="zh-CN"):
        self._language = language
        self.retranslate(language)
        self._username.clear()
        self._password.clear()
        self._show_password.setChecked(False)
        self._language_combo.setCurrentIndex(1 if language == "en-US" else 0)

    def _submit(self, action):
        if self._worker is not None and self._worker.isRunning():
            return
        username = self._username.text().strip()
        password = self._password.text()
        if not username:
            self._set_status(t("cloud_account_username_empty", self._language), error=True)
            return
        if not password:
            self._set_status(t("cloud_account_password_empty", self._language), error=True)
            return
        self._set_status(t("cloud_account_working", self._language))
        self._set_busy(True)
        worker = AccountWorker(
            action,
            DEFAULT_SERVER_URL,
            self._language,
            username=username,
            password=password,
            parent=self,
        )
        worker.done.connect(self._on_done)
        worker.failed.connect(self._on_failed)
        worker.finished.connect(self._on_finished)
        self._worker = worker
        worker.start()

    def _on_done(self, result):
        account = result.get("account") or {}
        self.started.emit(
            {
                "language": self._language_combo.currentData(),
                "username": account.get("username", ""),
                "mode": MODE_CLOUD,
                "account": {
                    "username": account.get("username", ""),
                    "token": result.get("token", ""),
                    "balance": account.get("balance"),
                },
            }
        )

    def _on_failed(self, message):
        self._set_busy(False)
        self._set_status(message, error=True)

    def _on_finished(self):
        worker = self._worker
        self._worker = None
        if worker is not None:
            worker.deleteLater()

    def _go_offline(self):
        if self._worker is not None and self._worker.isRunning():
            return
        self.started.emit(
            {
                "language": self._language_combo.currentData(),
                "username": "player",
                "mode": MODE_LOCAL,
                "account": None,
            }
        )

    def _set_status(self, text, error=False):
        self._status.setObjectName("welcomeStatus" if error else "welcomeSubtitle")
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)
        self._status.setText(text)
        self._status.setVisible(bool(text))

    def _set_busy(self, value):
        for widget in (
            self._username,
            self._password,
            self._show_password,
            self._sign_in,
            self._register,
            self._offline,
            self._language_combo,
        ):
            widget.setEnabled(not value)

    def retranslate(self, language):
        self._language = language
        self._title.setText(t("welcome_title", language))
        self._subtitle.setText(t("welcome_intro", language))
        self._username_label.setText(t("cloud_account_username", language))
        self._password_label.setText(t("cloud_account_password", language))
        self._language_label.setText(t("label_language", language))
        self._show_password.setText(t("cloud_account_show_password", language))
        self._sign_in.setText(t("cloud_account_sign_in", language))
        self._register.setText(t("cloud_account_register", language))
        self._offline.setText(t("welcome_offline", language))
        self._language_combo.setItemText(0, t("lang_zh", language))
        self._language_combo.setItemText(1, t("lang_en", language))
