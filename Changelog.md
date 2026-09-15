# v1.4.1 – Layout Polish

> 本次更新优化了界面布局：对弈、谜题与分析工具下的棋盘与侧栏尺寸保持统一，切换模块时界面不再跳动。
>
> This release polishes the layout: the board and side panel now stay the same size across Play, Puzzles, and Analysis, so switching modules no longer shifts the interface.

---

## 🎯 What's Changed
- 优化了界面布局：统一各模块的棋盘与侧栏尺寸，并微调了模块入口与按钮的对齐。

- Polished the layout: unified the board and side-panel sizes across modules and tidied module and button alignment.

---

## 🛠️ Full Changelog
- fix(gui): keep the board and side panel the same size across modules
- fix(gui): align the module rail buttons consistently
- chore(version): bump the app version to 1.4.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

# v1.4.0 – Puzzle Progress and Quick Jump

> 谜题页焕新：已解开的谜题会被记住，重开自动继续，并可直接跳到任意一题。

> The Puzzle page gets a refresh: solved puzzles are remembered, you resume automatically, and you can jump to any puzzle.

---

## 🎯 What's New

### ✅ Progress memory
- 已解开的谜题会被记录，重新打开自动从下一道未解题开始；顶部始终显示已完成题数。

- Solved puzzles are recorded, reopening resumes at the next unsolved one, and the completed count stays visible at the top.

### 🔀 Jump to any puzzle
- 「上一题 / 下一题」之间新增跳转框：输入题号回车或点「跳转」即可直达，分母固定为题目总数。

- A jump box between Previous and Next: type a number and press Enter or click Go, with the total fixed as the denominator.

### 🧹 Cleaner puzzle panel
- 题目信息改到所选题目集下方显示；未选择题集时隐藏相关控件，面板更清爽。

- Puzzle details now show under the selected collection, and related controls are hidden until a collection is chosen.

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

# v1.3.3 – Pause, Endgames, and a Cleaner Promotion

> 本次更新让对弈更可控：计时对局可以暂停，开局下方新增可自选的常见残局，时钟在你走出第一步前不会开始，升变改用 Lichess 风格的棋盘内联弹窗。
>
> This release makes Play more controllable: timed games can be paused, a set of common endgames joins the pickers, the clock waits for your first move, and promotion now uses an inline, Lichess-style picker.

---

## 🎯 What's New

### ⏸️ Pause a game
- 计时对局的两个时钟之间新增「暂停 / 继续」：暂停时停表并锁定走子，继续后恢复计时；未启用计时时不会显示。

- A Pause / Resume button now sits between the two clocks in timed games: it stops the clock and locks the board, resumes cleanly, and stays hidden when no clock is running.

### ♟️ Endgame practice
- 「开局」下方新增「残局」，内置后对单王、单车对单王、双车对单王、双象对单王、兵升变、王兵对王、后对车、后对兵升变八个常见残局，选中即从该局面开始对弈，并与开局互斥。

- Added an Endgame picker below Opening with eight common positions (queen, rook, two rooks, two bishops, pawn promotion, king and pawn, queen vs rook, queen vs pawn); picking one starts from that position and clears any opening line.

### ⏱️ Clock waits for the first move
- 尚未走子时双方时钟不会开始计时，走出第一手后才开始走表。

- The clock no longer starts before your first move; it begins once a move is played.

### ♟️ Inline promotion
- 升变改为锚定升变格的棋盘内联弹窗，按当前棋子集与棋盘配色显示后、车、象、马，悬停高亮，点击选择，Esc 或点击外部取消。

- Promotion is now an inline popup anchored to the promoting square, showing queen, rook, bishop, and knight in the current piece set and board colors, with hover highlight, click to pick, and Esc or click-away to cancel.

---

## 🛠️ Full Changelog
- feat(play): add a pause/resume control for timed games
- feat(play): add a selectable set of common endgames
- fix(play): keep the clock stopped until the first move
- feat(board): render an inline Lichess-style promotion picker
- fix(board): honour the PGN start FEN for positions and imports
- test: cover the bundled endgame positions
- chore(version): bump the app version to 1.3.3

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

# v1.3.2 – Clocks, Openings, and a Version Label

> 本次更新让「对弈」更接近真实棋局：新增可选的计时模式与开局选择，同时「关于」对话框会显示当前版本号。
>
> This release makes Play feel like a real game: optional time controls and opening selection, plus the current version shown in About.

---

## 🎯 What's New

