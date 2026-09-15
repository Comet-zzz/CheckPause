import time

import chess
import chess.pgn
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from checkpause.config import (
    DEFAULT_PLAY_LEVEL,
    DEFAULT_PLAY_TIME,
    ENGINE_PLAY_LEVELS,
    PLAY_TIME_CONTROLS,
)
from checkpause.core.endgames import load_endgames
from checkpause.core.openings import load_openings
from checkpause.core.play_session import PlaySession
from checkpause.gui.widgets.board import BoardWidget
from checkpause.gui.widgets.move_list import MoveListWidget
from checkpause.gui.workers import EngineMoveWorker
from checkpause.i18n import t

CLOCK_TICK_MS = 100


class PlayPage(QWidget):
    analysis_requested = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._level_id = DEFAULT_PLAY_LEVEL
        self._time_id = DEFAULT_PLAY_TIME
        self._opening_index = 0
        self._endgame_index = 0
        self._openings = load_openings()
        self._endgames = load_endgames()
        self._session = PlaySession()
        self._engine_worker = None
        self._engine_error = None
        self._clock_active = "unset"

        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(CLOCK_TICK_MS)
        self._clock_timer.timeout.connect(self._on_clock_tick)

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

        self._clock_white = QLabel()
        self._clock_black = QLabel()
        for clock in (self._clock_white, self._clock_black):
            clock_font = clock.font()
            clock_font.setPointSize(clock_font.pointSize() + 2)
            clock.setFont(clock_font)
        clock_row = QHBoxLayout()
        clock_row.addWidget(self._clock_white)
        clock_row.addStretch(1)
        self._btn_pause = QPushButton()
        self._btn_pause.clicked.connect(self._toggle_pause)
        clock_row.addWidget(self._btn_pause)
        clock_row.addStretch(1)
        clock_row.addWidget(self._clock_black)
        self._clock_row = QWidget()
        self._clock_row.setLayout(clock_row)

        self._side_label = QLabel()
        self._side_combo = QComboBox()
        self._side_combo.currentIndexChanged.connect(self._on_side_changed)

        self._level_label = QLabel()
        self._level_combo = QComboBox()
        self._level_combo.currentIndexChanged.connect(self._on_level_changed)

        self._time_label = QLabel()
        self._time_combo = QComboBox()
        self._time_combo.currentIndexChanged.connect(self._on_time_changed)

        self._opening_label = QLabel()
        self._opening_combo = QComboBox()
        self._opening_combo.currentIndexChanged.connect(
            self._on_opening_changed
        )

        self._endgame_label = QLabel()
        self._endgame_combo = QComboBox()
        self._endgame_combo.currentIndexChanged.connect(
            self._on_endgame_changed
        )

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
        controls.addWidget(self._time_label, 1, 0)
        controls.addWidget(self._time_combo, 1, 1)
        controls.addWidget(self._opening_label, 2, 0)
        controls.addWidget(self._opening_combo, 2, 1, 1, 3)
        controls.addWidget(self._endgame_label, 3, 0)
        controls.addWidget(self._endgame_combo, 3, 1, 1, 3)
        controls.addWidget(self._btn_new, 4, 0, 1, 2)
        controls.addWidget(self._btn_import, 4, 2, 1, 2)

        buttons = QHBoxLayout()
        buttons.addWidget(self._btn_undo)
        buttons.addWidget(self._btn_resign)

        self._result_label = QLabel()
        self._result_label.setWordWrap(True)

        layout.addWidget(self._clock_row)
        layout.addLayout(controls)
        layout.addLayout(buttons)
        layout.addWidget(self._move_list, 1)
        layout.addWidget(self._result_label)
        return panel

    def _new_game(self):
        self._stop_engine_worker()
        self._engine_error = None
        endgame = self._selected_endgame()
        opening = None if endgame is not None else self._selected_opening()
        self._session.new_game(
            human_color=self._session.human_color,
            start_fen=endgame["fen"] if endgame is not None else None,
            opening_moves=opening["moves"] if opening is not None else (),
            time_control=self._time_control(),
            now=time.monotonic(),
        )
        self.board.set_start_fen(self._session.start_fen)
        self.board.set_paused(False)
        self.board.set_interactive(True, self._session.human_color)
        self._sync_views()
        self._render_result()
        self._update_pause_button()
        self._update_buttons()
        self._sync_clock_timer()
        if self._session.board.turn != self._session.human_color:
            self._start_engine()

    def _sync_views(self, animate=False):
        moves = self._session.moves
        self.board.clear_selection()
        self.board.set_moves(moves, animate=animate)
        if moves:
            self._move_list.set_moves(self._pgn())
            self._move_list.set_current_ply(len(moves))
        else:
            self._move_list.clear()

    def _pgn(self):
        return str(chess.pgn.Game.from_board(self._session.board))

    def _level(self):
        for level in ENGINE_PLAY_LEVELS:
            if level["id"] == self._level_id:
                return level
        return ENGINE_PLAY_LEVELS[0]

    def _time_control(self):
        for control in PLAY_TIME_CONTROLS:
            if control["id"] == self._time_id:
                return control
        return PLAY_TIME_CONTROLS[0]

    def _selected_opening(self):
        if 1 <= self._opening_index <= len(self._openings):
            return self._openings[self._opening_index - 1]
        return None

    def _selected_endgame(self):
        if 1 <= self._endgame_index <= len(self._endgames):
            return self._endgames[self._endgame_index - 1]
        return None

    def _sync_clock_timer(self):
        if not self._session.clock_should_run():
            self._clock_timer.stop()
            return
        if not self._clock_timer.isActive():
            self._session.start_clock(time.monotonic())
            self._clock_timer.start()

    def _reset_clock(self):
        self._session.set_time_control(self._time_control())
        self._session.reset_clock(time.monotonic())
        self._sync_clock_timer()
        self._update_clock_labels()

    def _on_clock_tick(self):
        flagged = self._session.tick(time.monotonic())
        if flagged is not None:
            self._session.timeout(flagged)
            self._clock_timer.stop()
            self.board.clear_selection()
            self._render_result()
            self._update_buttons()
        self._update_clock_labels()

    def _update_clock_labels(self):
        session = self._session
        self._clock_row.setVisible(session.clock_enabled)
        if not session.clock_enabled:
            return
        active = (
            None
            if session.game_over or session.paused or not session.moves
            else session.board.turn
        )
        active_changed = active != self._clock_active
        self._clock_active = active
        for color, label in (
            (chess.WHITE, self._clock_white),
            (chess.BLACK, self._clock_black),
        ):
            key = (
                "play_clock_white"
                if color == chess.WHITE
                else "play_clock_black"
            )
            label.setText(
                f"{t(key, self._language)} "
                f"{PlaySession.format_clock(session.clock_remaining[color])}"
            )
            if active_changed:
                label.setStyleSheet(
                    "font-weight: bold;"
                    if color == active
                    else "color: #8a8a8a;"
                )

    def _toggle_pause(self):
        self._session.toggle_pause()
        if self._session.paused:
            self._clock_timer.stop()
        else:
            self._sync_clock_timer()
        self.board.set_paused(self._session.paused)
        self._update_pause_button()
        self._update_clock_labels()
        self._update_buttons()

    def _update_pause_button(self):
        key = "play_resume" if self._session.paused else "play_pause"
        tooltip_key = (
            "play_resume_tooltip"
            if self._session.paused
            else "play_pause_tooltip"
        )
        self._btn_pause.setText(t(key, self._language))
        self._btn_pause.setToolTip(t(tooltip_key, self._language))

    def _on_time_changed(self, _index):
        time_id = self._time_combo.currentData()
        if time_id:
            self._time_id = time_id
            self._reset_clock()

    def _on_opening_changed(self, index):
        if index < 0:
            return
        self._opening_index = index
        if index > 0 and self._endgame_index != 0:
            self._endgame_combo.blockSignals(True)
            self._endgame_combo.setCurrentIndex(0)
            self._endgame_combo.blockSignals(False)
            self._endgame_index = 0
        self._new_game()

    def _on_endgame_changed(self, index):
        if index < 0:
            return
        self._endgame_index = index
        if index > 0 and self._opening_index != 0:
            self._opening_combo.blockSignals(True)
            self._opening_combo.setCurrentIndex(0)
            self._opening_combo.blockSignals(False)
            self._opening_index = 0
        self._new_game()

    def _on_side_changed(self, _index):
        color = self._side_combo.currentData()
        if color is None or color == self._session.human_color:
            return
        self._session.human_color = color
        self._new_game()

    def _on_level_changed(self, _index):
        level_id = self._level_combo.currentData()
        if level_id:
            self._level_id = level_id

    def _on_move_requested(self, from_square, to_square):
        session = self._session
        if (
            session.paused
            or session.game_over
            or self._engine_worker is not None
        ):
            return
        if session.board.turn != session.human_color:
            return

        move = chess.Move(from_square, to_square)
        piece = session.board.piece_at(from_square)
        if (
            piece is not None
            and piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)
        ):
            promotion = self.board.promotion_choice(
                to_square, piece.color
            )
            if promotion is None:
                self.board.clear_selection()
                return
            move = chess.Move(from_square, to_square, promotion=promotion)

        if move not in session.board.legal_moves:
            self.board.clear_selection()
            return
        self._push_move(move)

    def _push_move(self, move):
        self._session.push(move)
        self._sync_clock_timer()
        self._sync_views(animate=True)
        if self._finish_if_over():
            return
        if self._session.board.turn != self._session.human_color:
            self._start_engine()
        else:
            self._update_buttons()

    def _start_engine(self):
        self._engine_error = None
        worker = EngineMoveWorker(
            self._session.board.fen(), self._level(), self._language, self
        )
        worker.move_ready.connect(self._on_engine_move)
        worker.failed.connect(self._on_engine_failed)
        worker.finished.connect(self._on_engine_finished)
        self._engine_worker = worker
        self._update_buttons()
        worker.start()

    def _on_engine_move(self, uci):
        if self.sender() is not self._engine_worker:
            return
        if self._session.game_over:
            return
        try:
            move = chess.Move.from_uci(uci)
        except ValueError:
            return
        if move not in self._session.board.legal_moves:
            return
        self._session.push(move)
        self._sync_clock_timer()
        self._sync_views(animate=True)
        if self._finish_if_over():
            return
        self._update_buttons()

    def _on_engine_failed(self, error):
        if self.sender() is not self._engine_worker:
            return
        self._engine_error = error
        self._clock_timer.stop()
        self._update_clock_labels()
        QMessageBox.warning(
            self,
            t("app_title", self._language),
            t("play_engine_error", self._language, error=error),
        )

    def _on_engine_finished(self):
        worker = self.sender()
        if worker is self._engine_worker:
            self._engine_worker = None
        worker.deleteLater()
        self._update_buttons()

    def _finish_if_over(self):
        if not self._session.finish_if_over():
            return False
        self._clock_timer.stop()
        self._update_clock_labels()
        self.board.clear_selection()
        self._render_result()
        self._update_buttons()
        return True

    def _undo(self):
        session = self._session
        if (
            self._engine_worker is not None
            or session.game_over
            or session.paused
        ):
            return
        if not session.undo():
            return
        self._engine_error = None
        self._sync_views()
        self._sync_clock_timer()
        self._update_clock_labels()
        self._render_result()
        self._update_buttons()
        if session.board.turn != session.human_color:
            self._start_engine()

    def _resign(self):
        if self._session.game_over:
            return
        self._session.resign()
        self._clock_timer.stop()
        self._update_clock_labels()
        self.board.clear_selection()
        self._render_result()
        self._update_buttons()

    def _import_to_analysis(self):
        if self._session.moves:
            self.analysis_requested.emit(self._pgn())

    def _render_result(self):
        if self._session.result_kind is None:
            self._result_label.clear()
        else:
            self._result_label.setText(
                t(
                    "play_result_" + self._session.result_kind,
                    self._language,
                )
            )

    def _update_buttons(self):
        session = self._session
        thinking = (
            self._engine_worker is not None
            and self._engine_worker.isRunning()
        )
        self._btn_undo.setEnabled(
            session.can_undo()
            and not thinking
            and not session.game_over
            and not session.paused
        )
        self._btn_resign.setEnabled(not session.game_over)
        self._btn_pause.setEnabled(
            not session.game_over and not thinking
        )
        self._btn_import.setEnabled(bool(session.moves))

    def set_theme(self, theme):
        self.board.set_theme(theme)
        self._move_list.set_theme(theme)

    def set_piece_set(self, name):
        self.board.set_piece_set(name)

    def set_board_theme(self, name):
        self.board.set_board_theme(name)

    def reset(self):
        self._session.human_color = chess.WHITE
        self._level_id = DEFAULT_PLAY_LEVEL
        self._time_id = DEFAULT_PLAY_TIME
        self._opening_index = 0
        self._endgame_index = 0
        self._side_combo.blockSignals(True)
        side_index = self._side_combo.findData(chess.WHITE)
        self._side_combo.setCurrentIndex(max(0, side_index))
        self._side_combo.blockSignals(False)
        self._level_combo.blockSignals(True)
        level_index = self._level_combo.findData(DEFAULT_PLAY_LEVEL)
        self._level_combo.setCurrentIndex(max(0, level_index))
        self._level_combo.blockSignals(False)
        self._time_combo.blockSignals(True)
        time_index = self._time_combo.findData(DEFAULT_PLAY_TIME)
        self._time_combo.setCurrentIndex(max(0, time_index))
        self._time_combo.blockSignals(False)
        self._opening_combo.blockSignals(True)
        if self._opening_combo.count():
            self._opening_combo.setCurrentIndex(0)
        self._opening_combo.blockSignals(False)
        self._endgame_combo.blockSignals(True)
        if self._endgame_combo.count():
            self._endgame_combo.setCurrentIndex(0)
        self._endgame_combo.blockSignals(False)
        self._new_game()

    def _stop_engine_worker(self):
        worker = self._engine_worker
        self._engine_worker = None
        if worker is not None and worker.isRunning():
            worker.wait(5000)

    def shutdown(self):
        self._stop_engine_worker()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_clock_timer()

    def hideEvent(self, event):
        self._clock_timer.stop()
        super().hideEvent(event)

    def retranslate(self, language):
        self._language = language
        self.board.retranslate(language)

        self._side_combo.blockSignals(True)
        self._side_combo.clear()
        self._side_combo.addItem(t("play_side_white", language), chess.WHITE)
        self._side_combo.addItem(t("play_side_black", language), chess.BLACK)
        side_index = self._side_combo.findData(self._session.human_color)
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

        self._time_combo.blockSignals(True)
        self._time_combo.clear()
        for control in PLAY_TIME_CONTROLS:
            self._time_combo.addItem(
                t("play_time_" + control["id"], language), control["id"]
            )
        time_index = self._time_combo.findData(self._time_id)
        self._time_combo.setCurrentIndex(max(0, time_index))
        self._time_combo.blockSignals(False)

        self._opening_combo.blockSignals(True)
        self._opening_combo.clear()
        self._opening_combo.addItem(
            t("play_opening_standard", language), None
        )
        for opening in self._openings:
            self._opening_combo.addItem(opening["name"], opening["name"])
        opening_index = max(
            0, min(self._opening_index, self._opening_combo.count() - 1)
        )
        self._opening_index = opening_index
        self._opening_combo.setCurrentIndex(opening_index)
        self._opening_combo.blockSignals(False)

        self._endgame_combo.blockSignals(True)
        self._endgame_combo.clear()
        self._endgame_combo.addItem(
            t("play_endgame_standard", language), None
        )
        for endgame in self._endgames:
            self._endgame_combo.addItem(
                t("play_endgame_" + endgame["id"], language), endgame["id"]
            )
        endgame_index = max(
            0, min(self._endgame_index, self._endgame_combo.count() - 1)
        )
        self._endgame_index = endgame_index
        self._endgame_combo.setCurrentIndex(endgame_index)
        self._endgame_combo.blockSignals(False)

        self._side_label.setText(t("play_side_label", language))
        self._level_label.setText(t("play_level_label", language))
        self._time_label.setText(t("play_time_label", language))
        self._opening_label.setText(t("play_opening_label", language))
        self._endgame_label.setText(t("play_endgame_label", language))
        self._btn_new.setText(t("play_new_game", language))
        self._btn_undo.setText(t("play_undo", language))
        self._btn_resign.setText(t("play_resign", language))
        self._btn_import.setText(t("play_import", language))

        self._render_result()
        self._update_pause_button()
        self._update_clock_labels()
        self._update_buttons()
