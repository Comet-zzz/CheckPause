import html
import time
import uuid

import chess
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from checkpause.core.puzzle import PuzzleSession
from checkpause.data.puzzles import (
    FAVORITES_ID,
    PuzzleCollection,
    add_favorite,
    append_outbox,
    attach_outbox_account_id,
    attempt_summary,
    delete_collection,
    favorite_keys,
    list_collections,
    load_outbox,
    mark_solved_key,
    puzzle_key,
    record_attempt,
    remove_outbox,
    solved_keys,
    toggle_favorite,
)
from checkpause.data.settings import get_account, get_server_url, save_account
from checkpause.gui.icons import action_icon
from checkpause.gui.theme import LIGHT
from checkpause.gui.widgets.board import BoardWidget
from checkpause.gui.workers import PuzzleImportWorker, PuzzleOnlineWorker
from checkpause.i18n import t


def _collection_name(collection, language):
    if collection.favorite:
        return t("puzzle_favorites_name", language)
    if collection.builtin:
        return t("puzzle_builtin_name", language)
    return collection.name


def _solution_text(fen, moves):
    """The movable line as SAN, so the result panel reads like a game."""
    board = chess.Board(fen)
    parts = []
    for uci in moves or []:
        try:
            move = chess.Move.from_uci(str(uci))
        except ValueError:
            break
        if move not in board.legal_moves:
            break
        san = board.san(move)
        if board.turn == chess.WHITE:
            parts.append(f"{board.fullmove_number}.{san}")
        else:
            parts.append(san)
        board.push(move)
    return " ".join(parts)


class _StatCard(QFrame):
    def __init__(self, caption_key, parent=None):
        super().__init__(parent)
        self._caption_key = caption_key
        self.setObjectName("puzzleStatCard")
        self.value = QLabel("—")
        self.value.setObjectName("puzzleStatValue")
        self.caption = QLabel()
        self.caption.setObjectName("puzzleStatCaption")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)
        layout.addWidget(self.value)
        layout.addWidget(self.caption)

    def set_value(self, value):
        self.value.setText("—" if value is None else str(value))

    def retranslate(self, language):
        self.caption.setText(t(self._caption_key, language))


