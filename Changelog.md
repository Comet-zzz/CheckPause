# v2.2.1 – Bug Fixes & Interface Polish

> **A focused patch: faster engine replies, smoother move review, more reliable PGN and analysis handling, and a cleaner interface.**

---

## 🎯 What's New

### 🐞 Bug fixes
- 修复打开包含多局对局的 PGN 文件时只能看到第一局的问题；现在会先弹出对局选择，再载入指定对局。
- 修复载入新棋谱、清空棋盘或改动线路后，旧分析结果与聊天上下文仍可能串到当前局面的问题；棋盘、着法表与引擎现在共用同一份已解析棋谱。

- Fixed PGN files containing several games only loading the first one; the app now asks which game to open.
- Fixed stale analysis results and chat context leaking into a new or edited line; the board, move list, and engine now share one parsed game.

### ✨ Interface & interaction
- 移除顶部菜单栏，设置、个性化与帮助统一收进侧栏齿轮菜单。
- 支持用鼠标滚轮浏览着法，复盘时前后切换更顺手。

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

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.2.0...v2.2.1

---

# v2.2.0 – Online Puzzles & Interface Polish

> **A new online puzzle experience, a cleaner interface, and continued image-recognition work.**

---

## 🎯 What's New

### 🧩 Online puzzles
- 新增在线谜题功能，带来更完整的训练与对局体验；后续版本会继续完善题目与练习流程。
- 优化了谜题相关的操作与信息展示，常用入口更直接。

- Added online puzzles for a more complete training and play experience; future releases will keep improving the puzzle flow.
- Refined the puzzle-related actions and information so common entry points feel more direct.

### ✨ Interface polish
- 继续优化了界面与布局，梳理了操作层级与信息呈现，整体更清晰顺手。
- 打磨了若干交互与视觉细节，中英文下的表现更一致。

- Continued refining the interface and layout, tidying the action hierarchy and information presentation for a clearer, smoother result.
- Polished a number of interaction and visual details so both languages behave more consistently.

### 🖼️ Image recognition (in progress)
- 识图功能持续优化中，后续版本将继续完善。
- Image recognition improvements are ongoing and will continue in future releases.

## 🛠️ Full Changelog
- feat(puzzle): add the online puzzle experience
- chore(gui): refine the interface and layout
- chore(recognition): continue improving image recognition

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.1.0...v2.2.0

---

# v2.1.0 – Learning Module & UI Polish

> **A new learning module for beginners, a cleaner interface, and continued image-recognition work.**

---

## 🎯 What's New

### 🎓 Learning module & UI
- 新增「学习」模块（从棋子走法到将杀），并优化了整体界面与布局，操作更直接。

- Added a Learn module from piece moves to checkmate, and refined the overall interface and layout for a more direct flow.

### 🖼️ Image recognition
- 图片识别功能持续优化中。

- Image recognition keeps improving.

## 🛠️ Full Changelog
- feat(learn): add an interactive beginner lesson module
- chore(gui): refine the interface and lesson layout
- chore(recognition): continue improving image recognition

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.5...v2.1.0

# v2.0.5 – UI & Interaction Refinements

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

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.4...v2.0.5

# v2.0.4 – Board Fixes & Interface Polish

> **A focused update: fixes for personalization styles not reaching every board, the board shrinking after switching to English, and the evaluation bar crowding the board when maximized, alongside a cleaner, more compact interface layout.**

---

## 🎯 What's New

### 🐞 Board fixes
- 修复个性化中更换棋子 / 棋盘样式只在「面板」模块生效的问题，对弈、谜题模块现在同步生效。
- 修复切换英文界面后棋盘被右侧面板挤压变小的问题，中英文下棋盘尺寸保持一致。
- 修复窗口最大化时评估工具条贴住甚至遮住棋盘第 8 横线的问题，工具条与棋盘之间现在保留固定间距。

