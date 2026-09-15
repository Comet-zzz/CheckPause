import chess
from PyQt6.QtCore import QEventLoop, QPoint, QRectF, Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget

from checkpause.gui.widgets.board.constants import (
    PROMOTION_CHOICES,
    PROMOTION_HOVER_RGBA,
)


class _PromotionPopup(QWidget):
    """Frameless promotion picker anchored to the promoting square."""

    def __init__(self, board_widget, to_square, color):
        super().__init__(board_widget, Qt.WindowType.Popup)
        self._board_widget = board_widget
        self._to_square = to_square
        self._color = color
        self._cell = max(
            32, int(board_widget._canvas._geometry()[3])
        )
        self._hover = -1
        self._result = None
        self._loop = QEventLoop()

        self.setFixedSize(self._cell, self._cell * len(PROMOTION_CHOICES))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._reposition()

    def choose(self):
        self.show()
        self.raise_()
        self._loop.exec()
        return self._result

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        light, dark = self._board_widget._square_colors()
        file_index = chess.square_file(self._to_square)
        rank_index = chess.square_rank(self._to_square)
        size = int(self._cell * 0.82)
        for index, piece_type in enumerate(PROMOTION_CHOICES):
            rect = QRectF(0, index * self._cell, self._cell, self._cell)
            is_light = (file_index + rank_index + index) % 2 == 1
            painter.fillRect(
                rect, QColor(light if is_light else dark)
            )
            if index == self._hover:
                painter.fillRect(rect, QColor(*PROMOTION_HOVER_RGBA))
            pixmap = self._board_widget._piece_pixmap(
                chess.Piece(piece_type, self._color), size
            )
            if pixmap is not None:
                painter.drawPixmap(
                    int((self._cell - size) / 2),
                    int(index * self._cell + (self._cell - size) / 2),
                    pixmap,
                )
        painter.end()

    def mouseMoveEvent(self, event):
        index = int(event.position().y()) // self._cell
        if 0 <= index < len(PROMOTION_CHOICES):
            if index != self._hover:
                self._hover = index
                self.update()
        elif self._hover != -1:
            self._hover = -1
            self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        index = int(event.position().y()) // self._cell
        if 0 <= index < len(PROMOTION_CHOICES):
            self._result = PROMOTION_CHOICES[index]
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()

    def hideEvent(self, event):
        self._loop.quit()
        super().hideEvent(event)

    def _reposition(self):
        canvas = self._board_widget._canvas
        x0, y0, _size, cell = canvas._geometry()
        row, col = canvas._display_from_square(
            self._to_square, self._board_widget._flipped
        )
        x = x0 + col * cell
        if row <= 3:
            y = y0 + row * cell
        else:
            y = y0 + (row + 1) * cell - self.height()
        self.move(
            canvas.mapToGlobal(QPoint(int(round(x)), int(round(y))))
        )
