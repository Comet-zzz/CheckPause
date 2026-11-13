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

# Row tints for the move list: the current move gets a stronger neutral wash
# than the row under the cursor. RGBA tuples so the tint sits lightly on the
# panel surface; the delegate adds a thin accent bar to the current row.
MOVE_ROW_COLORS = {
    LIGHT: {"current": (16, 20, 26, 30), "hover": (16, 20, 26, 14)},
    DARK: {"current": (255, 255, 255, 38), "hover": (255, 255, 255, 18)},
}

# Colours for the game-review move labels shown after each move. The label text
# is English in every language, so these are plain hex values, not tokens.
MOVE_LABEL_COLORS = {
    "Brilliant": "#26c2a3",
    "Great": "#5c8bb0",
    "Best": "#81b64c",
    "Excellent": "#81b64c",
    "Good": "#95b776",
    "Book": "#a88865",
    "Forced": "#9aa7b0",
    "Only move": "#9aa7b0",
    "Inaccuracy": "#f7c631",
    "Mistake": "#ffa459",
    "Miss": "#ee6b55",
    "Blunder": "#ca3431",
}

# The vector mark drawn after each move (see assets/icons). Every label uses a
# drawn SVG, tinted with the colour above, so the list never relies on colour
# alone.
MOVE_LABEL_ICONS = {
    "Brilliant": "review_brilliant",
    "Great": "review_great",
    "Best": "review_best",
    "Excellent": "review_excellent",
    "Good": "review_good",
    "Book": "book",
    "Forced": "review_forced",
    "Only move": "review_only_move",
    "Inaccuracy": "review_inaccuracy",
    "Mistake": "review_mistake",
    "Miss": "review_miss",
    "Blunder": "review_blunder",
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
        "history_selected_bg": "rgba(53, 102, 245, 0.12)",
        "history_selected_text": "#2f5bd7",
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
        "success": "#2f7d4f",
        "success_soft": "rgba(47, 125, 79, 0.10)",
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
        "history_selected_bg": "rgba(96, 140, 255, 0.22)",
        "history_selected_text": "#b8ccff",
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
        "success": "#7cc79a",
        "success_soft": "rgba(124, 199, 154, 0.12)",
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
QComboBox QAbstractItemView::item {
    min-height: 22px;
    padding: 4px 8px;
    border-radius: 4px;
}
QComboBox QAbstractItemView::item:hover {
    background-color: $hover;
}
QComboBox QAbstractItemView::item:selected {
    background-color: $menu_sel_bg;
    color: $menu_sel_text;
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
    outline: none;
}
QTableWidget::item {
    padding: 4px 6px;
}
QTableWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
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
QTreeWidget {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 10px;
    padding: 4px;
    outline: none;
}
QTreeWidget::item {
    padding: 6px 4px;
    border-radius: 6px;
}
QTreeWidget::item:hover {
    background-color: $hover;
}
QTreeWidget::item:selected {
    background-color: $accent_soft;
    color: $text;
}
QTreeWidget::branch {
    background: transparent;
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
#setupTitle {
    font-size: 15px;
    font-weight: 600;
}
#fieldLabel {
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
}
#segmentedControl {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
}
#segmentedControl QPushButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: $text_muted;
    min-height: 18px;
}
#segmentedControl QPushButton:hover {
    background-color: $hover;
    color: $text;
}
#segmentedControl QPushButton:checked {
    background-color: $surface;
    border-color: $border;
    color: $text;
    font-weight: 600;
}
#segmentedControl QPushButton:focus {
    border-color: $accent;
}
#positionCard {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 10px;
}
#positionName {
    font-size: 14px;
    font-weight: 600;
}
#positionMeta {
    color: $text_muted;
    font-size: 12px;
}
#previewCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#pickerName {
    font-size: 18px;
    font-weight: 600;
}
#pickerMeta {
    color: $text_muted;
    font-size: 12px;
}
#movesCard {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 10px;
}
#movesText {
    color: $text_muted;
    font-size: 12px;
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
#historyScroll {
    background: transparent;
    border: none;
}
#historyGroupLabel {
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 6px 3px 6px;
}
#historyRow {
    background: transparent;
    border-radius: 8px;
}
#historyRow[selecting="true"]:hover {
    background-color: $hover;
}
#historyRow[selected="true"] {
    background-color: $history_selected_bg;
}
#historyRow[selected="true"]:hover {
    background-color: $history_selected_bg;
}
#historyDate {
    color: $text;
    font-size: 13px;
}
#historyPerformance {
    color: $text_muted;
    font-size: 12px;
}
#historyRow[selected="true"] #historyDate,
#historyRow[selected="true"] #historyPerformance {
    color: $history_selected_text;
}
QCheckBox#historyCheck::indicator {
    width: 18px;
    height: 18px;
    border-radius: 9px;
}
QCheckBox#historyCheck::indicator:checked {
    background-color: $history_selected_text;
    border-color: $history_selected_text;
}
QTabWidget#sidePanelTabs::pane {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
QTabWidget#sidePanelTabs QTabBar::tab {
    background: transparent;
    color: $text_muted;
    padding: 7px 18px;
    margin: 0 2px;
    border: 1px solid transparent;
    border-radius: 8px;
}
QTabWidget#sidePanelTabs QTabBar::tab:hover {
    background-color: $hover;
    color: $text;
}
QTabWidget#sidePanelTabs QTabBar::tab:selected {
    background-color: $accent_soft;
    color: $text;
    font-weight: 600;
}
QTableWidget#moveTable {
    background: transparent;
    border: none;
}
QTableWidget#moveTable::item {
    border: none;
    padding: 0px;
}
#analysisTools QPushButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 4px 8px;
    min-height: 18px;
}
#analysisTools QPushButton:hover {
    background-color: $hover;
    border-color: $border;
}
#analysisTools QPushButton:pressed {
    background-color: $pressed;
}
#analysisTools QPushButton:disabled {
    background: transparent;
}
#summaryCard {
    background-color: $accent_soft;
    border: 1px solid $border;
    border-radius: 10px;
}
#summaryCard QLabel#accuracyLabel {
    color: $text;
    font-size: 16px;
    font-weight: 700;
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
#aboutTitle {
    color: $text;
    font-size: 22px;
    font-weight: 600;
}
#aboutBody {
    color: $text;
    font-size: 13px;
}
#aboutCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 16px;
}
#aboutDivider {
    background-color: $border;
    border: none;
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
#learnPage {
    background: transparent;
}
#learnHeaderTitle {
    font-size: 24px;
    font-weight: 700;
}
#learnHeaderSubtitle {
    color: $text_muted;
    font-size: 13px;
}
#learnHeaderProgress {
    color: $text_muted;
    font-size: 12px;
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 10px;
    padding: 5px 12px;
}
#learnSectionLabel {
    color: $text_muted;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 2px 2px 2px;
}
#learnCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 14px;
}
#learnCard:hover {
    background-color: $surface_alt;
    border-color: $border_strong;
}
#learnCardTitle {
    font-size: 16px;
    font-weight: 600;
}
#learnCardSubtitle {
    color: $text_muted;
    font-size: 12px;
}
#learnBadge {
    border-radius: 9px;
    padding: 3px 9px;
    font-size: 11px;
    font-weight: 600;
}
#learnBadge[status="done"] {
    background-color: $accent;
    color: $accent_text;
}
#learnBadge[status="active"] {
    background-color: $accent_soft;
    color: $text;
}
#learnBadge[status="new"] {
    background-color: transparent;
    color: $text_muted;
    border: 1px solid $border;
}
#learnBackButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 5px 8px;
    color: $text_muted;
}
#learnBackButton:hover {
    background-color: $hover;
    border-color: $border;
    color: $text;
}
#learnLessonTitle {
    font-size: 19px;
    font-weight: 700;
}
#learnLessonSubtitle {
    color: $text_muted;
    font-size: 12px;
}
#learnStepLabel {
    color: $text_muted;
    font-size: 12px;
}
#learnProgress {
    background-color: $accent_soft;
    border: none;
    border-radius: 3px;
    max-height: 6px;
    min-height: 6px;
}
#learnProgress::chunk {
    background-color: $accent;
    border-radius: 3px;
}
#learnPanel {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 14px;
}
#learnNote {
    color: $text_muted;
    font-size: 13px;
}
#learnInstruction {
    font-size: 15px;
    font-weight: 600;
}
#learnFeedback {
    color: $text_muted;
    font-size: 12px;
}
#learnFeedback[state="error"] {
    color: $danger;
}
#learnFeedback[state="success"] {
    color: $accent;
    font-weight: 600;
}
#learnHintButton, #learnRetryButton {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 7px 14px;
    color: $text_muted;
}
#learnHintButton:hover, #learnRetryButton:hover {
    background-color: $hover;
    color: $text;
}
#learnPrimaryButton {
    background-color: $accent;
    color: $accent_text;
    border: 1px solid $accent;
    border-radius: 8px;
    padding: 8px 22px;
    font-weight: 600;
}
#learnPrimaryButton:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
#learnPrimaryButton:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}
#puzzleScroll {
    background: transparent;
    border: none;
}
#puzzleHub, #puzzleProfile, #puzzleLibrary, #puzzleTrain {
    background: transparent;
}
#puzzleHeaderTitle {
    font-size: 22px;
    font-weight: 700;
}
#puzzleHero {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 14px;
}
#puzzleHeroTitle {
    font-size: 22px;
    font-weight: 700;
}
#puzzleHeroSub {
    color: $text_muted;
    font-size: 13px;
}
#puzzleHeroRating {
    font-size: 30px;
    font-weight: 700;
}
#puzzleHeroRatingCaption {
    color: $text_muted;
    font-size: 11px;
    font-weight: 600;
}
#puzzleHeroText {
    color: $text_muted;
    font-size: 13px;
}
#puzzlePrimaryButton {
    background-color: $accent;
    color: $accent_text;
    border: 1px solid $accent;
    border-radius: 8px;
    padding: 8px 22px;
    font-weight: 600;
}
#puzzlePrimaryButton:hover {
    background-color: $accent_hover;
    border-color: $accent_hover;
}
#puzzlePrimaryButton:pressed {
    background-color: $accent_pressed;
    border-color: $accent_pressed;
}
#puzzlePrimaryButton:disabled {
    background-color: $accent_off_bg;
    color: $accent_off_text;
    border-color: $border;
}
#puzzleSecondaryButton, #puzzleGhostButton {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 7px 14px;
    color: $text_muted;
}
#puzzleGhostButton {
    background: transparent;
    border-color: transparent;
}
#puzzleSecondaryButton:hover, #puzzleGhostButton:hover {
    background-color: $hover;
    color: $text;
}
#puzzleSecondaryButton:disabled, #puzzleGhostButton:disabled {
    color: $text_disabled;
    border-color: $border;
}
#puzzleIconButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 5px;
}
#puzzleIconButton:hover {
    background-color: $hover;
}
#puzzleIconButton:checked {
    background-color: $surface_alt;
    border-color: $border;
}
#puzzleIconButton:disabled {
    background: transparent;
}
#puzzleVoteButton {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 5px;
}
#puzzleVoteButton:hover {
    background-color: $hover;
}
#puzzleVoteButton:checked {
    background-color: $history_selected_bg;
}
#puzzleLinkButton {
    background: transparent;
    border: none;
    color: $text_muted;
    font-size: 13px;
    padding: 4px 2px;
}
#puzzleLinkButton:hover {
    color: $text;
}
#puzzleLinkButton:disabled {
    color: $text_disabled;
}
#puzzleSectionLabel {
    color: $text_muted;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 2px 2px 2px;
}
#puzzleStatCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleStatValue {
    font-size: 20px;
    font-weight: 600;
}
#puzzleStatCaption {
    color: $text_muted;
    font-size: 12px;
}
#puzzleActionCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 0;
    text-align: left;
}
#puzzleActionCard:hover {
    background-color: $surface_alt;
    border-color: $border_strong;
}
#puzzleActionCard:pressed {
    background-color: $surface_alt;
    border-color: $border_strong;
}
#puzzleActionCard:disabled {
    background-color: $surface_alt;
}
#puzzleActionCard:disabled QLabel {
    color: $text_disabled;
}
#puzzleActionArrow {
    color: $text_muted;
    font-size: 14px;
}
#puzzleCollectionCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 14px 16px;
    text-align: left;
}
#puzzleCollectionCard:hover {
    background-color: $surface_alt;
    border-color: $border_strong;
}
#puzzleCollectionName {
    font-size: 14px;
    font-weight: 600;
}
#puzzleCollectionMeta {
    color: $text_muted;
    font-size: 12px;
}
#puzzleCollectionBar {
    background-color: $accent_soft;
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}
#puzzleCollectionBar::chunk {
    background-color: $history_selected_text;
    border-radius: 2px;
}
#puzzleEmptyLabel {
    color: $text_muted;
    font-size: 13px;
    padding: 6px 2px;
}
#puzzleRatingPill {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 9px;
    padding: 3px 9px;
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
}
#puzzleNotice {
    color: $text_muted;
    font-size: 12px;
    padding: 2px 2px;
}
#puzzleModeLabel {
    font-size: 20px;
    font-weight: 600;
}
#puzzleCounterLabel {
    color: $text_muted;
    font-size: 12px;
}
#puzzleStatusTitle {
    font-size: 17px;
    font-weight: 600;
}
#puzzleStatusSub {
    color: $text_muted;
    font-size: 13px;
}
#puzzleResultDetail {
    color: $text_muted;
    font-size: 13px;
}
#puzzleLibraryCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleLibraryInfo {
    font-size: 16px;
    font-weight: 600;
}
#puzzleLibraryStatus {
    color: $text_muted;
    font-size: 12px;
}
#puzzleProfileScope {
    color: $text_muted;
    font-size: 12px;
}
#puzzleLibraryList, #puzzleRecentList {
    background: transparent;
    border: none;
    padding: 2px;
}
#puzzleLibraryList::item, #puzzleRecentList::item {
    border-radius: 8px;
    padding: 10px 12px;
}
#puzzleLibraryList::item:hover {
    background-color: $surface_alt;
}
#puzzleLibraryList::item:selected {
    background-color: $history_selected_bg;
    color: $history_selected_text;
}
#puzzleLibraryBar {
    background-color: $accent_soft;
    border: none;
    border-radius: 3px;
    min-height: 6px;
    max-height: 6px;
}
#puzzleLibraryBar::chunk {
    background-color: $history_selected_text;
    border-radius: 3px;
}
#puzzleRange {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
    padding: 5px 10px;
    color: $text;
}
#puzzleRangeGroup {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 8px;
}
#puzzleRangeButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 4px 9px;
    color: $text_muted;
    font-size: 12px;
}
#puzzleRangeButton:hover {
    color: $text;
}
#puzzleRangeButton:checked {
    background-color: $accent_soft;
    color: $text;
    font-weight: 600;
}
#puzzleThemeBox {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleThemeLabel {
    color: $text_muted;
    font-size: 13px;
}
#puzzleThemeBar {
    background-color: $accent_soft;
    border: none;
    border-radius: 3px;
}
#puzzleThemeBar::chunk {
    background-color: $accent;
    border-radius: 3px;
}
#puzzleTrainSide {
    background: transparent;
    border: none;
    border-radius: 0;
}
#puzzleMoveBox,
#puzzleStatusCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleMoveBox QLabel#puzzleEmptyLabel {
    padding: 12px;
}
QWidget#puzzleMoveList QTableWidget {
    background: transparent;
    border: none;
    font-size: 13px;
}
#puzzleTrainMeta,
#puzzleLadderValue {
    color: $history_selected_text;
    background-color: $history_selected_bg;
    border-radius: 7px;
    padding: 3px 8px;
    font-size: 16px;
    font-weight: 700;
}
#puzzleLadderDelta {
    font-size: 12px;
    font-weight: 600;
}
#puzzleLadderDelta[sign="up"] {
    color: $success;
}
#puzzleLadderDelta[sign="down"] {
    color: $danger;
}
#puzzleStatusCard[state="correct"] #puzzleStatusTitle,
#puzzleStatusCard[state="solved"] #puzzleStatusTitle {
    color: $success;
}
#puzzleStatusCard[state="wrong"] #puzzleStatusTitle {
    color: $danger;
}
#puzzleResultMeta {
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
}
#puzzleStatusCard[state="solved"] #puzzleResultMeta {
    color: $success;
}
#puzzleModeCard {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleModeTitle {
    font-size: 15px;
    font-weight: 600;
}
#puzzleModeText {
    color: $text_muted;
    font-size: 12px;
}
#puzzleModeCard QPushButton#puzzleSecondaryButton {
    padding: 6px 14px;
}
#puzzleSettings {
    background-color: $surface_alt;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleRatingHero {
    background-color: $accent_soft;
    border: 1px solid $border_strong;
    border-radius: 12px;
}
#puzzleRatingCaption {
    color: $text_muted;
    font-size: 12px;
    font-weight: 600;
}
#puzzleRatingValue {
    font-size: 32px;
    font-weight: 600;
}
#puzzleRatingSub {
    color: $text_muted;
    font-size: 12px;
}
#puzzleThemesBox {
    background-color: $surface;
    border: 1px solid $border;
    border-radius: 12px;
}
#puzzleThemesHint {
    color: $text_muted;
    font-size: 12px;
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


def token_color(theme, name):
    return _TOKENS.get(theme, _TOKENS[LIGHT])[name]


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


def muted_color(theme):
    """The muted text tint, for de-emphasised list content."""
    return _TOKENS.get(theme, _TOKENS[LIGHT])["text_muted"]


def accent_color(theme):
    """The selected/accent tint used by lists and current-row marks."""
    return _TOKENS.get(theme, _TOKENS[LIGHT])["history_selected_text"]