- Fixed piece and board style changes in Personalization only applying in the Panel module; Play and Puzzle now follow them too.
- Fixed the board shrinking after switching to English; the board now keeps the same size in both languages.
- Fixed the evaluation toolbar touching or covering the board's 8th rank when the window is maximized; a fixed gap is now kept between the toolbar and the board.

### 🧭 Interface polish
- 优化了分析页、侧栏与「关于」窗口的界面布局逻辑，重新梳理操作层级和信息层级，整体更紧凑。
- 打磨了若干控件与间距细节，中英文下的布局表现更一致。

- Refined the layout logic across the analysis panel, side panel and About window, tidying the action and information hierarchy for a more compact result.
- Polished a number of control and spacing details so the layout behaves more consistently in both languages.

## 🛠️ Full Changelog
- fix(personalization): apply piece and board styles to every board widget
- fix(gui): keep the board size stable when switching languages
- fix(board): reserve space for the evaluation strip above the board
- feat(gui): refine the analysis panel and side-panel layout
- chore(gui): tidy the About window and interface details

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.3...v2.0.4

# v2.0.3 – Play Setup Redesign & Analysis Fixes

> **A focused update: the Play setup panel has been rebuilt with clearer segmented controls and a searchable opening picker, alongside a small undo improvement and text fixes in the analysis panel.**

---

## 🎯 What's New

### ♟️ Play setup redesigned
- 重做对弈设置面板：我方改为「执白 / 执黑」分段选择，起始局面改为「标准 / 开局 / 残局」三种模式，只显示当前模式需要的设置，不再出现两个下拉互相清空。
- 开局选择改为独立选择器：按开放、半开放、封闭、侧翼分组，支持中英文搜索，右侧预览末局面与完整走法，替换掉原来 53 条的超长下拉列表。
- 残局下拉只在残局模式出现；切换模式时会记住上次选择。

- Rebuilt the Play setup panel: side is now a White / Black segmented control, and the starting position is a Standard / Opening / Endgame switch that only reveals the controls for the current mode instead of two dropdowns clearing each other.
- Openings now use a dedicated picker grouped by opening family, searchable in Chinese or English, with a board preview and the full move line, replacing the 53-item dropdown.
- The endgame dropdown only appears in Endgame mode, and switching modes remembers the previous choice.

### 🧰 Analysis panel fixes
- 分析面板棋盘新增撤销键：删除棋谱最后一步；对弈和谜题面板不显示。
- 修复分析操作栏「图片识别」「开始分析」按钮文字被截断。

- The analysis board gains an undo button that removes the last move of the line; it stays hidden on the Play and Puzzle boards.
- Fixed the clipped labels on the analysis action bar's Image recognition and Analyze buttons.

## 🛠️ Full Changelog
- feat(play): rebuild the setup panel with segmented side and start-position controls
- feat(play): add a searchable opening picker with family grouping and a board preview
- feat(analysis): add an undo button to the analysis board
- fix(analysis): keep action button labels from clipping
- chore(version): bump the app version to 2.0.3

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.2...v2.0.3

# v2.0.2 – Interface Polish & Image Recognition

> **A detail-focused update: the interface logic has been further refined for smoother everyday use, alongside the ongoing image recognition improvements.**

---

## 🎯 What's New

### 🧭 Interface logic refined
- 继续优化了界面逻辑，梳理了面板模块的布局与信息层级，常用操作更符合直觉。
- 打磨了若干交互细节，切换与反馈更一致、更顺畅。

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

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.1...v2.0.2

# v2.0.1 – Interface Polish & Image Recognition

> **A detail-focused update: the interface logic has been further refined for smoother everyday use, alongside the introduction of image recognition, still being improved.**

---

## 🎯 What's New

### 🧭 Interface logic refined
- 继续优化了界面逻辑，梳理了部分页面的布局与信息层级，常用操作更符合直觉。
- 打磨了若干交互细节，切换与反馈更一致、更顺畅。

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

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v2.0.0...v2.0.1

