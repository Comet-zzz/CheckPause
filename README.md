# 🧠 CheckPause - 国际象棋AI教练 / Chess AI Coach

一个基于 Stockfish + DeepSeek 的本地国际象棋复盘工具，支持连续追问，像真人教练一样帮你拆解棋局。

A local chess analysis tool powered by Stockfish + DeepSeek. Upload a PGN and get natural-language coaching with unlimited follow-up questions.

---

## ✨ 功能特点 / Features

- **本地引擎分析**：使用 Stockfish 计算每一步的评分和最佳走法（不依赖网络）  
  Local analysis via Stockfish – no cloud dependency.
- **AI自然语言讲解**：基于引擎数据，用自然语言解释你的失误和亮点  
  AI explains every move in plain language, based on engine data.
- **连续追问**：像和教练对话一样，随时追问“为什么这步更好？”  
  Ask follow-up questions like "Why is this move better?" – just like a real coach.
- **用户成长档案**：记录每盘棋的准确度，追踪你的进步趋势  
  Personal profile that tracks accuracy over time – see your improvement.
- **完全本地运行**：你的棋谱和 API Key 只保存在本地，隐私安全  
  Everything runs locally – your games and keys stay private.

---

## 🚀 快速开始 / Quick Start

### 1. 下载 Stockfish 引擎 / Download Stockfish

Stockfish 是开源国际象棋引擎，负责计算评分和最佳走法。

Stockfish is the open-source chess engine that calculates evaluations and best moves.

- 访问官网 / Visit: https://stockfishchess.org/download/
- 下载对应你系统的版本（Windows / macOS / Linux）
- 解压到某个文件夹，记住路径

---

### 2. 获取 DeepSeek API Key / Get your DeepSeek API Key

DeepSeek 负责将引擎数据翻译成自然语言讲解。

DeepSeek translates engine data into conversational coaching.

- 访问平台 / Visit: https://platform.deepseek.com/
- 注册账号并创建 API Key
- 复制你的 Key（格式：`sk-...`）

---

### 3. 配置环境变量 / Configure Environment Variables

复制 `.env.example` 文件，重命名为 `.env`，然后填入你的信息。

Copy `.env.example`, rename it to `.env`, and fill in your own values.

```env
DEEPSEEK_API_KEY = "sk-你的密钥"
STOCKFISH_PATH = "C:/你的路径/stockfish.exe"