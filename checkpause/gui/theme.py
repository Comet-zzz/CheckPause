LIGHT = "light"
DARK = "dark"

CHAT_COLORS = {
    LIGHT: {
        "user_bg": "#3a7bd5",
        "user_fg": "#ffffff",
        "ai_bg": "#ececec",
        "ai_fg": "#1a1a1a",
        "notice": "#8a8a8a",
        "error": "#c0392b",
    },
    DARK: {
        "user_bg": "#3a7bd5",
        "user_fg": "#ffffff",
        "ai_bg": "#2f2f2f",
        "ai_fg": "#e6e6e6",
        "notice": "#9a9a9a",
        "error": "#ff6b6b",
    },
}

LIGHT_STYLESHEET = """
QMenuBar {
    background-color: #f0f0f0;
}
QMenuBar::item {
    background-color: #e4e4e4;
    color: #1a1a1a;
    padding: 4px 12px;
}
QMenuBar::item:selected {
    background-color: #d6d6d6;
}
#moduleRail {
    background-color: #f3f4f6;
    border-right: 1px solid #e3e5e9;
}
#moduleRail QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 12px;
    color: #4b4f57;
    font-size: 12px;
    padding: 4px 6px;
}
#moduleRail QToolButton:hover {
    background-color: #eceef1;
}
#moduleRail QToolButton:checked {
    background-color: #e0e4e9;
    color: #33373d;
}
#moduleRail QToolButton::menu-indicator {
    image: none;
}
QSlider::groove:horizontal {
    height: 4px;
    background-color: #d0d3d8;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: #3a7bd5;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background-color: #3a7bd5;
}
QSlider::handle:horizontal:hover {
    background-color: #2f6bbd;
}
#boardEditBar QToolButton {
    background-color: #ffffff;
    border: 1px solid #d6d9de;
    border-radius: 4px;
    padding: 1px;
}
#boardEditBar QToolButton:hover {
    background-color: #eef1f5;
}
#boardEditBar QToolButton:checked {
    background-color: #cfe0f7;
    border-color: #3a7bd5;
}
#boardEditBar QLabel {
    color: #4a4d52;
}
#welcomePage {
    background-color: #f4f5f7;
}
#welcomeCard {
    background-color: #ffffff;
    border: 1px solid #e6e8ec;
    border-radius: 16px;
}
#welcomeTitle {
    color: #1f2328;
    font-size: 24px;
    font-weight: 600;
}
#welcomeSubtitle {
    color: #6b7280;
    font-size: 13px;
}
#welcomeFieldLabel {
    color: #4b5563;
    font-size: 12px;
    font-weight: 600;
}
#welcomePage QCheckBox {
    background-color: transparent;
}
#welcomePage QLineEdit, #welcomePage QComboBox {
    background-color: #ffffff;
    color: #1f2328;
    border: 1px solid #d8dce2;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
}
#welcomePage QLineEdit:focus, #welcomePage QComboBox:focus {
    border: 1px solid #3a7bd5;
}
#welcomePrimary {
    background-color: #3a7bd5;
    color: #ffffff;
    border: 1px solid #3a7bd5;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}
#welcomePrimary:hover {
    background-color: #2f6bbd;
    border-color: #2f6bbd;
}
#welcomePrimary:pressed {
    background-color: #2a61ad;
    border-color: #2a61ad;
}
#welcomePrimary:disabled {
    background-color: #aac5e9;
    border-color: #aac5e9;
    color: #eef3fa;
}
#welcomeSecondary {
    background-color: #ffffff;
    color: #33373d;
    border: 1px solid #d0d5dc;
    border-radius: 8px;
    padding: 9px 16px;
}
#welcomeSecondary:hover {
    background-color: #f2f4f7;
}
#welcomeSecondary:pressed {
    background-color: #e7eaef;
}
#welcomeSecondary:disabled {
    color: #a0a4aa;
    border-color: #e2e5ea;
}
#welcomeStatus {
    color: #c0392b;
    font-size: 12px;
}
"""

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #dcdcdc;
}
QMainWindow, QDialog {
    background-color: #1e1e1e;
}
QLabel {
    background-color: transparent;
}
QMenuBar {
    background-color: #2a2a2a;
    color: #dcdcdc;
}
QMenuBar::item {
    background-color: #1f1f1f;
    color: #dcdcdc;
    padding: 4px 12px;
}
QMenuBar::item:selected {
    background-color: #151515;
}
QMenu {
    background-color: #2a2a2a;
    color: #dcdcdc;
    border: 1px solid #3c3c3c;
}
QMenu::item {
    padding: 5px 22px;
}
QMenu::item:selected {
    background-color: #3a7bd5;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #3c3c3c;
    margin: 4px 8px;
}
QPushButton {
    background-color: #333333;
    color: #dcdcdc;
    border: 1px solid #4a4a4a;
    padding: 5px 12px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #3d3d3d;
}
QPushButton:pressed {
    background-color: #2b2b2b;
}
QPushButton:disabled {
    color: #777777;
    border-color: #3a3a3a;
}
QLineEdit, QPlainTextEdit, QTextBrowser, QTableWidget, QComboBox {
    background-color: #252526;
    color: #dcdcdc;
    border: 1px solid #3c3c3c;
    border-radius: 3px;
    selection-background-color: #3a7bd5;
    selection-color: #ffffff;
}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border-color: #3a7bd5;
}
QComboBox QAbstractItemView {
    background-color: #252526;
    color: #dcdcdc;
    selection-background-color: #3a7bd5;
}
QTabWidget::pane {
    border: 1px solid #3c3c3c;
}
QTabBar::tab {
    background-color: #2a2a2a;
    color: #b0b0b0;
    padding: 6px 14px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
}
QHeaderView::section {
    background-color: #2a2a2a;
    color: #dcdcdc;
    border: 1px solid #3c3c3c;
    padding: 4px;
}
QProgressBar {
    background-color: #252526;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    text-align: center;
    color: #dcdcdc;
}
QProgressBar::chunk {
    background-color: #3a7bd5;
    border-radius: 3px;
}
QSplitter::handle {
    background-color: #3c3c3c;
}
QScrollBar:vertical, QScrollBar:horizontal {
    background-color: #2a2a2a;
    border: none;
}
QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #4a4a4a;
    border-radius: 4px;
    min-height: 24px;
    min-width: 24px;
}
QScrollBar::add-line, QScrollBar::sub-line {
    height: 0px;
    width: 0px;
}
#moduleRail {
    background-color: #202124;
    border-right: 1px solid #34373b;
}
#moduleRail QToolButton {
    background-color: transparent;
    border: none;
    border-radius: 12px;
    color: #b6bac1;
    font-size: 12px;
    padding: 4px 6px;
}
#moduleRail QToolButton:hover {
    background-color: #2f3237;
}
#moduleRail QToolButton:checked {
    background-color: #3a3e44;
    color: #f0f0f0;
}
#moduleRail QToolButton::menu-indicator {
    image: none;
}
QSlider::groove:horizontal {
    height: 4px;
    background-color: #4a4a4a;
    border-radius: 2px;
}
QSlider::sub-page:horizontal {
    background-color: #3a7bd5;
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
    background-color: #3a7bd5;
}
QSlider::handle:horizontal:hover {
    background-color: #4a8ae0;
}
#boardEditBar QToolButton {
    background-color: #d9dce1;
    border: 1px solid #4a4a4a;
    border-radius: 4px;
    padding: 1px;
}
#boardEditBar QToolButton:hover {
    background-color: #eef1f5;
}
#boardEditBar QToolButton:checked {
    background-color: #9fc3ef;
    border-color: #3a7bd5;
}
#boardEditBar QLabel {
    color: #b8bbc0;
}
#welcomePage {
    background-color: #1a1b1d;
}
#welcomeCard {
    background-color: #26282b;
    border: 1px solid #34373b;
    border-radius: 16px;
}
#welcomeTitle {
    color: #f2f3f5;
    font-size: 24px;
    font-weight: 600;
}
#welcomeSubtitle {
    color: #9aa0a6;
    font-size: 13px;
}
#welcomeFieldLabel {
    color: #b8bcc2;
    font-size: 12px;
    font-weight: 600;
}
#welcomePage QCheckBox {
    background-color: transparent;
}
#welcomePage QLineEdit, #welcomePage QComboBox {
    background-color: #202124;
    color: #e6e6e6;
    border: 1px solid #3c3c3c;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
}
#welcomePage QLineEdit:focus, #welcomePage QComboBox:focus {
    border: 1px solid #3a7bd5;
}
#welcomePrimary {
    background-color: #3a7bd5;
    color: #ffffff;
    border: 1px solid #3a7bd5;
    border-radius: 8px;
    padding: 9px 16px;
    font-weight: 600;
}
#welcomePrimary:hover {
    background-color: #4a8ae0;
    border-color: #4a8ae0;
}
#welcomePrimary:pressed {
    background-color: #2f6bbd;
    border-color: #2f6bbd;
}
#welcomePrimary:disabled {
    background-color: #33465e;
    border-color: #33465e;
    color: #8fa3ba;
}
#welcomeSecondary {
    background-color: #2f3237;
    color: #e6e6e6;
    border: 1px solid #45484d;
    border-radius: 8px;
    padding: 9px 16px;
}
#welcomeSecondary:hover {
    background-color: #3a3e44;
}
#welcomeSecondary:pressed {
    background-color: #2a2d31;
}
#welcomeSecondary:disabled {
    color: #6a6e73;
    border-color: #3a3d41;
}
#welcomeStatus {
    color: #ff6b6b;
    font-size: 12px;
}
"""


def apply_theme(app, theme):
    app.setStyleSheet(DARK_STYLESHEET if theme == DARK else LIGHT_STYLESHEET)