# v2.0.0 – Interface Overhaul & Smoother Flows

> **A full interface overhaul: colour, icons and the layout hierarchy across every screen have been reworked for a more consistent, comfortable look and smoother everyday use, alongside updated security and privacy terms.**

---

## 🎯 What's New

### 🎨 Refreshed look and feel
- 重新设计并统一了全局配色与视觉样式，浅色与深色主题一并调整，各页面观感更一致。
- 重绘图标体系，按钮、侧栏与状态提示风格统一，信息一眼可辨。
- 打磨了卡片、留白与排版细节，界面更整洁。

- Redesigned and unified the global colour scheme and visual style, reworking the light and dark themes together so every screen looks consistent.
- Redrew the icon set so buttons, the side rail and status hints share one language and read at a glance.
- Polished cards, spacing and typography for a cleaner surface.

### 🧭 Smoother use of the app
- 重新梳理了主要页面的布局与信息层级，常用操作的位置更符合直觉。
- 面板、对弈、题库与统计之间的切换和状态保持一致，交互反馈更明确。
- 打磨了若干细节交互，减少多余步骤。

- Reworked the layout and information hierarchy of the main pages so common actions sit where they are expected.
- Kept the switching and state between Panel, Play, Puzzles and Statistics consistent, with clearer feedback.
- Polished a number of small interactions to cut out unnecessary steps.

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
- chore(version): bump the app version to 2.0.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

# v1.0.0 - Graphical Interface, Move List, Personalization, and Performance

> The first stable series of CheckPause. It grows from a command-line tool into a distributable, bilingual desktop app: a PyQt6 interface, light/dark themes, SMS-style AI chat, a clickable move list, a Lichess-style custom board with personalization, board flipping and performance ratings, an opening book, a configurable OpenAI-compatible API, and one-command Windows packaging.

---

## 🎯 What's New

### 🖥️ PyQt6 graphical interface
- 新增 `run_gui.py` 入口，代码整理为 `checkpause/` 包；命令行界面保留在 `cli/`。
- 左侧棋盘，「导入 / 分析 / 统计」三个标签页；顶栏菜单与标签页使用同一套按钮样式。
- 支持从文件打开 PGN、分析进度条与结果展示；导入页可直接粘贴 PGN，不再显示多余的「PGN 棋谱」标题。

- Added the `run_gui.py` entry and reorganised the code into the `checkpause` package; the CLI stays available under `cli/`.
- Board on the left, with Import / Analysis / Statistics tabs; the menu bar shares the same button styling as the tabs.
- Open PGN files, watch an analysis progress bar, and review results; paste a PGN straight into the Import tab without the redundant "PGN game" heading.

### 🧵 Background workers
- `StockfishAnalyzer` 改为可复用类，支持进度、逐步和停止回调。
- 新增 `AnalysisWorker` 与 `ChatWorker`（`QThread`），所有 UI 更新通过信号回传，分析可随时停止。

- `StockfishAnalyzer` is now a reusable class with progress, per-move, and stop callbacks.
- Added `AnalysisWorker` and `ChatWorker` (`QThread`); all UI updates go through signals and analysis can be stopped at any time.

### 🧱 Project structure
- 根目录的平铺模块整理为包结构：`checkpause/`（`core/` 引擎与 AI、`data/` 档案与设置、`i18n/` 文案、`gui/` 界面），命令行界面独立为 `cli/`。
- `config.py` 只保留常量与提示词；资源路径解析移到 `checkpause/resources.py`，棋子集与棋盘主题集中在 `checkpause/assets.py`。
- 引擎不再负责打印进度，终端进度条移入 `cli/engine_cli.py`；`userdata / settings / profile` 合并到 `checkpause/data/`。
- 中英文文案拆分为 `i18n/zh_CN.py` 与 `i18n/en_US.py`；聊天气泡配色集中到 `gui/theme.py`。
- 新增 `tests/`，用 `unittest` 覆盖表现评级、文案键一致性、档案读写与压缩分析。

