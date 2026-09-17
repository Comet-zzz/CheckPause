import json
import os

from checkpause.data.paths import SETTINGS_FILE, ensure_data_dir

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"

# Where the paid tier sends its requests. The client only ever sends raw
# material here; the tuned prompt stays on the server.
DEFAULT_SERVER_URL = "http://43.108.99.244"

MODE_LOCAL = "local"   # bring your own API key, straight to the provider
MODE_CLOUD = "cloud"   # through the CheckPause server


def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
        except (OSError, ValueError):
            return {}
    return {}


def save_settings(settings):
    ensure_data_dir()
    with open(SETTINGS_FILE, "w", encoding="utf-8") as handle:
        json.dump(settings, handle, ensure_ascii=False, indent=2)
    return settings


def get_api_key():
    key = (load_settings().get("api_key") or "").strip()
    if key:
        return key
    return os.getenv("DEEPSEEK_API_KEY", "").strip()


def get_base_url():
    return (load_settings().get("base_url") or "").strip() or DEFAULT_BASE_URL


def get_model():
    return (load_settings().get("model") or "").strip() or DEFAULT_MODEL


def get_ai_mode():
    mode = (load_settings().get("ai_mode") or "").strip()
    return mode if mode in (MODE_LOCAL, MODE_CLOUD) else MODE_LOCAL


def get_server_url():
    return (load_settings().get("server_url") or "").strip() or DEFAULT_SERVER_URL


def get_account():
    """The signed-in cloud account.

    Only the session token is kept, never the password: the token can be
    revoked server-side, a password cannot be un-leaked.
    """
    settings = load_settings()
    return {
        "username": (settings.get("account_username") or "").strip(),
        "token": (settings.get("account_token") or "").strip(),
        "balance": settings.get("account_balance"),
    }


def save_account(username, token, balance=None):
    settings = load_settings()
    settings["account_username"] = (username or "").strip()
    settings["account_token"] = (token or "").strip()
    settings["account_balance"] = balance
    return save_settings(settings)


def save_balance(balance):
    settings = load_settings()
    settings["account_balance"] = balance
    return save_settings(settings)


def clear_account():
    settings = load_settings()
    for key in ("account_username", "account_token", "account_balance"):
        settings.pop(key, None)
    return save_settings(settings)


def get_api_config():
    return {
        "mode": get_ai_mode(),
        "server_url": get_server_url(),
        "api_key": get_api_key(),
        "base_url": get_base_url(),
        "model": get_model(),
        "account": get_account(),
    }


def save_api_config(api_key, base_url, model, mode=None, server_url=None):
    settings = load_settings()
    settings["api_key"] = (api_key or "").strip()
    settings["base_url"] = (base_url or "").strip()
    settings["model"] = (model or "").strip()
    if mode is not None:
        settings["ai_mode"] = mode if mode in (MODE_LOCAL, MODE_CLOUD) else MODE_LOCAL
    if server_url is not None:
        settings["server_url"] = (server_url or "").strip()
    return save_settings(settings)


def get_stockfish_override():
    return (load_settings().get("stockfish_path") or "").strip()


def set_stockfish_path(path):
    settings = load_settings()
    settings["stockfish_path"] = (path or "").strip()
    return save_settings(settings)
