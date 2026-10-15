"""Render the README screenshots from the real application, offscreen.

The script boots the actual ``MainWindow`` on Qt's offscreen platform, loads a
real game and runs a real local Stockfish analysis so every score, arrow and
label in the pictures is genuine, then fills the chat, statistics, play and
puzzle pages with representative content and saves window grabs under
``docs/readme/<language>/``. Every grab keeps the window at its default size
and layout; nothing is resized or rescaled. One animated GIF walks the analysis
board through the decisive phase of the game, and the chat shot replays a
genuine cloud-tier reply captured in ``tools/screenshot_chat.json``.

User data is redirected to a temporary directory (``APPDATA``/``HOME`` are set
before the app resolves its data paths), so the developer's own profile,
settings and puzzle progress are never touched.

    .venv\\Scripts\\python.exe tools\\make_screenshots.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

_TEMP_HOME = tempfile.mkdtemp(prefix="checkpause-screenshots-")
os.environ["APPDATA"] = _TEMP_HOME
if sys.platform != "win32":
    os.environ["HOME"] = _TEMP_HOME

# The offscreen platform ships a bare font database; point it at the system
# fonts so the renders use the same glyphs as the real application.
if sys.platform == "win32":
    _FONT_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    os.environ.setdefault("QT_QPA_FONTDIR", _FONT_DIR)

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import chess
from PIL import Image
from PySide6.QtWidgets import QApplication

from checkpause.config import DEFAULT_ANALYSIS_DEPTH
from checkpause.core.engine import StockfishAnalyzer
from checkpause.core.review import classify
from checkpause.data.profile import create_profile, delete_profile, save_profile
from checkpause.data.puzzles import BUILTIN_ID
from checkpause.data.settings import MODE_LOCAL, set_ai_mode
from checkpause.gui.main_window import MainWindow
from checkpause.i18n import t

# Every grab is saved exactly as the window renders it at the application's own
# default size (1164x726 logical, set in MainWindow): no resize, no rescale, so
# the pictures match what a user sees.
LANGUAGES = ("en-US", "zh-CN")
FOLDERS = {"en-US": "en", "zh-CN": "zh"}
OUTPUT_ROOT = ROOT / "docs" / "readme"

# The hero shot position: after 16...Nxb8, with the mate in one on the board.
HERO_PLY = 32
# Plies shown in the walkthrough GIF, ending on the mate itself.
GIF_PLIES = (2, 12, 20, 26, 30, 32, 33)
GIF_FRAME_MS = 900

# The chat shot is built around a genuine cloud-tier exchange. This file holds
# a real question (about the game below) plus the reply the server's tuned
# prompt produced for it, with the game's moves and the ply to show. The reply
# is replayed verbatim so re-runs cost no credits; re-capture it only when the
# tuned prompt changes.
CHAT_REPLIES = ROOT / "tools" / "screenshot_chat.json"

OPERA_GAME = """[Event "Paris Opera"]
[Site "Paris"]
[Date "1858.??.??"]
[White "Morphy, Paul"]
[Black "Duke of Brunswick / Count Isouard"]
[Result "1-0"]