- Flat root modules became a package: `checkpause/` (`core/` engine and AI, `data/` profile and settings, `i18n/` strings, `gui/` interface), with the CLI split into `cli/`.
- `config.py` now holds only constants and prompts; resource lookup moved to `checkpause/resources.py`, and piece sets and board themes live in `checkpause/assets.py`.
- The engine no longer prints progress; the CLI progress bar moved to `cli/engine_cli.py`, and `userdata / settings / profile` merged into `checkpause/data/`.
- Locale dictionaries split into `i18n/zh_CN.py` and `i18n/en_US.py`; chat bubble colors now live in `gui/theme.py`.
- Added `tests/`, using `unittest` to cover performance ratings, message-key parity, profile storage, and compact analysis.

### 💬 SMS-style AI chat
- AI 回复显示在左侧气泡，用户消息显示在右侧气泡，圆角、自动换行。
- 气泡配色随明暗主题切换，并带流式输出与思考计时。

- AI replies appear in left bubbles; user messages appear on the right, rounded and word-wrapped.
- Bubbles follow the light/dark theme and stream replies with a thinking timer.

### 📋 Clickable move list
- 导入或开始分析 PGN 后，右侧显示「回合号 / 白方 / 黑方」着法列表，替代纯文本。
- 点击任意着法，棋盘立即跳到该局面，并高亮当前步；分析过程中高亮随进度移动。
- 「查看棋步 / 编辑 PGN」按钮可在列表与原文之间切换。

