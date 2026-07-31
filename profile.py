import json
import os
from datetime import datetime

PROFILE_FILE = "profile.json"

def load_profile():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(profile):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

def create_profile(username):
    profile = {
        "username": username,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_games": 0,
        "history": [],
        "latest_accuracy": None
    }
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