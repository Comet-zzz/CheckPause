import array
import csv
import io
import json
import os
import uuid

import chess
import chess.pgn

from checkpause.data.paths import DATA_DIR
from checkpause.resources import resource_path

PUZZLE_DIR = os.path.join(DATA_DIR, "puzzles")
INDEX_NAME = "index.json"

BUILTIN_PATH_PARTS = ("assets", "puzzles", "lichess_sample.jsonl")
BUILTIN_ID = "builtin-lichess-sample"
BUILTIN_SOURCE = "https://database.lichess.org/#puzzles"

CSV_EXTENSIONS = {".csv"}
PGN_EXTENSIONS = {".pgn", ".txt"}


class PuzzleImportError(Exception):
    def __init__(self, code, detail=""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def puzzle_dir():
    os.makedirs(PUZZLE_DIR, exist_ok=True)
    return PUZZLE_DIR


def _index_path(base_dir):
    return os.path.join(base_dir, INDEX_NAME)


def load_index(base_dir=None):
    base = base_dir or PUZZLE_DIR
    path = _index_path(base)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def save_index(entries, base_dir=None):
    base = base_dir or puzzle_dir()
    with open(_index_path(base), "w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)


def list_collections(base_dir=None):
    base = base_dir or PUZZLE_DIR
    result = []
    if base_dir is None and not is_builtin_hidden(base):
        builtin = builtin_collection()
        if builtin is not None:
            result.append(builtin)
    for meta in load_index(base):
        if not isinstance(meta, dict):
            continue
        path = meta.get("file")
        if path and os.path.isfile(path):
            result.append(meta)
    return result


def is_builtin_hidden(base_dir=None):
    base = base_dir or PUZZLE_DIR
    for meta in load_index(base):
        if (
            isinstance(meta, dict)
            and meta.get("id") == BUILTIN_ID
            and meta.get("hidden")
        ):
            return True
    return False


def builtin_collection():
    path = resource_path(*BUILTIN_PATH_PARTS)
    if not os.path.isfile(path):
        return None
    return {
        "id": BUILTIN_ID,
        "name": "Lichess Sample",
        "file": path,
        "format": "jsonl",
        "builtin": True,
        "source": BUILTIN_SOURCE,
    }


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def iter_lichess_csv(handle):
    reader = csv.DictReader(handle)
    for row in reader:
        fen = (row.get("FEN") or "").strip()
        moves = (row.get("Moves") or "").split()
        if not fen or not moves:
            continue
        yield {
            "id": (row.get("PuzzleId") or "").strip(),
            "fen": fen,
            "moves": moves,
            "rating": _to_int(row.get("Rating")),
            "themes": (row.get("Themes") or "").split(),
            "opponent_first": True,
        }


def iter_pgn_puzzles(text):
    stream = io.StringIO(text)
    while True:
        game = chess.pgn.read_game(stream)
        if game is None:
            break
        fen = (game.headers.get("FEN") or "").strip()
        moves = [move.uci() for move in game.mainline_moves()]
        if not fen or not moves:
            continue
        yield {
            "id": (game.headers.get("Event") or "").strip(),
            "fen": fen,
            "moves": moves,
            "rating": _to_int(game.headers.get("Rating")),
            "themes": (game.headers.get("Themes") or "").split(),
            "opponent_first": False,
        }


def iter_puzzles(path):
    ext = os.path.splitext(path)[1].lower()
    if ext in CSV_EXTENSIONS:
        with open(
            path, "r", encoding="utf-8-sig", errors="replace", newline=""
        ) as handle:
            yield from iter_lichess_csv(handle)
    elif ext in PGN_EXTENSIONS:
        with open(path, "r", encoding="utf-8", errors="replace") as handle:
            yield from iter_pgn_puzzles(handle.read())
    else:
        raise PuzzleImportError("unsupported_format")


def _remove_quietly(path):
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass


def import_collection(path, name=None, progress=None, base_dir=None):
    base = base_dir or puzzle_dir()
    os.makedirs(base, exist_ok=True)
    collection_id = uuid.uuid4().hex[:12]
    target = os.path.join(base, collection_id + ".jsonl")
    count = 0
    try:
        with open(target, "w", encoding="utf-8") as out:
            for puzzle in iter_puzzles(path):
                out.write(
                    json.dumps(puzzle, ensure_ascii=False, separators=(",", ":"))
                )
                out.write("\n")
                count += 1
                if progress is not None and count % 200 == 0:
                    progress(count)
    except PuzzleImportError:
        _remove_quietly(target)
        raise
    except Exception as exc:
        _remove_quietly(target)
        raise PuzzleImportError("read_error", str(exc))
    if count == 0:
        _remove_quietly(target)
        raise PuzzleImportError("empty")
    meta = {
        "id": collection_id,
        "name": name or os.path.splitext(os.path.basename(path))[0],
        "file": target,
        "format": os.path.splitext(path)[1].lower().lstrip("."),
        "count": count,
        "source": path,
    }
    entries = load_index(base)
    entries.append(meta)
    save_index(entries, base)
    if progress is not None:
        progress(count)
    return meta


def delete_collection(collection_id, base_dir=None):
    base = base_dir or puzzle_dir()
    entries = load_index(base)
    keep = []
    removed = None
    for meta in entries:
        if isinstance(meta, dict) and meta.get("id") == collection_id:
            removed = meta
            continue
        keep.append(meta)
    if collection_id == BUILTIN_ID:
        keep.append({"id": BUILTIN_ID, "builtin": True, "hidden": True})
        save_index(keep, base)
        return True
    if removed is None:
        return False
    save_index(keep, base)
    _remove_quietly(removed.get("file"))
    return True


class PuzzleCollection:
    """Lazy reader over a JSONL puzzle collection."""

    def __init__(self, meta):
        self.meta = dict(meta)
        self.id = self.meta.get("id", "")
        self.name = self.meta.get("name", "")
        self.file = self.meta.get("file", "")
        self.builtin = bool(self.meta.get("builtin"))
        self._offsets = None

    @property
    def count(self):
        value = self.meta.get("count")
        if value is not None:
            return int(value)
        if self._offsets is None:
            self._build_offsets()
        return len(self._offsets)

    def _build_offsets(self):
        offsets = array.array("q")
        with open(self.file, "rb") as handle:
            while True:
                position = handle.tell()
                line = handle.readline()
                if not line:
                    break
                if line.strip():
                    offsets.append(position)
        self._offsets = offsets

    def get(self, index):
        if self._offsets is None:
            self._build_offsets()
        if index < 0 or index >= len(self._offsets):
            return None
        with open(self.file, "rb") as handle:
            handle.seek(self._offsets[index])
            line = handle.readline()
        if not line:
            return None
        try:
            puzzle = json.loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return puzzle if isinstance(puzzle, dict) else None
