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

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.9.1...v2.0.0

# v1.9.1 – Play Screen Rework & System Language

> **The Play screen's layout logic has been reworked, separating setup from play with a clearer hierarchy and smoother controls. The installer and the first launch pick Chinese or English from the system language, and every hover tooltip is gone.** Leaving a game in progress now asks first, instead of a setting change silently discarding it.

---

## 🎯 What's New

### ♟️ Play screen logic reworked
- 重新梳理了对弈页的界面逻辑：配置与对局分开，开局前只管设置，开局后只保留对局需要的信息，层级更清晰。
- 时钟、结果与操作按钮重新归位，暂停、悔棋、认输等操作更顺手。

- Reworked the Play screen's layout logic: setup and play are now separate, so the panel only shows what the current step needs.
- Clocks, the result and the action buttons are regrouped, making pausing, undoing and resigning feel natural.

### 🈯 System language, on install and first launch
- 安装包按 Windows 界面语言选向导语言：中文系统直接用中文，其它语言默认英文，只有无法识别时才弹选择框。
- 首次启动的应用界面同样跟随系统语言（此前一律中文）；已有档案不受影响。

- The installer picks its wizard language from the Windows UI language: Chinese on Chinese systems, English everywhere else, with a chooser only when nothing matches.
- The first launch follows the system language as well (it used to always start in Chinese); existing profiles are unaffected.

### 🧹 A quieter interface
- 删除所有按钮的悬停提示气泡；纯图标按钮（棋盘导航、翻转、编辑棋子等）把文字移入读屏用的无障碍名称。

- Every hover tooltip is gone; icon-only controls (board navigation, flip, piece palette) move their text into accessible names for screen readers.

## 🛠️ Full Changelog
- feat(play): split the Play screen into setup and playing states
- feat(play): keep clocks and the result in a fixed header
- feat(play): allow pausing without a clock and a rematch after the game
- feat(play): confirm before leaving a game in progress
- feat(installer): choose the wizard language from the Windows UI language
- feat(startup): default the interface language to the system language
- refactor(gui): drop every hover tooltip but keep accessible names
- chore(i18n): simplify the turn and leave-game wording
- chore(version): bump the app version to 1.9.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.9.0...v1.9.1

# v1.9.0 – Cloud Account Onboarding & History Reset

> **The first-run page is now a cloud-account guide: sign in or sign up, or drop straight into offline mode. The separate local nickname is gone, renaming costs 60 CP credits, and "Delete user data" becomes "Delete history" in Statistics.** First launch no longer asks for a local username that had nothing to do with your account. It is now a card-based account page: enter a username and password to sign up or sign in, then the app switches to cloud mode. If the network is unavailable, choose "Offline mode" (the local name is player; sign in later from Settings). Cloud accounts can be renamed for 60 CP credits. The old "Delete user data" entry is gone, replaced by deleting game history from the Statistics panel.

---

## 🎯 What's New

### ☁️ Cloud account on first launch
- 首启页改为云端账号页：用户名 + 密码，注册或登录；成功后自动切到云端模式。
- 网络不通时可「使用离线模式」：本地档案名为 `player`、走免费本地模式，联网后在「设置 → 云端账号」登录即可。
- 卡片式界面：应用标志、标题层级、字段标签、主次按钮，浅色/深色主题都适配。

- First launch is now a cloud-account page: username + password to sign up or sign in, then it switches to cloud mode.
- When the network is unavailable, "Offline mode" continues as a local profile named `player` on the free local tier; sign in later from Settings > Cloud account.
- A card layout with the app mark, a clear title hierarchy, field labels and primary/secondary buttons, in both light and dark themes.

### ✏️ Paid username change
- 「设置 → 云端账号」新增「修改用户名」，收费 **60 CP积分**；余额不足会先提示。
- 费用由服务端决定（随账号返回 `rename_fee`），改费用无需重发客户端。

- Settings > Cloud account gains "Change username" for **60 CP credits**; a short balance is caught before the request.
- The price comes from the server (`rename_fee` on the account), so changing it needs no client release.

### 🧹 Delete history, not the whole account
- 移除「设置 → 删除用户数据」；统计面板底部新增「删除历史数据」，只清空对局历史与相关统计，保留账号与设置。
- 顺带修好一个以前存在的bug：删档不会退出云端账号。

- Removed Settings → Delete user data; Statistics now has "Delete history", which clears only the recorded games and their stats while keeping the profile.
- This also fixes an old inconsistency: deleting the profile used to leave you signed in to the cloud account.

