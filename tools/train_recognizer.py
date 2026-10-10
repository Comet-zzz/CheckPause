"""Train the board-screenshot classifier and export it to ONNX.

Offline only, never shipped. It renders synthetic boards from the bundled
piece sets (plus colour, noise, blur and highlight augmentation) so a small
network can read the 64 squares of a screenshot, then writes
``assets/recognition/board_cnn.onnx`` - the file ``core/recognize.py`` runs
through onnxruntime.

Run it in an environment with the training requirements installed::

    pip install -r requirements-train.txt
    python tools/train_recognizer.py --epochs 3 --boards-per-epoch 4000

The output is a work in progress: every new piece style the user might meet
should be added to ``assets/pieces`` and the model retrained.
"""

import argparse
import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import chess  # noqa: E402
import numpy as np  # noqa: E402
import onnx  # noqa: E402
import torch  # noqa: E402
from PySide6.QtCore import QRectF  # noqa: E402
from PySide6.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402
from torch import nn  # noqa: E402

from checkpause.assets import PIECE_SETS  # noqa: E402
from checkpause.core.recognize import (  # noqa: E402
    BOARD_LEN,
    MODEL_CELL,
    resize_rgb,
)

CELL_PX = 40
BOARD_PX = CELL_PX * BOARD_LEN
SPRITE_PX = 64
OUTPUT_PATH = os.path.join("assets", "recognition", "board_cnn.onnx")
PIECES_DIR = os.path.join("assets", "pieces")

PIECE_INDEX = {
    (chess.PAWN, chess.WHITE): 1,
    (chess.KNIGHT, chess.WHITE): 2,
    (chess.BISHOP, chess.WHITE): 3,
    (chess.ROOK, chess.WHITE): 4,
    (chess.QUEEN, chess.WHITE): 5,
    (chess.KING, chess.WHITE): 6,
    (chess.PAWN, chess.BLACK): 7,
    (chess.KNIGHT, chess.BLACK): 8,
    (chess.BISHOP, chess.BLACK): 9,
    (chess.ROOK, chess.BLACK): 10,
    (chess.QUEEN, chess.BLACK): 11,
    (chess.KING, chess.BLACK): 12,
}


def _sprite_filename(piece_type, color):
    letter = chess.piece_symbol(piece_type).upper()
    prefix = "w" if color == chess.WHITE else "b"
    return f"{prefix}{letter}.svg"


def _qimage_rgba(image):
    image = image.convertToFormat(QImage.Format.Format_RGBA8888)
    width, height = image.width(), image.height()
    stride = image.bytesPerLine()
    rows = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(height, stride)
    return rows[:, : width * 4].reshape(height, width, 4).copy()


def load_sprites():
    """Rasterise every piece of every bundled set to an RGBA array."""
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    _ = app
    sprites = {}
    for name in PIECE_SETS:
        pieces = {}
        for piece_type, color in PIECE_INDEX:
            path = os.path.join(PIECES_DIR, name, _sprite_filename(piece_type, color))
            renderer = QSvgRenderer(path)
            image = QImage(SPRITE_PX, SPRITE_PX, QImage.Format.Format_RGBA8888)
            image.fill(0)
            painter = QPainter(image)
            renderer.render(painter, QRectF(0, 0, SPRITE_PX, SPRITE_PX))
            painter.end()
            pieces[PIECE_INDEX[(piece_type, color)]] = _qimage_rgba(image).astype(np.float32)
        sprites[name] = pieces
    return list(sprites.values())


def random_position(rng):
    board = chess.Board()
    for _ in range(int(rng.integers(0, 70))):
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(moves[int(rng.integers(len(moves)))])
    return board


def _paste(board, sprite, row, col, rng):
    scale = float(rng.uniform(0.78, 1.0))
    side = max(8, int(round(CELL_PX * scale)))
    scaled = resize_rgb(sprite, side, side)
    max_off = CELL_PX - side
    off_y = int(rng.integers(0, max_off + 1)) if max_off > 0 else 0
    off_x = int(rng.integers(0, max_off + 1)) if max_off > 0 else 0
    y0 = row * CELL_PX + off_y
    x0 = col * CELL_PX + off_x
    region = board[y0 : y0 + side, x0 : x0 + side]
    alpha = scaled[..., 3:4] / 255.0
    board[y0 : y0 + side, x0 : x0 + side] = region * (1.0 - alpha) + scaled[..., :3] * alpha


def _box_blur(image):
    padded = np.pad(image, ((1, 1), (1, 1), (0, 0)), mode="edge")
    total = np.zeros_like(image)
    for dy in range(3):
        for dx in range(3):
            total += padded[dy : dy + image.shape[0], dx : dx + image.shape[1]]
    return total / 9.0


def _augment(board, rng):
    board = np.clip(board * float(rng.uniform(0.85, 1.15)) + float(rng.uniform(-12, 12)), 0, 255)
    if rng.random() < 0.4:
        board = _box_blur(board)
    noise = rng.normal(0.0, float(rng.uniform(0.0, 8.0)), board.shape)
    return np.clip(board + noise, 0, 255)


