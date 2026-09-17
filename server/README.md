# CheckPause Server

客户端在 `checkpause/`，这里是**服务端**。两者互不影响。

## 当前进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| ① | 服务能跑起来、外网能访问 | ✅ |
| ② | 拼提示词 → 调 DeepSeek → 流式返回 | ✅ 本次完成 |
| ③ | 账号 + 积分 + 充值 | 待做 |

## 接口

| 接口 | 用途 |
| --- | --- |
| `GET /` | 状态页：版本、运行时长、**提示词是否已安装**、**密钥是否已配置** |
| `GET /health` | 给监控用 |
| `POST /v1/analyze` | 接收棋谱与引擎数据，**在服务端拼提示词**，流式返回讲解 |

### POST /v1/analyze

请求：

```json
{
  "pgn": "1. e4 e5 2. Nf3 ...",
  "analysis": "e4: +0.31 best=Nf3; e5: -0.12 ...",
  "history": [
    { "role": "assistant", "content": "第一步已经讲过的内容" },
    { "role": "user", "content": "那第 5 步呢？" }
  ]
}
```

响应：`text/plain` 的流式片段（边生成边返回）。

**客户端不发送提示词** —— 它只给原始素材（棋谱、引擎数字、对话历史），提示词由服务端拼。

## 密钥与提示词放在哪

**都不在仓库里。** 默认读 `/etc/checkpause/`：

| 文件 | 内容 | 必需 |
| --- | --- | --- |
| `env` | `DEEPSEEK_API_KEY` 等环境变量，由 systemd 加载 | ✅ |
| `system_prompt.txt` | **调教好的系统提示词** | 建议 |
| `user_template.txt` | 包住棋谱与引擎数据的模板，用 `{pgn}` 和 `{analysis}` 占位 | 可选 |

**没装 `system_prompt.txt` 也能跑**，代码里有个朴素的占位版；状态页会显示 `"prompt": "placeholder"` 提醒你。

### 安装

```bash
# 密钥
install -m 640 -o checkpause -g checkpause \
    /etc/checkpause/env.example /etc/checkpause/env
nano /etc/checkpause/env          # 填入 DEEPSEEK_API_KEY

# 调教好的提示词（手工创建，永远不进 git）
nano /etc/checkpause/system_prompt.txt

systemctl restart checkpause
```

> ⚠️ **`system_prompt.txt` 是这个项目最值钱的东西，绝对不要提交进仓库。**
> 仓库是公开的，一提交就永久公开。改完提示词只需 `systemctl restart checkpause`，
> **不用重新打包客户端** —— 这正是把提示词放服务端的意义。

## 目录

```
server/
├── app.py                      # 路由：状态页、健康检查、/v1/analyze
├── config.py                   # 读 /etc/checkpause 下的密钥与提示词
├── prompting.py                # 在服务端拼消息（含历史轮数限制）
├── deepseek.py                 # 流式调用上游模型
├── requirements.txt
├── test_app.py / test_analyze.py
└── deploy/
    ├── install.sh              # 一键部署（幂等）
    ├── checkpause.service      # systemd
    ├── nginx-checkpause.conf   # nginx
    └── env.example             # env 模板
```

## 本地自测

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -m unittest server.test_app server.test_analyze -v
```

想本地跑起来看看：

```powershell
$env:CHECKPAUSE_CONFIG_DIR = "$PWD\server\deploy"
.venv\Scripts\python.exe -m uvicorn server.app:app --port 8000
```

没配 `DEEPSEEK_API_KEY` 时，状态页会显示 `"upstream_configured": false`，`/v1/analyze` 返回 502。

## 部署

```bash
# 首次
git clone https://github.com/Comet-zzz/CheckPause.git /srv/checkpause
bash /srv/checkpause/server/deploy/install.sh

# 以后每次更新
bash /srv/checkpause/server/deploy/install.sh
```

脚本会 `git pull`、刷新 venv、重建配置目录、重装 unit、重启服务，**重复执行安全**。

## 服务器上的位置

| 东西 | 在哪 |
| --- | --- |
| 代码 | `/srv/checkpause` |
| Python 环境 | `/srv/checkpause/.venv` |
| **密钥与提示词** | **`/etc/checkpause/`** |
| 服务单元 | `/etc/systemd/system/checkpause.service` |
| nginx 站点 | `/etc/nginx/sites-available/checkpause` |

```bash
systemctl status checkpause      # 活着没
journalctl -u checkpause -n 50   # 日志
systemctl restart checkpause     # 重启（改完提示词用它）
```

## 关于鉴权

`CHECKPAUSE_ACCESS_TOKEN` 是**临时措施**：设了之后请求必须带 `X-CheckPause-Token` 头。

它**不是真安全** —— 客户端是桌面包，密钥终究能被扒出来。它的作用只是**挡掉扫描器和顺手白嫖**。

第 ③ 阶段做账号系统时会用真正的鉴权替换掉它。

## 第 ③ 阶段要加什么

账号、积分账本、充值。需要补的坑（预扣+结算、流式中断兜底、原子扣费、价格版本号等）
见仓库根目录 `AGENTS.md` 的「积分方案」一节。
