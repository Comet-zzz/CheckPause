"""Application theme: colour tokens, palette and one shared stylesheet.

The light and dark themes are the same template with different token values,
so a widget style is added once and the two themes cannot drift apart.

The look is frosted glass: a soft gradient window, translucent surfaces with
hairline borders, and a neutral ink accent (no saturated blue).
"""

from string import Template

from PySide6.QtGui import QColor, QPalette

from checkpause.resources import resource_path

LIGHT = "light"
DARK = "dark"

CHAT_COLORS = {
    LIGHT: {
        "user_bg": "#22262b",
        "user_fg": "#ffffff",
        "ai_bg": "rgba(255, 255, 255, 0.66)",
        "ai_fg": "#1b1e23",
        "notice": "#5c636c",
        "error": "#b04a42",
    },
    DARK: {
        "user_bg": "rgba(255, 255, 255, 0.16)",
        "user_fg": "#f2f3f5",
        "ai_bg": "rgba(255, 255, 255, 0.07)",
        "ai_fg": "#e7e9ec",
        "notice": "#9aa1aa",
        "error": "#e0776e",
    },
}

# Row highlight for the move list: a soft neutral tint, not a second accent.
HIGHLIGHT_COLORS = {
    LIGHT: "#e4e6e9",
    DARK: "#3a3f45",
}

_TOKENS = {
    LIGHT: {
        "window_bg": (
            "qlineargradient(x1:0, y1:0, x2:0.9, y2:1,"
            " stop:0 #f7f8fa, stop:0.45 #eef0f4, stop:1 #e3e7ec)"
        ),
        "bg": "#f2f4f7",
        "overlay_bg": "rgba(252, 253, 254, 0.97)",
        "surface": "rgba(255, 255, 255, 0.72)",
        "surface_alt": "rgba(255, 255, 255, 0.42)",
        "border": "rgba(16, 20, 26, 0.10)",
        "border_strong": "rgba(16, 20, 26, 0.20)",
        "text": "#1b1e23",
        "text_muted": "#5c636c",
        "text_disabled": "#a2a7ad",
        "accent": "#26292f",
        "accent_hover": "#363b42",
        "accent_pressed": "#16181c",
        "accent_text": "#ffffff",
        "accent_soft": "rgba(16, 20, 26, 0.08)",
        "accent_off_bg": "rgba(16, 20, 26, 0.14)",
        "accent_off_text": "#8b9199",
        "hover": "rgba(16, 20, 26, 0.06)",
        "pressed": "rgba(16, 20, 26, 0.12)",
        "input_bg": "rgba(255, 255, 255, 0.78)",
        "selection_bg": "rgba(16, 20, 26, 0.12)",
        "selection_text": "#1b1e23",
        "scroll_bg": "rgba(16, 20, 26, 0.04)",
        "scroll_handle": "rgba(16, 20, 26, 0.22)",
        "scroll_handle_hover": "rgba(16, 20, 26, 0.34)",
        "danger": "#b04a42",
        "danger_hover": "#973d36",
        "danger_soft": "rgba(176, 74, 66, 0.12)",
        "menu_bg": "rgba(252, 253, 254, 0.97)",
        "menu_sel_bg": "rgba(16, 20, 26, 0.09)",
        "menu_sel_text": "#1b1e23",
        "rail_bg": "rgba(255, 255, 255, 0.45)",
        "rail_border": "rgba(16, 20, 26, 0.08)",
        "rail_text": "#4d545d",
        "rail_hover": "rgba(16, 20, 26, 0.06)",
        "rail_checked_bg": "rgba(16, 20, 26, 0.09)",
        "rail_checked_text": "#1b1e23",
        "editbar_btn_bg": "rgba(255, 255, 255, 0.9)",
        "editbar_btn_border": "rgba(16, 20, 26, 0.16)",
        "editbar_btn_hover": "#ffffff",
        "editbar_btn_checked": "rgba(16, 20, 26, 0.18)",
    },
    DARK: {
        "window_bg": (
            "qlineargradient(x1:0, y1:0, x2:0.9, y2:1,"
            " stop:0 #17191d, stop:0.5 #1d2025, stop:1 #131519)"
        ),
        "bg": "#191c20",
        "overlay_bg": "rgba(34, 37, 43, 0.97)",
        "surface": "rgba(255, 255, 255, 0.07)",
        "surface_alt": "rgba(255, 255, 255, 0.045)",
        "border": "rgba(255, 255, 255, 0.12)",
        "border_strong": "rgba(255, 255, 255, 0.22)",
        "text": "#e7e9ec",
        "text_muted": "#9aa1aa",
        "text_disabled": "#6f757d",
        "accent": "#e9ebee",
        "accent_hover": "#f6f7f8",
        "accent_pressed": "#cdd1d6",
        "accent_text": "#17191d",
        "accent_soft": "rgba(255, 255, 255, 0.12)",
        "accent_off_bg": "rgba(255, 255, 255, 0.10)",
        "accent_off_text": "#7c828a",
        "hover": "rgba(255, 255, 255, 0.08)",
        "pressed": "rgba(255, 255, 255, 0.14)",
        "input_bg": "rgba(255, 255, 255, 0.06)",
        "selection_bg": "rgba(255, 255, 255, 0.18)",
        "selection_text": "#f2f3f5",
        "scroll_bg": "rgba(255, 255, 255, 0.03)",
        "scroll_handle": "rgba(255, 255, 255, 0.18)",
        "scroll_handle_hover": "rgba(255, 255, 255, 0.30)",
        "danger": "#e0776e",
        "danger_hover": "#ea8b83",
        "danger_soft": "rgba(224, 119, 110, 0.14)",
        "menu_bg": "rgba(34, 37, 43, 0.97)",
        "menu_sel_bg": "rgba(255, 255, 255, 0.12)",
        "menu_sel_text": "#f2f3f5",
        "rail_bg": "rgba(20, 22, 26, 0.50)",
        "rail_border": "rgba(255, 255, 255, 0.08)",
        "rail_text": "#b9bfc7",
        "rail_hover": "rgba(255, 255, 255, 0.08)",
        "rail_checked_bg": "rgba(255, 255, 255, 0.14)",
        "rail_checked_text": "#f2f3f5",
        "editbar_btn_bg": "rgba(233, 235, 238, 0.92)",
        "editbar_btn_border": "rgba(255, 255, 255, 0.24)",
        "editbar_btn_hover": "#f4f6f8",
        "editbar_btn_checked": "rgba(16, 20, 26, 0.35)",
    },
}

