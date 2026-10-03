"""The public pages: what CheckPause is, and what it costs.

They exist because Alipay's onboarding wants screenshots of a shop, and before
this there was nothing to photograph on this server except an API status blob.

The price list is rendered from the same pack list the payment endpoints use,
so a price change cannot leave the shop page advertising something else. There
is deliberately no JavaScript: a page whose only job is to be read should render
the same for a reviewer, a screenshot and a text browser. The language switcher
is a pair of links (``?lang=zh`` / ``?lang=en``) for the same reason.

Every picture is inline SVG - the logo mark, the boards, the interface mock and
the icons - so the pages need no static directory, no nginx change and no image
files to keep in sync, and they render fully offline.
"""

import json

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
  .nav-right { display: flex; align-items: center; }
  .nav-links a { color: var(--muted); font-size: 14.5px; margin-left: 28px;
                 transition: color .15s ease; }
  .nav-links a:hover { color: var(--ink); }
  .lang { display: inline-flex; margin-left: 26px; padding: 3px; border-radius: 999px;
          border: 1px solid var(--line2); background: rgba(255,255,255,.03); }
  .lang a { padding: 4px 13px; border-radius: 999px; font-size: 13px; color: var(--muted); }
  .lang a.on { background: rgba(255,255,255,.10); color: var(--ink); }
  .lang a:hover { color: var(--ink); }

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

  .cta { display: flex; flex-wrap: wrap; gap: 14px; align-items: center; }
  .btn { display: inline-block; padding: 13px 27px; border-radius: 11px;
         font-size: 15px; font-weight: 600; color: #fff; cursor: pointer;
         background: linear-gradient(180deg, #6a98ff, #3f74e6);
         border: 1px solid rgba(255,255,255,.18);
         box-shadow: 0 12px 28px rgba(63,116,230,.34);
         transition: transform .16s ease, box-shadow .16s ease; }
  .btn:hover { transform: translateY(-1px); box-shadow: 0 16px 34px rgba(63,116,230,.46); }
  .btn.ghost { background: rgba(255,255,255,.05); color: var(--ink);
               border: 1px solid var(--line2); box-shadow: none; }
  .btn.ghost:hover { background: rgba(255,255,255,.09); }

  .dl { position: relative; }
  .dl-btn { display: inline-flex; align-items: center; gap: 10px; font: inherit; }
  .dl-btn svg { width: 15px; height: 15px; }
  .dl:hover .dl-btn svg, .dl:focus-within .dl-btn svg { transform: rotate(180deg); }
  .dl-menu { position: absolute; top: calc(100% + 10px); left: 0; z-index: 30;
             min-width: 268px; padding: 8px; border-radius: 14px;
             border: 1px solid var(--line2); background: rgba(13,18,28,.98);
             backdrop-filter: blur(14px); box-shadow: 0 26px 54px rgba(0,0,0,.52);
             opacity: 0; visibility: hidden; transform: translateY(-6px);
             transition: opacity .16s ease, transform .16s ease, visibility .16s ease; }
  .dl:hover .dl-menu, .dl:focus-within .dl-menu { opacity: 1; visibility: visible;
                                                   transform: none; }
  .dl-item { display: flex; align-items: center; justify-content: space-between;
             gap: 16px; padding: 11px 13px; border-radius: 10px;
             color: var(--ink); font-size: 14.5px; }
  a.dl-item:hover { background: rgba(255,255,255,.06); }
  .dl-name { font-weight: 600; }
  .dl-meta { color: var(--muted2); font-size: 12.5px; }
  .dl-sub a { color: var(--brand2); font-size: 13px; margin-left: 14px; }
  .dl-sub a:hover { text-decoration: underline; }
  .dl-hint { padding: 7px 13px 5px; color: var(--muted2); font-size: 12px; }

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
    .nav-links a { margin-left: 15px; font-size: 13.5px; }
    .lang { margin-left: 14px; }
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
    "chevron": '<path d="M6 9l6 6 6-6"/>',
}