- After importing or analyzing a PGN, the right side shows a move list (# / White / Black) instead of raw text.
- Clicking a move jumps the board to that position and highlights the current ply; the highlight follows analysis progress.
- A View moves / Edit PGN button toggles between the list and the raw text.

### ♟️ Board, controls, and personalization
- 棋盘改为 `QPainter` 自绘，不再使用 `chess.svg` 的默认样式。
- 采用 Lichess 开源棋子集，坐标、上一步高亮、被将军高亮和引擎箭头全部自绘，并跟随明暗主题。
- 新增「个性化」菜单（位于「设置」与「帮助」之间）：
  - **棋子**：cburnett、merida、chessnut、fantasy、spatial、celtic、kiwen-suwi、rhosgfx、totoy、mpchess（共 10 套）。
  - **棋盘**：绿色、棕色、蓝色、灰色、紫色、珊瑚（共 6 种配色）。
- 外观选择立即生效，并保存到 `profile.json`，下次启动自动恢复。

- The board is drawn with `QPainter` instead of the default `chess.svg` styling.
- Lichess open-source piece sets are used; coordinates, last-move highlight, check highlight, and the engine arrow are all drawn by us and follow the active theme.
- Added a Personalization menu between Settings and Help:
  - **Pieces**: cburnett, merida, chessnut, fantasy, spatial, celtic, kiwen-suwi, rhosgfx, totoy, mpchess (10 sets).
  - **Board**: Green, Brown, Blue, Gray, Purple, Coral (6 themes).
- Choices apply immediately, are saved to `profile.json`, and are restored on the next launch.

### 📊 Performance ratings
- 准确度改为五档"表现"评级：
  - 卓越 / Optimal：85% – 100%
  - 精准 / Precise：75% – 84%
  - 稳健 / Competent：65% – 74%
  - 平均 / Steady：50% – 64%
  - 欠考虑 / Volatile：0% – 49%
- 分析页显示本局表现；统计页保留"平均准确度 / 最近准确度"数值。
- 统计数据表新增居中的"表现"列（附百分比）。

- Accuracy is shown as five performance tiers:
  - Optimal: 85% – 100%; Precise: 75% – 84%; Competent: 65% – 74%; Steady: 50% – 64%; Volatile: 0% – 49%.
- The Analysis tab shows the game's performance; the Statistics tab keeps the average/latest accuracy numbers.
- The stats table gains a centered Performance column (with the percentage).

### 📖 Opening book
- 使用 Polyglot 格式开局库，通过 `chess.polyglot` 读取，无需额外依赖。
- 命中谱着时按满分计算并跳过该步引擎分析，仅在前 15 个回合（30 个半回合）内启用。
- 谱库源文件为 `assets/openings.pgn`（53 条常见开局线路），由 `tools/build_openings.py` 编译为 `assets/opening_book.bin`。

- Uses a Polyglot opening book read via `chess.polyglot`, with no extra dependency.
- Book moves score full marks and skip engine analysis for that move, limited to the first 15 moves (30 plies).
- The source is `assets/openings.pgn` (53 common opening lines), compiled into `assets/opening_book.bin` by `tools/build_openings.py`.

### 🔌 Configurable API
- 「设置 > API 设置...」可配置 **API Key**、**接口地址（Base URL）** 和 **模型名称**。
- 适用于 DeepSeek、OpenAI、OpenRouter、中转服务以及本地 Ollama / vLLM / LM Studio 等兼容接口。
- 默认仍为 DeepSeek（`https://api.deepseek.com` + `deepseek-flash`），未填写的地址或模型自动使用默认值。
- 未配置 API 时程序照常打开，仅 AI 对话提示去设置。

- Settings > API settings... configures the **API key**, **base URL**, and **model name**.
- Works with DeepSeek, OpenAI, OpenRouter, proxy services, and local OpenAI-compatible servers such as Ollama, vLLM, or LM Studio.
- Defaults remain DeepSeek (`https://api.deepseek.com` + `deepseek-flash`); empty fields fall back to the defaults.
- The app opens normally without a configured API; only AI chat prompts you to set one.

### 📦 Packaging and user data
- 配置改为懒加载：缺少 API Key 或 Stockfish 时不再启动即崩溃。
- 用户数据迁移到 `%APPDATA%\CheckPause\`（`profile.json` 与 `settings.json`），旧档案自动迁移。
- 新增 `CheckPause.spec`、`build_exe.ps1` 与 `requirements-build.txt`，用 PyInstaller 打包为 `dist\CheckPause\CheckPause.exe`。
- Stockfish、开局谱库和棋子资源随 exe 一起分发。

- Configuration is lazy-loaded: a missing API key or Stockfish no longer crashes on startup.
- User data moved to `%APPDATA%\CheckPause\` (`profile.json` and `settings.json`); existing profiles migrate automatically.
- Added `CheckPause.spec`, `build_exe.ps1`, and `requirements-build.txt` to build `dist\CheckPause\CheckPause.exe` with PyInstaller.
- Stockfish, the opening book, and piece assets ship with the exe.

### 🎨 Themes and localization
- 「设置 > 外观」可在浅色/深色模式间切换，默认浅色，偏好持久化。
- GUI 与 CLI 共用 `checkpause/i18n/`，界面支持中英文切换。

- Settings > Appearance switches between light and dark mode; light is the default and the choice is persisted.
- GUI and CLI share `checkpause/i18n/`, supporting Chinese and English.

---

## 🛠️ Full Changelog
- feat(gui): add the PyQt6 main window with board, chat, and stats
- feat(gui): run Stockfish analysis and AI chat in background threads
- feat(gui): open PGN files with analysis progress
- feat(gui): add light/dark themes with persistence
- feat(gui): render chat as theme-aware left/right bubbles
- feat(gui): draw the board with QPainter, Lichess pieces, highlights, and arrows
- feat(gui): make board navigation icon-only and add a flip-board control
- feat(gui): add a Personalization menu with 10 piece sets and 6 board themes
- feat(gui): add a clickable move list with current-ply highlighting and an editor toggle
- feat(gui): map accuracy to five performance ratings on the analysis and stats views
- feat(engine): expose `StockfishAnalyzer` with progress/move/stop callbacks
- feat(engine): treat opening book moves as full marks and skip engine analysis
- feat(engine): report book moves in the compact analysis sent to the AI
- feat(api): configure an OpenAI-compatible base URL, key, and model
- feat(settings): store API config under the user data directory
- feat(config): lazy-load the API key and Stockfish with frozen-app path support
- feat(tools): add a PGN-to-Polyglot opening book builder
- feat(packaging): add a PyInstaller spec and build script bundling Stockfish, book, and pieces
- feat(profile): persist language, theme, `piece_set`, and `board_theme`
- refactor(profile): absolute paths, `delete_profile()`, and legacy profile migration
- refactor(ai): build the client per request and report errors provider-neutrally
- refactor(app): move core code into the `checkpause` package and the CLI into `cli/`
- refactor(config): split constants, resource lookup, assets, and user data storage
- refactor(engine): move the CLI progress wrapper into `cli/engine_cli.py`
- refactor(i18n): split locale dictionaries and centralise chat colors in the theme module
- test: add unittest coverage for ratings, i18n keys, profile storage, and compact analysis
- chore(gui): rename tabs to Import / Analysis / Statistics and style the menu bar like tabs
- build: point `CheckPause.spec` at `run_gui.py`
- chore(gui): reduce the default window size without changing proportions
- chore(assets): bundle 10 Lichess piece sets
- fix(engine): keep the CLI wrapper behavior unchanged
- docs(about): add author, copyright, and piece-set attributions

---

## ⚠️ Breaking Changes

- 用户数据位置从程序目录改为 `%APPDATA%\CheckPause\`，旧数据会自动迁移。
- 评分口径变化：开局谱着现在恒为满分，分析更快。
- API 设置从「仅 key」扩展为「key + 地址 + 模型」；旧的 `api_key` 配置继续有效。
- 新增依赖 `PyQt6`，请重新执行 `pip install -r requirements.txt`。
- 入口脚本由 `gui_main.py` 改为 `run_gui.py`；命令行入口为 `run_cli.py`（或 `python -m cli.main`），模块路径统一为 `checkpause.*`。
- 历史记录仍按数值准确度存储，统计页顶部保留准确度数值，表格改为居中的"表现"列。
- 分发时请提供整个 `dist\CheckPause` 文件夹；每位用户需填写自己的 API Key。
- 棋子集遵循各自许可（GPLv2+、Apache-2.0、MIT、CC BY、CC0），分发时请保留署名。

- User data now lives in `%APPDATA%\CheckPause\`; existing data is migrated automatically.
- Scoring change: opening book moves now always count as full marks and analysis is faster.
- API settings grew from key-only to key + base URL + model; existing `api_key` values keep working.
- Added the `PyQt6` dependency; run `pip install -r requirements.txt` again.
- The GUI entry is now `run_gui.py`; start the CLI with `run_cli.py` (or `python -m cli.main`), and all module paths are now `checkpause.*`.
- History is still stored as numeric accuracy; the stats summary keeps accuracy numbers and the table shows a centered Performance column.
- Ship the whole `dist\CheckPause` folder; each user must provide their own API key.
- Piece sets keep their own licenses (GPLv2+, Apache-2.0, MIT, CC BY, CC0); keep the attributions when redistributing.

# v0.3.1 - Bilingual CLI and Persistent Language Preferences

> This release adds bilingual CLI support. Users can choose their interface language on first launch and switch languages at any time.

---

## 🎯 What's New
### 🌐 Bilingual CLI
- 首次启动时选择中文或 English。
- PGN 输入提示、统计信息、Thinking 计时器、Stockfish 状态和错误提示会统一使用所选语言。
- AI 回复逻辑保持不变，模型仍会根据用户提问的语言回答。

- Choose Chinese or English on first launch.
- PGN prompts, statistics, the thinking timer, Stockfish status, and error messages follow the selected language.
- AI response behavior is unchanged and still follows the language of the user's question.

### 💾 Persistent language preference
- 语言偏好会保存到 `profile.json`。
- 旧版档案没有语言字段时，默认使用中文，不影响现有用户。
- 输入 `/language` 或 `/lang` 可以随时切换语言。

- The language preference is stored in `profile.json`.
- Existing profiles without a language field default to Chinese.
- Use `/language` or `/lang` to switch languages at any time.

### 🧩 Centralized localization
- 新增 `i18n.py`，集中管理 CLI 文案。
- 错误处理、Stockfish 分析和用户交互都接入统一的语言系统。

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

- 无破坏性变更。
- 旧版 `profile.json` 可以继续使用，未设置语言时默认使用中文。

- No breaking changes.
- Existing `profile.json` files remain compatible and default to Chinese when no language is configured.

# v0.3.0 - Reliable AI, Easier Setup, Cleaner Architecture

> This release focuses on **reliability**, **easier setup**, and a **cleaner architecture**. CP now uses the latest available DeepSeek Flash model and handles API, network, and Stockfish configuration issues more gracefully.

---

## 🎯 What's New
### 🤖 Updated DeepSeek model
- 将模型配置更新为 API 当前支持的 `deepseek-flash`。
- 该模型对应最新的 DeepSeek Flash 服务版本，避免使用无效的模型 ID。

- Updated the model configuration to the currently supported `deepseek-flash`.
- This avoids invalid model ID errors when calling the DeepSeek API.

### 🛡️ Reliable AI request handling
- 为 DeepSeek 请求增加 **60 秒超时**。
- 关闭无上限的自动重试，避免程序长时间无响应。
- 新增网络错误、超时、API 密钥错误、请求过频和服务端错误提示。
- AI 请求失败后不会直接崩溃，可以继续提问。

- Added a **60-second timeout** for DeepSeek requests.
- Disabled unlimited automatic retries to prevent long hangs.
- Added clear messages for network, timeout, authentication, rate-limit, and server errors.
- Failed requests no longer terminate the chat session.

### ♟️ Easier Stockfish setup
- 下载并配置了官方 Stockfish 19 Windows 版本。
- `.env` 中现在可以直接使用 Stockfish 可执行文件的完整路径。
- `config.py` 增加本地 Stockfish 路径检查，并在配置缺失时给出明确提示。

- Added the official Stockfish 19 Windows build to the project setup.
- `.env` can now point directly to the Stockfish executable.
- Added local path validation and clearer configuration errors.

### 🧩 Modular CLI architecture
- 保留 `main.py` 作为程序入口。
- 新增 `input_handler.py`，负责 PGN 输入和用户数据清除命令。
- 新增 `chat_ui.py`，负责 AI 对话、实时计时器和聊天命令。
- 减少 `main.py` 中的重复逻辑，让后续维护更简单。

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

- 无需修改现有 `profile.json`。
- 需要确保 PyCharm 使用项目虚拟环境：
  `D:\PycharmProjects\CheckPause-Alpha\.venv\Scripts\python.exe`
- `.env` 中的 `DEEPSEEK_API_KEY` 仍然必须有效。

- Existing `profile.json` files remain compatible.
- PyCharm should use the project virtual environment:
  `D:\PycharmProjects\CheckPause-Alpha\.venv\Scripts\python.exe`
- A valid `DEEPSEEK_API_KEY` is still required in `.env`.

# v0.2.1 - Smarter CLI, Leaner Prompt, Real-time Timer

> This release focuses on **interaction experience** and **token efficiency**. CP now shows a live timer while thinking, and significantly compresses the game data sent to DeepSeek – saving you time and money.

---

## 🎯 What's New
### ⏱️ Real‑time thinking timer 
- 在等待 DeepSeek 回复时，控制台会显示动态计时：`💭 Thinking... (2.3s)`
- 一旦开始收到回复，计时器自动停止并显示首包耗时，让你知道 AI 正在工作，不再干等。

- A live timer appears while waiting for DeepSeek: `💭 Thinking... (2.3s)`
- The timer stops automatically once the first response chunk arrives, showing you the initial latency – no more staring at a blank screen.

### 🧹 Leaner prompt
- 新增 `compact_analysis()` 函数，将冗长的棋谱分析数据压缩为紧凑文本：
  - 旧格式：`{turn_color: 'Turn 1 White', move: 'e4', engine_score: 20, best_move: 'e5'}`
  - 新格式：`e4(score:20, best:e5); Nf3(score:15)` 
- **Token 消耗减少约 60%**，同时保留完整信息，AI 依然能准确回答问题。

- Added `compact_analysis()` to compress long analysis data into a compact string:
  - Old: `{turn_color: 'Turn 1 White', move: 'e4', engine_score: 20, best_move: 'e5'}`
  - New: `e4(score:20, best:e5); Nf3(score:15)`
- **Reduces token usage by ~60%** while keeping all essential info – the AI remains just as accurate.

### 📊 Smarter stats display
- 启动时显示 **最后对局日期** 和 **平均准确度**，一目了然。
- 更新档案后，自动计算平均准确度的变化趋势并显示箭头（`↑+1.2%` / `↓0.8%` / `持平`）。

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

- 无。本次更新完全向后兼容，旧档案文件 (`profile.json`) 可直接使用。

- None. This release is fully backward‑compatible – existing `profile.json` files work as is.

# v0.2.0 - CPL-based Accuracy & Deeper Analysis

> This release marks the first major leap in analysis quality for CheckPause (CP). Instead of just checking "right or wrong", it now measures "how far from perfect".

---

## 🔥 What's New

### 📊 CPL-Based Accuracy Scoring
- 准确度不再依赖“是否与引擎首选走法完全一致”的二元判断。
- 改用 **CPL（Centipawn Loss / 厘兵损失）** 衡量每一步的质量，将差距映射为 0～1 的连续得分。
- 准确度现在更接近 Chess.com / Lichess 的风格，能真实反映棋力水平。

- Accuracy is no longer a binary "match or not" judgment.
- Now uses **CPL (Centipawn Loss)** to evaluate every move, mapping the gap to a continuous 0–1 score.
- Accuracy is now closer to Chess.com / Lichess style, reflecting real skill levels.

### ⚙️ Deeper Engine Analysis
- 引擎限制从固定的 `0.5秒` 升级为 **`depth=18, time=2.0s`** 组合限制。
- 分析深度大幅提升，能捕捉更多深层战术和精确走法。

- Engine limit upgraded from fixed `0.5s` to a combined **`depth=18, time=2.0s`** limit.
- Analysis depth is significantly improved, capturing more tactical nuances and precise moves.

### 🧹 Profile Cleanup
- 移除 `Current main issue` 功能——该功能生成的建议过于笼统，实用性有限。
- 用户档案现在更干净，只保留准确度、总局数和历史记录。

- Removed the `Current main issue` feature – the suggestions were too generic and had limited practical value.
- Player profile is now cleaner, keeping only accuracy, total games, and history.

### 🧭 CLI Improvements
- 在粘贴棋谱阶段，输入 `clear` 或 `/reset` 即可清除所有用户数据并退出，无需等分析完成。

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

- 由于新算法每步需分析两次，分析时间大约是旧版的 **2 倍**。但换取的是更准确、更有意义的评分。
- 用户档案结构已更改，建议清除旧档案（输入 `clear` 即可）以重新开始。

- Due to two analyses per move, analysis time is roughly **2x** the previous version. This is traded for more accurate and meaningful scoring.
- Profile structure has changed. It is recommended to clear your old profile (type `clear`) and start fresh.
---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v0.1.0...v0.2.0

# v0.1.0
