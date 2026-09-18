# CheckPause Server

客户端在 `checkpause/`，这里是**服务端**。两者互不影响。

## 当前进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| ① | 服务能跑起来、外网能访问 | ✅ |
| ② | 拼提示词 → 调上游模型 → 流式返回 | ✅ |
| ③ | 账号 + 积分 + 充值 | ✅ 沙箱 + **生产真付均已通过** |
| ④ | 公网 HTTPS `notify_url` / 域名 | ⬜ 靠交易查询兜底，能到账 |

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
| `env` | `UPSTREAM_API_KEY` 等环境变量，由 systemd 加载 | ✅ |
| `system_prompt.txt` | **调教好的系统提示词** | 建议 |
| `user_template.txt` | 包住棋谱与引擎数据的模板，用 `{pgn}` 和 `{analysis}` 占位 | 可选 |

**没装 `system_prompt.txt` 也能跑**，代码里有个朴素的占位版；状态页会显示 `"prompt": "placeholder"` 提醒你。

### 安装

```bash
# 密钥
install -m 640 -o checkpause -g checkpause \
    /etc/checkpause/env.example /etc/checkpause/env
nano /etc/checkpause/env          # 填入 UPSTREAM_API_KEY

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
├── upstream.py                 # 流式调用上游模型
├── requirements.txt
├── test_app.py / test_analyze.py
└── deploy/
    ├── install.sh                         # 一键部署（幂等）
    ├── checkpause.service                 # systemd
    ├── checkpause-version-refresh.service # 刷新版本清单（oneshot）
    ├── checkpause-version-refresh.timer   # 每 2 分钟触发一次
    ├── refresh-version-json.sh            # 拉 version.json 到 /srv/downloads
    ├── nginx-checkpause.conf              # nginx
    └── env.example                        # env 模板
```

## 本地自测

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -m unittest server.test_app server.test_analyze -v
```

想本地跑起来看看：

```powershell
$env:CHECKPAUSE_CONFIG_DIR = "$PWD\server\deploy"
$env:CHECKPAUSE_DB = "$env:TEMP\checkpause-dev.db"
.venv\Scripts\python.exe -m uvicorn server.app:app --port 8000
```

`CHECKPAUSE_DB` **在 Windows 上必须设**：默认值是 Linux 的
`/var/lib/checkpause/checkpause.db`，不设的话本地会去建一个 `D:\var\lib\...`。

没配 `UPSTREAM_API_KEY` 时，状态页会显示 `"upstream_configured": false`，`/v1/analyze` 返回 502。

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
| **积分账本（SQLite）** | **`/var/lib/checkpause/checkpause.db`** |
| 服务单元 | `/etc/systemd/system/checkpause.service` |
| 版本清单刷新 | `/etc/systemd/system/checkpause-version-refresh.{service,timer}` |
| **版本清单文件** | **`/srv/downloads/version.json`**（nginx 在 `/version.json` 发出去） |
| 安装包镜像目录 | `/srv/downloads/` |
| nginx 站点 | `/etc/nginx/sites-available/checkpause` |

```bash
systemctl status checkpause      # 活着没
journalctl -u checkpause -n 50   # 日志
systemctl restart checkpause     # 重启（改完提示词用它）
```

### 版本清单镜像（客户端检查更新用的）

客户端先请求 `http://43.108.99.244/version.json`，nginx 直接发
`/srv/downloads/version.json`。这个文件由 `checkpause-version-refresh.timer`
每 2 分钟从 GitHub 拉一次（原子替换，失败保留旧文件）。

```bash
systemctl list-timers checkpause-version-refresh.timer   # 下次什么时候跑
systemctl status checkpause-version-refresh.service      # 上次成功没
curl -s http://127.0.0.1/version.json                    # 现在发的是哪一版
```

**发新版后确认一下**：这个文件停在旧版本时，手动检查更新会信它，
于是"发了新版但没人收到提示"（v1.6.1 那个 bug 的翻版）。