_STRINGS = {
    "zh": {
        "title_home": "CheckPause - 国际象棋复盘工具",
        "title_shop": "CheckPause - 定价",
        "desc": "CheckPause 是一款国际象棋复盘工具：导入棋谱，逐着查看引擎评估与讲解，"
        "定位关键转折并理解更优选择。",
        "nav_home": "首页",
        "nav_features": "功能",
        "nav_guide": "流程",
        "nav_pricing": "定价",
        "pill": "国际象棋 · 复盘与训练",
        "hero_1": "读懂",
        "hero_2": "每一步棋的得失",
        "hero_lede": "导入棋谱，逐着查看引擎评估与讲解：定位关键转折，"
        "理解当时的更优选择，把对局沉淀为可以复用的经验。",
        "download": "下载",
        "dl_windows": "Windows",
        "dl_windows_meta": "x64 · .exe",
        "dl_macos": "macOS",
        "dl_apple": "Apple 芯片",
        "dl_intel": "Intel",
        "dl_hint": "macOS 提供 Apple 芯片与 Intel 两个版本",
        "chip_best": "最优着法 Nf3",
        "chip_blunder": "失误 12… Nf3",
        "trust": [
            "内置 Stockfish 引擎",
            "标准 PGN 棋谱导入",
            "开局线路与精选题集",
            "本地功能可离线使用",
        ],
        "features_kicker": "功能",
        "features_title": "为认真复盘而设计",
        "features_sub": "从棋谱导入到逐着讲解，围绕同一局棋，"
        "把评估、思路与训练串成一条完整的复盘链路。",
        "f1_t": "棋谱导入",
        "f1_b": "支持标准 PGN 格式，可直接粘贴来自 Lichess 等平台的棋局，"
        "自动解析对局信息与完整着法序列。",
        "f2_t": "引擎分析",
        "f2_b": "内置 Stockfish，逐着给出评估分数与最优着法，" "并标记关键节点，便于聚焦全局转折。",
        "f3_t": "复盘讲解",
        "f3_b": "将引擎评估整理为结构化文字，说明失误成因、局面判断与改进方向。",
        "f4_t": "追问答疑",
        "f4_b": "针对具体着法或局面提问，获得聚焦该处的解释与思路分析。",
        "f5_t": "打谱与训练",
        "f5_b": "内置开局线路与精选题目，兼顾打谱、解题与对弈训练。",
        "show_kicker": "界面",
        "show_title": "一份清晰的复盘报告",
        "show_sub": "左侧棋盘与评估条，右侧着法列表与讲解；"
        "关键失误直接标出，无需在长串数字中自行寻找。",
        "report_name": "CheckPause · 复盘",
        "eval_label": "局面评估",
        "q": "第 12 手 Nf3 的问题在哪里？",
        "a": "该着法放弃了对 e5 的控制，并为黑方 <b>e5–e4</b> 的推进创造了机会。"
        "更稳妥的次序是先将马调往 d2，再逐步争夺中心。",
        "fine": "云端复盘讲解由服务端模型生成，需联网并消耗 CP积分；" "本地分析功能无需联网。",
        "guide_kicker": "上手",
        "guide_title": "三步开始复盘",
        "s1_t": "获取并安装",
        "s1_b": "下载桌面客户端，支持 Windows 与 macOS，安装过程无需管理员权限。",
        "s2_t": "建立本地档案",
        "s2_b": "首次启动设置用户名与语言，档案与棋局数据保存在本机。",
        "s3_t": "导入并复盘",
        "s3_b": "导入一局棋，逐着查看评估与讲解；针对疑问可随时追问。",
        "band_title": "从下一局棋开始",
        "band_body": "安装 CheckPause，把每一盘对局变成可以反复回看的复盘。",
        "band_download": "前往下载",
        "band_pricing": "查看",
        "footer_ops": "CheckPause · 本站由 CometZZZ 运营 · 版权保留",
        "footer_download": "下载",
        "footer_pricing": "定价",
        "shop_kicker": "定价",
        "shop_title": "CP积分",
        "shop_sub": "云端复盘按用量计费。CP积分充入账号后长期有效，"
        "按实际消耗扣除，可在客户端内随时查看余额与流水。",
        "credits": "{} CP积分",
        "popular": "最受欢迎",
        "pack_hint": "约 {} 次完整复盘",
        "shop_fine": "1 CP积分 = ¥0.01。一次完整复盘（含棋谱与引擎数据分析、"
        "生成讲解）通常消耗 6 至 10 CP积分。",
        "topup_kicker": "充值",
        "topup_title": "充值方式",
        "topup_items": [
            "在客户端「设置 → 云端账号」中选择面额",
            "浏览器打开支付宝付款页面，扫码或登录完成支付",
            "支付完成后返回客户端，余额自动到账，无需人工操作",
        ],
        "refund_kicker": "说明",
        "refund_title": "退款与声明",
        "refund_items": [
            "<b>虚拟商品</b>：CP积分充入账号后即可使用，余额与每一笔流水均可在客户端查看",
            "<b>异常处理</b>：如遇重复扣费或功能异常，请联系作者核实，未消费部分将原路退回",
            "<b>效果说明</b>：本工具提供复盘辅助，不承诺棋力提升幅度",
        ],
    },
    "en": {
        "title_home": "CheckPause - Chess Review and Training",
        "title_shop": "CheckPause - Pricing",
        "desc": "CheckPause is a chess review tool: import a game, step through "
        "the engine evaluation and notes, and see the better choices.",
        "nav_home": "Home",
        "nav_features": "Features",
        "nav_guide": "Workflow",
        "nav_pricing": "Pricing",
        "pill": "Chess · Review and Training",
        "hero_1": "Understand",
        "hero_2": "every move you play",
        "hero_lede": "Import a game and step through the engine's evaluation and "
        "notes: find the turning points, see what else was available, and turn "
        "each game into experience you can reuse.",
        "download": "Download",
        "dl_windows": "Windows",
        "dl_windows_meta": "x64 · .exe",
        "dl_macos": "macOS",
        "dl_apple": "Apple silicon",
        "dl_intel": "Intel",
        "dl_hint": "macOS ships as Apple silicon and Intel builds",
        "chip_best": "Best move Nf3",
        "chip_blunder": "Blunder 12… Nf3",
        "trust": [
            "Built-in Stockfish engine",
            "Standard PGN import",
            "Opening lines and puzzles",
            "Local features work offline",
        ],
        "features_kicker": "Features",
        "features_title": "Built for serious review",
        "features_sub": "From import to move-by-move notes, everything revolves "
        "around one game, connecting evaluation, ideas and training.",
        "f1_t": "Game import",
        "f1_b": "Standard PGN is supported; paste a game from Lichess or another "
        "platform and the moves and headers are parsed automatically.",
        "f2_t": "Engine analysis",
        "f2_b": "Stockfish is built in. Every move gets an evaluation and the "
        "best line, with the turning points marked so you can focus.",
        "f3_t": "Written notes",
        "f3_b": "Engine numbers become structured text: what went wrong, how to "
        "read the position, and what to aim for instead.",
        "f4_t": "Follow-up questions",
        "f4_b": "Ask about a specific move or position and get an explanation "
        "focused on exactly that moment.",
        "f5_t": "Study and practice",
        "f5_b": "Opening lines and curated puzzles are included, so you can "
        "review, solve and play in one place.",
        "show_kicker": "Interface",
        "show_title": "A review that reads clearly",
        "show_sub": "Board and evaluation bar on the left, moves and notes on the "
        "right; the turning points are marked, so you do not have to hunt "
        "through a wall of numbers.",
        "report_name": "CheckPause · Review",
        "eval_label": "Evaluation",
        "q": "What is wrong with 12. Nf3?",
        "a": "The move gives up control of e5 and lets Black play <b>e5–e4</b>. "
        "A steadier order is to bring the knight to d2 first and contest the "
        "centre step by step.",
        "fine": "Cloud review notes are generated by a server-side model; they "
        "need a connection and consume CP credits. Local analysis works offline.",
        "guide_kicker": "Getting started",
        "guide_title": "Three steps to your first review",
        "s1_t": "Download and install",
        "s1_b": "Get the desktop client for Windows or macOS; installation needs "
        "no administrator rights.",
        "s2_t": "Create a local profile",
        "s2_b": "Choose a username and language on first launch; your profile and "
        "games stay on your machine.",
        "s3_t": "Import and review",
        "s3_b": "Import a game and step through the evaluation and notes; ask "
        "follow-up questions any time.",
        "band_title": "Start with your next game",
        "band_body": "Install CheckPause and turn every game into a review you "
        "can come back to.",
        "band_download": "Download",
        "band_pricing": "See",
        "footer_ops": "CheckPause · Operated by CometZZZ · All rights reserved",
        "footer_download": "Download",
        "footer_pricing": "Pricing",
        "shop_kicker": "Pricing",
        "shop_title": "CP credits",
        "shop_sub": "Cloud review is billed by usage. CP credits stay valid in "
        "your account and are charged as you go; the client shows your balance "
        "and every transaction.",
        "credits": "{} CP credits",
        "popular": "Most popular",
        "pack_hint": "about {} full reviews",
        "shop_fine": "1 CP credit = ¥0.01. A full review (import, engine "
        "analysis and written notes) usually costs 6 to 10 CP credits.",
        "topup_kicker": "Top-up",
        "topup_title": "How to top up",
        "topup_items": [
            "Choose an amount under Settings → Cloud account in the client",
            "Your browser opens the Alipay checkout; scan the code or sign in to pay",
            "Return to the client and the credits appear automatically",
        ],
        "refund_kicker": "Notes",
        "refund_title": "Refunds and terms",
        "refund_items": [
            "<b>Virtual goods</b>: credits are usable as soon as they arrive, "
            "and the client shows your balance and full history",
            "<b>Problems</b>: for a duplicate charge or a fault, contact the "
            "author and any unspent amount is refunded to the original method",
            "<b>Scope</b>: this tool assists review; it does not promise a " "specific rating gain",
        ],
    },
}


