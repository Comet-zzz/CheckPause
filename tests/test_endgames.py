import unittest

import chess

from checkpause.core.endgames import load_endgames


class EndgamesTests(unittest.TestCase):
    def test_bundled_endgames_are_valid(self):
        endgames = load_endgames()
        self.assertTrue(endgames)
        ids = set()
        for endgame in endgames:
            self.assertTrue(endgame["id"])
            self.assertNotIn(endgame["id"], ids)
            ids.add(endgame["id"])
            board = chess.Board(endgame["fen"])
            self.assertTrue(board.is_valid(), endgame["id"])
            self.assertFalse(board.is_game_over(), endgame["id"])

    def test_load_endgames_returns_copies(self):
        first = load_endgames()
        first[0]["id"] = "changed"
        self.assertNotEqual(load_endgames()[0]["id"], "changed")


if __name__ == "__main__":
    unittest.main()
