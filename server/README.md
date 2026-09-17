# CheckPause Server

客户端在 `checkpause/`，这里是**服务端**。两者互不影响。

## 当前进度

| 阶段 | 内容 | 状态 |
| --- | --- | --- |
| ① | 服务能跑起来、外网能访问 | ✅ 本次完成 |
| ② | 拼提示词 → 调 DeepSeek → 流式返回 | 待做 |
| ③ | 账号 + 积分 + 充值 | 待做 |

**这一版只有两个接口，没有任何业务逻辑**，目的是先把"代码 → 服务器 → nginx → 外网"这条链路验证通。链路通了之后再加业务代码，出问题时就只可能是业务问题，不会和部署问题混在一起。

| 接口 | 用途 |
| --- | --- |
| `GET /` | 给人看的：浏览器打开就是它 |
| `GET /health` | 给机器看的：以后监控用 |

## 目录

```
server/
├── app.py                      # 服务本体（目前只有状态页）
├── requirements.txt            # 依赖
├── test_app.py                 # 自测
├── README.md                   # 本文件
└── deploy/
    ├── install.sh              # 一键部署脚本
    ├── checkpause.service      # systemd：开机自启 + 崩溃自动重启
    └── nginx-checkpause.conf   # nginx：把 80 端口转给 app
```

## 本地自测

在仓库根目录执行：

```powershell
.venv\Scripts\python.exe -m unittest server.test_app -v
```

## 部署

服务端跑在阿里云 Ubuntu 24.04 上（首尔，免备案）。

**首次：**

```bash
git clone https://github.com/Comet-zzz/CheckPause.git /srv/checkpause
bash /srv/checkpause/server/deploy/install.sh
```

**以后每次更新：**

```bash
bash /srv/checkpause/server/deploy/install.sh
```

脚本会把代码 `git pull` 到最新、刷新虚拟环境、重启服务，**重复执行是安全的**。

## 服务器上的位置

| 东西 | 在哪 |
| --- | --- |
| 代码 | `/srv/checkpause` |
| Python 环境 | `/srv/checkpause/.venv` |
| 服务单元 | `/etc/systemd/system/checkpause.service` |
| nginx 站点 | `/etc/nginx/sites-available/checkpause` |

**常用命令：**

```bash
systemctl status checkpause      # 看服务活着没
systemctl restart checkpause     # 重启
journalctl -u checkpause -n 50   # 看最近 50 行日志
```

## 为什么要 nginx + app 两层

app 只监听 `127.0.0.1:8000`，**外网碰不到它**；nginx 监听 `80`，把请求转给 app。

好处是防火墙只需要开 80 和 443，app 本身不直接暴露。以后加 HTTPS 也只动 nginx 一层。

## 还没做的安全项

- 服务以 `checkpause` 用户运行（不是 root），但该用户有 `/home` 目录，暂未收紧
- 还没上 HTTPS（需要域名）
- 还没有接口鉴权——第 ③ 阶段加账号时一起做

## 第 ② 阶段要加什么

新增 `POST /v1/analyze`：

1. 客户端发来棋谱 + 引擎数据
2. **服务端**拼提示词（提示词永远不下发到客户端）
3. 调 DeepSeek，流式回传
4. 把「好的提示词」放在服务器上的独立文件里，**不进这个公开仓库**
