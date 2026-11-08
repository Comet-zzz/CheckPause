"""Inline the generated board SVGs into the static page."""

from __future__ import annotations

import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[0]

template = (HERE / "index.template.html").read_text(encoding="utf-8")
hero = (HERE / "hero-board.svg").read_text(encoding="utf-8")
mate = (HERE / "mate-board.svg").read_text(encoding="utf-8")
icon = base64.b64encode((ROOT / "assets" / "icons" / "app_icon.svg").read_bytes()).decode("ascii")

html = (
    template.replace("<!--HERO_BOARD-->", hero)
    .replace("<!--MATE_BOARD-->", mate)
    .replace(
        "<!--FAVICON-->",
        f'<link rel="icon" href="data:image/svg+xml;base64,{icon}">',
    )
)

(HERE / "index.html").write_text(html, encoding="utf-8")
print("index.html", (HERE / "index.html").stat().st_size, "bytes")
