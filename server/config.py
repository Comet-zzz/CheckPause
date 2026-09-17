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


def access_token():
    """Shared secret expected in the ``X-CheckPause-Token`` header.

    An empty value disables the check, which is only sensible for local work.
    This is a stopgap: it keeps scanners and casual abuse off the endpoint but
    it cannot be a real secret while it ships inside a desktop client. Real
    accounts replace it in the next milestone.
    """
    return os.environ.get("CHECKPAUSE_ACCESS_TOKEN", "").strip()
