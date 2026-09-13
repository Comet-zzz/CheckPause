import io
import math
import os
import time

import chess
import chess.pgn
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
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
SELECTED_RGBA = (255, 214, 102, 150)
TARGET_RGBA = (40, 40, 40, 90)
TARGET_HOVER_RGBA = (40, 40, 40, 130)
HOVER_RGBA = (255, 255, 255, 36)
DRAG_LIFT = 1.08

ANIMATION_MS = 130
FRAME_MS = 16
DRAG_THRESHOLD = 5


class _BoardCanvas(QWidget):
    def __init__(self, owner, parent=None):
        super().__init__(parent)
        self._owner = owner
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.setMouseTracking(True)
        self._press_pos = None
        self._press_square = None
        self._press_was_selected = False
        self._drag_square = None
        self._dragging = False
        self._drag_pos = None
        self._hover_square = None

    def mousePressEvent(self, event):
        owner = self._owner
        if not owner._interactive:
            return
        if event.button() == Qt.MouseButton.RightButton:
            owner.clear_selection()
            self._reset_press()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        square = self._square_at(event.position())
        if square is None:
            return
        self._press_pos = event.position()
        self._press_square = square
        self._press_was_selected = owner._selected == square
        self._drag_square = None
        self._dragging = False

        if (
            owner._selected is not None
            and square in owner._targets
            and owner.try_move(owner._selected, square)
        ):
            return
        if owner.select_square(square):
            self._drag_square = square
        else:
            owner.clear_selection()
            self._reset_press()

    def mouseMoveEvent(self, event):
        owner = self._owner
        if not owner._interactive:
            return
        pos = event.position()
        pressed = event.buttons() & Qt.MouseButton.LeftButton
        if self._press_square is not None and pressed:
            if not self._dragging:
                delta = pos - self._press_pos
                if (
                    delta.x() * delta.x() + delta.y() * delta.y()
                    > DRAG_THRESHOLD * DRAG_THRESHOLD
                ):
                    if (
                        self._drag_square is not None
                        and owner._selected == self._drag_square
                    ):
                        self._dragging = True
                        self._drag_pos = pos
                        self.setCursor(Qt.CursorShape.ClosedHandCursor)
                    else:
                        self._press_square = None
            if self._dragging:
                self._drag_pos = pos
                self._hover_square = self._square_at(pos)
                self.update()
                return
        square = self._square_at(pos)
        if square != self._hover_square:
            self._hover_square = square
            self.update()
        self._update_cursor(square)

    def mouseReleaseEvent(self, event):
        owner = self._owner
        if not owner._interactive:
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        square = self._square_at(event.position())
        if self._dragging:
            self._dragging = False
            self._drag_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            handled = False
            if (
                square is not None
                and owner._selected is not None
                and square in owner._targets
            ):
                handled = owner.try_move(owner._selected, square)
            if not handled and owner._selected is not None:
                if (
                    square is None
                    or square == owner._selected
                    or not owner.select_square(square)
                ):
                    owner.start_drag_return(
                        event.position(), owner._selected
                    )
            self._reset_press()
            self.update()
        else:
            if self._press_was_selected and square == self._press_square:
                owner.clear_selection()
            self._reset_press()
        self._update_cursor(square)

    def leaveEvent(self, event):
        if self._hover_square is not None:
            self._hover_square = None
            self.update()

    def _reset_press(self):
        self._press_pos = None
        self._press_square = None
        self._press_was_selected = False
        self._drag_square = None

    def _square_at(self, pos):
        x0, y0, board_size, square = self._geometry()
        if not (
            x0 <= pos.x() < x0 + board_size
            and y0 <= pos.y() < y0 + board_size
        ):
            return None
        col = int((pos.x() - x0) // square)
        row = int((pos.y() - y0) // square)
        return self._square_from_display(row, col, self._owner._flipped)

    def _update_cursor(self, square):
        owner = self._owner
        if square is not None and (
            (owner._selected is not None and square in owner._targets)
            or owner.can_pick(square)
        ):
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

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

        hidden = set()
        animation = owner._animation
        if animation is not None:
            hidden.add(animation["to"])
            if animation["rook"] is not None:
                hidden.add(animation["rook"][1])
        if self._dragging and owner._selected is not None:
            hidden.add(owner._selected)
        if owner._drag_return is not None and not self._dragging:
            hidden.add(owner._drag_return["origin"])

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

                if owner._selected == sq:
                    painter.fillRect(rect, QColor(*SELECTED_RGBA))

                if sq == self._hover_square and owner.can_pick(sq):
                    painter.fillRect(rect, QColor(*HOVER_RGBA))

                if (
                    self._dragging
                    and sq == self._hover_square
                    and sq in owner._targets
                ):
                    painter.fillRect(rect, QColor(*TARGET_HOVER_RGBA))

                piece = board.piece_at(sq)
                if piece is not None and sq not in hidden:
                    self._draw_piece(painter, piece, rect, square)

                if sq in owner._targets:
                    self._draw_target(painter, rect, square, piece)

        self._draw_coordinates(painter, palette, x0, y0, board_size, square)

        if animation is not None:
            self._draw_animation(painter, x0, y0, square, animation)
        if self._dragging and owner._selected is not None:
            self._draw_dragged(painter, owner._selected, square)
        drag_return = owner._drag_return
        if drag_return is not None and not self._dragging:
            self._draw_drag_return(painter, x0, y0, square, drag_return)

        best = owner._best_moves.get(owner._index)
        if best:
            arrow = QColor(palette["arrow"])
            arrow.setAlpha(200)
            self._draw_arrow(painter, best, x0, y0, square, arrow)

        painter.end()

    def _draw_piece(self, painter, piece, rect, square, scale=1.0):
        renderer = self._owner._piece_renderer(piece)
        if renderer is None:
            return
        size = (square * (1 - 2 * 0.06)) * scale
        center = rect.center()
        renderer.render(
            painter,
            QRectF(
                center.x() - size / 2,
                center.y() - size / 2,
                size,
                size,
            ),
        )

    def _draw_piece_at(self, painter, piece, center, square, scale=1.0):
        renderer = self._owner._piece_renderer(piece)
        if renderer is None:
            return
        size = (square * (1 - 2 * 0.06)) * scale
        renderer.render(
            painter,
            QRectF(
                center.x() - size / 2,
                center.y() - size / 2,
                size,
                size,
            ),
        )

    def _center_of(self, square, x0, y0, cell):
        row, col = self._display_from_square(square, self._owner._flipped)
        return QPointF(x0 + (col + 0.5) * cell, y0 + (row + 0.5) * cell)

    def _draw_animation(self, painter, x0, y0, cell, animation):
        elapsed = time.monotonic() - animation["start"]
        progress = min(1.0, elapsed / animation["duration"])
        eased = 1 - (1 - progress) ** 3
        owner = self._owner

        captured = animation["captured_piece"]
        if captured is not None:
            painter.save()
            painter.setOpacity(max(0.0, 1.0 - eased))
            captured_center = self._center_of(
                animation["captured_square"], x0, y0, cell
            )
            self._draw_piece_at(painter, captured, captured_center, cell)
            painter.restore()

        start = self._center_of(animation["from"], x0, y0, cell)
        end = self._center_of(animation["to"], x0, y0, cell)
        center = QPointF(
            start.x() + (end.x() - start.x()) * eased,
            start.y() + (end.y() - start.y()) * eased,
        )
        self._draw_piece_at(painter, animation["piece"], center, cell)

        rook = animation["rook"]
        if rook is not None:
            rook_piece = owner._board.piece_at(rook[1])
            if rook_piece is not None:
                rook_start = self._center_of(rook[0], x0, y0, cell)
                rook_end = self._center_of(rook[1], x0, y0, cell)
                rook_center = QPointF(
                    rook_start.x() + (rook_end.x() - rook_start.x()) * eased,
                    rook_start.y() + (rook_end.y() - rook_start.y()) * eased,
                )
                self._draw_piece_at(
                    painter, rook_piece, rook_center, cell
                )

    def _draw_dragged(self, painter, square, cell):
        if self._drag_pos is None:
            return
        piece = self._owner._board.piece_at(square)
        if piece is None:
            return
        painter.save()
        painter.setOpacity(0.92)
        self._draw_piece_at(
            painter, piece, self._drag_pos, cell, DRAG_LIFT
        )
        painter.restore()

    def _draw_drag_return(self, painter, x0, y0, cell, drag_return):
        elapsed = time.monotonic() - drag_return["start"]
        progress = min(1.0, elapsed / drag_return["duration"])
        eased = 1 - (1 - progress) ** 3
        end = self._center_of(drag_return["origin"], x0, y0, cell)
        start = drag_return["from_pos"]
        center = QPointF(
            start.x() + (end.x() - start.x()) * eased,
            start.y() + (end.y() - start.y()) * eased,
        )
        self._draw_piece_at(painter, drag_return["piece"], center, cell)

    def _draw_target(self, painter, rect, square, piece):
        color = QColor(*TARGET_RGBA)
        if piece is not None:
            pen = QPen(color)
            pen.setWidthF(square * 0.07)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            inset = square * 0.08
            painter.drawEllipse(rect.adjusted(inset, inset, -inset, -inset))
        else:
            radius = square * 0.17
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(QPointF(rect.center()), radius, radius)

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
    move_requested = pyqtSignal(int, int)

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
        self._interactive = False
        self._human_color = chess.WHITE
        self._selected = None
        self._targets = set()
        self._animation = None
        self._drag_return = None
        self._start_fen = None

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(FRAME_MS)
        self._anim_timer.timeout.connect(self._on_animation_tick)

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

        self._nav = QWidget()
        nav_layout = QHBoxLayout(self._nav)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.addWidget(self._btn_first)
        nav_layout.addWidget(self._btn_prev)
        nav_layout.addWidget(self._btn_next)
        nav_layout.addWidget(self._btn_last)

        nav_row = QHBoxLayout()
        nav_row.addWidget(self._nav, 1)
        nav_row.addWidget(self._btn_flip)

        layout = QVBoxLayout(self)
        layout.addWidget(self._canvas, 1)
        layout.addWidget(self._step_label)
        layout.addLayout(nav_row)

        self.retranslate(self._language)

    def load_pgn(self, pgn_text):
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None:
            return False, t("pgn_invalid", self._language)
        moves = list(game.mainline_moves())
        if not moves:
            return False, t("pgn_no_moves", self._language)
        self._start_fen = None
        self._moves = moves
        self._best_moves = {}
        self._index = 0
        self.render()
        return True, None

    def set_start_fen(self, fen):
        self._start_fen = fen or None
        self._moves = []
        self._best_moves = {}
        self._index = 0
        self.render()

    def set_navigation_visible(self, visible):
        self._nav.setVisible(bool(visible))

    def set_hint(self, uci):
        if uci:
            self._best_moves[self._index] = uci
            self._canvas.update()

    def clear_hint(self):
        if self._best_moves.pop(self._index, None) is not None:
            self._canvas.update()

    def set_results(self, results):
        self._best_moves = {}
        for i, record in enumerate(results or [], start=1):
            best = record.get("best_move")
            if best:
                self._best_moves[i] = best
        self.render()

    def clear(self):
        self._start_fen = None
        self._moves = []
        self._best_moves = {}
        self._index = 0
        self.render()

    def set_moves(self, moves, index=None, animate=False):
        previous_count = len(self._moves)
        self._moves = list(moves)
        self._best_moves = {}
        if index is None:
            self._index = len(self._moves)
        else:
            self._index = max(0, min(index, len(self._moves)))
        self.render()
        if (
            animate
            and self._index == len(self._moves)
            and len(self._moves) > previous_count
        ):
            self._start_animation(self._moves[-1])

    def set_interactive(self, enabled, human_color=chess.WHITE):
        self._interactive = enabled
        self._human_color = human_color
        self._flipped = human_color == chess.BLACK
        self.render()

    def clear_selection(self):
        self._selected = None
        self._targets = set()
        self._canvas.update()

    def can_pick(self, square):
        if not self._interactive or self._index != len(self._moves):
            return False
        board = self._board
        if board.is_game_over() or board.turn != self._human_color:
            return False
        piece = board.piece_at(square)
        return piece is not None and piece.color == self._human_color

    def select_square(self, square):
        if not self.can_pick(square):
            return False
        self._selected = square
        self._targets = {
            move.to_square
            for move in self._board.legal_moves
            if move.from_square == square
        }
        self._canvas.update()
        return True

    def try_move(self, from_square, to_square):
        if self._selected != from_square or to_square not in self._targets:
            return False
        self.clear_selection()
        self.move_requested.emit(from_square, to_square)
        return True

    def on_square_clicked(self, square):
        if self._selected is not None and square in self._targets:
            self.try_move(self._selected, square)
            return
        if self.select_square(square):
            return
        self.clear_selection()

    def _start_animation(self, move):
        piece = self._board.piece_at(move.to_square)
        if piece is None:
            return
        previous = self._board.copy()
        previous.pop()
        captured_square = move.to_square
        if previous.is_en_passant(move):
            captured_square = chess.square(
                chess.square_file(move.to_square),
                chess.square_rank(move.from_square),
            )
        captured_piece = previous.piece_at(captured_square)

        rook = None
        if (
            piece.piece_type == chess.KING
            and abs(
                chess.square_file(move.to_square)
                - chess.square_file(move.from_square)
            )
            == 2
        ):
            rank = chess.square_rank(move.from_square)
            if chess.square_file(move.to_square) > chess.square_file(
                move.from_square
            ):
                rook = (chess.square(7, rank), chess.square(5, rank))
            else:
                rook = (chess.square(0, rank), chess.square(3, rank))

        self._animation = {
            "piece": piece,
            "from": move.from_square,
            "to": move.to_square,
            "rook": rook,
            "captured_square": captured_square,
            "captured_piece": captured_piece,
            "start": time.monotonic(),
            "duration": ANIMATION_MS / 1000.0,
        }
        self._anim_timer.start()
        self._canvas.update()

    def start_drag_return(self, from_pos, square):
        piece = self._board.piece_at(square)
        if piece is None:
            return
        self._drag_return = {
            "piece": piece,
            "origin": square,
            "from_pos": QPointF(from_pos),
            "start": time.monotonic(),
            "duration": ANIMATION_MS / 1000.0,
        }
        self._anim_timer.start()
        self._canvas.update()

    def _stop_animation(self):
        self._animation = None
        self._drag_return = None
        if self._anim_timer.isActive():
            self._anim_timer.stop()

    def _on_animation_tick(self):
        now = time.monotonic()
        if (
            self._animation is not None
            and now - self._animation["start"] >= self._animation["duration"]
        ):
            self._animation = None
        if (
            self._drag_return is not None
            and now - self._drag_return["start"] >= self._drag_return["duration"]
        ):
            self._drag_return = None
        if self._animation is None and self._drag_return is None:
            self._anim_timer.stop()
        self._canvas.update()

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
        self._stop_animation()
        self._selected = None
        self._targets = set()
        if self._start_fen:
            try:
                self._board = chess.Board(self._start_fen)
            except ValueError:
                self._board = chess.Board()
        else:
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
