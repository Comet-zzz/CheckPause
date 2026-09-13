"""Build the bundled puzzle sample from the Lichess puzzle database.

The full database (https://database.lichess.org/#puzzles) is released under
CC0 and contains millions of puzzles. Downloading all of it (~300 MB
compressed) is impractical to ship, so this script fetches only the first
megabytes of the zstd stream via an HTTP range request, then keeps a
rating-stratified, validated sample.

Usage:
    pip install zstandard
    python tools/build_puzzles.py

Output: assets/puzzles/lichess_sample.jsonl
"""

import csv
import io
import json
import os
import sys
import urllib.request

import chess
import zstandard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from checkpause.core.puzzle import PuzzleSession  # noqa: E402

SOURCE_URL = "https://database.lichess.org/lichess_db_puzzle.csv.zst"
OUT_PATH = os.path.join(ROOT, "assets", "puzzles", "lichess_sample.jsonl")

MAX_COMPRESSED_BYTES = 4 * 1024 * 1024
MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
MAX_ROWS = 400000
PER_BUCKET = 300
TARGET = 2000

MIN_POPULARITY = 80
MIN_PLAYS = 50


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _fetch_range(url, max_bytes):
    request = urllib.request.Request(
        url,
        headers={
            "Range": f"bytes=0-{max_bytes - 1}",
            "User-Agent": "CheckPause-build/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        return response.read(max_bytes)


def _decompress(data):
    reader = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data))
    buffer = bytearray()
    try:
        while len(buffer) < MAX_DECOMPRESSED_BYTES:
            chunk = reader.read(1 << 20)
            if not chunk:
                break
            buffer += chunk
    except zstandard.ZstdError:
        pass
    finally:
        reader.close()
    return bytes(buffer)


def _is_valid(fen, moves):
    try:
        session = PuzzleSession(fen, moves, opponent_first=True)
    except Exception:
        return False
    guards = 0
    while not session.solved:
        guards += 1
        if guards > 40:
            return False
        if session.is_human_turn:
            uci = session.expected_move
            if not uci:
                return False
            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                return False
            if move not in session.board.legal_moves:
                return False
            if session.play(move) == "wrong":
                return False
        elif session.opponent_reply() is None:
            return False
    return True


def _collect(buffer):
    text = buffer.decode("utf-8", errors="ignore")
    if "\n" in text:
        text = text.rsplit("\n", 1)[0]
    reader = csv.DictReader(io.StringIO(text))
    buckets = {}
    seen = 0
    for row in reader:
        seen += 1
        if seen > MAX_ROWS:
            break
        fen = (row.get("FEN") or "").strip()
        moves = (row.get("Moves") or "").split()
        if not fen or not moves:
            continue
        rating = _to_int(row.get("Rating"))
        if rating is None:
            continue
        if (_to_int(row.get("Popularity")) or 0) < MIN_POPULARITY:
            continue
        if (_to_int(row.get("NbPlays")) or 0) < MIN_PLAYS:
            continue
        bucket = buckets.setdefault(min(rating // 200, 15), [])
        if len(bucket) >= PER_BUCKET:
            continue
        bucket.append(
            {
                "id": (row.get("PuzzleId") or "").strip(),
                "fen": fen,
                "moves": moves,
                "rating": rating,
                "themes": (row.get("Themes") or "").split(),
                "opponent_first": True,
            }
        )
    return buckets, seen


def _select(buckets):
    selected = []
    keys = sorted(buckets)
    while len(selected) < TARGET:
        progressed = False
        for key in keys:
            bucket = buckets[key]
            if bucket and len(selected) < TARGET:
                selected.append(bucket.pop(0))
                progressed = True
        if not progressed:
            break
    return selected


def build():
    print(f"downloading first {MAX_COMPRESSED_BYTES // (1024 * 1024)} MB ...")
    data = _fetch_range(SOURCE_URL, MAX_COMPRESSED_BYTES)
    buffer = _decompress(data)
    print(f"decompressed {len(buffer) // (1024 * 1024)} MB")

    buckets, seen = _collect(buffer)
    candidates = _select(buckets)
    print(f"scanned {seen} rows, sampled {len(candidates)} candidates")

    valid = [
        puzzle
        for puzzle in candidates
        if _is_valid(puzzle["fen"], puzzle["moves"])
    ]
    valid.sort(key=lambda item: item["rating"])
    print(f"validated {len(valid)} puzzles")

    if not valid:
        print("no puzzles were produced")
        return 1

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        for puzzle in valid:
            handle.write(
                json.dumps(puzzle, ensure_ascii=False, separators=(",", ":"))
            )
            handle.write("\n")

    ratings = [puzzle["rating"] for puzzle in valid]
    print(
        f"written {len(valid)} puzzles "
        f"(rating {min(ratings)}-{max(ratings)}) to {OUT_PATH}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(build())
