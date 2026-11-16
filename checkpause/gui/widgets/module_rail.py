from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from checkpause.gui.icons import rail_icon
from checkpause.i18n import t

RAIL_WIDTH = 128
FOOTER_HEIGHT = 48


class _AccountButton(QToolButton):
    """Text-only rail button that elides a long account name."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._full_text = ""

    def set_full_text(self, text):
        self._full_text = text
        self._apply_elide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self):
        text = self._full_text
        width = self.width() - 8
        if width > 0 and text:
            text = self.fontMetrics().elidedText(text, Qt.TextElideMode.ElideRight, width)
        super().setText(text)


class ModuleRail(QWidget):
    module_selected = Signal(str)
    account_clicked = Signal()
    settings_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("moduleRail")
        self.setFixedWidth(RAIL_WIDTH)

        self._language = "zh-CN"
        self._theme = "light"
        self._modules = {}

        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._module_box = QVBoxLayout()
        self._module_box.setContentsMargins(8, 14, 8, 0)
        self._module_box.setSpacing(4)
        layout.addLayout(self._module_box)
        layout.addStretch(1)
        layout.addWidget(self._build_footer())

    def add_module(self, module_id, label_key, icon_name):
        button = QToolButton()
        button.setObjectName("railModule")
        button.setCheckable(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIconSize(QSize(20, 20))
        button.setFixedHeight(40)
        button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        button.clicked.connect(lambda _checked=False, mid=module_id: self.module_selected.emit(mid))
        self._group.addButton(button)
        self._module_box.addWidget(button)
        self._modules[module_id] = {
            "button": button,
            "label_key": label_key,
            "icon_name": icon_name,
        }
        self._apply_icon(module_id)
        return button

    def _build_footer(self):
        footer = QWidget()
        footer.setObjectName("railFooter")
        footer.setFixedHeight(FOOTER_HEIGHT)

        row = QHBoxLayout(footer)
        row.setContentsMargins(6, 6, 6, 8)
        row.setSpacing(4)

        self._account_button = _AccountButton()
        self._account_button.setObjectName("railAccount")
        self._account_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self._account_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._account_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._account_button.setFixedHeight(32)
        self._account_button.clicked.connect(lambda: self.account_clicked.emit())

        self._settings_button = QToolButton()
        self._settings_button.setObjectName("railSettings")
        self._settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_button.setFixedSize(32, 32)
        self._settings_button.setIconSize(QSize(18, 18))
        self._settings_button.clicked.connect(lambda: self.settings_clicked.emit())

        row.addWidget(self._account_button, 1)
        row.addWidget(self._settings_button)
        return footer

    def set_account_name(self, name):
        self._account_button.setAccessibleName(name)
        self._account_button.set_full_text(name)

    def _apply_icon(self, module_id):
        entry = self._modules[module_id]
        entry["button"].setIcon(rail_icon(self._theme, entry["icon_name"]))

    def set_theme(self, theme):
        self._theme = theme
        for module_id in self._modules:
            self._apply_icon(module_id)
        self._settings_button.setIcon(rail_icon(theme, "settings", size=18))

    def set_active(self, module_id):
        self._group.setExclusive(False)
        for mid, entry in self._modules.items():
            entry["button"].setChecked(mid == module_id)
        self._group.setExclusive(True)

    def retranslate(self, language):
        self._language = language
        for entry in self._modules.values():
            label = t(entry["label_key"], language)
            entry["button"].setText(label)
        self._settings_button.setAccessibleName(t("menu_settings", language))