### ⏱️ Time controls
- 「对弈」新增「计时」选项，内置无限制、1+0、3+0、3+2、5+0、5+3、10+0、10+5、15+10、30+0 等常见模式。
- 棋盘上方显示双方剩余时间，走子后按模式加秒，超时即判负；离开对弈页面时自动暂停。

- Play now offers a Clock option with common modes: Unlimited, 1+0, 3+0, 3+2, 5+0, 5+3, 10+0, 10+5, 15+10, and 30+0.
- Both players' remaining time is shown above the board, increments are added after each move, running out of time loses the game, and the clock pauses while you are away from Play.

### 📖 Opening selection
- 「对弈」新增「开局」选项，可直接选一个开局并从该局面的终局开始对弈，开局着法会出现在着法列表中。

- Play now offers an Opening option: pick an opening and start from its final position, with the opening moves listed in the move list.

### ℹ️ Version in About
- 「帮助 → 关于」现在会显示当前版本号，中英文界面均已适配。

- Help → About now shows the current version number in both Chinese and English.

---

## 🛠️ Full Changelog
- feat(play): add selectable time controls with a running clock
- feat(play): allow starting a game from a chosen opening
- feat(about): show the current app version
- chore(version): bump the app version to 1.3.2

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

# v1.3.1 – Tidier First Run

> 本次更新只是小幅整理：整体流程更符合逻辑，界面也更整洁。
>
> A small housekeeping release: the flow is more logical and the interface tidier.

---

## 🎯 What's Changed
- 对首次进入的流程与默认外观做了整理，整体更符合逻辑、更整洁。

- Tidied up the first-run flow and default appearance for a more logical, cleaner experience.

---

## 🛠️ Full Changelog
- refactor(gui): make the first-run flow more logical and the interface tidier
- chore(version): bump the app version to 1.3.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.
---

# v1.3.0 – Puzzles and Importable Collections

> 本次更新在「对弈」与「分析工具」之间新增「谜题」模块，用于做战术题。程序不预设题库内容，用户可以自行导入开源免费的题集，并且内置了一份取自 Lichess puzzle database（CC0 公共领域）的精选样例，开箱即可练手。解题支持走对继续、走错即时提示、对手自动应着、提示箭头与显示答案；导入的题集以本地 JSONL 保存并按偏移量惰性读取，再大的题库也不会一次性占满内存。
>
> This release adds a Puzzles module between Play and Analysis for working through tactics. The app ships no preset library of its own: users can import free, open-source puzzle collections themselves, and a curated sample from the Lichess puzzle database (CC0 public domain) is bundled so there is something to solve out of the box. Solving gives correct/wrong feedback, plays the opponent's replies automatically, and offers hints and a full reveal; imported collections are stored locally as JSONL and read lazily by byte offset, so even very large files never load into memory at once.

---

## 🎯 What's New

### 🧩 Puzzle module
- 侧栏新增「谜题」模块，位于「对弈」与「分析工具」之间，拥有独立页面与棋盘。
- 点击己方棋子走正解：走对继续，走错即时提示并可重试，不会污染棋盘状态。
- 对手应着自动播放，双方按题解交替行棋；支持升变选择与拖拽/点击走子。
- 「提示」在棋盘上以箭头标出下一手，「显示答案」自动演示剩余解法，另有「重试」重开本题。
- 「上一题 / 下一题」在题集内切换，右侧显示题号、难度与主题标签。
- 走子动画、拖拽与棋盘翻转沿用对弈模块的统一交互；分析页仍保持只读浏览。

- Added a Puzzles module to the rail, between Play and Analysis, with its own page and board.
- Click a piece to play the solution: correct moves continue, wrong moves give instant feedback and can be retried without disturbing the board state.
- Opponent replies play automatically, alternating solver and opponent down the line; promotion picking and drag-or-click moves both work.
- Hint draws an arrow for the next move, Show solution walks through the rest, and Retry restarts the puzzle.
- Previous / Next step through the collection, with the puzzle number, rating, and theme tags shown beside the board.
- Move animation, dragging, and board flipping reuse the same interaction as the Play module; the analysis board stays read-only.

### 📥 Import your own collections
- 「导入题集...」支持 Lichess puzzle database 的 CSV 与含 FEN 的 PGN 题集，后续可扩展更多来源。
- 兼容 Lichess 约定：FEN 是对方走子之前的局面，着法序列的第一手为对方着法，第二手起才是解法。
- 大文件在后台线程流式解析并写入本地 JSONL，导入进度实时显示，界面不卡顿。
- 题集按行偏移量惰性读取，数百万题的题库也不会在启动或切题时全量载入内存。
- 题集列表显示来源文件名与题目数量，可随时删除。

