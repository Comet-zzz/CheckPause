import json
import os

from checkpause.data.paths import SETTINGS_FILE, ensure_data_dir

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-flash"


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


def get_api_config():
    return {
        "api_key": get_api_key(),
        "base_url": get_base_url(),
        "model": get_model(),
    }


def save_api_config(api_key, base_url, model):
    settings = load_settings()
    settings["api_key"] = (api_key or "").strip()
    settings["base_url"] = (base_url or "").strip()
    settings["model"] = (model or "").strip()
    return save_settings(settings)


def get_stockfish_override():
    return (load_settings().get("stockfish_path") or "").strip()


def set_stockfish_path(path):
    settings = load_settings()
    settings["stockfish_path"] = (path or "").strip()
    return save_settings(settings)