## 🛠️ Full Changelog
- feat(welcome): make the first launch a cloud-account page with an offline mode
- feat(welcome): redesign the page as a themed card with the app logo
- feat(account): charge a rename fee and add a Change username action
- feat(server): add POST /v1/accounts/rename, charged in one transaction
- feat(settings): switch to cloud mode after signing in
- feat(stats): delete game history from the Statistics panel
- refactor(profile): drop the separate local nickname entry
- refactor(welcome): stop asking for a local username on first launch
- chore(server): add CHECKPAUSE_RENAME_FEE_CREDITS (default 60)
- chore(version): bump the app version to 1.9.0

---

## ⚠️ Breaking Changes

- 首启不再设置本机昵称；离线用户本机显示名为 `player`。旧档案不受影响。
- 云端账号改名收费 **60 CP积分**，且需要服务端升级到含 `/v1/accounts/rename` 的版本。
- 「设置 → 删除用户数据」已移除，改用统计面板的「删除历史数据」。

- First launch no longer sets a local nickname; offline users show as `player`. Existing profiles are unaffected.
- Renaming a cloud account costs **60 CP credits** and needs a server that has `/v1/accounts/rename`.
- Settings → Delete user data is gone; use Delete history in Statistics instead.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.8.4...v1.9.0

# v1.8.4 - Multi-Line Live Analysis & Game-End Sounds

> **Live analysis now runs multi-line and deepens over time, with a numeric score, and the sound bugs are fixed.** In the Panel module the engine keeps one process alive and deepens the search, showing up to three ranked best moves (the best drawn thickest, the rest thinner and fainter) that change with depth, plus a numeric score next to the bar, so the board looks nicer and behaves more logically.

---

## 🎯 What's New

### 🔍 Multi-line, deeper live analysis
- 实时分析改为**常驻引擎**，逐层加深并实时刷新，能直接看到推荐着法随深度变化。
- 开启「显示推荐着法」后，最多同时显示**三条**推荐箭头，最优一条最粗，其余依次变细变淡。
- 深度越高搜索越久，机器负载相应更明显。

- The live search now keeps **one persistent engine** that deepens step by step and streams each depth, so you can watch the suggestions change as it thinks.
- With "Show best move" on, up to **three** ranked arrows appear, the best drawn thickest and the rest thinner and fainter.
- A higher depth searches longer, so the machine works noticeably harder.

## 🛠️ Full Changelog
- feat(analysis): keep a persistent engine and stream the live search by depth
- feat(analysis): show up to three ranked best-move arrows via MultiPV
- feat(board): show a numeric evaluation beside the depth selector
- feat(menu): move Appearance into Personalization above Pieces
- fix(board): hide the evaluation row while editing the board
- fix(board): stop the hint switch from re-scoring the evaluation bar
- fix(sound): play the check effect when a capture also gives check
- feat(sound): add dedicated checkmate and draw effects
- chore(version): bump the app version to 1.8.4

---

## ⚠️ Breaking Changes

- 「显示推荐着法」现在最多给出三条推荐，且开关只控制箭头显隐；评估条始终独立更新。
- 新增 `checkmate` / `draw` 音效文件；旧档案无需迁移。
- 「外观」菜单位置调整到「个性化 → 外观」。

- "Show best move" can now show up to three suggestions and only toggles the arrows; the bar updates independently.
- New `checkmate` / `draw` sound files ship alongside the existing set; no profile migration is needed.
- The Appearance submenu moved to Personalization → Appearance.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.8.3...v1.8.4

# v1.8.3 - Evaluation Bar & Cleaner Sounds

> **A new Stockfish evaluation bar sits above the board, moving smoothly with each position, with an optional best-move arrow; and the move sounds are down to one.** In the Panel module a bar fills the empty space above the board, its white/black split tracking who stands better, and it animates on every step. Under it you can tick "Show best move" to draw the engine's choice as a frosted-glass arrow, and pick the analysis depth (10–22). The sound sets are now just one, with the old "Digital" renamed to "Default".

---

## 🎯 What's New

### 📊 Live evaluation bar
- 棋盘上方新增评估条：白色比例代表白方优势、黑色代表黑方，中线刻度标出均势，随引擎评分**平滑动画**过渡。
- 评估条**始终显示**，不会挤占布局；`面板` 里的棋盘尺寸与 `对弈`、`谜题` 完全一致。
- 引擎以背景线程分析当前局面，快速翻棋时只保留最新一次请求，不拖慢操作。

