"""Shared page layout primitives.

The app has two page shapes: a scrollable home column, and a board workspace
whose side slot keeps one fixed width. Both live here so pages cannot drift
back into per-page splitter sizes.
"""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget

# The board workspace: the board takes every remaining pixel, the panel keeps
# this width at every window size.
SIDE_PANEL_WIDTH = 384
# Home pages centre one column instead of stretching edge to edge.
HOME_MAX_WIDTH = 1120
# The lesson board is deliberately smaller than the analysis board.
LESSON_BOARD_MAX_WIDTH = 600


class BoardWorkspace(QWidget):
    """A board plus a side slot with a fixed width.

    ``panel_position="right"`` is the analysis/play/puzzle shape; ``"bottom"``
    is the lesson shape, where the panel sits under the board and shares its
    column. The board is not capped: it keeps growing until the pane's height
    limits the square, which keeps the layout tight on large windows.
    """

    def __init__(
        self,
        board,
        panel,
        panel_width=SIDE_PANEL_WIDTH,
        panel_position="right",
        parent=None,
    ):
        super().__init__(parent)
        self._board = board
        self._panel = panel
        self._right_side = panel_position != "bottom"
        self._shown = False
        if panel_position == "bottom":
            self._build_bottom(board, panel)
        else:
            self._build_right(board, panel, panel_width)

    def _build_right(self, board, panel, panel_width):
        panel.setFixedWidth(panel_width)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(board, 1)
        row.addWidget(panel)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addLayout(row)
        outer.addStretch(1)

    def _build_bottom(self, board, panel):
        board.setMaximumWidth(LESSON_BOARD_MAX_WIDTH)
        column = QWidget()
        column.setMaximumWidth(LESSON_BOARD_MAX_WIDTH)
        column_layout = QVBoxLayout(column)
        column_layout.setContentsMargins(0, 0, 0, 0)
        column_layout.setSpacing(10)
        column_layout.addWidget(board, 1)
        column_layout.addWidget(panel)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addStretch(0)
        row.addWidget(column, 1)
        row.addStretch(0)

    def showEvent(self, event):
        super().showEvent(event)
        self._shown = True
        self._sync_block_height()
        QTimer.singleShot(0, self._sync_block_height)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_block_height()

    def _sync_block_height(self):
        """Give the board and its menu one height: the board block's height.

        The board is square and often width-limited, so the page can be taller
        than the board. Stretching both columns to the page height left a blank
        card above the board and below its navigation; instead the block ends at
        the board and the rest of the page stays page background.
        """
        if not self._right_side or not self._shown:
            return
        block = max(1, min(self._board.natural_height(), self.height()))
        self._board.setFixedHeight(block)
        self._panel.setFixedHeight(block)
