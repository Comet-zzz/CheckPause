from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from checkpause import APP_VERSION, AUTHOR, COPYRIGHT_YEAR, GITHUB_URL
from checkpause.i18n import t


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
    form.addRow(t("api_key_label", language), key_field)
    form.addRow("", show_toggle)
    form.addRow(t("api_base_url_label", language), base_field)
    form.addRow(t("api_model_label", language), model_field)

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
        if not key_field.text().strip():
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
            "api_key": key_field.text().strip(),
            "base_url": base_field.text().strip(),
            "model": model_field.text().strip(),
        }
    return None


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
