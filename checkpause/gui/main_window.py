from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QActionGroup
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QTabWidget,
    QWidget,
)

from checkpause.assets import (
    BOARD_THEMES,
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    PIECE_SETS,
)
from checkpause.config import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from checkpause.core.engine import compact_analysis
from checkpause.data.profile import (
    create_profile,
    delete_profile,
    load_profile,
    set_board_theme,
    set_language,
    set_piece_set,
    set_theme,
    update_profile,
)
from checkpause.data.settings import get_api_config, save_api_config
from checkpause.gui.dialogs import (
    api_settings_dialog,
    choose_language_dialog,
    confirm_close_dialog,
    confirm_delete_dialog,
    show_about,
)
from checkpause.gui.pages.analysis_page import AnalysisPage
from checkpause.gui.pages.chat_page import ChatPage
from checkpause.gui.pages.play_page import PlayPage
from checkpause.gui.pages.puzzle_page import PuzzlePage
from checkpause.gui.pages.stats_page import StatsPage
from checkpause.gui.pages.welcome_page import WelcomePage
from checkpause.gui.theme import DARK, LIGHT, apply_theme
from checkpause.gui.widgets.board_widget import BoardWidget
from checkpause.gui.widgets.module_rail import ModuleRail
from checkpause.gui.workers import AnalysisWorker, ChatWorker
from checkpause.i18n import t