def _normalize_lang(value):
    return "en" if value.strip().lower().startswith("en") else "zh"


def _download_links():
    """Resolve installer links from the mirror manifest, with a safe fallback.

    The manifest is written by the deploy scripts; when it is missing (a fresh
    checkout, the tests) every link points at the release page instead.
    """
    links = {"windows": DOWNLOAD_URL, "mac_arm": DOWNLOAD_URL, "mac_intel": DOWNLOAD_URL}
    try:
        raw = (config.downloads_dir() / "version.json").read_text(encoding="utf-8")
        urls = json.loads(raw).get("urls", {})
    except (OSError, ValueError):
        return links
    links["windows"] = urls.get("windows-x86_64") or DOWNLOAD_URL
    links["mac_arm"] = urls.get("macos-arm64") or DOWNLOAD_URL
    links["mac_intel"] = urls.get("macos-x86_64") or DOWNLOAD_URL
    return links


def _page(title, description, lang, body):
    html_lang = "zh-CN" if lang == "zh" else "en"
    return HTMLResponse(
        "<!doctype html>\n"
        f'<html lang="{html_lang}">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<meta name="description" content="{description}">\n'
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
        'aria-label="board" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="{size}" height="{size}" rx="14" fill="#0b1220"/>'
        f"{''.join(parts)}</svg>"
    )


