import os
import tempfile
import unittest

import chess

from checkpause.core.openings import load_openings


class OpeningsTests(unittest.TestCase):
    def test_bundled_openings_are_legal(self):
        openings = load_openings()
        if not openings:
            self.skipTest("bundled openings file is not present")
        for opening in openings:
            self.assertTrue(opening["name"])
            board = chess.Board()
            for move in opening["moves"]:
                self.assertIn(move, board.legal_moves)
                board.push(move)

    def test_custom_openings_file(self):
        text = (
            '[Opening "Test Line"]\n'
            "1. e4 e5 2. Nf3 Nc6\n\n"
            '[Opening "Second Line"]\n'
            "1. d4 d5 2. c4 e6\n"
        )
        with tempfile.TemporaryDirectory() as base:
            path = os.path.join(base, "openings.pgn")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            openings = load_openings(path)
        self.assertEqual(
            [o["name"] for o in openings], ["Test Line", "Second Line"]
        )
        self.assertEqual(len(openings[0]["moves"]), 4)

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_openings("does-not-exist.pgn"), [])


if __name__ == "__main__":
    unittest.main()
