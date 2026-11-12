import time
import uuid
from datetime import UTC, datetime

import chess
from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QButtonGroup,
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

from checkpause.assets import DEFAULT_PIECE_SET
from checkpause.core.puzzle import PuzzleSession, validate_puzzle
from checkpause.data.puzzles import (
    MISTAKES_ID,
    PuzzleCollection,
    PuzzleListCollection,
    append_outbox,
    attach_outbox_account_id,
    attempt_summary,
    delete_collection,
    list_collections,
    load_outbox,
    mark_solved_key,
    mistake_puzzles,
    puzzle_key,
    record_attempt,
    remove_outbox,
    solved_keys,
)
from checkpause.data.settings import get_account, get_server_url, save_account
from checkpause.gui.icons import action_icon
from checkpause.gui.theme import LIGHT, accent_color, token_color
from checkpause.gui.widgets.board import BoardWidget
from checkpause.gui.widgets.move_list import MoveListWidget
from checkpause.gui.workers import PuzzleGameWorker, PuzzleImportWorker, PuzzleOnlineWorker
from checkpause.i18n import t
from checkpause.resources import resource_path

# A worker that outlives a closing window must stay referenced, otherwise Qt
# destroys a running QThread and aborts the process.
_LINGERING_WORKERS = set()


def _collection_name(collection, language):
    if getattr(collection, "id", "") == MISTAKES_ID:
        return t("puzzle_home_mistakes", language)
    if collection.builtin:
        return t("puzzle_builtin_name", language)
    return collection.name


def _solution_text(fen, moves, opponent_first=False):
    """The movable line as SAN, so the result panel reads like a game.

    With ``opponent_first`` the first move is the opponent's setup, not part of
    what the solver had to find; apply it but leave it out of the label.
    """
    board = chess.Board(fen)
    move_list = list(moves or [])
    start = 0
    if opponent_first and move_list:
        try:
            setup = chess.Move.from_uci(str(move_list[0]))
        except ValueError:
            setup = None
        if setup is not None and setup in board.legal_moves:
            board.push(setup)
            start = 1
    parts = []
    for uci in move_list[start:]:
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


def _format_local_time(value):
    try:
        parsed = datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return ""
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone().strftime("%m-%d %H:%M")


def _join_theme_names(names, language):
    separator = "、" if language.startswith("zh") else ", "
    return separator.join(_theme_name(name, language) for name in names)


_THEME_NAMES = {
    "advancedPawn": ("进阶兵", "Advanced pawn"),
    "advantage": ("占据优势", "Advantage"),
    "anastasiaMate": ("阿纳斯塔西娅杀", "Anastasia's mate"),
    "arabianMate": ("阿拉伯杀", "Arabian mate"),
    "attackingF2F7": ("攻击 f2/f7", "Attacking f2/f7"),
    "attraction": ("吸引", "Attraction"),
    "backRankMate": ("底线杀", "Back-rank mate"),
    "baldwinMate": ("鲍德温杀", "Baldwin's mate"),
    "bishopEndgame": ("象残局", "Bishop endgame"),
    "bodenMate": ("博登杀", "Boden's mate"),
    "capturingDefender": ("消灭防守者", "Capturing the defender"),
    "castling": ("易位", "Castling"),
    "clearance": ("清线", "Clearance"),
    "collinearMove": ("共线移动", "Collinear move"),
    "crushing": ("碾压", "Crushing"),
    "defensiveMove": ("防守着", "Defensive move"),
    "deflection": ("引离", "Deflection"),
    "discoveredAttack": ("发现攻击", "Discovered attack"),
    "doubleBishopMate": ("双象杀", "Double-bishop mate"),
    "doubleCheck": ("双将", "Double check"),
    "dovetailMate": ("燕尾杀", "Dovetail mate"),
    "endgame": ("残局", "Endgame"),
    "enPassant": ("吃过路兵", "En passant"),
    "epauletteMate": ("肩章杀", "Epaulette mate"),
    "equality": ("均势", "Equality"),
    "exposedKing": ("暴露的王", "Exposed king"),
    "fork": ("捉双", "Fork"),
    "grecoMate": ("格雷科杀", "Greco's mate"),
    "hangingPiece": ("悬子", "Hanging piece"),
    "hookMate": ("钩杀", "Hook mate"),
    "interference": ("阻断", "Interference"),
    "intermezzo": ("中间着", "Intermezzo"),
    "killBoxMate": ("杀棋盒", "Kill-box mate"),
    "kingEndgame": ("王残局", "King endgame"),
    "kingsideAttack": ("王翼进攻", "Kingside attack"),
    "knightEndgame": ("马残局", "Knight endgame"),
    "long": ("长题", "Long puzzle"),
    "mate": ("将杀", "Mate"),
    "mateIn1": ("一步杀", "Mate in 1"),
    "mateIn2": ("两步杀", "Mate in 2"),
    "mateIn3": ("三步杀", "Mate in 3"),
    "mateIn4": ("四步杀", "Mate in 4"),
    "mateIn5": ("五步杀", "Mate in 5"),
    "middlegame": ("中局", "Middlegame"),
    "morphysMate": ("摩尔菲杀", "Morphy's mate"),
    "oneMove": ("一步题", "One move"),
    "opening": ("开局", "Opening"),
    "operaMate": ("歌剧杀", "Opera mate"),
    "overloading": ("过载", "Overloading"),
    "pawnEndgame": ("兵残局", "Pawn endgame"),
    "pin": ("牵制", "Pin"),
    "promotion": ("升变", "Promotion"),
    "queenEndgame": ("后残局", "Queen endgame"),
    "queenRookEndgame": ("后车残局", "Queen and rook endgame"),
    "queensideAttack": ("后翼进攻", "Queenside attack"),
    "quietMove": ("静着", "Quiet move"),
    "rookEndgame": ("车残局", "Rook endgame"),
    "sacrifice": ("弃子", "Sacrifice"),
    "sharpMate": ("尖锐杀", "Sharp mate"),
    "short": ("短题", "Short puzzle"),
    "skewer": ("串击", "Skewer"),
    "smotheredMate": ("闷杀", "Smothered mate"),
    "stalemate": ("逼和", "Stalemate"),
    "supportedMate": ("有援杀", "Supported mate"),
    "trapping": ("困子", "Trapping"),
    "underPromotion": ("低升变", "Underpromotion"),
    "undervaluedPiece": ("低估棋子", "Undervalued piece"),
    "veryLong": ("超长题", "Very long puzzle"),
    "vukovicMate": ("武科维奇杀", "Vukovic mate"),
    "xRay": ("X 射线", "X-ray"),
    "zugzwang": ("迫走", "Zugzwang"),
}


def _theme_name(theme, language):
    pair = _THEME_NAMES.get(str(theme))
    if pair is None:
        text = str(theme).replace("_", " ")
        text = "".join(" " + char.lower() if char.isupper() else char for char in text).strip()
        return text or "—"
    return pair[0] if language.startswith("zh") else pair[1]


def _format_duration(duration_ms):
    try:
        seconds = max(0, round(int(duration_ms or 0) / 1000))
    except (TypeError, ValueError):
        seconds = 0
    if seconds <= 0:
        return "—"
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}:{seconds:02d}"


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
        self._name = QLabel()
        self._name.setObjectName("puzzleCollectionName")
        self._meta = QLabel()
        self._meta.setObjectName("puzzleCollectionMeta")
        self._bar = QProgressBar()
        self._bar.setObjectName("puzzleCollectionBar")
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setRange(0, 100)

        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(self._name, 1)
        top.addWidget(self._meta)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(9)
        layout.addLayout(top)
        layout.addWidget(self._bar)
        layout.addStretch(1)
        self.setMinimumHeight(92)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        for widget in (self._name, self._meta, self._bar):
            widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        self.clicked.connect(lambda: self.clicked_id.emit(self._collection.id))
        self.retranslate(language)

    def sizeHint(self):
        hint = super().sizeHint()
        return QSize(hint.width(), 92)

    def minimumSizeHint(self):
        return QSize(0, 92)

    def retranslate(self, language):
        solved = len(solved_keys(self._collection))
        total = self._collection.count or 0
        self._name.setText(_collection_name(self._collection, language))
        self._meta.setText(
            t(
                "puzzle_collection_progress",
                language,
                solved=solved,
                total=total,
            )
        )
        self._bar.setValue(min(100, round(solved / total * 100)) if total else 0)


