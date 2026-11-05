"""Persistent progress for the learning module."""

import json
import os

from checkpause.data.paths import DATA_DIR

PROGRESS_NAME = "learn_progress.json"


def _progress_path(base_dir=None):
    base = base_dir or DATA_DIR
    return os.path.join(base, PROGRESS_NAME)


def load_progress(base_dir=None):
    path = _progress_path(base_dir)
    if not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    raw = data.get("lessons") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    progress = {}
    for lesson_id, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        try:
            step = int(entry.get("step", 0))
        except (TypeError, ValueError):
            continue
        progress[str(lesson_id)] = {
            "step": max(0, step),
            "completed": bool(entry.get("completed", False)),
        }
    return progress


def save_lesson_progress(lesson_id, step, total, completed=False, base_dir=None):
    if not lesson_id:
        return None
    progress = load_progress(base_dir)
    try:
        step = int(step)
        total = int(total)
    except (TypeError, ValueError):
        return None
    progress[lesson_id] = {
        "step": max(0, min(step, total)),
        "completed": bool(completed),
    }
    base = base_dir or DATA_DIR
    os.makedirs(base, exist_ok=True)
    with open(_progress_path(base), "w", encoding="utf-8") as handle:
        json.dump(
            {"version": 1, "lessons": progress},
            handle,
            ensure_ascii=False,
            indent=2,
        )
    return progress[lesson_id]


def reset_progress(base_dir=None):
    base = base_dir or DATA_DIR
    os.makedirs(base, exist_ok=True)
    with open(_progress_path(base), "w", encoding="utf-8") as handle:
        json.dump({"version": 1, "lessons": {}}, handle, ensure_ascii=False, indent=2)
    return {}
