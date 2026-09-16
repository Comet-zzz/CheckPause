# ♟️ CheckPause

将博弈树搜索与自然语言生成相结合的国际象棋分析工具，帮助棋手理解自己的决策偏差。

[![release](https://img.shields.io/github/v/release/Comet-zzz/CheckPause?style=for-the-badge&label=release&color=blue)](https://github.com/Comet-zzz/CheckPause/releases/latest)
[![downloads](https://img.shields.io/github/downloads/Comet-zzz/CheckPause/total?style=for-the-badge&label=downloads&color=blue)](https://github.com/Comet-zzz/CheckPause/releases/download/v1.5.1/CheckPause_Setup_1.5.1.exe)
[![license](https://img.shields.io/badge/license-GPL--3.0-blue?style=for-the-badge)](LICENSE)
[![中文](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-blue?style=for-the-badge)](README.zh-CN.md)
[![English](https://img.shields.io/badge/English-gray?style=for-the-badge)](README.md)

CheckPause 使用本地 Stockfish 评估每一步，再由任意 OpenAI 兼容的大模型把引擎数据翻译成自然语言讲解，并配有可点击的着法列表、自绘棋盘、表现评级与成长档案。

---

## ✨ 功能特性

- **PyQt6 桌面界面**：左侧棋盘，右侧「导入 / 分析 / 统计」三个标签页，中英文界面随时切换。
- **本地引擎分析**：Stockfish 逐步计算评分与最佳着法，进度实时显示、可随时停止；Polyglot 开局谱库自动识别谱着并跳过引擎计算。
- **AI 自然语言讲解**：基于引擎数据流式回答，可像和教练对话一样追问「为什么这步更好？」，兼容 DeepSeek、OpenAI、OpenRouter 及本地模型。
- **可点击着法列表**：点击任意着法跳转局面并高亮当前步，分析过程中高亮随进度移动；支持翻转棋盘与引擎最佳着法箭头。
- **人机对弈**：侧栏「对弈」模块可直接与 Stockfish 下棋，点击走子、执白/执黑、100–3000 分难度滑条（1320 分以上由引擎 Elo 限制器标定）、多种计时模式（1+0 到 30+0，含加秒与无限制）、可选开局与残局、悔棋、认输、升变选择与棋步回看，并可一键把整盘棋送入分析。
- **谜题训练**：在「对弈」与「分析」之间新增谜题模块，内置一份 Lichess 精选样例可直接练手，也可导入自己的开源题集（Lichess CSV、含 FEN 的 PGN）；支持走对继续、走错提示、提示箭头、显示答案与难度/主题展示，导入大题库时按需惰性读取。
- **表现评级与成长档案**：五档评级（卓越 / 精准 / 稳健 / 平均 / 欠考虑），统计页记录每盘棋的准确度与历史趋势。
- **个性化外观**：10 套 Lichess 开源棋子、6 种棋盘配色、明暗主题，选择即时生效并持久化。
- **隐私优先**：棋谱与 API Key 只保存在本机，分析不依赖云端。

---

## 🚀 快速开始

### Windows 用户

1. 从文末「下载」获取 `CheckPause_Setup_1.5.1.exe`；
2. 双击运行安装包，按提示完成安装（无需管理员权限，可勾选创建桌面快捷方式）；
3. 从桌面或开始菜单启动 CheckPause，首次使用会要求设置用户名和界面语言；
4. 打开「设置 → API 设置...」填写 API Key（默认 DeepSeek，可改成任意 OpenAI 兼容接口）；
5. 在「导入」页粘贴 PGN 或打开文件，点击「开始分析」，完成后切到「分析」页向 AI 提问。

> 没有配置 API 也能正常分析和看棋，只是 AI 对话不可用。

### 从源码运行

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

### 命令行版本

原有命令行流程仍然保留：

```powershell
python run_cli.py        # 或 python -m cli.main
```

粘贴 PGN → Stockfish 分析 → 终端内与 AI 连续对话；支持 `/language` 切换语言、`clear` 清除用户数据。

---

## ⚙️ 配置与数据

- 应用内「设置 → API 设置...」可配置 **API Key**、**接口地址（Base URL）** 与 **模型名称**；默认 `https://api.deepseek.com` + `deepseek-flash`，留空自动回退默认值。
- 用户数据保存在 `%APPDATA%\CheckPause\`：`profile.json`（用户名、语言、主题、外观、历史记录）与 `settings.json`（API 配置），旧版一并迁移。

---

## 🧱 项目结构

```
run_gui.py / run_cli.py        # GUI / CLI 入口
checkpause/
  config.py  resources.py  assets.py
  core/      engine.py  ai.py  rating.py  puzzle.py  play_session.py  openings.py  endgames.py
  data/      paths.py  settings.py  profile.py  puzzles.py
  i18n/      zh_CN.py  en_US.py
  gui/       main_window.py  dialogs.py  theme.py  workers.py
             pages/    analysis_page.py  chat_page.py  stats_page.py  play_page.py  puzzle_page.py  welcome_page.py
             widgets/  move_list.py  module_rail.py  board/widget.py  board/canvas.py  board/promo.py  board/constants.py
cli/         main.py  chat_ui.py  input_handler.py  engine_cli.py
tests/       unittest 测试
tools/       build_openings.py  build_puzzles.py
assets/      pieces/  puzzles/  openings.pgn  opening_book.bin
```

GUI 与 CLI 共用 `checkpause` 核心逻辑，互不依赖界面代码。

---

## 🧪 测试与打包

```powershell
python -m unittest discover -s tests -v   # 单元测试
.\build_exe.ps1                            # 便携目录 + 单文件安装包
```

打包需要 [Inno Setup 6.3+](https://jrsoftware.org/isdl.php)：`winget install JRSoftware.InnoSetup`

若提示"禁止运行脚本"，改用：`powershell -ExecutionPolicy Bypass -File .\build_exe.ps1`

`CheckPause.spec` 会把 Stockfish、开局谱库与棋子资源一并打进 `dist\CheckPause\`，`installer\CheckPause.iss` 再把整个目录编译成一个安装包。版本号自动读取 `checkpause\__init__.py` 中的 `APP_VERSION`。

产出：

| 产物 | 用途 |
| --- | --- |
| `dist\CheckPause_Setup_<版本>.exe` | **安装包，发给用户的那个文件** |
| `dist\CheckPause\CheckPause.exe` | 便携版（安装包的中间产物，需连同整个文件夹一起分发） |

### 发布新版本

1. 修改 `checkpause/__init__.py` 的 `APP_VERSION` 与 `version_info.txt`，并在 `Changelog.md` 顶部新增一节；
2. 运行 `.\build_exe.ps1`，得到 `dist\CheckPause_Setup_<版本>.exe`；
3. 在 GitHub 上创建 Release 并上传该安装包；
4. **更新仓库根目录的 `version.json`**，把 `latest` 与 `url` 指向新版本；
5. 同步更新 `README.md` 与 `README.zh-CN.md` 里的版本号、安装包直链与 SHA-256——downloads 徽章与文末「下载」段落都直接指向 `.exe`，必须跟着换到新文件。

客户端启动约 2.5 秒后会读取 `version.json`（依次尝试 jsDelivr 与 raw.githubusercontent），发现更高版本就提示用户。**第 4 步忘了做，老用户就收不到更新提示**——安装包已经传上去但没人知道。

---

## 🙏 致谢

- 棋子来自 Lichess 开源棋子集（cburnett、merida、chessnut、fantasy、spatial、celtic、kiwen-suwi、rhosgfx、totoy、mpchess），版权归各作者所有，遵循 GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 等许可。
- 引擎为 [Stockfish](https://stockfishchess.org/)（GPLv3），开局库由 `tools/build_openings.py` 从公开开局线路编译。
- 安装包由 [Inno Setup](https://jrsoftware.org/isinfo.php) 生成，并使用其官方简体中文语言包（`installer/languages/ChineseSimplified.isl`，维护者 Zhenghan Yang）。
- 许可：CheckPause 以 [GNU 通用公共许可证 v3.0](LICENSE) 发布，版权所有 (C) 2026 CometZZZ；内置组件沿用各自原有许可——Stockfish 为 GPLv3（源码可从 https://stockfishchess.org/download/ 获取），棋子集遵循上述各自许可。

---

## ⬇️ 下载

**最新版：CheckPause v1.5.1（Windows x64）**

- 📦 [CheckPause_Setup_1.5.1.exe](https://github.com/Comet-zzz/CheckPause/releases/download/v1.5.1/CheckPause_Setup_1.5.1.exe)（107.6 MB，已内置 Stockfish、开局库、棋子资源与 Lichess 精选题集）
- SHA-256：`5351A037CD0537E789D8A69586E38209A67D7E9F14C29A6FBA56FC0C9D7A47D7`
- 双击运行安装包即可，安装后从桌面或开始菜单启动；程序未签名，若 Windows SmartScreen 提示，请选择「更多信息 → 仍要运行」。
- 全部版本：https://github.com/Comet-zzz/CheckPause/releases

---

[English README](README.md)