class _CollectionCard(QPushButton):
    clicked_id = Signal(str)

    def __init__(self, collection, language, parent=None):
        super().__init__(parent)
        self._collection = collection
        self.setObjectName("puzzleCollectionCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(78)
        self.clicked.connect(lambda: self.clicked_id.emit(self._collection.id))
        self.retranslate(language)

    def retranslate(self, language):
        solved = len(solved_keys(self._collection))
        name = _collection_name(self._collection, language)
        self.setText(f"{name}\n{solved}/{self._collection.count}")


class _HubView(QWidget):
    train_requested = Signal()
    mistakes_requested = Signal()
    library_requested = Signal()
    profile_requested = Signal()
    collection_requested = Signal(str)
    daily_requested = Signal()
    solved_requested = Signal()
    sign_in_requested = Signal()
    difficulty_changed = Signal(str)
    theme_filter_changed = Signal(str)
    auto_next_changed = Signal(bool)
    challenge_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._online = False
        self._rating = None
        self._cards = []
        self._topics = (
            ("", "puzzle_theme_all"),
            ("mate", "puzzle_theme_mate"),
            ("fork", "puzzle_theme_fork"),
            ("pin", "puzzle_theme_pin"),
            ("endgame", "puzzle_theme_endgame"),
            ("middlegame", "puzzle_theme_middlegame"),
            ("opening", "puzzle_theme_opening"),
            ("sacrifice", "puzzle_theme_sacrifice"),
            ("advantage", "puzzle_theme_advantage"),
            ("defensiveMove", "puzzle_theme_defense"),
        )

        scroll = QScrollArea()
        scroll.setObjectName("puzzleScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("puzzleHub")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(18)

        self._title = QLabel()
        self._title.setObjectName("puzzleHeaderTitle")
        self._subtitle = QLabel()
        self._subtitle.setObjectName("puzzleHeaderSubtitle")
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        title_box.addWidget(self._title)
        title_box.addWidget(self._subtitle)
        self._status = QLabel()
        self._status.setObjectName("puzzleStatusPill")
        self._btn_profile = QPushButton()
        self._btn_profile.setObjectName("puzzleGhostButton")
        self._btn_profile.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_profile.clicked.connect(self.profile_requested.emit)
        header = QHBoxLayout()
        header.addLayout(title_box, 1)
        header.addWidget(self._status, 0, Qt.AlignmentFlag.AlignTop)
        header.addWidget(self._btn_profile, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self._notice = QLabel()
        self._notice.setObjectName("puzzleNotice")
        self._notice.setWordWrap(True)
        self._notice.setVisible(False)
        layout.addWidget(self._notice)

        hero = QFrame()
        hero.setObjectName("puzzleHero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 18, 20, 18)
        hero_layout.setSpacing(6)
        self._hero_title = QLabel()
        self._hero_title.setObjectName("puzzleHeroTitle")
        self._hero_text = QLabel()
        self._hero_text.setObjectName("puzzleHeroText")
        self._hero_text.setWordWrap(True)
        self._btn_train = QPushButton()
        self._btn_train.setObjectName("puzzlePrimaryButton")
        self._btn_train.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_train.clicked.connect(self.train_requested.emit)
        hero_layout.addWidget(self._hero_title)
        hero_layout.addWidget(self._hero_text)
        hero_layout.addSpacing(6)
        hero_layout.addWidget(self._btn_train, 0, Qt.AlignmentFlag.AlignLeft)

        self._difficulty_label = QLabel()
        self._difficulty = QComboBox()
        self._difficulty.setObjectName("puzzleRange")
        self._difficulty.currentIndexChanged.connect(
            lambda _index: self.difficulty_changed.emit(self._difficulty.currentData() or "normal")
        )
        self._theme_label = QLabel()
        self._theme_filter = QComboBox()
        self._theme_filter.setObjectName("puzzleRange")
        self._theme_filter.currentIndexChanged.connect(
            lambda _index: self.theme_filter_changed.emit(self._theme_filter.currentData() or "")
        )
        self._auto_next = QCheckBox()
        self._auto_next.toggled.connect(self.auto_next_changed.emit)
        self._challenge = QComboBox()
        self._challenge.setObjectName("puzzleRange")
        self._challenge.currentIndexChanged.connect(
            lambda _index: self.challenge_changed.emit(self._challenge.currentData() or "")
        )
        self._btn_daily = QPushButton()
        self._btn_daily.setObjectName("puzzleSecondaryButton")
        self._btn_daily.clicked.connect(self.daily_requested.emit)
        self._btn_solved = QPushButton()
        self._btn_solved.setObjectName("puzzleSecondaryButton")
        self._btn_solved.clicked.connect(self.solved_requested.emit)
        self._btn_signin = QPushButton()
        self._btn_signin.setObjectName("puzzleSecondaryButton")
        self._btn_signin.clicked.connect(self.sign_in_requested.emit)
        filters = QHBoxLayout()
        filters.setSpacing(8)
        filters.addWidget(self._difficulty_label)
        filters.addWidget(self._difficulty)
        filters.addWidget(self._theme_label)
        filters.addWidget(self._theme_filter)
        filters.addWidget(self._auto_next)
        filters.addWidget(self._challenge)
        filters.addStretch(1)
        filters.addWidget(self._btn_daily)
        filters.addWidget(self._btn_solved)
        filters.addWidget(self._btn_signin)
        hero_layout.addLayout(filters)
        layout.addWidget(hero)

        cards = QHBoxLayout()
        cards.setSpacing(10)
        self._attempted = _StatCard("puzzle_home_attempted")
        self._solved = _StatCard("puzzle_home_solved")
        self._accuracy = _StatCard("puzzle_home_accuracy")
        for card in (self._attempted, self._solved, self._accuracy):
            cards.addWidget(card, 1)
        layout.addLayout(cards)

        self._tools_label = QLabel()
        self._tools_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._tools_label)
        tools = QHBoxLayout()
        tools.setSpacing(8)
        self._btn_mistakes = QPushButton()
        self._btn_mistakes.setObjectName("puzzleSecondaryButton")
        self._btn_mistakes.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_mistakes.clicked.connect(self.mistakes_requested.emit)
        self._btn_library = QPushButton()
        self._btn_library.setObjectName("puzzleSecondaryButton")
        self._btn_library.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_library.clicked.connect(self.library_requested.emit)
        tools.addWidget(self._btn_mistakes)
        tools.addWidget(self._btn_library)
        tools.addStretch(1)
        layout.addLayout(tools)

        self._collections_label = QLabel()
        self._collections_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._collections_label)
        self._collection_grid = QGridLayout()
        self._collection_grid.setHorizontalSpacing(12)
        self._collection_grid.setVerticalSpacing(12)
        self._collection_grid.setColumnStretch(0, 1)
        self._collection_grid.setColumnStretch(1, 1)
        layout.addLayout(self._collection_grid)
        self._empty_label = QLabel()
        self._empty_label.setObjectName("puzzleEmptyLabel")
        self._empty_label.setVisible(False)
        layout.addWidget(self._empty_label)
        self._source_note = QLabel()
        self._source_note.setObjectName("puzzleSourceNote")
        self._source_note.setWordWrap(True)
        layout.addWidget(self._source_note)
        layout.addStretch(1)
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.retranslate(self._language)

    def set_summary(self, summary):
        self._attempted.set_value(summary.get("unique_attempted", 0))
        self._solved.set_value(summary.get("unique_solved", 0))
        self._accuracy.set_value(f"{summary.get('accuracy', 0)}%")

    def set_online(self, online, rating=None):
        self._online = bool(online)
        self._rating = rating
        text = t("puzzle_home_online" if online else "puzzle_home_local", self._language)
        if online and rating is not None:
            text += f" · {round(float(rating))}"
        self._status.setText(text)
        self._status.setProperty("online", bool(online))
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)
        self._btn_daily.setVisible(self._online)
        self._btn_solved.setVisible(self._online)
        self._btn_signin.setVisible(not self._online)

    def set_notice(self, text=""):
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))

    def set_train_enabled(self, enabled):
        self._btn_train.setEnabled(bool(enabled))

    def set_challenge(self, mode):
        index = self._challenge.findData(mode or "")
        if index < 0:
            return
        self._challenge.blockSignals(True)
        self._challenge.setCurrentIndex(index)
        self._challenge.blockSignals(False)

    def set_collections(self, collections, language):
        self._language = language
        while self._collection_grid.count():
            item = self._collection_grid.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._cards = []
        visible = [collection for collection in collections if not collection.favorite]
        for index, collection in enumerate(visible):
            card = _CollectionCard(collection, language)
            card.clicked_id.connect(self.collection_requested.emit)
            self._cards.append(card)
            self._collection_grid.addWidget(card, index // 2, index % 2)
        self._empty_label.setVisible(not visible)

    def _fill_combo(self, combo, items, fallback):
        current = combo.currentData()
        if current is None:
            current = fallback
        combo.blockSignals(True)
        combo.clear()
        for data, key in items:
            combo.addItem(t(key, self._language), data)
        index = combo.findData(current)
        combo.setCurrentIndex(index if index >= 0 else 0)
        combo.blockSignals(False)

    def retranslate(self, language):
        self._language = language
        self._title.setText(t("nav_puzzle", language))
        self._subtitle.setText(t("puzzle_home_subtitle", language))
        self._btn_profile.setText(t("puzzle_home_profile", language))
        self._hero_title.setText(t("puzzle_home_train_title", language))
        self._hero_text.setText(t("puzzle_home_train_subtitle", language))
        self._btn_train.setText(t("puzzle_home_train", language))
        self._difficulty_label.setText(t("puzzle_home_difficulty", language))
        self._theme_label.setText(t("puzzle_home_theme", language))
        self._auto_next.setText(t("puzzle_home_auto_next", language))
        self._fill_combo(
            self._challenge,
            (
                ("", "puzzle_challenge_none"),
                ("storm", "puzzle_challenge_storm"),
                ("racer", "puzzle_challenge_racer"),
            ),
            "",
        )
        self._btn_daily.setText(t("puzzle_home_daily", language))
        self._btn_solved.setText(t("puzzle_home_review_solved", language))
        self._btn_signin.setText(t("puzzle_home_sign_in", language))
        self._fill_combo(
            self._difficulty,
            (
                ("easy", "puzzle_difficulty_easy"),
                ("normal", "puzzle_difficulty_normal"),
                ("hard", "puzzle_difficulty_hard"),
            ),
            "normal",
        )
        self._fill_combo(self._theme_filter, self._topics, "")
        self._tools_label.setText(t("puzzle_home_tools", language))
        self._btn_mistakes.setText(t("puzzle_home_mistakes", language))
        self._btn_library.setText(t("puzzle_home_library", language))
        self._collections_label.setText(t("puzzle_home_collections", language))
        self._empty_label.setText(t("puzzle_home_no_collections", language))
        self._source_note.setText(t("puzzle_source_note", language))
        self.set_online(self._online, self._rating)
        for card in self._cards:
            card.retranslate(language)
        for card in (self._attempted, self._solved, self._accuracy):
            card.retranslate(language)


class _TrainView(QWidget):
    back_requested = Signal()
    hint_requested = Signal()
    retry_requested = Signal()
    favorite_requested = Signal()
    reveal_requested = Signal()
    next_requested = Signal()
    profile_requested = Signal()
    replay_requested = Signal()
    vote_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT
        self._favorited = False
        self._rating = None
        self._game_url = ""
        self.setObjectName("puzzleTrain")

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("puzzleGhostButton")
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.clicked.connect(self.back_requested.emit)
        self._mode_label = QLabel()
        self._mode_label.setObjectName("puzzleModeLabel")
        self._counter_label = QLabel()
        self._counter_label.setObjectName("puzzleCounterLabel")
        self._rating_label = QLabel()
        self._rating_label.setObjectName("puzzleRatingPill")
        self._rating_label.setVisible(False)
        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(self._btn_back)
        top.addWidget(self._mode_label)
        top.addWidget(self._rating_label)
        top.addStretch(1)
        top.addWidget(self._counter_label)

        self._prompt = QLabel()
        self._prompt.setObjectName("puzzlePrompt")
        self._prompt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._prompt.setWordWrap(True)
        self._game_link = QLabel()
        self._game_link.setObjectName("puzzleGameLink")
        self._game_link.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._game_link.setOpenExternalLinks(True)
        self._game_link.setTextFormat(Qt.TextFormat.RichText)
        self._game_link.setVisible(False)
        self._notice = QLabel()
        self._notice.setObjectName("puzzleNotice")
        self._notice.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._notice.setWordWrap(True)
        self._notice.setVisible(False)

        self.board = BoardWidget()
        self.board.set_navigation_visible(False)
        self.board.setMinimumWidth(360)
        self.board.setMaximumWidth(600)
        self.board.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )
        board_row = QHBoxLayout()
        board_row.setContentsMargins(0, 0, 0, 0)
        board_row.addStretch(1)
        board_row.addWidget(self.board, 6)
        board_row.addStretch(1)

        self._result_panel = QFrame()
        self._result_panel.setObjectName("puzzleResultPanel")
        self._result_panel.setVisible(False)
        self._result_title = QLabel()
        self._result_title.setObjectName("puzzleResultTitle")
        self._result_detail = QLabel()
        self._result_detail.setObjectName("puzzleResultDetail")
        self._result_detail.setWordWrap(True)
        self._result_meta = QLabel()
        self._result_meta.setObjectName("puzzleResultMeta")
        self._result_meta.setWordWrap(True)
        self._result_meta.setVisible(False)
        self._result_solution = QLabel()
        self._result_solution.setObjectName("puzzleSolution")
        self._result_solution.setWordWrap(True)
        self._result_solution.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._btn_result_retry = QPushButton()
        self._btn_result_retry.setObjectName("puzzleSecondaryButton")
        self._btn_result_retry.clicked.connect(self.retry_requested.emit)
        self._btn_result_favorite = QPushButton()
        self._btn_result_favorite.setObjectName("puzzleSecondaryButton")
        self._btn_result_favorite.clicked.connect(self.favorite_requested.emit)
        self._btn_result_profile = QPushButton()
        self._btn_result_profile.setObjectName("puzzleSecondaryButton")
        self._btn_result_profile.clicked.connect(self.profile_requested.emit)
        self._btn_replay = QPushButton()
        self._btn_replay.setObjectName("puzzleSecondaryButton")
        self._btn_replay.clicked.connect(self.replay_requested.emit)
        self._btn_vote_up = QPushButton()
        self._btn_vote_up.setObjectName("puzzleSecondaryButton")
        self._btn_vote_up.clicked.connect(lambda: self.vote_requested.emit(1))
        self._btn_vote_down = QPushButton()
        self._btn_vote_down.setObjectName("puzzleSecondaryButton")
        self._btn_vote_down.clicked.connect(lambda: self.vote_requested.emit(-1))
        self._btn_next = QPushButton()
        self._btn_next.setObjectName("puzzlePrimaryButton")
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.clicked.connect(self.next_requested.emit)
        result_buttons = QHBoxLayout()
        result_buttons.setSpacing(8)
        result_buttons.addWidget(self._btn_result_retry)
        result_buttons.addWidget(self._btn_result_favorite)
        result_buttons.addWidget(self._btn_result_profile)
        result_buttons.addWidget(self._btn_replay)
        result_buttons.addWidget(self._btn_vote_up)
        result_buttons.addWidget(self._btn_vote_down)
        result_buttons.addStretch(1)
        result_buttons.addWidget(self._btn_next)
        result_layout = QVBoxLayout(self._result_panel)
        result_layout.setContentsMargins(16, 12, 16, 12)
        result_layout.setSpacing(5)
        result_layout.addWidget(self._result_title)
        result_layout.addWidget(self._result_detail)
        result_layout.addWidget(self._result_meta)
        result_layout.addWidget(self._result_solution)
        result_layout.addLayout(result_buttons)

        self._btn_hint = QPushButton()
        self._btn_hint.setObjectName("puzzleSecondaryButton")
        self._btn_hint.clicked.connect(self.hint_requested.emit)
        self._btn_reveal = QPushButton()
        self._btn_reveal.setObjectName("puzzleSecondaryButton")
        self._btn_reveal.clicked.connect(self.reveal_requested.emit)
        self._btn_favorite = QPushButton()
        self._btn_favorite.setObjectName("puzzleSecondaryButton")
        self._btn_favorite.clicked.connect(self.favorite_requested.emit)
        bottom = QHBoxLayout()
        bottom.setSpacing(8)
        bottom.addWidget(self._btn_hint)
        bottom.addWidget(self._btn_reveal)
        bottom.addStretch(1)
        bottom.addWidget(self._btn_favorite)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 16, 24, 18)
        layout.setSpacing(10)
        layout.addLayout(top)
        layout.addWidget(self._prompt)
        layout.addWidget(self._game_link)
        layout.addWidget(self._notice)
        layout.addLayout(board_row, 1)
        layout.addWidget(self._result_panel)
        layout.addLayout(bottom)

    def set_rating(self, rating):
        self._rating = rating
        if rating is None:
            self._rating_label.setVisible(False)
            return
        self._rating_label.setText(
            t("puzzle_online_rating", self._language, rating=round(float(rating)))
        )
        self._rating_label.setVisible(True)

    def set_online_info(self, mode, rating):
        self._mode_label.setText(mode)
        self._counter_label.clear()
        self.set_rating(rating)

    def set_session_info(self, mode, index, total, human_color):
        self._mode_label.setText(mode)
        self.set_rating(None)
        self._counter_label.setText(
            t(
                "puzzle_train_progress",
                self._language,
                index=index + 1,
                total=total,
            )
        )
        color = t(
            "puzzle_side_white" if human_color == chess.WHITE else "puzzle_side_black",
            self._language,
        )
        self._prompt.setText(t("puzzle_train_your_turn", self._language, color=color))

    def set_prompt(self, text):
        self._prompt.setText(text)

    def set_counter(self, text):
        self._counter_label.setText(text or "")

    def set_notice(self, text=""):
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))

    def set_solving(self, solving):
        self._btn_hint.setEnabled(solving)
        self._btn_reveal.setEnabled(solving)
        self._btn_favorite.setEnabled(True)

    def show_result(self, state, title, detail, solution="", meta=""):
        self._result_title.setText(title)
        self._result_detail.setText(detail)
        self.set_result_meta(meta)
        self._result_solution.setText(solution)
        self._result_solution.setVisible(bool(solution))
        self._result_panel.setProperty("state", state)
        self._result_panel.style().unpolish(self._result_panel)
        self._result_panel.style().polish(self._result_panel)
        self._result_panel.setVisible(True)
        self._btn_hint.setEnabled(False)
        self._btn_reveal.setEnabled(False)

    def set_result_meta(self, text):
        self._result_meta.setText(text or "")
        self._result_meta.setVisible(bool(text))

    def set_attempt_result(self, data, streak=0):
        if not isinstance(data, dict):
            return
        if not data.get("rated"):
            text = t("puzzle_result_practice", self._language)
        else:
            before = data.get("rating_before")
            after = data.get("rating_after")
            delta = data.get("rating_delta")
            if before is None or after is None or delta is None:
                return
            text = t(
                "puzzle_result_rating",
                self._language,
                before=round(float(before)),
                after=round(float(after)),
                delta=f"{float(delta):+g}",
            )
        if streak:
            text += " · " + t("puzzle_result_streak", self._language, streak=streak)
        self.set_result_meta(text)

    def set_game_link(self, url):
        self._game_url = (url or "").strip()
        if not self._game_url:
            self._game_link.clear()
            self._game_link.setVisible(False)
            return
        safe = html.escape(self._game_url, quote=True)
        self._game_link.setText(
            t("puzzle_game_from", self._language) + f': <a href="{safe}">{safe}</a>'
        )
        self._game_link.setVisible(True)

    def hide_result(self):
        self._result_panel.setVisible(False)
        self._result_panel.setProperty("state", "")
        self._result_solution.clear()
        self.set_result_meta("")
        self.set_solving(True)

    def set_next_enabled(self, enabled):
        self._btn_next.setEnabled(enabled)

    def set_favorite(self, favorited):
        self._favorited = bool(favorited)
        self._btn_favorite.setText(
            t("puzzle_unfavorite" if favorited else "puzzle_favorite", self._language)
        )
        self._btn_result_favorite.setText(self._btn_favorite.text())
        icon = "star_filled" if favorited else "star"
        self._btn_favorite.setIcon(action_icon(self._theme, icon))
        self._btn_result_favorite.setIcon(action_icon(self._theme, icon))

    def apply_icons(self, theme):
        self._theme = theme
        for button, name in (
            (self._btn_back, "nav_prev"),
            (self._btn_hint, "hint"),
            (self._btn_reveal, "review_best"),
            (self._btn_result_retry, "reset"),
        ):
            button.setIcon(action_icon(theme, name))
            button.setIconSize(QSize(16, 16))
        self.set_favorite(self._favorited)

    def retranslate(self, language):
        self._language = language
        self._btn_back.setText(t("puzzle_train_back", language))
        self._btn_hint.setText(t("puzzle_train_hint", language))
        self._btn_reveal.setText(t("puzzle_train_reveal", language))
        self._btn_result_retry.setText(t("puzzle_train_retry", language))
        self._btn_result_profile.setText(t("puzzle_home_profile", language))
        self._btn_next.setText(t("puzzle_train_next", language))
        self._btn_replay.setText(t("puzzle_train_replay", language))
        self._btn_vote_up.setText(t("puzzle_vote_up", language))
        self._btn_vote_down.setText(t("puzzle_vote_down", language))
        self._btn_favorite.setText(t("puzzle_favorite", language))
        self._btn_result_favorite.setText(t("puzzle_favorite", language))
        self.set_favorite(self._favorited)
        self.set_rating(self._rating)
        self.set_game_link(self._game_url)

    def set_theme(self, theme):
        self.board.set_theme(theme)
        self.apply_icons(theme)

    def set_piece_set(self, name):
        self.board.set_piece_set(name)

    def set_board_theme(self, name):
        self.board.set_board_theme(name)

    def set_sound_enabled(self, enabled):
        self.board.set_sound_enabled(enabled)

    def set_sound_set(self, name):
        self.board.set_sound_set(name)


