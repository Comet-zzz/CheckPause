from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class EvalBar(QWidget):
    """Thin vertical evaluation bar hosted by the analysis side panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("evalBar")
        self.setFixedWidth(10)
        self.setMinimumHeight(80)
        self._ratio = 0.5
        self._light = "#ffffff"
        self._dark = "#2b2f34"
        self._border = "#59000000"

    def set_ratio(self, ratio):
        ratio = max(0.0, min(1.0, float(ratio)))
        if abs(ratio - self._ratio) < 0.001:
            return
        self._ratio = ratio
        self.update()

    def set_colors(self, light, dark, border):
        self._light = light
        self._dark = dark
        self._border = border
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.width() / 2.0
        shape = QPainterPath()
        shape.addRoundedRect(rect, radius, radius)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self._dark))
        painter.drawPath(shape)

        painter.setClipPath(shape)
        painter.fillRect(
            QRectF(
                rect.left(),
                rect.bottom() - rect.height() * self._ratio,
                rect.width(),
                rect.height() * self._ratio,
            ),
            QColor(self._light),
        )
        painter.setClipping(False)

        notch = QColor(self._border)
        notch.setAlpha(90)
        pen = QPen(notch)
        pen.setWidthF(1.0)
        painter.setPen(pen)
        center_y = rect.center().y()
        painter.drawLine(
            QPointF(rect.left(), center_y),
            QPointF(rect.right(), center_y),
        )

        pen = QPen(QColor(self._border))
        pen.setWidthF(1.0)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, radius, radius)