- A bar above the board shows white's share in white and black's in black, a centre tick marking equality, animating smoothly to each engine score.
- The bar is always on and takes no layout space, so the Panel board keeps exactly the same size as Play and Puzzles.
- The engine scores the current position on a background thread; rapid navigation keeps only the latest request, so nothing feels stuck.

### ✨ Best-move hint arrow
- 评估条下方新增「显示推荐着法」开关与「深度」下拉（10–22），左右对称排布，选择即时生效并记住。
- 勾选后，用**半透明玻璃质感**的箭头在棋盘上标出 Stockfish 推荐着法，浅格深格上都清晰。
- 取消勾选只隐藏箭头，评估条照常更新。

- Under the bar sit a "Show best move" switch and a "Depth" selector (10–22), laid out symmetrically, applied at once and remembered.
- When ticked, the engine's choice is drawn as a **frosted-glass arrow**, readable on both light and dark squares.
- Untick it to hide only the arrow; the bar keeps updating.

### 🔊 One sound set
- 音效精简为一种：移除「经典」「木质」，原「电子」更名为**「默认」**，可在「个性化 → 音效」里切换或关闭。
- 旧档案里保存过已删除音效的，自动回落到默认。

- The sound sets are reduced to one: Classic and Wood are gone, and Digital is renamed **Default**, still switchable or turned off under Personalization → Sound.
- A profile that had saved a removed set falls back to the default automatically.

---

## 🛠️ Full Changelog
- feat(board): draw a live Stockfish evaluation bar above the analysis board
- feat(board): animate the evaluation bar between scores
- feat(board): show the engine best move as a frosted-glass arrow
- feat(board): add a hint toggle and depth selector under the bar
- feat(engine): add score reading and evaluation-ratio helpers
- feat(workers): add `LiveAnalysisWorker` for background position scoring
- feat(data): remember the hint switch and analysis depth
- feat(sound): keep only the default set and drop the classic/wood assets
- refactor(sound): rename the digital set to the default set
- chore(version): bump the app version to 1.8.3

---

## ⚠️ Breaking Changes

- 评估功能默认开启；不需要箭头可在评估条下方取消「显示推荐着法」。
- 音效只剩「默认」一种，自定义过的「经典」「木质」会回落到默认。
- 用户设置新增 `hint_enabled` 与 `eval_depth`；`sound_set` 中已删除的取值会自动回落。

- The evaluation feature is on by default; untick "Show best move" under the bar if you do not want the arrow.
- Only the Default sound set remains; a saved Classic or Wood choice falls back to it.
- The profile gains `hint_enabled` and `eval_depth`; a removed `sound_set` value falls back automatically.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.8.2...v1.8.3

# v1.8.2 - HTTPS Cloud Endpoint

**Cloud mode now talks to the HTTPS domain `checkpause.com`.** The connection is encrypted and no longer relies on a bare IP; an older install that saved the previous address is migrated automatically. Local mode (bring your own key) is unchanged.

## 🎯 What's Changed

### 🔐 HTTPS cloud endpoint
- 云端模式默认地址由 `http://43.108.99.244` 换成 `https://checkpause.com`，账号、充值、分析请求全程加密。
- 设置里若保存过旧的裸 IP，会**自动视为未设置**并改用新域名；自定义的服务地址不受影响。
- The cloud-mode default moved from `http://43.108.99.244` to `https://checkpause.com`, so sign-in, top-ups and analysis all travel over TLS.
- A settings file holding the old bare IP is treated as unset and moves to the domain; a genuinely custom address is left untouched.

## 🛠️ Full Changelog

- feat(cloud): default the server URL to https://checkpause.com
- fix(settings): migrate a saved plain-HTTP IP to the HTTPS domain

## ⚠️ Breaking Changes

- 无破坏性变更。旧地址会自动迁移；如需继续用自定义服务器地址，在设置中填写即可。
- No breaking changes. The previous address is migrated automatically; a custom server address still works if entered in settings.

# v1.8.1 - Move Sounds

> **Every move now has a sound, and you can pick its style just like piece sets and board themes.** Quiet moves, captures, checks, castling and promotions each get their own sound, in Play, Puzzles and the analysis panel alike, on by default. Switch styles or turn it off under Personalization → Sound. Every clip is synthesised by the project itself, with no third-party assets.

---

## 🎯 What's New

### 🔊 Move sounds
- 走子播放音效：普通走子、吃子、将军、易位、升变各不相同，默认开启。
- 三个模块统一生效：「对弈」「谜题」与「面板」都已接入，单步前后翻棋也有一致的声音。
- 引擎跑分析时的自动回放**保持安静**，不会在分析过程中连着响一串。

