import io
from dataclasses import dataclass

import chess.pgn


@dataclass(frozen=True)
class PgnGame:
    """Where one game sits in a PGN document, plus its header tags."""

    offset: int
    end: int
    headers: dict


def scan_pgn_games(text):
    """Return every game in ``text`` without parsing all of their moves.

    Header scanning is much cheaper than parsing complete games, which keeps a
    large collection usable in a picker. Headerless games are checked for at
    least one move so trailing text does not become a phantom entry.
    """
    games = []
    handle = io.StringIO(text or "")
    while True:
        offset = handle.tell()
        try:
            headers = chess.pgn.read_headers(handle)
        except (ValueError, OSError):
            break
        if headers is None:
            break
        end = handle.tell()
        if not headers:
            handle.seek(offset)
            try:
                game = chess.pgn.read_game(handle)
            except (ValueError, OSError):
                break
            if game is None or not _has_moves(game):
                continue
            headers = game.headers
            end = handle.tell()
        games.append(PgnGame(offset=offset, end=end, headers=dict(headers)))
    return games


def pgn_game_text(text, game):
    """The exact slice of ``text`` belonging to one scanned game."""
    return (text or "")[game.offset : game.end].strip()


def pgn_has_moves(text):
    """Whether a single-game PGN contains at least one legal mainline move."""
    try:
        game = chess.pgn.read_game(io.StringIO(text or ""))
    except (ValueError, OSError):
        return False
    return game is not None and _has_moves(game)


def _has_moves(game):
    try:
        return any(game.mainline_moves())
    except (ValueError, OSError):
        return False
