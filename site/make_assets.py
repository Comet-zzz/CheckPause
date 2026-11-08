"""Generate marketing board SVGs from the app's own piece files.

Run with the project venv:
    .venv\\Scripts\\python.exe site\\make_assets.py
"""

from __future__ import annotations

import base64
import math
from pathlib import Path

import chess

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PIECES = ROOT / "assets" / "pieces" / "kiwen-suwi"

S = 80
M = 38
SIZE = S * 8
W = SIZE + 2 * M

LIGHT = "#dee3e6"
DARK = "#8ca2ad"
FRAME = "#12151c"
COORD = "#cfd8e3"

ACCENT = "#5fe1ff"
GOLD = "#b08a3e"
ALERT = "#ff4d9d"


def piece_uri(symbol: str, piece_set: str = "kiwen-suwi") -> str:
    color = "w" if symbol.isupper() else "b"
    name = f"{color}{symbol.upper()}"
    raw = (ROOT / "assets" / "pieces" / piece_set / f"{name}.svg").read_text(encoding="utf-8")
    head, rest = raw.split(">", 1)
    if "viewBox" not in head:
        raw = head.replace("<svg", '<svg viewBox="0 0 260 260"', 1) + ">" + rest
    encoded = base64.b64encode(raw.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def square_xy(square: int) -> tuple[float, float]:
    return (
        M + chess.square_file(square) * S,
        M + (7 - chess.square_rank(square)) * S,
    )


def square_rect(square: int, inset: float = 0) -> tuple[float, float, float, float]:
    x, y = square_xy(square)
    return x + inset, y + inset, S - 2 * inset, S - 2 * inset


def arrow(
    tail: int,
    head: int,
    color: str,
    width: float = 10,
    head_len: float = 27,
    opacity: float = 1,
) -> str:
    x1, y1 = square_xy(tail)
    x2, y2 = square_xy(head)
    x1 += S / 2
    y1 += S / 2
    x2 += S / 2
    y2 += S / 2

    angle = math.atan2(y2 - y1, x2 - x1)
    ux, uy = math.cos(angle), math.sin(angle)
    px, py = -uy, ux

    line_x = x2 - ux * head_len * 0.86
    line_y = y2 - uy * head_len * 0.86
    base_x = x2 - ux * head_len
    base_y = y2 - uy * head_len
    half = head_len * 0.6

    p1 = (base_x + px * half, base_y + py * half)
    p2 = (base_x - px * half, base_y - py * half)

    return (
        f'<line class="arrow-line" x1="{x1:.2f}" y1="{y1:.2f}" '
        f'x2="{line_x:.2f}" y2="{line_y:.2f}" stroke="{color}" '
        f'stroke-width="{width}" stroke-linecap="round" opacity="{opacity}" pathLength="1"/>'
        f'<path class="arrow-head" d="M{x2:.2f} {y2:.2f} '
        f'L{p1[0]:.2f} {p1[1]:.2f} L{p2[0]:.2f} {p2[1]:.2f} Z" '
        f'fill="{color}" opacity="{opacity}"/>'
    )


def render(
    fen: str,
    *,
    piece_set: str = "kiwen-suwi",
    last_move: tuple[int, int] | None = None,
    arrows: list[str] | None = None,
    marks: list[tuple[int, str, float, str | None]] | None = None,
    frame: str = FRAME,
) -> str:
    board = chess.Board(fen)
    assert board.is_valid(), f"invalid FEN: {fen}"

    parts: list[str] = [
        f'<rect width="{W}" height="{W}" rx="12" fill="{frame}"/>',
        f'<rect x="{M - 1}" y="{M - 1}" width="{SIZE + 2}" height="{SIZE + 2}" '
        f'fill="none" stroke="#ffffff" stroke-opacity=".07"/>',
    ]

    for rank in range(8):
        for file in range(8):
            x = M + file * S
            y = M + (7 - rank) * S
            fill = DARK if (file + rank) % 2 == 0 else LIGHT
            parts.append(f'<rect x="{x}" y="{y}" width="{S}" height="{S}" fill="{fill}"/>')

    if last_move:
        for square in last_move:
            x, y, w, h = square_rect(square)
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                f'fill="{GOLD}" fill-opacity=".20"/>'
            )

    for square, color, opacity, stroke in marks or []:
        x, y, w, h = square_rect(square, 2)
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
            f'fill="{color}" fill-opacity="{opacity}" rx="3"'
            + (f' stroke="{stroke}" stroke-opacity=".55" stroke-width="2.5"' if stroke else "")
            + "/>"
        )

    parts.extend(arrows or [])

    for square, piece in board.piece_map().items():
        x, y = square_xy(square)
        parts.append(
            f'<image x="{x}" y="{y}" width="{S}" height="{S}" '
            f'href="{piece_uri(piece.symbol(), piece_set)}"/>'
        )

    for file in range(8):
        x = M + file * S + S / 2
        parts.append(
            f'<text x="{x:.1f}" y="{M + SIZE + 26}" text-anchor="middle" '
            f'fill="{COORD}" fill-opacity=".55" font-size="13" '
            f'font-family="Consolas, monospace" letter-spacing="1">'
            f"{chr(ord('a') + file)}</text>"
        )
    for rank in range(8):
        y = M + (7 - rank) * S + S / 2 + 4
        parts.append(
            f'<text x="{M - 15}" y="{y:.1f}" text-anchor="middle" '
            f'fill="{COORD}" fill-opacity=".55" font-size="13" '
            f'font-family="Consolas, monospace">'
            f"{rank + 1}</text>"
        )

    body = "".join(parts)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {W}" '
        f'aria-hidden="true">{body}</svg>'
    )


