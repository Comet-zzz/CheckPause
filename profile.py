import json
import os
from datetime import datetime

PROFILE_FILE = "profile.json"

def load_profile():
    """加载用户档案，如果不存在则返回 None"""
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_profile(profile):
    """保存用户档案"""
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

def create_profile(username):
    """首次创建用户档案"""
    profile = {
        "username": username,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_games": 0,
        "history": [],
        "latest_accuracy": None,
        "latest_issues": None
    }
    save_profile(profile)
    return profile

def update_profile(profile, accuracy, issues, pgn):
    """更新用户档案（每次分析完成后调用）"""
    profile["total_games"] += 1
    profile["history"].append({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "accuracy": accuracy,
        "issues": issues,
        "pgn": pgn[:200] + "..." if len(pgn) > 200 else pgn
    })
    if len(profile["history"]) > 20:
        profile["history"] = profile["history"][-20:]
    profile["latest_accuracy"] = accuracy
    profile["latest_issues"] = issues
    save_profile(profile)
    return profile

def get_accuracy_trend(profile):
    """获取进步趋势（最近3局的准确度变化）"""
    history = profile["history"]
    if len(history) < 2:
        return None
    recent = history[-3:] if len(history) >= 3 else history
    values = [h["accuracy"] for h in recent]
    if len(values) >= 2:
        diff = values[-1] - values[-2]
        if diff > 0:
            return f"↑ 提升 {diff:.1f}%"
        elif diff < 0:
            return f"↓ 下降 {abs(diff):.1f}%"
        else:
            return "持平"
    return None

def get_avg_accuracy(profile):
    """获取平均准确度"""
    if not profile["history"]:
        return None
    total = sum(h["accuracy"] for h in profile["history"])
    return total / len(profile["history"])