def _header(lang, path, s):
    home = f"/?lang={lang}"
    return (
        '<header class="nav">'
        f'<a class="brand" href="{home}">{_logo()}<span>CheckPause</span></a>'
        '<div class="nav-right"><nav class="nav-links">'
        f'<a href="{home}">{s["nav_home"]}</a>'
        f'<a href="/?lang={lang}#features">{s["nav_features"]}</a>'
        f'<a href="/?lang={lang}#guide">{s["nav_guide"]}</a>'
        f'<a href="/shop?lang={lang}">{s["nav_pricing"]}</a>'
        "</nav>"
        f'<div class="lang"><a class="{"on" if lang == "zh" else ""}" '
        f'href="{path}?lang=zh">中文</a>'
        f'<a class="{"on" if lang == "en" else ""}" '
        f'href="{path}?lang=en">EN</a></div>'
        "</div></header>"
    )


def _footer(lang, s):
    return (
        "<footer>"
        f'<span>{s["footer_ops"]}</span>'
        f'<span><a href="{DOWNLOAD_URL}">{s["footer_download"]}</a> · '
        f'<a href="/shop?lang={lang}">{s["footer_pricing"]}</a></span>'
        "</footer>"
    )


def _download_menu(s):
    links = _download_links()
    return (
        '<div class="dl">'
        f'<button class="btn dl-btn" type="button">{s["download"]}'
        f'{_icon("chevron")}</button>'
        '<div class="dl-menu">'
        f'<a class="dl-item" href="{links["windows"]}">'
        f'<span class="dl-name">{s["dl_windows"]}</span>'
        f'<span class="dl-meta">{s["dl_windows_meta"]}</span></a>'
        '<div class="dl-item">'
        f'<span class="dl-name">{s["dl_macos"]}</span>'
        f'<span class="dl-sub"><a href="{links["mac_arm"]}">{s["dl_apple"]}</a>'
        f'<a href="{links["mac_intel"]}">{s["dl_intel"]}</a></span>'
        "</div>"
        f'<div class="dl-hint">{s["dl_hint"]}</div>'
        "</div></div>"
    )


