# ♟️ CheckPause

将博弈树搜索与自然语言生成相结合的国际象棋分析工具，帮助棋手理解自己的决策偏差。

A chess analysis tool that combines game-tree search with natural language generation to help players understand their own decision-making biases.

CheckPause 使用本地 Stockfish 评估每一步，再由任意 OpenAI 兼容的大模型把引擎数据翻译成自然语言讲解，并配有可点击的着法列表、自绘棋盘、表现评级与成长档案。

CheckPause evaluates every move with a local Stockfish engine, then lets any OpenAI-compatible model explain the engine data in plain language, alongside a clickable move list, a custom-drawn board, performance ratings, and a personal growth profile.

---

## ✨ 功能特性 / Features

- **PyQt6 桌面界面**：左侧棋盘，右侧「导入 / 分析 / 统计」三个标签页，中英文界面随时切换。  
  PyQt6 desktop app: the board on the left, with Import / Analysis / Statistics tabs, in Chinese or English.
- **本地引擎分析**：Stockfish 逐步计算评分与最佳着法，进度实时显示、可随时停止；Polyglot 开局谱库自动识别谱着并跳过引擎计算。  
  Local engine analysis: Stockfish scores every move with progress and stop support; a Polyglot opening book detects book moves and skips engine work.
- **AI 自然语言讲解**：基于引擎数据流式回答，可像和教练对话一样追问「为什么这步更好？」，兼容 DeepSeek、OpenAI、OpenRouter 及本地模型。  
  AI explanations: streamed answers based on engine data, with follow-up questions like a real coach; works with DeepSeek, OpenAI, OpenRouter, and local models.
- **可点击着法列表**：点击任意着法跳转局面并高亮当前步，分析过程中高亮随进度移动；支持翻转棋盘与引擎最佳着法箭头。  
  Clickable move list: jump to any position and highlight the current ply; the board also shows engine best-move arrows and can be flipped.
- **人机对弈**：侧栏「对弈」模块可直接与 Stockfish 下棋，点击走子、执白/执黑、五档难度、悔棋、认输、升变选择与棋步回看，并可一键把整盘棋送入分析。  
  Play against the computer: the Play module takes on Stockfish with click-to-move, White/Black, five difficulty levels, undo, resign, promotion picking, and move review — plus one-click send to analysis.
- **表现评级与成长档案**：五档评级（卓越 / 精准 / 稳健 / 平均 / 欠考虑），统计页记录每盘棋的准确度与历史趋势。  
  Performance ratings and profile: five tiers (Optimal / Precise / Competent / Steady / Volatile) plus per-game accuracy history on the Statistics tab.
- **个性化外观**：10 套 Lichess 开源棋子、6 种棋盘配色、明暗主题，选择即时生效并持久化。  
  Personalization: 10 Lichess piece sets, 6 board themes, and light/dark modes, applied instantly and saved.
- **隐私优先**：棋谱与 API Key 只保存在本机，分析不依赖云端。  
  Privacy first: your games and API keys stay on your machine; analysis never depends on the cloud.

---

## 🚀 快速开始 / Quick Start

### Windows 用户 / Windows users

1. 从文末「下载」获取 `CheckPause-v1.2.0-windows-x64.zip`；  
   Get `CheckPause-v1.2.0-windows-x64.zip` from the Download section at the end of this file.
2. 解压到任意目录（请解压整个文件夹，Stockfish、开局库和棋子资源都在里面）；  
   Unzip the whole folder — Stockfish, the opening book, and piece assets are bundled inside.
3. 双击 `CheckPause.exe` 启动，首次使用会要求设置用户名和界面语言；  
   Run `CheckPause.exe`; first launch asks for a username and interface language.
4. 打开「设置 → API 设置...」填写 API Key（默认 DeepSeek，可改成任意 OpenAI 兼容接口）；  
   Open Settings → API settings... and enter an API key (DeepSeek by default; any OpenAI-compatible endpoint works).
5. 在「导入」页粘贴 PGN 或打开文件，点击「开始分析」，完成后切到「分析」页向 AI 提问。  
   Paste or open a PGN on the Import tab, click Analyze, then ask questions on the Analysis tab.

> 没有配置 API 也能正常分析和看棋，只是 AI 对话不可用。  
> Analysis and board features work without an API key; only AI chat needs one.

### 从源码运行 / Run from source

要求 Python 3.10+。

```powershell
git clone https://github.com/Comet-zzz/CheckPause.git
cd CheckPause
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run_gui.py
```

源码运行时需要自行准备 Stockfish（发布包中已内置）：

