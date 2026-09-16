# ♟️ CheckPause

A chess analysis tool that combines game-tree search with natural language generation to help players understand their own decision-making biases.

[![downloads](https://img.shields.io/github/downloads/Comet-zzz/CheckPause/total?style=for-the-badge&label=downloads&color=blue)](https://github.com/Comet-zzz/CheckPause/releases/download/v1.5.2/CheckPause_Setup_1.5.2.exe)
[![license](https://img.shields.io/badge/license-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![Chinese](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-brown?style=for-the-badge)](README.zh-CN.md)
[![English](https://img.shields.io/badge/English-blue?style=for-the-badge)](README.md)

CheckPause evaluates every move with a local Stockfish engine, then lets any OpenAI-compatible model explain the engine data in plain language, alongside a clickable move list, a custom-drawn board, performance ratings, and a personal growth profile.

---

## ✨ Features

- **PyQt6 desktop app**: the board on the left, with Import / Analysis / Statistics tabs, in Chinese or English.
- **Local engine analysis**: Stockfish scores every move with progress and stop support; a Polyglot opening book detects book moves and skips engine work.
- **AI explanations**: streamed answers based on engine data, with follow-up questions like a real coach; works with DeepSeek, OpenAI, OpenRouter, and local models.
- **Clickable move list**: jump to any position and highlight the current ply; the board also shows engine best-move arrows and can be flipped.
- **Play against the computer**: the Play module takes on Stockfish with click-to-move, White/Black, a 100–3000 rating slider (1320 and above calibrated by the engine's Elo limiter), common time controls (1+0 through 30+0, with increments or unlimited), selectable openings and endgames, undo, resign, promotion picking, and move review — plus one-click send to analysis. Setup pickers lock once a game is under way and unlock on New game.
- **Puzzle training**: a Puzzles module between Play and Analysis ships with a Lichess sample and accepts your own open collections (Lichess CSV, FEN-based PGN), with correct/wrong feedback, hints, and rating/theme display. A Favorites collection gathers the puzzles you star or miss for later review, and large collections are read lazily.
- **Performance ratings and profile**: five tiers (Optimal / Precise / Competent / Steady / Volatile) plus per-game accuracy history on the Statistics tab.
- **Personalization**: 10 Lichess piece sets, 6 board themes, and light/dark modes, applied instantly and saved.
- **Privacy first**: your games and API keys stay on your machine; analysis never depends on the cloud.

---

## 🚀 Quick Start

### Windows users

1. Get `CheckPause_Setup_1.5.2.exe` from the Download section at the end of this file.
2. Run the installer and follow the prompts — no administrator rights needed, and a desktop shortcut is optional.
3. Launch CheckPause from the desktop or Start Menu; first launch asks for a username and interface language.
4. Open Settings → API settings... and enter an API key (DeepSeek by default; any OpenAI-compatible endpoint works).
5. Paste or open a PGN on the Import tab, click Analyze, then ask questions on the Analysis tab.

> Analysis and board features work without an API key; only AI chat needs one.

### Run from source

Requires Python 3.10+.

```powershell
git clone https://github.com/Comet-zzz/CheckPause.git
cd CheckPause
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_gui.py
```

Running from source requires your own Stockfish build (the release installer bundles one):

- Download the build for your platform from https://stockfishchess.org/download/;
- Put it at `stockfish\stockfish\stockfish-windows-x86-64-universal.exe`, or set `STOCKFISH_PATH` in `.env`.

The API key can be entered in the app, or you can copy `.env.example` to `.env`:

```env
DEEPSEEK_API_KEY = "sk-your-api-key-here"
STOCKFISH_PATH = "C:/your/path/to/stockfish.exe"
```

### CLI

The original CLI flow is still available:

```powershell
python run_cli.py        # or python -m cli.main
```

Paste a PGN, analyze it with Stockfish, and chat with the AI in the terminal (`/language` switches languages, `clear` deletes user data).

---

## ⚙️ Configuration and data

- Settings → API settings... configures the API key, base URL, and model name; defaults to `https://api.deepseek.com` + `deepseek-flash`, and blank fields fall back to those defaults.
- User data lives in `%APPDATA%\CheckPause\`: `profile.json` (username, language, theme, appearance, history) and `settings.json` (API config); legacy profiles migrate automatically.

---

## 🧱 Project structure

```
run_gui.py / run_cli.py        # GUI / CLI entry points
checkpause/
  config.py  resources.py  assets.py
  core/      engine.py  ai.py  rating.py  puzzle.py  play_session.py  openings.py  endgames.py
  data/      paths.py  settings.py  profile.py  puzzles.py
  i18n/      zh_CN.py  en_US.py
  gui/       main_window.py  dialogs.py  theme.py  workers.py
             pages/    analysis_page.py  chat_page.py  stats_page.py  play_page.py  puzzle_page.py  welcome_page.py
             widgets/  move_list.py  module_rail.py  board/widget.py  board/canvas.py  board/promo.py  board/constants.py
cli/         main.py  chat_ui.py  input_handler.py  engine_cli.py
tests/       unittest suite
tools/       build_openings.py  build_puzzles.py
assets/      pieces/  puzzles/  openings.pgn  opening_book.bin
```

The GUI and CLI share the `checkpause` core logic and never depend on each other's UI code.

---

## 🧪 Tests and packaging

```powershell
python -m unittest discover -s tests -v   # unit tests
.\build_exe.ps1                            # portable folder + single-file installer
```

Packaging requires [Inno Setup 6.3+](https://jrsoftware.org/isdl.php): `winget install JRSoftware.InnoSetup`

If PowerShell refuses to run the script, use: `powershell -ExecutionPolicy Bypass -File .\build_exe.ps1`

`CheckPause.spec` bundles Stockfish, the opening book, and piece assets into `dist\CheckPause\`; `installer\CheckPause.iss` then compiles that folder into a single-file installer placed in `dist\`. The version is read from `APP_VERSION` in `checkpause\__init__.py`.

Output:

| Artifact | Purpose |
| --- | --- |
| `dist\CheckPause_Setup_<version>.exe` | **The installer — the file you send to users** |
| `dist\CheckPause\CheckPause.exe` | Portable build (intermediate product of the installer; must be distributed together with the whole folder) |

### Releasing an update

1. Bump `APP_VERSION` in `checkpause/__init__.py` and `version_info.txt`, and add a new section at the top of `Changelog.md`;
2. Run `.\build_exe.ps1` to produce `dist\CheckPause_Setup_<version>.exe`;
3. Create a GitHub Release and upload that installer;
4. **Update `version.json` in the repository root** so `latest` and `url` point at the new version;
5. Update the version number, installer link, and SHA-256 in `README.md` and `README.zh-CN.md` — the downloads badge and the Download section both point straight at the `.exe`, so they must follow the new file.

Clients read `version.json` about 2.5 seconds after launch (jsDelivr first, then raw.githubusercontent) and prompt when a higher version is listed. Step 4 is what actually reaches existing users: without it the new installer exists but nobody is told about it.

---

## 🙏 Credits

- Pieces come from Lichess open-source piece sets (cburnett, merida, chessnut, fantasy, spatial, celtic, kiwen-suwi, rhosgfx, totoy, mpchess), each owned by its author under GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 licenses.
- Engine: [Stockfish](https://stockfishchess.org/) (GPLv3); the opening book is compiled from public opening lines by `tools/build_openings.py`.
- The installer is built with [Inno Setup](https://jrsoftware.org/isinfo.php) and uses its official Simplified Chinese language file (`installer/languages/ChineseSimplified.isl`, maintained by Zhenghan Yang).
- License: CheckPause is released under the [GNU General Public License v3.0](LICENSE), Copyright (C) 2026 CometZZZ. Bundled components keep their own terms — Stockfish is GPLv3 (source available at https://stockfishchess.org/download/), and the piece sets keep the licenses listed above.

---

## ⬇️ Download

**Latest: CheckPause v1.5.2 (Windows x64)**

- 📦 [CheckPause_Setup_1.5.2.exe](https://github.com/Comet-zzz/CheckPause/releases/download/v1.5.2/CheckPause_Setup_1.5.2.exe) (107.6 MB — ships with Stockfish, the opening book, piece assets, and a curated Lichess puzzle set)
- SHA-256: `FDC9A81D0C6B76B359EC1DE330887299674CB0E0D1DFC32D9441E953AAEE3E59`
- Run the installer, then launch CheckPause from the desktop or Start Menu. The build is unsigned; if SmartScreen appears, choose More info → Run anyway.
- All releases: https://github.com/Comet-zzz/CheckPause/releases

---

[Chinese README](README.zh-CN.md)
