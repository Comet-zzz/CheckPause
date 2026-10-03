import math
import time

import chess
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import QSizePolicy, QWidget

from checkpause.core.engine import eval_ratio
from checkpause.gui.widgets.board.constants import (
    CHECK_RGBA,
    DRAG_LIFT,
    DRAG_THRESHOLD,
    EVAL_BLACK_RGBA,
    EVAL_BORDER_RGBA,
    EVAL_WHITE_RGBA,
    HOVER_RGBA,
    LAST_MOVE_RGBA,
    SELECTED_RGBA,
    TARGET_HOVER_RGBA,
    TARGET_RGBA,
)


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
        self._eval_ratio = 0.5
        self._eval_from = 0.5
        self._eval_to = 0.5
        self._eval_started = 0.0
        self._eval_duration = 0.28
        self._eval_timer = QTimer(self)
        self._eval_timer.setInterval(16)
        self._eval_timer.timeout.connect(self._step_eval_animation)

    def mousePressEvent(self, event):
        owner = self._owner
        if owner._editable:
            self._edit_press(event)
            return
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
        if owner._editable:
            self._edit_move(event)
            return
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
        if owner._editable:
            self._edit_release(event)
            return
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

    def _edit_press(self, event):
        owner = self._owner
        square = self._square_at(event.position())
        if event.button() == Qt.MouseButton.RightButton:
            if square is not None:
                owner.edit_remove(square)
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        if square is None:
            return
        self._press_pos = event.position()
        self._press_square = square
        self._drag_square = square
        self._dragging = False
        self._hover_square = square
        owner.clear_selection()
        if owner.piece_at(square) is not None:
            owner._selected = square
        self.update()

    def _edit_move(self, event):
        pos = event.position()
        if self._press_square is None:
            square = self._square_at(pos)
            if square != self._hover_square:
                self._hover_square = square
                self.update()
            self._update_cursor(square)
            return
        if not self._dragging:
            delta = pos - self._press_pos
            if (
                delta.x() * delta.x() + delta.y() * delta.y()
                > DRAG_THRESHOLD * DRAG_THRESHOLD
            ):
                self._dragging = True
                self._drag_pos = pos
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        if self._dragging:
            self._drag_pos = pos
            self._hover_square = self._square_at(pos)
            self.update()

    def _edit_release(self, event):
        owner = self._owner
        origin = self._drag_square
        square = self._square_at(event.position())
        dragged = self._dragging
        self._dragging = False
        self._drag_pos = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self._reset_press()
        if dragged:
            if origin is not None:
                if square is None:
                    owner.edit_remove(origin)
                elif square != origin:
                    owner.edit_move_piece(origin, square)
        elif owner._edit_tool is not None and square is not None:
            owner.edit_place(square)
        self.update()

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
        if owner._editable:
            if square is not None:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
            return
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.place_eval_controls()

    def _eval_bar_metrics(self, square):
        bar_h = min(22.0, max(10.0, square * 0.24))
        gap = max(3.0, square * 0.04)
        return bar_h, gap

    def _eval_row(self, x0, y0, board_size, square):
        """Geometry for the evaluation bar and the controls under it.

        Both live in the empty margin above the board: the bar spans the full
        board width and the controls stretch across the line below it. Nothing
        takes layout space, so the board keeps exactly the same size as the
        play and puzzle boards.
        """
        owner = self._owner
        controls = getattr(owner, "_eval_controls", None)
        bar_h, gap = self._eval_bar_metrics(square)
        controls_h = 0
        if owner._eval_available and controls is not None:
            controls.adjustSize()
            controls_h = controls.sizeHint().height()
        row_h = bar_h + (gap + controls_h if controls_h else 0)
        top_margin = y0
        row_y = max(0.0, (top_margin - row_h) / 2.0)
        bar_rect = QRectF(x0, row_y, board_size, bar_h)
        controls_rect = QRectF(
            x0,
            row_y + bar_h + gap,
            board_size,
            controls_h,
        )
        return bar_rect, controls_rect

    def place_eval_controls(self):
        owner = self._owner
        controls = getattr(owner, "_eval_controls", None)
        if controls is None or not owner._eval_available:
            return
        x0, y0, board_size, square = self._geometry()
        _, controls_rect = self._eval_row(x0, y0, board_size, square)
        controls.setGeometry(
            int(controls_rect.x()),
            int(controls_rect.y()),
            int(controls_rect.width()),
            int(controls_rect.height()),
        )
        controls.raise_()

    def animate_eval(self, margin, mate=None):
        target = eval_ratio(margin, mate)
        self._eval_from = self._eval_ratio
        self._eval_to = target
        self._eval_started = time.monotonic()
        if not self._eval_timer.isActive():
            self._eval_timer.start()
        self.update()

    def _step_eval_animation(self):
        elapsed = time.monotonic() - self._eval_started
        progress = elapsed / self._eval_duration
        if progress >= 1.0:
            self._eval_ratio = self._eval_to
            self._eval_timer.stop()
        else:
            eased = 1.0 - (1.0 - progress) ** 3
            self._eval_ratio = self._eval_from + (
                self._eval_to - self._eval_from
            ) * eased
        self.update()

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
        if owner._last_move is not None and not owner._editable:
            highlighted.add(owner._last_move.from_square)
            highlighted.add(owner._last_move.to_square)

        check_square = board.king(board.turn) if board.is_check() else None

        hidden = set()
        animation = owner._animation
        if animation is not None:
            hidden.add(animation["to"])
            if animation["captured_piece"] is not None:
                hidden.add(animation["captured_square"])
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
                    and not owner._editable
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
        if not owner._editable:
            self._draw_eval_bar(painter, x0, y0, board_size, square)

        if animation is not None:
            self._draw_animation(painter, x0, y0, square, animation)
        if self._dragging and owner._selected is not None:
            self._draw_dragged(painter, owner._selected, square)
        drag_return = owner._drag_return
        if drag_return is not None and not self._dragging:
            self._draw_drag_return(painter, x0, y0, square, drag_return)

        best = None
        live = owner._live_eval
        if (
            live is not None
            and owner._hint_enabled
            and live["index"] == owner._index
        ):
            best = live.get("uci")
        if not best:
            best = owner._best_moves.get(owner._index)
        if best and not owner._editable:
            self._draw_arrow(painter, best, x0, y0, square)

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
            opacity = eased if animation.get("fade_in") else 1.0 - eased
            if opacity > 0.0:
                painter.save()
                painter.setOpacity(opacity)
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

    def _draw_eval_bar(self, painter, x0, y0, board_size, square):
        owner = self._owner
        if not owner._eval_available:
            return
        rect, _ = self._eval_row(x0, y0, board_size, square)
        radius = rect.height() / 2.0
        ratio = max(0.0, min(1.0, self._eval_ratio))

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        shape = QPainterPath()
        shape.addRoundedRect(rect, radius, radius)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(*EVAL_BLACK_RGBA))
        painter.drawPath(shape)

        painter.setClipPath(shape)
        painter.fillRect(
            QRectF(
                rect.left(),
                rect.top(),
                rect.width() * ratio,
                rect.height(),
            ),
            QColor(*EVAL_WHITE_RGBA),
        )
        painter.setClipping(False)

        notch = QColor(*EVAL_BORDER_RGBA)
        notch.setAlpha(90)
        pen = QPen(notch)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        center_x = rect.center().x()
        painter.drawLine(
            QPointF(center_x, rect.top()), QPointF(center_x, rect.bottom())
        )

        border = QColor(*EVAL_BORDER_RGBA)
        border.setAlpha(150)
        pen = QPen(border)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
        painter.restore()

    def _draw_arrow(self, painter, uci, x0, y0, square):
        """A frosted-glass arrow: translucent fill, bright rim, soft shadow."""
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
        px, py = -uy, ux

        shaft = square * 0.085
        head_len = square * 0.30
        head_half = square * 0.205
        neck = QPointF(end.x() - ux * head_len, end.y() - uy * head_len)

        path = QPainterPath()
        path.moveTo(start.x() + px * shaft, start.y() + py * shaft)
        path.lineTo(neck.x() + px * shaft, neck.y() + py * shaft)
        path.lineTo(neck.x() + px * head_half, neck.y() + py * head_half)
        path.lineTo(end.x(), end.y())
        path.lineTo(neck.x() - px * head_half, neck.y() - py * head_half)
        path.lineTo(neck.x() - px * shaft, neck.y() - py * shaft)
        path.lineTo(start.x() - px * shaft, start.y() - py * shaft)
        path.closeSubpath()

        glass = QLinearGradient(start, end)
        glass.setColorAt(0.0, QColor(198, 222, 245, 110))
        glass.setColorAt(0.55, QColor(224, 238, 252, 150))
        glass.setColorAt(1.0, QColor(244, 251, 255, 200))
        brush = QBrush(glass)

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.translate(square * 0.02, square * 0.04)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(20, 35, 55, 55))
        painter.drawPath(path)
        painter.translate(-square * 0.02, -square * 0.04)

        rim = QPen(QColor(255, 255, 255, 170))
        rim.setWidthF(max(1.0, square * 0.018))
        rim.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        rim.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(rim)
        painter.setBrush(brush)
        painter.drawPath(path)

        painter.restore()