- Sounds play on every move: quiet moves, captures, checks, castling and promotions each have their own, on by default.
- The Play, Puzzles and Panel modules all use them, and single-step navigation sounds consistent too.
- The engine's automatic replay while analysing stays silent, so a long game is not rattled off sound after sound.

### 🎛️ Selectable sound sets
- 「个性化 → 音效」可在 **关闭 / 经典 / 木质 / 电子** 之间切换，与棋子、棋盘的选择方式一致，即时生效并记住。
- 所有音效由 `tools/make_sounds.py` 程序合成（无第三方素材），因此没有任何版权归属问题。

- Personalization → Sound offers **Off / Classic / Wood / Digital**, chosen the same way as piece sets and board themes, applied at once and remembered.
- Every clip is synthesised by `tools/make_sounds.py` with no third-party assets, so there are no attribution requirements.

---

## 🛠️ Full Changelog
- feat(sound): play a distinct sound for moves, captures, checks, castling and promotions
- feat(sound): wire the sounds into Play, Puzzles and the analysis panel
- feat(sound): add Off / Classic / Wood / Digital sets under Personalization
- feat(tools): add `tools/make_sounds.py` to regenerate every clip
- feat(i18n): add the sound menu strings in Chinese and English
- fix(sound): keep the analysis replay silent
- chore(version): bump the app version to 1.8.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。音效默认开启，可在「个性化 → 音效」里关闭。
- 用户设置在 `profile.json` 中新增 `sound_set`；旧版本里的音效开关会自动迁移。

- No breaking changes. Sound is on by default and can be turned off under Personalization → Sound.
- The preference is stored as a new `sound_set` field in `profile.json`; the previous on/off choice is migrated automatically.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.8.0...v1.8.1

# v1.8.0 - macOS and the Analysis Panel

> **Adds a macOS build (Apple Silicon and Intel) and turns the analysis tool into an editable analysis panel.** The macOS build ships as a `.dmg` with feature parity to Windows; the analysis panel gains move animations and a board editor, and can analyze from any position.

---

## 🎯 What's Changed

