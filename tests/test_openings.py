import os
import tempfile
import unittest

import chess

from checkpause.core.openings import (
    OPENING_CATEGORY_ORDER,
    load_openings,
    opening_display_name,
    opening_san,
)


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

    def test_bundled_openings_carry_grouping_and_chinese_names(self):
        openings = load_openings()
        if not openings:
            self.skipTest("bundled openings file is not present")
        for opening in openings:
            self.assertIn(opening["category"], OPENING_CATEGORY_ORDER)
            self.assertTrue(opening["family"])
            self.assertTrue(opening["family_zh"])
            self.assertTrue(opening["name_zh"])
            if ":" in opening["name"]:
                self.assertTrue(opening["variation"])
                self.assertTrue(opening["variation_zh"])

    def test_opening_san_and_localized_name(self):
        with tempfile.TemporaryDirectory() as base:
            path = os.path.join(base, "openings.pgn")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write('[Opening "Test Line"]\n1. e4 e5 2. Nf3\n\n')
            opening = load_openings(path)[0]
        self.assertEqual(opening["category"], "other")
        self.assertEqual(opening_san(opening), "1. e4 e5 2. Nf3")
        self.assertEqual(opening_display_name(opening, "zh-CN"), "Test Line")
        self.assertEqual(opening_display_name(opening, "en-US"), "Test Line")

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
        self.assertEqual([o["name"] for o in openings], ["Test Line", "Second Line"])
        self.assertEqual(len(openings[0]["moves"]), 4)

    def test_missing_file_returns_empty(self):
        self.assertEqual(load_openings("does-not-exist.pgn"), [])


if __name__ == "__main__":
    unittest.main()