class _LibraryView(QWidget):
    back_requested = Signal()
    import_requested = Signal()
    delete_requested = Signal(str)
    start_requested = Signal(str)
    prev_requested = Signal()
    next_requested = Signal()
    jump_requested = Signal(int)
    selection_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._collections = []
        self.setObjectName("puzzleLibrary")

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("puzzleGhostButton")
        self._btn_back.clicked.connect(self.back_requested.emit)
        self._title = QLabel()
        self._title.setObjectName("puzzleHeaderTitle")
        self._btn_import = QPushButton()
        self._btn_import.setObjectName("puzzleSecondaryButton")
        self._btn_import.clicked.connect(self.import_requested.emit)
        self._btn_delete = QPushButton()
        self._btn_delete.setObjectName("puzzleSecondaryButton")
        self._btn_delete.clicked.connect(self._emit_delete)
        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self._btn_back)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._btn_import)
        header.addWidget(self._btn_delete)

        self._info = QLabel()
        self._info.setObjectName("puzzleLibraryInfo")
        self._info.setWordWrap(True)
        self._list = QListWidget()
        self._list.setObjectName("puzzleLibraryList")
        self._list.currentRowChanged.connect(self._on_row_changed)

        self._btn_prev = QPushButton()
        self._btn_prev.clicked.connect(self.prev_requested.emit)
        self._jump_edit = QLineEdit()
        self._jump_edit.setFixedWidth(52)
        self._jump_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._jump_edit.returnPressed.connect(self._emit_jump)
        self._jump_total = QLabel()
        self._jump_total.setObjectName("puzzleCounterLabel")
        self._btn_jump = QPushButton()
        self._btn_jump.clicked.connect(self._emit_jump)
        self._btn_next = QPushButton()
        self._btn_next.clicked.connect(self.next_requested.emit)
        nav = QHBoxLayout()
        nav.setSpacing(6)
        nav.addWidget(self._btn_prev)
        nav.addWidget(self._jump_edit)
        nav.addWidget(self._jump_total)
        nav.addWidget(self._btn_jump)
        nav.addWidget(self._btn_next)
        nav.addStretch(1)

        self._btn_start = QPushButton()
        self._btn_start.setObjectName("puzzlePrimaryButton")
        self._btn_start.clicked.connect(self._emit_start)
        self._status = QLabel()
        self._status.setObjectName("puzzleLibraryStatus")
        self._status.setWordWrap(True)
        bottom = QHBoxLayout()
        bottom.addWidget(self._status, 1)
        bottom.addWidget(self._btn_start)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 28)
        layout.setSpacing(12)
        layout.addLayout(header)
        layout.addWidget(self._info)
        layout.addWidget(self._list, 1)
        layout.addLayout(nav)
        layout.addLayout(bottom)
        self.retranslate(self._language)
        self.set_current(None, 0)

    def set_collections(self, collections, current_id=None):
        self._collections = list(collections)
        self._list.blockSignals(True)
        self._list.clear()
        for collection in collections:
            name = _collection_name(collection, self._language)
            item = QListWidgetItem(f"{name} ({collection.count})")
            item.setData(Qt.ItemDataRole.UserRole, collection.id)
            self._list.addItem(item)
        self._list.blockSignals(False)
        if current_id is not None:
            for row in range(self._list.count()):
                item = self._list.item(row)
                if item.data(Qt.ItemDataRole.UserRole) == current_id:
                    self._list.setCurrentRow(row)
                    return

    def set_current(self, collection, index):
        has_collection = collection is not None
        self._btn_delete.setEnabled(
            has_collection and not collection.favorite and collection.id != FAVORITES_ID
        )
        self._btn_start.setEnabled(has_collection and collection.count > 0)
        self._btn_prev.setEnabled(has_collection)
        self._btn_next.setEnabled(has_collection)
        self._btn_jump.setEnabled(has_collection)
        self._jump_edit.setEnabled(has_collection)
        if not has_collection:
            self._info.setText(t("puzzle_library_select", self._language))
            self._jump_edit.clear()
            self._jump_total.clear()
            return
        self._info.setText(
            t(
                "puzzle_info",
                self._language,
                name=_collection_name(collection, self._language),
                solved=len(solved_keys(collection)),
                total=collection.count,
            )
        )
        self._jump_edit.setText(str(index + 1) if collection.count else "")
        self._jump_total.setText(f"/{collection.count}")
        self._btn_prev.setEnabled(index > 0)
        self._btn_next.setEnabled(collection.count > 0 and index + 1 < collection.count)

    def set_status(self, text):
        self._status.setText(text)
        self._status.setVisible(bool(text))

    def set_import_enabled(self, enabled):
        self._btn_import.setEnabled(enabled)

    def select_row(self, collection_id):
        for row in range(self._list.count()):
            item = self._list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == collection_id:
                self._list.setCurrentRow(row)
                return

    def _current_id(self):
        item = self._list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else ""

    def _on_row_changed(self, row):
        item = self._list.item(row) if row >= 0 else None
        if item is not None:
            self.selection_changed.emit(item.data(Qt.ItemDataRole.UserRole))

    def _emit_delete(self):
        collection_id = self._current_id()
        if collection_id:
            self.delete_requested.emit(collection_id)

    def _emit_start(self):
        collection_id = self._current_id()
        if collection_id:
            self.start_requested.emit(collection_id)

    def _emit_jump(self):
        try:
            value = int(self._jump_edit.text().strip())
        except ValueError:
            return
        self.jump_requested.emit(value)

    def apply_icons(self, theme):
        for button, name in (
            (self._btn_back, "nav_prev"),
            (self._btn_import, "import"),
            (self._btn_delete, "trash"),
            (self._btn_prev, "nav_prev"),
            (self._btn_next, "nav_next"),
        ):
            button.setIcon(action_icon(theme, name))
            button.setIconSize(QSize(16, 16))

    def retranslate(self, language):
        self._language = language
        self._btn_back.setText(t("puzzle_train_back", language))
        self._title.setText(t("puzzle_library_title", language))
        self._btn_import.setText(t("puzzle_import", language))
        self._btn_delete.setText(t("puzzle_delete", language))
        self._btn_prev.setText(t("puzzle_prev", language))
        self._btn_next.setText(t("puzzle_next", language))
        self._btn_jump.setText(t("puzzle_jump", language))
        self._btn_start.setText(t("puzzle_library_start", language))
        self._jump_edit.setAccessibleName(t("puzzle_jump_tip", language))