MODULES = (
    {"id": "play", "label_key": "nav_play"},
    {"id": "puzzle", "label_key": "nav_puzzle"},
    {"id": "analysis", "label_key": "nav_analysis"},
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.profile = load_profile()
        self._language = (self.profile or {}).get("language", "zh-CN")
        self._theme = (self.profile or {}).get("theme", LIGHT)
        self._piece_set = (self.profile or {}).get(
            "piece_set", DEFAULT_PIECE_SET
        )
        self._board_theme = (self.profile or {}).get(
            "board_theme", DEFAULT_BOARD_THEME
        )
        self._messages = []
        self._results = []
        self._current_pgn = ""
        self._analysis_worker = None
        self._chat_worker = None
        self._module = "analysis"

        self._stack = QStackedWidget()

        self._welcome = WelcomePage()
        self._welcome.started.connect(self._on_welcome_started)

        self._main_view = self._build_main_view()

        self._stack.addWidget(self._welcome)
        self._stack.addWidget(self._main_view)

        self._build_menus()
        self._rail = self._build_rail()

        shell = QWidget()
        shell_layout = QHBoxLayout(shell)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)
        shell_layout.addWidget(self._rail)
        shell_layout.addWidget(self._stack, 1)
        self.setCentralWidget(shell)

        if self.profile:
            self._enter_main()
        else:
            self._show_welcome()

        self._apply_theme()
        self._apply_board_preferences()
        self.resize(1164, 726)

    def _build_main_view(self):
        self._analysis_view = self._build_analysis_view()

        self.play_page = PlayPage()
        self.play_page.analysis_requested.connect(self._on_play_import)

        self.puzzle_page = PuzzlePage()

        main_stack = QStackedWidget()
        main_stack.addWidget(self._analysis_view)
        main_stack.addWidget(self.play_page)
        main_stack.addWidget(self.puzzle_page)
        self._main_stack = main_stack
        return main_stack

    def _build_analysis_view(self):
        self.board = BoardWidget()

        self.analysis_page = AnalysisPage()
        self.chat_page = ChatPage()
        self.stats_page = StatsPage()
        self.analysis_page.analyze_requested.connect(self._start_analysis)
        self.analysis_page.stop_requested.connect(self._stop_analysis)
        self.analysis_page.open_file_requested.connect(self._open_pgn_file)
        self.analysis_page.ply_selected.connect(self.board.goto)
        self.analysis_page.moves_shown.connect(self._on_moves_shown)
        self.board.index_changed.connect(self.analysis_page.set_current_ply)
        self.chat_page.send_requested.connect(self._send_chat)
        self.chat_page.reset_requested.connect(self._reset_chat)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.analysis_page, "")
        self.tabs.addTab(self.chat_page, "")
        self.tabs.addTab(self.stats_page, "")

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.board)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([760, 520])
        return splitter

    def _build_rail(self):
        rail = ModuleRail()
        for module in MODULES:
            rail.add_module(module["id"], module["label_key"])
        rail.module_selected.connect(self._on_module_selected)
        rail.retranslate(self._language)
        return rail

    def _on_module_selected(self, module_id):
        if module_id not in ("analysis", "play", "puzzle"):
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
        else:
            self._main_stack.setCurrentWidget(self._analysis_view)
        self._rail.set_active(self._module)

    def _build_menus(self):
        menubar = self.menuBar()

        self._menu_settings = menubar.addMenu("")

        self._menu_appearance = self._menu_settings.addMenu("")
        self._theme_group = QActionGroup(self)
        self._theme_group.setExclusive(True)
        self._act_light = QAction(self)
        self._act_light.setCheckable(True)
        self._act_light.triggered.connect(lambda: self._change_theme(LIGHT))
        self._act_dark = QAction(self)
        self._act_dark.setCheckable(True)
        self._act_dark.triggered.connect(lambda: self._change_theme(DARK))
        self._theme_group.addAction(self._act_light)
        self._theme_group.addAction(self._act_dark)
        self._menu_appearance.addAction(self._act_light)
        self._menu_appearance.addAction(self._act_dark)
        self._act_light.setChecked(self._theme == LIGHT)
        self._act_dark.setChecked(self._theme == DARK)

        self._menu_settings.addSeparator()

        self._act_api_settings = QAction(self)
        self._act_api_settings.triggered.connect(self._open_api_settings)
        self._act_language = QAction(self)
        self._act_language.triggered.connect(self._change_language)
        self._act_delete = QAction(self)
        self._act_delete.triggered.connect(self._delete_profile)
        self._menu_settings.addAction(self._act_api_settings)
        self._menu_settings.addAction(self._act_language)
        self._menu_settings.addAction(self._act_delete)

        self._menu_personalization = menubar.addMenu("")

        self._menu_pieces = self._menu_personalization.addMenu("")
        self._piece_group = QActionGroup(self)
        self._piece_group.setExclusive(True)
        self._piece_actions = {}
        for name in PIECE_SETS:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(name == self._piece_set)
            action.triggered.connect(
                lambda _checked, value=name: self._change_piece_set(value)
            )
            self._piece_group.addAction(action)
            self._menu_pieces.addAction(action)
            self._piece_actions[name] = action

        self._menu_board = self._menu_personalization.addMenu("")
        self._board_group = QActionGroup(self)
        self._board_group.setExclusive(True)
        self._board_actions = {}
        for name in BOARD_THEMES:
            action = QAction(self)
            action.setCheckable(True)
            action.setChecked(name == self._board_theme)
            action.triggered.connect(
                lambda _checked, value=name: self._change_board_theme(value)
            )
            self._board_group.addAction(action)
            self._menu_board.addAction(action)
            self._board_actions[name] = action

        self._menu_help = menubar.addMenu("")
        self._act_about = QAction(self)
        self._act_about.triggered.connect(
            lambda: show_about(self, self._language)
        )
        self._menu_help.addAction(self._act_about)

    def _enter_main(self):
        self._language = (self.profile or {}).get("language", "zh-CN")
        self._stack.setCurrentWidget(self._main_view)
        self._show_module()
        self._retranslate()
        self._refresh_stats()

    def _show_welcome(self):
        self.setWindowTitle(t("app_title", self._language))
        self._welcome.prepare(self._language)
        self._stack.setCurrentWidget(self._welcome)
        self._rail.set_active(None)

    def _on_welcome_started(self, username, language):
        self.profile = create_profile(username, language)
        self._language = language
        self._theme = self.profile.get("theme", LIGHT)
        self._piece_set = self.profile.get("piece_set", DEFAULT_PIECE_SET)
        self._board_theme = self.profile.get(
            "board_theme", DEFAULT_BOARD_THEME
        )
        self._act_light.setChecked(self._theme == LIGHT)
        self._act_dark.setChecked(self._theme == DARK)
        self._piece_actions[self._piece_set].setChecked(True)
        self._board_actions[self._board_theme].setChecked(True)
        self._apply_theme()
        self._apply_board_preferences()
        self._enter_main()

    def _retranslate(self):
        self.setWindowTitle(t("app_title", self._language))
        self._menu_settings.setTitle(t("menu_settings", self._language))
        self._menu_appearance.setTitle(t("menu_appearance", self._language))
        self._act_light.setText(t("theme_light", self._language))
        self._act_dark.setText(t("theme_dark", self._language))
        self._menu_help.setTitle(t("menu_help", self._language))
        self._act_api_settings.setText(t("action_api_settings", self._language))
        self._act_language.setText(t("action_change_language", self._language))
        self._act_delete.setText(t("action_delete_data", self._language))
        self._act_about.setText(t("action_about", self._language))

        self._menu_personalization.setTitle(
            t("menu_personalization", self._language)
        )
        self._menu_pieces.setTitle(t("menu_pieces", self._language))
        self._menu_board.setTitle(t("menu_board", self._language))
        for name, action in self._board_actions.items():
            action.setText(
                t("board_theme_" + name, self._language)
            )

        self.tabs.setTabText(0, t("tab_analysis", self._language))
        self.tabs.setTabText(1, t("tab_chat", self._language))
        self.tabs.setTabText(2, t("tab_stats", self._language))

        self._welcome.retranslate(self._language)
        self._rail.retranslate(self._language)
        self.board.retranslate(self._language)
        self.analysis_page.retranslate(self._language)
        self.play_page.retranslate(self._language)
        self.puzzle_page.retranslate(self._language)
        self.chat_page.retranslate(self._language)
        self.stats_page.retranslate(self._language)
        self._refresh_stats()

    def _refresh_stats(self):
        self.stats_page.refresh(self.profile)

    def _on_moves_shown(self, pgn):
        if not self.board._moves:
            self.board.load_pgn(pgn)

    def _start_analysis(self, pgn):
        if self._analysis_worker and self._analysis_worker.isRunning():
            return
        ok, err = self.board.load_pgn(pgn)
        if not ok:
            self.analysis_page.set_status(
                t("parse_failed", self._language, error=err)
            )
            return

        self._current_pgn = pgn
        self._results = []
        self.board.set_results([])
        self.analysis_page.show_moves(pgn)
        self.analysis_page.set_accuracy(None)
        self.analysis_page.set_progress(0)
        self.analysis_page.set_status(t("status_parsing", self._language))
        self.analysis_page.set_busy(True)
        self.tabs.setCurrentWidget(self.analysis_page)

        self._analysis_worker = AnalysisWorker(pgn, self._language, self)
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
        percent = int(index / total * 100)
        self.analysis_page.set_progress(percent)
        self.analysis_page.set_status(
            t("status_analyzing", self._language, percent=percent)
        )
        self.board.goto(index)

    def _on_analysis_done(self, results, accuracy):
        self._results = results
        self.board.set_results(results)
        self.analysis_page.set_progress(100)
        self.analysis_page.set_accuracy(accuracy)
        self.analysis_page.set_status(t("analysis_done", self._language))
        self.tabs.setCurrentWidget(self.analysis_page)

        if self.profile:
            self.profile = update_profile(
                self.profile, accuracy, self._current_pgn
            )
            self._refresh_stats()

        self._messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    棋谱=self._current_pgn, 数据=compact_analysis(results)
                ),
            },
        ]
        self.chat_page.clear_history()
        self.chat_page.append_notice(t("chat_welcome", self._language))

    def _on_analysis_failed(self, error):
        self.analysis_page.set_status(
            t("analysis_failed", self._language, error=error)
        )

    def _on_analysis_finished(self):
        self.analysis_page.set_busy(False)
        worker = self._analysis_worker
        self._analysis_worker = None
        if worker is not None:
            worker.deleteLater()

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
            with open(path, "r", encoding="utf-8", errors="replace") as handle:
                content = handle.read()
        except OSError as exc:
            self.analysis_page.set_status(str(exc))
            return
        self.analysis_page.set_pgn(content)
        if self.board.load_pgn(content)[0]:
            self.analysis_page.show_moves(content)
        self.tabs.setCurrentWidget(self.analysis_page)

    def _on_play_import(self, pgn):
        self.analysis_page.set_pgn(pgn)
        if self.board.load_pgn(pgn)[0]:
            self.analysis_page.show_moves(pgn)
        self._module = "analysis"
        self._show_module()
        self.tabs.setCurrentWidget(self.analysis_page)

    def _send_chat(self, text):
        if not self._messages:
            self.chat_page.append_notice(t("chat_no_analysis", self._language))
            return
        if self._chat_worker and self._chat_worker.isRunning():
            return

        username = self.profile["username"] if self.profile else "You"
        self.chat_page.append_user(username, text)
        self._messages.append({"role": "user", "content": text})
        self.chat_page.begin_assistant()
        self.chat_page.set_busy(True)

        self._chat_worker = ChatWorker(self._messages, self._language, self)
        self._chat_worker.chunk.connect(self.chat_page.append_chunk)
        self._chat_worker.done.connect(self._on_chat_done)
        self._chat_worker.failed.connect(self._on_chat_failed)
        self._chat_worker.finished.connect(self._on_chat_finished)
        self._chat_worker.start()

    def _on_chat_done(self, full_reply):
        self._messages.append({"role": "assistant", "content": full_reply})

    def _on_chat_failed(self, error):
        self.chat_page.show_error(error)

    def _on_chat_finished(self):
        self.chat_page.set_busy(False)
        worker = self._chat_worker
        self._chat_worker = None
        if worker is not None:
            worker.deleteLater()

    def _reset_chat(self):
        self._messages = self._messages[:2]
        self.chat_page.clear_history()
        self.chat_page.append_notice(t("chat_welcome", self._language))

    def _apply_theme(self):
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, self._theme)
        self.chat_page.set_theme(self._theme)
        self.board.set_theme(self._theme)
        self.analysis_page.set_theme(self._theme)
        self.play_page.set_theme(self._theme)
        self.puzzle_page.set_theme(self._theme)

    def _apply_board_preferences(self):
        self.board.set_piece_set(self._piece_set)
        self.board.set_board_theme(self._board_theme)
        self.play_page.set_piece_set(self._piece_set)
        self.play_page.set_board_theme(self._board_theme)
        self.puzzle_page.set_piece_set(self._piece_set)
        self.puzzle_page.set_board_theme(self._board_theme)

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
        self.board.set_piece_set(name)

    def _change_board_theme(self, name):
        self._board_theme = name
        if self.profile:
            self.profile = set_board_theme(self.profile, name)
        self.board.set_board_theme(name)

    def _open_api_settings(self):
        result = api_settings_dialog(
            self, self._language, get_api_config()
        )
        if not result:
            return
        save_api_config(
            result["api_key"], result["base_url"], result["model"]
        )
        QMessageBox.information(
            self,
            t("api_settings_title", self._language),
            t("api_settings_saved", self._language),
        )

    def _change_language(self):
        chosen = choose_language_dialog(self, self._language)
        if not chosen or chosen == self._language:
            return
        self._language = chosen
        if self.profile:
            self.profile = set_language(self.profile, chosen)
        self._retranslate()

    def _delete_profile(self):
        if not confirm_delete_dialog(self, self._language):
            return
        delete_profile()
        self.profile = None
        self._theme = LIGHT
        self._piece_set = DEFAULT_PIECE_SET
        self._board_theme = DEFAULT_BOARD_THEME
        self._act_light.setChecked(True)
        self._piece_actions[DEFAULT_PIECE_SET].setChecked(True)
        self._board_actions[DEFAULT_BOARD_THEME].setChecked(True)
        self._apply_theme()
        self._apply_board_preferences()
        self._messages = []
        self._results = []
        self._current_pgn = ""
        self.board.clear()
        self.analysis_page.clear()
        self.analysis_page.set_accuracy(None)
        self.analysis_page.set_progress(0)
        self.chat_page.clear_history()
        self.play_page.reset()
        self.puzzle_page.reset()
        self._module = "analysis"
        self._refresh_stats()
        self._show_welcome()

    def closeEvent(self, event):
        if not confirm_close_dialog(self, self._language):
            event.ignore()
            return
        if self._analysis_worker and self._analysis_worker.isRunning():
            self._analysis_worker.requestInterruption()
            self._analysis_worker.wait(3000)
        if self._chat_worker and self._chat_worker.isRunning():
            self._chat_worker.terminate()
            self._chat_worker.wait(1000)
        self.play_page.shutdown()
        self.puzzle_page.shutdown()
        super().closeEvent(event)
