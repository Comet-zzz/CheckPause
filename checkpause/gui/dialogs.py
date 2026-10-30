from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from checkpause import (
    APP_VERSION,
    AUTHOR,
    COPYRIGHT_YEAR,
    GITHUB_URL,
    WEBSITE_URL,
)
from checkpause.data.settings import (
    DEFAULT_SERVER_URL,
    MODE_LOCAL,
    get_api_key,
    get_base_url,
    get_model,
)
from checkpause.gui.icons import action_icon
from checkpause.gui.workers import AccountWorker, UpdateDownloadWorker
from checkpause.i18n import t

# How often to ask whether a payment has landed, and when to stop asking.
# Three seconds feels immediate without hammering the server; ten minutes is
# longer than the cashier holds an order anyway.
POLL_INTERVAL_MS = 3000
POLL_LIMIT = 200


def choose_language_dialog(parent, current="zh-CN"):
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("menu_language", current))

    combo = QComboBox()
    combo.addItem(t("lang_zh", current), "zh-CN")
    combo.addItem(t("lang_en", current), "en-US")
    if current == "en-US":
        combo.setCurrentIndex(1)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)

    layout = QVBoxLayout(dialog)
    layout.addWidget(QLabel(t("label_language", current)))
    layout.addWidget(combo)
    layout.addWidget(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return combo.currentData()
    return None


def api_settings_dialog(parent, language):
    """The bring-your-own-key path.

    The cloud account is the ordinary way in and has its own menu entry; this
    dialog is the advanced option for a user who has their own key. It asks for
    the key, the endpoint and the model, all of them the user's to choose: the
    app ships no provider and suggests no address. Saving is also choosing to
    run against what was entered, which is why the result carries the local
    mode.
    """
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("api_settings_title", language))
    dialog.setMinimumWidth(520)

    key_field = QLineEdit()
    key_field.setEchoMode(QLineEdit.EchoMode.Password)
    key_field.setPlaceholderText(t("api_key_placeholder", language))
    key_field.setText(get_api_key())

    show_toggle = QCheckBox(t("api_key_show", language))
    show_toggle.toggled.connect(
        lambda checked: key_field.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
    )

    base_field = QLineEdit()
    base_field.setText(get_base_url())

    model_field = QLineEdit()
    model_field.setText(get_model())

    form = QFormLayout()
    form.setHorizontalSpacing(16)
    form.setVerticalSpacing(10)
    form.addRow(t("api_key_label", language), key_field)
    form.addRow("", show_toggle)
    form.addRow(t("api_base_url_label", language), base_field)
    form.addRow(t("api_model_label", language), model_field)

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
    ok_button.setText(t("btn_yes", language))
    ok_button.setObjectName("primaryButton")
    buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_no", language))

    def on_accept():
        if not key_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("api_settings_title", language),
                t("api_key_empty", language),
            )
            return
        if not base_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("api_settings_title", language),
                t("api_base_url_empty", language),
            )
            return
        if not model_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("api_settings_title", language),
                t("api_model_empty", language),
            )
            return
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)

    layout = QVBoxLayout(dialog)
    layout.addLayout(form)
    layout.addWidget(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {
            "mode": MODE_LOCAL,
            "api_key": key_field.text().strip(),
            "base_url": base_field.text().strip(),
            "model": model_field.text().strip(),
        }
    return None


def cloud_account_dialog(parent, language, config=None):
    """Sign in, register, or just look at the balance.

    Returns the account to store when something changed, otherwise None. Only
    the token is ever handed back: the password is used for the one request
    that needs it and is then dropped.
    """
    config = config or {}
    server_url = (config.get("server_url") or "").strip() or DEFAULT_SERVER_URL
    account = dict(config.get("account") or {})
    changed = {"value": False, "action": ""}
    busy = {"worker": None}

    dialog = QDialog(parent)
    dialog.setWindowTitle(t("cloud_account_title", language))
    dialog.setMinimumWidth(500)

    hint = QLabel(t("cloud_account_hint", language))
    hint.setWordWrap(True)

    server_field = QLineEdit(server_url)
    server_field.setPlaceholderText("http://...")

    username_field = QLineEdit(account.get("username", ""))
    password_field = QLineEdit()
    password_field.setEchoMode(QLineEdit.EchoMode.Password)

    show_toggle = QCheckBox(t("cloud_account_show_password", language))
    show_toggle.toggled.connect(
        lambda checked: password_field.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
    )

    status = QLabel()
    status.setWordWrap(True)

    sign_in_button = QPushButton(t("cloud_account_sign_in", language))
    sign_in_button.setObjectName("primaryButton")
    register_button = QPushButton(t("cloud_account_register", language))
    rename_button = QPushButton(t("cloud_account_rename", language))
    refresh_button = QPushButton(t("cloud_account_refresh", language))
    sign_out_button = QPushButton(t("cloud_account_sign_out", language))
    close_button = QPushButton(t("cloud_account_close", language))

    # Buying credits. The server owns the prices; this only picks one of the
    # packs it offers and then hands the browser over to the payment page.
    pack_combo = QComboBox()
    buy_button = QPushButton(t("cloud_topup_buy", language))
    buy_button.setObjectName("primaryButton")
    topup_label = QLabel(t("cloud_topup_label", language))
    topup_status = QLabel()
    topup_status.setWordWrap(True)

    form = QFormLayout()
    form.setHorizontalSpacing(16)
    form.setVerticalSpacing(10)
    form.addRow(t("cloud_account_server", language), server_field)
    form.addRow(t("cloud_account_username", language), username_field)
    form.addRow(t("cloud_account_password", language), password_field)
    form.addRow("", show_toggle)

    row = QHBoxLayout()
    for button in (
        sign_in_button,
        register_button,
        rename_button,
        refresh_button,
        sign_out_button,
    ):
        row.addWidget(button)
    row.addStretch(1)
    row.addWidget(close_button)

    topup_row = QHBoxLayout()
    topup_row.addWidget(topup_label)
    topup_row.addWidget(pack_combo, 1)
    topup_row.addWidget(buy_button)

    layout = QVBoxLayout(dialog)
    layout.addWidget(hint)
    layout.addLayout(form)
    layout.addWidget(status)
    layout.addLayout(topup_row)
    layout.addWidget(topup_status)
    layout.addLayout(row)

    credentials = (
        username_field,
        password_field,
        show_toggle,
        sign_in_button,
        register_button,
    )
    # A hidden input still leaves its label behind, which reads as a bug, so the
    # labels move with their fields.
    credential_labels = [(field, form.labelForField(field)) for field in credentials]
    session_buttons = (rename_button, refresh_button, sign_out_button)
    topup_widgets = (topup_label, pack_combo, buy_button, topup_status)
    everything = credentials + session_buttons + topup_widgets + (close_button, server_field)

    def signed_in():
        return bool(account.get("token"))

    def show_status():
        if not signed_in():
            status.setText(t("cloud_account_not_signed_in", language))
            return
        balance = account.get("balance")
        lines = [
            t(
                "cloud_account_signed_in",
                language,
                username=account.get("username", ""),
            )
        ]
        if balance is None:
            lines.append(t("cloud_account_balance_unknown", language))
        else:
            lines.append(t("cloud_account_balance", language, balance=balance))
        status.setText("\n".join(lines))

    def refresh():
        logged_in = signed_in()
        for widget in credentials:
            widget.setVisible(not logged_in)
        for _field, label in credential_labels:
            if label is not None and label.text():
                label.setVisible(not logged_in)
        for widget in session_buttons + topup_widgets:
            widget.setVisible(logged_in)
        server_field.setEnabled(not logged_in)
        if not logged_in:
            username_field.setFocus()
        show_status()

    def set_busy(value):
        for widget in everything:
            widget.setEnabled(not value)
        if value:
            status.setText(t("cloud_account_working", language))
        else:
            refresh()

    def finish():
        busy["worker"] = None
        set_busy(False)

    def on_done(action, result):
        if action == "packs":
            pack_combo.clear()
            for pack in result.get("packs") or []:
                pack_combo.addItem(
                    t(
                        "cloud_topup_pack",
                        language,
                        yuan=pack.get("yuan", 0),
                        credits=pack.get("credits", 0),
                    ),
                    pack.get("yuan"),
                )
            finish()
            return

        if action == "open_order":
            order = result.get("order") or {}
            if order.get("pay_url"):
                topup_status.setText(t("cloud_topup_waiting", language))
                # The checkout belongs in a browser - Alipay's form is built to
                # be submitted by one - so the desktop app opens a page rather
                # than trying to become a web application.
                QDesktopServices.openUrl(QUrl(order["pay_url"]))
                start_polling(order.get("order_id", ""))
            finish()
            return

        changed["value"] = True
        changed["action"] = action
        account.update(
            {
                "username": (result.get("account") or {}).get("username", ""),
                "token": result.get("token", ""),
                "balance": (result.get("account") or {}).get("balance"),
                "rename_fee": (result.get("account") or {}).get("rename_fee"),
            }
        )
        finish()
        if action in ("sign_in", "register"):
            QMessageBox.information(
                dialog,
                t("cloud_account_title", language),
                t(
                    "cloud_account_welcome",
                    language,
                    username=account["username"],
                ),
            )
        elif action == "rename":
            QMessageBox.information(
                dialog,
                t("cloud_rename_title", language),
                t("cloud_rename_done", language, username=account["username"]),
            )
        elif action == "sign_out":
            # A logout ends the dialog rather than leaving the user on a
            # just-emptied form; the window then returns to the sign-in screen.
            dialog.accept()
        elif action == "me" and pack_combo.count() == 0 and signed_in():
            # The prices are the server's to decide; ask once per dialog.
            run("packs")

    def on_failed(message):
        finish()
        QMessageBox.warning(dialog, t("cloud_account_title", language), message)

    def run(action, **values):
        if busy["worker"] is not None:
            return
        set_busy(True)
        # Parented to the window rather than the dialog: closing the dialog
        # must never destroy a thread that is still running.
        worker = AccountWorker(
            action,
            server_field.text().strip(),
            language,
            parent=parent if parent is not None else dialog,
            **values,
        )
        worker.done.connect(lambda result: on_done(action, result))
        worker.failed.connect(on_failed)
        worker.finished.connect(worker.deleteLater)
        busy["worker"] = worker
        worker.start()

    def sign_in():
        if not username_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("cloud_account_title", language),
                t("cloud_account_username_empty", language),
            )
            return
        if not password_field.text():
            QMessageBox.warning(
                dialog,
                t("cloud_account_title", language),
                t("cloud_account_password_empty", language),
            )
            return
        run(
            "sign_in",
            username=username_field.text().strip(),
            password=password_field.text(),
        )

    def register():
        if not username_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("cloud_account_title", language),
                t("cloud_account_username_empty", language),
            )
            return
        if not password_field.text():
            QMessageBox.warning(
                dialog,
                t("cloud_account_title", language),
                t("cloud_account_password_empty", language),
            )
            return
        run(
            "register",
            username=username_field.text().strip(),
            password=password_field.text(),
        )

    def sign_out():
        run("sign_out", token=account.get("token", ""))

    def rename():
        if not signed_in():
            return
        new_name, ok = QInputDialog.getText(
            dialog,
            t("cloud_rename_title", language),
            t("cloud_rename_prompt", language),
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        fee = account.get("rename_fee") or 0
        balance = account.get("balance")
        if balance is not None and balance < fee:
            QMessageBox.warning(
                dialog,
                t("cloud_rename_title", language),
                t("cloud_rename_no_credit", language, fee=fee),
            )
            return
        answer = QMessageBox.question(
            dialog,
            t("cloud_rename_title", language),
            t(
                "cloud_rename_fee",
                language,
                fee=fee,
                balance=balance if balance is not None else "?",
            ),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        run("rename", token=account.get("token", ""), username=new_name)

    def buy():
        if pack_combo.count() == 0:
            return
        run(
            "open_order",
            token=account.get("token", ""),
            yuan=pack_combo.currentData(),
        )

    # Waiting for a payment. Polling is what makes the purchase arrive at all:
    # the server either hears from Alipay or asks it, and nothing pushes the
    # news to a desktop client.
    poll = {"timer": None, "worker": None, "order_id": "", "tries": 0}

    def forget_poll_worker():
        poll["worker"] = None

    def stop_polling():
        if poll["timer"] is not None:
            poll["timer"].stop()
        poll["order_id"] = ""
        poll["tries"] = 0

    def on_poll_done(result):
        poll["worker"] = None
        order = result.get("order") or {}
        if order.get("status") != "paid":
            return
        stop_polling()
        changed["value"] = True
        changed["action"] = "order_status"
        account["balance"] = order.get("balance")
        topup_status.setText(t("cloud_topup_done", language, balance=order.get("balance")))
        show_status()

    def poll_once():
        if not poll["order_id"] or poll["worker"] is not None:
            return
        poll["tries"] += 1
        if poll["tries"] > POLL_LIMIT:
            stop_polling()
            topup_status.setText(t("cloud_topup_gave_up", language))
            return
        worker = AccountWorker(
            "order_status",
            server_field.text().strip(),
            language,
            token=account.get("token", ""),
            order_id=poll["order_id"],
            parent=parent if parent is not None else dialog,
        )
        worker.done.connect(on_poll_done)
        worker.failed.connect(lambda _message: None)
        worker.finished.connect(forget_poll_worker)
        worker.finished.connect(worker.deleteLater)
        poll["worker"] = worker
        worker.start()

    def start_polling(order_id):
        stop_polling()
        poll["order_id"] = order_id
        if poll["timer"] is None:
            poll["timer"] = QTimer(dialog)
            poll["timer"].setInterval(POLL_INTERVAL_MS)
            poll["timer"].timeout.connect(poll_once)
        poll["timer"].start()

    sign_in_button.clicked.connect(sign_in)
    register_button.clicked.connect(register)
    rename_button.clicked.connect(rename)
    refresh_button.clicked.connect(lambda: run("me", token=account.get("token", "")))
    sign_out_button.clicked.connect(sign_out)
    buy_button.clicked.connect(buy)
    close_button.clicked.connect(dialog.accept)

    refresh()
    if signed_in():
        # The cached number is only a hint; ask while the dialog is open.
        run("me", token=account.get("token", ""))

    dialog.exec()
    if not changed["value"]:
        return None
    return dict(account, action=changed["action"])


def confirm_dialog(parent, language, title_key, text_key):
    """A yes/no warning whose wording comes from two i18n keys."""
    box = QMessageBox(parent)
    box.setWindowTitle(t(title_key, language))
    box.setText(t(text_key, language))
    box.setIcon(QMessageBox.Icon.Warning)
    yes_button = box.addButton(t("btn_yes", language), QMessageBox.ButtonRole.AcceptRole)
    yes_button.setObjectName("dangerButton")
    box.addButton(t("btn_no", language), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is yes_button


def confirm_close_dialog(parent, language="zh-CN"):
    box = QMessageBox(parent)
    box.setWindowTitle(t("confirm_close_title", language))
    box.setText(t("confirm_close_text", language))
    box.setIcon(QMessageBox.Icon.Question)
    yes_button = box.addButton(t("btn_yes", language), QMessageBox.ButtonRole.AcceptRole)
    yes_button.setObjectName("primaryButton")
    box.addButton(t("btn_no", language), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is yes_button


def show_about(parent, language, theme="light"):
    dialog = QDialog(parent)
    dialog.setObjectName("aboutDialog")
    dialog.setWindowTitle(t("about_title", language))
    dialog.setMinimumWidth(480)

    card = QFrame()
    card.setObjectName("aboutCard")
    card_layout = QVBoxLayout(card)
    card_layout.setContentsMargins(24, 22, 24, 18)
    card_layout.setSpacing(12)

    title = QLabel(t("app_title", language))
    title.setObjectName("aboutTitle")

    version = QLabel(t("about_version", language, version=APP_VERSION))
    version.setObjectName("mutedLabel")

    heading = QVBoxLayout()
    heading.setContentsMargins(0, 0, 0, 0)
    heading.setSpacing(2)
    heading.addWidget(title)
    heading.addWidget(version)

    body = QLabel(t("about_text", language).split("\n", 1)[-1])
    body.setObjectName("aboutBody")
    body.setWordWrap(True)

    divider = QFrame()
    divider.setObjectName("aboutDivider")
    divider.setFixedHeight(1)

    author = QLabel(t("about_author", language, author=AUTHOR))
    author.setObjectName("mutedLabel")
    copyright_label = QLabel(t("about_copyright", language, year=COPYRIGHT_YEAR, author=AUTHOR))
    copyright_label.setObjectName("mutedLabel")

    meta = QHBoxLayout()
    meta.setContentsMargins(0, 0, 0, 0)
    meta.addWidget(author)
    meta.addStretch(1)
    meta.addWidget(copyright_label)

    github_logo = QLabel()
    github_logo.setPixmap(action_icon(theme, "github", size=16).pixmap(16, 16))
    github_logo.setFixedSize(16, 16)
    github_logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    github_name = GITHUB_URL.split("://", 1)[-1]
    link = QLabel(f'<a href="{GITHUB_URL}">{github_name}</a>')
    link.setOpenExternalLinks(True)
    link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

    github_row = QHBoxLayout()
    github_row.setContentsMargins(0, 0, 0, 0)
    github_row.setSpacing(8)
    github_row.addWidget(github_logo)
    github_row.addWidget(link)
    github_row.addStretch(1)

    web_logo = QLabel()
    web_logo.setPixmap(action_icon(theme, "globe", size=16).pixmap(16, 16))
    web_logo.setFixedSize(16, 16)
    web_logo.setAlignment(Qt.AlignmentFlag.AlignVCenter)

    website_name = WEBSITE_URL.split("://", 1)[-1]
    website = QLabel(f'<a href="{WEBSITE_URL}">{website_name}</a>')
    website.setOpenExternalLinks(True)
    website.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)

    website_row = QHBoxLayout()
    website_row.setContentsMargins(0, 0, 0, 0)
    website_row.setSpacing(8)
    website_row.addWidget(web_logo)
    website_row.addWidget(website)
    website_row.addStretch(1)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    close_button = buttons.button(QDialogButtonBox.StandardButton.Close)
    close_button.setText(t("about_close", language))
    close_button.setObjectName("primaryButton")
    close_button.setMinimumWidth(96)
    buttons.rejected.connect(dialog.reject)

    card_layout.addLayout(heading)
    card_layout.addWidget(body)
    card_layout.addWidget(divider)
    card_layout.addLayout(meta)
    card_layout.addLayout(github_row)
    card_layout.addLayout(website_row)
    card_layout.addWidget(buttons)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(14, 14, 14, 14)
    layout.addWidget(card)

    dialog.exec()


def show_update_dialog(parent, language, info, in_app=False):
    """Offer an update; return True when the user chooses to download it."""
    box = QMessageBox(parent)
    box.setWindowTitle(t("update_title", language))
    box.setIcon(QMessageBox.Icon.Information)
    box.setText(
        t(
            "update_available",
            language,
            version=info.version,
            current=APP_VERSION,
        )
    )
    if info.notes:
        box.setInformativeText(info.notes)

    download_key = "update_download_install" if in_app else "update_download"
    download = box.addButton(t(download_key, language), QMessageBox.ButtonRole.AcceptRole)
    download.setObjectName("primaryButton")
    box.addButton(t("update_later", language), QMessageBox.ButtonRole.RejectRole)
    box.exec()

    if box.clickedButton() is not download:
        return False
    if not in_app:
        QDesktopServices.openUrl(QUrl(info.url))
    return True


class _UpdateDownloadDialog(QDialog):
    def __init__(self, parent, language, info):
        super().__init__(parent)
        self._language = language
        self.installer_path = None
        self.error = None
        self.setWindowTitle(t("update_title", language))
        self.setMinimumWidth(360)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._status = QLabel(t("update_downloading", language))
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self._cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        self._cancel_button.setText(t("update_cancel", language))
        buttons.rejected.connect(self._cancel_download)

        layout = QVBoxLayout(self)
        layout.addWidget(self._status)
        layout.addWidget(self._progress)
        layout.addWidget(buttons)

        self._worker = UpdateDownloadWorker(info.url, info.version, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, downloaded, total):
        if total <= 0:
            return
        percent = min(100, downloaded * 100 // total)
        self._progress.setRange(0, 100)
        self._progress.setValue(percent)
        self._status.setText(t("update_downloading_progress", self._language, percent=percent))

    def _cancel_download(self):
        self._cancel_button.setEnabled(False)
        self._status.setText(t("update_canceling", self._language))
        self._worker.requestInterruption()

    def _on_finished(self):
        self.error = self._worker.error
        self.installer_path = self._worker.installer_path
        if self.installer_path is not None:
            self.accept()
            return
        self.reject()


def download_update_dialog(parent, language, info):
    dialog = _UpdateDownloadDialog(parent, language, info)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.installer_path
    if dialog.error:
        QMessageBox.warning(
            parent,
            t("update_title", language),
            t("update_download_failed", language, error=dialog.error),
        )
    return None


def confirm_update_install(parent, language):
    box = QMessageBox(parent)
    box.setWindowTitle(t("update_title", language))
    box.setIcon(QMessageBox.Icon.Question)
    box.setText(t("update_install_prompt", language))
    install = box.addButton(
        t("update_install_now", language),
        QMessageBox.ButtonRole.AcceptRole,
    )
    install.setObjectName("primaryButton")
    box.addButton(
        t("update_install_later", language),
        QMessageBox.ButtonRole.RejectRole,
    )
    box.exec()
    return box.clickedButton() is install
