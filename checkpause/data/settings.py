import json
import os
import secrets

from checkpause.data.paths import SETTINGS_FILE, ensure_data_dir
from checkpause.data.secrets import load_secrets, save_secrets

# No provider is baked in: the local tier is whatever the user configures. The
# endpoint and the model have no default on purpose, so nothing here points at a
# particular service.

# The plain-HTTP IP this used before the domain existed. An install may have
# saved it verbatim when the settings dialog was opened; treat it as "unset" so
# upgrading moves to HTTPS instead of staying pinned to the old address. A
# genuinely custom address is left alone.
LEGACY_SERVER_URLS = ("http://43.108.99.244",)

# Address and model an earlier version pre-filled on the user's behalf. They are
# treated as "unset" too, so after an upgrade the dialog opens empty instead of
# showing a provider the user never chose. A value the user typed is kept.
LEGACY_BASE_URLS = ("https://api.deepseek.com",)
LEGACY_MODELS = ("deepseek-flash",)

# Where the paid tier sends its requests. The client only ever sends raw
# material here; the tuned prompt stays on the server.
DEFAULT_SERVER_URL = "https://checkpause.com"

MODE_LOCAL = "local"  # bring your own API key, straight to the provider
MODE_CLOUD = "cloud"  # through the CheckPause server


_SECRET_KEYS = ("api_key", "account_token")


def _read_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, encoding="utf-8") as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    return data
        except (OSError, ValueError):
            return {}
    return {}


def _write_settings(settings):
    ensure_data_dir()
    temp_path = SETTINGS_FILE + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8", newline="") as handle:
            json.dump(settings, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, SETTINGS_FILE)
    finally:
        try:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        except OSError:
            # Best-effort cleanup; the replace already succeeded or failed.
            pass


def load_settings():
    """Non-secret settings, migrating legacy plaintext keys on first read."""
    settings = _read_settings()
    secrets = load_secrets()
    changed = False
    for key in _SECRET_KEYS:
        legacy = str(settings.pop(key, "") or "").strip()
        if legacy:
            secrets[key] = legacy
            changed = True
    if changed:
        if save_secrets(secrets):
            _write_settings(settings)
        else:
            # The secure store is unavailable; keep the values so the user
            # does not lose them. A later save retries the migration.
            for key in _SECRET_KEYS:
                if secrets.get(key):
                    settings[key] = secrets[key]
    return settings


def save_settings(settings):
    """Persist non-secret settings; extract secrets into the secret store."""
    settings = dict(settings or {})
    secrets = load_secrets()
    secrets_changed = False
    for key in _SECRET_KEYS:
        if key not in settings:
            continue
        value = str(settings.pop(key) or "").strip()
        if value != str(secrets.get(key) or "").strip():
            if value:
                secrets[key] = value
            else:
                secrets.pop(key, None)
            secrets_changed = True
    if secrets_changed and not save_secrets(secrets):
        for key in _SECRET_KEYS:
            if secrets.get(key):
                settings[key] = secrets[key]
    _write_settings(settings)
    return settings


def _secret_value(name):
    load_settings()  # migrate legacy plaintext values before reading
    value = load_secrets().get(name)
    if value is None:
        value = _read_settings().get(name)
    return str(value or "").strip()


def get_api_key():
    return _secret_value("api_key")


def get_base_url():
    url = (load_settings().get("base_url") or "").strip()
    return "" if url in LEGACY_BASE_URLS else url


def get_model():
    model = (load_settings().get("model") or "").strip()
    return "" if model in LEGACY_MODELS else model


def get_ai_mode():
    # Cloud is the baseline: an account needs no configuration, and an install
    # that has never chosen a mode is treated as one that wants the cloud path.
    mode = (load_settings().get("ai_mode") or "").strip()
    return mode if mode in (MODE_LOCAL, MODE_CLOUD) else MODE_CLOUD


def get_server_url():
    url = (load_settings().get("server_url") or "").strip()
    if not url or url in LEGACY_SERVER_URLS:
        return DEFAULT_SERVER_URL
    return url


def get_account():
    """The signed-in cloud account.

    Only the session token is kept, never the password: the token can be
    revoked server-side, a password cannot be un-leaked.
    """
    settings = load_settings()
    try:
        account_id = int(settings.get("account_id"))
    except (TypeError, ValueError):
        account_id = None
    return {
        "id": account_id,
        "username": (settings.get("account_username") or "").strip(),
        "token": _secret_value("account_token"),
        "balance": settings.get("account_balance"),
    }


def save_account(username, token, balance=None, account_id=None):
    settings = load_settings()
    settings["account_username"] = (username or "").strip()
    settings["account_token"] = (token or "").strip()
    settings["account_balance"] = balance
    if account_id is None:
        settings.pop("account_id", None)
    else:
        try:
            settings["account_id"] = int(account_id)
        except (TypeError, ValueError):
            settings.pop("account_id", None)
    return save_settings(settings)


def save_balance(balance):
    settings = load_settings()
    settings["account_balance"] = balance
    return save_settings(settings)


def clear_account():
    settings = load_settings()
    for key in ("account_id", "account_username", "account_balance"):
        settings.pop(key, None)
    settings["account_token"] = ""
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
        settings["ai_mode"] = mode if mode in (MODE_LOCAL, MODE_CLOUD) else MODE_CLOUD
    if server_url is not None:
        settings["server_url"] = (server_url or "").strip()
    return save_settings(settings)


def set_ai_mode(mode):
    """Remember which tier the app should use, without touching the key."""
    settings = load_settings()
    settings["ai_mode"] = mode if mode in (MODE_LOCAL, MODE_CLOUD) else MODE_CLOUD
    return save_settings(settings)


def get_stockfish_override():
    return (load_settings().get("stockfish_path") or "").strip()


def set_stockfish_path(path):
    settings = load_settings()
    settings["stockfish_path"] = (path or "").strip()
    return save_settings(settings)


def get_share_reviews():
    """Whether review content may be collected to improve the model.

    There is no in-app switch for this: consent is given once, by accepting the
    agreement shown during installation, so this is always true here. It exists
    so the choice has one named place rather than being assumed in the client.
    """
    return True


def get_install_id():
    """A random per-install id, created once.

    It gives the server something to count a rate limit against without knowing
    who the user is. It is deliberately not derived from any hardware or account
    value, so it identifies the install and nothing else.
    """
    settings = load_settings()
    install_id = (settings.get("install_id") or "").strip()
    if install_id:
        return install_id
    install_id = secrets.token_hex(16)
    settings["install_id"] = install_id
    save_settings(settings)
    return install_id
