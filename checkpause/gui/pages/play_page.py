import chess
import chess.pgn
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from checkpause.config import DEFAULT_PLAY_LEVEL, ENGINE_PLAY_LEVELS
from checkpause.gui.dialogs import promotion_dialog
from checkpause.gui.widgets.board_widget import BoardWidget
from checkpause.gui.widgets.move_list import MoveListWidget
from checkpause.gui.workers import EngineMoveWorker
from checkpause.i18n import t


class PlayPage(QWidget):
    analysis_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._human_color = chess.WHITE
        self._level_id = DEFAULT_PLAY_LEVEL
        self._game = chess.Board()
        self._moves = []
        self._game_over = False
        self._result_kind = None
        self._engine_worker = None
        self._engine_error = None

        self.board = BoardWidget()
        self.board.move_requested.connect(self._on_move_requested)
        self._move_list = MoveListWidget()
        self._move_list.ply_selected.connect(self.board.goto)
        self.board.index_changed.connect(self._move_list.set_current_ply)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.board)
        splitter.addWidget(self._build_panel())
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([760, 520])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.retranslate(self._language)
        self._new_game()

    def _build_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        status_font = self._status_label.font()
        status_font.setBold(True)
        self._status_label.setFont(status_font)

        self._side_label = QLabel()
        self._side_combo = QComboBox()
        self._side_combo.currentIndexChanged.connect(self._on_side_changed)

        self._level_label = QLabel()
        self._level_combo = QComboBox()
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)

        self._btn_new = QPushButton()
        self._btn_new.clicked.connect(self._new_game)
        self._btn_undo = QPushButton()
        self._btn_undo.clicked.connect(self._undo)
        self._btn_resign = QPushButton()
        self._btn_resign.clicked.connect(self._resign)
        self._btn_import = QPushButton()
        self._btn_import.clicked.connect(self._import_to_analysis)

        controls = QGridLayout()
        controls.addWidget(self._side_label, 0, 0)
        controls.addWidget(self._side_combo, 0, 1)
        controls.addWidget(self._level_label, 0, 2)
        controls.addWidget(self._level_combo, 0, 3)
        controls.addWidget(self._btn_new, 1, 0, 1, 2)
        controls.addWidget(self._btn_import, 1, 2, 1, 2)

        buttons = QHBoxLayout()
        buttons.addWidget(self._btn_undo)
        buttons.addWidget(self._btn_resign)

        self._result_label = QLabel()
        self._result_label.setWordWrap(True)

        layout.addWidget(self._status_label)
        layout.addLayout(controls)
        layout.addLayout(buttons)
        layout.addWidget(self._move_list, 1)
        layout.addWidget(self._result_label)
        return panel

    def _new_game(self):
        self._stop_engine_worker()
        self._engine_error = None
        self._game = chess.Board()
        self._moves = []
        self._game_over = False
        self._result_kind = None
        self.board.set_interactive(True, self._human_color)
        self._sync_views()
        self._render_result()
        self._update_buttons()
        if self._human_color == chess.BLACK:
            self._start_engine()
        else:
            self._update_status()

    def _sync_views(self):
        self.board.clear_selection()
        self.board.set_moves(self._moves)
        if self._moves:
            self._move_list.set_moves(self._pgn())
            self._move_list.set_current_ply(len(self._moves))
        else:
            self._move_list.clear()

    def _pgn(self):
        return str(chess.pgn.Game.from_board(self._game))

    def _level(self):
        for level in ENGINE_PLAY_LEVELS:
            if level["id"] == self._level_id:
                return level
        return ENGINE_PLAY_LEVELS[0]

    def _on_side_changed(self, _index):
        color = self._side_combo.currentData()
        if color is None or color == self._human_color:
            return
        self._human_color = color
        self._new_game()

    def _on_level_changed(self, _index):
        level_id = self._level_combo.currentData()
        if level_id:
            self._level_id = level_id

    def _on_move_requested(self, from_square, to_square):
        if self._game_over or self._engine_worker is not None:
            return
        if self._game.turn != self._human_color:
            return

        move = chess.Move(from_square, to_square)
        piece = self._game.piece_at(from_square)
        if (
            piece is not None
            and piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)
        ):
            promotion = promotion_dialog(self, self._language)
            if promotion is None:
                self.board.clear_selection()
                return
            move = chess.Move(from_square, to_square, promotion=promotion)

        if move not in self._game.legal_moves:
            self.board.clear_selection()
            return
        self._push_move(move)

    def _push_move(self, move):
        self._game.push(move)
        self._moves.append(move)
        self._sync_views()
        if self._finish_if_over():
            return
        if self._game.turn != self._human_color:
            self._start_engine()
        else:
            self._update_status()
            self._update_buttons()

    def _start_engine(self):
        self._engine_error = None
        worker = EngineMoveWorker(
            self._game.fen(), self._level(), self._language, self
        )
        worker.move_ready.connect(self._on_engine_move)
        worker.failed.connect(self._on_engine_failed)
        worker.finished.connect(self._on_engine_finished)
        self._engine_worker = worker
        self._update_status()
        self._update_buttons()
        worker.start()

    def _on_engine_move(self, uci):
        if self.sender() is not self._engine_worker:
            return
        if self._game_over:
            return
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return
        if move not in self._game.legal_moves:
            return
        self._game.push(move)
        self._moves.append(move)
        self._sync_views()
        if self._finish_if_over():
            return
        self._update_status()
        self._update_buttons()

    def _on_engine_failed(self, error):
        if self.sender() is not self._engine_worker:
            return
        self._engine_error = error
        self._update_status()

    def _on_engine_finished(self):
        worker = self.sender()
        if worker is self._engine_worker:
            self._engine_worker = None
        worker.deleteLater()
        self._update_status()
        self._update_buttons()

    def _finish_if_over(self):
        if not self._game.is_game_over():
            return False
        self._game_over = True
        outcome = self._game.outcome()
        if outcome is None or outcome.winner is None:
            self._result_kind = "draw"
        elif outcome.winner == self._human_color:
            self._result_kind = "win"
        else:
            self._result_kind = "lose"
        self.board.clear_selection()
        self._render_result()
        self._update_status()
        self._update_buttons()
        return True

    def _undo(self):
        if self._engine_worker is not None or self._game_over:
            return
        if not self._moves:
            return
        self._game.pop()
        self._moves.pop()
        if self._moves and self._game.turn != self._human_color:
            self._game.pop()
            self._moves.pop()
        self._result_kind = None
        self._engine_error = None
        self._sync_views()
        self._render_result()
        self._update_buttons()
        if self._game.turn != self._human_color:
            self._start_engine()
        else:
            self._update_status()

    def _resign(self):
        if self._game_over:
            return
        self._game_over = True
        self._result_kind = "resign"
        self.board.clear_selection()
        self._render_result()
        self._update_status()
        self._update_buttons()

    def _import_to_analysis(self):
        if self._moves:
            self.analysis_requested.emit(self._pgn())

    def _render_result(self):
        if self._result_kind is None:
            self._result_label.clear()
        else:
            self._result_label.setText(
                t("play_result_" + self._result_kind, self._language)
            )

    def _update_status(self):
        if self._game_over:
            self._status_label.setText(
                t("play_status_game_over", self._language)
            )
            return
        if self._engine_error:
            self._status_label.setText(
                t(
                    "play_engine_error",
                    self._language,
                    error=self._engine_error,
                )
            )
            return
        if self._engine_worker is not None and self._engine_worker.isRunning():
            self._status_label.setText(
                t("play_status_thinking", self._language)
            )
            return
        if self._game.is_check():
            self._status_label.setText(t("play_status_check", self._language))
        else:
            self._status_label.setText(
                t("play_status_your_turn", self._language)
            )

    def _update_buttons(self):
        thinking = (
            self._engine_worker is not None
            and self._engine_worker.isRunning()
        )
        self._btn_undo.setEnabled(
            bool(self._moves) and not thinking and not self._game_over
        )
        self._btn_resign.setEnabled(not self._game_over)
        self._btn_import.setEnabled(bool(self._moves))

    def set_theme(self, theme):
        self.board.set_theme(theme)
        self._move_list.set_theme(theme)

    def set_piece_set(self, name):
        self.board.set_piece_set(name)

    def set_board_theme(self, name):
        self.board.set_board_theme(name)

    def reset(self):
        self._human_color = chess.WHITE
        self._level_id = DEFAULT_PLAY_LEVEL
        self._side_combo.blockSignals(True)
        side_index = self._side_combo.findData(chess.WHITE)
        self._side_combo.setCurrentIndex(max(0, side_index))
        self._side_combo.blockSignals(False)
        self._level_combo.blockSignals(True)
        level_index = self._level_combo.findData(DEFAULT_PLAY_LEVEL)
        self._level_combo.setCurrentIndex(max(0, level_index))
        self._level_combo.blockSignals(False)
        self._new_game()

    def _stop_engine_worker(self):
        worker = self._engine_worker
        self._engine_worker = None
        if worker is not None and worker.isRunning():
            worker.wait(5000)

    def shutdown(self):
        self._stop_engine_worker()

    def retranslate(self, language):
        self._language = language
        self.board.retranslate(language)

        self._side_combo.blockSignals(True)
        self._side_combo.clear()
        self._side_combo.addItem(t("play_side_white", language), chess.WHITE)
        self._side_combo.addItem(t("play_side_black", language), chess.BLACK)
        side_index = self._side_combo.findData(self._human_color)
        self._side_combo.setCurrentIndex(max(0, side_index))
        self._side_combo.blockSignals(False)

        self._level_combo.blockSignals(True)
        self._level_combo.clear()
        for level in ENGINE_PLAY_LEVELS:
            self._level_combo.addItem(
                t("play_level_" + level["id"], language), level["id"]
            )
        level_index = self._level_combo.findData(self._level_id)
        self._level_combo.setCurrentIndex(max(0, level_index))
        self._level_combo.blockSignals(False)

        self._side_label.setText(t("play_side_label", language))
        self._level_label.setText(t("play_level_label", language))
        self._btn_new.setText(t("play_new_game", language))
        self._btn_undo.setText(t("play_undo", language))
        self._btn_resign.setText(t("play_resign", language))
        self._btn_import.setText(t("play_import", language))

        self._render_result()
        self._update_status()
        self._update_buttons()
