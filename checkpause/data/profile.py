import json
import os
from datetime import datetime

from checkpause import BASE_DIR
from checkpause.assets import (
    DEFAULT_BOARD_THEME,
    DEFAULT_PIECE_SET,
    DEFAULT_SOUND_SET,
    SOUND_CHOICES,
    SOUND_OFF,
)
from checkpause.config import (
    DEFAULT_EVAL_DEPTH,
    DEFAULT_HINT_ENABLED,
    EVAL_DEPTH_OPTIONS,
)
from checkpause.data.paths import PROFILE_FILE, ensure_data_dir

LEGACY_PROFILE_FILE = os.path.join(BASE_DIR, "profile.json")


def _normalize(profile):
    profile.setdefault("language", "zh-CN")
    profile.setdefault("theme", "light")
    profile.setdefault("piece_set", DEFAULT_PIECE_SET)
    profile.setdefault("board_theme", DEFAULT_BOARD_THEME)
    if "sound_set" not in profile:
        # Migrate the on/off boolean used before sound sets existed.
        profile["sound_set"] = (
            SOUND_OFF if profile.get("sound") is False else DEFAULT_SOUND_SET
        )
    profile.pop("sound", None)
    if profile["sound_set"] not in SOUND_CHOICES:
        profile["sound_set"] = DEFAULT_SOUND_SET
    profile.pop("eval_enabled", None)
    profile.setdefault("hint_enabled", DEFAULT_HINT_ENABLED)
    if profile.get("eval_depth") not in EVAL_DEPTH_OPTIONS:
        profile["eval_depth"] = DEFAULT_EVAL_DEPTH
    return profile


def delete_profile():
    if os.path.exists(PROFILE_FILE):
        os.remove(PROFILE_FILE)
        return True
    return False


def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, encoding="utf-8") as handle:
            return _normalize(json.load(handle))

    if os.path.exists(LEGACY_PROFILE_FILE):
        with open(LEGACY_PROFILE_FILE, encoding="utf-8") as handle:
            profile = _normalize(json.load(handle))
        save_profile(profile)
        try:
            os.remove(LEGACY_PROFILE_FILE)
        except OSError:
            pass
        return profile

    return None


def save_profile(profile):
    ensure_data_dir()
    with open(PROFILE_FILE, "w", encoding="utf-8") as handle:
        json.dump(profile, handle, ensure_ascii=False, indent=2)


def create_profile(username, language="zh-CN"):
    profile = {
        "username": username,
        "language": language,
        "theme": "light",
        "piece_set": DEFAULT_PIECE_SET,
        "board_theme": DEFAULT_BOARD_THEME,
        "sound_set": DEFAULT_SOUND_SET,
        "hint_enabled": DEFAULT_HINT_ENABLED,
        "eval_depth": DEFAULT_EVAL_DEPTH,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_games": 0,
        "history": [],
        "latest_accuracy": None
    }
    save_profile(profile)
    return profile


def set_language(profile, language):
    profile["language"] = language
    save_profile(profile)
    return profile


def set_theme(profile, theme):
    profile["theme"] = theme
    save_profile(profile)
    return profile


def set_piece_set(profile, piece_set):
    profile["piece_set"] = piece_set
    save_profile(profile)
    return profile


def set_board_theme(profile, board_theme):
    profile["board_theme"] = board_theme
    save_profile(profile)
    return profile


def set_sound_set(profile, name):
    profile["sound_set"] = name if name in SOUND_CHOICES else DEFAULT_SOUND_SET
    save_profile(profile)
    return profile


def set_hint_enabled(profile, enabled):
    profile["hint_enabled"] = bool(enabled)
    save_profile(profile)
    return profile


def set_eval_depth(profile, depth):
    profile["eval_depth"] = (
        depth if depth in EVAL_DEPTH_OPTIONS else DEFAULT_EVAL_DEPTH
    )
    save_profile(profile)
    return profile


def update_profile(profile, accuracy, pgn):
    profile["total_games"] += 1
    profile["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": accuracy,
        "pgn": pgn[:200] + "..." if len(pgn) > 200 else pgn
    })
    if len(profile["history"]) > 20:
        profile["history"] = profile["history"][-20:]
    profile["latest_accuracy"] = accuracy
    save_profile(profile)
    return profile


def get_accuracy_trend(profile):
    history = profile["history"]
    if len(history) < 2:
        return None
    recent = history[-3:] if len(history) >= 3 else history
    values = [h["accuracy"] for h in recent]
    if len(values) >= 2:
        diff = values[-1] - values[-2]
        if diff > 0:
            return f"↑ +{diff:.1f}%"
        elif diff < 0:
            return f"↓ {abs(diff):.1f}%"
        else:
            return "stable"
    return None


def get_avg_accuracy(profile):
    if not profile["history"]:
        return None
    total = sum(h["accuracy"] for h in profile["history"])
    return total / len(profile["history"])
