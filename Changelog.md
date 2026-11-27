# v2.2.1 – Bug Fixes & Interface Polish

> **A focused patch: faster engine replies, smoother move review, more reliable PGN and analysis handling, and a cleaner interface.**

---

## 🎯 What's New

### 🐞 Bug fixes
- 修复打开包含多局对局的 PGN 文件时只能看到第一局的问题。
- 修复载入新棋谱、清空棋盘或改动线路后，旧分析结果与聊天上下文仍可能串联当前局面的问题；棋盘、着法表与引擎现在共用同一份已解析棋谱。

- Fixed PGN files containing several games only loading the first one.
- Fixed stale analysis results and chat context leaking into a new or edited line; the board, move list, and engine now share one parsed game.

### ✨ Interface & interaction
- 移除顶部菜单栏，设置、个性化与帮助统一收进侧栏齿轮菜单。
- 支持用鼠标滚轮浏览着法，复盘时前后切换更自然。

- Removed the top menu bar and moved settings, personalization, and help into the rail's gear menu.
- Added mouse-wheel move browsing for quicker review.

### ⚡ Performance
- 与 AI 对弈时引擎改为常驻进程，不再每一步重新启动 Stockfish；落子响应更快，同一局内复用搜索缓存。

- The AI opponent now keeps one Stockfish process alive instead of restarting it for every move, so replies arrive faster and the search cache is reused within a game.

## 🛠️ Full Changelog
- fix(analysis): choose a game when a PGN contains several
- refactor(analysis): parse each PGN once and clear stale analysis
- feat(ui): browse moves with the mouse wheel
- chore(gui): move the top menus into the rail settings menu
- perf(play): reuse one Stockfish process for AI moves

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.2.0...v2.2.1

---

# v2.2.0 – Online Puzzles

> **A new online puzzle experience, a cleaner interface, and continued image-recognition work.**

---

## 🎯 What's New

### 🧩 Online puzzles
- 新增在线谜题功能，后续版本会继续完善题目与练习流程。
- 优化了谜题相关的操作与信息展示，常用入口更直接。

- Added online puzzles; future releases will keep improving the puzzle flow.
- Refined the puzzle-related actions and information so common entry points feel more direct.


### 🖼️ Image recognition (in progress)
- 识图功能持续优化中，后续版本将继续完善。
- Image recognition improvements are ongoing and will continue in future releases.

## 🛠️ Full Changelog
- feat(puzzle): add the online puzzle experience
- chore(gui): refine the interface and layout
- chore(recognition): continue improving image recognition

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.1.0...v2.2.0

---

# v2.1.0 – Learning Module

> **A new learning module for beginners, a cleaner interface, and continued image-recognition work.**

---

## 🎯 What's New

### 🎓 Learning module 
- 新增「学习」模块（从棋子走法到将杀）。

- Added a Learn module from piece moves to checkmate.

### 🖼️ Image recognition
- 图片识别功能持续优化中。

- Image recognition keeps improving.

## 🛠️ Full Changelog
- feat(learn): add an interactive beginner lesson module
- chore(gui): refine the interface and lesson layout
- chore(recognition): continue improving image recognition

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.5...v2.1.0

---

# v2.0.5 – Interaction Refinements

> **A small quality-of-life update with a more focused interface and smoother interaction logic.**

---

## 🎯 What's New

### 🧭 UI & usage refinements
- 优化了部分页面的界面细节与操作逻辑，让日常使用更清晰、顺手。
- 调整了部分重复提示与视觉元素，减少干扰，让界面更简洁。
- Windows 安装版支持在应用内下载更新并显示进度，确认后自动启动安装并重启软件。

- Refined parts of the interface and interaction flow for a clearer, smoother everyday experience.
- Reduced redundant visual elements and prompts to keep the interface focused.
- Windows users can download updates in-app with progress feedback, then install and restart the app.

## 🛠️ Full Changelog
- chore(gui): refine interface details and interaction logic
- feat(updater): download and install Windows updates in-app

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.4...v2.0.5

