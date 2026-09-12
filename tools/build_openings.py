import os
import sys

import chess
import chess.pgn
import chess.polyglot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PGN_PATH = os.path.join(ROOT, "assets", "openings.pgn")
OUT_PATH = os.path.join(ROOT, "assets", "opening_book.bin")

PROMOTION_PARTS = {
    None: 0,
    chess.KNIGHT: 1,
    chess.BISHOP: 2,
    chess.ROOK: 3,
    chess.QUEEN: 4,
}


def encode_move(move):
    return (
        (move.to_square & 0x3F)
        | ((move.from_square & 0x3F) << 6)
        | (PROMOTION_PARTS[move.promotion] << 12)
    )


def build():
    entries = {}
    games = 0
    plies = 0

    with open(PGN_PATH, "r", encoding="utf-8") as handle:
        while True:
            game = chess.pgn.read_game(handle)
            if game is None:
                break
            games += 1
            board = chess.Board()
            for move in game.mainline_moves():
                if move not in board.legal_moves:
                    name = game.headers.get("Opening", "?")
                    print(f"illegal move {move} in '{name}' at ply {plies + 1}")
                    return 1
                key = chess.polyglot.zobrist_hash(board)
                raw_move = encode_move(move)
                moves = entries.setdefault(key, {})
                moves[raw_move] = moves.get(raw_move, 0) + 1
                board.push(move)
                plies += 1

    with open(OUT_PATH, "wb") as out:
        for key in sorted(entries):
            for raw_move, weight in entries[key].items():
                out.write(
                    chess.polyglot.ENTRY_STRUCT.pack(key, raw_move, weight, 0)
                )

    print(f"games: {games}, positions: {len(entries)}, plies: {plies}")
    print(f"written: {OUT_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