class _ProfileView(QWidget):
    back_requested = Signal()
    range_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._summary = {}

        scroll = QScrollArea()
        scroll.setObjectName("puzzleScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        inner = QWidget()
        inner.setObjectName("puzzleProfile")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(16)

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("puzzleGhostButton")
        self._btn_back.clicked.connect(self.back_requested.emit)
        self._title = QLabel()
        self._title.setObjectName("puzzleHeaderTitle")
        self._range = QComboBox()
        self._range.setObjectName("puzzleRange")
        for days in (7, 30, 90, 0):
            self._range.addItem("", days)
        self._range.setCurrentIndex(1)
        self._range.currentIndexChanged.connect(
            lambda _index: self.range_changed.emit(int(self._range.currentData()))
        )
        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self._btn_back)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._range)
        layout.addLayout(header)
        self._scope_note = QLabel()
        self._scope_note.setObjectName("puzzleProfileScope")
        self._scope_note.setWordWrap(True)
        layout.addWidget(self._scope_note)

        self._notice = QLabel()
        self._notice.setObjectName("puzzleNotice")
        self._notice.setWordWrap(True)
        self._notice.setVisible(False)
        layout.addWidget(self._notice)

        first = QHBoxLayout()
        first.setSpacing(10)
        self._rating = _StatCard("puzzle_profile_rating")
        self._attempted = _StatCard("puzzle_profile_attempts")
        self._solved = _StatCard("puzzle_profile_solved")
        self._accuracy = _StatCard("puzzle_profile_accuracy")
        self._streak = _StatCard("puzzle_profile_streak")
        for card in (
            self._rating,
            self._attempted,
            self._solved,
            self._accuracy,
            self._streak,
        ):
            first.addWidget(card, 1)
        layout.addLayout(first)

        second = QHBoxLayout()
        second.setSpacing(10)
        self._solved_avg = _StatCard("puzzle_profile_solved_avg")
        self._failed_avg = _StatCard("puzzle_profile_failed_avg")
        self._retryable = _StatCard("puzzle_profile_retryable")
        self._active_days = _StatCard("puzzle_profile_active_days")
        for card in (self._solved_avg, self._failed_avg, self._retryable, self._active_days):
            second.addWidget(card, 1)
        layout.addLayout(second)

        self._themes_label = QLabel()
        self._themes_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._themes_label)
        self._themes_box = QFrame()
        self._themes_box.setObjectName("puzzleThemeBox")
        self._themes_layout = QVBoxLayout(self._themes_box)
        self._themes_layout.setContentsMargins(14, 12, 14, 12)
        self._themes_layout.setSpacing(8)
        layout.addWidget(self._themes_box)
        self._empty_themes = QLabel()
        self._empty_themes.setObjectName("puzzleEmptyLabel")
        layout.addWidget(self._empty_themes)

        self._recent_label = QLabel()
        self._recent_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._recent_label)
        self._recent = QListWidget()
        self._recent.setObjectName("puzzleRecentList")
        self._recent.setMinimumHeight(180)
        layout.addWidget(self._recent)
        self._empty = QLabel()
        self._empty.setObjectName("puzzleEmptyLabel")
        self._empty.setWordWrap(True)
        layout.addWidget(self._empty)
        layout.addStretch(1)
        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.retranslate(self._language)
        self.refresh({}, self._language)

    def set_range(self, days):
        for index in range(self._range.count()):
            if int(self._range.itemData(index)) == days:
                self._range.blockSignals(True)
                self._range.setCurrentIndex(index)
                self._range.blockSignals(False)
                return

    def set_notice(self, text=""):
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))

    def refresh(self, summary, language):
        self._language = language
        self._summary = summary
        self._rating.set_value(summary.get("rating"))
        self._attempted.set_value(summary.get("attempts", 0))
        self._solved.set_value(summary.get("unique_solved", 0))
        self._accuracy.set_value(f"{summary.get('accuracy', 0)}%")
        self._streak.set_value(summary.get("streak", 0))
        self._solved_avg.set_value(summary.get("solved_avg_rating"))
        self._failed_avg.set_value(summary.get("failed_avg_rating"))
        self._retryable.set_value(summary.get("retryable", 0))
        self._active_days.set_value(summary.get("active_days", 0))
        self._rebuild_themes(summary.get("themes") or [])
        self._rebuild_recent(summary.get("recent") or [])
        has_data = bool(summary.get("attempts"))
        self._empty.setVisible(not has_data)
        self._themes_box.setVisible(bool(summary.get("themes")))
        self._empty_themes.setVisible(has_data and not summary.get("themes"))

    def _clear_theme_rows(self):
        while self._themes_layout.count():
            item = self._themes_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_themes(self, themes):
        self._clear_theme_rows()
        for row in themes:
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(3)
            label = QLabel(
                t(
                    "puzzle_profile_theme_row",
                    self._language,
                    theme=row["theme"],
                    attempts=row["attempts"],
                    accuracy=row["accuracy"],
                )
            )
            label.setObjectName("puzzleThemeLabel")
            bar = QProgressBar()
            bar.setObjectName("puzzleThemeBar")
            bar.setRange(0, 100)
            bar.setValue(row["accuracy"])
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            layout.addWidget(label)
            layout.addWidget(bar)
            self._themes_layout.addWidget(widget)

    def _rebuild_recent(self, recent):
        self._recent.clear()
        for entry in recent:
            date = str(entry.get("created_at", ""))[:16].replace("T", " ")
            rating = entry.get("rating")
            rating_text = str(rating) if rating else "—"
            result = t(
                "puzzle_profile_result_solved"
                if entry.get("result") == "solved"
                else "puzzle_profile_result_failed",
                self._language,
            )
            themes = ", ".join(entry.get("themes") or []) or "—"
            text = t(
                "puzzle_profile_recent_row",
                self._language,
                date=date,
                rating=rating_text,
                result=result,
                themes=themes,
            )
            item = QListWidgetItem(text)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self._recent.addItem(item)

    def retranslate(self, language):
        self._language = language
        self._btn_back.setText(t("puzzle_train_back", language))
        self._title.setText(t("puzzle_profile_title", language))
        self._scope_note.setText(t("puzzle_profile_scope", language))
        self._range.setItemText(0, t("puzzle_profile_range_7", language))
        self._range.setItemText(1, t("puzzle_profile_range_30", language))
        self._range.setItemText(2, t("puzzle_profile_range_90", language))
        self._range.setItemText(3, t("puzzle_profile_range_all", language))
        self._themes_label.setText(t("puzzle_profile_themes", language))
        self._recent_label.setText(t("puzzle_profile_recent", language))
        self._empty.setText(t("puzzle_profile_empty", language))
        self._empty_themes.setText(t("puzzle_profile_no_themes", language))
        for card in (
            self._rating,
            self._attempted,
            self._solved,
            self._accuracy,
            self._streak,
            self._solved_avg,
            self._failed_avg,
            self._retryable,
            self._active_days,
        ):
            card.retranslate(language)
        if self._summary:
            self.refresh(self._summary, language)

    def apply_icons(self, theme):
        self._btn_back.setIcon(action_icon(theme, "nav_prev"))
        self._btn_back.setIconSize(QSize(16, 16))