- Import collection... accepts Lichess puzzle database CSV files and FEN-based PGN collections, with room for more formats later.
- Follows the Lichess convention: the FEN is the position before the opponent moves, the first move of the line is the opponent's, and the solution starts from the second move.
- Large files are parsed on a background thread and streamed to local JSONL, with live import progress and a responsive interface.
- Collections are read lazily by line offset, so multi-million-puzzle files never load fully into memory on startup or when changing puzzles.
- The collection list shows the source name and puzzle count, and each collection can be deleted at any time.

### 🎁 Bundled Lichess sample
- 内置一份取自 Lichess puzzle database（CC0 公共领域）的精选样例：2000 道题，约 440 KB，难度覆盖 399–3177。
- 通过 `tools/build_puzzles.py` 可复现该样例：HTTP Range 只下载题库开头数 MB，按难度分层抽样、过滤低质量题目，并逐题校验解法合法可解。
- 内置题集同样可以删除；删除后会记住选择，不再自动出现，用户也可重新导入完整题库。

- Bundled a curated sample from the Lichess puzzle database (CC0 public domain): 2,000 puzzles in about 440 KB, spanning ratings 399–3177.
- The sample is reproducible via `tools/build_puzzles.py`, which downloads only the first few megabytes via an HTTP range request, samples across rating bands, filters out low-quality entries, and validates that every solution is legal and solvable.
- The bundled collection can be deleted like any other; the choice is remembered so it does not reappear automatically, and users can import the full database whenever they want.

### ♟️ Board and internals
- `BoardWidget` 支持任意 FEN 起始局面、临时隐藏导航按钮，以及提示箭头。
- 新增 `PuzzleSession`（纯逻辑，负责题解与对错判定）与 `PuzzleImportWorker`（后台导入线程）。
- 中英文文案补齐；「关于」新增谜题来源与 CC0 说明。

- `BoardWidget` gained arbitrary starting FENs, a toggle for the navigation row, and hint arrows.
- Added `PuzzleSession` (pure logic for the solution and correctness checks) and `PuzzleImportWorker` (a background import thread).
- Added Chinese and English strings, plus a puzzle source and CC0 note in About.

---

