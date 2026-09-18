import sys

import chess.engine

STOCKFISH_DIRECTORY = ("stockfish", "stockfish")

_WINDOWS_ENGINE = "stockfish-windows-x86-64-universal.exe"

# Stockfish ships one universal binary for macOS that covers both Apple
# Silicon and Intel, and a plain "stockfish" on Linux.
_MACOS_ENGINE = "stockfish-macos-universal"
_LINUX_ENGINE = "stockfish"


def stockfish_executable_name(platform_name=None):
    """The bundled engine filename for ``platform_name`` (default: this OS)."""
    platform_name = platform_name or sys.platform
    if platform_name == "win32":
        return _WINDOWS_ENGINE
    if platform_name == "darwin":
        return _MACOS_ENGINE
    return _LINUX_ENGINE


STOCKFISH_RELATIVE = STOCKFISH_DIRECTORY + (stockfish_executable_name(),)

OPENING_BOOK_RELATIVE = ("assets", "opening_book.bin")

BOOK_MAX_PLIES = 30
BOOK_MIN_WEIGHT = 1

ENGINE_LIMIT = chess.engine.Limit(depth=18, time=2.0)

PLAY_RATING_MIN = 100
PLAY_RATING_MAX = 3000
PLAY_RATING_DEFAULT = 1500
PLAY_RATING_STEP = 50

# Stockfish cannot limit its own strength through UCI_Elo below roughly this
# rating, so anything weaker is only an approximation built from Skill Level
# plus a node cap. Probe the engine for the real floor before trusting this.
PLAY_ELO_FLOOR = 1320

# Node budgets instead of wall-clock limits keep a level reproducible across
# machines: a slow CPU then thinks longer, but not shallower.
PLAY_WEAK_NODES = (16, 32768)
PLAY_STRONG_NODES = (32768, 1000000)

PLAY_RATING_TIERS = (
    {"id": "beginner", "rating": 600},
    {"id": "easy", "rating": 1000},
    {"id": "medium", "rating": 1500},
    {"id": "hard", "rating": 2100},
    {"id": "master", "rating": 2800},
)


def clamp_play_rating(rating):
    return max(PLAY_RATING_MIN, min(PLAY_RATING_MAX, int(rating)))


def play_rating_tier(rating):
    """Return the tier id whose landmark rating is closest to ``rating``."""
    rating = clamp_play_rating(rating)
    return min(
        PLAY_RATING_TIERS,
        key=lambda tier: abs(tier["rating"] - rating),
    )["id"]


def play_engine_settings(rating, elo_floor=None, supports_elo=True):
    """Translate a target rating into UCI options plus a search budget.

    Ratings at or above ``elo_floor`` use Stockfish's calibrated
    ``UCI_Elo`` limiter. Lower ratings fall back to ``Skill Level`` and a
    logarithmic node cap, so they carry no calibrated meaning. Engines
    without ``UCI_Elo`` always use that approximation.
    """
    rating = clamp_play_rating(rating)
    if not supports_elo:
        return _weak_settings(rating, PLAY_RATING_MAX)

    floor = PLAY_ELO_FLOOR if elo_floor is None else int(elo_floor)
    floor = max(PLAY_RATING_MIN, min(PLAY_RATING_MAX, floor))
    if rating < floor:
        return _weak_settings(rating, floor)

    share = (rating - floor) / max(1, PLAY_RATING_MAX - floor)
    low, high = PLAY_STRONG_NODES
    return {
        "options": {"UCI_LimitStrength": True, "UCI_Elo": rating},
        "nodes": int(round(low + share * (high - low))),
        "approximate": False,
    }


def _weak_settings(rating, floor):
    share = (rating - PLAY_RATING_MIN) / max(1, floor - PLAY_RATING_MIN)
    low, high = PLAY_WEAK_NODES
    return {
        "options": {"Skill Level": round(share * 10)},
        "nodes": int(round(low * (high / low) ** share)),
        "approximate": True,
    }

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