def _hero(s):
    return (
        '<section class="hero">'
        '<div class="hero-copy">'
        f'<span class="pill"><span class="dot"></span>{s["pill"]}</span>'
        f'<h1>{s["hero_1"]}<br><span class="grad">{s["hero_2"]}</span></h1>'
        f'<p class="lede">{s["hero_lede"]}</p>'
        f'<div class="cta">{_download_menu(s)}</div>'
        "</div>"
        '<div class="hero-art">'
        f"{_board_svg()}"
        f'<span class="chip a"><i></i>{s["chip_best"]}</span>'
        f'<span class="chip b bad"><i></i>{s["chip_blunder"]}</span>'
        "</div></section>"
    )


def _trust(s):
    items = [("engine", 0), ("import", 1), ("book", 2), ("shield", 3)]
    cells = "".join(f"<div>{_icon(key)}{s['trust'][index]}</div>" for key, index in items)
    return f'<div class="trust">{cells}</div>'


def _features(s):
    items = [
        ("span3", "import", s["f1_t"], s["f1_b"]),
        ("span3", "analysis", s["f2_t"], s["f2_b"]),
        ("span2", "chat", s["f3_t"], s["f3_b"]),
        ("span2", "puzzle", s["f4_t"], s["f4_b"]),
        ("span2", "book", s["f5_t"], s["f5_b"]),
    ]
    cards = "".join(
        f'<div class="card {span}"><span class="glow"></span>'
        f'<div class="ico">{_icon(key)}</div>'
        f"<h3>{title}</h3><p>{text}</p></div>"
        for span, key, title, text in items
    )
    return (
        '<section class="section" id="features">'
        f'<div class="kicker">{s["features_kicker"]}</div>'
        f'<h2 class="title">{s["features_title"]}</h2>'
        f'<p class="sub">{s["features_sub"]}</p>'
        f'<div class="bento">{cards}</div>'
        "</section>"
    )


def _showcase(s):
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
        f'<div class="kicker">{s["show_kicker"]}</div>'
        f'<h2 class="title">{s["show_title"]}</h2>'
        f'<p class="sub">{s["show_sub"]}</p>'
        '<div class="panel">'
        '<div class="panel-top"><i></i><i></i><i></i>'
        f'<span class="name">{s["report_name"]}</span></div>'
        '<div class="panel-body">'
        f'<div class="panel-board">{_board_svg()}</div>'
        '<div class="panel-side">'
        f'<div class="eval-label"><span>{s["eval_label"]}</span><b>+0.42</b></div>'
        '<div class="bar"><span></span></div>'
        f'<div class="moves">{move_cells}</div>'
        '<div class="chat">'
        f'<div class="q">{s["q"]}</div>'
        f'<div class="a">{s["a"]}</div>'
        "</div></div></div></div>"
        f'<p class="fine">{s["fine"]}</p>'
        "</section>"
    )


