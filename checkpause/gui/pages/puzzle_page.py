import chess
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
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
    FAVORITES_ID,
    PuzzleCollection,
    add_favorite,
    delete_collection,
    favorite_keys,
    favorites_collection,
    list_collections,
    mark_solved,
    puzzle_key,
    solved_indices,
    toggle_favorite,
)
from checkpause.gui.widgets.board import BoardWidget
from checkpause.gui.workers import PuzzleImportWorker
from checkpause.i18n import t


class PuzzlePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._collections = []
        self._info_items = []
        self._solved = set()
        self._collection = None
        self._index = 0
        self._puzzle = None
        self._session = None
        self._import_worker = None
        self._favorite_keys = set()

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
        self._btn_favorite = QPushButton()
        self._btn_favorite.clicked.connect(self._toggle_favorite)
        self._btn_retry = QPushButton()
        self._btn_retry.clicked.connect(self._retry)

        self._jump_edit = QLineEdit()
        self._jump_edit.setFixedWidth(48)
        self._jump_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._jump_edit.returnPressed.connect(self._on_jump)
        self._jump_total = QLabel()
        self._jump_total.setStyleSheet("color: gray;")
        self._btn_jump = QPushButton()
        self._btn_jump.clicked.connect(self._on_jump)

        jump_box = QWidget()
        jump_layout = QHBoxLayout(jump_box)
        jump_layout.setContentsMargins(0, 0, 0, 0)
        jump_layout.setSpacing(4)
        jump_layout.addWidget(self._jump_edit)
        jump_layout.addWidget(self._jump_total)
        jump_layout.addWidget(self._btn_jump)
        self._jump_box = jump_box

        solve_box = QWidget()
        solve_layout = QHBoxLayout(solve_box)
        solve_layout.setContentsMargins(0, 0, 0, 0)
        solve_layout.addWidget(self._btn_hint)
        solve_layout.addWidget(self._btn_retry)
        solve_layout.addWidget(self._btn_favorite)
        self._solve_box = solve_box

        collection_row = QHBoxLayout()
        collection_row.addWidget(self._btn_import)
        collection_row.addWidget(self._btn_delete)

        nav_row = QHBoxLayout()
        nav_row.addWidget(self._btn_prev, 1)
        nav_row.addWidget(jump_box)
        nav_row.addWidget(self._btn_next, 1)

        layout.addWidget(self._status_label)
        layout.addWidget(self._collections_label)
        layout.addLayout(collection_row)
        layout.addWidget(self._collection_list, 1)
        layout.addLayout(nav_row)
        layout.addWidget(solve_box)
        self.panel = panel
        return panel

    def refresh_collections(self, select_id=None):
        self._collections = [
            PuzzleCollection(meta) for meta in list_collections()
        ]
        self._clear_info_items()
        self._collection_list.blockSignals(True)
        self._collection_list.clear()
        for collection in self._collections:
            item = QListWidgetItem(
                f"{self._display_name(collection)} ({collection.count})"
            )
            item.setData(Qt.ItemDataRole.UserRole, collection.id)
            self._collection_list.addItem(item)
        self._collection_list.setCurrentRow(-1)
        self._collection_list.blockSignals(False)

        self._collection = None
        self._solved = set()
        self._puzzle = None
        self._session = None
        self._index = 0
        self._favorite_keys = favorite_keys()
        self.board.clear()
        self.board.set_navigation_visible(False)

        if any(not collection.favorite for collection in self._collections):
            self._set_status("")
        else:
            self._set_status(t("puzzle_empty", self._language))
        if select_id:
            for row in range(self._collection_list.count()):
                item = self._collection_list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == select_id:
                    self._collection_list.setCurrentRow(row)
                    break
        self._update_controls()

    def _on_collection_selected(self, row):
        item = self._collection_list.item(row)
        collection_id = item.data(Qt.ItemDataRole.UserRole) if item else None
        if collection_id is None:
            self._collection = None
            self._solved = set()
            self._puzzle = None
            self._session = None
            self._index = 0
            self._clear_info_items()
            self.board.clear()
            self.board.set_navigation_visible(False)
            self._update_controls()
            return
        for collection in self._collections:
            if collection.id == collection_id:
                self._load_collection(collection)
                return

    def _load_collection(self, collection):
        self._collection = collection
        self._solved = solved_indices(collection.id)
        self.board.set_navigation_visible(False)
        if collection.count == 0:
            self._puzzle = None
            self._session = None
            self._index = 0
            self.board.clear()
            self._set_status(
                ""
                if collection.favorite
                else t("puzzle_status_bad_data", self._language)
            )
            self._update_info()
            self._update_controls()
            return
        self._load_puzzle(self._start_index())

    def _start_index(self):
        if self._collection is None:
            return 0
        for index in range(self._collection.count):
            if index not in self._solved:
                return index
        return 0

    def _load_puzzle(self, index):
        if self._collection is None:
            return
        puzzle = self._collection.get(index)
        if puzzle is None:
            self._puzzle = None
            self._session = None
            self._set_status(t("puzzle_status_bad_data", self._language))
            self._update_info()
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
            self._update_info()
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
        self._clear_info_items()
        if self._collection is None:
            return
        if self._puzzle is None:
            if not (self._collection.favorite and self._collection.count == 0):
                return
            lines = [t("puzzle_favorites_empty", self._language)]
        else:
            lines = [
                t(
                    "puzzle_info",
                    self._language,
                    name=self._display_name(self._collection),
                    solved=len(self._solved),
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
        row = self._current_collection_row()
        if row < 0:
            return
        self._collection_list.blockSignals(True)
        for offset, line in enumerate(lines, start=1):
            item = QListWidgetItem(line)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            font = item.font()
            font.setItalic(True)
            item.setFont(font)
            self._collection_list.insertItem(row + offset, item)
            self._info_items.append(item)
        self._collection_list.blockSignals(False)

    def _clear_info_items(self):
        self._collection_list.blockSignals(True)
        for item in self._info_items:
            row = self._collection_list.row(item)
            if row >= 0:
                self._collection_list.takeItem(row)
        self._collection_list.blockSignals(False)
        self._info_items = []

    def _current_collection_row(self):
        if self._collection is None:
            return -1
        for row in range(self._collection_list.count()):
            item = self._collection_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == self._collection.id:
                return row
        return -1

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
            self._auto_favorite()
            self._set_status(t("puzzle_status_wrong", self._language))
            return

        self._sync_board(animate=True)
        self._update_controls()
        if session.solved:
            self._mark_current_solved()
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
            self._mark_current_solved()
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

    def _toggle_favorite(self):
        if self._collection is None or self._puzzle is None:
            return
        added = toggle_favorite(
            self._puzzle, source_id=self._collection.id
        )
        self._favorite_keys = favorite_keys()
        self._refresh_favorites_collection()
        self._set_status(
            t(
                "puzzle_favorited" if added else "puzzle_unfavorited",
                self._language,
            )
        )
        if self._collection.favorite:
            self._reload_favorites()
        else:
            self._update_controls()

    def _auto_favorite(self):
        if self._collection is None or self._puzzle is None:
            return
        if add_favorite(self._puzzle, source_id=self._collection.id):
            self._favorite_keys = favorite_keys()
            self._refresh_favorites_collection()
            self._update_controls()

    def _refresh_favorites_collection(self):
        for index, collection in enumerate(self._collections):
            if collection.id == FAVORITES_ID:
                self._collections[index] = PuzzleCollection(
                    favorites_collection()
                )
                break
        for row in range(self._collection_list.count()):
            item = self._collection_list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) != FAVORITES_ID:
                continue
            for collection in self._collections:
                if collection.id == FAVORITES_ID:
                    item.setText(
                        f"{self._display_name(collection)} "
                        f"({collection.count})"
                    )
                    break
            break

    def _reload_favorites(self):
        for collection in self._collections:
            if collection.id == FAVORITES_ID:
                self._load_collection(collection)
                return

    def _update_favorite_button(self):
        favorited = (
            self._puzzle is not None
            and puzzle_key(self._puzzle) in self._favorite_keys
        )
        self._btn_favorite.setText(
            t(
                "puzzle_unfavorite" if favorited else "puzzle_favorite",
                self._language,
            )
        )

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
        if collection.favorite:
            return t("puzzle_favorites_name", self._language)
        if collection.builtin:
            return t("puzzle_builtin_name", self._language)
        return collection.name

    def _mark_current_solved(self):
        if self._collection is None or self._puzzle is None:
            return
        if self._index in self._solved:
            return
        self._solved.add(self._index)
        mark_solved(self._collection.id, self._index)
        self._update_info()

    def _on_jump(self):
        if self._collection is None:
            return
        try:
            value = int(self._jump_edit.text().strip())
        except ValueError:
            value = self._index + 1
        value = max(1, min(value, self._collection.count))
        if value - 1 != self._index:
            self._load_puzzle(value - 1)
        else:
            self._update_jump()

    def _update_jump(self):
        if self._collection is None or self._collection.count == 0:
            self._jump_edit.clear()
            self._jump_edit.setEnabled(False)
            self._jump_total.clear()
            self._btn_jump.setEnabled(False)
            return
        self._jump_edit.setText(str(self._index + 1))
        self._jump_edit.setEnabled(True)
        self._jump_total.setText(f"/{self._collection.count}")
        self._btn_jump.setEnabled(True)

    def _update_controls(self):
        has_session = self._session is not None
        solved = bool(self._session and self._session.solved)
        has_collection = self._collection is not None
        self._jump_box.setVisible(has_collection)
        self._solve_box.setVisible(has_collection)
        self._btn_prev.setVisible(has_collection)
        self._btn_next.setVisible(has_collection)
        self._btn_hint.setEnabled(has_session and not solved)
        self._btn_retry.setEnabled(has_session)
        self._btn_favorite.setEnabled(has_session)
        self._btn_delete.setEnabled(
            has_collection and not self._collection.favorite
        )
        self._btn_prev.setEnabled(has_collection and self._index > 0)
        self._btn_next.setEnabled(
            has_collection and self._index + 1 < self._collection.count
        )
        self._update_favorite_button()
        self._update_jump()

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
        self._btn_retry.setText(t("puzzle_retry", language))
        self._btn_jump.setText(t("puzzle_jump", language))
        self._jump_edit.setToolTip(t("puzzle_jump_tip", language))
        for row in range(self._collection_list.count()):
            item = self._collection_list.item(row)
            collection_id = item.data(Qt.ItemDataRole.UserRole)
            if collection_id is None:
                continue
            for collection in self._collections:
                if collection.id == collection_id:
                    item.setText(
                        f"{self._display_name(collection)} ({collection.count})"
                    )
                    break
        if self._puzzle is not None:
            self._update_info()
        elif self._collection is not None and self._collection.count == 0:
            self._update_info()
        elif not self._collections:
            self._set_status(t("puzzle_empty", language))
        self._update_controls()
