import os

import chess
import chess.pgn

from checkpause.resources import resource_path

OPENINGS_FILE_PARTS = ("assets", "openings.pgn")


def _openings_path():
    path = resource_path(*OPENINGS_FILE_PARTS)
    if os.path.isfile(path):
        return path
    return None


def load_openings(path=None):
    """Return the bundled opening lines as ``{"name", "moves"}`` dicts.

    ``moves`` is a list of legal ``chess.Move`` objects leading from the
    starting position. Unreadable or illegal lines are skipped.
    """
    path = path or _openings_path()
    if not path or not os.path.isfile(path):
        return []

    openings = []
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        while True:
            try:
                game = chess.pgn.read_game(handle)
            except Exception:
                break
            if game is None:
                break
            moves = _legal_prefix(game.mainline_moves())
            if not moves:
                continue
            name = game.headers.get("Opening") or f"Opening {len(openings) + 1}"
            openings.append({"name": name, "moves": moves})
    return openings


def _legal_prefix(moves):
    board = chess.Board()
    legal = []
    for move in moves:
        if move not in board.legal_moves:
            break
        board.push(move)
        legal.append(move)
    return legal
