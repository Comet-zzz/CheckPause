# ♟️ CheckPause

将博弈树搜索与自然语言生成相结合的国际象棋分析工具，帮助棋手理解自己的决策偏差。

[![downloads](https://img.shields.io/github/downloads/Comet-zzz/CheckPause/total?style=for-the-badge&label=downloads&color=blue)](https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.0/CheckPause_Setup_1.7.0.exe)
[![license](https://img.shields.io/badge/license-Proprietary-lightgrey?style=for-the-badge)](LICENSE)
[![中文](https://img.shields.io/badge/%E4%B8%AD%E6%96%87-blue?style=for-the-badge)](README.zh-CN.md)
[![English](https://img.shields.io/badge/English-gray?style=for-the-badge)](README.md)

CheckPause 使用本地 Stockfish 评估每一步，再由任意 OpenAI 兼容的大模型把引擎数据翻译成自然语言讲解，并配有可点击的着法列表、自绘棋盘、表现评级与成长档案。

---

## ✨ 功能特性

- **PySide6 桌面界面**：左侧棋盘，右侧「导入 / 分析 / 统计」三个标签页，中英文界面随时切换。
- **本地引擎分析**：Stockfish 逐步计算评分与最佳着法，进度实时显示、可随时停止；Polyglot 开局谱库自动识别谱着并跳过引擎计算。
- **AI 自然语言讲解**：基于引擎数据流式回答，可像和教练对话一样追问「为什么这步更好？」，兼容 DeepSeek、OpenAI、OpenRouter 及本地模型。
- **可点击着法列表**：点击任意着法跳转局面并高亮当前步，分析过程中高亮随进度移动；支持翻转棋盘与引擎最佳着法箭头。
- **人机对弈**：侧栏「对弈」模块可直接与 Stockfish 下棋，点击走子、执白/执黑、100–3000 分难度滑条（1320 分以上由引擎 Elo 限制器标定）、多种计时模式（1+0 到 30+0，含加秒与无限制）、可选开局与残局、悔棋、认输、升变选择与棋步回看，并可一键把整盘棋送入分析；对局开始后设置项自动锁定，点「新对局」即可重新调整。
- **谜题训练**：在「对弈」与「分析」之间新增谜题模块，内置一份 Lichess 精选样例可直接练手，也可导入自己的开源题集（Lichess CSV、含 FEN 的 PGN）；支持走对继续、走错提示、提示箭头与难度/主题展示；「收藏夹」会自动收录你点过「收藏」或答错的题目，导入大题库时按需惰性读取。
- **表现评级与成长档案**：五档评级（卓越 / 精准 / 稳健 / 平均 / 欠考虑），统计页记录每盘棋的准确度与历史趋势。
- **个性化外观**：10 套 Lichess 开源棋子、6 种棋盘配色、明暗主题，选择即时生效并持久化。
- **隐私优先**：棋谱与 API Key 只保存在本机，分析不依赖云端。

---

## 🚀 快速开始

### Windows 用户

1. 从文末「下载」获取 `CheckPause_Setup_1.7.0.exe`；
2. 双击运行安装包，按提示完成安装（无需管理员权限，可勾选创建桌面快捷方式）；
3. 从桌面或开始菜单启动 CheckPause，首次使用会要求设置用户名和界面语言；
4. 打开「设置 → API 设置...」填写 API Key（默认 DeepSeek，可改成任意 OpenAI 兼容接口）；
5. 在「导入」页粘贴 PGN 或打开文件，点击「开始分析」，完成后切到「分析」页向 AI 提问。

> 没有配置 API 也能正常分析和看棋，只是 AI 对话不可用。

---

## ⚙️ 配置与数据

- 应用内「设置 → API 设置...」可配置 **API Key**、**接口地址（Base URL）** 与 **模型名称**；默认 `https://api.deepseek.com` + `deepseek-flash`，留空自动回退默认值。
- 用户数据保存在 `%APPDATA%\CheckPause\`：`profile.json`（用户名、语言、主题、外观、历史记录）与 `settings.json`（API 配置），旧版一并迁移。

---

## 🙏 致谢

- 棋子来自 Lichess 开源棋子集（cburnett、merida、chessnut、fantasy、spatial、celtic、kiwen-suwi、rhosgfx、totoy、mpchess），版权归各作者所有，遵循 GPLv2+ / Apache-2.0 / MIT / CC BY / CC0 等许可。
- 引擎为 [Stockfish](https://stockfishchess.org/)（GPLv3），开局库由公开开局线路编译。
- 安装包由 [Inno Setup](https://jrsoftware.org/isinfo.php) 生成，并使用其官方简体中文语言包（`installer/languages/ChineseSimplified.isl`，维护者 Zhenghan Yang）。
- 许可：CheckPause 为**专有软件**，版权所有 (C) 2026 CometZZZ，保留所有权利，详见 [LICENSE](LICENSE)；**v1.6.1 及更早版本仍按其发布时的 GPLv3 授权**。内置组件沿用各自原有许可——Stockfish 为 GPLv3（源码可从 https://stockfishchess.org/download/ 获取），棋子集遵循上述各自许可。

---

## ⬇️ 下载

**最新版：CheckPause v1.7.0（Windows x64）**

- 🚀 **国内加速下载（推荐）**：[CheckPause_Setup_1.7.0.exe](http://43.108.99.244/download/CheckPause_Setup_1.7.0.exe) — 同一份文件放在国内能稳定连上的服务器上，通常几十秒下完
- 📦 [GitHub 下载](https://github.com/Comet-zzz/CheckPause/releases/download/v1.7.0/CheckPause_Setup_1.7.0.exe)（114.5 MB，已内置 Stockfish、开局库、棋子资源与 Lichess 精选题集）
- SHA-256：`5CA34298B9D1D328848FDCC5CE50AAE7EDACD1452167332D35855CDC020F9E3B`（两个链接是同一个文件，哈希一致）
- 双击运行安装包即可，安装后从桌面或开始菜单启动；程序未签名，若 Windows SmartScreen 提示，请选择「更多信息 → 仍要运行」。
- 全部版本：https://github.com/Comet-zzz/CheckPause/releases

---

[English README](README.md)
