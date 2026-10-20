"""Searchable opening picker with a grouped tree and a board preview."""

import os
from collections import Counter

import chess
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from checkpause.assets import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    PIECE_SETS,
)
from checkpause.core.openings import opening_display_name, opening_san
from checkpause.gui.widgets.board.constants import LAST_MOVE_RGBA
from checkpause.i18n import t
from checkpause.resources import resource_path

PREVIEW_SIZE = 300
ROLE_INDEX = int(Qt.ItemDataRole.UserRole)
ROLE_SEARCH = ROLE_INDEX + 1


class _OpeningPreview(QWidget):
    """A small read-only board showing where an opening ends up."""

    def __init__(self, piece_set=DEFAULT_PIECE_SET, board_theme=DEFAULT_BOARD_THEME, parent=None):
        super().__init__(parent)
        self._piece_set = piece_set if piece_set in PIECE_SETS else DEFAULT_PIECE_SET
        self._board_theme = board_theme if board_theme in BOARD_THEMES else DEFAULT_BOARD_THEME
        self._board = chess.Board()
        self._last_move = None
        self._renderers = {}
        self.setFixedSize(PREVIEW_SIZE, PREVIEW_SIZE)

    def set_position(self, board, last_move=None):
        self._board = board.copy()
        self._last_move = last_move
        self.update()

    def _piece_renderer(self, piece):
        code = ("w" if piece.color == chess.WHITE else "b") + piece.symbol().upper()
        if code not in self._renderers:
            path = resource_path("assets", "pieces", self._piece_set, code + ".svg")
            renderer = None
            if os.path.isfile(path):
                renderer = QSvgRenderer(path)
                if not renderer.isValid():
                    renderer = None
            self._renderers[code] = renderer
        return self._renderers[code]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        side = min(self.width(), self.height())
        x0 = (self.width() - side) / 2.0
        y0 = (self.height() - side) / 2.0
        cell = side / 8.0
        light_color, dark_color = BOARD_THEMES[self._board_theme]
        highlighted = set()
        if self._last_move is not None:
            highlighted.add(self._last_move.from_square)
            highlighted.add(self._last_move.to_square)

        for row in range(8):
            rank = 7 - row
            for file_index in range(8):
                square = chess.square(file_index, rank)
                rect = QRectF(
                    x0 + file_index * cell,
                    y0 + row * cell,
                    cell,
                    cell,
                )
                is_light = (file_index + rank) % 2 == 1
                painter.fillRect(rect, QColor(light_color if is_light else dark_color))
                if square in highlighted:
                    painter.fillRect(rect, QColor(*LAST_MOVE_RGBA))
                piece = self._board.piece_at(square)
                if piece is None:
                    continue
                renderer = self._piece_renderer(piece)
                if renderer is None:
                    continue
                size = cell * 0.88
                painter.save()
                painter.translate(rect.center())
                painter.translate(-size / 2.0, -size / 2.0)
                renderer.render(painter, QRectF(0, 0, size, size))
                painter.restore()