1. e4 e5 2. Nf3 d6 3. d4 Bg4 4. dxe5 Bxf3 5. Qxf3 dxe5 6. Bc4 Nf6 7. Qb3 Qe7
8. Nc3 c6 9. Bg5 b5 10. Nxb5 cxb5 11. Bxb5+ Nbd7 12. O-O-O Rd8 13. Rxd7 Rxd7
14. Rd1 Qe6 15. Bxd7+ Nxd7 16. Qb8+ Nxb8 17. Rd8# 1-0
"""

STATS_TOTAL_GAMES = 23
STATS_HISTORY = (
    ("2026-09-28 21:14:05", 71.2),
    ("2026-10-01 20:03:11", 74.6),
    ("2026-10-04 19:47:32", 68.4),
    ("2026-10-06 22:31:08", 78.9),
    ("2026-10-09 21:05:44", 76.3),
    ("2026-10-11 18:52:19", 81.7),
    ("2026-10-13 23:10:02", 79.5),
    ("2026-10-15 20:41:57", 83.2),
)


def _pump(milliseconds):
    """Run the event loop briefly so layout, timers and animations settle."""
    app = QApplication.instance()
    deadline = time.monotonic() + milliseconds / 1000.0
    while time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)


def _grab(window, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pixmap = window.grab()
    pixmap.save(str(path), "PNG")
    size = f"{pixmap.width()}x{pixmap.height()}"
    print(f"  saved {path.relative_to(ROOT)} ({size}, {path.stat().st_size // 1024} KB)")


def _folder(language):
    return OUTPUT_ROOT / FOLDERS[language]


def _boot_window(language, with_profile):
    """Create a fresh window; ``with_profile`` skips the welcome screen."""
    delete_profile()
    if with_profile:
        create_profile("player", language)
        # The fresh settings default to the cloud tier, which without an
        # account opens the welcome screen; the shots want the local tier.
        set_ai_mode(MODE_LOCAL)
    window = MainWindow()
    window._update_timer.stop()
    window.show()
    _pump(150)
    return window


def _capture_welcome(language):
    window = _boot_window(language, with_profile=False)
    window._language = language
    window._show_welcome()
    _pump(150)
    _grab(window, _folder(language) / "welcome.png")
    window.hide()
    return window


def _open_game(window, pgn, language):
    """Load the game and run the genuine local analysis over it."""
    window.analysis_page.set_pgn(pgn)
    window.analysis_page.show_moves(pgn)
    window.board.load_pgn(pgn)
    window._current_pgn = pgn

    print("  running Stockfish analysis...")
    results, error, accuracy = StockfishAnalyzer().analyze(pgn, language=language)
    if error is not None:
        raise SystemExit(f"analysis failed: {error}")
    annotated, _ = classify(results, pgn)

    window._results = annotated
    window.board.set_results(annotated)
    window.analysis_page.set_progress(100)
    window.analysis_page.set_accuracy(accuracy)
    window.analysis_page.set_review(annotated)
    window.analysis_page.set_status(t("analysis_done", language))
    window.tabs.setCurrentWidget(window.analysis_page)
    print(f"  game analysed: accuracy {accuracy}%")
    return annotated, accuracy


def _goto_ply(window, records, ply):
    """Show the position after ``ply`` moves with its engine evaluation."""
    window.board.goto(ply, animate=False, sound=False)
    if ply >= len(records):
        return  # the final position keeps the previous evaluation
    record = records[ply]
    lines = []
    for alt in record.get("alts") or []:
        if alt.get("uci"):
            lines.append({"uci": alt["uci"], "margin": alt.get("cp"), "mate": alt.get("mate")})
    window.board.apply_live_eval(lines[:3], DEFAULT_ANALYSIS_DEPTH)
    _pump(450)  # let the evaluation bar animation finish


def _capture_analysis(window, language):
    window.tabs.setCurrentWidget(window.analysis_page)
    _grab(window, _folder(language) / "analysis.png")


def _capture_chat(window, language):
    """Show the recorded cloud exchange on the game and ply it is about."""
    data = json.loads(CHAT_REPLIES.read_text(encoding="utf-8"))
    records, _ = _open_game(window, data["pgn"], language)
    _goto_ply(window, records, data["ply"])

    script = data[language]
    chat = window.chat_page
    chat.clear_history()
    chat.append_notice(t("chat_welcome", language))
    chat.append_user(window.profile["username"], script["question"])
    chat.begin_assistant()
    chat.append_chunk(script["reply"])
    window.tabs.setCurrentWidget(chat)
    _grab(window, _folder(language) / "chat.png")


def _capture_stats(window, language):
    history = [{"date": date, "accuracy": accuracy, "pgn": ""} for date, accuracy in STATS_HISTORY]
    profile = window.profile
    profile["total_games"] = STATS_TOTAL_GAMES
    profile["history"] = history
    profile["latest_accuracy"] = history[-1]["accuracy"]
    save_profile(profile)
    window._refresh_stats()
    window.tabs.setCurrentWidget(window.stats_page)
    _grab(window, _folder(language) / "stats.png")


def _capture_play(window):
    page = window.play_page
    opening_index = page._opening_combo.findText("Italian Game: Giuoco Piano")
    if opening_index > 0:
        page._opening_combo.setCurrentIndex(opening_index)
    time_index = page._time_combo.findData("rapid_10_0")
    if time_index >= 0:
        page._time_combo.setCurrentIndex(time_index)

    page._started = True
    page._session.clock_started = True
    page._session.clock_remaining = {chess.WHITE: 512.0, chess.BLACK: 536.0}
    page._update_panel_state()
    page._sync_clock_timer()
    page._update_clock_labels()

    window._module = "play"
    window._show_module()
    _grab(window, _folder(window._language) / "play.png")
    page._clock_timer.stop()


def _puzzle_index():
    """Pick one built-in puzzle that shows a readable middlegame position."""
    sample = ROOT / "assets" / "puzzles" / "lichess_sample.jsonl"
    fallback = None
    for index, line in enumerate(sample.read_text(encoding="utf-8").splitlines()):
        try:
            puzzle = json.loads(line)
        except ValueError:
            continue
        themes = puzzle.get("themes") or []
        rating = puzzle.get("rating") or 0
        if "middlegame" not in themes or "mateIn2" not in themes:
            continue
        if not 1000 <= rating <= 1400:
            continue
        if len(puzzle.get("moves") or []) < 4:
            continue
        if puzzle.get("id") == "005nD":
            return index
        if fallback is None:
            fallback = index
    return fallback


def _capture_puzzle(window, language):
    page = window.puzzle_page
    page.refresh_collections(select_id=BUILTIN_ID)
    index = _puzzle_index()
    if index is not None:
        page._load_puzzle(index)
    window._module = "puzzle"
    window._show_module()
    _grab(window, _folder(language) / "puzzle.png")


def _save_walkthrough(window, language, records):
    window.tabs.setCurrentWidget(window.analysis_page)
    frames_dir = Path(tempfile.mkdtemp(prefix="checkpause-gif-"))
    try:
        _render_walkthrough(window, language, records, frames_dir)
    finally:
        shutil.rmtree(frames_dir, ignore_errors=True)


def _render_walkthrough(window, language, records, frames_dir):
    frame_paths = []
    for order, ply in enumerate(GIF_PLIES):
        _goto_ply(window, records, ply)
        frame_path = frames_dir / f"frame-{order:02d}.png"
        window.grab().save(str(frame_path), "PNG")
        frame_paths.append(frame_path)

    images = []
    for frame_path in frame_paths:
        with Image.open(frame_path) as source:
            images.append(source.convert("RGB"))
    frames = [image.quantize(colors=128, method=Image.Quantize.MEDIANCUT) for image in images]
    durations = [GIF_FRAME_MS] * (len(frames) - 1) + [GIF_FRAME_MS * 2]

    path = _folder(language) / "walkthrough.gif"
    path.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )
    print(f"  saved {path.relative_to(ROOT)} ({path.stat().st_size // 1024} KB)")


def _capture_language(language):
    print(f"[{language}]")
    window = _boot_window(language, with_profile=True)
    # The screenshots set the evaluation by hand, so the live search is parked.
    window._eval_failed = True
    window._stop_eval_worker()

    records, _ = _open_game(window, OPERA_GAME, language)
    _goto_ply(window, records, HERO_PLY)
    _capture_analysis(window, language)
    _capture_stats(window, language)
    _capture_play(window)
    _capture_puzzle(window, language)

    window._module = "analysis"
    window._show_module()
    _save_walkthrough(window, language, records)
    # Last: the chat shot loads its own game, which replaces what the board
    # pane shows.
    _capture_chat(window, language)

    window.hide()
    return window


def main():
    app = QApplication(sys.argv)
    print(f"temporary data directory: {_TEMP_HOME}")
    windows = [
        _capture_welcome("en-US"),
        _capture_welcome("zh-CN"),
        _capture_language("en-US"),
        _capture_language("zh-CN"),
    ]
    print("done")
    del windows
    app.quit()
    shutil.rmtree(_TEMP_HOME, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