---
# v2.0.4 – Board Fixes

> **A focused update: fixes for personalization styles not reaching every board, the board shrinking after switching to English, and the evaluation bar crowding the board when maximized, alongside a cleaner, more compact interface layout.**

---

## 🎯 What's New

### 🐞 Board fixes
- 修复个性化中更换棋子 / 棋盘样式只在「面板」模块生效的问题。
- 修复切换英文界面后棋盘被右侧面板挤压变小的问题，中英文下棋盘尺寸保持一致。
- 修复窗口最大化时评估工具条遮住棋盘第 8 横线的问题，工具条与棋盘之间现在保留固定间距。

- Fixed piece and board style changes in Personalization only applying in the Panel module.
- Fixed the board shrinking after switching to English; the board now keeps the same size in both languages.
- Fixed the evaluation toolbar touching or covering the board's 8th rank when the window is maximized; a fixed gap is now kept between the toolbar and the board.

## 🛠️ Full Changelog
- fix(personalization): apply piece and board styles to every board widget
- fix(gui): keep the board size stable when switching languages
- fix(board): reserve space for the evaluation strip above the board
- feat(gui): refine the analysis panel and side-panel layout
- chore(gui): tidy the About window and interface details

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.3...v2.0.4

---

# v2.0.3 – Play Setup Redesign & Analysis Fixes

> **A focused update: the Play setup panel has been rebuilt with clearer segmented controls and a searchable opening picker, alongside a small undo improvement and text fixes in the analysis panel.**

---

## 🎯 What's New

### ♟️ Play setup redesigned
- 重新设计对弈设置面板。
- 开局选择改为独立选择器：按开放、半开放、封闭、侧翼分组，支持中英文搜索，右侧预览末局面与完整走法。
- 残局下拉只在残局模式出现；切换模式时会记住上次选择。

- Rebuilt the Play setup panel.
- Openings now use a dedicated picker grouped by opening family, searchable in Chinese or English, with a board preview and the full move line.
- The endgame dropdown only appears in Endgame mode, and switching modes remembers the previous choice.

### 🧰 Analysis panel fixes
- 分析面板棋盘新增撤销键。

- The analysis board gains an undo button.

## 🛠️ Full Changelog
- feat(play): rebuild the setup panel with segmented side and start-position controls
- feat(play): add a searchable opening picker with family grouping and a board preview
- feat(analysis): add an undo button to the analysis board
- fix(analysis): keep action button labels from clipping
- chore(version): bump the app version to 2.0.3

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.2...v2.0.3

---

# v2.0.2 – Interface Polish

> **A detail-focused update: the interface logic has been further refined for smoother everyday use, alongside the ongoing image recognition improvements.**

---

## 🎯 What's New

### 🧭 Interface logic refined
- 继续优化了界面逻辑，梳理了面板模块的布局与信息层级，常用操作更符合直觉。
- 完善若干交互细节，切换与反馈更一致、更流畅。

- Continued refining the interface logic, tidying the Panel module's layout and information hierarchy so common actions feel more natural.
- Polished a number of interaction details for more consistent, smoother switching and feedback.

### 🖼️ Image recognition (in progress)
- 识图功能持续优化中，后续版本将继续完善。
- Image recognition improvements are ongoing and will continue in future releases.

## 🛠️ Full Changelog
- feat(gui): refine the interface logic and layout in the Panel module
- chore(gui): polish interaction details
- chore(version): bump the app version to 2.0.2

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.1...v2.0.2

---

# v2.0.1 – Interface Polish & Image Recognition

> **A detail-focused update: the interface logic has been further refined for smoother everyday use, alongside the introduction of image recognition, still being improved.**

---

## 🎯 What's New

### 🧭 Interface logic refined
- 继续优化了界面逻辑，梳理了部分页面的布局与信息层级，常用操作更符合直觉。
- 完善若干交互细节，切换与反馈更一致、更流畅。

