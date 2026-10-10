"""Read a chess position out of an axis-aligned board screenshot.

Everything here runs on the user's machine: a small ONNX classifier scores the
64 squares, the result is checked against the rules of chess, and the caller
gets a FEN to confirm. No image is uploaded anywhere, and the module does not
import Qt, so the geometry, the FEN assembly and the validation can be tested
on their own with a stand-in classifier.

The model is trained offline by ``tools/train_recognizer.py`` from synthetic
boards rendered with the bundled piece sets.
"""

import chess
import numpy as np

# Class order the bundled model is trained with: index 0 is an empty square,
# 1-6 are the white pieces, 7-12 the black ones. The letters double as the FEN
# alphabet, uppercase for White.
CLASSES = ("1", "P", "N", "B", "R", "Q", "K", "p", "n", "b", "r", "q", "k")

BOARD_LEN = 8
MODEL_CELL = 32  # side of the square patch the model takes
BOARD_PATCH = MODEL_CELL * BOARD_LEN

# The board search scores each candidate grid by how cleanly its two square
# colours alternate; a real board separates the two families far better than a
# misaligned grid or a plain screenshot background.
_MIN_SCORE = 0.3


class RecognizeError(RuntimeError):
    """A board could not be read; ``code`` names the i18n message to show."""

    def __init__(self, code):
        super().__init__(code)
        self.code = code


