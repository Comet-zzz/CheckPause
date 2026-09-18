# ♟️ CheckPause

A chess analysis tool that combines game-tree search with natural language generation to help players understand their own decision-making biases.

<a href="#⬇️-download"><img alt="Downloads" src="https://img.shields.io/github/downloads/Comet-zzz/CheckPause/total?style=for-the-badge&label=Download&color=brightgreen"></a><a href="https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.2/CheckPause_Setup_1.7.2.exe"><img alt="Windows x64" src="https://img.shields.io/badge/Windows-x64-0078D4?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTAgMGgxMS40djExLjRIMHptMTIuNiAwSDI0djExLjRIMTIuNnpNMCAxMi42aDExLjRWMjRIMHptMTIuNiAwSDI0VjI0SDEyLjZ6Ii8%2BPC9zdmc%2B"></a><a href="https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.2/CheckPause-1.7.2-macOS-M-series.dmg"><img alt="macOS M-series" src="https://img.shields.io/badge/macOS-M--series-black?style=for-the-badge&logo=apple&logoColor=white"></a><a href="https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.2/CheckPause-1.7.2-macOS-Intel.dmg"><img alt="macOS Intel" src="https://img.shields.io/badge/macOS-Intel-black?style=for-the-badge&logo=apple&logoColor=white"></a>
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

1. Get `CheckPause_Setup_1.7.2.exe` from the Download section at the end of this file.
2. Run the installer and follow the prompts — no administrator rights needed, and a desktop shortcut is optional.
3. Launch CheckPause from the desktop or Start Menu; first launch asks for a username and interface language.
4. Open Settings → API settings... and enter an API key (DeepSeek by default; any OpenAI-compatible endpoint works).
5. Paste or open a PGN on the Import tab, click Analyze, then ask questions on the Analysis tab.

> Analysis and board features work without an API key; only AI chat needs one.

### macOS users

1. Download the `.dmg` for your chip from the [Releases](https://github.com/Comet-zzz/CheckPause/releases) page (`M-series` for Apple Silicon, `Intel` for Intel Macs).
2. Open the `.dmg` and drag CheckPause into Applications.
3. The build is unsigned and not notarized. On first launch, **right-click the icon → Open**, or allow it under System Settings → Privacy & Security → Open Anyway.
4. From there the steps match Windows (set an API key, import a PGN, start analysis).

---

## ⚙️ Configuration and data

- Settings → API settings... configures the API key, base URL, and model name; defaults to `https://api.deepseek.com` + `deepseek-flash`, and blank fields fall back to those defaults.
- User data lives in `%APPDATA%\CheckPause\` on Windows and `~/Library/Application Support/CheckPause/` on macOS: `profile.json` (username, language, theme, appearance, history) and `settings.json` (API config); legacy profiles migrate automatically.

---

## 🙏 Credits

- Pieces come from Lichess open-source piece sets (cburnett, merida, chessnut, fantasy, spatial, celtic, kiwen-suwi, rhosgfx, totoy, mpchess), each owned by its author under GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 licenses.
- Engine: [Stockfish](https://stockfishchess.org/) (GPLv3); the opening book is compiled from public opening lines.
- The installer is built with [Inno Setup](https://jrsoftware.org/isinfo.php) and uses its official Simplified Chinese language file (`installer/languages/ChineseSimplified.isl`, maintained by Zhenghan Yang).
- License: CheckPause is proprietary software — Copyright (C) 2026 CometZZZ, all rights reserved. See [LICENSE](LICENSE). Versions up to and including v1.6.1 remain available under the GPLv3 they were published with. Bundled components keep their own terms: Stockfish is GPLv3 (source available at https://stockfishchess.org/download/), and the piece sets keep the licenses listed above.

---

## ⬇️ Download

**Latest: CheckPause v1.7.2 (Windows x64)**

- 🚀 **Fast mirror (recommended in China)**: [CheckPause_Setup_1.7.2.exe](http://43.108.99.244/download/CheckPause_Setup_1.7.2.exe) — the same file served from a host that is reachable without the usual throttling, usually done in well under a minute
- 📦 [Download from GitHub](https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.2/CheckPause_Setup_1.7.2.exe) (114.5 MB — ships with Stockfish, the opening book, piece assets, and a curated Lichess puzzle set)
- SHA-256: `AC1B731C14C81BE016B2532436EF155DCE67F560BF01A51518FCB25961BB22DF` (both links serve the identical file)
- Run the installer, then launch CheckPause from the desktop or Start Menu. The build is unsigned; if SmartScreen appears, choose More info → Run anyway.

**Latest: CheckPause v1.7.2 (macOS)**

- 🚀 **Fast mirror (recommended in China)**: [M-series](http://43.108.99.244/download/CheckPause-1.7.2-macOS-M-series.dmg) (131.8 MB) · [Intel](http://43.108.99.244/download/CheckPause-1.7.2-macOS-Intel.dmg) (56.6 MB)
- 📦 [Download from GitHub](https://github.com/Comet-zzz/CheckPause/releases/tag/v1.7.2) (both `.dmg` files on the release page)
- SHA-256: arm64 `6AF9E7EE680D5B7DA1069EC81ECEBAB393157683EA79A0F7E7035A55FD25E565`, Intel `E899195198C5F74D916C7D233AB69FB1EC2FF10109ECE6346512F13B60812155`
- Open the `.dmg`, drag CheckPause into Applications, then **right-click the icon → Open** the first time (the build is unsigned and not notarized).
- All releases: https://github.com/Comet-zzz/CheckPause/releases

---

[Chinese README](README.zh-CN.md)
