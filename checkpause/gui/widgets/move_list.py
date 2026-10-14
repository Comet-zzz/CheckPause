import io

import chess
import chess.pgn
from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QStyle,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from checkpause.gui.icons import action_icon
from checkpause.gui.theme import (
    LIGHT,
    MOVE_LABEL_COLORS,
    MOVE_LABEL_ICONS,
    MOVE_ROW_COLORS,
    muted_color,
)

_MARK_PIXELS = 16
_MARK_GAP = 14
_NUMBER_MARGIN = 6
_MOVE_MARGIN = 12
_PILL_PAD = 10
_ROW_HEIGHT = 34


class _MoveDelegate(QStyledItemDelegate):
    """Paints one cell of the move list.

    The move numbers are de-emphasised, the current move gets a soft rounded
    wash, the row under the cursor a lighter one, and the review mark is drawn
    just after the move text so it reads as belonging to that move.
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._owner = owner

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), _ROW_HEIGHT)

    def paint(self, painter, option, index):
        owner = self._owner
        rect = option.rect
        column = index.column()
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        mark = index.data(Qt.ItemDataRole.UserRole) if column != 0 else None
        current = owner.is_current_cell(index.row(), column)

        tint = None
        if current:
            tint = owner.row_color("current")
        elif option.state & QStyle.StateFlag.State_MouseOver:
            tint = owner.row_color("hover")

        font = QFont(option.font)
        if current:
            font.setBold(True)
        metrics = QFontMetrics(font)

        painter.save()
        if tint is not None:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(tint)
            painter.drawRoundedRect(self._pill_rect(rect, column, text, mark, metrics), 7, 7)

        painter.setFont(font)
        if column == 0:
            painter.setPen(owner.number_color())
            text_rect = rect.adjusted(_NUMBER_MARGIN, 0, -6, 0)
            align = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        else:
            painter.setPen(option.palette.color(QPalette.ColorRole.Text))
            text_rect = rect.adjusted(_MOVE_MARGIN, 0, -2, 0)
            align = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        painter.drawText(text_rect, align, text)

        if mark:
            icon = owner.label_icon(mark)
            if icon is not None:
                x = rect.left() + _MOVE_MARGIN + metrics.horizontalAdvance(text) + _MARK_GAP
                y = rect.center().y() - _MARK_PIXELS // 2
                icon.paint(painter, QRect(x, y, _MARK_PIXELS, _MARK_PIXELS))
        painter.restore()

    def _pill_rect(self, rect, column, text, mark, metrics):
        """The rounded wash behind one row, sized to its content."""
        if column == 0:
            return rect.adjusted(3, 2, -3, -2)
        width = metrics.horizontalAdvance(text)
        if mark:
            width += _MARK_GAP + _MARK_PIXELS
        left = rect.left() + _MOVE_MARGIN - _PILL_PAD
        return QRect(left, rect.top() + 2, width + _PILL_PAD * 2, rect.height() - 4)


class MoveListWidget(QWidget):
    ply_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = LIGHT
        self._ply_count = 0
        self._current = 0
        self._offset = 0
        self._first_number = 1
        self._sans = []
        self._labels = []

        self._table = QTableWidget(0, 3)
        self._table.setObjectName("moveTable")
        self._table.setHorizontalHeaderLabels(["#", "W", "B"])
        self._table.horizontalHeader().setVisible(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self._table.verticalHeader().setDefaultSectionSize(_ROW_HEIGHT)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._table.setMouseTracking(True)
        self._table.viewport().setMouseTracking(True)
        self._table.viewport().setCursor(Qt.CursorShape.PointingHandCursor)
        self._table.setItemDelegate(_MoveDelegate(self))
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.cellClicked.connect(self._on_click)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._table)

    def set_moves(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None:
            return False
        start = game.board()
        board = start.copy()
        sans = []
        for move in game.mainline_moves():
            sans.append(board.san(move))
            board.push(move)
        if not sans:
            return False

        self._offset = 0 if start.turn == chess.WHITE else 1
        self._first_number = start.fullmove_number
        self._ply_count = len(sans)
        self._sans = sans
        self._labels = []
        rows = (self._ply_count + 1 + self._offset) // 2
        self._table.clearContents()
        self._table.setRowCount(rows)
        for ply, san in enumerate(sans, start=1):
            index = ply - 1 + self._offset
            row = index // 2
            col = 1 if index % 2 == 0 else 2
            if col == 1 or row == 0:
                number = QTableWidgetItem(f"{self._first_number + row}.")
                self._table.setItem(row, 0, number)
            item = QTableWidgetItem(san)
            self._table.setItem(row, col, item)

        self._current = 0
        self._apply_highlight()
        return True

    def clear(self):
        self._table.clearContents()
        self._table.setRowCount(0)
        self._ply_count = 0
        self._current = 0
        self._offset = 0
        self._first_number = 1
        self._sans = []
        self._labels = []

    def set_labels(self, labels):
        """Attach a review label to each move; the delegate draws its mark."""
        self._labels = list(labels or [])
        for ply, san in enumerate(self._sans, start=1):
            item = self._item_for_ply(ply)
            if item is None:
                continue
            label = self._labels[ply - 1] if ply - 1 < len(self._labels) else None
            item.setText(san)
            item.setData(Qt.ItemDataRole.UserRole, label)
            item.setToolTip(label or "")
        self._table.viewport().update()

    def label_icon(self, label):
        name = MOVE_LABEL_ICONS.get(label)
        if not name:
            return None
        return action_icon(self._theme, name, size=_MARK_PIXELS, color=MOVE_LABEL_COLORS.get(label))

    def row_color(self, kind):
        values = MOVE_ROW_COLORS.get(self._theme, MOVE_ROW_COLORS[LIGHT])[kind]
        return QColor(*values)

    def number_color(self):
        return QColor(muted_color(self._theme))

    def is_current_cell(self, row, column):
        if column == 0:
            return False
        return self._ply_for_cell(row, column) == self._current

    def set_current_ply(self, ply):
        self._current = ply
        self._apply_highlight()
        item = self._item_for_ply(ply)
        if item is not None:
            self._table.scrollToItem(item, QAbstractItemView.ScrollHint.PositionAtCenter)

    def set_theme(self, theme):
        self._theme = theme
        self._apply_highlight()

    def _item_for_ply(self, ply):
        if ply <= 0 or ply > self._ply_count:
            return None
        index = ply - 1 + self._offset
        row = index // 2
        col = 1 if index % 2 == 0 else 2
        return self._table.item(row, col)

    def _ply_for_cell(self, row, column):
        if column == 0:
            index = row * 2
        else:
            index = row * 2 + (0 if column == 1 else 1)
        ply = index + 1 - self._offset
        return ply if 1 <= ply <= self._ply_count else None

    def _apply_highlight(self):
        self._table.viewport().update()

    def _on_click(self, row, col):
        ply = self._ply_for_cell(row, col)
        if ply is not None:
            self.ply_selected.emit(ply)
