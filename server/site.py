"""The public pages: what CheckPause is, and what it costs.

They exist because Alipay's onboarding wants screenshots of a shop, and before
this there was nothing to photograph on this server except an API status blob.

The price list is rendered from the same pack list the payment endpoints use,
so a price change cannot leave the shop page advertising something else. There
is deliberately no JavaScript: a page whose only job is to be read should render
the same for a reviewer, a screenshot and a text browser.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from server import config

router = APIRouter(tags=["site"])

STYLE = """
  * { box-sizing: border-box; }
  body { margin: 0; background: #f5f6f8; color: #24292f;
         font-family: system-ui, "Segoe UI", "Microsoft YaHei", sans-serif;
         line-height: 1.7; }
  .wrap { max-width: 780px; margin: 0 auto; padding: 48px 24px 72px; }
  header { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
  .logo { font-size: 26px; font-weight: 700; letter-spacing: .5px; }
  .tag { color: #6b7280; font-size: 14px; }
  h2 { font-size: 17px; margin: 36px 0 12px; }
  p, li { font-size: 15px; }
  ul { padding-left: 20px; }
  .card { background: #fff; border-radius: 12px; padding: 28px 32px;
          box-shadow: 0 2px 14px rgba(0,0,0,.06); }
  .btn { display: inline-block; margin-top: 24px; padding: 11px 26px;
         background: #1677ff; color: #fff; text-decoration: none;
         border-radius: 8px; font-size: 15px; }
  table { width: 100%; border-collapse: collapse; margin-top: 8px; }
  th, td { text-align: left; padding: 14px 4px; border-bottom: 1px solid #eceef1;
           font-size: 15px; }
  th { color: #6b7280; font-weight: 500; font-size: 13px; }
  td.credits { font-weight: 600; }
  td.price { text-align: right; font-weight: 600; color: #1677ff; }
  .note { color: #6b7280; font-size: 14px; margin-top: 22px; }
  footer { margin-top: 40px; color: #9ca3af; font-size: 13px; }
  a { color: #1677ff; }
"""


def _page(title, body):
    return HTMLResponse(
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>{}</title>\n<style>{}</style>\n</head>\n<body>\n"
        '<div class="wrap">\n{}\n</div>\n</body>\n</html>\n'.format(
            title, STYLE, body
        )
    )


def _header():
    return (
        '<header><span class="logo">CheckPause</span>'
        '<span class="tag">国际象棋 AI 复盘工具</span></header>'
    )


def _footer():
    return (
        '<footer>CheckPause · 本站由 CometZZZ 运营 · '
        '如有问题请通过软件内的联系方式反馈</footer>'
    )


@router.get("/", response_class=HTMLResponse)
def home():
    """The front door."""
    return _page(
        "CheckPause - 国际象棋 AI 复盘工具",
        _header()
        + """
<div class="card">
<p>CheckPause 是一个 Windows 桌面程序，用来看懂自己下过的棋。</p>
<p>它会读取你的棋谱和引擎的逐着分析，然后用中文把一个棋手最该知道的事讲清楚：
这一步问题出在哪、当时应该怎么想、下次怎么避免。</p>
<a class="btn" href="/shop">查看价格</a>
</div>

<h2>它能做什么</h2>
<ul>
  <li><b>导入棋谱</b> —— 支持 PGN，可从 Lichess 等平台复制粘贴</li>
  <li><b>引擎分析</b> —— 内置 Stockfish，逐着给出评分和最优走法</li>
  <li><b>AI 讲解</b> —— 把引擎的数字翻译成人话，指出关键失误和更好的思路</li>
  <li><b>随时追问</b> —— 对某一步不理解，直接问它「这里为什么不能走马」</li>
  <li><b>打谱与做题</b> —— 开局库、Lichess 精选题集</li>
</ul>

<h2>怎么用</h2>
<ul>
  <li>下载安装包，双击安装到自己的电脑上（不需要管理员权限）</li>
  <li>在软件内注册一个账号，按需充值 CP积分</li>
  <li>导入棋谱，开始复盘</li>
</ul>
<p class="note">也可以完全离线使用：不使用云端讲解时，软件本体的打谱、引擎分析功能不受影响。</p>
"""
        + _footer(),
    )


@router.get("/shop", response_class=HTMLResponse)
def shop():
    """The price list. Screenshot material for Alipay's onboarding."""
    rows = "".join(
        '<tr><td class="credits">{} CP积分</td>'
        '<td>一次完整复盘约消耗 8 CP积分</td>'
        '<td class="price">¥{}</td></tr>'.format(
            yuan * config.CREDITS_PER_YUAN, yuan
        )
        for yuan in config.topup_packs()
    )
    return _page(
        "CheckPause - 价格",
        _header()
        + """
<div class="card">
<h2 style="margin-top:0">CP积分</h2>
<p>云端讲解按用量计费。CP积分充进账号后长期有效，用多少扣多少。</p>
<table>
  <tr><th>面额</th><th>大约可以</th><th style="text-align:right">价格</th></tr>
  {rows}
</table>
<p class="note">1 CP积分 = ¥0.01。一次完整复盘（包含棋谱与引擎数据分析、
生成讲解）通常消耗 6 到 10 CP积分。</p>
</div>

<h2>怎么充值</h2>
<ul>
  <li>在软件的「设置 → 云端账号」里选择面额</li>
  <li>浏览器会打开支付宝付款页面，用支付宝扫码或登录付款</li>
  <li>付完回到软件，余额自动到账，不需要手动操作</li>
</ul>

<h2>退款与说明</h2>
<ul>
  <li>CP积分为虚拟商品，充值后即进入账号，可随时查看余额与每一笔流水</li>
  <li>如遇重复扣费或功能异常，请联系作者核实，会原路退回未消费部分</li>
  <li>本工具提供复盘辅助，不承诺棋力提升幅度</li>
</ul>
"""
        .replace("{rows}", rows)
        + _footer(),
    )