- Continued refining the interface logic, tidying the layout and information hierarchy on several screens so common actions feel more natural.
- Polished a number of interaction details for more consistent, smoother switching and feedback.

### 🖼️ Image recognition (in progress)
- 引入了图片识别功能，相关能力仍在持续完善中。
- Introduced image recognition, which is still being improved.

## 🛠️ Full Changelog
- feat(gui): refine the interface logic and layout across screens
- feat(gui): add image recognition
- chore(gui): polish interaction details
- chore(version): bump the app version to 2.0.1

---

## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.0...v2.0.1

---

# v2.0.0 – Interface Overhaul & Smoother Flows

> **A full interface overhaul: colour, icons and the layout hierarchy across every screen have been reworked for a more consistent, comfortable look and smoother everyday use, alongside updated security and privacy terms.**

---

## 🎯 What's New  
### 🎨 Refreshed look and feel
 - 统一了全局配色、图标与视觉样式（含明暗主题），优化了卡片、留白与排版。
 - 重新排列主要页面布局和信息层级，使面板、对弈、题库与统计之间的切换和状态更一致、反馈更清晰。
 - Unified the global colour scheme, icon set and visual style across light and dark themes, and polishes cards, spacing and typography.
 - Reworked the layout and information hierarchy of the main pages so Panel, Play, Puzzles and Statistics switch consistently with clearer feedback.

### 🔐 Security & privacy 
- 更新了安装协议与隐私政策，相关条款更加明确。 
- 加强了数据处理与运行安全方面的工作。  
- Updated the installation agreement and the privacy policy, with clearer terms. 
- Strengthened the handling of data and the security of day-to-day operation.  
## 🛠️ Full Changelog 
- feat(gui): overhaul the colour scheme and visual style across screens 
- feat(gui): redraw the icon set and unify light and dark themes 
- refactor(gui): streamline the layout and information hierarchy on the main pages 
- chore(gui): polish cards, spacing and typography 
- chore(security): update the installation agreement and privacy policy 
- chore(version): bump the app version to 2.0.0  ---  
## ⚠️ Breaking Changes

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.0.0...v2.0.0

---

# v1.0.0 - Graphical Interface, Move List, Personalization, and Performance

> **The first stable series of CheckPause: a distributable, bilingual PyQt6 desktop app with board analysis, AI chat, a clickable move list, personalization, and one-command packaging.**

---

## 🎯 What's New

### 🖥️ Graphical interface
- 新增 PyQt6 桌面界面：导入 / 分析 / 统计、棋盘、着法列表、浅色/深色主题。
- 支持打开或粘贴 PGN，显示分析进度与逐手结果。

- Added a PyQt6 desktop interface: Import / Analysis / Statistics, board, move list, and light/dark themes.
- Open or paste PGNs, with analysis progress and per-move results.

### 💬 AI chat and analysis
- AI 对话改为左右气泡、流式输出和思考计时，分析可随时停止。
- 准确度改为五档表现评级，并显示在分析页和统计页。
- Stockfish 在后台运行，不阻塞界面；开局谱着按满分计算并跳过分析。

- AI chat uses left/right bubbles with streaming replies and a thinking timer; analysis can be stopped at any time.
- Accuracy is shown as five performance tiers on the analysis and statistics views.
- Stockfish runs in the background; book moves score full marks and skip engine analysis.

### ♟️ Board and personalization
- 新增 Polyglot 开局库，前 15 回合的谱着直接命中。
- 外观选择立即生效，并保存到 `profile.json`。

- Added a Polyglot opening book for the first 15 moves.
- Appearance choices apply immediately and persist in `profile.json`.

### 🔌 API and packaging
- API 设置支持 Key、Base URL、模型名，兼容 OpenAI 格式接口和本地服务。
- 提供 PyInstaller 打包脚本，Stockfish、开局库和棋子随程序分发。
- 未配置 API 时程序照常启动，只有 AI 对话会提示去设置。

- API settings cover key, base URL, and model, compatible with OpenAI-style and local endpoints.
- Added a PyInstaller build script; Stockfish, the opening book, and pieces ship with the app.
- The app starts without an API key; only AI chat asks you to configure one.

