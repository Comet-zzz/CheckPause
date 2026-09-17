from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from checkpause import APP_VERSION, AUTHOR, COPYRIGHT_YEAR, GITHUB_URL
from checkpause.data.settings import (
    DEFAULT_SERVER_URL,
    MODE_CLOUD,
    MODE_LOCAL,
)
from checkpause.gui.workers import AccountWorker
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


def api_settings_dialog(parent, language, config=None):
    config = config or {}
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("api_settings_title", language))
    dialog.setMinimumWidth(520)

    hint = QLabel(t("api_settings_hint", language))
    hint.setWordWrap(True)

    mode_combo = QComboBox()
    mode_combo.addItem(t("mode_local", language), MODE_LOCAL)
    mode_combo.addItem(t("mode_cloud", language), MODE_CLOUD)
    if config.get("mode") == MODE_CLOUD:
        mode_combo.setCurrentIndex(1)

    mode_hint = QLabel()
    mode_hint.setWordWrap(True)

    server_field = QLineEdit()
    server_field.setPlaceholderText("http://...")
    server_field.setText(config.get("server_url", "") or "")

    key_field = QLineEdit()
    key_field.setEchoMode(QLineEdit.EchoMode.Password)
    key_field.setPlaceholderText(t("api_key_placeholder", language))
    key_field.setText(config.get("api_key", "") or "")

    show_toggle = QCheckBox(t("api_key_show", language))
    show_toggle.toggled.connect(
        lambda checked: key_field.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )
    )

    base_field = QLineEdit()
    base_field.setPlaceholderText(t("api_base_url_placeholder", language))
    base_field.setText(config.get("base_url", "") or "")

    model_field = QLineEdit()
    model_field.setPlaceholderText(t("api_model_placeholder", language))
    model_field.setText(config.get("model", "") or "")

    form = QFormLayout()
    form.setHorizontalSpacing(16)
    form.setVerticalSpacing(10)
    form.addRow(t("ai_mode_label", language), mode_combo)
    form.addRow("", mode_hint)
    form.addRow(t("server_url_label", language), server_field)
    form.addRow(t("api_key_label", language), key_field)
    form.addRow("", show_toggle)
    form.addRow(t("api_base_url_label", language), base_field)
    form.addRow(t("api_model_label", language), model_field)

    # The provider fields are local mode's business. In cloud mode they are
    # hidden rather than greyed out, because leaving them on screen would show
    # anyone who opened this dialog which model the server runs on - and that
    # is a question the service deliberately does not answer.
    provider_fields = (key_field, show_toggle, base_field, model_field)
    provider_rows = [
        (field, form.labelForField(field)) for field in provider_fields
    ]

    def refresh_mode():
        """Show only the fields the chosen mode actually needs."""
        cloud = mode_combo.currentData() == MODE_CLOUD
        mode_hint.setText(
            t("mode_cloud_hint" if cloud else "mode_local_hint", language)
        )
        hint.setVisible(not cloud)
        for field, label in provider_rows:
            field.setVisible(not cloud)
            field.setEnabled(not cloud)
            if label is not None:
                label.setVisible(not cloud)
        server_field.setEnabled(cloud)

    mode_combo.currentIndexChanged.connect(refresh_mode)
    refresh_mode()

    buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
    )
    buttons.button(
        QDialogButtonBox.StandardButton.Ok
    ).setText(t("btn_yes", language))
    buttons.button(
        QDialogButtonBox.StandardButton.Cancel
    ).setText(t("btn_no", language))

    def on_accept():
        if mode_combo.currentData() == MODE_CLOUD:
            if not server_field.text().strip():
                QMessageBox.warning(
                    dialog,
                    t("api_settings_title", language),
                    t("server_url_empty", language),
                )
                return
        elif not key_field.text().strip():
            QMessageBox.warning(
                dialog,
                t("api_settings_title", language),
                t("api_key_empty", language),
            )
            return
        dialog.accept()

    buttons.accepted.connect(on_accept)
    buttons.rejected.connect(dialog.reject)

    layout = QVBoxLayout(dialog)
    layout.addWidget(hint)
    layout.addLayout(form)
    layout.addWidget(buttons)

    if dialog.exec() == QDialog.DialogCode.Accepted:
        return {
            "mode": mode_combo.currentData(),
            "server_url": server_field.text().strip(),
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
    changed = {"value": False}
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
    register_button = QPushButton(t("cloud_account_register", language))
    refresh_button = QPushButton(t("cloud_account_refresh", language))
    sign_out_button = QPushButton(t("cloud_account_sign_out", language))
    close_button = QPushButton(t("cloud_account_close", language))

    # Buying credits. The server owns the prices; this only picks one of the
    # packs it offers and then hands the browser over to the payment page.
    pack_combo = QComboBox()
    buy_button = QPushButton(t("cloud_topup_buy", language))
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
    credential_labels = [
        (field, form.labelForField(field)) for field in credentials
    ]
    session_buttons = (refresh_button, sign_out_button)
    topup_widgets = (topup_label, pack_combo, buy_button, topup_status)
    everything = (
        credentials + session_buttons + topup_widgets
        + (close_button, server_field)
    )

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
            lines.append(
                t("cloud_account_balance", language, balance=balance)
            )
        status.setText("\n".join(lines))

    def refresh():
        logged_in = signed_in()
        for widget in credentials:
            widget.setVisible(not logged_in)
        for field, label in credential_labels:
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
        account.update(
            {
                "username": (result.get("account") or {}).get("username", ""),
                "token": result.get("token", ""),
                "balance": (result.get("account") or {}).get("balance"),
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
        elif action == "me" and pack_combo.count() == 0 and signed_in():
            # The prices are the server's to decide; ask once per dialog.
            run("packs")

    def on_failed(message):
        finish()
        QMessageBox.warning(
            dialog, t("cloud_account_title", language), message
        )

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
        account["balance"] = order.get("balance")
        topup_status.setText(
            t("cloud_topup_done", language, balance=order.get("balance"))
        )
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
    refresh_button.clicked.connect(
        lambda: run("me", token=account.get("token", ""))
    )
    sign_out_button.clicked.connect(sign_out)
    buy_button.clicked.connect(buy)
    close_button.clicked.connect(dialog.accept)

    refresh()
    if signed_in():
        # The cached number is only a hint; ask while the dialog is open.
        run("me", token=account.get("token", ""))

    dialog.exec()
    return account if changed["value"] else None


def confirm_delete_dialog(parent, language="zh-CN"):
    box = QMessageBox(parent)
    box.setWindowTitle(t("confirm_delete_title", language))
    box.setText(t("confirm_delete_text", language))
    box.setIcon(QMessageBox.Icon.Warning)
    yes_button = box.addButton(
        t("btn_yes", language), QMessageBox.ButtonRole.AcceptRole
    )
    box.addButton(t("btn_no", language), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is yes_button


def confirm_close_dialog(parent, language="zh-CN"):
    box = QMessageBox(parent)
    box.setWindowTitle(t("confirm_close_title", language))
    box.setText(t("confirm_close_text", language))
    box.setIcon(QMessageBox.Icon.Question)
    yes_button = box.addButton(
        t("btn_yes", language), QMessageBox.ButtonRole.AcceptRole
    )
    box.addButton(t("btn_no", language), QMessageBox.ButtonRole.RejectRole)
    box.exec()
    return box.clickedButton() is yes_button


def show_about(parent, language):
    dialog = QDialog(parent)
    dialog.setWindowTitle(t("about_title", language))
    dialog.setMinimumWidth(440)

    title = QLabel(t("app_title", language))
    title_font = title.font()
    title_font.setPointSize(title_font.pointSize() + 4)
    title_font.setBold(True)
    title.setFont(title_font)

    body = QLabel(t("about_text", language).split("\n", 1)[-1])
    body.setWordWrap(True)

    version = QLabel(t("about_version", language, version=APP_VERSION))
    version_font = version.font()
    version_font.setBold(True)
    version.setFont(version_font)

    author = QLabel(t("about_author", language, author=AUTHOR))
    copyright_label = QLabel(
        t("about_copyright", language, year=COPYRIGHT_YEAR, author=AUTHOR)
    )
    link = QLabel(f'<a href="{GITHUB_URL}">{GITHUB_URL}</a>')
    link.setOpenExternalLinks(True)
    link.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextBrowserInteraction
    )

    pieces = QLabel(t("about_pieces", language))
    pieces.setWordWrap(True)
    pieces.setStyleSheet("color: #8a8a8a;")

    puzzles = QLabel(t("about_puzzles", language))
    puzzles.setWordWrap(True)
    puzzles.setStyleSheet("color: #8a8a8a;")

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.button(QDialogButtonBox.StandardButton.Close).setText(
        t("about_close", language)
    )
    buttons.rejected.connect(dialog.reject)

    layout = QVBoxLayout(dialog)
    layout.addWidget(title)
    layout.addWidget(version)
    layout.addWidget(body)
    layout.addSpacing(8)
    layout.addWidget(author)
    layout.addWidget(copyright_label)
    layout.addWidget(link)
    layout.addWidget(pieces)
    layout.addWidget(puzzles)
    layout.addWidget(buttons)

    dialog.exec()


def show_update_dialog(parent, language, info):
    """Offer a link to a newer release. Returns True when the user accepted."""
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

    download = box.addButton(
        t("update_download", language), QMessageBox.ButtonRole.AcceptRole
    )
    box.addButton(
        t("update_later", language), QMessageBox.ButtonRole.RejectRole
    )
    box.exec()

    if box.clickedButton() is not download:
        return False
    QDesktopServices.openUrl(QUrl(info.url))
    return True
