import io
import os
import tempfile
import unittest
from unittest import mock

import chess

from checkpause.core.puzzle import PuzzleSession
from checkpause.data import puzzles

CSV_HEADER = (
    "PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays,"
    "Themes,GameUrl,OpeningTags\n"
)
CSV_ROW = (
    "00sHx,q3k1nr/1pp1nQpp/3p4/1P2p3/4P3/B1PP1b2/B5PP/5K2 b k - 0 17,"
    "e8d7 a2e6 d7d8 f7f8,1760,80,83,72,mate mateIn2,url,\n"
)


def _mate_in_one_fen():
    board = chess.Board()
    for san in ("f3", "e5", "g4"):
        board.push_san(san)
    return board.fen()


class PuzzleSessionTests(unittest.TestCase):
    def test_solves_checkmate(self):
        session = PuzzleSession(
            _mate_in_one_fen(), ["d8h4"], opponent_first=False
        )
        self.assertEqual(session.human_color, chess.BLACK)
        self.assertEqual(session.play(chess.Move.from_uci("d8h4")), "solved")
        self.assertTrue(session.solved)

    def test_wrong_move_is_rejected(self):
        session = PuzzleSession(
            _mate_in_one_fen(), ["d8h4"], opponent_first=False
        )
        wrong = chess.Move.from_uci("f8c5")
        self.assertIn(wrong, session.board.legal_moves)
        self.assertEqual(session.play(wrong), "wrong")
        self.assertFalse(session.solved)

    def test_opponent_first_applies_setup(self):
        session = PuzzleSession(
            chess.STARTING_FEN, ["e2e4", "e7e5"], opponent_first=True
        )
        self.assertEqual(session.human_color, chess.BLACK)
        self.assertEqual(len(session.applied_moves), 1)
        self.assertEqual(session.expected_move, "e7e5")
        self.assertEqual(
            session.play(chess.Move.from_uci("e7e5")), "solved"
        )

    def test_opponent_reply_alternates(self):
        session = PuzzleSession(
            chess.STARTING_FEN,
            ["e2e4", "e7e5", "g1f3"],
            opponent_first=True,
        )
        self.assertEqual(
            session.play(chess.Move.from_uci("e7e5")), "correct"
        )
        self.assertFalse(session.solved)
        self.assertIsNotNone(session.opponent_reply())
        self.assertTrue(session.solved)


class PuzzleParserTests(unittest.TestCase):
    def test_iter_lichess_csv(self):
        rows = list(puzzles.iter_lichess_csv(io.StringIO(CSV_HEADER + CSV_ROW)))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["id"], "00sHx")
        self.assertEqual(
            row["moves"], ["e8d7", "a2e6", "d7d8", "f7f8"]
        )
        self.assertTrue(row["opponent_first"])
        self.assertEqual(row["rating"], 1760)
        self.assertEqual(row["themes"], ["mate", "mateIn2"])

    def test_iter_pgn_puzzles(self):
        text = (
            '[Event "P1"]\n'
            '[FEN "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR'
            ' w KQkq - 0 2"]\n'
            '[Rating "1200"]\n'
            '[SetUp "1"]\n\n'
            "1. Nf3\n"
        )
        rows = list(puzzles.iter_pgn_puzzles(text))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["moves"], ["g1f3"])
        self.assertFalse(rows[0]["opponent_first"])
        self.assertEqual(rows[0]["rating"], 1200)


class PuzzleStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def _write_csv(self):
        path = os.path.join(self.base, "sample.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(CSV_HEADER + CSV_ROW)
        return path

    def test_import_list_get_delete(self):
        path = self._write_csv()
        meta = puzzles.import_collection(path, base_dir=self.base)
        self.assertEqual(meta["count"], 1)
        self.assertEqual(meta["format"], "csv")

        collections = puzzles.list_collections(self.base)
        self.assertEqual(len(collections), 1)
        collection = puzzles.PuzzleCollection(collections[0])
        self.assertEqual(collection.count, 1)
        puzzle = collection.get(0)
        self.assertEqual(puzzle["moves"][0], "e8d7")

        self.assertTrue(
            puzzles.delete_collection(meta["id"], base_dir=self.base)
        )
        self.assertEqual(puzzles.list_collections(self.base), [])

    def test_unsupported_format_leaves_no_collection(self):
        path = os.path.join(self.base, "data.bin")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("nothing")
        with self.assertRaises(puzzles.PuzzleImportError):
            puzzles.import_collection(path, base_dir=self.base)
        self.assertEqual(puzzles.list_collections(self.base), [])

    def test_empty_file_is_rejected(self):
        path = os.path.join(self.base, "empty.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(CSV_HEADER)
        with self.assertRaises(puzzles.PuzzleImportError) as ctx:
            puzzles.import_collection(path, base_dir=self.base)
        self.assertEqual(ctx.exception.code, "empty")


class BuiltinPuzzleTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patch = mock.patch.object(puzzles, "PUZZLE_DIR", self._tmp.name)
        patch.start()
        self.addCleanup(patch.stop)

    def test_builtin_can_be_hidden(self):
        if puzzles.builtin_collection() is None:
            self.skipTest("bundled puzzle sample is not present")
        ids = [meta["id"] for meta in puzzles.list_collections()]
        self.assertIn(puzzles.BUILTIN_ID, ids)

        self.assertTrue(puzzles.delete_collection(puzzles.BUILTIN_ID))
        self.assertTrue(puzzles.is_builtin_hidden())
        ids = [meta["id"] for meta in puzzles.list_collections()]
        self.assertNotIn(puzzles.BUILTIN_ID, ids)


class PuzzleProgressTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def _write_csv(self):
        path = os.path.join(self.base, "sample.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(CSV_HEADER + CSV_ROW)
        return path

    def test_solved_indices_start_empty(self):
        self.assertEqual(
            puzzles.solved_indices("missing", base_dir=self.base), set()
        )

    def test_mark_solved_is_deduplicated(self):
        puzzles.mark_solved("c1", 3, base_dir=self.base)
        puzzles.mark_solved("c1", 1, base_dir=self.base)
        puzzles.mark_solved("c1", 3, base_dir=self.base)
        self.assertEqual(
            puzzles.solved_indices("c1", base_dir=self.base), {1, 3}
        )

    def test_progress_is_per_collection(self):
        puzzles.mark_solved("c1", 0, base_dir=self.base)
        self.assertEqual(
            puzzles.solved_indices("c2", base_dir=self.base), set()
        )

    def test_clear_progress(self):
        puzzles.mark_solved("c1", 0, base_dir=self.base)
        self.assertTrue(puzzles.clear_progress("c1", base_dir=self.base))
        self.assertEqual(
            puzzles.solved_indices("c1", base_dir=self.base), set()
        )
        self.assertFalse(puzzles.clear_progress("c1", base_dir=self.base))

    def test_delete_collection_clears_progress(self):
        meta = puzzles.import_collection(
            self._write_csv(), base_dir=self.base
        )
        puzzles.mark_solved(meta["id"], 0, base_dir=self.base)
        puzzles.delete_collection(meta["id"], base_dir=self.base)
        self.assertEqual(
            puzzles.solved_indices(meta["id"], base_dir=self.base), set()
        )


class PuzzleFavoritesTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def _puzzle(self, puzzle_id="p1"):
        return {
            "id": puzzle_id,
            "fen": chess.STARTING_FEN,
            "moves": ["e2e4"],
            "rating": 1200,
            "themes": ["mate"],
            "opponent_first": False,
        }

    def test_add_and_key_by_puzzle_id(self):
        puzzle = self._puzzle()
        self.assertFalse(puzzles.is_favorite(puzzle, self.base))
        self.assertTrue(puzzles.add_favorite(puzzle, base_dir=self.base))
        self.assertTrue(puzzles.is_favorite(puzzle, self.base))
        self.assertIn("p1", puzzles.favorite_keys(self.base))
        self.assertFalse(puzzles.add_favorite(puzzle, base_dir=self.base))

    def test_remove_and_toggle(self):
        puzzle = self._puzzle()
        puzzles.add_favorite(puzzle, base_dir=self.base)
        self.assertFalse(puzzles.toggle_favorite(puzzle, base_dir=self.base))
        self.assertFalse(puzzles.is_favorite(puzzle, self.base))
        self.assertTrue(puzzles.toggle_favorite(puzzle, base_dir=self.base))
        self.assertTrue(puzzles.is_favorite(puzzle, self.base))

    def test_fallback_key_uses_fen_and_moves(self):
        puzzle = self._puzzle(puzzle_id="")
        self.assertTrue(puzzles.add_favorite(puzzle, base_dir=self.base))
        self.assertTrue(puzzles.is_favorite(dict(puzzle), self.base))

    def test_store_persists_source_id_and_content(self):
        puzzle = self._puzzle()
        puzzles.add_favorite(puzzle, source_id="src", base_dir=self.base)
        stored = puzzles.load_favorites(self.base)
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0]["source_id"], "src")
        self.assertEqual(stored[0]["moves"], ["e2e4"])

    def test_delete_collection_refuses_favorites(self):
        self.assertFalse(
            puzzles.delete_collection(puzzles.FAVORITES_ID, base_dir=self.base)
        )

    def test_virtual_collection_tracks_count(self):
        collection = puzzles.PuzzleCollection(
            puzzles.favorites_collection(self.base)
        )
        self.assertTrue(collection.favorite)
        self.assertEqual(collection.count, 0)
        puzzles.add_favorite(self._puzzle("a"), base_dir=self.base)
        puzzles.add_favorite(self._puzzle("b"), base_dir=self.base)
        refreshed = puzzles.PuzzleCollection(
            puzzles.favorites_collection(self.base)
        )
        self.assertEqual(refreshed.count, 2)
        self.assertEqual(refreshed.get(0)["id"], "a")


class FavoritesListedTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patch = mock.patch.object(puzzles, "PUZZLE_DIR", self._tmp.name)
        patch.start()
        self.addCleanup(patch.stop)

    def test_favorites_is_always_listed_and_not_deletable(self):
        ids = [meta["id"] for meta in puzzles.list_collections()]
        self.assertIn(puzzles.FAVORITES_ID, ids)
        self.assertFalse(puzzles.delete_collection(puzzles.FAVORITES_ID))


if __name__ == "__main__":
    unittest.main()
