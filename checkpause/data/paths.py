import os
import sys

from checkpause import APP_NAME


def data_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, APP_NAME)
    return os.path.join(os.path.expanduser("~"), "." + APP_NAME.lower())


DATA_DIR = data_dir()
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    return DATA_DIR
