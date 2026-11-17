import subprocess
import sys

from PySide6.QtCore import QLocale, QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QTabBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from checkpause import APP_VERSION
from checkpause.assets import (
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    DEFAULT_SOUND_SET,
    SOUND_CHOICES,
    SOUND_OFF,
)
from checkpause.config import (
    DEFAULT_ANALYSIS_DEPTH,
    DEFAULT_EVAL_DEPTH,
    DEFAULT_HINT_ENABLED,
    IMAGE_RECOGNITION_ENABLED,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
)
from checkpause.core import collect
from checkpause.core.engine import compact_analysis, player_side
from checkpause.core.pgn import (
    parse_pgn_game,
    parse_single_game,
    pgn_game_text,
    scan_pgn_games,
)
from checkpause.core.review import classify
from checkpause.data.profile import (
    clear_history,
    delete_history_records,
    load_profile,
    open_profile,
    set_board_theme,
    set_eval_depth,
    set_hint_enabled,
    set_language,
    set_piece_set,
    set_sound_set,
    set_theme,
    set_username,
    update_profile,
)
from checkpause.data.settings import (
    MODE_CLOUD,
    MODE_LOCAL,
    clear_account,
    get_account,
    get_api_config,
    save_account,
    save_api_config,
    save_balance,
    set_ai_mode,
)
from checkpause.gui.dialogs import (
    choose_pgn_game_dialog,
    cloud_account_dialog,
    confirm_close_dialog,
    confirm_dialog,
    confirm_update_install,
    download_update_dialog,
    pgn_paste_dialog,
    settings_dialog,
    show_update_dialog,
)
from checkpause.gui.icons import app_icon
from checkpause.gui.layouts import BoardWorkspace
from checkpause.gui.pages.analysis_page import AnalysisPage
from checkpause.gui.pages.chat_page import ChatPage
from checkpause.gui.pages.learn_page import LearnPage
from checkpause.gui.pages.play_page import PlayPage
from checkpause.gui.pages.puzzle_page import PuzzlePage
from checkpause.gui.pages.stats_page import StatsPage
from checkpause.gui.pages.welcome_page import WelcomePage
from checkpause.gui.theme import LIGHT, apply_theme
from checkpause.gui.widgets.board import BoardWidget
from checkpause.gui.widgets.eval_bar import EvalBar
from checkpause.gui.widgets.module_rail import ModuleRail
from checkpause.gui.workers import (
    AccountWorker,
    AnalysisWorker,
    ChatWorker,
    LiveAnalysisWorker,
    RecognizeWorker,
    UpdateCheckWorker,
)
from checkpause.i18n import t

MODULES = (
    {"id": "play", "label_key": "nav_play", "icon": "rail_play"},
    {"id": "puzzle", "label_key": "nav_puzzle", "icon": "rail_puzzle"},
    {"id": "learn", "label_key": "nav_learn", "icon": "rail_learn"},
    {"id": "analysis", "label_key": "nav_analysis", "icon": "rail_analysis"},
)

# At this width the board workspace (board + navigation + margins) is 624
# logical pixels tall, so the default window fits it without a page-background
# band below. Taller windows still show page background; a square board cannot
# fill a page that is taller than its pane is wide.
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 624
MIN_WINDOW_WIDTH = 920
MIN_WINDOW_HEIGHT = 600


def _system_language():
    """First-run language: Simplified Chinese on Chinese systems, else English."""
    if QLocale.system().name().startswith("zh"):
        return "zh-CN"
    return "en-US"


