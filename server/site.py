"""The public pages: what CheckPause is, and what it costs.

They exist because Alipay's onboarding wants screenshots of a shop, and before
this there was nothing to photograph on this server except an API status blob.

The price list is rendered from the same pack list the payment endpoints use,
so a price change cannot leave the shop page advertising something else. There
is deliberately no JavaScript: a page whose only job is to be read should render
the same for a reviewer, a screenshot and a text browser.

Every picture is inline SVG - the logo mark, the boards, the interface mock and
the icons - so the pages need no static directory, no nginx change and no image
files to keep in sync, and they render fully offline.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from server import config

router = APIRouter(tags=["site"])

DOWNLOAD_URL = "https://github.com/Comet-zzz/CheckPause/releases"

STYLE = """
  :root {
    --bg: #080b12; --bg2: #0c111c;
    --ink: #e8edf7; --muted: #97a4bb; --muted2: #6b788f;
    --line: rgba(255,255,255,.08); --line2: rgba(255,255,255,.15);
    --brand: #5b8cff; --brand2: #92b6ff; --gold: #e0b25a;
  }
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body {
    margin: 0; color: var(--ink); line-height: 1.7;
    font-family: system-ui, "Segoe UI", "Microsoft YaHei", sans-serif;
    -webkit-font-smoothing: antialiased;
    background:
      radial-gradient(900px 520px at 12% -8%, rgba(91,140,255,.20), transparent 60%),
      radial-gradient(760px 520px at 96% -4%, rgba(224,178,90,.10), transparent 55%),
      var(--bg);
  }
  body::before {
    content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image:
      linear-gradient(rgba(255,255,255,.032) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,.032) 1px, transparent 1px);
    background-size: 62px 62px;
    -webkit-mask-image: radial-gradient(circle at 50% 0%, #000, transparent 72%);
    mask-image: radial-gradient(circle at 50% 0%, #000, transparent 72%);
  }
  a { color: var(--brand2); text-decoration: none; }
  .wrap { position: relative; z-index: 1; max-width: 1080px; margin: 0 auto;
          padding: 0 24px 72px; }

  .nav { position: sticky; top: 0; z-index: 20; display: flex;
         align-items: center; justify-content: space-between; padding: 14px 0;
         background: rgba(8,11,18,.72); backdrop-filter: blur(14px);
         border-bottom: 1px solid var(--line); }
  .brand { display: flex; align-items: center; gap: 11px; color: var(--ink);
           font-weight: 700; font-size: 18px; letter-spacing: .6px; }
  .brand .logo { display: block; border-radius: 9px; }
  .nav-links a { color: var(--muted); font-size: 14.5px; margin-left: 28px;
                 transition: color .15s ease; }
  .nav-links a:hover { color: var(--ink); }

  .hero { display: grid; grid-template-columns: 1.05fr .95fr; gap: 48px;
          align-items: center; padding: 66px 0 34px; }
  .pill { display: inline-flex; align-items: center; gap: 9px; padding: 7px 15px;
          border-radius: 999px; border: 1px solid var(--line2);
          background: rgba(255,255,255,.04); color: var(--brand2);
          font-size: 13px; letter-spacing: .4px; }
  .pill .dot { width: 6px; height: 6px; border-radius: 50%;
               background: var(--brand); box-shadow: 0 0 10px var(--brand); }
  .hero h1 { font-size: 52px; line-height: 1.12; margin: 24px 0 18px;
             letter-spacing: -.5px; font-weight: 800; }
  .hero h1 .grad { background: linear-gradient(100deg, #a9c6ff, #5b8cff 48%, #e0b25a);
                   -webkit-background-clip: text; background-clip: text;
                   color: transparent; }
  .hero .lede { color: var(--muted); font-size: 17px; max-width: 34em; margin: 0 0 30px; }
  .cta { display: flex; flex-wrap: wrap; gap: 14px; }
  .btn { display: inline-block; padding: 13px 27px; border-radius: 11px;
         font-size: 15px; font-weight: 600; color: #fff;
         background: linear-gradient(180deg, #6a98ff, #3f74e6);
         border: 1px solid rgba(255,255,255,.18);
         box-shadow: 0 12px 28px rgba(63,116,230,.34);
         transition: transform .16s ease, box-shadow .16s ease; }
  .btn:hover { transform: translateY(-1px); box-shadow: 0 16px 34px rgba(63,116,230,.46); }
  .btn.ghost { background: rgba(255,255,255,.05); color: var(--ink);
               border: 1px solid var(--line2); box-shadow: none; }
  .btn.ghost:hover { background: rgba(255,255,255,.09); }

  .hero-art { position: relative; display: flex; justify-content: center; padding: 8px; }
  .hero-art::before { content: ""; position: absolute; width: 360px; height: 360px;
                      border-radius: 50%; filter: blur(12px);
                      background: radial-gradient(circle, rgba(91,140,255,.38), transparent 62%); }
  .board { position: relative; width: 100%; max-width: 330px; height: auto;
           filter: drop-shadow(0 26px 52px rgba(0,0,0,.58)); }
  .chip { position: absolute; display: flex; align-items: center; gap: 8px;
          padding: 9px 13px; border-radius: 12px; font-size: 13px;
          background: rgba(15,21,34,.92); border: 1px solid var(--line2);
          box-shadow: 0 14px 32px rgba(0,0,0,.45); backdrop-filter: blur(8px); }
  .chip i { width: 7px; height: 7px; border-radius: 50%; background: #7fe0a6;
            box-shadow: 0 0 9px #7fe0a6; }
  .chip.bad i { background: #ff8f8f; box-shadow: 0 0 9px #ff8f8f; }
  .chip.a { top: 13%; right: -4%; }
  .chip.b { bottom: 11%; left: -6%; }

  .trust { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px;
           background: var(--line); border: 1px solid var(--line);
           border-radius: 16px; overflow: hidden; margin-top: 34px; }
  .trust div { display: flex; align-items: center; gap: 12px; padding: 20px 22px;
               background: var(--bg2); color: var(--muted); font-size: 14.5px; }
  .trust svg { width: 20px; height: 20px; color: var(--brand2); flex: none; }
  .trust b { color: var(--ink); font-weight: 600; }

  .section { padding: 68px 0 4px; }
  .kicker { color: var(--brand2); font-size: 13px; letter-spacing: 2.6px;
            text-transform: uppercase; font-weight: 600; }
  h2.title { font-size: 31px; margin: 12px 0 12px; letter-spacing: -.3px; font-weight: 750; }
  .sub { color: var(--muted); font-size: 16px; max-width: 46em; margin: 0 0 34px; }

  .bento { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; }
  .card { position: relative; overflow: hidden; border-radius: 18px; padding: 26px;
          border: 1px solid var(--line);
          background: linear-gradient(180deg, rgba(255,255,255,.045), rgba(255,255,255,.012));
          transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease; }
  .card:hover { transform: translateY(-3px); border-color: var(--line2);
                box-shadow: 0 24px 50px rgba(0,0,0,.42); }
  .card .glow { position: absolute; inset: 0; pointer-events: none; border-radius: inherit;
                background: radial-gradient(320px 150px at 14% 0%,
                rgba(91,140,255,.16), transparent 70%); }
  .card .ico { position: relative; width: 44px; height: 44px; border-radius: 12px;
               display: flex; align-items: center; justify-content: center;
               color: var(--brand2); border: 1px solid rgba(91,140,255,.3);
               background: linear-gradient(160deg, rgba(91,140,255,.24), rgba(91,140,255,.05)); }
  .card .ico svg { width: 22px; height: 22px; }
  .card h3 { position: relative; margin: 18px 0 8px; font-size: 17px; }
  .card p { position: relative; margin: 0; color: var(--muted); font-size: 14.5px; }
  .card.span3 { grid-column: span 3; }
  .card.span2 { grid-column: span 2; }

  .panel { border: 1px solid var(--line); border-radius: 20px; overflow: hidden;
           background: linear-gradient(180deg, #0e1420, #0a0f18);
           box-shadow: 0 34px 74px rgba(0,0,0,.5); }
  .panel-top { display: flex; align-items: center; gap: 8px; padding: 12px 16px;
               border-bottom: 1px solid var(--line); background: rgba(255,255,255,.02); }
  .panel-top i { width: 11px; height: 11px; border-radius: 50%; background: #2a3446; }
  .panel-top .name { margin-left: 8px; color: var(--muted2); font-size: 13px;
                     letter-spacing: .5px; }
  .panel-body { display: grid; grid-template-columns: 320px 1fr; }
  .panel-board { padding: 24px; border-right: 1px solid var(--line); }
  .panel-board .board { max-width: 100%; }
  .panel-side { padding: 24px 28px; }
  .eval-label { display: flex; justify-content: space-between; color: var(--muted);
                font-size: 13px; margin-bottom: 8px; }
  .eval-label b { color: #7fe0a6; }
  .bar { height: 8px; border-radius: 999px; background: rgba(255,255,255,.09); overflow: hidden; }
  .bar span { display: block; height: 100%; width: 61%;
              background: linear-gradient(90deg, #3f74e6, #7fe0a6); }
  .moves { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin: 16px 0 20px; }
  .moves span { padding: 7px 4px; text-align: center; border-radius: 8px; font-size: 13px;
                color: var(--muted); border: 1px solid var(--line);
                background: rgba(255,255,255,.02); }
  .moves span.hot { color: #ff9d9d; border-color: rgba(255,143,143,.5);
                    background: rgba(255,143,143,.08); }
  .chat { display: grid; gap: 10px; }
  .chat .q { justify-self: start; padding: 10px 14px; border-radius: 12px; font-size: 14px;
             color: #cfe0ff; background: rgba(91,140,255,.12);
             border: 1px solid rgba(91,140,255,.28); }
  .chat .a { padding: 12px 14px; border-radius: 12px; font-size: 14px; color: var(--muted);
             background: rgba(255,255,255,.03); border: 1px solid var(--line); }
  .chat .a b { color: var(--brand2); }

  .steps { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
  .step { border-radius: 16px; padding: 24px; border: 1px solid var(--line);
          background: linear-gradient(180deg, rgba(255,255,255,.04), transparent); }
  .step .n { font-size: 13px; font-weight: 600; letter-spacing: 2px; color: var(--brand2); }
  .step h3 { margin: 10px 0 8px; font-size: 16.5px; }
  .step p { margin: 0; color: var(--muted); font-size: 14.5px; }

  .band { margin-top: 68px; padding: 46px; text-align: center; border-radius: 22px;
          border: 1px solid var(--line2);
          background:
            radial-gradient(680px 260px at 50% 0%, rgba(91,140,255,.20), transparent 70%),
            linear-gradient(180deg, rgba(255,255,255,.04), transparent); }
  .band h2 { font-size: 27px; margin: 0 0 10px; font-weight: 750; }
  .band p { color: var(--muted); margin: 0 auto 26px; max-width: 36em; }
  .band .quiet { display: block; margin-top: 18px; color: var(--muted2); font-size: 13.5px; }
  .fine { color: var(--muted2); font-size: 13px; margin-top: 20px; }

  /* shop */
  .card-panel { border: 1px solid var(--line); border-radius: 20px; padding: 32px 34px;
                background: linear-gradient(180deg, rgba(255,255,255,.045),
                rgba(255,255,255,.012)); }
  .packs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0 4px; }
  .pack { position: relative; text-align: center; border-radius: 16px; padding: 28px 20px;
          border: 1px solid var(--line); background: rgba(255,255,255,.02);
          transition: transform .16s ease, border-color .16s ease; }
  .pack:hover { transform: translateY(-3px); border-color: var(--line2); }
  .pack.popular { border-color: rgba(91,140,255,.55);
                  box-shadow: 0 18px 40px rgba(63,116,230,.20); }
  .pack .badge { position: absolute; top: -11px; left: 50%; transform: translateX(-50%);
                 padding: 3px 13px; border-radius: 999px; white-space: nowrap;
                 font-size: 12px; font-weight: 600; color: #fff;
                 background: linear-gradient(180deg, #6a98ff, #3f74e6); }
  .pack .credits { font-size: 21px; font-weight: 700; }
  .pack .price { font-size: 30px; font-weight: 800; color: var(--brand2); margin: 8px 0 2px; }
  .pack .hint { color: var(--muted2); font-size: 13.5px; }
  ul { padding-left: 20px; }
  li { font-size: 15px; color: var(--muted); margin-bottom: 4px; }
  li b { color: var(--ink); font-weight: 600; }

  footer { margin-top: 64px; padding-top: 26px; border-top: 1px solid var(--line);
           display: flex; flex-wrap: wrap; gap: 14px; justify-content: space-between;
           color: var(--muted2); font-size: 13px; }
  footer a { color: var(--muted); }

  @media (max-width: 860px) {
    .hero { grid-template-columns: 1fr; gap: 30px; padding-top: 40px; }
    .hero h1 { font-size: 38px; }
    .hero-art { order: -1; max-width: 250px; margin: 0 auto; }
    .trust { grid-template-columns: repeat(2, 1fr); }
    .bento { grid-template-columns: 1fr; }
    .card.span3, .card.span2 { grid-column: auto; }
    .panel-body { grid-template-columns: 1fr; }
    .panel-board { border-right: none; border-bottom: 1px solid var(--line); }
    .steps, .packs { grid-template-columns: 1fr; }
    .nav-links a { margin-left: 16px; }
  }
"""

# The king from the application icon, reused so the mark on the site is the
# mark in the installer.
_KING_MARK = (
    '<g fill="#f6f7f9" stroke="#f6f7f9" stroke-width="4" stroke-linejoin="round">'
    '<path d="M157 206 L157 153 A10 10 0 0 1 177 153 L186 192 L195 118 '
    "A12 12 0 0 1 219 118 L231 178 L241 84 A15 15 0 0 1 271 84 L281 178 "
    "L293 118 A12 12 0 0 1 317 118 L326 192 L335 153 A10 10 0 0 1 355 153 "
    'L355 206 Z"/>'
    '<rect x="156" y="206" width="200" height="30" rx="11"/>'
    '<path d="M208 244 C 204 300 208 346 145 390 L367 390 C 304 346 308 300 '
    '304 244 Z" stroke-width="5"/>'
    '<rect x="139" y="386" width="234" height="26" rx="8"/>'
    '<rect x="133" y="418" width="246" height="26" rx="10"/>'
    "</g>"
)

_PIECE_SHAPES = {
    "king": (
        '<rect x="-2.1" y="-25" width="4.2" height="8.6" rx="1.6"/>'
        '<rect x="-6.4" y="-21.7" width="12.8" height="4.2" rx="1.6"/>'
        '<path d="M-7 -9 C-7 -13 -3.6 -13 -2.6 -18 L2.6 -18 C3.6 -13 7 -13 7 -9 Z"/>'
        '<path d="M-9.4 9 C-9.4 0 -4.6 0 -3 -8 L3 -8 C4.6 0 9.4 0 9.4 9 Z"/>'
        '<rect x="-11.8" y="9" width="23.6" height="5.2" rx="2.1"/>'
    ),
    "pawn": (
        '<circle cx="0" cy="-13.5" r="6"/>'
        '<path d="M-8.4 8 C-8.4 -1 -4 -1 -2.6 -8 L2.6 -8 C4 -1 8.4 -1 8.4 8 Z"/>'
        '<rect x="-11.2" y="8" width="22.4" height="5" rx="2"/>'
    ),
    "knight": (
        '<path d="M6.5 8 L-7 8 C-7 3 -7.5 -2 -6.5 -7 C-5.6 -11.5 -2.6 -13.8 '
        '0.5 -15 L2 -20 L4.5 -16.5 C8.5 -15 10.6 -11 10 -6.5 C9.4 -2.5 7.4 3 6.5 8 Z"/>'
        '<rect x="-11" y="8" width="22" height="5" rx="2"/>'
    ),
}

_ICONS = {
    "import": (
        '<path d="M7 3h7l4 4v14H7z"/><path d="M14 3v4h4"/>'
        '<path d="M12 10v6"/><path d="M9.5 13.5 12 16l2.5-2.5"/>'
    ),
    "analysis": (
        '<circle cx="10.5" cy="10.5" r="6.5"/><path d="M15.5 15.5 20 20"/>'
        '<path d="M8 12.5v-2M10.5 12.5V8.5M13 12.5v-3"/>'
    ),
    "chat": '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
    "puzzle": (
        '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.4"/>'
        '<path d="M12 1.5v3M12 19.5v3M1.5 12h3M19.5 12h3"/>'
    ),
    "engine": (
        '<rect x="7" y="7" width="10" height="10" rx="2"/>'
        '<rect x="10.5" y="10.5" width="3" height="3"/>'
        '<path d="M9 3v3M15 3v3M9 18v3M15 18v3M3 9h3M3 15h3M18 9h3M18 15h3"/>'
    ),
    "book": (
        '<path d="M4 4h6a3 3 0 0 1 3 3v13a3 3 0 0 0-3-3H4z"/>'
        '<path d="M20 4h-6a3 3 0 0 0-3 3v13a3 3 0 0 1 3-3h6z"/>'
    ),
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z"/>'
    '<path d="M9.5 12l2 2 3.5-4"/>',
    "download": '<path d="M12 3v11"/><path d="M8 10.5l4 4 4-4"/><path d="M5 20h14"/>',
}


def _page(title, body):
    return HTMLResponse(
        "<!doctype html>\n"
        '<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="description" content="CheckPause - 国际象棋复盘工具">\n'
        f"<title>{title}</title>\n"
        f"<style>{STYLE}</style>\n</head>\n<body>\n"
        f'<div class="wrap">\n{body}\n</div>\n</body>\n</html>\n'
    )


def _logo():
    return (
        '<svg class="logo" viewBox="0 0 512 512" width="32" height="32" '
        'aria-hidden="true" xmlns="http://www.w3.org/2000/svg">'
        '<rect width="512" height="512" rx="116" fill="#111827"/>'
        f"{_KING_MARK}</svg>"
    )


def _icon(name):
    return (
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'
        f"{_ICONS[name]}</svg>"
    )


def _board_svg():
    """A small board with a few pieces, drawn as inline SVG.

    It is generated rather than hand-written so the squares line up, and it
    borrows no third-party artwork - the pieces are plain geometry.
    """
    cell = 34
    span = cell * 8
    pad = 14
    pieces = [
        (4, 0, "black", "king"),
        (3, 1, "black", "pawn"),
        (2, 5, "white", "knight"),
        (4, 4, "white", "pawn"),
        (3, 7, "white", "king"),
    ]
    parts = []
    for row in range(8):
        for col in range(8):
            fill = "#e9d8b6" if (row + col) % 2 == 0 else "#b18451"
            x = pad + col * cell
            y = pad + row * cell
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" fill="{fill}"/>')
    for col, row, colour, kind in pieces:
        if colour == "white":
            fill, stroke = "#fbfbf7", "#3a3a3a"
        else:
            fill, stroke = "#2b2f36", "#0b0d10"
        cx = pad + col * cell + cell / 2
        cy = pad + row * cell + cell - 7
        parts.append(
            f'<g transform="translate({cx:g} {cy:g}) scale(0.72)" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1.4" stroke-linejoin="round" '
            f'stroke-linecap="round">{_PIECE_SHAPES[kind]}</g>'
        )
    size = span + pad * 2
    return (
        f'<svg class="board" viewBox="0 0 {size} {size}" role="img" '
        'aria-label="棋盘示意图" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{size}" height="{size}" rx="14" fill="#0b1220"/>'
        f"{''.join(parts)}</svg>"
    )


def _header():
    return (
        '<header class="nav">'
        f'<a class="brand" href="/">{_logo()}<span>CheckPause</span></a>'
        '<nav class="nav-links">'
        '<a href="#features">功能</a>'
        '<a href="#guide">流程</a>'
        '<a href="/shop">定价</a>'
        "</nav></header>"
    )


def _footer():
    return (
        "<footer>"
        "<span>CheckPause · 本站由 CometZZZ 运营 · 版权保留</span>"
        f'<span><a href="{DOWNLOAD_URL}">下载</a> · '
        '<a href="/shop">定价</a></span>'
        "</footer>"
    )


def _hero():
    return (
        '<section class="hero">'
        '<div class="hero-copy">'
        '<span class="pill"><span class="dot"></span>国际象棋 · 复盘与训练</span>'
        '<h1>读懂<br><span class="grad">每一步棋的得失</span></h1>'
        '<p class="lede">导入棋谱，逐着查看引擎评估与讲解：定位关键转折，'
        "理解当时的更优选择，把对局沉淀为可以复用的经验。</p>"
        '<div class="cta">'
        '<a class="btn" href="#features">了解功能</a>'
        '<a class="btn ghost" href="#guide">使用流程</a>'
        "</div></div>"
        '<div class="hero-art">'
        f"{_board_svg()}"
        '<span class="chip a"><i></i>最优着法 Nf3</span>'
        '<span class="chip b bad"><i></i>失误 12… Nf3</span>'
        "</div></section>"
    )


def _trust():
    items = [
        ("engine", "内置 Stockfish 引擎"),
        ("import", "标准 PGN 棋谱导入"),
        ("book", "开局线路与精选题集"),
        ("shield", "本地功能可离线使用"),
    ]
    cells = "".join(f"<div>{_icon(key)}{text}</div>" for key, text in items)
    return f'<div class="trust">{cells}</div>'


def _features():
    items = [
        (
            "span3",
            "import",
            "棋谱导入",
            "支持标准 PGN 格式，可直接粘贴来自 Lichess 等平台的棋局，"
            "自动解析对局信息与完整着法序列。",
        ),
        (
            "span3",
            "analysis",
            "引擎分析",
            "内置 Stockfish，逐着给出评估分数与最优着法，并标记关键节点，" "便于聚焦全局转折。",
        ),
        (
            "span2",
            "chat",
            "复盘讲解",
            "将引擎评估整理为结构化文字，说明失误成因、局面判断与改进方向。",
        ),
        ("span2", "puzzle", "追问答疑", "针对具体着法或局面提问，获得聚焦该处的解释与思路分析。"),
        ("span2", "book", "打谱与训练", "内置开局线路与精选题目，兼顾打谱、解题与对弈训练。"),
    ]
    cards = "".join(
        f'<div class="card {span}"><span class="glow"></span>'
        f'<div class="ico">{_icon(key)}</div>'
        f"<h3>{title}</h3><p>{text}</p></div>"
        for span, key, title, text in items
    )
    return (
        '<section class="section" id="features">'
        '<div class="kicker">功能</div>'
        '<h2 class="title">为认真复盘而设计</h2>'
        '<p class="sub">从棋谱导入到逐着讲解，围绕同一局棋，把评估、'
        "思路与训练串成一条完整的复盘链路。</p>"
        f'<div class="bento">{cards}</div>'
        "</section>"
    )


def _showcase():
    moves = [
        "e4",
        "e5",
        "Nf3",
        "Nc6",
        "Bb5",
        "a6",
        "Ba4",
        "Nf6",
        "c3",
        "Be7",
        "d4",
        "exd4",
        "cxd4",
        "b5",
        "Bc2",
        "d5",
    ]
    move_cells = "".join(
        f'<span class="{"hot" if cell == "Nf3" else ""}">{cell}</span>' for cell in moves
    )
    return (
        '<section class="section" id="report">'
        '<div class="kicker">界面</div>'
        '<h2 class="title">一份清晰的复盘报告</h2>'
        '<p class="sub">左侧棋盘与评估条，右侧着法列表与讲解；'
        "关键失误直接标出，无需在长串数字中自行寻找。</p>"
        '<div class="panel">'
        '<div class="panel-top"><i></i><i></i><i></i>'
        '<span class="name">CheckPause · 复盘</span></div>'
        '<div class="panel-body">'
        f'<div class="panel-board">{_board_svg()}</div>'
        '<div class="panel-side">'
        '<div class="eval-label"><span>局面评估</span><b>+0.42</b></div>'
        '<div class="bar"><span></span></div>'
        f'<div class="moves">{move_cells}</div>'
        '<div class="chat">'
        '<div class="q">第 12 手 Nf3 的问题在哪里？</div>'
        '<div class="a">该着法放弃了对 e5 的控制，并为黑方 <b>e5–e4</b> 的推进'
        "创造了机会。更稳妥的次序是先将马调往 d2，再逐步争夺中心。</div>"
        "</div></div></div></div>"
        '<p class="fine">云端复盘讲解由服务端 AI 生成，需联网并消耗 CP积分；'
        "本地分析功能无需联网。</p>"
        "</section>"
    )


def _steps():
    items = [
        ("01", "获取并安装", "下载桌面客户端，支持 Windows 与 macOS，" "安装过程无需管理员权限。"),
        ("02", "建立本地档案", "首次启动设置用户名与语言，" "档案与棋局数据保存在本机。"),
        ("03", "导入并复盘", "导入一局棋，逐着查看评估与讲解；" "针对疑问可随时追问。"),
    ]
    cards = "".join(
        f'<div class="step"><div class="n">{number}</div>' f"<h3>{title}</h3><p>{text}</p></div>"
        for number, title, text in items
    )
    return (
        '<section class="section" id="guide">'
        '<div class="kicker">上手</div>'
        '<h2 class="title">三步开始复盘</h2>'
        f'<div class="steps">{cards}</div>'
        "</section>"
    )


def _band():
    return (
        '<section class="band">'
        "<h2>从下一局棋开始</h2>"
        "<p>安装 CheckPause，把每一盘对局变成可以反复回看的复盘。</p>"
        f'<a class="btn" href="{DOWNLOAD_URL}">前往下载</a>'
        '<span class="quiet">查看 <a href="/shop">定价</a></span>'
        "</section>"
    )


@router.get("/", response_class=HTMLResponse)
def home():
    """The front door."""
    return _page(
        "CheckPause - 国际象棋复盘工具",
        _header() + _hero() + _trust() + _features() + _showcase() + _steps() + _band() + _footer(),
    )


def _pack_cards():
    packs = config.topup_packs()
    popular = packs[len(packs) // 2]
    cards = []
    for yuan in packs:
        credits = yuan * config.CREDITS_PER_YUAN
        is_popular = yuan == popular
        badge = '<span class="badge">最受欢迎</span>' if is_popular else ""
        cards.append(
            f'<div class="pack{" popular" if is_popular else ""}">{badge}'
            f'<div class="credits">{credits} CP积分</div>'
            f'<div class="price">¥{yuan}</div>'
            f'<div class="hint">约 {credits // 8} 次完整复盘</div>'
            "</div>"
        )
    return "".join(cards)


@router.get("/shop", response_class=HTMLResponse)
def shop():
    """The price list. Screenshot material for Alipay's onboarding."""
    return _page(
        "CheckPause - 定价",
        _header() + '<section class="section" style="padding-top:56px">'
        '<div class="kicker">定价</div>'
        '<h2 class="title">CP积分</h2>'
        '<p class="sub">云端复盘按用量计费。CP积分充入账号后长期有效，'
        "按实际消耗扣除，可在客户端内随时查看余额与流水。</p>"
        "</section>" + '<div class="card-panel">'
        f'<div class="packs">{_pack_cards()}</div>'
        '<p class="fine">1 CP积分 = ¥0.01。一次完整复盘（含棋谱与引擎数据'
        "分析、生成讲解）通常消耗 6 至 10 CP积分。</p>"
        "</div>"
        '<section class="section">'
        '<div class="kicker">充值</div>'
        '<h2 class="title">充值方式</h2>'
        "<ul>"
        "<li>在客户端「设置 → 云端账号」中选择面额</li>"
        "<li>浏览器打开支付宝付款页面，扫码或登录完成支付</li>"
        "<li>支付完成后返回客户端，余额自动到账，无需人工操作</li>"
        "</ul>"
        "</section>"
        '<section class="section">'
        '<div class="kicker">说明</div>'
        '<h2 class="title">退款与声明</h2>'
        "<ul>"
        "<li><b>虚拟商品</b>：CP积分充入账号后即可使用，"
        "余额与每一笔流水均可在客户端查看</li>"
        "<li><b>异常处理</b>：如遇重复扣费或功能异常，请联系作者核实，"
        "未消费部分将原路退回</li>"
        "<li><b>效果说明</b>：本工具提供复盘辅助，不承诺棋力提升幅度</li>"
        "</ul>"
        "</section>" + _footer(),
    )