class OpeningPicker(QDialog):
    """Pick a bundled opening by family, with search and a live preview."""

    def __init__(
        self,
        parent,
        openings,
        language,
        piece_set=DEFAULT_PIECE_SET,
        board_theme=DEFAULT_BOARD_THEME,
        selected_name=None,
    ):
        super().__init__(parent)
        self._openings = list(openings)
        self._language = language
        self._selected_index = None
        self._leaf_items = []
        self._family_items = []
        self._category_items = []
        self._items_by_index = {}

        self.setWindowTitle(t("opening_picker_title", language))
        self.setMinimumSize(860, 600)
        self.resize(900, 620)
        self.setSizeGripEnabled(False)

        self._search = QLineEdit()
        self._search.setPlaceholderText(t("opening_search_placeholder", language))
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)

        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setAnimated(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._tree.currentItemChanged.connect(self._on_current_changed)
        self._tree.itemDoubleClicked.connect(self._on_item_activated)
        self._tree.itemActivated.connect(self._on_item_activated)

        self._preview = _OpeningPreview(piece_set, board_theme)
        preview_card = QWidget()
        preview_card.setObjectName("previewCard")
        preview_layout = QVBoxLayout(preview_card)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.addWidget(self._preview, 0, Qt.AlignmentFlag.AlignCenter)

        self._name_label = QLabel()
        self._name_label.setObjectName("pickerName")
        self._name_label.setWordWrap(True)
        self._subtitle_label = QLabel()
        self._subtitle_label.setObjectName("pickerMeta")
        self._subtitle_label.setWordWrap(True)

        moves_caption = QLabel(t("opening_moves_label", language))
        moves_caption.setObjectName("fieldLabel")
        self._moves_label = QLabel()
        self._moves_label.setObjectName("movesText")
        self._moves_label.setWordWrap(True)
        self._moves_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        moves_card = QWidget()
        moves_card.setObjectName("movesCard")
        moves_layout = QVBoxLayout(moves_card)
        moves_layout.setContentsMargins(12, 10, 12, 10)
        moves_layout.setSpacing(4)
        moves_layout.addWidget(moves_caption)
        moves_layout.addWidget(self._moves_label)

        self._buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self._ok_button = self._buttons.button(QDialogButtonBox.StandardButton.Ok)
        self._ok_button.setText(t("opening_picker_use", language))
        self._ok_button.setObjectName("primaryButton")
        self._ok_button.setEnabled(False)
        self._buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(t("btn_no", language))
        self._buttons.accepted.connect(self.accept)
        self._buttons.rejected.connect(self.reject)

        left = QVBoxLayout()
        left.setSpacing(10)
        left.addWidget(self._search)
        left.addWidget(self._tree, 1)

        right = QVBoxLayout()
        right.setSpacing(10)
        right.addWidget(preview_card, 0, Qt.AlignmentFlag.AlignHCenter)
        right.addWidget(self._name_label)
        right.addWidget(self._subtitle_label)
        right.addWidget(moves_card)
        right.addStretch(1)
        right.addWidget(self._buttons)

        content = QHBoxLayout()
        content.setSpacing(16)
        content.addLayout(left, 1)
        content.addLayout(right, 1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addLayout(content)

        self._build_tree()
        self._select_initial(selected_name)
        self._search.setFocus()

    @property
    def selected_opening(self):
        if self._selected_index is None:
            return None
        return self._openings[self._selected_index]

    def _build_tree(self):
        self._tree.clear()
        self._leaf_items = []
        self._family_items = []
        self._category_items = []
        self._items_by_index = {}
        families = {}
        categories = {}
        family_counts = Counter(
            (
                opening.get("category") or "other",
                opening.get("family") or opening["name"],
            )
            for opening in self._openings
        )

        for index, opening in enumerate(self._openings):
            category = opening.get("category") or "other"
            category_item = categories.get(category)
            if category_item is None:
                category_item = QTreeWidgetItem([t("opening_group_" + category, self._language)])
                category_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                category_item.setData(0, ROLE_INDEX, None)
                font = category_item.font(0)
                font.setBold(True)
                category_item.setFont(0, font)
                self._tree.addTopLevelItem(category_item)
                self._category_items.append(category_item)
                categories[category] = category_item

            family = opening.get("family") or opening["name"]
            family_key = (category, family)
            if family_counts[family_key] > 1:
                family_item = families.get(family_key)
                if family_item is None:
                    family_item = QTreeWidgetItem([self._family_label(opening)])
                    family_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                    family_item.setData(0, ROLE_INDEX, None)
                    category_item.addChild(family_item)
                    self._family_items.append(family_item)
                    families[family_key] = family_item
                parent = family_item
                label = self._variation_label(opening)
            else:
                parent = category_item
                label = opening_display_name(opening, self._language)

            item = QTreeWidgetItem([label])
            item.setData(0, ROLE_INDEX, index)
            item.setData(0, ROLE_SEARCH, self._search_text(opening))
            item.setToolTip(0, opening["name"])
            parent.addChild(item)
            self._leaf_items.append(item)
            self._items_by_index[index] = item

        for category_item in self._category_items:
            category_item.setExpanded(True)

    def _family_label(self, opening):
        if self._language == "en-US":
            return opening.get("family") or opening["name"]
        return opening.get("family_zh") or opening.get("family") or opening["name"]

    def _variation_label(self, opening):
        if self._language == "en-US":
            return opening.get("variation") or opening["name"]
        return (
            opening.get("variation_zh")
            or opening.get("variation")
            or opening.get("name_zh")
            or opening["name"]
        )

    def _search_text(self, opening):
        category = opening.get("category") or "other"
        parts = [
            opening.get("name", ""),
            opening.get("name_zh", ""),
            opening.get("family", ""),
            opening.get("family_zh", ""),
            opening.get("variation", ""),
            opening.get("variation_zh", ""),
            t("opening_group_" + category, self._language),
        ]
        return " ".join(part for part in parts if part).lower()

    def _select_initial(self, selected_name):
        index = None
        if selected_name:
            for candidate, opening in enumerate(self._openings):
                if opening["name"] == selected_name:
                    index = candidate
                    break
        if index is None and self._leaf_items:
            index = self._leaf_items[0].data(0, ROLE_INDEX)
        if index is not None:
            self._select_index(int(index))

    def _select_index(self, index):
        item = self._items_by_index.get(index)
        if item is None:
            return
        self._tree.scrollToItem(item)
        if self._tree.currentItem() is item:
            self._show_opening(index)
            return
        self._tree.setCurrentItem(item)

    def _select_first_visible(self):
        for item in self._leaf_items:
            if item.isHidden():
                continue
            self._tree.scrollToItem(item)
            index = item.data(0, ROLE_INDEX)
            if self._tree.currentItem() is item:
                self._show_opening(int(index))
            else:
                self._tree.setCurrentItem(item)
            return True
        self._show_empty()
        return False

    def _show_empty(self):
        self._selected_index = None
        self._ok_button.setEnabled(False)
        self._name_label.setText(t("opening_no_results", self._language))
        self._subtitle_label.clear()
        self._moves_label.clear()
        self._preview.set_position(chess.Board())

    def _on_search(self, text):
        query = text.strip().lower()
        for item in self._leaf_items:
            item.setHidden(bool(query) and query not in item.data(0, ROLE_SEARCH))
        for family_item in self._family_items:
            visible = any(
                not family_item.child(row).isHidden() for row in range(family_item.childCount())
            )
            family_item.setHidden(not visible)
            if query:
                family_item.setExpanded(visible)
        for category_item in self._category_items:
            visible = any(
                not category_item.child(row).isHidden() for row in range(category_item.childCount())
            )
            category_item.setHidden(not visible)
            if query:
                category_item.setExpanded(visible)
        if query:
            self._select_first_visible()
            return
        for family_item in self._family_items:
            family_item.setExpanded(False)
        for category_item in self._category_items:
            category_item.setExpanded(True)
        if self._selected_index is None:
            self._select_first_visible()
            return
        item = self._items_by_index.get(self._selected_index)
        if item is None:
            return
        parent = item.parent()
        if parent is not None and parent.parent() is not None:
            parent.setExpanded(True)
        self._tree.scrollToItem(item)

    def _on_current_changed(self, current, _previous):
        if current is None:
            return
        index = current.data(0, ROLE_INDEX)
        if index is None:
            if current.childCount():
                current.setExpanded(True)
                for row in range(current.childCount()):
                    child = current.child(row)
                    if not child.isHidden():
                        self._tree.setCurrentItem(child)
                        break
            return
        self._show_opening(int(index))

    def _show_opening(self, index):
        opening = self._openings[index]
        board = chess.Board()
        last_move = None
        for move in opening["moves"]:
            last_move = move
            board.push(move)
        self._preview.set_position(board, last_move)
        self._name_label.setText(opening_display_name(opening, self._language))
        if self._language == "en-US":
            category = opening.get("category") or "other"
            self._subtitle_label.setText(t("opening_group_" + category, self._language))
        else:
            self._subtitle_label.setText(opening["name"])
        self._moves_label.setText(opening_san(opening))
        self._selected_index = index
        self._ok_button.setEnabled(True)

    def _on_item_activated(self, item, _column):
        if item.data(0, ROLE_INDEX) is not None:
            self.accept()


def choose_opening_dialog(
    parent,
    openings,
    language,
    piece_set=DEFAULT_PIECE_SET,
    board_theme=DEFAULT_BOARD_THEME,
    selected_name=None,
):
    """Show the picker and return the chosen opening, or None."""
    dialog = OpeningPicker(
        parent,
        openings,
        language,
        piece_set=piece_set,
        board_theme=board_theme,
        selected_name=selected_name,
    )
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.selected_opening
    return None