## 账号与积分

请求必须带 `Authorization: Bearer <token>`，token 来自注册或登录：

```bash
curl -s http://127.0.0.1:8000/v1/accounts/register \
     -H 'Content-Type: application/json' \
     -d '{"username":"player","password":"hunter22"}'
```

| 接口 | 作用 |
| --- | --- |
| `POST /v1/accounts/register` | 注册，返回 token |
| `POST /v1/accounts/login` | 登录，返回 token |
| `POST /v1/accounts/logout` | 让当前 token 失效 |
| `GET /v1/accounts/me` | 余额 |
| `GET /v1/accounts/ledger` | 自己的流水 |

`POST /v1/analyze` 的收费流程是**预扣 → 结算**：

1. 按输入长度和输出上限估一个预扣额，**原子地**从余额里划走（余额不够直接 402）
2. 调上游，流式返回
3. 拿到 `usage` 后按真实 token 结算，多退少补
4. **流中断拿不到 `usage` 时按预扣结算**，不白送；上游拒单则全额退还

单价在 `server/pricing.py`，改完记得**同时改 `PRICE_VERSION`** —— 每条流水都记着当时的价格版本号。

### 管理员操作

没有 HTTP 后台，只能在服务器上跑（这是故意的：多一个 URL 就多一个要被攻破的东西）：

```bash
cd /srv/checkpause
.venv/bin/python -m server.admin users
.venv/bin/python -m server.admin show player
.venv/bin/python -m server.admin add-credits player 1000 --note "微信转账"
.venv/bin/python -m server.admin grant player 100 --note "补偿"
.venv/bin/python -m server.admin set-password player
.venv/bin/python -m server.admin sweep
```

`add-credits` 记的是**真实收款**，所以会触发首充福利；`grant` 不会。
加错两次就用 `grant <用户名> -1000` 冲回来 —— 账本是只增不改的，纠正靠反向流水。

**备份**：`/var/lib/checkpause/checkpause.db` 里是全部余额和密码哈希，丢了就全没了。

## 支付（支付宝 AI 网页应用收款）

桌面客户端不需要变成网页应用：它只用浏览器打开 `/pay/{order_id}`，那一页由本服务渲染
支付宝签名好的表单。**付款成功以验签通知或 `alipay.trade.query` 为准**，同步回跳不算数。

| 文件 | 作用 |
| --- | --- |
| `alipay.py` | 下单表单（`page_execute`）/ 通知验签 / 查单 / 退款 / 退款查询 / 关单 |
| `payments.py` | 价格挡位、订单、付款页、`/v1/pay/notify`、`/v1/pay/return`、状态端点 |
| `store.py` | `orders` 表 + `mark_order_paid`（幂等入账） |

配置读 `/etc/checkpause/env`：

```
AIPAY_APP_ID / AIPAY_PRIVATE_PKCS_KEY / AIPAY_ALIPAY_PUBLIC_KEY / AIPAY_GATEWAY
AIPAY_NOTIFY_URL / AIPAY_RETURN_URL / AIPAY_SELLER_ID   # 都可留空
```

- **`AIPAY_PRIVATE_PKCS_KEY` 必须是 PKCS#1（控制台标"非 JAVA 语言私钥"）**；
  塞 Java 的 PKCS#8 会在签名时报 `int() argument must be ... not 'Sequence'`
- 没有公网 HTTPS 时**省略** `notify_url`（不要传占位 URL），靠交易查询兜底
- 沙箱网关 `https://openapi-sandbox.dl.alipaydev.com/gateway.do`，
  生产 `https://openapi.alipay.com/gateway.do`

**2026-09-18 生产真付一笔 ¥1 成功入账**（交易号 `2026091822001471611438397651`）。
剩下的只是补公网 HTTPS `notify_url`，让到账更即时。

开单（客户端发版前用这个收款，比手动加积分好）：

```bash
.venv/bin/python -m server.admin open-order <用户名> <元>
```
