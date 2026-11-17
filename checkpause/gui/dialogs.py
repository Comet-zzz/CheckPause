from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import (
    QColor,
    QDesktopServices,
    QFontDatabase,
    QKeySequence,
    QPainter,
    QPixmap,
    QShortcut,
)
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QButtonGroup,
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from checkpause import (
    APP_VERSION,
    AUTHOR,
    COPYRIGHT_YEAR,
    GITHUB_URL,
    SUPPORT_EMAIL,
    WEBSITE_URL,
)
from checkpause.assets import BOARD_THEMES, PIECE_SETS, SOUND_CHOICES
from checkpause.core.pgn import parse_pgn_game, pgn_game_text, scan_pgn_games
from checkpause.data.settings import (
    DEFAULT_SERVER_URL,
    get_api_key,
    get_base_url,
    get_model,
)
from checkpause.gui.icons import action_icon
from checkpause.gui.theme import DARK, LIGHT
from checkpause.gui.workers import AccountWorker, UpdateDownloadWorker
from checkpause.i18n import t
from checkpause.resources import resource_path

# How often to ask whether a payment has landed, and when to stop asking.
# Three seconds feels immediate without hammering the server; ten minutes is
# longer than the cashier holds an order anyway.
POLL_INTERVAL_MS = 3000
POLL_LIMIT = 200


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
    dialog.setObjectName("accountDialog")
    dialog.setWindowTitle(t("cloud_account_title", language))
    dialog.setFixedWidth(380)

    def divider():
        line = QFrame()
        line.setObjectName("accountDivider")
        line.setFixedHeight(1)
        return line

    # The account owns this window: the balance is the headline and topping up
    # is one section inside the card, not the reason the window exists.
    subtitle = QLabel(t("cloud_account_subtitle", language))
    subtitle.setObjectName("accountSubtitle")
    subtitle.setWordWrap(True)

    status = QLabel()
    status.setObjectName("accountStatusLine")
    status.setWordWrap(True)
    status.setVisible(False)

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

    sign_in_button = QPushButton(t("cloud_account_sign_in", language))
    sign_in_button.setObjectName("primaryButton")
    register_button = QPushButton(t("cloud_account_register", language))
    rename_button = QPushButton(t("cloud_account_rename", language))
    refresh_button = QPushButton(t("cloud_account_refresh", language))
    refresh_button.setObjectName("accountPill")
    sign_out_button = QPushButton(t("cloud_account_sign_out", language))
    delete_button = QPushButton(t("cloud_account_delete", language))
    delete_button.setObjectName("dangerButton")

    # Buying credits. The server owns the prices; this only picks one of the
    # packs it offers and then hands the browser over to the payment page.
    pack_combo = QComboBox()
    buy_button = QPushButton(t("cloud_topup_buy", language))
    buy_button.setObjectName("primaryButton")
    topup_title = QLabel(t("cloud_topup_title", language))
    topup_title.setObjectName("accountSectionTitle")
    topup_status = QLabel()
    topup_status.setWordWrap(True)
    topup_status.setVisible(False)
    topup_hint = QLabel(t("cloud_topup_hint", language))
    topup_hint.setObjectName("accountHint")
    topup_hint.setWordWrap(True)

    avatar = QLabel()
    avatar.setObjectName("accountAvatar")
    avatar.setFixedSize(40, 40)
    avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

    name_label = QLabel()
    name_label.setObjectName("accountName")
    signed_in_label = QLabel(t("cloud_account_status_signed_in", language))
    signed_in_label.setObjectName("accountMuted")

    heading = QVBoxLayout()
    heading.setContentsMargins(0, 0, 0, 0)
    heading.setSpacing(1)
    heading.addWidget(name_label)
    heading.addWidget(signed_in_label)

    header_row = QHBoxLayout()
    header_row.setContentsMargins(0, 0, 0, 0)
    header_row.setSpacing(12)
    header_row.addWidget(avatar)
    header_row.addLayout(heading, 1)

    balance_value = QLabel()
    balance_value.setObjectName("accountBalanceValue")
    balance_unit = QLabel(t("cloud_account_balance_unit", language))
    balance_unit.setObjectName("accountBalanceUnit")

    balance_row = QHBoxLayout()
    balance_row.setContentsMargins(0, 0, 0, 0)
    balance_row.setSpacing(6)
    balance_row.addWidget(balance_value, 0, Qt.AlignmentFlag.AlignBottom)
    balance_row.addWidget(balance_unit, 0, Qt.AlignmentFlag.AlignBottom)
    balance_row.addStretch(1)
    balance_row.addWidget(refresh_button)

    # The server address is only needed for self-hosted deployments, so it
    # stays folded away instead of dominating the sign-in form.
    server_box = QWidget()
    server_box.setObjectName("accountServer")
    server_layout = QVBoxLayout(server_box)
    server_layout.setContentsMargins(0, 0, 0, 0)
    server_layout.setSpacing(4)
    server_layout.addWidget(QLabel(t("cloud_account_server", language)))
    server_layout.addWidget(server_field)
    server_box.setVisible(False)

    advanced_toggle = QCheckBox(t("cloud_account_advanced", language))
    advanced_toggle.toggled.connect(server_box.setVisible)

    form = QFormLayout()
    form.setHorizontalSpacing(12)
    form.setVerticalSpacing(8)
    form.addRow(t("cloud_account_username", language), username_field)
    form.addRow(t("cloud_account_password", language), password_field)
    form.addRow("", show_toggle)

    sign_buttons = QHBoxLayout()
    sign_buttons.setSpacing(8)
    sign_buttons.addWidget(sign_in_button, 1)
    sign_buttons.addWidget(register_button, 1)

    auth_box = QWidget()
    auth_box.setObjectName("accountAuth")
    auth_layout = QVBoxLayout(auth_box)
    auth_layout.setContentsMargins(0, 0, 0, 0)
    auth_layout.setSpacing(8)
    auth_layout.addLayout(form)
    auth_layout.addWidget(advanced_toggle)
    auth_layout.addWidget(server_box)
    auth_layout.addLayout(sign_buttons)

    account_card = QFrame()
    account_card.setObjectName("accountCard")
    card_layout = QVBoxLayout(account_card)
    card_layout.setContentsMargins(18, 16, 18, 16)
    card_layout.setSpacing(12)
    card_layout.addLayout(header_row)
    card_layout.addWidget(divider())
    card_layout.addLayout(balance_row)
    card_layout.addWidget(divider())
    card_layout.addWidget(topup_title)
    card_layout.addWidget(pack_combo)
    card_layout.addWidget(buy_button)
    card_layout.addWidget(topup_status)
    card_layout.addWidget(topup_hint)

    # One row, equal width: the three account actions are equally easy to reach.
    account_row = QHBoxLayout()
    account_row.setSpacing(8)
    account_row.addWidget(rename_button, 1)
    account_row.addWidget(sign_out_button, 1)
    account_row.addWidget(delete_button, 1)

    account_box = QWidget()
    account_box.setObjectName("accountSession")
    account_layout = QVBoxLayout(account_box)
    account_layout.setContentsMargins(0, 0, 0, 0)
    account_layout.setSpacing(12)
    account_layout.addWidget(account_card)
    account_layout.addLayout(account_row)

    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(18, 18, 18, 18)
    layout.setSpacing(12)
    layout.addWidget(subtitle)
    layout.addWidget(status)
    layout.addWidget(auth_box)
    layout.addWidget(account_box)

    everything = (auth_box, account_box)

    def signed_in():
        return bool(account.get("token"))

    def show_status():
        if not signed_in():
            subtitle.setVisible(True)
            account_box.setVisible(False)
            return
        subtitle.setVisible(False)
        account_box.setVisible(True)
        username = account.get("username", "")
        avatar.setText((username[:1] or "?").upper())
        name_label.setText(username)
        balance = account.get("balance")
        balance_value.setText("—" if balance is None else str(balance))
        fee = account.get("rename_fee")
        rename_button.setToolTip(
            t("cloud_rename_cost", language, fee=fee) if fee is not None else ""
        )

    def refresh():
        logged_in = signed_in()
        auth_box.setVisible(not logged_in)
        if not logged_in:
            username_field.setFocus()
        show_status()
        dialog.adjustSize()

    def set_busy(value):
        for widget in everything:
            widget.setEnabled(not value)
        if value:
            status.setText(t("cloud_account_working", language))
            status.setVisible(True)
        else:
            status.setVisible(False)
            refresh()

    def finish():
        busy["worker"] = None
        set_busy(False)

    def on_done(action, result):
        if action == "packs":
            pack_combo.clear()
            for pack in result.get("packs") or []:
                price = pack.get("price_cents", 0) / 100
                pack_combo.addItem(
                    t(
                        "cloud_topup_pack",
                        language,
                        price=f"{price:.2f}",
                        credits=pack.get("credits", 0),
                    ),
                    pack.get("product_id"),
                )
            finish()
            return

        if action == "open_order":
            order = result.get("order") or {}
            if order.get("pay_url"):
                topup_status.setText(t("cloud_topup_waiting", language))
                topup_status.setVisible(True)
                # The hosted checkout belongs in a browser, so the desktop app
                # opens a page rather than trying to become a web application.
                QDesktopServices.openUrl(QUrl(order["pay_url"]))
                start_polling(order.get("order_id", ""))
            finish()
            return

        changed["value"] = True
        changed["action"] = action
        account.update(
            {
                "id": (result.get("account") or {}).get("id"),
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
        elif action == "delete_account":
            QMessageBox.information(
                dialog,
                t("cloud_delete_title", language),
                t("cloud_delete_done", language),
            )
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

    def delete_account():
        if not signed_in():
            return
        answer = QMessageBox.question(
            dialog,
            t("cloud_delete_title", language),
            t("cloud_delete_confirm", language),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        run("delete_account", token=account.get("token", ""))

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
            product_id=pack_combo.currentData(),
        )

    # Waiting for a payment. Polling is what makes the purchase arrive at all:
    # the server hears from Creem, and nothing pushes the news to a desktop
    # client.
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
        topup_status.setVisible(True)
        show_status()

    def poll_once():
        if not poll["order_id"] or poll["worker"] is not None:
            return
        poll["tries"] += 1
        if poll["tries"] > POLL_LIMIT:
            stop_polling()
            topup_status.setText(t("cloud_topup_gave_up", language))
            topup_status.setVisible(True)
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
    delete_button.clicked.connect(delete_account)
    buy_button.clicked.connect(buy)

    refresh()
    if signed_in():
        # The cached number is only a hint; ask while the dialog is open.
        run("me", token=account.get("token", ""))

    dialog.exec()
    if not changed["value"]:
        return None
    return dict(account, action=changed["action"])


def _piece_label(name):
    """Turn an asset id like ``kiwen-suwi`` into something a person reads."""
    return " ".join(part.capitalize() for part in name.split("-"))


PREVIEW_PIECES = ("wK", "wQ", "wR", "wN")


def _piece_pixmap(piece_set, code, size):
    renderer = QSvgRenderer(resource_path("assets", "pieces", piece_set, code + ".svg"))
    if not renderer.isValid():
        return QPixmap()
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter)
    painter.end()
    return pixmap


def _pieces_preview(piece_set, size=24):
    gap = 2
    pieces = [_piece_pixmap(piece_set, code, size) for code in PREVIEW_PIECES]
    pixmap = QPixmap(len(pieces) * (size + gap) - gap, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    for index, piece in enumerate(pieces):
        painter.drawPixmap(index * (size + gap), 0, piece)
    painter.end()
    return pixmap


def _board_preview(name, size=64):
    """The chosen board's two colours, shown as a little 4x4 board."""
    light, dark = BOARD_THEMES.get(name, BOARD_THEMES["blue"])
    cell = size // 4
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    for row in range(4):
        for column in range(4):
            color = light if (row + column) % 2 == 0 else dark
            painter.fillRect(column * cell, row * cell, cell, cell, QColor(color))
    painter.end()
    return pixmap


class _SettingsDialog(QDialog):
    """Every preference in one window: a category list beside the options.

    Changes apply the moment a control is touched. The language switch is the
    only one that rebuilds the window, because its own labels have to follow.
    """

    def __init__(self, parent, language, current, handlers):
        super().__init__(parent)
        self.setObjectName("settingsDialog")
        self._language = language
        self._current = dict(current)
        self._handlers = handlers
        self._page_index = 0
        self._shell = None
        self._root = QVBoxLayout(self)
        self._root.setContentsMargins(0, 0, 0, 0)
        self.setFixedWidth(580)
        self._build()

    # -- construction ---------------------------------------------------

    def _build(self):
        if self._shell is not None:
            self._root.removeWidget(self._shell)
            self._shell.deleteLater()
        self.setWindowTitle(t("menu_settings", self._language))
        self._shell = QWidget()
        self._root.addWidget(self._shell)

        outer = QHBoxLayout(self._shell)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(14)

        self._nav = QWidget()
        self._nav.setObjectName("settingsNav")
        self._nav.setFixedWidth(150)
        nav_layout = QVBoxLayout(self._nav)
        nav_layout.setContentsMargins(6, 6, 6, 6)
        nav_layout.setSpacing(2)
        group = QButtonGroup(self._shell)
        group.setExclusive(True)
        self._nav_buttons = []
        self._stack = QStackedWidget()

        for index, key in enumerate(("general", "look", "service", "about")):
            button = QPushButton(t("settings_section_" + key, self._language))
            button.setObjectName("settingsNavItem")
            button.setCheckable(True)
            button.setFixedHeight(34)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, i=index: self._show_page(i))
            group.addButton(button)
            nav_layout.addWidget(button)
            self._nav_buttons.append(button)
            self._stack.addWidget(self._page(key))
        nav_layout.addStretch(1)

        outer.addWidget(self._nav)
        outer.addWidget(self._stack, 1)

        self._show_page(min(self._page_index, self._stack.count() - 1))
        self._lock_size()

    def _show_page(self, index):
        self._page_index = index
        self._stack.setCurrentIndex(index)
        for position, button in enumerate(self._nav_buttons):
            button.setChecked(position == index)

    def _lock_size(self):
        """One fixed window size, tall enough for every page."""
        height = self._nav.sizeHint().height()
        for index in range(self._stack.count()):
            page = self._stack.widget(index)
            body = page.widget() if isinstance(page, QScrollArea) else page
            height = max(height, body.sizeHint().height())
        self.setFixedSize(self.width(), height + 28)

    def _page(self, key):
        scroll = QScrollArea()
        scroll.setObjectName("settingsPage")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(14)
        getattr(self, "_page_" + key)(layout)
        scroll.setWidget(body)
        return scroll

    def _page_general(self, layout):
        box = self._panel(layout)
        self._choice_row(
            box,
            "menu_language",
            [("zh-CN", t("lang_zh", self._language)), ("en-US", t("lang_en", self._language))],
            "language",
        )
        self._choice_row(
            box,
            "settings_theme",
            [(LIGHT, t("theme_light", self._language)), (DARK, t("theme_dark", self._language))],
            "theme",
        )
        self._choice_row(
            box,
            "menu_sound",
            [(name, t("sound_" + name, self._language)) for name in SOUND_CHOICES],
            "sound_set",
        )

    def _page_look(self, layout):
        box = self._panel(layout)
        self._piece_picker(box)
        self._board_picker(box)

    def _page_service(self, layout):
        box = self._panel(layout)
        key_field = QLineEdit(get_api_key())
        key_field.setEchoMode(QLineEdit.EchoMode.Password)
        key_field.setPlaceholderText(t("api_key_placeholder", self._language))
        show_toggle = QCheckBox(t("api_key_show", self._language))
        show_toggle.toggled.connect(
            lambda checked: key_field.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        base_field = QLineEdit(get_base_url())
        model_field = QLineEdit(get_model())

        form = QFormLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.addRow(t("api_key_label", self._language), key_field)
        form.addRow("", show_toggle)
        form.addRow(t("api_base_url_label", self._language), base_field)
        form.addRow(t("api_model_label", self._language), model_field)
        box.addLayout(form)

        status = QLabel()
        status.setObjectName("settingsRowHint")

        def on_save():
            api_key = key_field.text().strip()
            base_url = base_field.text().strip()
            model = model_field.text().strip()
            checks = (
                (api_key, "api_key_empty"),
                (base_url, "api_base_url_empty"),
                (model, "api_model_empty"),
            )
            for value, key in checks:
                if not value:
                    QMessageBox.warning(
                        self,
                        t("api_settings_title", self._language),
                        t(key, self._language),
                    )
                    return
            handler = self._handlers.get("save_byok")
            if handler is not None:
                handler(api_key, base_url, model)
            status.setText(t("api_settings_saved", self._language))

        save_button = QPushButton(t("settings_save", self._language))
        save_button.setObjectName("primaryButton")
        save_button.clicked.connect(on_save)
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(save_button)
        row.addWidget(status, 1)
        box.addLayout(row)

    def _page_about(self, layout):
        box = self._panel(layout, stretch=False)
        version = QLabel(t("about_version", self._language, version=APP_VERSION))
        version.setObjectName("settingsVersion")
        description = QLabel(t("about_text", self._language))
        description.setObjectName("settingsRowHint")
        description.setWordWrap(True)
        box.addWidget(version)
        box.addWidget(description)
        box.addLayout(self._link_row("github", GITHUB_URL))
        box.addLayout(self._link_row("globe", WEBSITE_URL))
        box.addLayout(self._link_row("mail", f"mailto:{SUPPORT_EMAIL}", SUPPORT_EMAIL))

        check = QPushButton(t("action_check_update", self._language))
        check.setObjectName("primaryButton")
        check.clicked.connect(lambda: self._hand_off("check_update"))
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        buttons.addWidget(check)
        buttons.addStretch(1)
        box.addLayout(buttons)

        box.addStretch(1)
        copyright_line = QLabel(
            t("about_copyright", self._language, year=COPYRIGHT_YEAR, author=AUTHOR)
        )
        copyright_line.setObjectName("settingsVersion")
        copyright_row = QHBoxLayout()
        copyright_row.addStretch(1)
        copyright_row.addWidget(copyright_line)
        box.addLayout(copyright_row)

    # -- building blocks ------------------------------------------------

    def _panel(self, layout, stretch=True):
        card = QFrame()
        card.setObjectName("settingsCard")
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        outer = QVBoxLayout(card)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(14)
        content = QVBoxLayout()
        content.setSpacing(14)
        outer.addLayout(content)
        if stretch:
            outer.addStretch(1)
        layout.addWidget(card)
        return content

    def _row_label(self, text):
        label = QLabel(text)
        label.setObjectName("settingsRowLabel")
        label.setMinimumWidth(56)
        return label

    def _link_row(self, icon_name, url, text=None):
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        if icon_name:
            icon = QLabel()
            icon.setPixmap(
                action_icon(self._current.get("theme", LIGHT), icon_name, size=16).pixmap(16, 16)
            )
            icon.setFixedSize(16, 16)
            icon.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            row.addWidget(icon)
        else:
            row.addSpacing(24)
        label = QLabel(f'<a href="{url}">{text or url.split("://", 1)[-1]}</a>')
        label.setObjectName("settingsRowHint")
        label.setOpenExternalLinks(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        row.addWidget(label)
        row.addStretch(1)
        return row

    def _choice_row(self, box, label_key, options, key):
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(self._row_label(t(label_key, self._language)))
        row.addStretch(1)
        group = QButtonGroup(self._shell)
        group.setExclusive(True)
        for value, text in options:
            button = QPushButton(text)
            button.setObjectName("settingsChoice")
            button.setCheckable(True)
            button.setChecked(self._current.get(key) == value)
            group.addButton(button)
            button.clicked.connect(lambda _checked=False, v=value, k=key: self._choose(k, v))
            row.addWidget(button)
        box.addLayout(row)

    def _piece_picker(self, box):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._row_label(t("menu_pieces", self._language)))
        row.addStretch(1)
        combo = QComboBox()
        combo.setMinimumWidth(140)
        for name in PIECE_SETS:
            combo.addItem(_piece_label(name), name)
        index = combo.findData(self._current.get("piece_set"))
        if index >= 0:
            combo.setCurrentIndex(index)
        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setPixmap(_pieces_preview(self._current.get("piece_set", PIECE_SETS[0])))
        preview.setFixedSize(preview.pixmap().size())

        def on_change(_index):
            value = combo.currentData()
            preview.setPixmap(_pieces_preview(value))
            self._choose("piece_set", value)

        combo.currentIndexChanged.connect(on_change)
        row.addWidget(combo)
        row.addWidget(preview)
        box.addLayout(row)

    def _board_picker(self, box):
        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self._row_label(t("menu_board", self._language)))
        row.addStretch(1)
        combo = QComboBox()
        combo.setMinimumWidth(140)
        for name in BOARD_THEMES:
            combo.addItem(t("board_theme_" + name, self._language), name)
        index = combo.findData(self._current.get("board_theme"))
        if index >= 0:
            combo.setCurrentIndex(index)
        preview = QLabel()
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setPixmap(_board_preview(self._current.get("board_theme", "blue")))
        preview.setFixedSize(preview.pixmap().size())

        def on_change(_index):
            value = combo.currentData()
            preview.setPixmap(_board_preview(value))
            self._choose("board_theme", value)

        combo.currentIndexChanged.connect(on_change)
        row.addWidget(combo)
        row.addWidget(preview)
        box.addLayout(row)

    # -- actions --------------------------------------------------------

    def _choose(self, key, value):
        if self._current.get(key) == value:
            return
        self._current[key] = value
        handler = self._handlers.get(key)
        if handler is not None:
            handler(value)
        if key in ("language", "theme"):
            # Language changes the labels and the theme changes the link icons.
            if key == "language":
                self._language = value
            self._build()

    def _hand_off(self, name):
        handler = self._handlers.get(name)
        if handler is None:
            return
        self.accept()
        handler()


def settings_dialog(parent, language, current, handlers):
    """Open the one window that owns every preference."""
    dialog = _SettingsDialog(parent, language, current, handlers)
    dialog.exec()


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

        self._worker = UpdateDownloadWorker(info.url, info.version, info.sha256, self)
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


class _PgnGameDialog(QDialog):
    def __init__(self, parent, language, games):
        super().__init__(parent)
        self._games = list(games)
        self.setObjectName("pgnGameDialog")
        self.setWindowTitle(t("pgn_games_title", language))
        self.setMinimumSize(560, 380)

        intro = QLabel(t("pgn_games_intro", language, count=len(self._games)))
        intro.setObjectName("mutedLabel")
        intro.setWordWrap(True)

        self._list = QListWidget()
        self._list.setObjectName("pgnGameList")
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        for index, game in enumerate(self._games, start=1):
            item = QListWidgetItem(_pgn_game_label(index, game.headers))
            item.setToolTip(item.text())
            self._list.addItem(item)
        self._list.setCurrentRow(0)
        self._list.itemDoubleClicked.connect(lambda _item: self.accept())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        load = buttons.button(QDialogButtonBox.StandardButton.Ok)
        load.setText(t("pgn_games_load", language))
        load.setObjectName("primaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_no", language))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(intro)
        layout.addWidget(self._list, 1)
        layout.addWidget(buttons)

    def selected_index(self):
        row = self._list.currentRow()
        if row < 0 or row >= len(self._games):
            return None
        return row


