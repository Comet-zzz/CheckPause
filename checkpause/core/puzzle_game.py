"""Load a puzzle's source game so the sidebar can show the full move list."""

import io
import json
import urllib.parse
import urllib.request

import chess
import chess.pgn

LICHESS_PUZZLE_API = "https://lichess.org/api/puzzle/{puzzle_id}"
_HISTORY_CACHE = {}


def _same_position(left, right):
    return (
        left.board_fen(),
        left.turn,
        left.castling_rights,
    ) == (
        right.board_fen(),
        right.turn,
        right.castling_rights,
    )


def history_from_pgn(pgn, fen, opponent_first=False):
    """Return the moves leading to ``fen`` and the game's starting FEN.

    The returned line stops at the puzzle's setup move, so the solution is not
    exposed. Moves are ``chess.Move`` objects.
    """
    try:
        target = chess.Board(fen)
    except ValueError:
        return [], None
    game = chess.pgn.read_game(io.StringIO(pgn or ""))
    if game is None:
        return [], None
    start_fen = None
    if game.headers.get("SetUp") == "1" and game.headers.get("FEN"):
        start_fen = game.headers["FEN"]
    moves = list(game.mainline_moves())
    board = game.board()
    for index, move in enumerate(moves):
        if _same_position(board, target):
            end = index + 1 if opponent_first else index
            return moves[:end], start_fen
        board.push(move)
    if _same_position(board, target):
        return moves, start_fen
    return [], None


def fetch_pgn(puzzle_id, timeout=6):
    url = LICHESS_PUZZLE_API.format(puzzle_id=urllib.parse.quote(str(puzzle_id), safe=""))
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "CheckPause"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    pgn = (data.get("game") or {}).get("pgn") or ""
    if not pgn:
        raise ValueError("puzzle game has no PGN")
    return pgn


def load_history(puzzle_id, fen, opponent_first=False, timeout=6):
    """Fetch and parse the game, caching by puzzle id and position."""
    key = (str(puzzle_id), fen, bool(opponent_first))
    if key in _HISTORY_CACHE:
        return _HISTORY_CACHE[key]
    pgn = fetch_pgn(puzzle_id, timeout=timeout)
    history = history_from_pgn(pgn, fen, opponent_first)
    _HISTORY_CACHE[key] = history
    return history