- 从 https://stockfishchess.org/download/ 下载对应平台版本；
- 放到 `stockfish\stockfish\stockfish-windows-x86-64-universal.exe`，或在 `.env` 中配置 `STOCKFISH_PATH`。

API Key 可以在应用内填写，也可以复制 `.env.example` 为 `.env`：

```env
DEEPSEEK_API_KEY = "sk-your-api-key-here"
STOCKFISH_PATH = "C:/your/path/to/stockfish.exe"
```

### 命令行版本 / CLI

原有命令行流程仍然保留：

```powershell
python run_cli.py        # 或 python -m cli.main
```

粘贴 PGN → Stockfish 分析 → 终端内与 AI 连续对话；支持 `/language` 切换语言、`clear` 清除用户数据。

The original CLI flow is still available: paste a PGN, analyze it with Stockfish, and chat with the AI in the terminal (`/language` switches languages, `clear` deletes user data).

---

## ⚙️ 配置与数据 / Configuration and data

- 应用内「设置 → API 设置...」可配置 **API Key**、**接口地址（Base URL）** 与 **模型名称**；默认 `https://api.deepseek.com` + `deepseek-flash`，留空自动回退默认值。  
  Settings → API settings... configures the API key, base URL, and model name; defaults to `https://api.deepseek.com` + `deepseek-flash`.
- 用户数据保存在 `%APPDATA%\CheckPause\`：`profile.json`（用户名、语言、主题、外观、历史记录）与 `settings.json`（API 配置），旧版一并迁移。  
  User data lives in `%APPDATA%\CheckPause\`: `profile.json` (username, language, theme, appearance, history) and `settings.json` (API config); legacy profiles migrate automatically.

---

## 🧱 项目结构 / Project structure

```
run_gui.py / run_cli.py        # GUI / CLI 入口
checkpause/
  config.py  resources.py  assets.py
  core/      engine.py  ai.py  rating.py
  data/      paths.py  settings.py  profile.py
  i18n/      zh_CN.py  en_US.py
  gui/       main_window.py  dialogs.py  theme.py  workers.py
             pages/    analysis_page.py  chat_page.py  stats_page.py  play_page.py  welcome_page.py
             widgets/  board_widget.py  move_list.py
cli/         main.py  chat_ui.py  input_handler.py  engine_cli.py
tests/       unittest 测试
tools/       build_openings.py
assets/      pieces/  openings.pgn  opening_book.bin
```

GUI 与 CLI 共用 `checkpause` 核心逻辑，互不依赖界面代码。

The GUI and CLI share the `checkpause` core logic and never depend on each other's UI code.

---

## 🧪 测试与打包 / Tests and packaging

```powershell
python -m unittest discover -s tests -v   # 单元测试
.\build_exe.ps1                            # 打包为 dist\CheckPause\CheckPause.exe
```

`CheckPause.spec` 会把 Stockfish、开局谱库与棋子资源一并打进发布目录。

`CheckPause.spec` bundles Stockfish, the opening book, and piece assets into the distribution folder.

---

## 🙏 致谢 / Credits

- 棋子来自 Lichess 开源棋子集（cburnett、merida、chessnut、fantasy、spatial、celtic、kiwen-suwi、rhosgfx、totoy、mpchess），版权归各作者所有，遵循 GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 等许可。  
  Pieces come from Lichess open-source piece sets, each owned by its author under GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 licenses.
- 引擎为 [Stockfish](https://stockfishchess.org/)（GPLv3），开局库由 `tools/build_openings.py` 从公开开局线路编译。  
  Engine: [Stockfish](https://stockfishchess.org/) (GPLv3); the opening book is compiled from public opening lines by `tools/build_openings.py`.

---

## ⬇️ 下载 / Download

**最新版 / Latest: CheckPause v1.2.0（Windows x64）**

- 📦 [CheckPause-v1.2.0-windows-x64.zip](https://github.com/Comet-zzz/CheckPause/releases/download/v1.2.0/CheckPause-v1.2.0-windows-x64.zip)（123.7 MB，已内置 Stockfish、开局库与棋子资源）
- SHA-256：`4196C54FEDC3BD1E23D5C60633F7D0E488ECB1EF0424DD8C29DD3660BB9BEE16`
- 解压后双击 `CheckPause.exe` 即可运行；程序未签名，若 Windows SmartScreen 提示，请选择「更多信息 → 仍要运行」。  
  Unzip and run `CheckPause.exe`. The build is unsigned; if SmartScreen appears, choose More info → Run anyway.
- 全部版本 / All releases：https://github.com/Comet-zzz/CheckPause/releases