_TEMPLATE = Template(
    """
QWidget {
    background: transparent;
    color: $text;
}
QMainWindow, QDialog {
    background: $window_bg;
}
QLabel {
    background: transparent;
}
QLabel#mutedLabel {
    color: $text_muted;
    font-size: 12px;
}
QLabel#accuracyLabel {
    color: $accent;
    font-weight: 600;
}
QLabel[emphasis="true"] {
    font-weight: 600;
}
QLabel[clockActive="true"] {
    color: $accent;
    font-weight: 600;
}
QLabel[clockActive="false"] {
    color: $text_muted;
}
QToolTip {
    background-color: $overlay_bg;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 4px 8px;
}
QMenuBar {
    background: transparent;
    color: $text;
}
QMenuBar::item {
    background: transparent;
    padding: 5px 12px;
    border-radius: 6px;
    margin: 2px;
}
QMenuBar::item:selected {
    background-color: $hover;
}
QMenu {
    background-color: $menu_bg;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 6px;
}
QMenu::item {
    padding: 6px 24px 6px 12px;
    border-radius: 6px;
}
QMenu::item:selected {
    background-color: $menu_sel_bg;
    color: $menu_sel_text;
}
QMenu::item:disabled {
    color: $text_disabled;
}
QMenu::separator {
    height: 1px;
    background-color: $border;
    margin: 5px 8px;
}
QPushButton {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 6px;
    padding: 6px 14px;
    min-height: 18px;
}
QPushButton:hover {
    background-color: $hover;
}
QPushButton:pressed {
    background-color: $pressed;
}
QPushButton:disabled {
    background-color: $surface_alt;
    color: $text_disabled;
    border-color: $border;
}
QPushButton:focus {
    border-color: $accent;
    outline: none;
}
QPushButton#primaryButton {
    background-color: $accent;
    color: $accent_text;
    border-color: $accent;
    font-weight: 600;
}
QPushButton#primaryButton:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
QPushButton#primaryButton:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}
QPushButton#primaryButton:disabled {
    background-color: $accent_off_bg;
    color: $accent_off_text;
    border-color: transparent;
}
QPushButton#primaryButton:focus {
    border-color: $accent_pressed;
}
QPushButton#dangerButton {
    color: $danger;
    border-color: $border_strong;
}
QPushButton#dangerButton:hover {
    background-color: $danger_soft;
    border-color: $danger;
    color: $danger_hover;
}
QPushButton#dangerButton:disabled {
    background-color: $surface_alt;
    color: $text_disabled;
    border-color: $border;
}
QLineEdit, QPlainTextEdit, QTextBrowser, QTextEdit, QSpinBox, QComboBox {
    background-color: $input_bg;
    color: $text;
    border: 1px solid $border;
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
}
QPlainTextEdit, QTextBrowser, QTextEdit {
    padding: 8px;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextBrowser:focus, QComboBox:focus {
    border-color: $accent;
}
QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled {
    background-color: $surface_alt;
    color: $text_disabled;
}
QComboBox {
    padding: 5px 10px;
}
QComboBox::drop-down {
    border: none;
    background: transparent;
    width: 24px;
}
QComboBox::down-arrow {
    image: url("$icon_chevron_down");
    width: 12px;
    height: 12px;
}
QComboBox QAbstractItemView {
    background-color: $menu_bg;
    color: $text;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
    selection-background-color: $menu_sel_bg;
    selection-color: $menu_sel_text;
    outline: none;
}
QCheckBox {
    background: transparent;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid $border_strong;
    border-radius: 4px;
    background-color: $input_bg;
}
QCheckBox::indicator:hover {
    border-color: $accent;
}
QCheckBox::indicator:checked {
    background-color: $accent;
    border-color: $accent;
    image: url("$icon_check");
}
QCheckBox::indicator:disabled {
    background-color: $surface_alt;
    border-color: $border;
}
QTableWidget, QTableView {
    background-color: $surface;
    alternate-background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    gridline-color: $border;
    selection-background-color: $selection_bg;
    selection-color: $selection_text;
}
QTableWidget::item {
    padding: 4px 6px;
}
QHeaderView::section {
    background-color: $surface_alt;
    color: $text_muted;
    border: none;
    border-bottom: 1px solid $border;
    padding: 6px 8px;
}
QTableCornerButton::section {
    background-color: $surface_alt;
    border: none;
}
QListWidget {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
}
QListWidget::item:hover {
    background-color: $hover;
}
QListWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
}
QTabWidget::pane {
    background: transparent;
    border: 1px solid $border;
    border-radius: 8px;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: $text_muted;
    padding: 6px 14px;
    margin-right: 4px;
    border: 1px solid transparent;
    border-radius: 6px;
}
QTabBar::tab:hover {
    background-color: $hover;
    color: $text;
}
QTabBar::tab:selected {
    background-color: $accent_soft;
    color: $text;
    font-weight: 600;
}
QProgressBar {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 5px;
    min-height: 8px;
    max-height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: $accent;
    border-radius: 4px;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background-color: $scroll_handle;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background-color: $scroll_handle_hover;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 2px;
}
QScrollBar::handle:horizontal {
    background-color: $scroll_handle;
    border-radius: 5px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background-color: $scroll_handle_hover;
}
QScrollBar::add-line, QScrollBar::sub-line {
    width: 0px;
    height: 0px;
}
QScrollBar::add-page, QScrollBar::sub-page {
    background: transparent;
}
QSlider::groove:horizontal {
    height: 4px;
    background-color: $border_strong;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: $accent;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    margin: -6px 0;
    border-radius: 8px;
    background-color: $accent;
}
QSlider::handle:horizontal:hover {
    background-color: $accent_hover;
}
QSlider::handle:horizontal:disabled {
    background-color: $text_disabled;
}
QSplitter::handle {
    background: transparent;
}
QSplitter::handle:horizontal {
    width: 6px;
}
QSplitter::handle:hover {
    background-color: $border;
}
QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
#moduleRail {
    background-color: $rail_bg;
    border-right: 1px solid $rail_border;
}
#moduleRail QToolButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    color: $rail_text;
    font-size: 12px;
    padding: 6px;
}
#moduleRail QToolButton:hover {
    background-color: $rail_hover;
}
#moduleRail QToolButton:checked {
    background-color: $rail_checked_bg;
    border-color: $border;
    color: $rail_checked_text;
    font-weight: 600;
}
#moduleRail QToolButton::menu-indicator {
    image: none;
}
#panelCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#statCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#statValue {
    color: $text;
    font-size: 22px;
    font-weight: 600;
}
#statCaption {
    color: $text_muted;
    font-size: 12px;
}
#evalControls {
    background-color: $accent_soft;
    border: 1px solid $border;
    border-radius: 10px;
}
#evalControls QLabel {
    color: $text_muted;
    font-size: 12px;
}
#evalControls QCheckBox {
    font-size: 12px;
}
#evalControls QComboBox {
    padding: 2px 8px;
}
#evalValue {
    color: $text;
    font-size: 13px;
    font-weight: 600;
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 1px 9px;
}
#boardEditBar QToolButton {
    background-color: $editbar_btn_bg;
    border: 1px solid $editbar_btn_border;
    border-radius: 6px;
    padding: 1px;
}
#boardEditBar QToolButton:hover {
    background-color: $editbar_btn_hover;
}
#boardEditBar QToolButton:checked {
    background-color: $editbar_btn_checked;
    border-color: $accent;
}
#boardEditBar QLabel {
    color: $text_muted;
}
#welcomePage {
    background: transparent;
}
#welcomeCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 16px;
}
#welcomeTitle {
    color: $text;
    font-size: 24px;
    font-weight: 600;
}
#welcomeSubtitle {
    color: $text_muted;
    font-size: 13px;
}
#welcomeFieldLabel {
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
}
#welcomeStatus {
    color: $danger;
    font-size: 12px;
}
#welcomePage QLineEdit, #welcomePage QComboBox {
    background-color: $input_bg;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
}
#welcomePage QLineEdit:focus, #welcomePage QComboBox:focus {
    border: 1px solid $accent;
}
#welcomePrimary {
    background-color: $accent;
    color: $accent_text;
    border: 1px solid $accent;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}
#welcomePrimary:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
#welcomePrimary:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}
#welcomePrimary:disabled {
    background-color: $accent_off_bg;
    border-color: transparent;
    color: $accent_off_text;
}
#welcomeSecondary {
    background-color: $surface;
    color: $text;
    border: 1px solid $border_strong;
    border-radius: 8px;
    padding: 9px 16px;
}
#welcomeSecondary:hover {
    background-color: $hover;
}
#welcomeSecondary:pressed {
    background-color: $pressed;
}
#welcomeSecondary:disabled {
    color: $text_disabled;
    border-color: $border;
}
"""
)

