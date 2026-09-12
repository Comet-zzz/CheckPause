import os
import sys

from checkpause import BASE_DIR
from checkpause.config import OPENING_BOOK_RELATIVE, STOCKFISH_RELATIVE
from checkpause.i18n import t


def resource_path(*parts):
    if getattr(sys, "frozen", False):
        base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        base = BASE_DIR
    return os.path.join(base, *parts)


def _stockfish_candidates():
    from checkpause.data.settings import get_stockfish_override

    override = get_stockfish_override()
    if override:
        yield override

    env_path = os.getenv("STOCKFISH_PATH", "").strip()
    if env_path:
        yield env_path

    yield resource_path(*STOCKFISH_RELATIVE)

    if getattr(sys, "frozen", False):
        yield os.path.join(os.path.dirname(sys.executable), *STOCKFISH_RELATIVE)

    yield os.path.join(BASE_DIR, *STOCKFISH_RELATIVE)


def get_stockfish_path(language="zh-CN"):
    for path in _stockfish_candidates():
        if path and os.path.isfile(path):
            return path
    raise RuntimeError(t("stockfish_missing", language))


def get_opening_book_path():
    candidates = [resource_path(*OPENING_BOOK_RELATIVE)]
    if getattr(sys, "frozen", False):
        candidates.append(
            os.path.join(os.path.dirname(sys.executable), *OPENING_BOOK_RELATIVE)
        )
    candidates.append(os.path.join(BASE_DIR, *OPENING_BOOK_RELATIVE))
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None
