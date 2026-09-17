"""Server configuration: the tuned prompt, the API key, and where they live.

Nothing sensitive is kept in this repository. The tuned prompt, the upstream
API key and the access token are read from a directory outside the checkout -
``/etc/checkpause`` by default - so they can never be committed, and so the
public copy of this code contains only placeholders.

``CHECKPAUSE_CONFIG_DIR`` overrides that location, which is how the tests point
the code at a temporary directory.
"""

import os
import pathlib

DEFAULT_CONFIG_DIR = "/etc/checkpause"

# Only used when the real prompt file is missing, so a fresh checkout still
# runs and so tests do not need one. Deliberately plain: the tuned prompt is
# what the paid tier is paying for, and it lives on the server.
FALLBACK_SYSTEM_PROMPT = (
    "You are a chess coach. Using the engine data you are given, explain the "
    "player's mistakes in plain, encouraging language."
)

FALLBACK_USER_TEMPLATE = """PGN:
{pgn}

Engine analysis:
{analysis}"""

# Answers are billed by the token, so one reply must not be able to cost an
# unbounded amount. The upstream default is far higher than a coaching answer
# needs; this cap is still comfortably above a normal one.
DEFAULT_MAX_ANSWER_TOKENS = 3000

# Share of a first purchase handed back as bonus credits. Ten percent of a
# CNY 10 top-up means 1100 credits for CNY 10, which trims the first sale's
# margin from about 50% to about 45%. Zero switches the offer off.
DEFAULT_FIRST_TOPUP_BONUS_PERCENT = 10


def config_dir():
    override = os.environ.get("CHECKPAUSE_CONFIG_DIR", "").strip()
    return pathlib.Path(override or DEFAULT_CONFIG_DIR)


def _read(name):
    try:
        return (config_dir() / name).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def system_prompt():
    """The tuned coaching prompt, or the plain fallback."""
    return _read("system_prompt.txt") or FALLBACK_SYSTEM_PROMPT


def user_template():
    """The template that wraps the game and the engine numbers."""
    return _read("user_template.txt") or FALLBACK_USER_TEMPLATE


def using_placeholder_prompt():
    """True when no tuned prompt has been installed yet."""
    return not _read("system_prompt.txt")


def api_key():
    return os.environ.get("DEEPSEEK_API_KEY", "").strip()


def base_url():
    return os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()


def model():
    return os.environ.get("DEEPSEEK_MODEL", "deepseek-chat").strip()


def _positive_int(name, default):
    try:
        value = int(os.environ.get(name, "").strip())
    except ValueError:
        return default
    return value if value > 0 else default


def max_answer_tokens():
    """Upper bound on one reply, so a request cannot cost without limit."""
    return _positive_int(
        "CHECKPAUSE_MAX_ANSWER_TOKENS", DEFAULT_MAX_ANSWER_TOKENS
    )


def first_topup_bonus_percent():
    """Extra credits given on a first purchase, as a percentage."""
    try:
        return max(
            0,
            int(
                os.environ.get(
                    "CHECKPAUSE_FIRST_TOPUP_BONUS_PERCENT", ""
                ).strip()
            ),
        )
    except ValueError:
        return DEFAULT_FIRST_TOPUP_BONUS_PERCENT