### 🍎 macOS build
- 新增 **macOS 版（Apple Silicon 与 Intel）**，功能与 Windows 版一致；通过 GitHub Actions 在 macOS runner 上打包，产出 `.dmg`。
- 引擎使用 **Stockfish 的 macOS universal 二进制**，单个文件同时覆盖 M 系列与 Intel。
- 用户数据保存在 `~/Library/Application Support/CheckPause/`（Windows 仍为 `%APPDATA%\CheckPause\`）。
- 更新清单新增按平台区分的下载地址；macOS 客户端不会再被推送 `.exe`。

- A **macOS build (Apple Silicon and Intel)** with feature parity to Windows, produced by GitHub Actions on macOS runners and shipped as a `.dmg`.
- Bundles Stockfish's **macOS universal binary**, one file covering both M-series and Intel.
- User data lives in `~/Library/Application Support/CheckPause/` on macOS (`%APPDATA%\CheckPause\` on Windows).
- The update manifest now carries per-platform download URLs, so a macOS client is never offered a `.exe`.

### ♟️ Analysis panel: move animation
- 分析回放、上一步/下一步与棋步列表点击现在都有**平滑的走子动画**，与对弈、谜题两个模块一致。
- 前进与后退都有动画：吃子淡入淡出、易位时车一起移动、退回升变时显示原来的兵。

- Analysis playback, the prev/next buttons and the move list now **animate every move**, matching the play and puzzle modules.
- Animations run in both directions: captures fade, castling carries the rook, and stepping back through a promotion shows the pawn again.

### ✏️ Analysis panel: board editor
- 新增**编辑棋盘**按钮：棋子调色板与擦除；拖动可移动棋子，右键或拖出棋盘可删除。
- 可设置**走子方、易位权、吃过路兵**（只列出当前局面下合法的吃过路兵格）。
- **初始局面 / 清空棋盘 / 复制 FEN / 应用 / 取消**，应用后的局面成为新的分析起点。

- A new **Edit board** mode with a piece palette and eraser; drag a piece to move it, right-click or drag it off the board to delete.
- **Side to move, castling rights and en passant** can be set; only legal en passant squares are offered.
- **Start position, clear board, copy FEN, apply and cancel**; the applied position becomes the new starting point for analysis.

### 🧩 Analysis panel: play moves and analyze any position
- 可以直接在分析棋盘上**走棋**（双方、含升变），续在棋谱后面，或从任意一步**分支出新变化**；改写棋谱时会重置旧的分析结果。
- 分析引擎现在识别 PGN 的 **`SetUp` / `FEN` 头**，编辑出来的局面（或自带 FEN 的棋谱）可以直接分析。
- 棋步列表支持**黑方先走**的局面，列编号与手数正确。
- 侧栏的「分析工具」改名为「面板」（英文界面 "Panel"），位置与功能不变。

- You can **play moves on the analysis board itself** (both sides, promotions included), continuing the game or **branching from any move**; rewriting the line resets the previous results.
- The engine now honours a PGN's **`SetUp` / `FEN` headers**, so edited positions (and games that carry a FEN) can be analyzed directly.
- The move list handles positions where **Black moves first**, with the correct columns and move numbers.
- The sidebar module "Analysis" is now labelled "Panel"; its position and contents are unchanged.

---

## 🛠️ Full Changelog
- feat(macos): platform-aware Stockfish executable path
- feat(macos): cross-platform PyInstaller spec with a `.app` bundle and `.icns` icon
- feat(macos): GitHub Actions workflow building arm64 and x86_64 `.dmg` images
- feat(macos): store user data in `~/Library/Application Support/CheckPause/`
- feat(updater): pick the download URL from the manifest's per-platform `urls` map
- fix(updater): never offer the Windows installer to a macOS client
- feat(analysis): animate move navigation in both directions
- feat(analysis): add a board editor with a piece palette, turn, castling and en passant
- feat(analysis): play legal moves on the analysis board and branch the line
- feat(engine): analyze from a PGN's `SetUp`/`FEN` starting position
- feat(move-list): support positions where Black moves first
- chore(i18n): call the analysis module "Panel"
- chore(version): bump the app version to 1.8.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。Windows 版的棋盘、引擎分析、存档与两种 AI 模式均保持原样。
- macOS 包未签名、未公证，首次打开需右键 → 打开，或到「系统设置 → 隐私与安全性」点「仍要打开」。
- 侧栏入口「分析工具」已改名为「面板」，位置不变。

- No breaking changes. On Windows the board, engine analysis, saved games and both AI modes are unchanged.
- The macOS build is unsigned and not notarized, so the first launch needs right-click → Open, or "Open Anyway" under System Settings → Privacy & Security.
- The sidebar entry "Analysis" is now labelled "Panel"; its position is unchanged.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.7.2...v1.8.0

SHA-256: `978609890A2650B934DF66F7C7B1947BF6EF51327F6ABD3A5B4E48200C12B804`

# v1.7.2 - Icon Fix

> **Fixes the issue where the installed Windows application showed the default Python icon.** Version 1.7.2 fixes the application icon and the icons used by Start Menu and desktop shortcuts.
>
> A small update otherwise: the board, engine analysis, saved games and both AI modes are unchanged.

---

## 🎯 What's Changed

### 🖥️ Application icon fix
- 启动时明确设置 CheckPause 应用图标。
- SVG 图标加载失败时回退到内置 `app.ico`。
- 修复开始菜单和桌面快捷方式使用的图标路径。
- 安装包继续使用同一份应用图标资源。

- The CheckPause application icon is set explicitly at startup.
- SVG loading falls back to the bundled `app.ico` when necessary.
- Start Menu and desktop shortcuts now use the correct icon path.
- The installer uses the same icon resource as the application.

---

## 🛠️ Full Changelog
- fix(icon): set the application icon explicitly at startup
- fix(icon): fall back to the bundled ICO when SVG rendering fails
- fix(installer): point shortcuts at the bundled application icon
- chore(version): bump the app version to 1.7.2

---

## ⚠️ Breaking Changes

- 无破坏性变更。
- 已安装 1.7.1 的用户直接安装本版本即可修复图标显示问题。

- No breaking changes.
- Users on 1.7.1 can install this version directly to fix the icon display issue.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.7.1...v1.7.2

SHA-256: `AC1B731C14C81BE016B2532436EF155DCE67F560BF01A51518FCB25961BB22DF`

# v1.7.1 - Instant Update Checks

> The "Check for updates" action no longer waits on a timeout. The previous code queried two GitHub mirrors in sequence, one of which is often unreachable from mainland China, so every check consumed that timeout before returning. Both are now queried concurrently, with the project's own server checked first, so the result appears almost immediately.
>
> A small update otherwise: the board, engine analysis, saved games and both AI modes are unchanged.

---

## 🎯 What's Changed

### ⚡ Faster update checks
- 两个 GitHub 镜像改为**并发**请求，等待时间由两者之和缩短为其中较慢的一个。
- 新增**自建服务器**作为首要来源（`http://43.108.99.244/version.json`）：国内访问速度快，且直接读取磁盘文件，不存在 CDN 缓存导致的版本滞后。
- 手动「检查更新」**以主源为准**，主源返回即显示结果；仅在主源不可达时回退到 GitHub 镜像。
- 开机后的后台检查仍会查询全部三个来源并取最高版本，用于发现主源文件过期的情况。

