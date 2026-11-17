import unittest

from checkpause.core.pgn import pgn_game_text, pgn_has_moves, scan_pgn_games

GAME_ONE = '[Event "One"]\n[White "Alice"]\n[Black "Bob"]\n\n1. e4 e5 2. Nf3 *'
GAME_TWO = '[Event "Two"]\n[White "Carol"]\n[Black "Dave"]\n\n1. d4 d5 *'


class ScanPgnGamesTests(unittest.TestCase):
    def test_reads_every_game_header_and_slice(self):
        text = f"{GAME_ONE}\n\n{GAME_TWO}\n"

        games = scan_pgn_games(text)

        self.assertEqual(len(games), 2)
        self.assertEqual(games[0].headers["White"], "Alice")
        self.assertEqual(games[1].headers["White"], "Carol")
        self.assertIn("1. e4 e5", pgn_game_text(text, games[0]))
        self.assertNotIn("1. d4 d5", pgn_game_text(text, games[0]))
        self.assertIn("1. d4 d5", pgn_game_text(text, games[1]))
        self.assertNotIn("1. e4 e5", pgn_game_text(text, games[1]))

    def test_a_headerless_game_is_kept(self):
        text = "1. e4 e5 2. Nf3 *"

        games = scan_pgn_games(text)

        self.assertEqual(len(games), 1)
        self.assertEqual(pgn_game_text(text, games[0]), text)

    def test_trailing_text_does_not_become_a_phantom_game(self):
        text = f"{GAME_ONE}\n\ngarbage\n\n"

        games = scan_pgn_games(text)

        self.assertEqual(len(games), 1)
        self.assertEqual(games[0].headers["White"], "Alice")

    def test_empty_input_has_no_games(self):
        self.assertEqual(scan_pgn_games(""), [])
        self.assertEqual(scan_pgn_games(None), [])

    def test_moves_must_exist_for_a_pasted_game(self):
        self.assertTrue(pgn_has_moves("1. e4 e5 *"))
        self.assertFalse(pgn_has_moves('[White "Alice"]\n\n*'))
        self.assertFalse(pgn_has_moves("garbage"))


if __name__ == "__main__":
    unittest.main()