def main() -> None:
    # Morphy - Duke of Brunswick, Paris 1858. Position after 15...Nxd7.
    hero_fen = "4k2r/p2n1ppp/4q3/4p1B1/8/1Q6/PPP2PPP/2KR4 w - - 0 16"
    hero_board = chess.Board(hero_fen)
    qb8 = chess.Move.from_uci("b3b8")
    nxb8 = chess.Move.from_uci("d7b8")
    rd8 = chess.Move.from_uci("d1d8")
    assert qb8 in hero_board.legal_moves
    hero_board.push(qb8)
    assert nxb8 in hero_board.legal_moves
    hero_board.push(nxb8)
    assert rd8 in hero_board.legal_moves
    hero_board.push(rd8)
    assert hero_board.is_checkmate(), "expected mate after 17.Rd8#"

    hero = render(
        hero_fen,
        piece_set="kiwen-suwi",
        arrows=[arrow(chess.B3, chess.B8, ACCENT, width=10, head_len=27, opacity=0.92)],
        marks=[
            (chess.B3, ACCENT, 0.0, ACCENT),
            (chess.B8, ACCENT, 0.16, ACCENT),
        ],
    )
    (OUT / "hero-board.svg").write_text(hero, encoding="utf-8")

    mate_fen = "1n1Rk2r/p4ppp/4q3/4p1B1/8/8/PPP2PPP/2KR4 b - - 0 17"
    mate_board = chess.Board(mate_fen)
    assert mate_board.is_valid() and mate_board.is_checkmate()

    mate = render(
        mate_fen,
        piece_set="kiwen-suwi",
        marks=[
            (chess.D8, ACCENT, 0.16, ACCENT),
            (chess.E8, ALERT, 0.14, ALERT),
        ],
        frame=FRAME,
    )
    (OUT / "mate-board.svg").write_text(mate, encoding="utf-8")

    print("hero-board.svg", (OUT / "hero-board.svg").stat().st_size, "bytes")
    print("mate-board.svg", (OUT / "mate-board.svg").stat().st_size, "bytes")
    print("hero arrow square:", chess.square_name(chess.B3), "->", chess.square_name(chess.B8))


if __name__ == "__main__":
    main()
