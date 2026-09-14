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

ENGINE_PLAY_LEVELS = (
    {"id": "beginner", "skill": 0, "depth": 1, "time": 0.05},
    {"id": "easy", "skill": 4, "depth": 2, "time": 0.1},
    {"id": "medium", "skill": 8, "depth": 5, "time": 0.3},
    {"id": "hard", "skill": 14, "depth": 9, "time": 0.8},
    {"id": "master", "skill": 20, "depth": 14, "time": 1.5},
)
DEFAULT_PLAY_LEVEL = "medium"

PLAY_TIME_CONTROLS = (
    {"id": "unlimited", "base": None, "increment": 0},
    {"id": "bullet_1_0", "base": 60, "increment": 0},
    {"id": "blitz_3_0", "base": 180, "increment": 0},
    {"id": "blitz_3_2", "base": 180, "increment": 2},
    {"id": "blitz_5_0", "base": 300, "increment": 0},
    {"id": "blitz_5_3", "base": 300, "increment": 3},
    {"id": "rapid_10_0", "base": 600, "increment": 0},
    {"id": "rapid_10_5", "base": 600, "increment": 5},
    {"id": "rapid_15_10", "base": 900, "increment": 10},
    {"id": "classical_30_0", "base": 1800, "increment": 0},
)
DEFAULT_PLAY_TIME = "unlimited"

SYSTEM_PROMPT = "Please answer user's questions based on the provided PGN game and Stockfish analysis data."

USER_PROMPT_TEMPLATE = """This is the PGN game and Stockfish analysis data:

PGN Game:
{棋谱}

Stockfish Analysis Data per move:
{数据}"""
