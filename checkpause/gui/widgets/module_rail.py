from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from checkpause.gui.icons import rail_icon
from checkpause.i18n import t

RAIL_WIDTH = 108


class ModuleRail(QWidget):
    module_selected = pyqtSignal(str)

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
        layout.setContentsMargins(8, 14, 8, 14)
        layout.setSpacing(4)

        self._module_box = QVBoxLayout()
        self._module_box.setSpacing(4)
        layout.addLayout(self._module_box)
        layout.addStretch(1)

    def add_module(self, module_id, label_key, icon_name):
        button = QToolButton()
        button.setObjectName("railModule")
        button.setCheckable(True)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        button.setIconSize(QSize(20, 20))
        button.setFixedHeight(40)
        button.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        button.clicked.connect(
            lambda _checked=False, mid=module_id: self.module_selected.emit(
                mid
            )
        )
        self._group.addButton(button)
        self._module_box.addWidget(button)
        self._modules[module_id] = {
            "button": button,
            "label_key": label_key,
            "icon_name": icon_name,
        }
        self._apply_icon(module_id)
        return button

    def _apply_icon(self, module_id):
        entry = self._modules[module_id]
        entry["button"].setIcon(rail_icon(self._theme, entry["icon_name"]))

    def set_theme(self, theme):
        self._theme = theme
        for module_id in self._modules:
            self._apply_icon(module_id)

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
            entry["button"].setToolTip(label)