def choose_pgn_game_dialog(parent, language, games):
    """Return the index of the game the user picked, or None on cancel."""
    games = list(games or [])
    if not games:
        return None
    if len(games) == 1:
        return 0
    dialog = _PgnGameDialog(parent, language, games)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.selected_index()
    return None


def _pgn_game_label(index, headers):
    white = _pgn_header(headers, "White")
    black = _pgn_header(headers, "Black")
    result = _pgn_header(headers, "Result", "*")
    date = _pgn_header(headers, "Date")
    if date.startswith("????"):
        date = "?"
    event = _pgn_header(headers, "Event")
    round_number = _pgn_header(headers, "Round")
    eco = _pgn_header(headers, "ECO")

    details = [result, date]
    if event != "?":
        details.append(event)
    if round_number != "?":
        details.append(f"R{round_number}")
    if eco != "?":
        details.append(eco)
    return f"{index}. {white} — {black}\n{' · '.join(details)}"


def _pgn_header(headers, key, fallback="?"):
    value = str((headers or {}).get(key) or "").strip()
    return value or fallback


class _PgnPasteDialog(QDialog):
    def __init__(self, parent, language):
        super().__init__(parent)
        self._language = language
        self._selection = None
        self.setObjectName("pgnPasteDialog")
        self.setWindowTitle(t("pgn_paste_title", language))
        self.setMinimumSize(620, 460)

        self._edit = QPlainTextEdit()
        self._edit.setFont(QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont))
        self._edit.setPlaceholderText(t("pgn_paste_placeholder", language))
        self._edit.textChanged.connect(self._clear_error)

        self._error = QLabel()
        self._error.setObjectName("errorLabel")
        self._error.setWordWrap(True)
        self._error.setVisible(False)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        load = buttons.button(QDialogButtonBox.StandardButton.Ok)
        load.setText(t("pgn_games_load", language))
        load.setObjectName("primaryButton")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_no", language))
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)

        self._shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self._shortcut.activated.connect(self._accept)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.addWidget(self._edit, 1)
        layout.addWidget(self._error)
        layout.addWidget(buttons)
        self._edit.setFocus()

    def selection(self):
        return self._selection

    def _show_error(self, message):
        self._error.setText(message)
        self._error.setVisible(True)

    def _clear_error(self):
        self._error.clear()
        self._error.setVisible(False)

    def _accept(self):
        text = self._edit.toPlainText().strip()
        if not text:
            self._show_error(t("empty_pgn_error", self._language))
            return
        try:
            games = scan_pgn_games(text)
        except (ValueError, OSError):
            games = []
        if not games:
            self._show_error(t("pgn_invalid", self._language))
            return
        index = 0
        if len(games) > 1:
            index = choose_pgn_game_dialog(self, self._language, games)
            if index is None:
                return
        game_text = pgn_game_text(text, games[index])
        game = parse_pgn_game(game_text)
        if game is None:
            self._show_error(t("pgn_invalid", self._language))
            return
        if not any(game.mainline_moves()):
            self._show_error(t("pgn_no_moves", self._language))
            return
        self._selection = (game_text, game)
        self.accept()


def pgn_paste_dialog(parent, language):
    """Return ``(game_text, game)`` for the pasted game, or None on cancel."""
    dialog = _PgnPasteDialog(parent, language)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.selection()
    return None
