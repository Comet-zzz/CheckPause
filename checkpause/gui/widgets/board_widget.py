import io
import math
import os

import chess
import chess.pgn
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from checkpause.assets import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    PIECE_SETS,
)
from checkpause.gui.theme import DARK
from checkpause.i18n import t
from checkpause.resources import resource_path

LAST_MOVE_RGBA = (246, 246, 105, 150)
CHECK_RGBA = (224, 82, 82, 110)


class _BoardCanvas(QWidget):
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

    def _geometry(self):
        width = self.width()
        height = self.height()
        side = min(width, height)
        margin = max(16, int(side * 0.05))
        board_size = max(80, side - 2 * margin)
        x0 = (width - board_size) / 2
        y0 = (height - board_size) / 2
        return x0, y0, board_size, max(1.0, board_size / 8)

    def _square_from_display(self, row, col, flipped):
        if flipped:
            return chess.square(7 - col, row)
        return chess.square(col, 7 - row)

    def _display_from_square(self, sq, flipped):
        file_index = chess.square_file(sq)
        rank_index = chess.square_rank(sq)
        if flipped:
            return rank_index, 7 - file_index
        return 7 - rank_index, file_index

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        owner = self._owner
        palette = owner._palette()
        painter.fillRect(self.rect(), QColor(palette["margin"]))

        x0, y0, board_size, square = self._geometry()
        board = owner._board
        light_color, dark_color = owner._square_colors()

        highlighted = set()
        if owner._last_move is not None:
            highlighted.add(owner._last_move.from_square)
            highlighted.add(owner._last_move.to_square)

        check_square = board.king(board.turn) if board.is_check() else None

        flipped = owner._flipped
        for row in range(8):
            for col in range(8):
                sq = self._square_from_display(row, col, flipped)
                rect = QRectF(
                    x0 + col * square,
                    y0 + row * square,
                    square,
                    square,
                )
                is_light = (
                    chess.square_file(sq) + chess.square_rank(sq)
                ) % 2 == 1
                painter.fillRect(
                    rect, QColor(light_color if is_light else dark_color)
                )

                if sq in highlighted:
                    painter.fillRect(rect, QColor(*LAST_MOVE_RGBA))

                if sq == check_square:
                    painter.fillRect(rect, QColor(*CHECK_RGBA))

                piece = board.piece_at(sq)
                if piece is not None:
                    renderer = owner._piece_renderer(piece)
                    if renderer is not None:
                        inset = square * 0.06
                        renderer.render(
                            painter,
                            QRectF(
                                rect.x() + inset,
                                rect.y() + inset,
                                square - 2 * inset,
                                square - 2 * inset,
                            ),
                        )

        self._draw_coordinates(painter, palette, x0, y0, board_size, square)

        best = owner._best_moves.get(owner._index)
        if best:
            arrow = QColor(palette["arrow"])
            arrow.setAlpha(200)
            self._draw_arrow(painter, best, x0, y0, square, arrow)

        painter.end()

    def _draw_coordinates(self, painter, palette, x0, y0, board_size, square):
        font = painter.font()
        font.setPointSizeF(max(7.0, square * 0.3))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(palette["coord"]))

        label_w = min(x0, square * 0.5)
        label_h = min(y0, square * 0.5)
        flipped = self._owner._flipped
        files = "abcdefgh"
        for col in range(8):
            file_index = 7 - col if flipped else col
            rect = QRectF(
                x0 + col * square, y0 + board_size, square, label_h
            )
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, files[file_index]
            )
        for row in range(8):
            rank_index = row if flipped else 7 - row
            rect = QRectF(
                x0 - label_w, y0 + row * square, label_w, square
            )
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignCenter, str(rank_index + 1)
            )

    def _draw_arrow(self, painter, uci, x0, y0, square, color):
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return

        def center(sq):
            row, col = self._display_from_square(sq, self._owner._flipped)
            return QPointF(
                x0 + (col + 0.5) * square,
                y0 + (row + 0.5) * square,
            )

        start = center(move.from_square)
        end = center(move.to_square)
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        dist = math.hypot(dx, dy)
        if dist == 0:
            return
        ux, uy = dx / dist, dy / dist

        head_length = square * 0.34
        line_start = QPointF(
            start.x() + ux * square * 0.18, start.y() + uy * square * 0.18
        )
        line_end = QPointF(
            end.x() - ux * head_length * 0.7, end.y() - uy * head_length * 0.7
        )

        pen = QPen(color)
        pen.setWidthF(square * 0.16)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawLine(line_start, line_end)

        base = QPointF(
            end.x() - ux * head_length, end.y() - uy * head_length
        )
        perp_x, perp_y = -uy, ux
        half = head_length * 0.55
        p1 = QPointF(base.x() + perp_x * half, base.y() + perp_y * half)
        p2 = QPointF(base.x() - perp_x * half, base.y() - perp_y * half)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(color))
        painter.drawPolygon(QPolygonF([end, p1, p2]))