- The two GitHub mirrors are now queried **concurrently**, so the wait is that of the slowest one rather than their sum.
- A **primary source on the project's own server** is consulted first: fast to reach from China, and read directly from disk, so no CDN cache can hold a release back.
- A manual check **trusts the primary source** and shows its answer as soon as it arrives, falling back to the GitHub mirrors only when the server cannot be reached.
- The background check at launch still queries all three sources and keeps the highest version, which is how a stale primary manifest would be detected.

### 🖥️ Server
- nginx 新增 `/version.json`，由 `checkpause-version-refresh.timer` 每 2 分钟从仓库刷新（原子替换，失败保留旧文件）。

- nginx serves `/version.json`, refreshed from the repository every 2 minutes by `checkpause-version-refresh.timer`.

---

## 🛠️ Full Changelog
- fix(update): query every mirror at once instead of one after another
- feat(update): check our own server first so a manual check answers at once
- feat(server): mirror the version manifest from our own box
- chore(version): bump the app version to 1.7.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。
- ⚠️ 服务器需先重新部署（`git pull` + `install.sh`），主源才会生效；仍在使用 1.7.0 的用户需升级到本版本，才能获得即点即得的检查结果。

- No breaking changes.
- ⚠️ The server must be redeployed (`git pull` + `install.sh`) before the primary source exists, and users still on 1.7.0 need this release to get the instant result.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.7.0...v1.7.1

SHA-256: `D8A3BF0B864B1AC509F07B48B9A484EBCC97BBAD8726D92464C2CDA58EC84C19`

# v1.7.0 - Cloud Coaching

> A new **cloud coaching** mode: no API key of your own, just an account and some CP credits. It uses a prompt tuned on the server.
>
> **Local mode is unchanged** — the interface, the controls and saved games all stay as they are. Only cloud mode requires a sign-in, so if you stay on local mode this release changes nothing for you.
>
> Top up under Settings → Cloud account: choose an amount, pay in your browser, and the balance is already there when you return.

---

## 🎯 What's Changed

### ☁️ Cloud coaching
- 设置中新增「AI 模式」选项：**本地模式**（自行填写 API Key，与以往一致）或**云端模式**（使用 CheckPause 账号与提示词）。
- 云端模式需要注册/登录。密码仅用于登录，软件**不保存密码**，只保存一个可随时吊销的令牌。
- 充值流程：选择金额 → 浏览器打开支付宝付款 → 余额自动到账，无需手动刷新。
- 余额显示于「设置 → 云端账号」，同时显示在菜单中。

- Settings gains an **AI mode** choice: local (your own API key, exactly as before) or cloud (a CheckPause account and prompt).
- Cloud mode requires an account. The password is used only to sign in and is never stored; the app keeps a revocable token instead.
- Topping up: choose an amount, pay in the browser, and the balance arrives automatically, with no manual refresh.
- The balance appears under Settings → Cloud account and in the menu.

### 🔒 No model name shown in cloud mode
- 此前模型输入框仅置灰、仍留在界面上；现在**完全隐藏**，云端模式下界面不会出现任何模型名称。

- The model field used to be greyed out but still visible. In cloud mode the model and endpoint fields are now **hidden entirely**, so no model name appears on screen.

### 💬 Billing unit is now CP credits
- 界面、错误提示、付款页面统一改成 **CP积分**（英文界面为 CP credits）。

- The billing unit is now called **CP credits** everywhere it can be read.

---

## 🛠️ Full Changelog
- feat(client): sign in to a cloud account and show the balance
- feat(client): buy CP credits and watch the balance update by itself
- feat(client): hide the provider fields in cloud mode
- chore(i18n): call them CP credits
- chore(version): bump the app version to 1.7.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。棋盘、引擎分析、存档与本地模式均保持原样。
- 云端模式为新增的可选项，需要时在设置中切换即可。

