import unittest

import chess

from checkpause.core.puzzle_game import history_from_pgn

PGN = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"


class PuzzleGameHistoryTests(unittest.TestCase):
    def test_stops_at_the_puzzle_position(self):
        board = chess.Board()
        board.push_san("e4")
        moves, start_fen = history_from_pgn(PGN, board.fen())
        self.assertIsNone(start_fen)
        self.assertEqual([move.uci() for move in moves], ["e2e4"])

    def test_opponent_first_includes_the_setup_move(self):
        board = chess.Board()
        board.push_san("e4")
        moves, _ = history_from_pgn(PGN, board.fen(), opponent_first=True)
        self.assertEqual([move.uci() for move in moves], ["e2e4", "e7e5"])

    def test_unknown_position_has_no_history(self):
        moves, start_fen = history_from_pgn(PGN, chess.Board().fen())
        self.assertEqual(moves, [])
        self.assertIsNone(start_fen)

    def test_accepts_a_non_standard_start(self):
        fen = "4k3/8/8/8/8/8/8/4K2R w K - 0 1"
        pgn = f'[SetUp "1"]\n[FEN "{fen}"]\n\n1. O-O'
        board = chess.Board(fen)
        board.push_san("O-O")
        moves, start_fen = history_from_pgn(pgn, board.fen())
        self.assertEqual(start_fen, fen)
        self.assertEqual([move.uci() for move in moves], ["e1g1"])


if __name__ == "__main__":
    unittest.main()
