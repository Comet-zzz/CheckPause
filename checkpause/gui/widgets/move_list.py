import io

import chess
import chess.pgn
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from checkpause.gui.theme import DARK


class MoveListWidget(QWidget):
    ply_selected = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "light"
        self._ply_count = 0
        self._current = 0

        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["#", "W", "B"])
        self._table.horizontalHeader().setVisible(False)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setShowGrid(False)
        self._table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
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
        board = game.board()
        sans = []
        for move in game.mainline_moves():
            sans.append(board.san(move))
            board.push(move)
        if not sans:
            return False

        self._ply_count = len(sans)
        rows = (self._ply_count + 1) // 2
        self._table.clearContents()
        self._table.setRowCount(rows)
        for ply, san in enumerate(sans, start=1):
            row = (ply - 1) // 2
            col = 1 if ply % 2 == 1 else 2
            if col == 1:
                number = QTableWidgetItem(f"{row + 1}.")
                number.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                self._table.setItem(row, 0, number)
            item = QTableWidgetItem(san)
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
            self._table.setItem(row, col, item)

        self._current = 0
        self._apply_highlight()
        return True

    def clear(self):
        self._table.clearContents()
        self._table.setRowCount(0)
        self._ply_count = 0
        self._current = 0

    def set_current_ply(self, ply):
        self._current = ply
        self._apply_highlight()
        item = self._item_for_ply(ply)
        if item is not None:
            self._table.scrollToItem(
                item, QAbstractItemView.ScrollHint.PositionAtCenter
            )

    def set_theme(self, theme):
        self._theme = theme
        self._apply_highlight()

    def _item_for_ply(self, ply):
        if ply <= 0 or ply > self._ply_count:
            return None
        row = (ply - 1) // 2
        col = 1 if ply % 2 == 1 else 2
        return self._table.item(row, col)

    def _highlight_color(self):
        return QColor("#2f4a6b") if self._theme == DARK else QColor("#bcd6f5")

    def _apply_highlight(self):
        for row in range(self._table.rowCount()):
            for col in (1, 2):
                item = self._table.item(row, col)
                if item is not None:
                    item.setBackground(QBrush())
                    font = item.font()
                    font.setBold(False)
                    item.setFont(font)
        item = self._item_for_ply(self._current)
        if item is not None:
            item.setBackground(QBrush(self._highlight_color()))
            font = item.font()
            font.setBold(True)
            item.setFont(font)

    def _on_click(self, row, col):
        if col == 0:
            ply = row * 2 + 1
        else:
            ply = row * 2 + (1 if col == 1 else 2)
        if 1 <= ply <= self._ply_count:
            self.ply_selected.emit(ply)
