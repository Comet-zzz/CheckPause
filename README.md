# ♟️ CheckPause

A chess analysis tool that combines game-tree search with natural language generation to help players understand their own decision-making biases.

[![downloads](https://img.shields.io/github/downloads/Comet-zzz/CheckPause/total?style=for-the-badge&label=downloads&color=blue)](https://github.com/Comet-zzz/CheckPause/releases/download/v1.6.1/CheckPause_Setup_1.6.1.exe)
[![license](https://img.shields.io/badge/license-Proprietary-lightgrey?style=for-the-badge)](LICENSE)
[![Chinese](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-brown?style=for-the-badge)](README.zh-CN.md)
[![English](https://img.shields.io/badge/English-blue?style=for-the-badge)](README.md)

CheckPause evaluates every move with a local Stockfish engine, then lets any OpenAI-compatible model explain the engine data in plain language, alongside a clickable move list, a custom-drawn board, performance ratings, and a personal growth profile.

---

## ✨ Features

- **PySide6 desktop app**: the board on the left, with Import / Analysis / Statistics tabs, in Chinese or English.
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

1. Get `CheckPause_Setup_1.6.1.exe` from the Download section at the end of this file.
2. Run the installer and follow the prompts — no administrator rights needed, and a desktop shortcut is optional.
3. Launch CheckPause from the desktop or Start Menu; first launch asks for a username and interface language.
4. Open Settings → API settings... and enter an API key (DeepSeek by default; any OpenAI-compatible endpoint works).
5. Paste or open a PGN on the Import tab, click Analyze, then ask questions on the Analysis tab.

> Analysis and board features work without an API key; only AI chat needs one.

---

## ⚙️ Configuration and data

- Settings → API settings... configures the API key, base URL, and model name; defaults to `https://api.deepseek.com` + `deepseek-flash`, and blank fields fall back to those defaults.
- User data lives in `%APPDATA%\CheckPause\`: `profile.json` (username, language, theme, appearance, history) and `settings.json` (API config); legacy profiles migrate automatically.

---

## 🙏 Credits

- Pieces come from Lichess open-source piece sets (cburnett, merida, chessnut, fantasy, spatial, celtic, kiwen-suwi, rhosgfx, totoy, mpchess), each owned by its author under GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 licenses.
- Engine: [Stockfish](https://stockfishchess.org/) (GPLv3); the opening book is compiled from public opening lines.
- The installer is built with [Inno Setup](https://jrsoftware.org/isinfo.php) and uses its official Simplified Chinese language file (`installer/languages/ChineseSimplified.isl`, maintained by Zhenghan Yang).
- License: CheckPause is proprietary software — Copyright (C) 2026 CometZZZ, all rights reserved. See [LICENSE](LICENSE). Versions up to and including v1.6.1 remain available under the GPLv3 they were published with. Bundled components keep their own terms: Stockfish is GPLv3 (source available at https://stockfishchess.org/download/), and the piece sets keep the licenses listed above.

---

## ⬇️ Download

**Latest: CheckPause v1.6.1 (Windows x64)**

- 📦 [CheckPause_Setup_1.6.1.exe](https://github.com/Comet-zzz/CheckPause/releases/download/v1.6.1/CheckPause_Setup_1.6.1.exe) (113.8 MB — ships with Stockfish, the opening book, piece assets, and a curated Lichess puzzle set)
- SHA-256: `1A30C9C2E4C4DB2272B2B5BACFA3715401F5757138DF8AF7D143E1A59187674E`
- Run the installer, then launch CheckPause from the desktop or Start Menu. The build is unsigned; if SmartScreen appears, choose More info → Run anyway.
- All releases: https://github.com/Comet-zzz/CheckPause/releases

---

[Chinese README](README.zh-CN.md)