## 🛠️ Full Changelog
- feat(puzzle): add the Puzzle module between Play and Analysis
- feat(puzzle): solve puzzles with wrong-move feedback, automatic opponent replies, hints, and reveal
- feat(puzzle): import Lichess CSV and FEN-based PGN collections
- feat(puzzle): stream large imports to JSONL with a lazy byte-offset reader
- feat(puzzle): bundle a curated 2,000-puzzle sample from the Lichess database (CC0)
- feat(tools): add `tools/build_puzzles.py` to rebuild the bundled sample
- feat(board): support arbitrary starting FENs, hint arrows, and a toggleable navigation row
- feat(gui): register the Puzzle module in the module rail and wire theme/board/language prefs
- feat(i18n): add Chinese and English strings for the Puzzle module
- feat(about): credit the Lichess puzzle database (CC0)
- refactor(board): keep a start FEN so positions can begin outside the standard game
- chore(build): add `zstandard` to `requirements-build.txt` for regenerating the sample
- chore(version): bump the app version to 1.3.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。`profile.json`、棋子/棋盘偏好、主题、API 配置与统计记录继续有效。
- 新增用户数据目录 `%APPDATA%\CheckPause\puzzles\`，仅在导入题集或删除内置题集时创建。
- 内置题集为只读资源，删除记录写入 `puzzles\index.json`；如需恢复，删除该文件即可。
- 打包体积约增加 0.5 MB（内置题集），`CheckPause.spec` 会随 `assets` 一并打包，无需改动。
- 从源码重建内置题集需要 `pip install zstandard`，仅构建期使用，运行时不依赖。

- No breaking changes. `profile.json`, piece/board preferences, themes, API settings, and statistics keep working.
- A new user data folder, `%APPDATA%\CheckPause\puzzles\`, is created only when importing a collection or deleting the bundled one.
- The bundled collection is a read-only resource; deleting it writes a marker to `puzzles\index.json`, and removing that file restores it.
- The package grows by roughly 0.5 MB (the bundled sample); `CheckPause.spec` already ships `assets`, so no packaging change is needed.
- Rebuilding the bundled sample from source needs `pip install zstandard`; it is build-time only and never required at runtime.
---

# v1.2.2 – Quiet Engine Launch

> 本次更新修复了窗口模式（`console=False`，无控制台）构建在对弈时的一个恼人问题：电脑每走一步都会闪出一个控制台窗口。原因是该构建自身没有控制台，而每次走子都会新建一个控制台子进程来运行 Stockfish，Windows 便为它分配一个新控制台窗口。现在引擎进程以隐藏方式启动，对弈全程干净无弹窗。
>
> This release fixes an annoying issue in the windowed, console-less build (`console=False`): a console window flashed on every computer move. Because that build has no console of its own, each move spawned a console-subsystem Stockfish process, and Windows allocated a fresh console window for it. The engine now launches hidden, so play stays clean from start to finish.

---

## 🎯 What's Fixed

### 🪟 No more console window on every engine move
- 窗口模式（无控制台）构建在对弈中，电脑走子不再弹出并瞬间关闭的控制台窗口。
- 新增统一的引擎启动封装 `open_stockfish()`，在 Windows 下以 `CREATE_NO_WINDOW` 启动 Stockfish。
- 对弈模块与「分析」模块的引擎启动都走同一封装，行为一致。

- The windowed, console-less build no longer flashes a short-lived console window when the computer moves.
- Added a single engine launch helper, `open_stockfish()`, which starts Stockfish with `CREATE_NO_WINDOW` on Windows.
- Both the Play module and the Analysis module now launch the engine through the same helper for consistent behavior.

---

## 🛠️ Full Changelog
- fix(engine): launch Stockfish with `CREATE_NO_WINDOW` so windowed builds show no console
- refactor(engine): add `open_stockfish()` and route all engine starts through it
- fix(play): stop the console flash on every computer move
- chore(version): bump the app version to 1.2.2

---

## ⚠️ Breaking Changes

- 无破坏性变更。棋子/棋盘偏好、主题、API 配置与统计记录继续有效。
- 仅改变 Windows 下引擎子进程的启动方式；从源码运行或带控制台运行时本就看不到该窗口，命令行界面同样不受影响。

- No breaking changes. Piece/board preferences, themes, API settings, and statistics keep working.
- Only how the engine child process is launched on Windows changes; running from source or with a console never showed the window, and the CLI is unaffected.
---

# v1.2.1 – Smooth Board Interaction

> 本次更新专注对弈手感：棋子可以拖拽，合法落点跟随悬停高亮，走子平滑滑动，被吃子淡出，拖到非法格会滑回原位并保持选中。整体交互向 Lichess / chess.com 靠拢，不再有瞬移和硬回弹。
>
> This release focuses on how the board feels: pieces can be dragged, legal targets respond to hover, moves slide smoothly, captures fade out, and an illegal drop slides the piece home while staying selected. The interaction now matches the intuition of Lichess and chess.com.

---

## 🎯 What's New

### 🖱️ Drag and hover
- 棋子支持拖拽：按住即可拖起，棋子跟随光标并微微放大，原格清空，合法落点圆点保持可见。
- 拖动时悬停到合法落点会加深高亮；悬停到可动棋子或合法落点时光标变为手型。
- 点击走子保留：点棋子显示圆点、点圆点走子；再点同一棋子或右键可取消选中。

- Drag-and-drop: hold a piece to pick it up; it follows the cursor and lifts slightly while legal-target dots stay visible.
- Hovering a legal target deepens its highlight, and the cursor becomes a hand over movable pieces and targets.
- Click-to-move is unchanged: click a piece for dots, click a dot to move, click the same piece again or right-click to deselect.

### 🎞️ Move animation
- 走子改为 130ms ease-out 平滑滑动，你走和电脑走都有动画。
- 王车易位时王与车同时滑动；被吃子在滑动过程中淡出，而不是瞬间消失。
- 拖到非法格松手时，棋子以同样的缓动滑回原位并保持选中。

- Moves slide with a 130ms ease-out animation, for both your moves and the engine's.
- Castling animates king and rook together, and captured pieces fade out instead of vanishing.
- Dropping on an illegal square slides the piece home with the same easing, keeping it selected.

---

## 🛠️ Full Changelog
- feat(board): support drag-and-drop moves with the piece following the cursor
- feat(board): keep click-to-move with legal-target dots and click-again to deselect
- feat(board): add hover highlights and pointer/hand cursors
- feat(board): animate moves with ease-out sliding, castling rooks, and capture fades
- feat(board): animate pieces snapping back after an illegal drop
- refactor(board): replay the move animation for both player and engine moves
- chore(version): bump the app version to 1.2.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。棋子/棋盘偏好、主题、API 配置与统计记录继续有效。
- 仅分析页保持只读浏览，动画与拖拽只在「对弈」模块启用。

- No breaking changes. Piece/board preferences, themes, API settings, and statistics keep working.
- The analysis board stays read-only; dragging and animations only run in the Play module.
---

# v1.2.0 – Play Against the Computer

> 本次更新兑现了侧栏注册表的预留：新增「对弈」模块，可以直接和 Stockfish 下棋。点击棋子再点高亮落点即可行棋，支持执白/执黑、五档难度、悔棋、认输、升变选择与棋步回看，还能把整盘棋一键送入分析模块。引擎思考在后台线程运行，界面全程不卡顿。
>
> This release delivers on the module registry: a new Play module lets you take on Stockfish directly. Click a piece and a highlighted square to move, play as White or Black, choose from five difficulty levels, undo, resign, pick a promotion piece, and review every move; one click sends the game to the analysis module. The engine thinks on a background thread, so the interface never freezes.

---

## 🎯 What's New

### 🤖 Play against the computer
- 侧栏新增「对弈」模块（位于「分析工具」上方），点击进入独立对弈界面。
- 点击己方棋子选中，合法落点以圆点（空格）或圆环（可吃子）提示，再点落点即走子。
- 支持「执白 / 执黑」：选择执黑时棋盘自动翻转，并由电脑先行。
- 五档难度：入门、简单、中等、困难、大师，映射 Stockfish 的 `Skill Level` 与思考深度/时间。
- 兵升变弹出选择框，可选后、车、象、马。

- Added a Play module to the rail (above Analysis) with its own game screen.
- Click one of your pieces to select it; legal targets show as dots (empty squares) or rings (captures), and clicking a target makes the move.
- Play as White or Black: choosing Black flips the board and lets the engine move first.
- Five levels — Beginner, Easy, Medium, Hard, Master — mapped to Stockfish's `Skill Level` plus depth/time.
- Pawn promotion opens a picker for Queen, Rook, Bishop, or Knight.

### 🎮 Game controls
- 新对局、悔棋（回退你与电脑各一步，轮到你重新走）、认输。
- 状态栏显示「轮到你走棋 / 电脑思考中 / 将军」，终局显示胜负或和棋结果。
- 棋步列表实时更新，可点击回看任意局面；棋盘翻转与导航按钮沿用分析页的交互。
- 「导入分析」把当前棋谱（含完整着法）直接送到分析模块，可立即开始 Stockfish 分析。

- New game, undo (takes back both your move and the engine's reply, returning the turn to you), and resign.
- The status line shows Your turn / Computer is thinking / Check, and the result appears when the game ends.
- The move list updates live and lets you step back to any position; flip and navigation work like the analysis board.
- Send to analysis pushes the full game into the analysis module, ready for an immediate Stockfish run.

### ⚙️ Engine and internals
- 新增 `EngineMoveWorker`（`QThread`）：每次走子独立启动 Stockfish，思考过程不阻塞界面，关闭窗口或开新局时会安全回收线程。
- `BoardWidget` 增加可复用的交互模式（选中高亮、合法落点、`move_requested` 信号），分析页仍保持只读浏览。
- 对弈界面自动跟随现有主题、棋子集与棋盘配色设置。

- Added `EngineMoveWorker` (`QThread`): each move spins up Stockfish in the background, the UI never blocks, and threads are reclaimed safely on exit or when starting a new game.
- `BoardWidget` gained a reusable interactive mode (selection highlight, legal targets, a `move_requested` signal) while the analysis board stays read-only.
- The Play screen follows the current theme, piece set, and board theme automatically.

---

## 🛠️ Full Changelog
- feat(gui): add the Play page with an interactive board against Stockfish
- feat(gui): register the Play module above Analysis in the module rail
- feat(gui): support click-to-move with selection and legal-target highlights
- feat(gui): add side selection, automatic board flip, and engine-first opening
- feat(gui): add five difficulty levels backed by Stockfish Skill Level
- feat(gui): add new game, undo, resign, and send-to-analysis controls
- feat(gui): add a promotion dialog for queen, rook, bishop, or knight
- feat(gui): show turn status, check, and final result messages
- feat(worker): add `EngineMoveWorker` for background engine play
- refactor(board): add interactive mode and `set_moves` to `BoardWidget`
- feat(i18n): add Chinese and English strings for the Play module
- chore(version): bump the app version to 1.2.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。现有 `profile.json`、棋子/棋盘偏好、API 配置与统计记录继续有效。
- 对弈功能使用随程序分发的 Stockfish，无需额外安装。

- No breaking changes. Existing `profile.json`, piece/board preferences, API settings, and statistics keep working.
- Play uses the Stockfish binary bundled with the app; no extra installation is needed.
---

# v1.1.0 – Module Rail and Close Confirmation

> 本次更新为应用装上左侧模块侧栏：主窗口改为「侧栏 + 页面堆栈」的外壳结构，模块由注册表驱动，当前仅注册「分析工具」，后续谜题、对弈等模块可直接注册接入。同时新增关闭确认弹窗，避免误触退出打断分析或对话。
>
> This release adds a left module rail: the main window becomes a rail + stacked-pages shell, driven by a module registry that currently holds Analysis only, so Puzzles, Play, and others can plug in later. It also adds a close-confirmation dialog so analysis or chat is never interrupted by an accidental exit.

---

## 🎯 What's New

### 🧭 Left module rail
- 新增 84px 左侧模块栏（`gui/widgets/module_rail.py`），主窗口改为「侧栏 + 页面堆栈」的外壳结构。
- 模块由注册表（`MODULES`）驱动，目前仅注册「分析工具」；后续谜题、对弈等模块注册后即可接入。
- 欢迎页与主界面共用同一外壳；模块高亮跟随当前页面，语言切换同步刷新。
- 浅色/深色两套侧栏配色：灰色圆角选中态、悬停反馈、右侧分隔线；窗口默认宽度相应调整。

- Added an 84px left module rail (`gui/widgets/module_rail.py`); the main window is now a rail + stacked-pages shell.
- Modules come from the `MODULES` registry, currently only Analysis; Puzzles, Play, and others can plug in later by registering.
- The welcome page and the main view share the same shell; the active item follows the current page and refreshes on language switches.
- Light/dark rail styling with a gray rounded selection, hover feedback, and a right border; the default window width grew to fit the rail.

### 🚪 Close confirmation
- 关闭窗口时弹出确认框：取消则窗口保持打开，确认后才退出。
- 退出前仍会安全停止 Stockfish 分析与 AI 对话线程，不留残余进程。

- Closing the window now asks for confirmation: cancel keeps it open, confirm exits.
- On exit, the Stockfish analysis and AI chat threads are still stopped safely, leaving no processes behind.

---

## 🛠️ Full Changelog
- feat(gui): add a left module rail with a registry for future modules
- feat(gui): wrap the welcome page and the main view in a rail + stack shell
- feat(gui): add a confirmation dialog before closing the window
- feat(theme): style the module rail for light and dark themes
- feat(i18n): add rail and close-confirmation strings in Chinese and English

---

## ⚠️ Breaking Changes

- 无破坏性变更。现有 `profile.json`、棋子/棋盘偏好与 API 配置继续有效。
- 入口脚本与模块路径（`run_gui.py`、`checkpause.*`）保持不变。

- No breaking changes. Existing `profile.json`, piece/board preferences, and API settings keep working.
- The entry point and module paths (`run_gui.py`, `checkpause.*`) are unchanged.
---

# v1.0.0 – Graphical Interface, Move List, Personalization, and Performance

> CheckPause 的首个正式系列版本。它从一个命令行工具成长为可分发的中英文桌面应用：PyQt6 图形界面、明暗主题、短信式 AI 对话、可点击的着法列表、Lichess 风格的自绘棋盘与个性化外观、翻转棋盘与表现评级、开局谱库、可配置的 OpenAI 兼容接口，以及一键打包的 Windows exe。
>
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
---

# v0.3.1 – Bilingual CLI and Persistent Language Preferences

> 本次更新为 CLI 加入中英文语言选择。用户可以在首次启动时选择界面语言，也可以在运行过程中随时切换。
>
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
---

# v0.3.0 – Reliable AI, Easier Setup, Cleaner Architecture

> 本次更新聚焦于 **稳定性**、**配置体验** 和 **代码结构**。CP 现在使用最新可用的 DeepSeek Flash 模型，并能更好地处理网络、API 和 Stockfish 配置问题。
>
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