class _SideTabBar(QTabBar):
    """Tab bar that stretches its tabs across the whole panel width.

    A styled QTabBar ignores ``setExpanding`` (the stylesheet fixes the tab
    width), so the bar reports the panel's width and splits it evenly. This
    turns the three panel tabs into one full-width segmented control.
    """

    def sizeHint(self):
        size = super().sizeHint()
        parent = self.parentWidget()
        if parent is not None and parent.width() > size.width():
            return QSize(parent.width(), size.height())
        return size

    def tabSizeHint(self, index):
        size = super().tabSizeHint(index)
        count = self.count()
        if count <= 0 or self.width() <= 0:
            return size
        return QSize(max(size.width(), self.width() // count), size.height())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        if app is not None:
            app.setWindowIcon(app_icon())
        self.profile = load_profile()
        self._language = (self.profile or {}).get("language") or _system_language()
        self._theme = (self.profile or {}).get("theme", LIGHT)
        self._piece_set = (self.profile or {}).get("piece_set", DEFAULT_PIECE_SET)
        self._board_theme = (self.profile or {}).get("board_theme", DEFAULT_BOARD_THEME)
        self._sound_set = (self.profile or {}).get("sound_set", DEFAULT_SOUND_SET)
        self._hint_enabled = (self.profile or {}).get("hint_enabled", DEFAULT_HINT_ENABLED)
        self._eval_depth = (self.profile or {}).get("eval_depth", DEFAULT_EVAL_DEPTH)
        self._analysis_depth = (self.profile or {}).get("analysis_depth", DEFAULT_ANALYSIS_DEPTH)
        self._eval_worker = None
        self._eval_token = 0
        self._eval_failed = False
        self._messages = []
        self._results = []
        self._current_pgn = ""
        self._current_game = None
        self._current_analysis = ""
        self._user_side = ""
        api_config = get_api_config()
        self._ai_mode = api_config["mode"]
        self._server_url = api_config["server_url"]
        self._account = api_config["account"]
        # Samples an earlier run could not upload are retried in the background;
        # a launch must not depend on a network round trip for that.
        collect.flush_sample_outbox_async(self._server_url)
        self._analysis_worker = None
        self._analysis_pgn = ""
        self._chat_worker = None
        self._account_worker = None
        self._image_worker = None
        self._update_worker = None
        self._update_manual = False
        self._skipped_update = ""
        self._installing_update = False
        self._module = "analysis"

        self._stack = QStackedWidget()

        self._welcome = WelcomePage()
        self._welcome.started.connect(self._on_welcome_started)

        self._main_view = self._build_main_view()

        self._stack.addWidget(self._welcome)
        self._stack.addWidget(self._main_view)

        self._rail = self._build_rail()

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._rail)
        shell_layout.addWidget(self._stack, 1)
        self.setCentralWidget(shell)

        # A cloud profile with no account was logged out, so open on the
        # sign-in screen rather than the main view.
        if not self.profile or self._is_signed_out_cloud():
            self._show_welcome()
        else:
            self._enter_main()

        self._apply_theme()
        self._apply_board_preferences()
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        # Delayed so the window is on screen before any prompt can appear.
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._check_for_update)
        self._update_timer.start(2500)

    def _check_for_update(self, manual=False):
        self._update_timer.stop()
        if manual:
            # A manual check ignores the "Later" choice made earlier this run.
            self._skipped_update = ""
            self._update_manual = True
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        if not manual:
            self._update_manual = False
        # A manual check trusts the primary mirror and returns at once; the
        # launch-time background check stays thorough and compares every
        # mirror, which is what catches a stale primary copy.
        worker = UpdateCheckWorker(self, quick=manual)
        worker.checked.connect(self._on_update_checked)
        worker.failed.connect(self._on_update_failed)
        self._update_worker = worker
        worker.start()

    def _on_update_checked(self, info):
        manual = self._update_manual
        self._update_manual = False
        if info is None:
            if manual:
                QMessageBox.information(
                    self,
                    t("action_check_update", self._language),
                    t("update_none", self._language),
                )
            return
        # "Later" only lasts until the app closes; the next launch asks again.
        if info.version == self._skipped_update:
            return
        in_app_update = sys.platform == "win32" and getattr(sys, "frozen", False)
        if not show_update_dialog(self, self._language, info, in_app=in_app_update):
            self._skipped_update = info.version
            return
        if not in_app_update:
            return
        installer_path = download_update_dialog(self, self._language, info)
        if installer_path is None:
            return
        if not confirm_update_install(self, self._language):
            return
        self._start_update_installer(installer_path)

    def _start_update_installer(self, installer_path):
        try:
            subprocess.Popen([installer_path], close_fds=True)
        except OSError as exc:
            QMessageBox.warning(
                self,
                t("update_title", self._language),
                t("update_install_failed", self._language, error=str(exc)),
            )
            return
        self._installing_update = True
        self.close()

    def _on_update_failed(self):
        if not self._update_manual:
            return
        self._update_manual = False
        QMessageBox.warning(
            self,
            t("action_check_update", self._language),
            t("update_failed", self._language),
        )

    def _build_main_view(self):
        self._analysis_view = self._build_analysis_view()

        self.play_page = PlayPage()
        self.play_page.analysis_requested.connect(self._on_play_import)

        self.puzzle_page = PuzzlePage()
        self.puzzle_page.sign_in_requested.connect(self._open_cloud_account)
        self.puzzle_page.analysis_requested.connect(self._on_puzzle_import)
        self.learn_page = LearnPage()

        main_stack = QStackedWidget()
        main_stack.addWidget(self._analysis_view)
        main_stack.addWidget(self.play_page)
        main_stack.addWidget(self.puzzle_page)
        main_stack.addWidget(self.learn_page)
        self._main_stack = main_stack
        return main_stack

    def _build_analysis_view(self):
        self.board = BoardWidget()
        self.board.set_edit_available(True)
        self.board.set_interactive(True, None)
        self.board.set_undo_visible(True)
        self.board.set_eval_available(True)
        self.board.move_requested.connect(self._on_analysis_move_requested)
        self.board.line_changed.connect(self._on_line_changed)
        self.board.position_applied.connect(self._on_position_applied)
        self.board.position_changed.connect(self._on_position_changed)
        self.board.hint_toggled.connect(self._on_hint_toggled)
        self.board.eval_depth_changed.connect(self._on_eval_depth_changed)

        self.analysis_page = AnalysisPage()
        self.chat_page = ChatPage()
        self.stats_page = StatsPage()
        self.analysis_page.analyze_requested.connect(self._on_analyze_requested)
        self.analysis_page.stop_requested.connect(self._stop_analysis)
        self.analysis_page.open_file_requested.connect(self._open_pgn_file)
        self.analysis_page.paste_requested.connect(self._paste_pgn)
        self.analysis_page.image_requested.connect(self._recognize_image)
        self.analysis_page.clear_requested.connect(self._clear_analysis_board)
        self.analysis_page.ply_selected.connect(self.board.goto)
        self.board.index_changed.connect(self.analysis_page.set_current_ply)
        self.chat_page.send_requested.connect(self._send_chat)
        self.chat_page.reset_requested.connect(self._reset_chat)
        self.stats_page.history_cleared.connect(self._clear_history)
        self.stats_page.history_delete_requested.connect(self._delete_history_records)
        self.stats_page.analyze_requested.connect(self._open_analysis_tab)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("sidePanelTabs")
        self.tabs.setTabBar(_SideTabBar())
        self.tabs.tabBar().setCursor(Qt.CursorShape.PointingHandCursor)
        self.tabs.addTab(self.analysis_page, "")
        self.tabs.addTab(self.chat_page, "")
        self.tabs.addTab(self.stats_page, "")

        self._eval_bar = EvalBar()
        self._eval_bar.set_colors(*self.board.eval_colors())
        self.board.eval_ratio_changed.connect(self._eval_bar.set_ratio)

        bar_host = QWidget()
        bar_layout = QVBoxLayout(bar_host)
        bar_layout.setContentsMargins(6, 6, 0, 0)
        bar_layout.setSpacing(0)
        bar_layout.addWidget(self._eval_bar, 1)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(8)
        content_layout.addWidget(self.board.eval_controls())
        content_layout.addWidget(self.tabs, 1)

        panel = QWidget()
        panel.setObjectName("analysisPanel")
        panel_layout = QHBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)
        panel_layout.setSpacing(0)
        panel_layout.addWidget(bar_host)
        panel_layout.addWidget(content, 1)

        workspace = BoardWorkspace(self.board, panel)
        return workspace

    def _build_rail(self):
        rail = ModuleRail()
        for module in MODULES:
            rail.add_module(module["id"], module["label_key"], module["icon"])
        rail.module_selected.connect(self._on_module_selected)
        rail.account_clicked.connect(self._open_cloud_account)
        rail.settings_clicked.connect(self._open_settings)
        rail.retranslate(self._language)
        rail.set_account_name(self._account_button_text())
        return rail

    def _on_module_selected(self, module_id):
        if module_id not in ("analysis", "play", "puzzle", "learn"):
            return
        self._module = module_id
        if self._stack.currentWidget() is not self._main_view:
            self._enter_main()
        else:
            self._show_module()

    def _show_module(self):
        if self._module == "play":
            self._main_stack.setCurrentWidget(self.play_page)
        elif self._module == "puzzle":
            self._main_stack.setCurrentWidget(self.puzzle_page)
        elif self._module == "learn":
            self._main_stack.setCurrentWidget(self.learn_page)
        else:
            self._main_stack.setCurrentWidget(self._analysis_view)
        self._rail.set_active(self._module)

    def _open_settings(self):
        """One window for every preference; changes apply as they are made."""
        settings_dialog(
            self,
            self._language,
            {
                "theme": self._theme,
                "language": self._language,
                "piece_set": self._piece_set,
                "board_theme": self._board_theme,
                "sound_set": self._sound_set,
            },
            {
                "theme": self._change_theme,
                "language": self._set_language,
                "piece_set": self._change_piece_set,
                "board_theme": self._change_board_theme,
                "sound_set": self._change_sound_set,
                "save_byok": self._save_byok,
                "check_update": lambda: self._check_for_update(manual=True),
            },
        )

    def _set_chrome_visible(self, visible):
        self._rail.setVisible(visible)

    def _enter_main(self):
        self._language = (self.profile or {}).get("language", "zh-CN")
        self._set_chrome_visible(True)
        self._stack.setCurrentWidget(self._main_view)
        self._show_module()
        self._retranslate()
        self._sync_local_username()
        self._refresh_stats()
        self._ensure_eval_worker()

    def _is_signed_out_cloud(self):
        """True when cloud was chosen but no account is signed in any more."""
        return self._ai_mode == MODE_CLOUD and not self._account.get("token")

    def _show_welcome(self):
        self.setWindowTitle(t("app_title", self._language))
        self._set_chrome_visible(False)
        self._welcome.prepare(self._language)
        self._stack.setCurrentWidget(self._welcome)
        self._rail.set_active(None)

    def _on_welcome_started(self, result):
        username = result.get("username") or "player"
        language = result.get("language", "zh-CN")
        mode = result.get("mode", MODE_LOCAL)
        self.profile = open_profile(username, language, use_username=(mode == MODE_CLOUD))
        self._language = language
        self._theme = self.profile.get("theme", LIGHT)
        self._piece_set = self.profile.get("piece_set", DEFAULT_PIECE_SET)
        self._board_theme = self.profile.get("board_theme", DEFAULT_BOARD_THEME)
        self._sound_set = self.profile.get("sound_set", DEFAULT_SOUND_SET)
        self._hint_enabled = self.profile.get("hint_enabled", DEFAULT_HINT_ENABLED)
        self._eval_depth = self.profile.get("eval_depth", DEFAULT_EVAL_DEPTH)
        self._analysis_depth = self.profile.get("analysis_depth", DEFAULT_ANALYSIS_DEPTH)
        # The cloud account is the identity; offline just leaves it unset.
        set_ai_mode(mode)
        self._ai_mode = mode
        account = result.get("account")
        if account and account.get("token"):
            save_account(
                account.get("username", ""),
                account["token"],
                account.get("balance"),
                account.get("id"),
            )
        self._account = get_account()
        self._refresh_account_button()
        self._apply_theme()
        self._apply_board_preferences()
        self._enter_main()

    def _retranslate(self):
        self.setWindowTitle(t("app_title", self._language))
        self._refresh_account_button()

        self.tabs.setTabText(0, t("tab_analysis", self._language))
        self.tabs.setTabText(1, t("tab_chat", self._language))
        self.tabs.setTabText(2, t("tab_stats", self._language))

        self._welcome.retranslate(self._language)
        self._rail.retranslate(self._language)
        self.board.retranslate(self._language)
        self.analysis_page.retranslate(self._language)
        self.play_page.retranslate(self._language)
        self.puzzle_page.retranslate(self._language)
        self.learn_page.retranslate(self._language)
        self.chat_page.retranslate(self._language)
        self.stats_page.retranslate(self._language)
        self._refresh_stats()

    def _refresh_stats(self):
        self.stats_page.refresh(self.profile)

    def _sync_local_username(self):
        """When signed in, the cloud name is the local display name."""
        if not self.profile:
            return
        username = self._account.get("username", "")
        if self._account.get("token") and username and self.profile.get("username") != username:
            self.profile = set_username(self.profile, username)

    def _open_analysis_tab(self):
        self.tabs.setCurrentWidget(self.analysis_page)

    def _on_analyze_requested(self):
        if not self._current_pgn.strip():
            self.analysis_page.set_status(t("empty_pgn_error", self._language))
            return
        self._start_analysis(self._current_pgn)

    def _start_analysis(self, pgn):
        if self._analysis_worker and self._analysis_worker.isRunning():
            return
        if self.board.is_editing():
            self.analysis_page.set_status(t("edit_finish_first", self._language))
            return
        game = self._current_game
        if game is None or pgn != self._current_pgn:
            game = parse_single_game(pgn)
        if game is None:
            self.analysis_page.set_status(t("pgn_invalid", self._language))
            return
        ok, err = self.board.load_game(game)
        if not ok:
            self.analysis_page.set_status(t("parse_failed", self._language, error=err))
            return

        self._invalidate_analysis(clear_chat=True)
        self._current_pgn = pgn
        self._current_game = game
        self._user_side = player_side(pgn, (self.profile or {}).get("username", ""), game=game)
        self.board.set_interactive(False)
        self.board.set_edit_enabled(False)
        self.analysis_page.show_game(game)
        self.analysis_page.set_status(t("status_parsing", self._language))
        self.analysis_page.set_busy(True)
        self.tabs.setCurrentWidget(self.analysis_page)

        self._analysis_worker = AnalysisWorker(
            pgn,
            self._language,
            self,
            depth=self._analysis_depth,
            game=game,
        )
        self._analysis_pgn = pgn
        self._analysis_worker.progress.connect(self.analysis_page.set_progress)
        self._analysis_worker.move_done.connect(self._on_move_done)
        self._analysis_worker.done.connect(self._on_analysis_done)
        self._analysis_worker.failed.connect(self._on_analysis_failed)
        self._analysis_worker.finished.connect(self._on_analysis_finished)
        self._analysis_worker.start()

    def _stop_analysis(self):
        if self._analysis_worker and self._analysis_worker.isRunning():
            self._analysis_worker.requestInterruption()
            self.analysis_page.set_status(t("analysis_stopped", self._language))

    def _on_move_done(self, index, total, san, fen):
        if self._current_pgn != self._analysis_pgn:
            return
        percent = int(index / total * 100)
        self.analysis_page.set_progress(percent)
        self.analysis_page.set_status(t("status_analyzing", self._language, percent=percent))
        # The engine walks the game move by move; that is not the user
        # playing, so it must not rattle off a sound for every ply.
        self.board.goto(index, sound=False)

    def _on_analysis_move_requested(self, from_square, to_square):
        if self._analysis_worker is not None:
            return
        self.board.play_move(from_square, to_square)

    def _on_line_changed(self, replaced):
        self._invalidate_analysis(clear_chat=True)
        self._refresh_analysis_line("")

    def _on_position_applied(self, fen):
        self._invalidate_analysis(clear_chat=True)
        self._refresh_analysis_line("", show_moves=False)

    def _clear_analysis_board(self):
        self.board.clear()
        self._current_pgn = ""
        self._user_side = ""
        self._invalidate_analysis(clear_chat=True)
        self.analysis_page.show_empty()
        self.analysis_page.set_status("")

    def _invalidate_analysis(self, clear_chat=True):
        self._clear_analysis_results()
        self._current_analysis = ""
        self._current_game = None
        if clear_chat:
            self._messages = []
            self.chat_page.clear_history()

    def _clear_analysis_results(self):
        self._results = []
        self.board.set_results([])
        self.analysis_page.set_accuracy(None)
        self.analysis_page.set_review([])
        self.analysis_page.set_progress(0)

    def _refresh_analysis_line(self, status=None, show_moves=True):
        self._current_game = self.board.line_game()
        self._current_pgn = str(self._current_game)
        if show_moves:
            self.analysis_page.show_game(self._current_game)
        else:
            self.analysis_page.show_empty()
        if status is not None:
            self.analysis_page.set_status(status)

    def _on_analysis_done(self, results, accuracy):
        if self._current_pgn != self._analysis_pgn:
            return
        annotated, _ = classify(results, self._current_pgn, game=self._current_game)
        self._results = annotated
        self.board.set_results(annotated)
        self.analysis_page.set_progress(100)
        self.analysis_page.set_accuracy(accuracy)
        self.analysis_page.set_review(annotated)
        self.analysis_page.set_status(t("analysis_done", self._language))
        self.tabs.setCurrentWidget(self.analysis_page)

        if self.profile:
            self.profile = update_profile(self.profile, accuracy, self._current_pgn)
            self._refresh_stats()

        self._current_analysis = compact_analysis(annotated)
        side_label = {"white": "White", "black": "Black"}.get(self._user_side, "unknown")
        self._messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    棋谱=self._current_pgn, 数据=self._current_analysis, 执色=side_label
                ),
            },
        ]
        self.chat_page.clear_history()
        self.chat_page.append_notice(t("chat_welcome", self._language))

    def _on_analysis_failed(self, error):
        if self._current_pgn != self._analysis_pgn:
            return
        self.analysis_page.set_status(t("analysis_failed", self._language, error=error))

    def _on_analysis_finished(self):
        self.analysis_page.set_busy(False)
        self.board.set_interactive(True, None)
        self.board.set_edit_enabled(True)
        worker = self._analysis_worker
        self._analysis_worker = None
        if worker is not None:
            worker.deleteLater()
        # Live evaluation was paused while the full analysis ran; catch up on
        # whatever position the board ended on.
        self._request_live_eval(self.board.current_fen())

    def _open_pgn_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("action_open_pgn", self._language),
            "",
            "PGN (*.pgn);;All files (*.*)",
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except OSError as exc:
            self.analysis_page.set_status(str(exc))
            return
        self._load_pgn_text(content)

    def _load_pgn_text(self, text):
        try:
            games = scan_pgn_games(text)
        except (ValueError, OSError):
            games = []
        if not games:
            self.analysis_page.set_status(t("pgn_invalid", self._language))
            return False
        index = 0
        if len(games) > 1:
            index = choose_pgn_game_dialog(self, self._language, games)
            if index is None:
                return False
        game_text = pgn_game_text(text, games[index])
        game = parse_pgn_game(game_text)
        if game is None:
            self.analysis_page.set_status(t("pgn_invalid", self._language))
            return False
        return self._apply_loaded_game(game_text, game)

    def _apply_loaded_game(self, game_text, game):
        ok, err = self.board.load_game(game)
        if not ok:
            self.analysis_page.set_status(t("parse_failed", self._language, error=err))
            return False
        self._invalidate_analysis(clear_chat=True)
        self._current_pgn = game_text
        self._current_game = game
        self._user_side = player_side(
            game_text, (self.profile or {}).get("username", ""), game=game
        )
        self.analysis_page.show_game(game)
        self.analysis_page.set_status("")
        self.tabs.setCurrentWidget(self.analysis_page)
        return True

    def _paste_pgn(self):
        selection = pgn_paste_dialog(self, self._language)
        if selection:
            self._apply_loaded_game(*selection)

    def _recognize_image(self):
        if not IMAGE_RECOGNITION_ENABLED:
            return
        if self._image_worker is not None and self._image_worker.isRunning():
            return
        if self.board.is_editing():
            self.analysis_page.set_status(t("edit_finish_first", self._language))
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            t("action_open_image", self._language),
            "",
            t("image_filter", self._language),
        )
        if not path:
            return
        self.analysis_page.set_status(t("image_reading", self._language))
        self._image_worker = RecognizeWorker(path, self)
        self._image_worker.done.connect(self._on_image_recognized)
        self._image_worker.failed.connect(self._on_image_failed)
        self._image_worker.finished.connect(self._on_image_finished)
        self._image_worker.start()

    def _on_image_recognized(self, result):
        self.board.set_start_fen(result["fen"])
        self._invalidate_analysis(clear_chat=True)
        self._refresh_analysis_line(show_moves=False)
        self.tabs.setCurrentWidget(self.analysis_page)
        self.analysis_page.set_status(self._image_status(result))
        self._request_live_eval(self.board.current_fen())

    def _image_status(self, result):
        issues = list(dict.fromkeys(result.get("issues") or []))
        if not issues:
            return t("image_done", self._language)
        names = ", ".join(t("image_issue_" + code, self._language) for code in issues)
        return t("image_done_issues", self._language, issues=names)

    def _on_image_failed(self, code):
        self.analysis_page.set_status(t(code, self._language))

    def _on_image_finished(self):
        worker = self._image_worker
        self._image_worker = None
        if worker is not None:
            worker.deleteLater()

    def _on_play_import(self, pgn):
        if not self._load_pgn_text(pgn):
            return
        self._module = "analysis"
        self._show_module()
        self.tabs.setCurrentWidget(self.analysis_page)

    def _on_puzzle_import(self, pgn):
        self._on_play_import(pgn)
        if self.board.index == 0 and self.board.line_pgn():
            self.board.goto(len(self.board._moves))

    def _send_chat(self, text):
        if not self._messages:
            self.chat_page.append_notice(t("chat_no_analysis", self._language))
            return
        if self._chat_worker and self._chat_worker.isRunning():
            return
        # Cloud replies come out of a balance, so there has to be an account
        # before anything is sent.
        if (
            self._ai_mode == MODE_CLOUD
            and not self._account.get("token")
            and not self._ask_to_sign_in()
        ):
            return
        if not text.strip():
            return

        username = self.profile["username"] if self.profile else "You"
        self.chat_page.append_user(username, text)
        self._messages.append({"role": "user", "content": text})
        self.chat_page.begin_assistant()
        self.chat_page.set_busy(True)

        # Cloud mode sends raw material only: the server owns the prompt.
        cloud_request = None
        if self._ai_mode == MODE_CLOUD:
            cloud_request = {
                "server_url": self._server_url,
                "token": self._account.get("token", ""),
                "pgn": self._current_pgn,
                "analysis": self._current_analysis,
                "history": self._messages[2:],
                "side": self._user_side,
            }

        self._chat_worker = ChatWorker(
            self._messages, self._language, self, cloud_request=cloud_request
        )
        self._chat_worker.chunk.connect(self.chat_page.append_chunk)
        self._chat_worker.done.connect(self._on_chat_done)
        self._chat_worker.failed.connect(self._on_chat_failed)
        self._chat_worker.finished.connect(self._on_chat_finished)
        self._chat_worker.start()

    def _on_chat_done(self, full_reply):
        if self._ai_mode == MODE_LOCAL:
            # A local reply never reaches the server, so a de-identified copy is
            # offered for training unless the user has turned that off. The first
            # two entries are the system prompt and the game material, which the
            # sample carries separately, so only the conversation is passed on.
            collect.maybe_send_local_sample(
                self._server_url,
                self._current_pgn,
                self._current_analysis,
                self._messages[2:],
                full_reply,
                self._language,
                APP_VERSION,
                side=self._user_side,
            )
        self._messages.append({"role": "assistant", "content": full_reply})

    def _on_chat_failed(self, error):
        self.chat_page.show_error(error)

    def _on_chat_finished(self):
        self.chat_page.set_busy(False)
        worker = self._chat_worker
        self._chat_worker = None
        if worker is not None:
            worker.deleteLater()
        if self._ai_mode == MODE_CLOUD:
            self._refresh_balance()

    def _ask_to_sign_in(self):
        """Offer the account dialog; True once an account is available."""
        answer = QMessageBox.question(
            self,
            t("cloud_account_title", self._language),
            t("cloud_account_needs_signin", self._language),
        )
        if answer != QMessageBox.StandardButton.Yes:
            return False
        self._open_cloud_account()
        return bool(self._account.get("token"))

    def _account_button_text(self):
        if not self._account.get("token"):
            return t("cloud_account_not_signed_in", self._language)
        return self._account.get("username", "") or t("cloud_account_not_signed_in", self._language)

    def _refresh_account_button(self):
        if hasattr(self, "_rail"):
            self._rail.set_account_name(self._account_button_text())

    def _refresh_balance(self):
        """Ask the server what is left; the reply just came out of it."""
        if self._account_worker is not None or not self._account.get("token"):
            return
        worker = AccountWorker(
            "me",
            self._server_url,
            self._language,
            token=self._account.get("token", ""),
            parent=self,
        )
        worker.done.connect(self._on_balance)
        worker.failed.connect(lambda _message: None)
        worker.finished.connect(self._on_balance_finished)
        self._account_worker = worker
        worker.start()

    def _on_balance(self, result):
        balance = (result.get("account") or {}).get("balance")
        if balance is None:
            return
        self._account["balance"] = balance
        save_balance(balance)
        self._refresh_account_button()

    def _on_balance_finished(self):
        worker = self._account_worker
        self._account_worker = None
        if worker is not None:
            worker.deleteLater()

    def _open_cloud_account(self):
        result = cloud_account_dialog(self, self._language, get_api_config())
        if not result:
            return
        if result.get("token"):
            save_account(
                result.get("username", ""),
                result["token"],
                result.get("balance"),
                result.get("id"),
            )
        else:
            clear_account()
        self._account = get_account()
        action = result.get("action", "")
        if action in ("sign_out", "delete_account"):
            # Logging out is a full logout: go back to the sign-in screen the
            # app started on, instead of leaving the user in the main view with
            # no account behind it. A deleted account has nowhere else to go.
            self._refresh_account_button()
            self._show_welcome()
            return
        if action in ("sign_in", "register"):
            # Signing in is a choice to use the cloud tier; local stays one
            # menu click away in API settings.
            set_ai_mode(MODE_CLOUD)
            self._ai_mode = MODE_CLOUD
        if action in ("sign_in", "register", "rename") and self.profile:
            # The cloud name is the identity, so the local display follows it.
            self._sync_local_username()
            self._refresh_stats()
        self._refresh_account_button()
        if hasattr(self, "puzzle_page"):
            self.puzzle_page.refresh_account()

    def _reset_chat(self):
        self._messages = self._messages[:2]
        self.chat_page.clear_history()
        self.chat_page.append_notice(t("chat_welcome", self._language))

    def _apply_theme(self):
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self._theme)
        self._rail.set_theme(self._theme)
        self.chat_page.set_theme(self._theme)
        self.board.set_theme(self._theme)
        if hasattr(self, "_eval_bar"):
            self._eval_bar.set_colors(*self.board.eval_colors())
        self.analysis_page.set_theme(self._theme)
        self.play_page.set_theme(self._theme)
        self.puzzle_page.set_theme(self._theme)
        self.learn_page.set_theme(self._theme)

    def _apply_board_preferences(self):
        self.board.set_piece_set(self._piece_set)
        self.board.set_board_theme(self._board_theme)
        self.play_page.set_piece_set(self._piece_set)
        self.play_page.set_board_theme(self._board_theme)
        self.puzzle_page.set_piece_set(self._piece_set)
        self.puzzle_page.set_board_theme(self._board_theme)
        self.learn_page.set_piece_set(self._piece_set)
        self.learn_page.set_board_theme(self._board_theme)
        self.board.set_hint_enabled(self._hint_enabled)
        self.board.set_eval_depth(self._eval_depth)
        self._request_live_eval(self.board.current_fen())
        self._apply_sound()

    def _apply_sound(self):
        enabled = self._sound_set != SOUND_OFF
        for target in (
            self.board,
            self.play_page,
            self.puzzle_page,
            self.learn_page,
        ):
            target.set_sound_set(self._sound_set)
            target.set_sound_enabled(enabled)

    def _change_theme(self, theme):
        if theme == self._theme:
            return
        self._theme = theme
        if self.profile:
            self.profile = set_theme(self.profile, theme)
        self._apply_theme()

    def _change_piece_set(self, name):
        self._piece_set = name
        if self.profile:
            self.profile = set_piece_set(self.profile, name)
        for page in (self.board, self.play_page, self.puzzle_page, self.learn_page):
            page.set_piece_set(name)

    def _change_board_theme(self, name):
        self._board_theme = name
        if self.profile:
            self.profile = set_board_theme(self.profile, name)
        for page in (self.board, self.play_page, self.puzzle_page, self.learn_page):
            page.set_board_theme(name)

    def _change_sound_set(self, name):
        self._sound_set = name if name in SOUND_CHOICES else DEFAULT_SOUND_SET
        self._apply_sound()
        if self.profile:
            self.profile = set_sound_set(self.profile, self._sound_set)

    def _on_hint_toggled(self, enabled):
        self._hint_enabled = bool(enabled)
        retry = self._eval_failed
        self._eval_failed = False
        if self.profile:
            self.profile = set_hint_enabled(self.profile, self._hint_enabled)
        if retry:
            # The bar is evaluated whether or not hints are shown, so toggling
            # the switch must not refresh the score. Only an earlier failure
            # needs a fresh search to recover.
            self._request_live_eval(self.board.current_fen())

    def _on_eval_depth_changed(self, depth):
        self._eval_depth = int(depth)
        self._eval_failed = False
        if self.profile:
            self.profile = set_eval_depth(self.profile, self._eval_depth)
        self._request_live_eval(self.board.current_fen())

    def _on_position_changed(self, fen):
        if self._analysis_worker and self._analysis_worker.isRunning():
            # The full-game analysis runs its own engine; a second one per
            # navigated ply would only fight it for CPU.
            return
        self._request_live_eval(fen)

    def _ensure_eval_worker(self):
        if self._eval_worker is not None and self._eval_worker.isRunning():
            return self._eval_worker
        self._stop_eval_worker()
        worker = LiveAnalysisWorker(self._language, self)
        worker.evaluated.connect(self._on_live_eval)
        worker.failed.connect(self._on_live_eval_failed)
        self._eval_worker = worker
        worker.start()
        return worker

    def _request_live_eval(self, fen):
        if self._eval_failed:
            return
        worker = self._ensure_eval_worker()
        self._eval_token += 1
        # Latest wins: the worker abandons a search in flight for this one.
        worker.request(fen, self._eval_depth, self._eval_token)

    def _on_live_eval(self, result):
        if result.get("token") != self._eval_token:
            return
        self.board.apply_live_eval(result.get("lines") or [], result.get("depth"))

    def _on_live_eval_failed(self, error):
        # An unavailable engine must not break the rest of the app; stop
        # retrying every position until the feature is toggled again.
        self._eval_failed = True
        self._stop_eval_worker()

    def _stop_eval_worker(self):
        self._eval_token += 1
        worker = self._eval_worker
        self._eval_worker = None
        if worker is not None:
            worker.stop()
            worker.wait(2000)
            worker.deleteLater()

    def _save_byok(self, api_key, base_url, model):
        save_api_config(api_key, base_url, model, mode=MODE_LOCAL)
        self._ai_mode = MODE_LOCAL

    def _set_language(self, chosen):
        if not chosen or chosen == self._language:
            return
        self._language = chosen
        if self.profile:
            self.profile = set_language(self.profile, chosen)
        self._retranslate()

    def _clear_history(self):
        if not self.profile:
            return
        if not confirm_dialog(
            self,
            self._language,
            "stat_clear_history_title",
            "stat_clear_history_text",
        ):
            return
        self.profile = clear_history(self.profile)
        self._refresh_stats()

    def _delete_history_records(self, indices):
        if not self.profile or not indices:
            return
        if not confirm_dialog(
            self,
            self._language,
            "stat_delete_selected_title",
            "stat_delete_selected_text",
        ):
            return
        self.profile = delete_history_records(self.profile, indices)
        self._refresh_stats()

    def closeEvent(self, event):
        if not self._installing_update and not confirm_close_dialog(self, self._language):
            event.ignore()
            return
        self._update_timer.stop()
        if self._update_worker and self._update_worker.isRunning():
            self._update_worker.terminate()
            self._update_worker.wait(1000)
        if self._analysis_worker and self._analysis_worker.isRunning():
            self._analysis_worker.requestInterruption()
            self._analysis_worker.wait(3000)
        if self._chat_worker and self._chat_worker.isRunning():
            self._chat_worker.terminate()
            self._chat_worker.wait(1000)
        if self._image_worker and self._image_worker.isRunning():
            self._image_worker.terminate()
            self._image_worker.wait(1000)
        if self._account_worker and self._account_worker.isRunning():
            self._account_worker.terminate()
            self._account_worker.wait(500)
        self._stop_eval_worker()
        self.play_page.shutdown()
        self.puzzle_page.shutdown()
        super().closeEvent(event)
