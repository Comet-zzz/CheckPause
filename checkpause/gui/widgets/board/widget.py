import io
import os
import time

import chess
import chess.pgn
from PyQt6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from checkpause.assets import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    PIECE_SETS,
)
from checkpause.gui.icons import nav_icon
from checkpause.gui.theme import DARK
from checkpause.gui.widgets.board.canvas import _BoardCanvas
from checkpause.gui.widgets.board.constants import ANIMATION_MS, FRAME_MS
from checkpause.gui.widgets.board.promo import _PromotionPopup
from checkpause.i18n import t
from checkpause.resources import resource_path


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
        self._paused = False
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

        self._btn_first = QPushButton()
        self._btn_prev = QPushButton()
        self._btn_next = QPushButton()
        self._btn_last = QPushButton()
        self._btn_flip = QPushButton()
        for button in (self._btn_first, self._btn_prev, self._btn_next, self._btn_last):
            button.setEnabled(False)
            button.setMinimumWidth(44)
        self._btn_first.clicked.connect(self.first)
        self._btn_prev.clicked.connect(self.prev)
        self._btn_next.clicked.connect(self.next)
        self._btn_last.clicked.connect(self.last)
        self._btn_flip.clicked.connect(self.flip)
        self._apply_nav_icons()

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
        if game.headers.get("SetUp") == "1" and game.headers.get("FEN"):
            self._start_fen = game.headers["FEN"]
        else:
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

    def set_paused(self, paused):
        self._paused = bool(paused)
        if self._paused:
            self.clear_selection()

    def can_pick(self, square):
        if not self._interactive or self._paused:
            return False
        if self._index != len(self._moves):
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

    def _piece_pixmap(self, piece, size):
        renderer = self._piece_renderer(piece)
        if renderer is None:
            return None
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        return pixmap

    def promotion_choice(self, to_square, color):
        popup = _PromotionPopup(self, to_square, color)
        choice = popup.choose()
        popup.deleteLater()
        return choice

    def _square_colors(self):
        return BOARD_THEMES.get(
            self._board_theme, BOARD_THEMES[DEFAULT_BOARD_THEME]
        )

    def _apply_nav_icons(self):
        for button, name in (
            (self._btn_first, "nav_first"),
            (self._btn_prev, "nav_prev"),
            (self._btn_next, "nav_next"),
            (self._btn_last, "nav_last"),
            (self._btn_flip, "nav_flip"),
        ):
            button.setIcon(nav_icon(self._theme, name))
            button.setIconSize(QSize(18, 18))

    def set_theme(self, theme):
        self._theme = theme
        self._apply_nav_icons()
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