## 🛠️ Full Changelog
- feat(gui): add the PyQt6 main window with board, chat, and stats
- feat(gui): draw the board with QPainter, Lichess pieces, highlights, and arrows
- feat(gui): add a clickable move list with current-ply highlighting
- feat(gui): add a Personalization menu with piece sets and board themes
- feat(gui): map accuracy to five performance ratings
- feat(engine): treat opening book moves as full marks and skip engine analysis
- feat(api): configure an OpenAI-compatible base URL, key, and model
- feat(packaging): add a PyInstaller spec and build script
- refactor(app): move core code into the `checkpause` package and the CLI into `cli/`

---

## ⚠️ Breaking Changes

- User data moved to `%APPDATA%\CheckPause\`; existing data migrates automatically.
- Added the PyQt6 dependency; the GUI entry is `run_gui.py` and the CLI entry is `run_cli.py`.
- Opening-book moves now score full marks; API settings grew from key-only to key + base URL + model.
- Piece assets keep their original licenses; keep the attributions when redistributing.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v0.3.1...v1.0.0

---


# v0.3.1 - Bilingual CLI and Persistent Language Preferences

> This release adds bilingual CLI support. Users can choose their interface language on first launch and switch languages at any time.

---

## 🎯 What's New
### 🌐 Bilingual CLI
- Choose Chinese or English on first launch.
- PGN prompts, statistics, the thinking timer, Stockfish status, and error messages follow the selected language.
- AI response behavior is unchanged and still follows the language of the user's question.

### 💾 Persistent language preference
- The language preference is stored in `profile.json`.
- Existing profiles without a language field default to Chinese.
- Use `/language` or `/lang` to switch languages at any time.

### 🧩 Centralized localization
- Added `i18n.py` to centralize CLI messages.
- Error handling, Stockfish analysis, and user interaction now use the same localization system.

---

## 🛠️ Full Changelog
- feat(i18n): add Chinese and English CLI messages
- feat(profile): persist the user's preferred CLI language
- feat(cli): add language selection during first launch
- feat(cli): add `/language` and `/lang` commands
- refactor(cli): route prompts and status messages through the localization layer
- fix(ai): display request errors in the selected CLI language
- fix(profile): keep existing profile files backward-compatible

---

## ⚠️ Breaking Changes

- No breaking changes.
- Existing `profile.json` files remain compatible and default to Chinese when no language is configured.

# v0.3.0 - Reliable AI, Easier Setup, Cleaner Architecture

> This release focuses on **reliability**, **easier setup**, and a **cleaner architecture**. CP now uses the latest available DeepSeek Flash model and handles API, network, and Stockfish configuration issues more gracefully.

---

## 🎯 What's New
### 🤖 Updated DeepSeek model
- Updated the model configuration to the currently supported `deepseek-flash`.
- This avoids invalid model ID errors when calling the DeepSeek API.

### 🛡️ Reliable AI request handling
- Added a **60-second timeout** for DeepSeek requests.
- Disabled unlimited automatic retries to prevent long hangs.
- Added clear messages for network, timeout, authentication, rate-limit, and server errors.
- Failed requests no longer terminate the chat session.

### ♟️ Easier Stockfish setup
- Added the official Stockfish 19 Windows build to the project setup.
- `.env` can now point directly to the Stockfish executable.
- Added local path validation and clearer configuration errors.

### 🧩 Modular CLI architecture
- Kept `main.py` as the application entry point.
- Added `input_handler.py` for PGN input and profile commands.
- Added `chat_ui.py` for AI chat, the live timer, and chat commands.
- Reduced duplication and made the CLI easier to maintain.

---

## 🛠️ Full Changelog
- feat(ai): use the supported `deepseek-flash` model
- feat(ai): add timeout and explicit API error handling
- feat(config): validate Stockfish executable configuration
- chore(setup): add official Stockfish 19 Windows executable
- refactor(cli): move PGN input handling into `input_handler.py`
- refactor(cli): move chat interaction into `chat_ui.py`
- fix(cli): ensure the thinking timer stops after request failures
- chore(env): create project-local `.venv` and install dependencies

---

## ⚠️ Breaking Changes

- Existing `profile.json` files remain compatible.
- PyCharm should use the project virtual environment:
  `D:\PycharmProjects\CheckPause-Alpha\.venv\Scripts\python.exe`
- A valid `DEEPSEEK_API_KEY` is still required in `.env`.

# v0.2.1 - Smarter CLI, Leaner Prompt, Real-time Timer

> This release focuses on **interaction experience** and **token efficiency**. CP now shows a live timer while thinking, and significantly compresses the game data sent to DeepSeek – saving you time and money.

---

## 🎯 What's New
### ⏱️ Real‑time thinking timer 
- A live timer appears while waiting for DeepSeek: `💭 Thinking... (2.3s)`
- The timer stops automatically once the first response chunk arrives, showing you the initial latency – no more staring at a blank screen.

### 🧹 Leaner prompt
- Added `compact_analysis()` to compress long analysis data into a compact string:
  - Old: `{turn_color: 'Turn 1 White', move: 'e4', engine_score: 20, best_move: 'e5'}`
  - New: `e4(score:20, best:e5); Nf3(score:15)`
- **Reduces token usage by ~60%** while keeping all essential info – the AI remains just as accurate.

### 📊 Smarter stats display
- Shows **last game date** and **average accuracy** on startup.
- After updating profile, automatically displays trend arrows (`↑+1.2%` / `↓0.8%` / `持平`) for average accuracy.

---

## 🛠️ Full Changelog
- feat(cli): add real‑time timer during DeepSeek inference
- feat(cli): compact analysis data to reduce token usage
- feat(cli): display last game date and average accuracy trend
- refactor(cli): remove redundant latest accuracy display
- perf(cli): improve timer thread cleanup with try‑finally
- docs: update README to reflect new CLI behavior

---

## ⚠️ Breaking Changes


- None. This release is fully backward‑compatible – existing `profile.json` files work as is.

# v0.2.0 - CPL-based Accuracy & Deeper Analysis

> This release marks the first major leap in analysis quality for CheckPause (CP). Instead of just checking "right or wrong", it now measures "how far from perfect".

---

## 🔥 What's New

### 📊 CPL-Based Accuracy Scoring

- Accuracy is no longer a binary "match or not" judgment.
- Now uses **CPL (Centipawn Loss)** to evaluate every move, mapping the gap to a continuous 0–1 score.
- Accuracy is now closer to Chess.com / Lichess style, reflecting real skill levels.

### ⚙️ Deeper Engine Analysis
- Engine limit upgraded from fixed `0.5s` to a combined **`depth=18, time=2.0s`** limit.
- Analysis depth is significantly improved, capturing more tactical nuances and precise moves.

### 🧹 Profile Cleanup
- Removed the `Current main issue` feature – the suggestions were too generic and had limited practical value.
- Player profile is now cleaner, keeping only accuracy, total games, and history.

### 🧭 CLI Improvements

- You can now type `clear` or `/reset` during PGN input to wipe all data and exit – no need to wait for analysis to finish.

---

## 🛠️ Full Changelog 
- refactor(engine): replace binary accuracy with CPL-based scoring
- perf(engine): upgrade analysis limit to depth=18 / time=2.0s
- feat(cli): display username in input prompt
- feat(cli): support `clear` and `/reset` during PGN input
- refactor(profile): remove `latest_issues` and `issues` extraction
- refactor(i18n): migrate all prompts and data fields to English
- docs(readme): update to reflect new accuracy model

---

## ⚠️ Breaking Changes 
- Due to two analyses per move, analysis time is roughly **2x** the previous version. This is traded for more accurate and meaningful scoring.
- Profile structure has changed. It is recommended to clear your old profile (type `clear`) and start fresh.
---


# v0.1.0