def resize_rgb(image, out_h, out_w):
    """Bilinear resize of an (H, W, 3) image, shared by runtime and training."""
    image = np.asarray(image, dtype=np.float32)
    h, w = image.shape[:2]
    if h == out_h and w == out_w:
        return image.copy()
    ys = (np.arange(out_h) + 0.5) * (h / out_h) - 0.5
    xs = (np.arange(out_w) + 0.5) * (w / out_w) - 0.5
    y0 = np.clip(np.floor(ys).astype(np.int64), 0, h - 1)
    x0 = np.clip(np.floor(xs).astype(np.int64), 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    x1 = np.clip(x0 + 1, 0, w - 1)
    wy = np.clip(ys - y0, 0.0, 1.0)[:, None, None]
    wx = np.clip(xs - x0, 0.0, 1.0)[None, :, None]
    top = image[y0][:, x0] * (1.0 - wx) + image[y0][:, x1] * wx
    bottom = image[y1][:, x0] * (1.0 - wx) + image[y1][:, x1] * wx
    return top * (1.0 - wy) + bottom * wy


def _as_rgb(image):
    array = np.asarray(image)
    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
    if array.ndim != 3 or array.shape[2] < 3:
        raise RecognizeError("image_error_invalid")
    return array[..., :3].astype(np.float32)


def _downscale(image, max_side):
    h, w = image.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1.0:
        return image, 1.0
    out_h = max(1, int(round(h * scale)))
    out_w = max(1, int(round(w * scale)))
    return resize_rgb(image, out_h, out_w), scale


def _box_sum(image, size):
    """Sum every ``size`` x ``size`` window, aligned to its top-left pixel."""
    padded = np.zeros((image.shape[0] + 1, image.shape[1] + 1, image.shape[2]))
    padded[1:, 1:] = image
    integral = padded.cumsum(0).cumsum(1)
    return (
        integral[size:, size:]
        - integral[:-size, size:]
        - integral[size:, :-size]
        + integral[:-size, :-size]
    )


def _ring_colors(image, size):
    """The colour of each cell's border ring.

    Pieces sit in the middle of a cell, so the ring of pixels just inside the
    cell edge is almost always bare square colour. Scoring that instead of the
    full cell keeps dense positions from confusing the board search.
    """
    border = max(1, size // 8)
    inner = size - 2 * border
    if inner < 1:
        return None
    if size > image.shape[0] or size > image.shape[1]:
        return None
    outer = _box_sum(image, size)
    inner_sum = _box_sum(image, inner)
    oh, ow = outer.shape[:2]
    aligned = inner_sum[border : border + oh, border : border + ow]
    area = float(size * size - inner * inner)
    return (outer * (size * size) - aligned * (inner * inner)) / area


def _window_scores(grid):
    """Best 8x8 checkerboard fit across ``grid``: (score, row, col) or None."""
    gh, gw = grid.shape[:2]
    if gh < BOARD_LEN or gw < BOARD_LEN:
        return None
    windows = np.lib.stride_tricks.sliding_window_view(
        grid, (BOARD_LEN, BOARD_LEN), axis=(0, 1)
    ).transpose(0, 1, 3, 4, 2)
    rows, cols = np.mgrid[0:BOARD_LEN, 0:BOARD_LEN]
    even = ((rows + cols) % 2 == 0).astype(np.float32)[..., None]
    odd = 1.0 - even
    count = even.sum()
    mean_even = (windows * even).sum((2, 3)) / count
    mean_odd = (windows * odd).sum((2, 3)) / count
    var_even = (((windows - mean_even[:, :, None, None, :]) ** 2) * even).sum((2, 3)) / count
    var_odd = (((windows - mean_odd[:, :, None, None, :]) ** 2) * odd).sum((2, 3)) / count
    separation = ((mean_even - mean_odd) ** 2).mean(axis=-1)
    spread = (var_even + var_odd).mean(axis=-1)
    score = separation / (spread + 1e-3)
    index = np.unravel_index(np.argmax(score), score.shape)
    return float(score[index]), int(index[0]), int(index[1])


def _score_block(block):
    """Checkerboard fit of one 8x8 block of ring colours."""
    rows, cols = np.mgrid[0:BOARD_LEN, 0:BOARD_LEN]
    even = (rows + cols) % 2 == 0
    mean_even = block[even].mean(axis=0)
    mean_odd = block[~even].mean(axis=0)
    spread = ((block[even] - mean_even) ** 2).mean() + ((block[~even] - mean_odd) ** 2).mean()
    return float(((mean_even - mean_odd) ** 2).mean() / (spread + 1e-3))


def _score_at(ring, x, y, size):
    ys = y + np.arange(BOARD_LEN) * size
    xs = x + np.arange(BOARD_LEN) * size
    if x < 0 or y < 0 or ys[-1] >= ring.shape[0] or xs[-1] >= ring.shape[1]:
        return None
    return _score_block(ring[np.ix_(ys, xs)])


def _candidate_sizes(min_side):
    low = max(6, min_side // 20)
    high = max(low + 1, min_side // 6)
    sizes = np.linspace(low, high, 24)
    return sorted({int(round(value)) for value in sizes})


def _refine(image, x, y, size, score):
    """Nudge the coarse grid to the exact cell size and pixel origin."""
    best = (score, x, y, size)
    for candidate in range(max(6, size - 8), size + 9):
        ring = _ring_colors(image, candidate)
        if ring is None:
            continue
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                value = _score_at(ring, x + dx, y + dy, candidate)
                if value is not None and value > best[0]:
                    best = (value, x + dx, y + dy, candidate)
    return best


def detect_board(image, max_side=512):
    """Locate the 8x8 board and return its ``(x, y, size)`` box in pixels."""
    scaled, scale = _downscale(_as_rgb(image), max_side)
    min_side = min(scaled.shape[0], scaled.shape[1])
    best = None
    for size in _candidate_sizes(min_side):
        ring = _ring_colors(scaled, size)
        if ring is None:
            continue
        step = max(1, size // 12)
        for offset_y in range(0, size, step):
            for offset_x in range(0, size, step):
                grid = ring[offset_y::size, offset_x::size]
                found = _window_scores(grid)
                if found is None:
                    continue
                score, row, col = found
                if best is None or score > best[0]:
                    x = offset_x + col * size
                    y = offset_y + row * size
                    best = (score, x, y, size)
    if best is None or best[0] < _MIN_SCORE:
        raise RecognizeError("image_error_board")
    best = _refine(scaled, best[1], best[2], best[3], best[0])
    if best[0] < _MIN_SCORE:
        raise RecognizeError("image_error_board")
    _, x, y, size = best
    inv = 1.0 / scale
    span = size * BOARD_LEN
    return (
        int(round(x * inv)),
        int(round(y * inv)),
        max(1, int(round(span * inv))),
    )


def extract_cells(image, box, cell=MODEL_CELL):
    """Return the 64 squares as ``(64, cell, cell, 3)`` float patches."""
    x, y, size = box
    board = _as_rgb(image)[y : y + size, x : x + size]
    board = resize_rgb(board, cell * BOARD_LEN, cell * BOARD_LEN)
    reshaped = board.reshape(BOARD_LEN, cell, BOARD_LEN, cell, 3)
    return reshaped.transpose(0, 2, 1, 3, 4).reshape(-1, cell, cell, 3)


def fen_from_labels(labels):
    """Turn an 8x8 array of class indices into a FEN placement string."""
    rows = []
    for row in range(BOARD_LEN):
        text = ""
        empty = 0
        for col in range(BOARD_LEN):
            letter = CLASSES[int(labels[row][col])]
            if letter == "1":
                empty += 1
                continue
            if empty:
                text += str(empty)
                empty = 0
            text += letter
        if empty:
            text += str(empty)
        rows.append(text)
    return "/".join(rows) + " w - - 0 1"


def validate_fen(fen):
    """Rule issues that hint the reading may be wrong, as short codes."""
    board = chess.Board(fen)
    issues = []
    if len(board.pieces(chess.KING, chess.WHITE)) != 1:
        issues.append("kings")
    if len(board.pieces(chess.KING, chess.BLACK)) != 1:
        issues.append("kings")
    for color in (chess.WHITE, chess.BLACK):
        if len(board.pieces(chess.PAWN, color)) > 8:
            issues.append("pawns")
            break
    if "pawns" not in issues:
        for color in (chess.WHITE, chess.BLACK):
            for square in board.pieces(chess.PAWN, color):
                if chess.square_rank(square) in (0, 7):
                    issues.append("pawns")
                    break
            if "pawns" in issues:
                break
    return issues


class OnnxClassifier:
    """Runs the bundled classifier; the only place onnxruntime is imported."""

    def __init__(self, path):
        import onnxruntime

        self._session = onnxruntime.InferenceSession(path, providers=["CPUExecutionProvider"])
        self._input = self._session.get_inputs()[0].name

    def predict(self, cells):
        batch = np.asarray(cells, dtype=np.float32).transpose(0, 3, 1, 2) / 255.0
        logits = self._session.run(None, {self._input: batch})[0]
        logits = logits - logits.max(axis=1, keepdims=True)
        probabilities = np.exp(logits)
        probabilities /= probabilities.sum(axis=1, keepdims=True)
        return probabilities.argmax(axis=1), probabilities.max(axis=1)


def load_classifier():
    """Open the bundled model, or raise a ``RecognizeError`` naming the gap."""
    from checkpause.resources import get_recognizer_model_path

    path = get_recognizer_model_path()
    if not path:
        raise RecognizeError("image_error_model")
    try:
        return OnnxClassifier(path)
    except ImportError as exc:
        raise RecognizeError("image_error_runtime") from exc


def recognize(image, classifier=None, flipped=False):
    """Read a board image into a FEN plus per-cell confidence and issues."""
    box = detect_board(image)
    cells = extract_cells(image, box)
    model = classifier if classifier is not None else load_classifier()
    labels, confidence = model.predict(cells)
    labels = np.asarray(labels).reshape(BOARD_LEN, BOARD_LEN)
    if flipped:
        labels = labels[::-1, ::-1]
    fen = fen_from_labels(labels)
    return {
        "fen": fen,
        "box": box,
        "confidence": float(np.min(confidence)),
        "issues": validate_fen(fen),
    }