_CHECK_ICONS = {
    LIGHT: ("assets", "icons", "check.svg"),
    DARK: ("assets", "icons", "check_dark.svg"),
}
_CHEVRON_PATH = ("assets", "icons", "chevron_down.svg")


def _icon_url(parts):
    return resource_path(*parts).replace("\\", "/")


def _stylesheet(theme):
    tokens = dict(_TOKENS[theme])
    tokens["icon_check"] = _icon_url(_CHECK_ICONS[theme])
    tokens["icon_chevron_down"] = _icon_url(_CHEVRON_PATH)
    return _TEMPLATE.substitute(tokens)


def _palette(theme):
    tokens = _TOKENS[theme]
    palette = QPalette()
    role = QPalette.ColorRole
    group = QPalette.ColorGroup
    palette.setColor(role.Window, QColor(tokens["bg"]))
    palette.setColor(role.WindowText, QColor(tokens["text"]))
    palette.setColor(role.Base, QColor(tokens["bg"]))
    palette.setColor(role.AlternateBase, QColor(tokens["bg"]).lighter(106))
    palette.setColor(role.Text, QColor(tokens["text"]))
    palette.setColor(role.Button, QColor(tokens["bg"]))
    palette.setColor(role.ButtonText, QColor(tokens["text"]))
    palette.setColor(role.BrightText, QColor(tokens["text"]))
    palette.setColor(role.Highlight, QColor(tokens["accent"]))
    palette.setColor(role.HighlightedText, QColor(tokens["accent_text"]))
    palette.setColor(role.PlaceholderText, QColor(tokens["text_muted"]))
    palette.setColor(role.ToolTipBase, QColor(tokens["bg"]))
    palette.setColor(role.ToolTipText, QColor(tokens["text"]))
    palette.setColor(role.Link, QColor(tokens["text"]))
    palette.setColor(group.Disabled, role.Text, QColor(tokens["text_disabled"]))
    palette.setColor(group.Disabled, role.WindowText, QColor(tokens["text_disabled"]))
    palette.setColor(group.Disabled, role.ButtonText, QColor(tokens["text_disabled"]))
    palette.setColor(group.Disabled, role.Highlight, QColor(tokens["border"]))
    palette.setColor(group.Disabled, role.HighlightedText, QColor(tokens["text_muted"]))
    return palette


LIGHT_STYLESHEET = _stylesheet(LIGHT)
DARK_STYLESHEET = _stylesheet(DARK)


def apply_theme(app, theme):
    if theme not in _TOKENS:
        theme = LIGHT
    app.setStyle("Fusion")
    app.setPalette(_palette(theme))
    app.setStyleSheet(LIGHT_STYLESHEET if theme == LIGHT else DARK_STYLESHEET)


def danger_color(theme):
    """The danger (destructive action) tint for the given theme."""
    return _TOKENS.get(theme, _TOKENS[LIGHT])["danger"]