class PuzzlePage(QWidget):
    sign_in_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT
        self._collections = []
        self._solved_keys = set()
        self._collection = None
        self._index = 0
        self._puzzle = None
        self._session = None
        self._import_worker = None
        self._favorite_keys = set()
        self._attempt_recorded = False
        self._hinted = False
        self._started_at = 0.0
        self._last_duration_ms = 0
        self._revealing = False
        self._train_origin = "hub"
        self._library_collection = None
        self._library_index = 0
        self._profile_days = 30
        self._token = ""
        self._server_url = ""
        self._online = False
        self._online_rating = None
        self._online_rd = None
        self._online_stats = None
        self._online_stats_days = None
        self._online_rated = True
        self._client_attempt_id = ""
        self._next_worker = None
        self._stats_worker = None
        self._stats_requested_days = None
        self._stats_refresh_pending = False
        self._attempt_worker = None
        self._pending_attempts = load_outbox()
        self._attempts_paused = False
        self._attempt_retry_timer = QTimer(self)
        self._attempt_retry_timer.setSingleShot(True)
        self._attempt_retry_timer.timeout.connect(self._resume_attempts)
        self._hub_stats = None
        self._hub_stats_worker = None
        self._account_username = ""
        self._account_id = None
        self._account_id_worker = None
        self._account_id_attached = False
        self._account_id_checked = False
        self._auth_expired = False
        self._theme_filter = ""
        self._difficulty = "normal"
        self._auto_next = False
        self._streak = 0
        self._review_puzzles = []
        self._review_index = -1
        self._vote_worker = None
        self._replay_moves = []
        self._replay_index = 0
        self._replay_timer = QTimer(self)
        self._replay_timer.setInterval(700)
        self._replay_timer.timeout.connect(self._replay_step)
        self._auto_next_timer = QTimer(self)
        self._auto_next_timer.setSingleShot(True)
        self._auto_next_timer.timeout.connect(self._next)
        self._challenge_mode = ""
        self._challenge_active = False
        self._challenge_remaining = 0
        self._challenge_solved = 0
        self._challenge_mistakes = 0
        self._challenge_target = 12
        self._challenge_timer = QTimer(self)
        self._challenge_timer.setInterval(1000)
        self._challenge_timer.timeout.connect(self._challenge_tick)

        self._hub = _HubView(self)
        self._train = _TrainView(self)
        self._library = _LibraryView(self)
        self._profile = _ProfileView(self)
        self._stack = QStackedWidget(self)
        for view in (self._hub, self._train, self._library, self._profile):
            self._stack.addWidget(view)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        self._train.board.move_requested.connect(self._on_move_requested)
        self._hub.train_requested.connect(self._start_training)
        self._hub.mistakes_requested.connect(self._start_mistakes)
        self._hub.library_requested.connect(self.show_library)
        self._hub.profile_requested.connect(self.show_profile)
        self._hub.collection_requested.connect(self._start_collection)
        self._hub.daily_requested.connect(self._start_daily)
        self._hub.solved_requested.connect(self._start_solved)
        self._hub.sign_in_requested.connect(self.sign_in_requested.emit)
        self._hub.difficulty_changed.connect(self._set_difficulty)
        self._hub.theme_filter_changed.connect(self._set_theme_filter)
        self._hub.auto_next_changed.connect(self._set_auto_next)
        self._hub.challenge_changed.connect(self._set_challenge)
        self._train.back_requested.connect(self._back_from_train)
        self._train.hint_requested.connect(self._show_hint)
        self._train.retry_requested.connect(self._retry)
        self._train.favorite_requested.connect(self._toggle_favorite)
        self._train.reveal_requested.connect(self._reveal_solution)
        self._train.next_requested.connect(self._next)
        self._train.profile_requested.connect(self.show_profile)
        self._train.replay_requested.connect(self._replay_solution)
        self._train.vote_requested.connect(self._vote_puzzle)
        self._library.back_requested.connect(self.show_hub)
        self._library.import_requested.connect(self._choose_file)
        self._library.delete_requested.connect(self._delete_collection)
        self._library.start_requested.connect(self._start_collection)
        self._library.prev_requested.connect(lambda: self._browse(-1))
        self._library.next_requested.connect(lambda: self._browse(1))
        self._library.jump_requested.connect(self._jump)
        self._library.selection_changed.connect(self._select_collection)
        self._profile.back_requested.connect(self.show_hub)
        self._profile.range_changed.connect(self._set_profile_range)

        self._apply_icons()
        self.retranslate(self._language)
        self.refresh_collections()
        self.show_hub()

    def _apply_icons(self):
        self._train.apply_icons(self._theme)
        self._library.apply_icons(self._theme)
        self._profile.apply_icons(self._theme)

    def _find_collection(self, collection_id):
        for collection in self._collections:
            if collection.id == collection_id:
                return collection
        return None

    def refresh_collections(self, select_id=None):
        self._collections = [PuzzleCollection(meta) for meta in list_collections()]
        self._favorite_keys = favorite_keys()
        self._hub.set_collections(self._collections, self._language)
        self._library.set_collections(self._collections, select_id)
        if select_id:
            self._library.select_row(select_id)
        self._refresh_library()

    def _refresh_account(self):
        account = get_account()
        token = str(account.get("token") or "").strip()
        if token != self._token:
            self._online_stats = None
            self._online_stats_days = None
            self._hub_stats = None
            self._auth_expired = False
            self._account_id_attached = False
            self._account_id_checked = False
        self._token = token
        self._account_username = str(account.get("username") or "").strip().lower()
        self._account_id = account.get("id")
        self._server_url = get_server_url()
        if not self._token:
            self._online = False
            self._online_rating = None
            self._online_rd = None
        else:
            self._ensure_account_id()

    def _ensure_account_id(self):
        """Backfill the stable id for accounts saved before it existed."""
        if self._account_id is not None:
            if not self._account_id_attached:
                attach_outbox_account_id(self._account_id, self._account_username)
                self._account_id_attached = True
            return
        if self._account_id_checked or not self._token or not self._server_url:
            return
        if self._account_id_worker is not None and self._account_id_worker.isRunning():
            return
        worker = PuzzleOnlineWorker(
            "me",
            self._server_url,
            self._token,
            self._language,
            {},
            self,
        )
        self._account_id_worker = worker
        worker.done.connect(self._on_account_id_done)
        worker.failed.connect(self._on_account_id_failed)
        worker.finished.connect(lambda w=worker: self._clear_worker("me", w))
        worker.start()

    def _on_account_id_done(self, _action, result):
        self._account_id_checked = True
        account_id = result.get("id") if isinstance(result, dict) else None
        if account_id is None:
            return
        try:
            account_id = int(account_id)
        except (TypeError, ValueError):
            return
        self._account_id = account_id
        self._account_username = str(result.get("username") or self._account_username).lower()
        save_account(
            result.get("username", self._account_username),
            self._token,
            result.get("balance"),
            account_id,
        )
        attach_outbox_account_id(account_id, self._account_username)
        self._account_id_attached = True

    def _on_account_id_failed(self, _action, _message, _code):
        self._account_id_checked = True

    def _is_online(self):
        return bool(self._token and self._server_url and not self._auth_expired)

    def refresh_account(self):
        """Re-read the saved account after the sign-in dialog changed it."""
        self._refresh_account()
        if self._stack.currentWidget() is self._hub:
            self.show_hub()

    def show_hub(self):
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        self._stop_challenge()
        self._train.set_counter("")
        self._review_puzzles = []
        self._review_index = -1
        self._refresh_account()
        self.refresh_collections()
        self._hub.set_summary(self._hub_summary())
        self._hub.set_online(self._is_online(), self._online_rating)
        self._hub.set_notice(
            t("puzzle_online_signin_required", self._language) if self._auth_expired else ""
        )
        self._hub.set_train_enabled(True)
        self._stack.setCurrentWidget(self._hub)
        self._refresh_hub_stats()
        self._resume_attempts()

    def _hub_summary(self):
        # With an account the server is the source of truth, so the hub and the
        # profile cannot disagree after switching machines. The server caps its
        # window at 365 days, which is what "all" means here too.
        if self._is_online() and self._hub_stats is not None:
            return self._hub_stats
        return attempt_summary()

    def show_library(self):
        self.refresh_collections()
        if self._library_collection is None and self._collections:
            candidates = [item for item in self._collections if item.count > 0]
            self._select_collection((candidates or self._collections)[0].id)
        self._stack.setCurrentWidget(self._library)

    def show_profile(self):
        self._refresh_account()
        self._profile.set_range(self._profile_days)
        local = self._profile_summary()
        if self._is_online():
            if self._online_stats is not None and self._online_stats_days == self._profile_days:
                self._profile.refresh(self._online_stats, self._language)
                self._profile.set_notice("")
            else:
                self._profile.refresh(local, self._language)
                self._fetch_online_stats()
        else:
            self._profile.refresh(local, self._language)
            self._profile.set_notice("")
        self._stack.setCurrentWidget(self._profile)

    def _profile_summary(self):
        return attempt_summary(days=self._profile_days or None)

    def _set_profile_range(self, days):
        self._profile_days = int(days)
        if self._is_online():
            self._online_stats = None
            self._profile.set_notice(t("puzzle_online_loading", self._language))
            if self._stats_worker is not None and self._stats_worker.isRunning():
                self._stats_refresh_pending = True
            else:
                self._fetch_online_stats()
            return
        self._profile.refresh(self._profile_summary(), self._language)
        self._profile.set_notice("")

    def _start_training(self):
        self._refresh_account()
        if self._is_online():
            self._start_online_training()
            return
        self._start_local_training()

    def _start_local_training(self):
        preferred = None
        for collection in self._collections:
            if collection.favorite or collection.count == 0:
                continue
            if collection.builtin:
                preferred = collection
                break
            if preferred is None:
                preferred = collection
        if preferred is None:
            for collection in self._collections:
                if collection.favorite and collection.count:
                    preferred = collection
                    break
        if preferred is None:
            self.show_library()
            self._library.set_status(t("puzzle_empty", self._language))
            return
        self._start_collection(preferred.id)

    def _start_mistakes(self):
        self._refresh_account()
        if self._is_online():
            self._start_online_retry()
            return
        self._start_local_mistakes()

    def _start_local_mistakes(self):
        collection = self._find_collection(FAVORITES_ID)
        if collection is None or collection.count == 0:
            QMessageBox.information(
                self,
                t("puzzle_home_mistakes", self._language),
                t("puzzle_favorites_empty", self._language),
            )
            return
        self._start_collection(FAVORITES_ID)

    def _start_online_training(self):
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._start_online_request(
            "next",
            {"theme": self._theme_filter, "difficulty": self._difficulty},
            t("puzzle_online_loading", self._language),
        )

    def _start_online_retry(self):
        self._start_online_request(
            "retry",
            {},
            t("puzzle_online_retry_loading", self._language),
        )

    def _set_difficulty(self, value):
        self._difficulty = value if value in ("easy", "normal", "hard") else "normal"

    def _set_theme_filter(self, value):
        self._theme_filter = str(value or "")

    def _set_auto_next(self, enabled):
        self._auto_next = bool(enabled)

    def _set_challenge(self, mode):
        self._challenge_mode = mode if mode in ("storm", "racer") else ""
        if self._challenge_active:
            self._stop_challenge()
            self._train.set_counter("")
        if (
            self._challenge_mode
            and self._stack.currentWidget() is self._train
            and self._puzzle is not None
        ):
            self._start_challenge()

    def _start_challenge(self):
        if not self._challenge_mode or self._challenge_active:
            return
        self._challenge_active = True
        self._challenge_remaining = 180 if self._challenge_mode == "storm" else 60
        self._challenge_solved = 0
        self._challenge_mistakes = 0
        self._challenge_target = 12
        self._challenge_timer.start()
        self._update_challenge_label()

    def _challenge_time(self):
        minutes, seconds = divmod(max(0, self._challenge_remaining), 60)
        return f"{minutes}:{seconds:02d}"

    def _update_challenge_label(self):
        if self._challenge_mode == "storm":
            text = t(
                "puzzle_train_storm_time",
                self._language,
                time=self._challenge_time(),
                mistakes=self._challenge_mistakes,
            )
        else:
            text = t(
                "puzzle_train_racer_time",
                self._language,
                time=self._challenge_time(),
                solved=self._challenge_solved,
                target=self._challenge_target,
            )
        self._train.set_counter(text)

    def _challenge_tick(self):
        self._challenge_remaining -= 1
        self._update_challenge_label()
        if self._challenge_remaining <= 0:
            self._end_challenge()

    def _end_challenge(self):
        mode = self._challenge_mode
        self._stop_challenge()
        self._challenge_mode = ""
        self._hub.set_challenge("")
        self._auto_next_timer.stop()
        self._train.set_counter("")
        self._train.set_solving(False)
        if self._session is not None:
            self._train.board.set_interactive(False, self._session.human_color)
        if mode == "racer":
            outcome = t(
                "puzzle_train_racer_win"
                if self._challenge_solved >= self._challenge_target
                else "puzzle_train_racer_lose",
                self._language,
            )
            self._train.show_result(
                "challenge",
                t("puzzle_train_racer_title", self._language),
                t(
                    "puzzle_train_racer_detail",
                    self._language,
                    solved=self._challenge_solved,
                    target=self._challenge_target,
                    result=outcome,
                ),
            )
        else:
            self._train.show_result(
                "challenge",
                t("puzzle_train_storm_title", self._language),
                t(
                    "puzzle_train_storm_detail",
                    self._language,
                    solved=self._challenge_solved,
                    mistakes=self._challenge_mistakes,
                ),
            )
        self._train.set_next_enabled(True)

    def _stop_challenge(self):
        self._challenge_timer.stop()
        self._challenge_active = False

    def _start_daily(self):
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._start_online_request(
            "daily",
            {"difficulty": self._difficulty},
            t("puzzle_online_daily_loading", self._language),
        )

    def _start_solved(self):
        self._start_online_request(
            "solved",
            {},
            t("puzzle_online_solved_loading", self._language),
        )

    def _start_online_request(self, action, payload, notice):
        if self._next_worker is not None and self._next_worker.isRunning():
            if self._stack.currentWidget() is self._train:
                self._train.set_notice(notice)
            return
        self._hub.set_train_enabled(False)
        self._hub.set_notice(notice)
        if self._stack.currentWidget() is self._train:
            self._train.set_notice(notice)
        worker = PuzzleOnlineWorker(
            action,
            self._server_url,
            self._token,
            self._language,
            payload,
            self,
        )
        self._next_worker = worker
        worker.done.connect(self._on_online_next_done)
        worker.failed.connect(self._on_online_next_failed)
        worker.finished.connect(lambda w=worker: self._clear_worker("next", w))
        worker.start()

    def _on_online_next_done(self, action, result):
        self._hub.set_train_enabled(True)
        self._hub.set_notice("")
        if action == "solved":
            self._review_puzzles = result.get("puzzles") or []
            self._review_index = 0
            if not self._review_puzzles:
                self._hub.set_notice(t("puzzle_online_solved_empty", self._language))
                return
            self._load_review_puzzle()
            return
        self._review_puzzles = []
        self._review_index = -1
        self._load_online_puzzle(result, rated=action != "retry")
        if action == "retry":
            self._train.set_notice(t("puzzle_online_retry_unrated", self._language))

    def _load_review_puzzle(self):
        if not (0 <= self._review_index < len(self._review_puzzles)):
            self._hub.set_notice(t("puzzle_online_solved_empty", self._language))
            self.show_hub()
            return
        entry = self._review_puzzles[self._review_index]
        puzzle = entry.get("puzzle") if isinstance(entry, dict) else None
        if not isinstance(puzzle, dict):
            self._review_index += 1
            self._load_review_puzzle()
            return
        self._load_online_puzzle(
            {"puzzle": puzzle, "rating": self._online_rating, "rd": self._online_rd},
            rated=False,
        )
        self._train.set_notice(t("puzzle_online_practice", self._language))

    def _on_online_next_failed(self, action, message, code):
        self._hub.set_train_enabled(True)
        if code in ("missing_token", "unknown_token"):
            self._mark_online_expired()
        if action == "solved":
            self._hub.set_notice(t("puzzle_online_solved_empty", self._language))
            return
        if action == "daily":
            self._hub.set_notice(message)
            return
        if action == "retry" and code == "no_mistakes":
            self._hub.set_notice(message)
            return
        self.refresh_collections()
        if action == "retry":
            self._start_local_mistakes()
        else:
            self._start_local_training()
        if self._stack.currentWidget() is self._train:
            self._train.set_notice(t("puzzle_online_fallback", self._language))

    def _load_online_puzzle(self, result, rated=True):
        puzzle = result.get("puzzle") if isinstance(result, dict) else None
        if not isinstance(puzzle, dict) or not puzzle.get("fen"):
            self._start_local_training()
            return
        self._refresh_account()
        self._online = True
        self._online_rated = bool(rated)
        self._online_rating = result.get("rating")
        self._online_rd = result.get("rd")
        self._collection = None
        self._solved_keys = set()
        if not self._activate_puzzle(puzzle):
            self._train.set_prompt(t("puzzle_status_bad_data", self._language))
            self._stack.setCurrentWidget(self._train)
            return
        self._train.set_online_info(
            t(
                "puzzle_online_practice" if not self._online_rated else "puzzle_online_mode",
                self._language,
            ),
            self._online_rating,
        )
        self._train.set_prompt(
            t(
                "puzzle_train_your_turn",
                self._language,
                color=t(
                    "puzzle_side_white"
                    if self._session.human_color == chess.WHITE
                    else "puzzle_side_black",
                    self._language,
                ),
            )
        )
        self._train.set_notice("")
        self._train.set_next_enabled(True)
        self._hub.set_online(True, self._online_rating)
        self._stack.setCurrentWidget(self._train)
        self._start_challenge()

    def _refresh_hub_stats(self):
        if not self._is_online():
            return
        if self._hub_stats_worker is not None and self._hub_stats_worker.isRunning():
            return
        worker = PuzzleOnlineWorker(
            "stats",
            self._server_url,
            self._token,
            self._language,
            {"days": 365},
            self,
        )
        self._hub_stats_worker = worker
        worker.done.connect(self._on_hub_stats_done)
        worker.failed.connect(self._on_hub_stats_failed)
        worker.finished.connect(lambda w=worker: self._clear_worker("hub_stats", w))
        worker.start()

    def _on_hub_stats_done(self, _action, result):
        self._hub_stats = result
        self._online_rating = result.get("rating", self._online_rating)
        self._hub.set_summary(result)
        self._hub.set_online(True, self._online_rating)

    def _on_hub_stats_failed(self, _action, _message, code):
        if code in ("missing_token", "unknown_token"):
            self._mark_online_expired()
            return
        # Keep the local numbers on screen; the profile page explains in detail.
        self._hub.set_online(self._is_online(), self._online_rating)

    def _mark_online_expired(self):
        self._auth_expired = True
        self._online = False
        self._online_rating = None
        self._online_rd = None
        self._hub_stats = None
        self._hub.set_online(False)
        self._hub.set_notice(t("puzzle_online_signin_required", self._language))
        self._train.set_notice(t("puzzle_online_signin_required", self._language))

    def _fetch_online_stats(self):
        if self._stats_worker is not None and self._stats_worker.isRunning():
            return
        self._stats_refresh_pending = False
        self._profile.set_notice(t("puzzle_online_loading", self._language))
        self._stats_requested_days = self._profile_days
        worker = PuzzleOnlineWorker(
            "stats",
            self._server_url,
            self._token,
            self._language,
            {"days": self._profile_days},
            self,
        )
        self._stats_worker = worker
        worker.done.connect(self._on_online_stats_done)
        worker.failed.connect(self._on_online_stats_failed)
        worker.finished.connect(lambda w=worker: self._clear_worker("stats", w))
        worker.start()

    def _on_online_stats_done(self, _action, result):
        days = self._stats_requested_days
        if days != self._profile_days:
            return
        self._online_stats = result
        self._online_stats_days = days
        self._online_rating = result.get("rating")
        self._profile.refresh(result, self._language)
        self._profile.set_notice("")
        self._hub.set_online(True, self._online_rating)

    def _on_online_stats_failed(self, _action, _message, code):
        if self._stats_requested_days != self._profile_days:
            return
        if code in ("missing_token", "unknown_token"):
            self._mark_online_expired()
            return
        self._profile.set_notice(t("puzzle_online_profile_failed", self._language))

    def _clear_worker(self, kind, worker):
        if kind == "next" and self._next_worker is worker:
            self._next_worker = None
        elif kind == "stats" and self._stats_worker is worker:
            self._stats_worker = None
            if self._stats_refresh_pending:
                self._stats_refresh_pending = False
                self._fetch_online_stats()
        elif kind == "hub_stats" and self._hub_stats_worker is worker:
            self._hub_stats_worker = None
        elif kind == "attempt" and self._attempt_worker is worker:
            self._attempt_worker = None
        elif kind == "vote" and self._vote_worker is worker:
            self._vote_worker = None
        elif kind == "me" and self._account_id_worker is worker:
            self._account_id_worker = None
        worker.deleteLater()

    def _start_collection(self, collection_id, index=None):
        collection = self._find_collection(collection_id)
        if collection is None:
            return
        if collection.count == 0:
            self.show_library()
            self._library.set_status(t("puzzle_status_bad_data", self._language))
            return
        from_library = self._stack.currentWidget() is self._library
        self._online = False
        self._online_rated = True
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._collection = collection
        self._solved_keys = solved_keys(collection)
        self._train_origin = "library" if from_library else "hub"
        if index is None:
            target = self._library_index if from_library else self._start_index()
        else:
            target = index
        self._load_puzzle(max(0, min(int(target), collection.count - 1)))
        self._stack.setCurrentWidget(self._train)

    def _start_index(self):
        if self._collection is None:
            return 0
        for index in range(self._collection.count):
            if puzzle_key(self._collection.get(index)) not in self._solved_keys:
                return index
        return 0

    def _load_puzzle(self, index):
        if self._collection is None:
            return
        self._online = False
        puzzle = self._collection.get(index)
        if not self._activate_puzzle(puzzle):
            self._train.set_prompt(t("puzzle_status_bad_data", self._language))
            return
        self._index = index
        self._train.set_session_info(
            _collection_name(self._collection, self._language),
            index,
            self._collection.count,
            self._session.human_color,
        )
        self._train.set_next_enabled(True)
        self._library.set_current(self._library_collection, self._library_index)
        self._start_challenge()

    def _activate_puzzle(self, puzzle):
        self._reset_attempt_state()
        self._puzzle = None
        self._session = None
        if not isinstance(puzzle, dict) or not puzzle.get("fen"):
            self._train.hide_result()
            return False
        try:
            session = PuzzleSession(
                puzzle.get("fen", ""),
                puzzle.get("moves", []),
                bool(puzzle.get("opponent_first")),
            )
        except (ValueError, TypeError):
            self._train.hide_result()
            return False
        self._puzzle = puzzle
        self._session = session
        self._started_at = time.monotonic()
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        self._replay_moves = []
        board = self._train.board
        board.set_start_fen(puzzle.get("fen", ""))
        board.set_interactive(True, session.human_color)
        self._sync_board(animate=False)
        self._train.hide_result()
        self._train.set_game_link(puzzle.get("game_url"))
        self._train.set_favorite(puzzle_key(puzzle) in self._favorite_keys)
        self._client_attempt_id = uuid.uuid4().hex
        return True

    def _reset_attempt_state(self):
        self._attempt_recorded = False
        self._hinted = False
        self._revealing = False
        self._last_duration_ms = 0

    def _sync_board(self, animate=False):
        if self._session is None:
            self._train.board.clear()
            return
        self._train.board.set_moves(self._session.applied_moves, animate=animate)

    def _record_attempt(self, result):
        if self._attempt_recorded or self._puzzle is None:
            return
        self._attempt_recorded = True
        self._last_duration_ms = int((time.monotonic() - self._started_at) * 1000)
        source_id = self._collection.id if self._collection is not None else ""
        record_attempt(
            self._puzzle,
            result,
            source_id=source_id,
            duration_ms=self._last_duration_ms,
            hinted=self._hinted,
        )
        if self._online:
            self._queue_online_attempt(result)

    def _queue_online_attempt(self, result):
        if not self._is_online() or not self._client_attempt_id:
            return
        puzzle_id = str(self._puzzle.get("id") or "").strip()
        if not puzzle_id:
            return
        entry = {
            "puzzle_id": puzzle_id,
            "result": result,
            "duration_ms": self._last_duration_ms,
            "hinted": self._hinted,
            "rated": self._online_rated,
            "client_attempt_id": self._client_attempt_id,
            "account": self._account_username,
            "account_id": self._account_id,
            "server_url": self._server_url,
        }
        # Written before the request, so closing the app or losing the network
        # cannot turn a recorded session into a silent gap in the rating.
        append_outbox(entry)
        if not any(
            item.get("client_attempt_id") == entry["client_attempt_id"]
            for item in self._pending_attempts
        ):
            self._pending_attempts.append(entry)
        self._drain_attempts()

    def _next_pending_attempt(self):
        server_url = self._server_url.rstrip("/")
        for entry in self._pending_attempts:
            entry_account_id = str(entry.get("account_id") or "").strip()
            if self._account_id is not None and entry_account_id:
                if entry_account_id != str(self._account_id):
                    continue
            elif str(entry.get("account") or "").lower() != self._account_username:
                continue
            if str(entry.get("server_url") or "").strip().rstrip("/") != server_url:
                continue
            return entry
        return None

    def _drain_attempts(self):
        if self._attempts_paused or not self._is_online():
            return
        if self._attempt_worker is not None and self._attempt_worker.isRunning():
            return
        payload = self._next_pending_attempt()
        if payload is None:
            return
        worker = PuzzleOnlineWorker(
            "attempt",
            self._server_url,
            self._token,
            self._language,
            payload,
            self,
        )
        self._attempt_worker = worker
        worker.done.connect(
            lambda action, result, entry=payload: self._on_online_attempt_done(
                action, result, entry
            )
        )
        worker.failed.connect(
            lambda action, message, code, entry=payload: self._on_online_attempt_failed(
                action, message, code, entry
            )
        )
        worker.finished.connect(lambda w=worker: self._after_attempt_worker(w))
        worker.start()

    def _forget_attempt(self, entry):
        attempt_id = str(entry.get("client_attempt_id") or "")
        self._pending_attempts = [
            item for item in self._pending_attempts if item.get("client_attempt_id") != attempt_id
        ]
        remove_outbox(attempt_id)

    def _on_online_attempt_done(self, _action, result, entry):
        self._forget_attempt(entry)
        self._train.set_attempt_result(result, self._streak)
        rating = result.get("rating")
        if rating is None:
            return
        self._online_rating = rating
        self._online_rd = result.get("rd", self._online_rd)
        self._online_stats = None
        self._online_stats_days = None
        self._hub_stats = None
        self._train.set_rating(rating)
        self._hub.set_online(True, rating)

    def _on_online_attempt_failed(self, _action, _message, code, entry):
        if code == "puzzle_not_found":
            # The catalogue no longer has it; keeping it would block the queue.
            self._forget_attempt(entry)
            return
        if code in ("missing_token", "unknown_token"):
            self._mark_online_expired()
        self._attempts_paused = True
        self._train.set_notice(t("puzzle_online_sync_failed", self._language))
        self._schedule_attempt_retry(60000 if code == "too_many_attempts" else 30000)

    def _schedule_attempt_retry(self, delay_ms):
        self._attempt_retry_timer.start(max(1000, int(delay_ms)))

    def _resume_attempts(self):
        if self._attempt_worker is not None and self._attempt_worker.isRunning():
            return
        if self._auth_expired:
            return
        self._attempts_paused = False
        self._drain_attempts()

    def _after_attempt_worker(self, worker):
        self._clear_worker("attempt", worker)
        if not self._attempts_paused:
            self._drain_attempts()

    def _on_move_requested(self, from_square, to_square):
        session = self._session
        if session is None or session.solved or not session.is_human_turn or self._revealing:
            self._train.board.clear_selection()
            return
        if self._attempt_recorded:
            self._train.board.clear_selection()
            return
        move = chess.Move(from_square, to_square)
        piece = session.board.piece_at(from_square)
        if (
            piece is not None
            and piece.piece_type == chess.PAWN
            and chess.square_rank(to_square) in (0, 7)
        ):
            promotion = self._train.board.promotion_choice(to_square, piece.color)
            if promotion is None:
                self._train.board.clear_selection()
                return
            move = chess.Move(from_square, to_square, promotion=promotion)
        if move not in session.board.legal_moves:
            self._train.board.clear_selection()
            return
        status = session.play(move)
        self._train.board.clear_selection()
        if status == "wrong":
            self._streak = 0
            self._record_attempt("failed")
            if self._challenge_active and self._challenge_mode == "storm":
                self._challenge_mistakes += 1
                self._update_challenge_label()
                if self._challenge_mistakes >= 3:
                    self._end_challenge()
                    return
            self._auto_favorite()
            self._train.show_result(
                "failed",
                t("puzzle_train_failed_title", self._language),
                t("puzzle_train_failed_detail", self._language),
                self._solution_label(),
                meta=self._result_meta_text(),
            )
            return
        self._sync_board(animate=True)
        if session.solved:
            self._finish_solved()
        else:
            QTimer.singleShot(220, lambda s=session: self._play_reply(s))

    def _play_reply(self, session):
        if session is not self._session or session.solved or self._revealing:
            return
        if session.opponent_reply() is None:
            return
        self._sync_board(animate=True)
        if session.solved:
            self._finish_solved()

    def _finish_solved(self):
        self._streak += 1
        if self._challenge_active:
            self._challenge_solved += 1
            self._update_challenge_label()
        self._record_attempt("solved")
        self._mark_current_solved()
        self._train.show_result(
            "solved",
            t("puzzle_train_solved_title", self._language),
            self._solved_detail(),
            self._solution_label(),
            meta=self._result_meta_text(),
        )
        self._train.set_next_enabled(True)
        if self._auto_next:
            self._auto_next_timer.start(1500)

    def _result_meta_text(self):
        if self._online:
            key = "puzzle_result_pending_rating" if self._online_rated else "puzzle_result_practice"
        else:
            key = "puzzle_result_local_practice"
        text = t(key, self._language)
        if self._streak:
            text += " · " + t("puzzle_result_streak", self._language, streak=self._streak)
        return text

    def _solved_detail(self):
        rating = self._puzzle.get("rating") if self._puzzle else None
        seconds = max(1, round(self._last_duration_ms / 1000)) if self._last_duration_ms else 0
        if rating:
            return t(
                "puzzle_train_solved_detail",
                self._language,
                rating=rating,
                seconds=seconds,
            )
        return t("puzzle_train_solved_plain", self._language, seconds=seconds)

    def _solution_label(self):
        if not self._puzzle:
            return ""
        text = _solution_text(self._puzzle.get("fen", ""), self._puzzle.get("moves", []))
        if not text:
            return ""
        return t("puzzle_train_solution", self._language, moves=text)

    def _show_hint(self):
        if self._session is None or self._session.solved:
            return
        uci = self._session.expected_move
        if not uci:
            return
        self._hinted = True
        self._train.board.set_hint(uci)
        self._train.set_prompt(t("puzzle_status_hint", self._language, move=uci))

    def _reveal_solution(self):
        session = self._session
        if session is None or session.solved or self._revealing:
            return
        box = QMessageBox(self)
        box.setWindowTitle(t("puzzle_reveal_choice_title", self._language))
        box.setText(t("puzzle_reveal_choice", self._language))
        hint_button = box.addButton(
            t("puzzle_reveal_choice_hint", self._language),
            QMessageBox.ButtonRole.AcceptRole,
        )
        full_button = box.addButton(
            t("puzzle_reveal_choice_full", self._language),
            QMessageBox.ButtonRole.DestructiveRole,
        )
        box.exec()
        if box.clickedButton() is hint_button:
            self._show_hint()
            return
        if box.clickedButton() is not full_button:
            return
        self._streak = 0
        self._revealing = True
        self._record_attempt("failed")
        if self._challenge_active and self._challenge_mode == "storm":
            self._challenge_mistakes += 1
            self._update_challenge_label()
            if self._challenge_mistakes >= 3:
                self._revealing = False
                self._end_challenge()
                return
        self._train.set_solving(False)
        self._auto_play_step(session)

    def _auto_play_step(self, session):
        if session is not self._session or self._revealing is False:
            return
        if session.solved:
            self._train.show_result(
                "revealed",
                t("puzzle_train_revealed_title", self._language),
                t("puzzle_train_revealed_detail", self._language),
                self._solution_label(),
                meta=self._result_meta_text(),
            )
            return
        if session.is_human_turn:
            expected = session.expected_move
            if not expected:
                return
            try:
                move = chess.Move.from_uci(expected)
            except ValueError:
                return
            if session.play(move) == "wrong":
                return
        elif session.opponent_reply() is None:
            return
        self._sync_board(animate=True)
        if session.solved:
            self._train.show_result(
                "revealed",
                t("puzzle_train_revealed_title", self._language),
                t("puzzle_train_revealed_detail", self._language),
                self._solution_label(),
                meta=self._result_meta_text(),
            )
            return
        QTimer.singleShot(320, lambda s=session: self._auto_play_step(s))

    def _retry(self):
        if self._online and self._puzzle is not None:
            self._load_online_puzzle(
                {
                    "puzzle": self._puzzle,
                    "rating": self._online_rating,
                    "rd": self._online_rd,
                },
                rated=False,
            )
        elif self._puzzle is not None:
            self._load_puzzle(self._index)

    def _replay_solution(self):
        if not self._puzzle or self._session is None:
            return
        moves = [str(move) for move in (self._puzzle.get("moves") or [])]
        if not moves:
            return
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        self._replay_moves = moves
        self._replay_index = 0
        self._train.board.set_interactive(False, self._session.human_color)
        self._train.board.set_start_fen(self._puzzle.get("fen", ""))
        self._replay_timer.start()

    def _replay_step(self):
        if self._replay_index >= len(self._replay_moves):
            self._replay_timer.stop()
            return
        self._replay_index += 1
        self._train.board.set_moves(self._replay_moves[: self._replay_index], animate=True)
        if self._replay_index >= len(self._replay_moves):
            self._replay_timer.stop()

    def _vote_puzzle(self, value):
        if not self._is_online() or self._puzzle is None:
            self._train.set_notice(t("cloud_signin_required", self._language))
            return
        puzzle_id = str(self._puzzle.get("id") or "").strip()
        if not puzzle_id or (self._vote_worker is not None and self._vote_worker.isRunning()):
            return
        worker = PuzzleOnlineWorker(
            "vote",
            self._server_url,
            self._token,
            self._language,
            {"puzzle_id": puzzle_id, "vote": int(value)},
            self,
        )
        self._vote_worker = worker
        worker.done.connect(
            lambda _action, _result: self._train.set_notice(t("puzzle_vote_thanks", self._language))
        )
        worker.failed.connect(lambda _action, message, _code: self._train.set_notice(message))
        worker.finished.connect(lambda w=worker: self._clear_worker("vote", w))
        worker.start()

    def _next(self):
        self._auto_next_timer.stop()
        if self._review_puzzles:
            self._review_index += 1
            self._load_review_puzzle()
            return
        if self._online:
            self._start_online_training()
            return
        if self._collection is None:
            self.show_hub()
            return
        if self._index + 1 < self._collection.count:
            self._load_puzzle(self._index + 1)
            return
        if self._train_origin == "library":
            self.show_library()
        else:
            self.show_hub()

    def _back_from_train(self):
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        self._stop_challenge()
        self._train.set_counter("")
        self._review_puzzles = []
        self._review_index = -1
        if self._train_origin == "library":
            self.show_library()
        else:
            self.show_hub()

    def _toggle_favorite(self):
        if self._puzzle is None:
            return
        current_id = self._collection.id if self._collection is not None else ""
        added = toggle_favorite(self._puzzle, source_id=current_id)
        self._favorite_keys = favorite_keys()
        self.refresh_collections()
        fresh = self._find_collection(current_id)
        if fresh is not None:
            self._collection = fresh
        self._train.set_favorite(added)
        if current_id and self._collection.favorite and not added:
            self._solved_keys = solved_keys(self._collection)
            if self._collection.count:
                self._load_puzzle(min(self._index, self._collection.count - 1))
            else:
                self.show_hub()

    def _auto_favorite(self):
        if self._puzzle is None:
            return
        source_id = self._collection.id if self._collection is not None else ""
        if add_favorite(self._puzzle, source_id=source_id):
            self._favorite_keys = favorite_keys()
            self.refresh_collections()
            self._train.set_favorite(True)

    def _mark_current_solved(self):
        if self._collection is None or self._puzzle is None:
            return
        key = puzzle_key(self._puzzle)
        if not key or key in self._solved_keys:
            return
        self._solved_keys.add(key)
        mark_solved_key(self._collection.id, key)

    def _select_collection(self, collection_id):
        collection = self._find_collection(collection_id)
        self._library_collection = collection
        if collection is None:
            self._library_index = 0
        else:
            solved = solved_keys(collection)
            self._library_index = 0
            for index in range(collection.count):
                if puzzle_key(collection.get(index)) not in solved:
                    self._library_index = index
                    break
        self._refresh_library()

    def _refresh_library(self):
        if self._library_collection is not None:
            current = self._find_collection(self._library_collection.id)
            self._library_collection = current
            if current is not None and current.count:
                self._library_index = max(0, min(self._library_index, current.count - 1))
        self._library.set_current(self._library_collection, self._library_index)

    def _browse(self, delta):
        collection = self._library_collection
        if collection is None or not collection.count:
            return
        self._library_index = max(0, min(self._library_index + delta, collection.count - 1))
        self._refresh_library()

    def _jump(self, value):
        collection = self._library_collection
        if collection is None or not collection.count:
            return
        self._library_index = max(0, min(int(value) - 1, collection.count - 1))
        self._refresh_library()

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
        self._library.set_import_enabled(False)
        self._library.set_status(t("puzzle_status_loading", self._language))
        self._import_worker = PuzzleImportWorker(path, parent=self)
        self._import_worker.progress.connect(self._on_import_progress)
        self._import_worker.done.connect(self._on_import_done)
        self._import_worker.failed.connect(self._on_import_failed)
        self._import_worker.finished.connect(self._on_import_finished)
        self._import_worker.start()

    def _on_import_progress(self, count):
        self._library.set_status(t("puzzle_status_importing", self._language, count=count))

    def _on_import_done(self, meta):
        self._library.set_status(
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
        self._library.set_status(message)

    def _on_import_finished(self):
        self._library.set_import_enabled(True)
        worker = self._import_worker
        self._import_worker = None
        if worker is not None:
            worker.deleteLater()

    def _delete_collection(self, collection_id):
        collection = self._find_collection(collection_id)
        if collection is None:
            return
        answer = QMessageBox.question(
            self,
            t("puzzle_delete_title", self._language),
            t(
                "puzzle_delete_text",
                self._language,
                name=_collection_name(collection, self._language),
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        delete_collection(collection_id)
        if self._collection is not None and self._collection.id == collection_id:
            self._collection = None
            self._puzzle = None
            self._session = None
        if self._library_collection is not None and self._library_collection.id == collection_id:
            self._library_collection = None
            self._library_index = 0
        self.refresh_collections()
        self._library.set_status("")

    def retranslate(self, language):
        self._language = language
        self._train.retranslate(language)
        self._train.board.retranslate(language)
        self._hub.retranslate(language)
        self._library.retranslate(language)
        self._profile.retranslate(language)
        if self._session is not None and self._online:
            self._train.set_online_info(
                t("puzzle_online_mode", language),
                self._online_rating,
            )
            self._train.set_prompt(
                t(
                    "puzzle_train_your_turn",
                    language,
                    color=t(
                        "puzzle_side_white"
                        if self._session.human_color == chess.WHITE
                        else "puzzle_side_black",
                        language,
                    ),
                )
            )
        elif self._session is not None and self._collection is not None:
            self._train.set_session_info(
                _collection_name(self._collection, language),
                self._index,
                self._collection.count,
                self._session.human_color,
            )
        self._hub.set_collections(self._collections, language)
        self._library.set_collections(
            self._collections,
            self._library_collection.id if self._library_collection else None,
        )
        self._refresh_library()

    def set_theme(self, theme):
        self._theme = theme
        self._train.set_theme(theme)
        self._library.apply_icons(theme)
        self._profile.apply_icons(theme)

    def set_piece_set(self, name):
        self._train.set_piece_set(name)

    def set_board_theme(self, name):
        self._train.set_board_theme(name)

    def set_sound_enabled(self, enabled):
        self._train.set_sound_enabled(enabled)

    def set_sound_set(self, name):
        self._train.set_sound_set(name)

    def reset(self):
        self._collection = None
        self._puzzle = None
        self._session = None
        self._index = 0
        self._train.board.clear()
        self._train.board.set_navigation_visible(False)
        self.show_hub()

    def shutdown(self):
        for name in (
            "_import_worker",
            "_next_worker",
            "_stats_worker",
            "_attempt_worker",
        ):
            worker = getattr(self, name)
            setattr(self, name, None)
            if worker is not None and worker.isRunning():
                worker.wait(5000)
