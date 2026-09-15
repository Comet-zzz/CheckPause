import unittest

import chess

from checkpause.core.play_session import PlaySession


def uci(name):
    return chess.Move.from_uci(name)


class PlaySessionTests(unittest.TestCase):
    def test_new_game_defaults(self):
        session = PlaySession()
        self.assertEqual(session.human_color, chess.WHITE)
        self.assertEqual(session.moves, [])
        self.assertEqual(session.start_fen, None)
        self.assertFalse(session.game_over)
        self.assertIsNone(session.result_kind)
        self.assertIsNone(session.clock_remaining)

    def test_new_game_from_opening(self):
        session = PlaySession()
        session.new_game(opening_moves=[uci("e2e4"), uci("e7e5")])
        self.assertEqual(len(session.moves), 2)
        self.assertEqual(session.opening_ply, 2)
        self.assertEqual(session.board.fen().split()[0], "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR")

    def test_new_game_from_fen(self):
        fen = "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"
        session = PlaySession()
        session.new_game(start_fen=fen)
        self.assertEqual(session.start_fen, fen)
        self.assertEqual(session.board.fen(), fen)

    def test_push_and_undo_human_white(self):
        session = PlaySession(human_color=chess.WHITE)
        session.push(uci("e2e4"))
        session.push(uci("e7e5"))
        self.assertTrue(session.can_undo())
        self.assertTrue(session.undo())
        self.assertEqual(session.moves, [])
        self.assertFalse(session.can_undo())

    def test_undo_stops_at_opening(self):
        session = PlaySession()
        session.new_game(opening_moves=[uci("e2e4"), uci("e7e5")])
        session.push(uci("g1f3"))
        self.assertTrue(session.undo())
        self.assertEqual(len(session.moves), session.opening_ply)
        self.assertFalse(session.undo())

    def test_finish_if_over(self):
        session = PlaySession(human_color=chess.WHITE)
        session.new_game()
        self.assertFalse(session.finish_if_over())

        session.new_game(start_fen="7k/6Q1/6K1/8/8/8/8/8 b - - 0 1")
        self.assertTrue(session.finish_if_over())
        self.assertTrue(session.game_over)
        self.assertEqual(session.result_kind, "win")

    def test_resign_and_timeout(self):
        session = PlaySession(human_color=chess.WHITE)
        session.resign()
        self.assertTrue(session.game_over)
        self.assertEqual(session.result_kind, "resign")

        session = PlaySession(human_color=chess.WHITE)
        session.timeout(chess.WHITE)
        self.assertEqual(session.result_kind, "timeout_lose")
        session = PlaySession(human_color=chess.WHITE)
        session.timeout(chess.BLACK)
        self.assertEqual(session.result_kind, "timeout_win")

    def test_clock_lifecycle(self):
        session = PlaySession()
        session.new_game(
            time_control={"base": 5.0, "increment": 3.0}, now=0.0
        )
        self.assertEqual(session.clock_remaining, {chess.WHITE: 5.0, chess.BLACK: 5.0})
        self.assertFalse(session.clock_should_run())
        session.push(uci("e2e4"))
        self.assertTrue(session.clock_should_run())
        session.start_clock(10.0)
        self.assertIsNone(session.tick(11.0))
        self.assertAlmostEqual(session.clock_remaining[chess.BLACK], 4.0)
        self.assertEqual(session.board.turn, chess.BLACK)

    def test_clock_flag_and_increment(self):
        session = PlaySession()
        session.new_game(time_control={"base": 1.0, "increment": 2.0}, now=0.0)
        session.push(uci("e2e4"))
        session.start_clock(0.0)
        self.assertEqual(session.tick(2.0), chess.BLACK)
        self.assertEqual(session.clock_remaining[chess.BLACK], 0.0)

        session = PlaySession()
        session.new_game(time_control={"base": 5.0, "increment": 2.0}, now=0.0)
        session.push(uci("e2e4"))
        self.assertEqual(session.clock_remaining[chess.WHITE], 7.0)

    def test_pause_blocks_clock(self):
        session = PlaySession()
        session.new_game(time_control={"base": 5.0}, now=0.0)
        session.push(uci("e2e4"))
        self.assertTrue(session.clock_should_run())
        self.assertTrue(session.toggle_pause())
        self.assertFalse(session.clock_should_run())
        self.assertFalse(session.toggle_pause())
        self.assertTrue(session.clock_should_run())

    def test_clock_disabled(self):
        session = PlaySession()
        session.new_game(time_control={"base": None, "increment": 0}, now=0.0)
        session.push(uci("e2e4"))
        self.assertFalse(session.clock_enabled)
        self.assertFalse(session.clock_should_run())
        self.assertIsNone(session.tick(1.0))

    def test_format_clock(self):
        self.assertEqual(PlaySession.format_clock(5.25), "5.2")
        self.assertEqual(PlaySession.format_clock(65), "1:05")
        self.assertEqual(PlaySession.format_clock(-1), "0.0")


if __name__ == "__main__":
    unittest.main()