def _steps(s):
    items = [
        ("01", s["s1_t"], s["s1_b"]),
        ("02", s["s2_t"], s["s2_b"]),
        ("03", s["s3_t"], s["s3_b"]),
    ]
    cards = "".join(
        f'<div class="step"><div class="n">{number}</div>' f"<h3>{title}</h3><p>{text}</p></div>"
        for number, title, text in items
    )
    return (
        '<section class="section" id="guide">'
        f'<div class="kicker">{s["guide_kicker"]}</div>'
        f'<h2 class="title">{s["guide_title"]}</h2>'
        f'<div class="steps">{cards}</div>'
        "</section>"
    )


def _band(lang, s):
    return (
        '<section class="band">'
        f'<h2>{s["band_title"]}</h2>'
        f'<p>{s["band_body"]}</p>'
        f'<a class="btn" href="{DOWNLOAD_URL}">{s["band_download"]}</a>'
        f'<span class="quiet">{s["band_pricing"]} '
        f'<a href="/shop?lang={lang}">{s["nav_pricing"]}</a></span>'
        "</section>"
    )


@router.get("/", response_class=HTMLResponse)
def home(lang: str = ""):
    """The front door."""
    language = _normalize_lang(lang)
    s = _STRINGS[language]
    return _page(
        s["title_home"],
        s["desc"],
        language,
        _header(language, "/", s)
        + _hero(s)
        + _trust(s)
        + _features(s)
        + _showcase(s)
        + _steps(s)
        + _band(language, s)
        + _footer(language, s),
    )


def _pack_cards(s):
    packs = config.topup_packs()
    popular = packs[len(packs) // 2]
    cards = []
    for yuan in packs:
        credits = yuan * config.CREDITS_PER_YUAN
        is_popular = yuan == popular
        badge = f'<span class="badge">{s["popular"]}</span>' if is_popular else ""
        cards.append(
            f'<div class="pack{" popular" if is_popular else ""}">{badge}'
            f'<div class="credits">{s["credits"].format(credits)}</div>'
            f'<div class="price">¥{yuan}</div>'
            f'<div class="hint">{s["pack_hint"].format(credits // 8)}</div>'
            "</div>"
        )
    return "".join(cards)


@router.get("/shop", response_class=HTMLResponse)
def shop(lang: str = ""):
    """The price list. Screenshot material for Alipay's onboarding."""
    language = _normalize_lang(lang)
    s = _STRINGS[language]
    topup = "".join(f"<li>{item}</li>" for item in s["topup_items"])
    refund = "".join(f"<li>{item}</li>" for item in s["refund_items"])
    return _page(
        s["title_shop"],
        s["desc"],
        language,
        _header(language, "/shop", s) + '<section class="section" style="padding-top:56px">'
        f'<div class="kicker">{s["shop_kicker"]}</div>'
        f'<h2 class="title">{s["shop_title"]}</h2>'
        f'<p class="sub">{s["shop_sub"]}</p>'
        "</section>"
        + '<div class="card-panel">'
        + f'<div class="packs">{_pack_cards(s)}</div>'
        + f'<p class="fine">{s["shop_fine"]}</p>'
        + "</div>"
        + '<section class="section">'
        + f'<div class="kicker">{s["topup_kicker"]}</div>'
        + f'<h2 class="title">{s["topup_title"]}</h2>'
        + f"<ul>{topup}</ul>"
        + "</section>"
        + '<section class="section">'
        + f'<div class="kicker">{s["refund_kicker"]}</div>'
        + f'<h2 class="title">{s["refund_title"]}</h2>'
        + f"<ul>{refund}</ul>"
        + "</section>"
        + _footer(language, s),
    )
