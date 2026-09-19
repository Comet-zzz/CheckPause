import io
import os
import time

import chess
import chess.pgn
from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
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
    index_changed = Signal(int)
    move_requested = Signal(int, int)
    line_changed = Signal(bool)
    position_applied = Signal(str)

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
        self._free_line = False
        self._paused = False
        self._human_color = chess.WHITE
        self._selected = None
        self._targets = set()
        self._animation = None
        self._drag_return = None
        self._start_fen = None
        self._editable = False
        self._edit_available = False
        self._edit_tool = None
        self._edit_backup = None
        self._nav_visible = True

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(FRAME_MS)
        self._anim_timer.timeout.connect(self._on_animation_tick)

        self._canvas = _BoardCanvas(self)
        self._canvas.setMinimumSize(320, 320)

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
        self._btn_edit = QPushButton()
        self._btn_edit.setCheckable(True)
        self._btn_edit.setMinimumWidth(44)
        self._btn_edit.clicked.connect(self._on_edit_clicked)
        self._btn_edit.setVisible(False)
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
        left_spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        right_spacer = QSpacerItem(
            0, 0, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum
        )
        self._nav_spacers = (left_spacer, right_spacer)
        nav_row.addItem(left_spacer)
        nav_row.addWidget(self._step_label)
        nav_row.addWidget(self._btn_edit)
        nav_row.addWidget(self._btn_flip)
        nav_row.addItem(right_spacer)

        self._edit_bar = self._build_edit_bar()
        self._edit_bar.setVisible(False)

        layout = QVBoxLayout(self)
        layout.addWidget(self._canvas, 1)
        layout.addLayout(nav_row)
        layout.addWidget(self._edit_bar)

        self.retranslate(self._language)

    def _build_edit_bar(self):
        bar = QWidget()
        bar.setObjectName("boardEditBar")
        layout = QVBoxLayout(bar)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(4)

        self._palette_group = QButtonGroup(self)
        self._palette_group.setExclusive(True)
        self._palette_buttons = {}
        pieces_row = QHBoxLayout()
        pieces_row.setSpacing(2)
        for color in (chess.WHITE, chess.BLACK):
            if color == chess.BLACK:
                pieces_row.addSpacing(10)
            for piece_type in (
                chess.KING,
                chess.QUEEN,
                chess.ROOK,
                chess.BISHOP,
                chess.KNIGHT,
                chess.PAWN,
            ):
                button = QToolButton()
                button.setCheckable(True)
                button.setFixedSize(28, 28)
                button.setIconSize(QSize(22, 22))
                button.clicked.connect(
                    lambda _checked=False, piece=chess.Piece(
                        piece_type, color
                    ): self._on_palette(piece)
                )
                self._palette_group.addButton(button)
                self._palette_buttons[(color, piece_type)] = button
                pieces_row.addWidget(button)
        self._erase_button = QToolButton()
        self._erase_button.setCheckable(True)
        self._erase_button.setFixedSize(28, 28)
        self._erase_button.setIconSize(QSize(18, 18))
        self._erase_button.clicked.connect(
            lambda _checked=False: self._on_palette("erase")
        )
        self._palette_group.addButton(self._erase_button)
        pieces_row.addSpacing(10)
        pieces_row.addWidget(self._erase_button)
        pieces_row.addStretch(1)
        layout.addLayout(pieces_row)

        self._edit_turn = QComboBox()
        self._edit_turn.currentIndexChanged.connect(self._on_edit_turn)
        self._castling_boxes = []
        castling_row = QHBoxLayout()
        castling_row.setSpacing(4)
        for label, right in (
            ("K", chess.BB_H1),
            ("Q", chess.BB_A1),
            ("k", chess.BB_H8),
            ("q", chess.BB_A8),
        ):
            box = QCheckBox(label)
            box.toggled.connect(self._on_edit_castling)
            self._castling_boxes.append((box, right))
            castling_row.addWidget(box)
        self._ep_combo = QComboBox()
        self._ep_combo.setMinimumWidth(72)
        self._ep_combo.currentIndexChanged.connect(self._on_edit_ep)

        self._edit_turn_label = QLabel()
        self._castling_label = QLabel()
        self._ep_label = QLabel()
        position_row = QHBoxLayout()
        position_row.setSpacing(4)
        position_row.addWidget(self._edit_turn_label)
        position_row.addWidget(self._edit_turn)
        position_row.addSpacing(10)
        position_row.addWidget(self._castling_label)
        position_row.addLayout(castling_row)
        position_row.addSpacing(10)
        position_row.addWidget(self._ep_label)
        position_row.addWidget(self._ep_combo)
        position_row.addStretch(1)
        layout.addLayout(position_row)

        self._btn_edit_start = QPushButton()
        self._btn_edit_start.clicked.connect(self._edit_start)
        self._btn_edit_empty = QPushButton()
        self._btn_edit_empty.clicked.connect(self._edit_empty)
        self._btn_edit_copy = QPushButton()
        self._btn_edit_copy.clicked.connect(self._edit_copy_fen)
        self._btn_edit_apply = QPushButton()
        self._btn_edit_apply.clicked.connect(self.apply_edit)
        self._btn_edit_cancel = QPushButton()
        self._btn_edit_cancel.clicked.connect(self.cancel_edit)
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(4)
        buttons_row.addWidget(self._btn_edit_start)
        buttons_row.addWidget(self._btn_edit_empty)
        buttons_row.addWidget(self._btn_edit_copy)
        buttons_row.addStretch(1)
        buttons_row.addWidget(self._btn_edit_apply)
        buttons_row.addWidget(self._btn_edit_cancel)
        layout.addLayout(buttons_row)

        self._edit_hint = QLabel()
        self._edit_hint.setWordWrap(True)
        self._edit_note = QLabel()
        note_row = QHBoxLayout()
        note_row.setSpacing(8)
        note_row.addWidget(self._edit_hint, 1)
        note_row.addWidget(self._edit_note)
        layout.addLayout(note_row)
        self._ep_combo.setEnabled(False)
        self._refresh_palette_icons()
        return bar

    def _retranslate_edit_bar(self, language):
        for (color, piece_type), button in self._palette_buttons.items():
            name = {
                chess.KING: "piece_king",
                chess.QUEEN: "piece_queen",
                chess.ROOK: "piece_rook",
                chess.BISHOP: "piece_bishop",
                chess.KNIGHT: "piece_knight",
                chess.PAWN: "piece_pawn",
            }[piece_type]
            color_key = (
                "play_side_white" if color == chess.WHITE else "play_side_black"
            )
            button.setToolTip(
                t(color_key, language) + " " + t(name, language)
            )
        self._erase_button.setToolTip(t("edit_erase", language))
        self._edit_turn_label.setText(t("edit_turn_label", language))
        self._castling_label.setText(t("edit_castling_label", language))
        self._castling_label.setToolTip(t("edit_castling_hint", language))
        self._ep_label.setText(t("edit_ep_label", language))
        self._btn_edit_start.setText(t("btn_edit_start", language))
        self._btn_edit_empty.setText(t("btn_edit_empty", language))
        self._btn_edit_copy.setText(t("btn_edit_copy_fen", language))
        self._btn_edit_apply.setText(t("btn_edit_apply", language))
        self._btn_edit_cancel.setText(t("btn_edit_cancel", language))
        self._edit_hint.setText(t("edit_hint", language))
        self._edit_turn.blockSignals(True)
        current = self._edit_turn.currentData()
        self._edit_turn.clear()
        self._edit_turn.addItem(t("edit_side_white", language), chess.WHITE)
        self._edit_turn.addItem(t("edit_side_black", language), chess.BLACK)
        index = self._edit_turn.findData(current)
        self._edit_turn.setCurrentIndex(max(0, index))
        self._edit_turn.blockSignals(False)
        self._refresh_ep_options()

    def _refresh_palette_icons(self):
        for (color, piece_type), button in self._palette_buttons.items():
            pixmap = self._piece_pixmap(
                chess.Piece(piece_type, color), 22
            )
            button.setIcon(QIcon(pixmap) if pixmap is not None else QIcon())
        self._erase_button.setIcon(QIcon(self._erase_pixmap()))

    def _erase_pixmap(self):
        pixmap = QPixmap(22, 22)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        pen = QPen(QColor("#33363b"))
        pen.setWidthF(2.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(QPointF(6.0, 6.0), QPointF(16.0, 16.0))
        painter.drawLine(QPointF(16.0, 6.0), QPointF(6.0, 16.0))
        painter.end()
        return pixmap

    def load_pgn(self, pgn_text):
        self._end_edit()
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
        self._end_edit()
        self._start_fen = fen or None
        self._moves = []
        self._best_moves = {}
        self._index = 0
        self.render()

    def set_navigation_visible(self, visible):
        visible = bool(visible)
        self._nav_visible = visible
        if not visible and self._editable:
            self.cancel_edit()
        self._btn_edit.setVisible(visible and self._edit_available)
        self._nav.setVisible(visible)
        self._step_label.setVisible(visible)
        self._btn_flip.setMinimumWidth(0 if visible else 180)
        policy = QSizePolicy.Policy.Fixed if visible else QSizePolicy.Policy.Expanding
        for spacer in self._nav_spacers:
            spacer.changeSize(0, 0, policy, QSizePolicy.Policy.Minimum)

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
        self._end_edit()
        self._start_fen = None
        self._moves = []
        self._best_moves = {}
        self._index = 0
        self.render()

    def set_moves(self, moves, index=None, animate=False):
        self._end_edit()
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
            self._start_animation(self._moves[-1], forward=True)

    def set_interactive(self, enabled, human_color=None):
        self._interactive = enabled
        self._free_line = human_color is None
        if human_color is not None:
            self._human_color = human_color
            self._flipped = human_color == chess.BLACK
        else:
            self._human_color = None
        self.render()

    def set_edit_available(self, available):
        self._edit_available = bool(available)
        if not self._edit_available and self._editable:
            self.cancel_edit()
        self._btn_edit.setVisible(self._nav_visible and self._edit_available)

    def set_edit_enabled(self, enabled):
        self._btn_edit.setEnabled(bool(enabled))

    def is_editing(self):
        return self._editable

    def start_edit(self):
        if self._editable:
            return
        self._stop_animation()
        self._edit_backup = (self._start_fen, list(self._moves), self._index)
        self._editable = True
        self._edit_tool = None
        self._selected = None
        self._targets = set()
        self._board.halfmove_clock = 0
        self._board.fullmove_number = 1
        self._palette_group.setExclusive(False)
        for button in self._palette_group.buttons():
            button.setChecked(False)
        self._palette_group.setExclusive(True)
        self._sync_edit_controls()
        self._edit_bar.setVisible(True)
        self._btn_edit.setChecked(True)
        self.render()

    def apply_edit(self):
        if not self._editable:
            return None
        fen = self._board.fen()
        self._end_edit()
        self.set_start_fen(None if fen == chess.Board().fen() else fen)
        self.position_applied.emit(fen)
        return fen

    def cancel_edit(self):
        if not self._editable:
            return
        backup = self._edit_backup
        self._end_edit()
        if backup is not None:
            self._start_fen, moves, index = backup
            self._moves = list(moves)
            self._index = index
        self.render()
        self.index_changed.emit(self._index)

    def _end_edit(self):
        self._editable = False
        self._edit_tool = None
        self._edit_backup = None
        self._selected = None
        self._targets = set()
        self._edit_bar.setVisible(False)
        self._btn_edit.setChecked(False)

    def _on_edit_clicked(self, checked):
        if checked:
            self.start_edit()
        else:
            self.cancel_edit()

    def piece_at(self, square):
        return self._board.piece_at(square)

    def edit_place(self, square):
        tool = self._edit_tool
        if tool is None:
            return
        if tool == "erase":
            if self._board.piece_at(square) is not None:
                self._board.remove_piece_at(square)
        else:
            self._board.set_piece_at(square, chess.Piece(tool.piece_type, tool.color))
        self._canvas.update()

    def edit_move_piece(self, from_square, to_square):
        piece = self._board.piece_at(from_square)
        if piece is None:
            return
        self._board.remove_piece_at(from_square)
        self._board.set_piece_at(to_square, piece)
        self._canvas.update()

    def edit_remove(self, square):
        if self._board.piece_at(square) is not None:
            self._board.remove_piece_at(square)
            self._canvas.update()

    def _on_palette(self, tool):
        self._edit_tool = tool

    def _on_edit_turn(self, _index):
        color = self._edit_turn.currentData()
        if color is None:
            return
        self._board.turn = color
        self._refresh_ep_options()
        self._canvas.update()

    def _on_edit_castling(self, _checked):
        rights = chess.BB_EMPTY
        for box, right in self._castling_boxes:
            if box.isChecked():
                rights |= right
        self._board.castling_rights = rights
        self._canvas.update()

    def _on_edit_ep(self, _index):
        self._board.ep_square = self._ep_combo.currentData()
        self._canvas.update()

    def _edit_start(self):
        self._board = chess.Board()
        self._sync_edit_controls()
        self._canvas.update()

    def _edit_empty(self):
        self._board = chess.Board(None)
        self._sync_edit_controls()
        self._canvas.update()

    def _edit_copy_fen(self):
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(self._board.fen())
            self._edit_note.setText(t("edit_fen_copied", self._language))
            QTimer.singleShot(2000, self._clear_edit_note)

    def _clear_edit_note(self):
        self._edit_note.clear()

    def _sync_edit_controls(self):
        board = self._board
        self._edit_turn.blockSignals(True)
        self._edit_turn.setCurrentIndex(0 if board.turn == chess.WHITE else 1)
        self._edit_turn.blockSignals(False)
        for box, right in self._castling_boxes:
            box.blockSignals(True)
            box.setChecked(bool(board.castling_rights & right))
            box.blockSignals(False)
        self._refresh_ep_options()

    def _refresh_ep_options(self):
        board = self._board
        self._ep_combo.blockSignals(True)
        self._ep_combo.clear()
        self._ep_combo.addItem(t("edit_ep_none", self._language), None)
        ep_index = 0
        turn = board.turn
        rank = 5 if turn == chess.WHITE else 2
        pawn_rank = rank - 1 if turn == chess.WHITE else rank + 1
        enemy_pawn = chess.Piece(chess.PAWN, not turn)
        for file_index in range(8):
            square = chess.square(file_index, rank)
            if board.piece_at(chess.square(file_index, pawn_rank)) != enemy_pawn:
                continue
            if not any(
                board.piece_at(chess.square(neighbour, pawn_rank))
                == chess.Piece(chess.PAWN, turn)
                for neighbour in (file_index - 1, file_index + 1)
                if 0 <= neighbour <= 7
            ):
                continue
            probe = board.copy()
            probe.ep_square = square
            if not probe.has_legal_en_passant():
                continue
            self._ep_combo.addItem(chess.square_name(square), square)
            if square == board.ep_square:
                ep_index = self._ep_combo.count() - 1
        self._ep_combo.setCurrentIndex(ep_index)
        self._ep_combo.blockSignals(False)
        self._ep_combo.setEnabled(self._ep_combo.count() > 1)

    def play_move(self, from_square, to_square):
        piece = self._board.piece_at(from_square)
        if piece is None:
            return False
        promotion = None
        if (
            piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)
        ):
            promotion = self.promotion_choice(to_square, piece.color)
            if promotion is None:
                self.clear_selection()
                return False
        move = chess.Move(from_square, to_square, promotion=promotion)
        if move not in self._board.legal_moves:
            self.clear_selection()
            return False
        if self._index < len(self._moves) and self._moves[self._index] == move:
            self._index += 1
            self.render()
            self.index_changed.emit(self._index)
            return True
        replaced = self._index < len(self._moves)
        del self._moves[self._index :]
        self._moves.append(move)
        self._index = len(self._moves)
        self.render()
        self.line_changed.emit(replaced)
        self.index_changed.emit(self._index)
        return True

    def line_pgn(self):
        game = chess.pgn.Game()
        if self._start_fen:
            try:
                start = chess.Board(self._start_fen)
            except ValueError:
                start = None
            if start is not None:
                game.setup(start)
        node = game
        for move in self._moves:
            node = node.add_main_variation(move)
        return str(game)

    def clear_selection(self):
        self._selected = None
        self._targets = set()
        self._canvas.update()

    def set_paused(self, paused):
        self._paused = bool(paused)
        if self._paused:
            self.clear_selection()

    def can_pick(self, square):
        if not self._interactive or self._paused or self._editable:
            return False
        if not self._free_line and self._index != len(self._moves):
            return False
        board = self._board
        if board.is_game_over():
            return False
        if self._human_color is not None and board.turn != self._human_color:
            return False
        piece = board.piece_at(square)
        if piece is None:
            return False
        if self._human_color is not None and piece.color != self._human_color:
            return False
        return piece.color == board.turn

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

    def _start_animation(self, move, forward=True):
        board = self._board
        if forward:
            before = board.copy()
            try:
                before.pop()
            except IndexError:
                return
            piece = board.piece_at(move.to_square)
        else:
            before = board
            after = board.copy()
            try:
                after.push(move)
            except (ValueError, AssertionError):
                return
            piece = board.piece_at(move.from_square)
        if piece is None:
            return

        captured_square = move.to_square
        if before.is_en_passant(move):
            captured_square = chess.square(
                chess.square_file(move.to_square),
                chess.square_rank(move.from_square),
            )
        captured_piece = before.piece_at(captured_square)

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

        path_from, path_to = move.from_square, move.to_square
        if not forward:
            path_from, path_to = path_to, path_from
            if rook is not None:
                rook = (rook[1], rook[0])

        self._animation = {
            "piece": piece,
            "from": path_from,
            "to": path_to,
            "rook": rook,
            "captured_square": captured_square,
            "captured_piece": captured_piece,
            "fade_in": not forward,
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

    def goto(self, index, animate=True):
        if not self._moves or self._editable:
            return
        index = max(0, min(index, len(self._moves)))
        if index == self._index:
            return
        step = index - self._index
        self._index = index
        self.render()
        if animate and step in (1, -1):
            move = self._moves[index - 1] if step > 0 else self._moves[index]
            self._start_animation(move, forward=step > 0)
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
            (self._btn_edit, "edit"),
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
            self._refresh_palette_icons()
            self.render()

    def set_board_theme(self, name):
        if name in BOARD_THEMES:
            self._board_theme = name
            self.render()

    def render(self):
        self._stop_animation()
        self._selected = None
        self._targets = set()
        if not self._editable:
            if self._start_fen:
                try:
                    self._board = chess.Board(self._start_fen)
                except ValueError:
                    self._board = chess.Board()
            else:
                self._board = chess.Board()
            for move in self._moves[: self._index]:
                self._board.push(move)
            self._last_move = (
                self._moves[self._index - 1] if self._index > 0 else None
            )

        self._canvas.update()

        if self._index == 0:
            self._step_label.setText("")
        else:
            self._step_label.setText(
                t(
                    "board_step",
                    self._language,
                    index=self._index,
                    total=len(self._moves),
                )
            )

        self._nav.setEnabled(not self._editable)
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
        self._btn_edit.setToolTip(t("btn_edit_board", language))
        self._retranslate_edit_bar(language)
        self.render()
