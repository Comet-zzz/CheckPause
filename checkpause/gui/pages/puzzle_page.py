import chess
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.puzzle import PuzzleSession
from checkpause.data.puzzles import (
    PuzzleCollection,
    delete_collection,
    list_collections,
)
from checkpause.gui.widgets.board_widget import BoardWidget
from checkpause.gui.workers import PuzzleImportWorker
from checkpause.i18n import t


class PuzzlePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._collections = []
        self._collection = None
        self._index = 0
        self._puzzle = None
        self._session = None
        self._import_worker = None

        self.board = BoardWidget()
        self.board.set_navigation_visible(False)
        self.board.move_requested.connect(self._on_move_requested)

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
        self.refresh_collections()

    def _build_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        self._status_label = QLabel()
        self._status_label.setWordWrap(True)
        status_font = self._status_label.font()
        status_font.setBold(True)
        self._status_label.setFont(status_font)

        self._info_label = QLabel()
        self._info_label.setWordWrap(True)

        self._collections_label = QLabel()
        self._collection_list = QListWidget()
        self._collection_list.currentRowChanged.connect(
            self._on_collection_selected
        )

        self._btn_import = QPushButton()
        self._btn_import.clicked.connect(self._choose_file)
        self._btn_delete = QPushButton()
        self._btn_delete.clicked.connect(self._delete_current)

        self._btn_prev = QPushButton()
        self._btn_prev.clicked.connect(self._prev)
        self._btn_next = QPushButton()
        self._btn_next.clicked.connect(self._next)

        self._btn_hint = QPushButton()
        self._btn_hint.clicked.connect(self._show_hint)
        self._btn_solution = QPushButton()
        self._btn_solution.clicked.connect(self._reveal)
        self._btn_retry = QPushButton()
        self._btn_retry.clicked.connect(self._retry)

        collection_row = QHBoxLayout()
        collection_row.addWidget(self._btn_import)
        collection_row.addWidget(self._btn_delete)

        nav_row = QHBoxLayout()
        nav_row.addWidget(self._btn_prev)
        nav_row.addWidget(self._btn_next)

        solve_row = QHBoxLayout()
        solve_row.addWidget(self._btn_hint)
        solve_row.addWidget(self._btn_solution)
        solve_row.addWidget(self._btn_retry)

        layout.addWidget(self._status_label)
        layout.addWidget(self._info_label)
        layout.addWidget(self._collections_label)
        layout.addWidget(self._collection_list, 1)
        layout.addLayout(collection_row)
        layout.addLayout(nav_row)
        layout.addLayout(solve_row)
        return panel

    def refresh_collections(self, select_id=None):
        self._collections = [
            PuzzleCollection(meta) for meta in list_collections()
        ]
        self._collection_list.blockSignals(True)
        self._collection_list.clear()
        for collection in self._collections:
            self._collection_list.addItem(
                QListWidgetItem(
                    f"{self._display_name(collection)} ({collection.count})"
                )
            )
        target_row = 0
        if select_id:
            for row, collection in enumerate(self._collections):
                if collection.id == select_id:
                    target_row = row
                    break
        if self._collections:
            self._collection_list.setCurrentRow(target_row)
        self._collection_list.blockSignals(False)

        if self._collections:
            self._load_collection(self._collections[target_row])
        else:
            self._collection = None
            self._puzzle = None
            self._session = None
            self._index = 0
            self.board.clear()
            self.board.set_navigation_visible(False)
            self._info_label.clear()
            self._set_status(t("puzzle_empty", self._language))
            self._update_controls()

    def _on_collection_selected(self, row):
        if 0 <= row < len(self._collections):
            self._load_collection(self._collections[row])

    def _load_collection(self, collection):
        self._collection = collection
        self.board.set_navigation_visible(False)
        self._load_puzzle(0)

    def _load_puzzle(self, index):
        if self._collection is None:
            return
        puzzle = self._collection.get(index)
        if puzzle is None:
            self._puzzle = None
            self._session = None
            self._set_status(t("puzzle_status_bad_data", self._language))
            self._update_controls()
            return
        try:
            session = PuzzleSession(
                puzzle.get("fen", ""),
                puzzle.get("moves", []),
                bool(puzzle.get("opponent_first")),
            )
        except (ValueError, TypeError):
            self._puzzle = None
            self._session = None
            self._set_status(t("puzzle_status_bad_data", self._language))
            self._update_controls()
            return
        self._puzzle = puzzle
        self._session = session
        self._index = index
        self.board.set_start_fen(puzzle.get("fen", ""))
        self.board.set_interactive(True, session.human_color)
        self._sync_board(animate=False)
        self._update_info()
        self._update_controls()
        if session.solved:
            self._set_status(t("puzzle_status_solved", self._language))
        else:
            self._set_status("")

    def _sync_board(self, animate=False):
        if self._session is None:
            self.board.clear()
            return
        self.board.set_moves(self._session.applied_moves, animate=animate)

    def _update_info(self):
        if self._collection is None or self._puzzle is None:
            self._info_label.clear()
            return
        lines = [
            t(
                "puzzle_info",
                self._language,
                name=self._display_name(self._collection),
                index=self._index + 1,
                total=self._collection.count,
            )
        ]
        rating = self._puzzle.get("rating")
        if rating:
            lines.append(
                t("puzzle_rating", self._language, rating=rating)
            )
        themes = self._puzzle.get("themes") or []
        if themes:
            lines.append(
                t("puzzle_themes", self._language, themes=", ".join(themes))
            )
        self._info_label.setText("\n".join(lines))

    def _on_move_requested(self, from_square, to_square):
        session = self._session
        if session is None or session.solved or not session.is_human_turn:
            self.board.clear_selection()
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

        status = session.play(move)
        self.board.clear_selection()
        if status == "wrong":
            self._set_status(t("puzzle_status_wrong", self._language))
            return

        self._sync_board(animate=True)
        self._update_controls()
        if session.solved:
            self._set_status(t("puzzle_status_solved", self._language))
        else:
            self._set_status(t("puzzle_status_correct", self._language))
            QTimer.singleShot(220, lambda s=session: self._play_reply(s))

    def _play_reply(self, session):
        if session is not self._session or session.solved:
            return
        if session.opponent_reply() is None:
            return
        self._sync_board(animate=True)
        if session.solved:
            self._set_status(t("puzzle_status_solved", self._language))
        self._update_controls()

    def _show_hint(self):
        if self._session is None or self._session.solved:
            return
        uci = self._session.expected_move
        if not uci:
            return
        self.board.set_hint(uci)
        self._set_status(
            t("puzzle_status_hint", self._language, move=uci)
        )

    def _reveal(self):
        session = self._session
        if session is None or session.solved:
            return
        while not session.solved:
            uci = session.expected_move
            if not uci:
                break
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                break
            if move not in session.board.legal_moves:
                break
            if session.is_human_turn:
                if session.play(move) == "wrong":
                    break
            elif session.opponent_reply() is None:
                break
        self.board.clear_hint()
        self._sync_board(animate=False)
        self._update_controls()
        if session.solved:
            self._set_status(t("puzzle_status_revealed", self._language))
        else:
            self._set_status(t("puzzle_status_bad_data", self._language))

    def _retry(self):
        if self._puzzle is not None:
            self._load_puzzle(self._index)

    def _prev(self):
        if self._collection is not None and self._index > 0:
            self._load_puzzle(self._index - 1)

    def _next(self):
        if (
            self._collection is not None
            and self._index + 1 < self._collection.count
        ):
            self._load_puzzle(self._index + 1)

    def _choose_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("puzzle_import_title", self._language),
            "",
            t("puzzle_import_filter", self._language),
        )
        if path:
            self._start_import(path)

    def _start_import(self, path):
        if self._import_worker is not None and self._import_worker.isRunning():
            return
        self._btn_import.setEnabled(False)
        self._set_status(t("puzzle_status_loading", self._language))
        self._import_worker = PuzzleImportWorker(path, parent=self)
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.done.connect(self._on_import_done)
        self._import_worker.failed.connect(self._on_import_failed)
        self._import_worker.finished.connect(self._on_import_finished)
        self._import_worker.start()

    def _on_import_progress(self, count):
        self._set_status(
            t("puzzle_status_importing", self._language, count=count)
        )

    def _on_import_done(self, meta):
        self._set_status(
            t(
                "puzzle_status_imported",
                self._language,
                count=meta.get("count", 0),
            )
        )
        self.refresh_collections(select_id=meta.get("id"))

    def _on_import_failed(self, code, detail):
        key = "puzzle_import_error_" + (code or "read_error")
        if code == "read_error" and detail:
            message = t(key, self._language, error=detail)
        else:
            message = t(key, self._language)
        self._set_status(message)

    def _on_import_finished(self):
        self._btn_import.setEnabled(True)
        worker = self._import_worker
        self._import_worker = None
        if worker is not None:
            worker.deleteLater()

    def _delete_current(self):
        if self._collection is None:
            return
        answer = QMessageBox.question(
            self,
            t("puzzle_delete_title", self._language),
            t(
                "puzzle_delete_text",
                self._language,
                name=self._display_name(self._collection),
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete_collection(self._collection.id)
        self._collection = None
        self._puzzle = None
        self._session = None
        self.refresh_collections()

    def _set_status(self, text):
        self._status_label.setText(text)
        self._status_label.setVisible(bool(text))

    def _display_name(self, collection):
        if collection.builtin:
            return t("puzzle_builtin_name", self._language)
        return collection.name

    def _update_controls(self):
        has_session = self._session is not None
        solved = bool(self._session and self._session.solved)
        self._btn_hint.setEnabled(has_session and not solved)
        self._btn_solution.setEnabled(has_session and not solved)
        self._btn_retry.setEnabled(has_session)
        self._btn_delete.setEnabled(self._collection is not None)
        self._btn_prev.setEnabled(
            self._collection is not None and self._index > 0
        )
        self._btn_next.setEnabled(
            self._collection is not None
            and self._index + 1 < self._collection.count
        )

    def set_theme(self, theme):
        self.board.set_theme(theme)

    def set_piece_set(self, name):
        self.board.set_piece_set(name)

    def set_board_theme(self, name):
        self.board.set_board_theme(name)

    def reset(self):
        self._collection = None
        self._puzzle = None
        self._session = None
        self._index = 0
        self.board.clear()
        self.board.set_navigation_visible(False)
        self.refresh_collections()

    def shutdown(self):
        worker = self._import_worker
        self._import_worker = None
        if worker is not None and worker.isRunning():
            worker.wait(5000)

    def retranslate(self, language):
        self._language = language
        self.board.retranslate(language)
        self._collections_label.setText(
            t("puzzle_collections", language)
        )
        self._btn_import.setText(t("puzzle_import", language))
        self._btn_delete.setText(t("puzzle_delete", language))
        self._btn_prev.setText(t("puzzle_prev", language))
        self._btn_next.setText(t("puzzle_next", language))
        self._btn_hint.setText(t("puzzle_hint", language))
        self._btn_solution.setText(t("puzzle_solution", language))
        self._btn_retry.setText(t("puzzle_retry", language))
        for row, collection in enumerate(self._collections):
            item = self._collection_list.item(row)
            if item is not None:
                item.setText(
                    f"{self._display_name(collection)} ({collection.count})"
                )
        if self._puzzle is not None:
            self._update_info()
        elif self._collection is None:
            self._set_status(t("puzzle_empty", language))
        self._update_controls()