class BoardWidget(QWidget):
    index_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = "light"
        self._piece_set = DEFAULT_PIECE_SET
        self._board_theme = DEFAULT_BOARD_THEME
        self._moves = []
        self._best_moves = {}
        self._board = chess.Board()
        self._last_move = None
        self._index = 0
        self._flipped = False
        self._piece_cache = {}

        self._canvas = _BoardCanvas(self)
        self._canvas.setMinimumSize(520, 520)

        self._step_label = QLabel()
        self._step_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._btn_first = QPushButton("|◀")
        self._btn_prev = QPushButton("◀")
        self._btn_next = QPushButton("▶")
        self._btn_last = QPushButton("▶|")
        self._btn_flip = QPushButton("⇅")
        for button in (self._btn_first, self._btn_prev, self._btn_next, self._btn_last):
            button.setEnabled(False)
        self._btn_first.clicked.connect(self.first)
        self._btn_prev.clicked.connect(self.prev)
        self._btn_next.clicked.connect(self.next)
        self._btn_last.clicked.connect(self.last)
        self._btn_flip.clicked.connect(self.flip)

        nav_layout = QHBoxLayout()
        nav_layout.addWidget(self._btn_first)
        nav_layout.addWidget(self._btn_prev)
        nav_layout.addWidget(self._btn_next)
        nav_layout.addWidget(self._btn_last)
        nav_layout.addWidget(self._btn_flip)

        layout = QVBoxLayout(self)
        layout.addWidget(self._canvas, 1)
        layout.addWidget(self._step_label)
        layout.addLayout(nav_layout)

        self.retranslate(self._language)

    def load_pgn(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None:
            return False, t("pgn_invalid", self._language)
        moves = list(game.mainline_moves())
        if not moves:
            return False, t("pgn_no_moves", self._language)
        self._moves = moves
        self._best_moves = {}
        self._index = 0
        self.render()
        return True, None

    def set_results(self, results):
        self._best_moves = {}
        for i, record in enumerate(results or [], start=1):
            best = record.get("best_move")
            if best:
                self._best_moves[i] = best
        self.render()

    def clear(self):
        self._moves = []
        self._best_moves = {}
        self._index = 0
        self.render()

    def goto(self, index):
        if not self._moves:
            return
        self._index = max(0, min(index, len(self._moves)))
        self.render()
        self.index_changed.emit(self._index)

    def first(self):
        self.goto(0)

    def prev(self):
        self.goto(self._index - 1)

    def next(self):
        self.goto(self._index + 1)

    def last(self):
        self.goto(len(self._moves))

    def flip(self):
        self._flipped = not self._flipped
        self.render()

    def _palette(self):
        if self._theme == DARK:
            return {
                "margin": "#1e1e1e",
                "coord": "#cfcfcf",
                "arrow": "#15781b",
            }
        return {
            "margin": "#ffffff",
            "coord": "#4a4a4a",
            "arrow": "#15781b",
        }

    def _piece_renderer(self, piece):
        color = "w" if piece.color == chess.WHITE else "b"
        code = color + piece.symbol().upper()
        cache_key = self._piece_set + ":" + code
        if cache_key not in self._piece_cache:
            path = resource_path(
                "assets", "pieces", self._piece_set, code + ".svg"
            )
            renderer = None
            if os.path.isfile(path):
                renderer = QSvgRenderer(path)
                if not renderer.isValid():
                    renderer = None
            self._piece_cache[cache_key] = renderer
        return self._piece_cache[cache_key]

    def _square_colors(self):
        return BOARD_THEMES.get(
            self._board_theme, BOARD_THEMES[DEFAULT_BOARD_THEME]
        )

    def set_theme(self, theme):
        self._theme = theme
        self.render()

    def set_piece_set(self, name):
        if name in PIECE_SETS:
            self._piece_set = name
            self.render()

    def set_board_theme(self, name):
        if name in BOARD_THEMES:
            self._board_theme = name
            self.render()

    def render(self):
        self._board = chess.Board()
        for move in self._moves[: self._index]:
            self._board.push(move)
        self._last_move = self._moves[self._index - 1] if self._index > 0 else None

        self._canvas.update()

        if self._index == 0:
            self._step_label.setText(t("board_initial", self._language))
        else:
            self._step_label.setText(
                t(
                    "board_step",
                    self._language,
                    index=self._index,
                    total=len(self._moves),
                )
            )

        has_moves = bool(self._moves)
        self._btn_first.setEnabled(has_moves and self._index > 0)
        self._btn_prev.setEnabled(has_moves and self._index > 0)
        self._btn_next.setEnabled(has_moves and self._index < len(self._moves))
        self._btn_last.setEnabled(has_moves and self._index < len(self._moves))

    def retranslate(self, language):
        self._language = language
        self._btn_first.setToolTip(t("btn_first", language))
        self._btn_prev.setToolTip(t("btn_prev", language))
        self._btn_next.setToolTip(t("btn_next", language))
        self._btn_last.setToolTip(t("btn_last", language))
        self._btn_flip.setToolTip(t("btn_flip", language))
        self.render()