class _ModeCard(QFrame):
    clicked = Signal()

    def __init__(
        self,
        title_key,
        text_key=None,
        action_key="puzzle_mode_start",
        icon_name="",
        parent=None,
    ):
        super().__init__(parent)
        self._title_key = title_key
        self._text_key = text_key
        self._action_key = action_key
        self._description = ""
        self._icon_name = icon_name
        self._theme = LIGHT
        self.setObjectName("puzzleModeCard")

        self._icon = QLabel()
        self._icon.setFixedSize(18, 18)
        self.title = QLabel()
        self.title.setObjectName("puzzleModeTitle")
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(self._icon)
        title_row.addWidget(self.title)
        title_row.addStretch(1)

        self.text = QLabel()
        self.text.setObjectName("puzzleModeText")
        self.text.setWordWrap(True)
        self.button = QPushButton()
        self.button.setObjectName("puzzleSecondaryButton")
        self.button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.button.clicked.connect(self.clicked.emit)

        self._extra = QWidget()
        self._extra_layout = QVBoxLayout(self._extra)
        self._extra_layout.setContentsMargins(0, 0, 0, 0)
        self._extra_layout.setSpacing(4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(5)
        layout.addLayout(title_row)
        layout.addWidget(self.text)
        layout.addWidget(self._extra)
        layout.addStretch(1)
        layout.addWidget(self.button, 0, Qt.AlignmentFlag.AlignLeft)
        self.setMinimumHeight(148)

    def add_control(self, widget):
        self._extra_layout.addWidget(widget)

    def set_description(self, text):
        self._description = text or ""
        self.text.setText(self._description)
        self.text.setVisible(bool(self._description))

    def apply_icons(self, theme):
        self._theme = theme
        if not self._icon_name:
            return
        pixmap = action_icon(theme, self._icon_name).pixmap(QSize(18, 18), 1.0)
        self._icon.setPixmap(pixmap)

    def retranslate(self, language):
        self.title.setText(t(self._title_key, language))
        text = self._description or (t(self._text_key, language) if self._text_key else "")
        self.text.setText(text)
        self.text.setVisible(bool(text))
        self.button.setText(t(self._action_key, language))


def _piece_pixmap(piece_set, code, size):
    renderer = QSvgRenderer(resource_path("assets", "pieces", piece_set, code + ".svg"))
    if not renderer.isValid():
        return QPixmap()
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    return pixmap


class _BoardColumn(QWidget):
    """Keeps the board at a stable square size under the nav row."""

    SIZE = 580

    def __init__(self, board, parent=None):
        super().__init__(parent)
        self._board = board
        self._board.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._board.setFixedSize(self.SIZE, self.SIZE + self._board.chrome_height())
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._board)
        layout.addStretch(1)