- No breaking changes. The board, engine analysis, saved games and local mode are all unchanged.
- Cloud mode is new and optional; switch to it in Settings when you want it.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.6.1...v1.7.0

SHA-256: `5CA34298B9D1D328848FDCC5CE50AAE7EDACD1452167332D35855CDC020F9E3B`

# v1.6.1 - Update Notifications Fixed

> Fixes a silent failure: update notifications never fired. The app read its version manifest from a China-friendly CDN first, and that copy could be many hours stale, so the app believed it was already current and stayed quiet. Releases 1.5.4 and 1.6.0 most likely never reached existing users. Both sources are now consulted and the higher version wins.

---

## 🎯 What's Changed

### 🔔 Update notifications now fire
- 此前只读取**第一个**可连接的来源；该来源可能缓存着十几个小时前的版本号，软件据此误判为"已是最新"，因此不给出提示。
- 现在**两个来源都会读取**，并取版本号更高的一个；任一来源过期，都不会再掩盖新版本。

- Before: only the **first** reachable source was read. That source could serve a version number many hours old, so the app concluded it was current and stayed quiet.
- Now: **both sources are read** and the higher version wins, so a stale copy can no longer hide a release.

### 🧪 Three new tests
- 新增的三个测试覆盖"一个来源过期、另一个来源为新版本"的情形，其中包括本次实际遇到的场景。

- Three tests now cover the case where one mirror is stale and the other is current, including the exact situation that caused this release.

---

## 🛠️ Full Changelog
- fix(update): consult every mirror and keep the newest version found
- test(update): cover a stale mirror hiding a newer release
- chore(version): bump the app version to 1.6.1

---

## ⚠️ Breaking Changes

- 无破坏性变更。但需注意：**该修复仅在安装本版本后生效**；在此之前，软件仍无法发现新版本。

- No breaking changes. One caveat: the fix only takes effect once installed. Until then the app still cannot see new releases.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.6.0...v1.6.1

SHA-256: `1A30C9C2E4C4DB2272B2B5BACFA3715401F5757138DF8AF7D143E1A59187674E`

# v1.6.0 - PySide6 Migration

> The interface toolkit moves from PyQt6 to PySide6, the binding Qt maintains itself, licensed under the LGPL. This is not a feature release: the UI, the controls and your data are all unchanged. Install it as usual and everything stays where it was.

---

## 🎯 What's Changed

### 🔄 Qt's official binding
- 图形界面框架由 PyQt6 迁移到 **PySide6**。两者 API 几乎一致，所以这是一次纯粹的底层替换，没有重写任何界面。

- The GUI toolkit moves from PyQt6 to PySide6. The two APIs are near-identical, so this is a straight swap underneath rather than a rewrite of any screen.

### 🧩 Interface and data unchanged
- 布局、配色、字体、快捷键、棋子样式、谜题进度、统计数据、API 设置 —— **全部保持不变**。升级后第一次打开，看到的就是原来那个 CheckPause。

- Layout, colours, fonts, shortcuts, piece sets, puzzle progress, statistics and API settings all stay exactly as they are. The first launch after upgrading looks like the CheckPause you already know.

### 📦 A slightly larger installer
- 从 107.6 MB 变成约 114 MB。原因是 PySide6 的打包工具会带上一批程序用不到的 Qt 组件（QML、Quick、PDF 等），后续版本会把它们排除掉。

- The installer grows from 107.6 MB to roughly 114 MB, because PySide6's packaging pulls in Qt components the app never touches (QML, Quick, PDF and friends). A later release will trim them out.

---

## 🛠️ Full Changelog
- refactor(gui): migrate every module from PyQt6 to PySide6
- build: swap the dependency, the PyInstaller spec and the documentation
- chore(version): bump the app version to 1.6.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。直接覆盖安装即可，所有设置、统计与谜题进度都会保留。

- No breaking changes. Install straight over the previous version; every setting, statistic and puzzle progress is preserved.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.5.4...v1.6.0

SHA-256: `5774D732C4C3A5D3ACB262C894922D33DE894AEEAFF95D704C4A93841FF71F19`

# v1.5.0 - One-Click Installer

> **Archived**
>
> This is an early development build. Only the source archive is kept; the installer is no longer available for download.

---

> This release changes how you get CheckPause: no more unzipping a folder — run a single installer instead. It sets up desktop and Start Menu shortcuts for you, shows a Simplified Chinese interface, and never asks for administrator rights. CheckPause now also looks for new releases in the background and tells you when one is available.

---

## 🎯 What's New

