import unittest

from checkpause.core.pgn import (
    parse_pgn_game,
    parse_single_game,
    pgn_game_text,
    scan_pgn_games,
)

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
        game = parse_pgn_game('[White "Alice"]\n\n*')

        self.assertIsNotNone(game)
        self.assertFalse(any(game.mainline_moves()))

    def test_a_single_game_can_be_parsed_for_reuse(self):
        game = parse_single_game(GAME_ONE)

        self.assertIsNotNone(game)
        self.assertEqual(game.headers["White"], "Alice")
        self.assertIsNotNone(parse_pgn_game(GAME_ONE))

    def test_a_collection_is_not_silently_reduced_to_its_first_game(self):
        self.assertIsNone(parse_single_game(f"{GAME_ONE}\n\n{GAME_TWO}\n"))
        self.assertIsNone(parse_single_game(""))


if __name__ == "__main__":
    unittest.main()