class _HubView(QWidget):
    train_requested = Signal()
    library_requested = Signal()
    profile_requested = Signal()
    collection_requested = Signal(str)
    daily_requested = Signal()
    practice_requested = Signal()
    sign_in_requested = Signal()
    difficulty_changed = Signal(str)
    theme_filter_changed = Signal(str)
    auto_next_changed = Signal(bool)
    challenge_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT
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
        host = QWidget()
        host_layout = QHBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addStretch(1)
        inner = QWidget()
        inner.setObjectName("puzzleHub")
        inner.setMaximumWidth(1040)
        self._inner = inner
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 28, 32, 32)
        layout.setSpacing(18)

        self._btn_settings = QPushButton()
        self._btn_settings.setObjectName("puzzleGhostButton")
        self._btn_settings.setCheckable(True)
        self._btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_settings.toggled.connect(self._toggle_settings)

        self._page_title = QLabel()
        self._page_title.setObjectName("puzzlePageTitle")
        self._page_subtitle = QLabel()
        self._page_subtitle.setObjectName("puzzlePageSubtitle")
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(self._page_title)
        title_box.addWidget(self._page_subtitle)
        header = QHBoxLayout()
        header.setSpacing(16)
        header.addLayout(title_box)
        header.addStretch(1)
        header.addWidget(self._btn_settings, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addLayout(header)

        self._notice = QLabel()
        self._notice.setObjectName("puzzleNotice")
        self._notice.setWordWrap(True)
        self._notice.setVisible(False)
        layout.addWidget(self._notice)

        self._btn_train = QPushButton()
        self._btn_train.setObjectName("puzzlePrimaryButton")
        self._btn_train.setMinimumWidth(132)
        self._btn_train.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_train.clicked.connect(self.train_requested.emit)
        self._btn_practice = QPushButton()
        self._btn_practice.setObjectName("puzzleGhostButton")
        self._btn_practice.setMinimumWidth(132)
        self._btn_practice.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_practice.clicked.connect(self.practice_requested.emit)
        self._btn_signin = QPushButton()
        self._btn_signin.setObjectName("puzzleSecondaryButton")
        self._btn_signin.setMinimumWidth(132)
        self._btn_signin.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_signin.clicked.connect(self.sign_in_requested.emit)

        hero = QFrame()
        hero.setObjectName("puzzleHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(24, 20, 24, 20)
        hero_layout.setSpacing(24)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(3)
        self._hero_kicker = QLabel()
        self._hero_kicker.setObjectName("puzzleHeroKicker")
        self._hero_title = QLabel()
        self._hero_title.setObjectName("puzzleHeroTitle")
        self._hero_sub = QLabel()
        self._hero_sub.setObjectName("puzzleHeroSub")
        self._hero_sub.setWordWrap(True)
        hero_text.addWidget(self._hero_kicker)
        hero_text.addWidget(self._hero_title)
        hero_text.addWidget(self._hero_sub)
        hero_layout.addLayout(hero_text, 1)

        self._rating_box = QWidget()
        rating_layout = QVBoxLayout(self._rating_box)
        rating_layout.setContentsMargins(0, 0, 0, 0)
        rating_layout.setSpacing(0)
        self._rating_caption = QLabel()
        self._rating_caption.setObjectName("puzzleHeroRatingCaption")
        self._rating_value = QLabel("—")
        self._rating_value.setObjectName("puzzleHeroRating")
        rating_layout.addWidget(self._rating_caption)
        rating_layout.addWidget(self._rating_value)
        hero_layout.addWidget(self._rating_box)

        hero_actions = QVBoxLayout()
        hero_actions.setSpacing(6)
        hero_actions.addWidget(self._btn_train)
        hero_actions.addWidget(self._btn_practice)
        hero_actions.addWidget(self._btn_signin)
        hero_layout.addLayout(hero_actions)
        layout.addWidget(hero)

        self._settings = QFrame()
        self._settings.setObjectName("puzzleSettings")
        settings = QGridLayout(self._settings)
        settings.setContentsMargins(14, 10, 14, 10)
        settings.setHorizontalSpacing(10)
        settings.setVerticalSpacing(8)
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
        settings.addWidget(self._difficulty_label, 0, 0)
        settings.addWidget(self._difficulty, 0, 1)
        settings.addWidget(self._theme_label, 0, 2)
        settings.addWidget(self._theme_filter, 0, 3)
        settings.addWidget(self._auto_next, 1, 0, 1, 4)
        settings.setColumnStretch(1, 1)
        settings.setColumnStretch(3, 1)
        self._settings.setVisible(False)
        layout.addWidget(self._settings)

        modes = QHBoxLayout()
        modes.setSpacing(12)
        self._records_card = _ModeCard(
            "puzzle_home_records",
            "puzzle_records_text",
            "puzzle_mode_view",
            "list",
        )
        self._records_card.clicked.connect(self.profile_requested.emit)
        self._daily_card = _ModeCard(
            "puzzle_home_daily",
            "puzzle_daily_text",
            "puzzle_mode_start",
            "play",
        )
        self._daily_card.clicked.connect(self.daily_requested.emit)
        self._challenge_card = _ModeCard(
            "puzzle_home_challenge",
            "puzzle_challenge_text",
            "puzzle_mode_start",
            "learn_swords",
        )
        self._challenge = QComboBox()
        self._challenge.setObjectName("puzzleRange")
        self._challenge.currentIndexChanged.connect(
            lambda _index: self.challenge_changed.emit(self._challenge.currentData() or "")
        )
        self._challenge_card.add_control(self._challenge)
        self._challenge_card.clicked.connect(self.train_requested.emit)
        modes.addWidget(self._records_card, 1)
        modes.addWidget(self._daily_card, 1)
        modes.addWidget(self._challenge_card, 1)
        layout.addLayout(modes)

        collections_header = QHBoxLayout()
        self._collections_label = QLabel()
        self._collections_label.setObjectName("puzzleSectionLabel")
        self._btn_library = QPushButton()
        self._btn_library.setObjectName("puzzleGhostButton")
        self._btn_library.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_library.clicked.connect(self.library_requested.emit)
        collections_header.addWidget(self._collections_label)
        collections_header.addStretch(1)
        collections_header.addWidget(self._btn_library)
        layout.addLayout(collections_header)
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
        layout.addStretch(1)
        host_layout.addWidget(inner)
        host_layout.addStretch(1)
        scroll.setWidget(host)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.retranslate(self._language)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(0, min(1040, self.width() - 64))
        if self._inner.width() != width:
            self._inner.setFixedWidth(width)

    def _toggle_settings(self, visible):
        self._settings.setVisible(bool(visible))

    def set_online(self, online, rating=None):
        self._online = bool(online)
        self._rating = rating
        self._hero_title.setText(
            t(
                "puzzle_hub_online_title" if self._online else "puzzle_hub_local_title",
                self._language,
            )
        )
        if self._online and rating is not None:
            self._hero_sub.setText(t("puzzle_hub_rating_hint", self._language))
        elif self._online:
            self._hero_sub.setText(t("puzzle_online_loading", self._language))
        else:
            self._hero_sub.setText(t("puzzle_home_signin_hint", self._language))
        self._rating_box.setVisible(self._online and rating is not None)
        if rating is not None:
            self._rating_value.setText(str(round(float(rating))))
        self._btn_train.setText(
            t("puzzle_home_ladder" if self._online else "puzzle_home_train", self._language)
        )
        self._btn_signin.setVisible(not self._online)
        self._btn_practice.setVisible(self._online)
        self._daily_card.button.setEnabled(self._online)
        self._daily_card.button.setVisible(self._online)
        self._daily_card.set_description(
            "" if self._online else t("puzzle_daily_offline", self._language)
        )

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
        visible = list(collections)
        single = len(visible) == 1
        for index, collection in enumerate(visible):
            card = _CollectionCard(collection, language)
            card.clicked_id.connect(self.collection_requested.emit)
            self._cards.append(card)
            if single:
                self._collection_grid.addWidget(card, 0, 0, 1, 2)
            else:
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

    def apply_icons(self, theme):
        self._theme = theme
        for card in (self._records_card, self._daily_card, self._challenge_card):
            card.apply_icons(theme)

    def retranslate(self, language):
        self._language = language
        self._page_title.setText(t("puzzle_hub_title", language))
        self._page_subtitle.setText(t("puzzle_hub_subtitle", language))
        self._hero_kicker.setText(t("puzzle_hub_kicker", language))
        self._rating_caption.setText(t("puzzle_hub_rating", language))
        self._btn_signin.setText(t("puzzle_home_sign_in", language))
        self._btn_library.setText(t("puzzle_home_library", language))
        self._btn_settings.setText(t("puzzle_home_settings", language))
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
        self._btn_practice.setText(t("puzzle_home_practice", language))
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
        self._records_card.retranslate(language)
        self._daily_card.retranslate(language)
        self._challenge_card.retranslate(language)
        self._collections_label.setText(t("puzzle_home_collections", language))
        self._empty_label.setText(t("puzzle_home_no_collections", language))
        self.set_online(self._online, self._rating)
        for card in self._cards:
            card.retranslate(language)
        self.apply_icons(self._theme)


class _TrainView(QWidget):
    back_requested = Signal()
    hint_requested = Signal()
    reveal_requested = Signal()
    next_requested = Signal()
    vote_requested = Signal(int)
    analysis_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._theme = LIGHT
        self._rating = None
        self._puzzle_rating = None
        self.setObjectName("puzzleTrain")

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("puzzleGhostButton")
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.clicked.connect(self.back_requested.emit)
        self._mode_label = QLabel()
        self._mode_label.setObjectName("puzzleModeLabel")
        self._counter_label = QLabel()
        self._counter_label.setObjectName("puzzleCounterLabel")
        self._turn_text = ""
        self._turn_color = None
        self._status_state = "playing"
        self._piece_set = DEFAULT_PIECE_SET
        self._status_icon = QLabel()
        self._status_icon.setObjectName("puzzleStatusIcon")
        self._status_icon.setFixedSize(28, 28)
        self._rating_value = QLabel()
        self._rating_value.setObjectName("puzzleLadderValue")
        self._rating_value.setVisible(False)
        self._rating_delta = QLabel()
        self._rating_delta.setObjectName("puzzleLadderDelta")
        self._rating_delta.setVisible(False)

        self._btn_analyze = QPushButton()
        self._btn_analyze.setObjectName("puzzleIconButton")
        self._btn_analyze.setFixedSize(30, 30)
        self._btn_analyze.setIconSize(QSize(18, 18))
        self._btn_analyze.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_analyze.clicked.connect(self._request_analysis)

        top = QHBoxLayout()
        top.setSpacing(10)
        top.addWidget(self._btn_back)
        top.addWidget(self._mode_label)
        top.addStretch(1)
        top.addWidget(self._counter_label)

        self._prompt = QLabel()
        self._prompt.setObjectName("puzzleStatusSub")
        self._prompt.setWordWrap(True)
        self._notice = QLabel()
        self._notice.setObjectName("puzzleNotice")
        self._notice.setWordWrap(True)
        self._notice.setVisible(False)

        self.board = BoardWidget()
        self.board.set_navigation_visible(True)
        self.board.set_edit_available(False)
        self.board.set_undo_visible(False)
        self.board.setMinimumWidth(360)
        self.board.setMaximumWidth(600)
        self.board.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        self._rating_overlay = QWidget(self.board)
        rating_overlay_layout = QHBoxLayout(self._rating_overlay)
        rating_overlay_layout.setContentsMargins(0, 0, 0, 0)
        rating_overlay_layout.setSpacing(6)
        rating_overlay_layout.addWidget(self._rating_value)
        rating_overlay_layout.addWidget(self._rating_delta)
        self._rating_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self._rating_overlay.move(14, 8)
        self._rating_overlay.setVisible(False)

        self._status_title = QLabel()
        self._status_title.setObjectName("puzzleStatusTitle")
        self._status_title.setWordWrap(True)
        self._result_detail = QLabel()
        self._result_detail.setObjectName("puzzleResultDetail")
        self._result_detail.setWordWrap(True)
        self._result_detail.setVisible(False)

        self._btn_hint = QPushButton()
        self._btn_hint.setObjectName("puzzleLinkButton")
        self._btn_hint.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_hint.clicked.connect(self.hint_requested.emit)
        self._btn_reveal = QPushButton()
        self._btn_reveal.setObjectName("puzzleLinkButton")
        self._btn_reveal.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_reveal.clicked.connect(self.reveal_requested.emit)
        self._solve_actions = QWidget()
        solve_layout = QHBoxLayout(self._solve_actions)
        solve_layout.setContentsMargins(0, 0, 0, 0)
        solve_layout.setSpacing(18)
        solve_layout.addWidget(self._btn_hint)
        solve_layout.addWidget(self._btn_reveal)
        solve_layout.addStretch(1)

        self._btn_next = QPushButton()
        self._btn_next.setObjectName("puzzlePrimaryButton")
        self._btn_next.setFixedHeight(40)
        self._btn_next.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self._btn_next.setIconSize(QSize(18, 18))
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.clicked.connect(self.next_requested.emit)
        self._btn_next.setVisible(False)

        self._vote_enabled = False
        self._vote_choice = 0
        self._btn_vote_up = QPushButton()
        self._btn_vote_up.setObjectName("puzzleVoteButton")
        self._btn_vote_up.setCheckable(True)
        self._btn_vote_up.setFixedSize(32, 30)
        self._btn_vote_up.setIconSize(QSize(18, 18))
        self._btn_vote_up.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_vote_up.clicked.connect(lambda: self._on_vote(1))
        self._btn_vote_down = QPushButton()
        self._btn_vote_down.setObjectName("puzzleVoteButton")
        self._btn_vote_down.setCheckable(True)
        self._btn_vote_down.setFixedSize(32, 30)
        self._btn_vote_down.setIconSize(QSize(18, 18))
        self._btn_vote_down.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_vote_down.clicked.connect(lambda: self._on_vote(-1))
        self._vote_row = QWidget()
        vote_layout = QHBoxLayout(self._vote_row)
        vote_layout.setContentsMargins(0, 0, 0, 0)
        vote_layout.setSpacing(6)
        vote_layout.addWidget(self._btn_vote_up)
        vote_layout.addWidget(self._btn_vote_down)
        vote_layout.addStretch(1)
        vote_layout.addWidget(self._btn_analyze)
        self._vote_row.setVisible(False)

        self._move_list = MoveListWidget()
        self._move_list.setObjectName("puzzleMoveList")
        self._move_list.setVisible(False)
        self._move_list.ply_selected.connect(self.board.goto)
        self.board.index_changed.connect(self._move_list.set_current_ply)
        self._moves_empty = QLabel()
        self._moves_empty.setObjectName("puzzleEmptyLabel")
        self._moves_empty.setWordWrap(True)
        self._moves_empty.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._moves_empty.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        self._move_box = QFrame()
        self._move_box.setObjectName("puzzleMoveBox")
        self._move_box.setMinimumHeight(180)
        self._move_box.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Expanding,
        )
        move_layout = QVBoxLayout(self._move_box)
        move_layout.setContentsMargins(6, 6, 6, 6)
        move_layout.setSpacing(2)
        move_layout.addWidget(self._moves_empty, 1)
        move_layout.addWidget(self._move_list, 1)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(self._status_title)
        title_row.addStretch(1)
        status_text = QVBoxLayout()
        status_text.setSpacing(2)
        status_text.addLayout(title_row)
        status_text.addWidget(self._prompt)
        status_header = QHBoxLayout()
        status_header.setSpacing(12)
        status_header.addWidget(self._status_icon, 0, Qt.AlignmentFlag.AlignTop)
        status_header.addLayout(status_text, 1)

        self._play_card = QFrame()
        self._play_card.setObjectName("puzzleStatusCard")
        play_layout = QVBoxLayout(self._play_card)
        play_layout.setContentsMargins(16, 14, 16, 14)
        play_layout.setSpacing(12)
        play_layout.addLayout(status_header)
        play_layout.addWidget(self._result_detail)
        play_layout.addWidget(self._notice)
        play_layout.addWidget(self._solve_actions)
        play_layout.addWidget(self._btn_next)
        play_layout.addWidget(self._vote_row)

        side = QFrame()
        side.setObjectName("puzzleTrainSide")
        side.setFixedWidth(340)
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        side_layout.setSpacing(12)
        side_layout.addWidget(self._play_card)
        side_layout.addWidget(self._move_box, 1)

        board_column = _BoardColumn(self.board)
        board_column.setFixedWidth(_BoardColumn.SIZE)

        content = QHBoxLayout()
        content.setSpacing(12)
        content.addStretch(1)
        content.addWidget(board_column)
        content.addWidget(side)
        content.addStretch(1)

        self._workspace = QWidget()
        self._workspace.setMaximumWidth(1040)
        workspace_layout = QVBoxLayout(self._workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(12)
        workspace_layout.addLayout(top)
        workspace_layout.addLayout(content, 1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 20)
        layout.addStretch(1)
        layout.addWidget(self._workspace)
        layout.addStretch(1)
        self.set_line("")
        self.hide_result()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(0, min(1040, self.width() - 56))
        if self._workspace.width() != width:
            self._workspace.setFixedWidth(width)

    def set_rating(self, rating, delta=None):
        self._rating = rating
        if rating is None:
            self._rating_value.setVisible(False)
            self._rating_delta.setVisible(False)
            self._rating_overlay.setVisible(False)
            return
        self._rating_value.setText(str(round(float(rating))))
        self._rating_value.setVisible(True)
        if delta is None:
            self._rating_delta.clear()
            self._rating_delta.setVisible(False)
        else:
            self._rating_delta.setText(f"{round(float(delta)):+d}")
            self._rating_delta.setProperty("sign", "up" if float(delta) >= 0 else "down")
            self._rating_delta.style().unpolish(self._rating_delta)
            self._rating_delta.style().polish(self._rating_delta)
            self._rating_delta.setVisible(True)
        self._rating_overlay.adjustSize()
        self._rating_overlay.setVisible(True)
        self._rating_overlay.raise_()

    def set_online_info(self, mode, rating):
        self._mode_label.setText(mode or "")
        self._mode_label.setVisible(bool(mode))
        self._counter_label.clear()
        self.set_rating(rating)

    def set_session_info(self, mode, index, total, human_color):
        self._mode_label.setText(mode or "")
        self._mode_label.setVisible(bool(mode))
        self.set_rating(None)
        self._counter_label.setText(
            t(
                "puzzle_train_progress",
                self._language,
                index=index + 1,
                total=total,
            )
        )
        self.set_turn(human_color)

    def _status_pixmap(self, kind):
        if kind == "turn":
            if self._turn_color is None:
                return QPixmap()
            code = "wK" if self._turn_color == chess.WHITE else "bK"
            return _piece_pixmap(self._piece_set, code, 26)
        if kind == "check":
            color = token_color(self._theme, "success")
            return action_icon(self._theme, "check", color=color).pixmap(QSize(22, 22), 1.0)
        if kind == "x":
            color = token_color(self._theme, "danger")
            return action_icon(self._theme, "x", color=color).pixmap(QSize(22, 22), 1.0)
        return action_icon(self._theme, "flag").pixmap(QSize(20, 20), 1.0)

    def _set_status(self, state, title, sub, icon_kind=None):
        self._status_state = state
        self._play_card.setProperty("state", state)
        self._play_card.style().unpolish(self._play_card)
        self._play_card.style().polish(self._play_card)
        self._status_title.setText(title or "")
        self._prompt.setText(sub or "")
        self._prompt.setVisible(bool(sub))
        if icon_kind:
            self._status_icon.setPixmap(self._status_pixmap(icon_kind))
            self._status_icon.setVisible(True)
        else:
            self._status_icon.clear()
            self._status_icon.setVisible(False)

    def set_turn(self, human_color):
        self._turn_color = human_color
        color = t(
            "puzzle_side_white" if human_color == chess.WHITE else "puzzle_side_black",
            self._language,
        )
        self._set_status(
            "playing",
            t("puzzle_train_your_turn", self._language, color=color),
            t("puzzle_train_find_best", self._language),
            "turn",
        )
        self._turn_text = ""
        self._result_detail.setVisible(False)
        self._notice.setVisible(False)
        self._solve_actions.setVisible(True)
        self._btn_next.setVisible(False)
        self._vote_row.setVisible(False)
        self._vote_choice = 0
        self._sync_vote_icons()
        self.set_solving(True)

    def show_correct(self):
        self._set_status(
            "correct",
            t("puzzle_train_best_move", self._language),
            t("puzzle_train_keep_going", self._language),
            "check",
        )
        self._result_detail.setVisible(False)
        self._solve_actions.setVisible(True)
        self._btn_next.setVisible(False)
        self._vote_row.setVisible(False)

    def show_wrong(self):
        self._set_status(
            "wrong",
            t("puzzle_train_not_best", self._language),
            t("puzzle_train_try_again", self._language),
            "x",
        )
        self._result_detail.setVisible(False)
        self._solve_actions.setVisible(True)
        self._btn_next.setVisible(False)
        self._vote_row.setVisible(False)

    def set_prompt(self, text):
        self._turn_text = text or ""
        self._status_state = "error"
        self._status_title.clear()
        self._status_icon.clear()
        self._status_icon.setVisible(False)
        self._prompt.setText(self._turn_text)
        self._prompt.setVisible(bool(self._turn_text))
        self._solve_actions.setVisible(False)
        self._result_detail.setVisible(False)
        self._btn_next.setVisible(False)
        self._vote_row.setVisible(False)

    def set_puzzle_info(self, rating):
        self._puzzle_rating = rating

    def set_line(self, pgn):
        if not pgn:
            self._move_list.clear()
            self._move_list.setVisible(False)
            self._moves_empty.setVisible(True)
            self._update_analyze_state()
            return
        if self._move_list.set_moves(pgn):
            self._move_list.setVisible(True)
            self._move_list.set_current_ply(self.board.index)
            self._moves_empty.setVisible(False)
        else:
            self._move_list.clear()
            self._move_list.setVisible(False)
            self._moves_empty.setVisible(True)
        self._update_analyze_state()

    def _update_analyze_state(self):
        self._btn_analyze.setEnabled(self.board.index > 0)

    def set_counter(self, text):
        self._counter_label.setText(text or "")

    def set_notice(self, text=""):
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))

    def set_solving(self, solving):
        self._btn_hint.setEnabled(solving)
        self._btn_reveal.setEnabled(solving)
        self._update_analyze_state()

    def show_result(self, state, title, detail):
        icon = "check" if state == "solved" else "flag"
        self._set_status(state, title, "", icon)
        self._result_detail.setText(detail if state == "challenge" else "")
        self._result_detail.setVisible(state == "challenge" and bool(detail))
        self._solve_actions.setVisible(False)
        self._btn_next.setVisible(True)
        show_tools = state == "solved"
        self._vote_row.setVisible(show_tools)
        self._btn_vote_up.setVisible(show_tools and self._vote_enabled)
        self._btn_vote_down.setVisible(show_tools and self._vote_enabled)
        self.set_solving(False)

    def _request_analysis(self):
        if self.board.index <= 0:
            return
        self.analysis_requested.emit(self.board.line_pgn(self.board.index))

    def hide_result(self):
        self._turn_text = ""
        self._set_status("playing", "", "")
        self._result_detail.clear()
        self._result_detail.setVisible(False)
        self._notice.setVisible(False)
        self._solve_actions.setVisible(True)
        self._btn_next.setVisible(False)
        self._vote_row.setVisible(False)
        self._vote_choice = 0
        self._sync_vote_icons()
        self.set_solving(True)
        if self._turn_color is not None:
            self.set_turn(self._turn_color)

    def set_next_enabled(self, enabled):
        self._btn_next.setEnabled(enabled)

    def set_vote_enabled(self, enabled):
        self._vote_enabled = bool(enabled)
        self._btn_vote_up.setVisible(self._vote_enabled)
        self._btn_vote_down.setVisible(self._vote_enabled)

    def _on_vote(self, value):
        if not self._vote_enabled or self._vote_choice == value:
            self._sync_vote_icons()
            return
        self._vote_choice = value
        self._sync_vote_icons()
        self.vote_requested.emit(value)

    def _sync_vote_icons(self):
        for button, value, name in (
            (self._btn_vote_up, 1, "thumb_up"),
            (self._btn_vote_down, -1, "thumb_down"),
        ):
            selected = self._vote_choice == value
            button.setChecked(selected)
            color = accent_color(self._theme) if selected else None
            button.setIcon(action_icon(self._theme, name, color=color))
            button.setIconSize(QSize(18, 18))

    def apply_icons(self, theme):
        self._theme = theme
        for button, name in (
            (self._btn_back, "nav_prev"),
            (self._btn_analyze, "rail_analysis"),
        ):
            button.setIcon(action_icon(theme, name))
            button.setIconSize(QSize(18, 18))
        self._btn_next.setIcon(action_icon(theme, "play", on_accent=True))
        self._btn_next.setIconSize(QSize(18, 18))
        kinds = {
            "playing": "turn",
            "correct": "check",
            "wrong": "x",
            "solved": "check",
            "revealed": "flag",
            "challenge": "flag",
        }
        kind = kinds.get(self._status_state)
        if kind:
            pixmap = self._status_pixmap(kind)
            self._status_icon.setPixmap(pixmap)
            self._status_icon.setVisible(not pixmap.isNull())
        self._sync_vote_icons()

    def retranslate(self, language):
        self._language = language
        self._btn_back.setText(t("puzzle_train_back", language))
        self._btn_hint.setText(t("puzzle_train_hint", language))
        self._btn_reveal.setText(t("puzzle_train_reveal", language))
        self._btn_next.setText(t("puzzle_train_continue", language))
        self._moves_empty.setText(t("puzzle_train_no_moves", language))
        for button, key in (
            (self._btn_vote_up, "puzzle_vote_up"),
            (self._btn_vote_down, "puzzle_vote_down"),
        ):
            label = t(key, language)
            button.setToolTip(label)
            button.setAccessibleName(label)
        self._btn_analyze.setAccessibleName(t("puzzle_train_analyze", language))
        self.set_rating(self._rating)
        self.set_puzzle_info(self._puzzle_rating)
        state = self._status_state
        if state == "playing" and self._turn_color is not None:
            self.set_turn(self._turn_color)
        elif state == "correct":
            self.show_correct()
        elif state == "wrong":
            self.show_wrong()
        elif state == "solved":
            self.show_result("solved", t("puzzle_train_solved_title", language), "")
        elif state == "revealed":
            self.show_result("revealed", t("puzzle_train_revealed_title", language), "")
        self._update_analyze_state()

    def set_theme(self, theme):
        self.board.set_theme(theme)
        self._move_list.set_theme(theme)
        self.apply_icons(theme)

    def set_piece_set(self, name):
        self._piece_set = name
        self.board.set_piece_set(name)
        if self._status_state == "playing" and self._turn_color is not None:
            self._status_icon.setPixmap(self._status_pixmap("turn"))

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
        self._info_meta = QLabel()
        self._info_meta.setObjectName("puzzleLibraryStatus")
        self._info_meta.setWordWrap(True)
        self._hint = QLabel()
        self._hint.setObjectName("puzzleLibraryStatus")
        self._hint.setWordWrap(True)
        self._current_label = QLabel()
        self._current_label.setObjectName("puzzleSectionLabel")
        self._status = QLabel()
        self._status.setObjectName("puzzleLibraryStatus")
        self._status.setWordWrap(True)
        self._progress = QProgressBar()
        self._progress.setObjectName("puzzleLibraryBar")
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(6)
        self._progress.setRange(0, 100)

        self._list = QListWidget()
        self._list.setObjectName("puzzleLibraryList")
        self._list.setSpacing(2)
        self._list.currentRowChanged.connect(self._on_row_changed)

        self._btn_prev = QPushButton()
        self._btn_prev.setObjectName("puzzleSecondaryButton")
        self._btn_prev.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_prev.clicked.connect(self.prev_requested.emit)
        self._jump_edit = QLineEdit()
        self._jump_edit.setFixedWidth(56)
        self._jump_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._jump_edit.returnPressed.connect(self._emit_jump)
        self._jump_total = QLabel()
        self._jump_total.setObjectName("puzzleCounterLabel")
        self._btn_jump = QPushButton()
        self._btn_jump.setObjectName("puzzleSecondaryButton")
        self._btn_jump.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_jump.clicked.connect(self._emit_jump)
        self._btn_next = QPushButton()
        self._btn_next.setObjectName("puzzleSecondaryButton")
        self._btn_next.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_next.clicked.connect(self.next_requested.emit)
        nav = QHBoxLayout()
        nav.setSpacing(8)
        nav.addWidget(self._btn_prev)
        nav.addWidget(self._jump_edit)
        nav.addWidget(self._jump_total)
        nav.addWidget(self._btn_jump)
        nav.addWidget(self._btn_next)
        nav.addStretch(1)

        self._btn_start = QPushButton()
        self._btn_start.setObjectName("puzzlePrimaryButton")
        self._btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_start.clicked.connect(self._emit_start)

        left = QFrame()
        left.setObjectName("puzzleLibraryCard")
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(10)
        left_layout.addWidget(self._list, 1)
        left_layout.addLayout(nav)

        right = QFrame()
        right.setObjectName("puzzleLibraryCard")
        right.setFixedWidth(300)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(20, 18, 20, 18)
        right_layout.setSpacing(10)
        right_layout.addWidget(self._current_label)
        right_layout.addWidget(self._info)
        right_layout.addWidget(self._info_meta)
        right_layout.addWidget(self._progress)
        right_layout.addWidget(self._status)
        right_layout.addWidget(self._hint)
        right_layout.addStretch(1)
        right_layout.addWidget(self._btn_start)

        content = QHBoxLayout()
        content.setSpacing(14)
        content.addWidget(left, 1)
        content.addWidget(right)

        self._workspace = QWidget()
        self._workspace.setMaximumWidth(1040)
        workspace_layout = QVBoxLayout(self._workspace)
        workspace_layout.setContentsMargins(0, 0, 0, 0)
        workspace_layout.setSpacing(12)
        workspace_layout.addLayout(header)
        workspace_layout.addLayout(content, 1)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 28)
        layout.addStretch(1)
        layout.addWidget(self._workspace)
        layout.addStretch(1)
        self.retranslate(self._language)
        self.set_current(None, 0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(0, min(1040, self.width() - 64))
        if self._workspace.width() != width:
            self._workspace.setFixedWidth(width)

    def set_collections(self, collections, current_id=None):
        self._collections = list(collections)
        self._list.blockSignals(True)
        self._list.clear()
        for collection in collections:
            name = _collection_name(collection, self._language)
            meta = t(
                "puzzle_collection_progress",
                self._language,
                solved=len(solved_keys(collection)),
                total=collection.count,
            )
            item = QListWidgetItem(f"{name}\n{meta}")
            item.setData(Qt.ItemDataRole.UserRole, collection.id)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            item.setSizeHint(QSize(0, 54))
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
        self._btn_delete.setEnabled(has_collection)
        self._btn_start.setEnabled(has_collection and collection.count > 0)
        self._btn_prev.setEnabled(has_collection)
        self._btn_next.setEnabled(has_collection)
        self._btn_jump.setEnabled(has_collection)
        self._jump_edit.setEnabled(has_collection)
        self._progress.setVisible(has_collection)
        if not has_collection:
            self._info.setText(t("puzzle_library_select", self._language))
            self._info_meta.clear()
            self._current_label.setVisible(False)
            self._progress.setValue(0)
            self._jump_edit.clear()
            self._jump_total.clear()
            return
        solved = len(solved_keys(collection))
        total = collection.count or 0
        self._current_label.setVisible(True)
        self._progress.setValue(min(100, round(solved / total * 100)) if total else 0)
        self._info.setText(_collection_name(collection, self._language))
        self._info_meta.setText(
            t(
                "puzzle_collection_progress",
                self._language,
                solved=solved,
                total=total,
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
                self._list.blockSignals(True)
                self._list.setCurrentRow(row)
                self._list.blockSignals(False)
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
            button.setIconSize(QSize(18, 18))

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
        self._current_label.setText(t("puzzle_library_current", language))
        self._hint.setText(t("puzzle_library_hint", language))
        self._jump_edit.setAccessibleName(t("puzzle_jump_tip", language))


class _ProfileView(QWidget):
    back_requested = Signal()
    range_changed = Signal(int)
    mistakes_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._language = "zh-CN"
        self._summary = {}
        self._range_days = 30

        scroll = QScrollArea()
        scroll.setObjectName("puzzleScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        host_layout = QHBoxLayout(host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        host_layout.addStretch(1)
        inner = QWidget()
        inner.setObjectName("puzzleProfile")
        inner.setMaximumWidth(1040)
        self._inner = inner
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(14)

        self._btn_back = QPushButton()
        self._btn_back.setObjectName("puzzleGhostButton")
        self._btn_back.clicked.connect(self.back_requested.emit)
        self._title = QLabel()
        self._title.setObjectName("puzzleHeaderTitle")
        self._btn_mistakes = QPushButton()
        self._btn_mistakes.setObjectName("puzzlePrimaryButton")
        self._btn_mistakes.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_mistakes.clicked.connect(self.mistakes_requested.emit)
        self._range_box = QFrame()
        self._range_box.setObjectName("puzzleRangeGroup")
        range_layout = QHBoxLayout(self._range_box)
        range_layout.setContentsMargins(2, 2, 2, 2)
        range_layout.setSpacing(0)
        self._range_group = QButtonGroup(self._range_box)
        self._range_group.setExclusive(True)
        self._range_buttons = []
        for days in (7, 30, 90, 0):
            button = QPushButton()
            button.setObjectName("puzzleRangeButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, value=days: self._on_range_button(value))
            self._range_group.addButton(button)
            range_layout.addWidget(button)
            self._range_buttons.append((days, button))
        header = QHBoxLayout()
        header.setSpacing(8)
        header.addWidget(self._btn_back)
        header.addWidget(self._title)
        header.addStretch(1)
        header.addWidget(self._btn_mistakes)
        header.addWidget(self._range_box)
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

        self._rating_hero = QFrame()
        self._rating_hero.setObjectName("puzzleRatingHero")
        hero_layout = QHBoxLayout(self._rating_hero)
        hero_layout.setContentsMargins(20, 16, 20, 16)
        hero_layout.setSpacing(18)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(2)
        self._rating_caption = QLabel()
        self._rating_caption.setObjectName("puzzleRatingCaption")
        self._rating_value = QLabel("—")
        self._rating_value.setObjectName("puzzleRatingValue")
        self._rating_sub = QLabel()
        self._rating_sub.setObjectName("puzzleRatingSub")
        self._rating_sub.setWordWrap(True)
        hero_text.addWidget(self._rating_caption)
        hero_text.addWidget(self._rating_value)
        hero_text.addWidget(self._rating_sub)
        hero_layout.addLayout(hero_text, 1)
        layout.addWidget(self._rating_hero)

        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self._attempted = _StatCard("puzzle_profile_attempts")
        self._accuracy = _StatCard("puzzle_profile_accuracy")
        self._avg_time = _StatCard("puzzle_profile_avg_time")
        self._active_days = _StatCard("puzzle_profile_active_days")
        for card in (self._attempted, self._accuracy, self._avg_time, self._active_days):
            metrics.addWidget(card, 1)
        layout.addLayout(metrics)

        self._details = QFrame()
        self._details.setObjectName("puzzleProfileDetails")
        details_layout = QGridLayout(self._details)
        details_layout.setContentsMargins(16, 12, 16, 12)
        details_layout.setHorizontalSpacing(18)
        details_layout.setVerticalSpacing(2)
        self._detail_values = {}
        for index, key in enumerate(
            (
                "puzzle_profile_best_streak",
                "puzzle_profile_retryable",
                "puzzle_profile_solved_avg",
                "puzzle_profile_failed_avg",
            )
        ):
            caption = QLabel()
            caption.setObjectName("puzzleDetailCaption")
            value = QLabel("—")
            value.setObjectName("puzzleDetailValue")
            details_layout.addWidget(caption, 0, index)
            details_layout.addWidget(value, 1, index)
            details_layout.setColumnStretch(index, 1)
            self._detail_values[key] = (caption, value)
        layout.addWidget(self._details)

        self._themes_label = QLabel()
        self._themes_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._themes_label)
        self._themes_box = QFrame()
        self._themes_box.setObjectName("puzzleThemeBox")
        self._themes_layout = QGridLayout(self._themes_box)
        self._themes_layout.setContentsMargins(16, 12, 16, 12)
        self._themes_layout.setHorizontalSpacing(14)
        self._themes_layout.setVerticalSpacing(9)
        self._themes_layout.setColumnStretch(0, 1)
        self._themes_layout.setColumnStretch(3, 1)
        layout.addWidget(self._themes_box)
        self._empty_themes = QLabel()
        self._empty_themes.setObjectName("puzzleEmptyLabel")
        layout.addWidget(self._empty_themes)

        self._recent_label = QLabel()
        self._recent_label.setObjectName("puzzleSectionLabel")
        layout.addWidget(self._recent_label)
        self._recent_box = QFrame()
        self._recent_box.setObjectName("puzzleRecentBox")
        self._recent_layout = QVBoxLayout(self._recent_box)
        self._recent_layout.setContentsMargins(10, 8, 10, 8)
        self._recent_layout.setSpacing(2)
        layout.addWidget(self._recent_box)
        self._empty = QLabel()
        self._empty.setObjectName("puzzleEmptyLabel")
        self._empty.setWordWrap(True)
        layout.addWidget(self._empty)
        layout.addStretch(1)
        host_layout.addWidget(inner)
        host_layout.addStretch(1)
        scroll.setWidget(host)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)
        self.retranslate(self._language)
        self.refresh({}, self._language)
        self.set_range(self._range_days)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        width = max(0, min(1040, self.width() - 64))
        if self._inner.width() != width:
            self._inner.setFixedWidth(width)

    def _on_range_button(self, days):
        self._range_days = int(days)
        self._update_scope()
        self.range_changed.emit(self._range_days)

    def set_range(self, days):
        for value, button in self._range_buttons:
            if value == days:
                button.setChecked(True)
                self._range_days = days
                self._update_scope()
                return

    def _update_scope(self):
        if self._summary.get("rating") is None:
            self._scope_note.setText(t("puzzle_profile_scope_local", self._language))
            return
        key = "puzzle_profile_scope_days" if self._range_days else "puzzle_profile_scope_all"
        self._scope_note.setText(t(key, self._language, days=self._range_days))

    def set_notice(self, text=""):
        self._notice.setText(text or "")
        self._notice.setVisible(bool(text))

    def refresh(self, summary, language):
        self._language = language
        self._summary = summary or {}
        rating = self._summary.get("rating")
        self._rating_hero.setVisible(rating is not None)
        if rating is not None:
            self._rating_value.setText(f"{float(rating):.1f}")
            parts = []
            rd = self._summary.get("rd")
            if rd is not None:
                parts.append(t("puzzle_profile_rd", language, rd=round(float(rd))))
            rated = self._summary.get("rating_attempts")
            if rated:
                parts.append(t("puzzle_profile_rated_count", language, count=rated))
            parts.append(
                t(
                    "puzzle_profile_streak_value",
                    language,
                    count=self._summary.get("streak", 0),
                )
            )
            parts.append(
                t(
                    "puzzle_profile_best_streak_value",
                    language,
                    count=self._summary.get("best_streak", 0),
                )
            )
            self._rating_sub.setText(" · ".join(parts))

        self._attempted.set_value(self._summary.get("attempts", 0))
        self._accuracy.set_value(f"{self._summary.get('accuracy', 0)}%")
        self._avg_time.set_value(_format_duration(self._summary.get("avg_duration_ms")))
        self._active_days.set_value(self._summary.get("active_days", 0))
        for key, (caption, value) in self._detail_values.items():
            caption.setText(t(key, language))
            if key == "puzzle_profile_best_streak":
                value.setText(str(self._summary.get("best_streak", 0)))
            elif key == "puzzle_profile_retryable":
                value.setText(str(self._summary.get("retryable", 0)))
            elif key == "puzzle_profile_solved_avg":
                value.setText(str(self._summary.get("solved_avg_rating") or "—"))
            else:
                value.setText(str(self._summary.get("failed_avg_rating") or "—"))

        self._btn_mistakes.setVisible(int(self._summary.get("retryable") or 0) > 0)
        themes = self._summary.get("themes") or []
        self._rebuild_themes(themes)
        self._rebuild_recent(self._summary.get("recent") or [])
        has_data = bool(self._summary.get("attempts"))
        self._empty.setVisible(not has_data)
        self._themes_box.setVisible(bool(themes))
        self._recent_box.setVisible(has_data and bool(self._summary.get("recent")))
        self._themes_label.setVisible(bool(themes))
        self._recent_label.setVisible(has_data and bool(self._summary.get("recent")))
        self._empty_themes.setVisible(has_data and not themes)
        self._update_scope()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _rebuild_themes(self, themes):
        self._clear_layout(self._themes_layout)
        if not themes:
            return
        headers = (
            ("puzzle_profile_theme_name", 0),
            ("puzzle_profile_theme_attempts", 1),
            ("puzzle_profile_theme_accuracy", 2),
        )
        for key, column in headers:
            label = QLabel(t(key, self._language))
            label.setObjectName("puzzleThemeHeader")
            self._themes_layout.addWidget(label, 0, column)
        rows = sorted(
            themes,
            key=lambda row: (
                0 if row.get("attempts", 0) >= 2 else 1,
                row.get("accuracy", 0),
                -row.get("attempts", 0),
            ),
        )
        for index, row in enumerate(rows, start=1):
            name = QLabel(_theme_name(row.get("theme"), self._language))
            name.setObjectName("puzzleThemeName")
            count = QLabel(str(row.get("attempts", 0)))
            count.setObjectName("puzzleThemeMeta")
            accuracy = QLabel(f"{row.get('accuracy', 0)}%")
            accuracy.setObjectName("puzzleThemeMeta")
            bar = QProgressBar()
            bar.setObjectName("puzzleThemeBar")
            bar.setRange(0, 100)
            bar.setValue(int(row.get("accuracy", 0)))
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setMinimumWidth(120)
            self._themes_layout.addWidget(name, index, 0)
            self._themes_layout.addWidget(count, index, 1)
            self._themes_layout.addWidget(accuracy, index, 2)
            self._themes_layout.addWidget(bar, index, 3)

    def _rebuild_recent(self, recent):
        self._clear_layout(self._recent_layout)
        local_profile = self._summary.get("rating") is None
        for entry in recent:
            row = QFrame()
            row.setObjectName("puzzleRecentRow")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(10, 7, 10, 7)
            row_layout.setSpacing(10)
            solved = entry.get("result") == "solved"
            badge = QLabel("✓" if solved else "✗")
            badge.setObjectName("puzzleRecentBadge")
            badge.setProperty("result", "solved" if solved else "failed")
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedWidth(22)
            themes = entry.get("themes") or []
            theme_text = _join_theme_names(themes[:2], self._language) or "—"
            theme_label = QLabel(theme_text)
            theme_label.setObjectName("puzzleRecentTheme")
            rating = entry.get("rating")
            rating_label = QLabel(
                t("puzzle_profile_rating_short", self._language, rating=rating) if rating else "—"
            )
            rating_label.setObjectName("puzzleRecentMeta")
            duration = QLabel(_format_duration(entry.get("duration_ms")))
            duration.setObjectName("puzzleRecentMeta")
            date_label = QLabel(_format_local_time(entry.get("created_at")) or "—")
            date_label.setObjectName("puzzleRecentMeta")
            practice_label = QLabel(t("puzzle_profile_practice", self._language))
            practice_label.setObjectName("puzzleRecentMeta")
            row_layout.addWidget(badge)
            row_layout.addWidget(theme_label, 1)
            row_layout.addWidget(practice_label)
            practice_label.setVisible(local_profile or entry.get("rated") is False)
            row_layout.addWidget(rating_label)
            row_layout.addWidget(duration)
            row_layout.addWidget(date_label)
            self._recent_layout.addWidget(row)

    def retranslate(self, language):
        self._language = language
        self._btn_back.setText(t("puzzle_train_back", language))
        self._title.setText(t("puzzle_profile_title", language))
        self._btn_mistakes.setText(t("puzzle_home_mistakes", language))
        range_keys = (
            "puzzle_profile_range_7",
            "puzzle_profile_range_30",
            "puzzle_profile_range_90",
            "puzzle_profile_range_all",
        )
        for (_days, button), key in zip(self._range_buttons, range_keys, strict=False):
            button.setText(t(key, language))
        self._rating_caption.setText(t("puzzle_profile_rating", language))
        self._themes_label.setText(t("puzzle_profile_themes", language))
        self._recent_label.setText(t("puzzle_profile_recent", language))
        self._empty.setText(t("puzzle_profile_empty", language))
        self._empty_themes.setText(t("puzzle_profile_no_themes", language))
        for card in (self._attempted, self._accuracy, self._avg_time, self._active_days):
            card.retranslate(language)
        self._update_scope()
        if self._summary:
            self.refresh(self._summary, language)

    def apply_icons(self, theme):
        self._btn_back.setIcon(action_icon(theme, "nav_prev"))
        self._btn_back.setIconSize(QSize(18, 18))


class PuzzlePage(QWidget):
    sign_in_requested = Signal()
    analysis_requested = Signal(str)

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
        self._practice_mode = False
        self._client_attempt_id = ""
        self._next_worker = None
        self._next_request_id = 0
        self._stats_worker = None
        self._stats_requested_days = None
        self._stats_refresh_pending = False
        self._attempt_worker = None
        self._vote_worker = None
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
        self._game_workers = set()
        self._history_moves = []
        self._history_start_fen = None
        self._history_applied = False
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
        self._challenge_paused = False
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
        self._train.analysis_requested.connect(self.analysis_requested.emit)
        self._hub.train_requested.connect(self._start_training)
        self._hub.library_requested.connect(self.show_library)
        self._hub.profile_requested.connect(self.show_profile)
        self._hub.collection_requested.connect(self._start_collection)
        self._hub.daily_requested.connect(self._start_daily)
        self._hub.practice_requested.connect(self._start_practice)
        self._hub.sign_in_requested.connect(self.sign_in_requested.emit)
        self._hub.difficulty_changed.connect(self._set_difficulty)
        self._hub.theme_filter_changed.connect(self._set_theme_filter)
        self._hub.auto_next_changed.connect(self._set_auto_next)
        self._hub.challenge_changed.connect(self._set_challenge)
        self._train.back_requested.connect(self._back_from_train)
        self._train.hint_requested.connect(self._show_hint)
        self._train.reveal_requested.connect(self._reveal_solution)
        self._train.next_requested.connect(self._next)
        self._train.vote_requested.connect(self._send_vote)
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
        self._profile.mistakes_requested.connect(self._start_mistakes)

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
        self._collections = [
            PuzzleCollection(meta) for meta in list_collections() if not meta.get("favorite")
        ]
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
        self._train_origin = "hub"
        self._practice_mode = False
        self._train.set_counter("")
        self._review_puzzles = []
        self._review_index = -1
        self._refresh_account()
        self.refresh_collections()
        self._hub.set_online(self._is_online(), self._online_rating)
        self._hub.set_notice(
            t("puzzle_online_signin_required", self._language) if self._auth_expired else ""
        )
        self._hub.set_train_enabled(True)
        self._stack.setCurrentWidget(self._hub)
        self._refresh_hub_stats()
        self._resume_attempts()

    def _preferred_collection(self):
        """User imports first, then the bundled sample."""
        preferred = None
        builtin = None
        for collection in self._collections:
            if collection.count == 0:
                continue
            if collection.builtin:
                if builtin is None:
                    builtin = collection
                continue
            if preferred is None:
                preferred = collection
        return preferred if preferred is not None else builtin

    def show_library(self):
        self.refresh_collections()
        if self._library_collection is None and self._collections:
            candidates = [item for item in self._collections if item.count > 0]
            selected = (candidates or self._collections)[0]
            self._select_collection(selected.id)
            self._library.select_row(selected.id)
        elif self._library_collection is not None:
            self._library.select_row(self._library_collection.id)
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
        preferred = self._preferred_collection()
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
        failed = mistake_puzzles()
        if not failed:
            QMessageBox.information(
                self,
                t("puzzle_home_mistakes", self._language),
                t("puzzle_mistakes_empty", self._language),
            )
            return
        collection = PuzzleListCollection(
            {
                "id": MISTAKES_ID,
                "name": "",
                "format": "memory",
                "count": len(failed),
            },
            failed,
        )
        self._start_collection_object(collection, index=0, origin="hub")

    def _start_online_training(self):
        self._practice_mode = False
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._start_online_request(
            "next",
            {"theme": self._theme_filter, "difficulty": self._difficulty},
            t("puzzle_online_loading", self._language),
        )

    def _start_online_retry(self):
        self._practice_mode = False
        self._streak = 0
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
        self._challenge_paused = False
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
        self._challenge_paused = False

    def hideEvent(self, event):
        # Switching to another module must not let a timed challenge run down
        # (or auto-advance puzzles) behind the user's back.
        if self._challenge_active and self._challenge_timer.isActive():
            self._challenge_timer.stop()
            self._challenge_paused = True
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        super().hideEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if self._challenge_active and self._challenge_paused:
            self._challenge_paused = False
            self._challenge_timer.start()

    def _start_daily(self):
        self._practice_mode = False
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._start_online_request(
            "daily",
            {"difficulty": self._difficulty},
            t("puzzle_online_daily_loading", self._language),
        )

    def _start_practice(self):
        self._refresh_account()
        if not self._is_online():
            self._start_local_training()
            return
        self._practice_mode = True
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._start_online_request(
            "practice",
            {"theme": self._theme_filter, "difficulty": self._difficulty},
            t("puzzle_online_practice_loading", self._language),
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
        self._next_request_id += 1
        request_id = self._next_request_id
        self._next_worker = worker
        worker.done.connect(
            lambda action, result, rid=request_id: self._on_online_next_done(action, result, rid)
        )
        worker.failed.connect(
            lambda action, message, code, rid=request_id: self._on_online_next_failed(
                action, message, code, rid
            )
        )
        worker.finished.connect(lambda w=worker: self._clear_worker("next", w))
        worker.start()

    def _on_online_next_done(self, action, result, request_id):
        if request_id != self._next_request_id:
            return
        self._hub.set_train_enabled(True)
        self._hub.set_notice("")
        if not self.isVisible() or self._stack.currentWidget() not in (
            self._hub,
            self._train,
        ):
            return
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
        self._load_online_puzzle(result, rated=action not in ("retry", "practice"))

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

    def _on_online_next_failed(self, action, message, code, request_id):
        if request_id != self._next_request_id:
            return
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
        if not self.isVisible() or self._stack.currentWidget() not in (
            self._hub,
            self._train,
        ):
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
            if self._stack.currentWidget() is self._train:
                self._train.set_notice(t("puzzle_online_fallback", self._language))
            return
        self._refresh_account()
        self._online = True
        self._online_rated = bool(rated)
        self._train_origin = "hub"
        self._online_rating = result.get("rating")
        self._online_rd = result.get("rd")
        self._collection = None
        self._solved_keys = set()
        if not self._activate_puzzle(puzzle):
            self._start_local_training()
            if self._stack.currentWidget() is self._train:
                self._train.set_notice(t("puzzle_online_fallback", self._language))
            return
        self._train.set_online_info(
            t(
                "puzzle_online_mode" if self._online_rated else "puzzle_online_practice",
                self._language,
            ),
            self._online_rating if self._online_rated else None,
        )
        self._train.set_turn(self._session.human_color)
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
        self._practice_mode = False
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
        self._start_collection_object(collection, index=index)

    def _start_collection_object(self, collection, index=None, origin=None):
        if collection is None or collection.count == 0:
            self.show_library()
            self._library.set_status(t("puzzle_status_bad_data", self._language))
            return
        if origin is None:
            from_library = self._stack.currentWidget() is self._library
            origin = "library" if from_library else "hub"
        # A local session supersedes any online puzzle still being fetched.
        self._next_request_id += 1
        self._online = False
        self._online_rated = True
        self._practice_mode = False
        self._review_puzzles = []
        self._review_index = -1
        self._streak = 0
        self._collection = collection
        self._solved_keys = solved_keys(collection)
        self._train_origin = origin
        if index is None:
            target = self._library_index if origin == "library" else self._start_index()
        else:
            target = index
        target = max(0, min(int(target), collection.count - 1))
        if not self._load_puzzle(target):
            if origin == "library":
                self.show_library()
                self._library.set_status(t("puzzle_status_bad_data", self._language))
            else:
                self.show_hub()
                self._hub.set_notice(t("puzzle_status_bad_data", self._language))
            return
        self._stack.setCurrentWidget(self._train)

    def _start_index(self):
        if self._collection is None:
            return 0
        for index, puzzle in self._collection.iter_from():
            if puzzle_key(puzzle) not in self._solved_keys:
                return index
        return 0

    def _load_puzzle(self, index):
        if self._collection is None:
            return False
        self._online = False
        count = self._collection.count
        if count <= 0:
            self._show_bad_puzzle()
            return False
        start = max(0, min(int(index), count - 1))
        target = start
        while target < count:
            puzzle = self._collection.get(target)
            if self._activate_puzzle(puzzle):
                break
            target += 1
        else:
            self._show_bad_puzzle()
            return False
        self._index = target
        self._train.set_session_info(
            _collection_name(self._collection, self._language),
            target,
            count,
            self._session.human_color,
        )
        if target != start:
            self._train.set_notice(
                t(
                    "puzzle_status_skipped",
                    self._language,
                    count=target - start,
                )
            )
        self._train.set_next_enabled(True)
        self._library.set_current(self._library_collection, self._library_index)
        self._start_challenge()
        return True

    def _show_bad_puzzle(self):
        self._clear_board()
        self._puzzle = None
        self._session = None
        self._train.hide_result()
        self._train.set_prompt(t("puzzle_status_bad_data", self._language))

    def _clear_board(self):
        self._train.board.clear()
        self._train.set_line("")

    def _activate_puzzle(self, puzzle):
        self._reset_attempt_state()
        self._history_moves = []
        self._history_start_fen = None
        self._history_applied = False
        self._puzzle = None
        self._session = None
        if not isinstance(puzzle, dict) or not puzzle.get("fen"):
            self._clear_board()
            self._train.hide_result()
            return False
        fen = puzzle.get("fen", "")
        moves = puzzle.get("moves", [])
        opponent_first = bool(puzzle.get("opponent_first"))
        if not validate_puzzle(fen, moves, opponent_first):
            self._clear_board()
            self._train.hide_result()
            return False
        try:
            session = PuzzleSession(fen, moves, opponent_first)
        except (ValueError, TypeError):
            self._clear_board()
            self._train.hide_result()
            return False
        self._puzzle = puzzle
        self._session = session
        self._started_at = time.monotonic()
        self._auto_next_timer.stop()
        self._replay_timer.stop()
        self._replay_moves = []
        board = self._train.board
        board.set_start_fen(fen)
        board.set_interactive(True, session.human_color)
        self._train.set_puzzle_info(puzzle.get("rating"))
        self._train.set_vote_enabled(
            bool(self._online and self._token and str(puzzle.get("id") or "").strip())
        )
        self._sync_board(animate=False)
        self._train.hide_result()
        self._train.set_notice("")
        self._client_attempt_id = uuid.uuid4().hex
        if self._online:
            self._load_game_history(puzzle)
        return True

    def _reset_attempt_state(self):
        self._attempt_recorded = False
        self._hinted = False
        self._revealing = False
        self._last_duration_ms = 0

    def _sync_board(self, animate=False):
        if self._session is None:
            self._train.board.clear()
            self._train.set_line("")
            return
        moves = list(self._session.applied_moves)
        if self._history_applied:
            moves = self._history_moves + moves
        self._train.board.set_moves(moves, animate=animate)
        self._train.set_line(self._train.board.line_pgn())

    def _show_wrong_move(self, move):
        session = self._session
        if session is None:
            return
        moves = list(session.applied_moves)
        if self._history_applied:
            moves = self._history_moves + moves
        self._train.board.set_moves(moves + [move], animate=True)
        self._train.set_line(self._train.board.line_pgn())
        self._train.board.set_interactive(False, session.human_color)
        QTimer.singleShot(800, lambda s=session: self._revert_wrong_move(s))

    def _revert_wrong_move(self, session):
        if session is not self._session:
            return
        if self._stack.currentWidget() is not self._train:
            return
        if self._revealing:
            return
        self._sync_board(animate=False)
        self._train.board.set_interactive(True, session.human_color)

    def _load_game_history(self, puzzle):
        # Only puzzles served by our own catalogue are online. Local files hold
        # just the puzzle line, so fetching their source game from Lichess would
        # make "local" collections depend on the network (and leak which
        # puzzles were opened). Offline training must stay fully offline.
        if not self._online:
            return
        puzzle_id = str(puzzle.get("id") or "").strip()
        if not puzzle_id:
            return
        worker = PuzzleGameWorker(
            puzzle_id,
            puzzle.get("fen", ""),
            bool(puzzle.get("opponent_first")),
            parent=self,
        )
        self._game_workers.add(worker)
        worker.done.connect(self._on_game_history)
        worker.finished.connect(lambda w=worker: self._finish_game_worker(w))
        worker.start()

    def _finish_game_worker(self, worker):
        self._game_workers.discard(worker)
        worker.deleteLater()

    def _on_game_history(self, puzzle_id, moves, start_fen):
        if self._puzzle is None:
            return
        if str(self._puzzle.get("id") or "").strip() != puzzle_id:
            return
        if not moves:
            return
        if self._puzzle.get("opponent_first") and moves:
            moves = moves[:-1]
        if not self._history_is_legal(start_fen, moves):
            return
        self._history_moves = list(moves)
        self._history_start_fen = start_fen or None
        self._history_applied = True
        self._train.board.set_start_fen(self._history_start_fen)
        self._sync_board(animate=False)

    def _history_is_legal(self, start_fen, moves):
        if self._session is None or self._puzzle is None:
            return False
        try:
            board = chess.Board(start_fen) if start_fen else chess.Board()
            for move in moves:
                if move not in board.legal_moves:
                    return False
                board.push(move)
            solution = [chess.Move.from_uci(str(uci)) for uci in (self._puzzle.get("moves") or [])]
        except (TypeError, ValueError):
            return False
        if self._puzzle.get("opponent_first"):
            if not solution or solution[0] not in board.legal_moves:
                return False
            board.push(solution[0])
            solution = solution[1:]
        for move in solution:
            if move not in board.legal_moves:
                return False
            board.push(move)
        return True

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
            rated=bool(self._online and self._online_rated),
        )
        if self._online:
            self._queue_online_attempt(result)

    def _send_vote(self, value):
        if not self._online or not self._token or not self._server_url or self._puzzle is None:
            return
        puzzle_id = str(self._puzzle.get("id") or "").strip()
        if not puzzle_id:
            return
        if self._vote_worker is not None and self._vote_worker.isRunning():
            return
        worker = PuzzleOnlineWorker(
            "vote",
            self._server_url,
            self._token,
            self._language,
            {"puzzle_id": puzzle_id, "vote": value},
            self,
        )
        self._vote_worker = worker
        worker.failed.connect(self._on_vote_failed)
        worker.finished.connect(lambda w=worker: self._clear_worker("vote", w))
        worker.start()

    def _on_vote_failed(self, _action, _message, _code):
        self._train.set_notice(t("puzzle_vote_failed", self._language))

    def _queue_online_attempt(self, result):
        # A dead session must not throw away the attempt: the outbox is scoped
        # to this account, and a later sign-in can still upload it.
        if not self._client_attempt_id or not self._token or not self._server_url:
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
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
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
        rating = result.get("rating")
        if rating is None:
            return
        self._online_rating = rating
        self._online_rd = result.get("rd", self._online_rd)
        self._online_stats = None
        self._online_stats_days = None
        self._hub_stats = None
        self._train.set_rating(rating, result.get("rating_delta"))
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
        expected_index = len(session.applied_moves)
        if self._history_applied:
            expected_index += len(self._history_moves)
        if self._train.board.index != expected_index:
            self._train.board.last()
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
            self._show_wrong_move(move)
            self._train.show_wrong()
            return
        self._sync_board(animate=True)
        if session.solved:
            self._finish_solved()
        else:
            self._train.show_correct()
            QTimer.singleShot(220, lambda s=session: self._play_reply(s))

    def _play_reply(self, session):
        if self._stack.currentWidget() is not self._train:
            return
        if session is not self._session or session.solved or self._revealing:
            return
        if session.opponent_reply() is None:
            return
        self._sync_board(animate=True)
        if session.solved:
            self._finish_solved()

    def _finish_solved(self):
        if not self._attempt_recorded:
            self._streak += 1
        if self._challenge_active:
            self._challenge_solved += 1
            self._update_challenge_label()
        self._record_attempt("solved")
        self._mark_current_solved()
        self._train.show_result(
            "solved",
            t("puzzle_train_solved_title", self._language),
            "",
        )
        self._train.set_next_enabled(True)
        if self._auto_next:
            self._auto_next_timer.start(1500)

    def _show_hint(self):
        if self._session is None or self._session.solved or not self._session.is_human_turn:
            return
        uci = self._session.expected_move
        if not uci:
            return
        self._hinted = True
        self._train.board.set_hint(uci)

    def _reveal_solution(self):
        session = self._session
        if session is None or session.solved or self._revealing:
            return
        if not session.is_human_turn:
            return
        already_failed = self._attempt_recorded
        self._streak = 0
        self._revealing = True
        if not already_failed:
            self._record_attempt("failed")
        if self._challenge_active and self._challenge_mode == "storm" and not already_failed:
            self._challenge_mistakes += 1
            self._update_challenge_label()
            if self._challenge_mistakes >= 3:
                self._revealing = False
                self._end_challenge()
                return
        self._train.set_solving(False)
        self._auto_play_step(session)

    def _auto_play_step(self, session):
        if self._stack.currentWidget() is not self._train:
            return
        if session is not self._session or self._revealing is False:
            return
        if session.solved:
            self._train.show_result(
                "revealed",
                t("puzzle_train_revealed_title", self._language),
                "",
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
                "",
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
        history = [move.uci() for move in self._history_moves] if self._history_applied else []
        self._replay_moves = history + moves
        self._replay_index = len(history)
        self._train.board.set_interactive(False, self._session.human_color)
        start_fen = (
            self._history_start_fen if self._history_applied else self._puzzle.get("fen", "")
        )
        self._train.board.set_start_fen(start_fen)
        if history:
            self._train.board.set_moves(history, index=len(history))
            self._train.set_line(self._train.board.line_pgn())
        self._replay_timer.start()

    def _replay_step(self):
        if self._replay_index >= len(self._replay_moves):
            self._replay_timer.stop()
            return
        self._replay_index += 1
        self._train.board.set_moves(self._replay_moves[: self._replay_index], animate=True)
        self._train.set_line(self._train.board.line_pgn())
        if self._replay_index >= len(self._replay_moves):
            self._replay_timer.stop()

    def _next(self):
        self._auto_next_timer.stop()
        if self._review_puzzles:
            self._review_index += 1
            self._load_review_puzzle()
            return
        if self._online:
            if self._practice_mode:
                self._start_practice()
            else:
                self._start_online_training()
            return
        if self._collection is None:
            self.show_hub()
            return
        if self._index + 1 < self._collection.count and self._load_puzzle(self._index + 1):
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
            for index, puzzle in collection.iter_from():
                if puzzle_key(puzzle) not in solved:
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
                t(
                    "puzzle_online_mode" if self._online_rated else "puzzle_online_practice",
                    language,
                ),
                self._online_rating if self._online_rated else None,
            )
            self._train.set_turn(self._session.human_color)
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
        self._hub.apply_icons(theme)
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

    def shutdown(self):
        for timer in (
            self._challenge_timer,
            self._attempt_retry_timer,
            self._auto_next_timer,
            self._replay_timer,
        ):
            timer.stop()
        for name in (
            "_import_worker",
            "_next_worker",
            "_stats_worker",
            "_hub_stats_worker",
            "_attempt_worker",
            "_vote_worker",
            "_account_id_worker",
        ):
            worker = getattr(self, name)
            setattr(self, name, None)
            if worker is None or not worker.isRunning():
                continue
            if name == "_import_worker" and hasattr(worker, "cancel"):
                worker.cancel()
            # Online requests use PUZZLE_TIMEOUT (10 s); wait a little longer.
            worker.wait(13000 if name != "_import_worker" else 8000)
            if worker.isRunning():
                _keep_worker_alive(worker)
        for worker in list(self._game_workers):
            if worker.isRunning():
                worker.wait(8000)
            if worker.isRunning():
                _keep_worker_alive(worker)
        self._game_workers.clear()


def _keep_worker_alive(worker):
    worker.setParent(None)
    _LINGERING_WORKERS.add(worker)
    worker.finished.connect(lambda: _LINGERING_WORKERS.discard(worker))