def _highlight(board, rng):
    if rng.random() >= 0.15:
        return board
    row = int(rng.integers(BOARD_LEN))
    col = int(rng.integers(BOARD_LEN))
    color = np.array([246, 220, 92], np.float32)
    y0, x0 = row * CELL_PX, col * CELL_PX
    region = board[y0 : y0 + CELL_PX, x0 : x0 + CELL_PX]
    board[y0 : y0 + CELL_PX, x0 : x0 + CELL_PX] = region * 0.6 + color * 0.4
    return board


def render_board(labels, pieces, rng):
    light = rng.integers(150, 255, 3).astype(np.float32)
    dark = rng.integers(40, 140, 3).astype(np.float32)
    board = np.zeros((BOARD_PX, BOARD_PX, 3), np.float32)
    for row in range(BOARD_LEN):
        for col in range(BOARD_LEN):
            board[row * CELL_PX : (row + 1) * CELL_PX, col * CELL_PX : (col + 1) * CELL_PX] = (
                light if (row + col) % 2 == 0 else dark
            )
    for row in range(BOARD_LEN):
        for col in range(BOARD_LEN):
            index = int(labels[row][col])
            if index:
                _paste(board, pieces[index], row, col, rng)
    board = _highlight(board, rng)
    return _augment(board, rng)


def sample_batch(rng, sprites, boards):
    labels_batch = np.zeros((boards, BOARD_LEN, BOARD_LEN), np.int64)
    patches = np.zeros((boards * 64, 3, MODEL_CELL, MODEL_CELL), np.float32)
    targets = np.zeros(boards * 64, np.int64)
    for b in range(boards):
        position = random_position(rng)
        labels = np.zeros((BOARD_LEN, BOARD_LEN), np.int64)
        for square in chess.SQUARES:
            piece = position.piece_at(square)
            if piece is None:
                continue
            row = BOARD_LEN - 1 - chess.square_rank(square)
            col = chess.square_file(square)
            labels[row][col] = PIECE_INDEX[(piece.piece_type, piece.color)]
        labels_batch[b] = labels
        pieces = sprites[int(rng.integers(len(sprites)))]
        board = render_board(labels, pieces, rng)
        small = resize_rgb(board, BOARD_LEN * MODEL_CELL, BOARD_LEN * MODEL_CELL)
        reshaped = small.reshape(BOARD_LEN, MODEL_CELL, BOARD_LEN, MODEL_CELL, 3)
        cells = reshaped.transpose(0, 2, 1, 3, 4).reshape(-1, MODEL_CELL, MODEL_CELL, 3)
        base = b * 64
        patches[base : base + 64] = cells.transpose(0, 3, 1, 2)
        targets[base : base + 64] = labels.reshape(-1)
    return torch.from_numpy(patches / 255.0), torch.from_numpy(targets)


class BoardCNN(nn.Module):
    def __init__(self, classes=13):
        super().__init__()

        def block(cin, cout):
            return nn.Sequential(
                nn.Conv2d(cin, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
                nn.Conv2d(cout, cout, 3, padding=1, bias=False),
                nn.BatchNorm2d(cout),
                nn.ReLU(inplace=True),
                nn.MaxPool2d(2),
            )

        self.features = nn.Sequential(block(3, 32), block(32, 64), block(64, 96), block(96, 128))
        self.head = nn.Linear(128, classes)

    def forward(self, x):
        x = self.features(x)
        x = x.mean(dim=(2, 3))
        return self.head(x)


def evaluate(model, rng, sprites, boards):
    model.eval()
    patches, targets = sample_batch(rng, sprites, boards)
    with torch.no_grad():
        predictions = model(patches).argmax(1)
    return float((predictions == targets).float().mean())


def train(args):
    rng = np.random.default_rng(1234)
    torch.manual_seed(1234)
    sprites = load_sprites()
    model = BoardCNN()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss()

    model.train()
    steps = max(1, args.boards_per_epoch // args.batch_boards)
    for epoch in range(args.epochs):
        for step in range(steps):
            patches, targets = sample_batch(rng, sprites, args.batch_boards)
            optimizer.zero_grad()
            loss = criterion(model(patches), targets)
            loss.backward()
            optimizer.step()
            if step % args.log_every == 0:
                print(f"epoch {epoch + 1}/{args.epochs} step {step}/{steps} loss {loss.item():.4f}")
        print(f"epoch {epoch + 1} train accuracy {evaluate(model, rng, sprites, 64):.4f}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    model.eval()
    dummy = torch.zeros(1, 3, MODEL_CELL, MODEL_CELL)
    torch.onnx.export(
        model,
        dummy,
        OUTPUT_PATH,
        input_names=["input"],
        output_names=["logits"],
        dynamic_axes={"input": {0: "n"}, "logits": {0: "n"}},
        opset_version=17,
    )
    # torch writes the weights to a sidecar .data file; inline them so the app
    # ships one self-contained model.
    onnx.save_model(onnx.load(OUTPUT_PATH), OUTPUT_PATH, save_as_external_data=False)
    if os.path.exists(OUTPUT_PATH + ".data"):
        os.remove(OUTPUT_PATH + ".data")
    print(f"saved {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--boards-per-epoch", type=int, default=4000)
    parser.add_argument("--batch-boards", type=int, default=48)
    parser.add_argument("--log-every", type=int, default=20)
    train(parser.parse_args())


if __name__ == "__main__":
    main()
