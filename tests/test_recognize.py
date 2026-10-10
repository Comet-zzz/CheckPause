import unittest

import numpy as np

from checkpause.core import recognize as rec


def _make_board(labels, cell=40, margin=55):
    """A synthetic screenshot: two square colours with a blob per piece.

    The blob sits in the middle of the cell, so the border ring the detector
    samples stays bare square colour - exactly like a real board.
    """
    size = cell * rec.BOARD_LEN
    image = np.full((size + 2 * margin, size + 2 * margin, 3), 210, np.float32)
    light = np.array([240, 240, 228], np.float32)
    dark = np.array([120, 160, 92], np.float32)
    for row in range(rec.BOARD_LEN):
        for col in range(rec.BOARD_LEN):
            y0 = margin + row * cell
            x0 = margin + col * cell
            image[y0 : y0 + cell, x0 : x0 + cell] = light if (row + col) % 2 == 0 else dark
            if labels[row][col]:
                y1 = y0 + cell // 2
                x1 = x0 + cell // 2
                image[y1 - 8 : y1 + 8, x1 - 8 : x1 + 8] = (row * 20 + 40, col * 20 + 40, 90)
    return image


class _FakeClassifier:
    def __init__(self, labels, confidence=1.0):
        self._labels = np.asarray(labels).reshape(-1)
        self._confidence = confidence

    def predict(self, cells):
        return self._labels, np.full(cells.shape[0], self._confidence, np.float32)


class TestGeometry(unittest.TestCase):
    def test_detects_board_box(self):
        labels = np.zeros((8, 8), int)
        labels[7, 4] = 6
        image = _make_board(labels)
        x, y, size = rec.detect_board(image)
        self.assertAlmostEqual(x, 55, delta=3)
        self.assertAlmostEqual(y, 55, delta=3)
        self.assertAlmostEqual(size, 320, delta=8)

    def test_blank_image_has_no_board(self):
        blank = np.full((300, 300, 3), 128, np.float32)
        with self.assertRaises(rec.RecognizeError) as ctx:
            rec.detect_board(blank)
        self.assertEqual(ctx.exception.code, "image_error_board")

    def test_extract_cells_shape(self):
        image = _make_board(np.zeros((8, 8), int))
        box = rec.detect_board(image)
        cells = rec.extract_cells(image, box)
        self.assertEqual(cells.shape, (64, rec.MODEL_CELL, rec.MODEL_CELL, 3))

    def test_resize_keeps_average(self):
        image = np.full((4, 4, 3), 100.0, np.float32)
        resized = rec.resize_rgb(image, 2, 2)
        self.assertEqual(resized.shape, (2, 2, 3))
        self.assertAlmostEqual(float(resized.mean()), 100.0, places=4)


class TestFen(unittest.TestCase):
    def test_placement(self):
        labels = np.zeros((8, 8), int)
        labels[7, 4] = 6  # white king on e1
        labels[0, 4] = 12  # black king on e8
        self.assertEqual(rec.fen_from_labels(labels), "4k3/8/8/8/8/8/8/4K3 w - - 0 1")

    def test_pawns_and_files_run_length(self):
        labels = np.zeros((8, 8), int)
        labels[6, 0] = 1
        labels[6, 1] = 1
        rows = rec.fen_from_labels(labels).split(" ")[0].split("/")
        self.assertEqual(rows[6], "PP6")

    def test_validate_flags_pawn_on_back_rank(self):
        self.assertEqual(rec.validate_fen("P6k/8/8/8/8/8/8/7K w - - 0 1"), ["pawns"])

    def test_validate_flags_missing_king(self):
        self.assertEqual(rec.validate_fen("8/8/8/8/8/8/8/7K w - - 0 1"), ["kings"])

    def test_validate_accepts_normal_position(self):
        self.assertEqual(rec.validate_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1"), [])


class TestRecognize(unittest.TestCase):
    def test_end_to_end_with_fake_model(self):
        labels = np.zeros((8, 8), int)
        labels[7, 4] = 6
        labels[0, 4] = 12
        labels[6, 3] = 1
        image = _make_board(labels)
        result = rec.recognize(image, classifier=_FakeClassifier(labels))
        self.assertEqual(result["fen"], "4k3/8/8/8/8/8/3P4/4K3 w - - 0 1")
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["confidence"], 1.0)

    def test_flipped_rotates_one_hundred_eighty(self):
        labels = np.zeros((8, 8), int)
        labels[7, 4] = 6
        labels[0, 4] = 12
        image = _make_board(labels)
        result = rec.recognize(image, classifier=_FakeClassifier(labels), flipped=True)
        self.assertEqual(result["fen"], "3K4/8/8/8/8/8/8/3k4 w - - 0 1")


if __name__ == "__main__":
    unittest.main()