### 📦 Single-file installer
- 发布物从「一个需要解压的文件夹」变成单个 `CheckPause_Setup_<版本>.exe`：双击、下一步、完成，自动创建桌面快捷方式与开始菜单项，并在「应用和功能」中注册卸载入口。

- The release is now a single `CheckPause_Setup_<version>.exe` instead of a folder you have to unzip: double-click, Next, Finish. It creates desktop and Start Menu shortcuts and registers an uninstall entry in Apps & features.

### 🔔 Update notifications
- 启动后会在后台静默检查是否有新版本，有则提示并提供下载入口；检查过程不阻塞界面，处于离线状态或已是最新版时完全不打扰用户。对某个版本选择「稍后」后，不会再就同一版本重复提示。

- CheckPause now looks for a newer release quietly in the background and offers a download link when one is found. The check never blocks the UI, stays silent when offline or already up to date, and a version dismissed with "Later" is not asked about again.

### 🇨🇳 Chinese installer interface
- 安装界面使用 Inno Setup 官方简体中文语言包，中文系统的用户会自动预选中文，同时保留英文界面。

- The installer uses Inno Setup's official Simplified Chinese language file and preselects Chinese on Chinese systems, with English still available.

### 🔓 No administrator rights
- 安装到当前用户目录，全程不弹出 UAC 提权窗口，非管理员账户也能正常安装。

- Installs into the current user's directory and never shows a UAC elevation prompt, so non-administrator accounts can install it too.

### 🚧 Installs only where it can run
- Windows 10 以下的系统会在安装前直接拒绝并给出明确提示，而不是装完之后启动崩溃（Qt6 需要 Windows 10 或更高版本）。

- On systems older than Windows 10 the installer refuses up front with a clear message, instead of installing something that then crashes on launch (Qt6 requires Windows 10 or later).

### ⚙️ One command builds both
- `.\build_exe.ps1` 现在会依次完成 PyInstaller 打包与安装包编译，版本号自动读取 `checkpause/__init__.py`，不再需要手工同步；便携版仍照常生成。

- `.\build_exe.ps1` now runs PyInstaller and the installer compiler in sequence, reading the version from `checkpause/__init__.py` so nothing has to be kept in sync by hand; the portable build is still produced as before.

---

## 🛠️ Full Changelog
- feat(packaging): add an Inno Setup script producing a single-file installer
- feat(packaging): ship the official Simplified Chinese installer language file
- feat(packaging): install per-user so no UAC prompt is required
- feat(update): notify the user when a newer release is available
- feat(update): read a version manifest from a CDN mirror with a fallback source
- build: emit both the portable folder and the installer from build_exe.ps1
- build: read the release version from APP_VERSION instead of hardcoding it
- docs: document the packaging outputs and Inno Setup requirement
- chore(gitignore): ignore Inno Setup output and further local caches
- chore(version): bump the app version to 1.5.0

---

## ⚠️ Breaking Changes

- 分发方式变更：发布物由 `CheckPause-v1.4.x-windows-x64.zip` 变为 `CheckPause_Setup_1.5.0.exe`。老用户手里已解压的文件夹仍可继续使用，但今后只提供安装包。

- Distribution changed: the release artifact is now `CheckPause_Setup_1.5.0.exe` instead of `CheckPause-v1.4.x-windows-x64.zip`. Folders already unzipped by existing users keep working, but only the installer will be published from now on.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.4.1...v1.5.0

# v1.4.0 - Puzzle Progress and Quick Jump

> **Archived**
>
> This is an early development build. Only the source archive is kept; the installer is no longer available for download.

---

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

## 🛠️ Full Changelog
- feat(puzzle): remember solved puzzles and resume automatically
- feat(puzzle): add a jump box between previous/next
- refactor(puzzle): show puzzle details under the selected collection
- chore(version): bump the app version to 1.4.0

---

## ⚠️ Breaking Changes

- 无破坏性变更。

- No breaking changes.

---

**Full Changelog**: https://github.com/Comet-zzz/CheckPause/compare/v1.3.3...v1.4.0

# v1.3.0 - Puzzles and Importable Collections

> **Archived**
>
> This is an early development build. Only the source archive is kept; the installer is no longer available for download.

---

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

# v1.2.0 - Play Against the Computer

> **Archived**
>
> This is an early development build. Only the source archive is kept; the installer is no longer available for download.

---

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

# v1.1.0 - Module Rail and Close Confirmation

> **Archived**
>
> This is an early development build. Only the source archive is kept; the installer is no longer available for download.

---

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
