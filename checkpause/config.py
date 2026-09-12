import chess.engine

STOCKFISH_RELATIVE = (
    "stockfish",
    "stockfish",
    "stockfish-windows-x86-64-universal.exe",
)

OPENING_BOOK_RELATIVE = ("assets", "opening_book.bin")

BOOK_MAX_PLIES = 30
BOOK_MIN_WEIGHT = 1

ENGINE_LIMIT = chess.engine.Limit(depth=18, time=2.0)

SYSTEM_PROMPT = "Please answer user's questions based on the provided PGN game and Stockfish analysis data."

USER_PROMPT_TEMPLATE = """This is the PGN game and Stockfish analysis data:

PGN Game:
{棋谱}

Stockfish Analysis Data per move:
{数据}"""
