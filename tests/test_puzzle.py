import io
import json
import os
import tempfile
import unittest
from unittest import mock

import chess

from checkpause.core.puzzle import PuzzleSession, validate_puzzle
from checkpause.data import puzzles

CSV_HEADER = (
    "PuzzleId,FEN,Moves,Rating,RatingDeviation,Popularity,NbPlays," "Themes,GameUrl,OpeningTags\n"
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
        session = PuzzleSession(_mate_in_one_fen(), ["d8h4"], opponent_first=False)
        self.assertEqual(session.human_color, chess.BLACK)
        self.assertEqual(session.play(chess.Move.from_uci("d8h4")), "solved")
        self.assertTrue(session.solved)

    def test_wrong_move_is_rejected(self):
        session = PuzzleSession(_mate_in_one_fen(), ["d8h4"], opponent_first=False)
        wrong = chess.Move.from_uci("f8c5")
        self.assertIn(wrong, session.board.legal_moves)
        self.assertEqual(session.play(wrong), "wrong")
        self.assertFalse(session.solved)

    def test_opponent_first_applies_setup(self):
        session = PuzzleSession(chess.STARTING_FEN, ["e2e4", "e7e5"], opponent_first=True)
        self.assertEqual(session.human_color, chess.BLACK)
        self.assertEqual(len(session.applied_moves), 1)
        self.assertEqual(session.expected_move, "e7e5")
        self.assertEqual(session.play(chess.Move.from_uci("e7e5")), "solved")

    def test_opponent_reply_alternates(self):
        session = PuzzleSession(
            chess.STARTING_FEN,
            ["e2e4", "e7e5", "g1f3"],
            opponent_first=True,
        )
        self.assertEqual(session.play(chess.Move.from_uci("e7e5")), "correct")
        self.assertFalse(session.solved)
        self.assertIsNotNone(session.opponent_reply())
        self.assertTrue(session.solved)

    def test_illegal_expected_move_is_rejected_instead_of_raising(self):
        session = PuzzleSession(chess.STARTING_FEN, ["e2e5"], opponent_first=False)
        self.assertEqual(session.play(chess.Move.from_uci("e2e5")), "wrong")

    def test_illegal_setup_move_is_rejected(self):
        with self.assertRaises(ValueError):
            PuzzleSession(chess.STARTING_FEN, ["e2e5"], opponent_first=True)

    def test_validate_rejects_a_broken_line(self):
        self.assertTrue(validate_puzzle(_mate_in_one_fen(), ["d8h4"]))
        self.assertFalse(validate_puzzle(chess.STARTING_FEN, ["e2e5"]))
        self.assertFalse(validate_puzzle(chess.STARTING_FEN, []))


class PuzzleParserTests(unittest.TestCase):
    def test_iter_lichess_csv(self):
        rows = list(puzzles.iter_lichess_csv(io.StringIO(CSV_HEADER + CSV_ROW)))
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["id"], "00sHx")
        self.assertEqual(row["moves"], ["e8d7", "a2e6", "d7d8", "f7f8"])
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

        self.assertTrue(puzzles.delete_collection(meta["id"], base_dir=self.base))
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
        self.assertEqual(puzzles.solved_indices("missing", base_dir=self.base), set())

    def test_mark_solved_is_deduplicated(self):
        puzzles.mark_solved("c1", 3, base_dir=self.base)
        puzzles.mark_solved("c1", 1, base_dir=self.base)
        puzzles.mark_solved("c1", 3, base_dir=self.base)
        self.assertEqual(puzzles.solved_indices("c1", base_dir=self.base), {1, 3})

    def test_progress_is_per_collection(self):
        puzzles.mark_solved("c1", 0, base_dir=self.base)
        self.assertEqual(puzzles.solved_indices("c2", base_dir=self.base), set())

    def test_clear_progress(self):
        puzzles.mark_solved("c1", 0, base_dir=self.base)
        self.assertTrue(puzzles.clear_progress("c1", base_dir=self.base))
        self.assertEqual(puzzles.solved_indices("c1", base_dir=self.base), set())
        self.assertFalse(puzzles.clear_progress("c1", base_dir=self.base))

    def test_delete_collection_clears_progress(self):
        meta = puzzles.import_collection(self._write_csv(), base_dir=self.base)
        puzzles.mark_solved(meta["id"], 0, base_dir=self.base)
        puzzles.delete_collection(meta["id"], base_dir=self.base)
        self.assertEqual(puzzles.solved_indices(meta["id"], base_dir=self.base), set())

    def _collection(self, filename, ids, collection_id="c1"):
        path = os.path.join(self.base, filename)
        with open(path, "w", encoding="utf-8") as handle:
            for puzzle_id in ids:
                handle.write(
                    json.dumps(
                        {
                            "id": puzzle_id,
                            "fen": chess.STARTING_FEN,
                            "moves": ["e2e4"],
                        }
                    )
                    + "\n"
                )
        return puzzles.PuzzleCollection({"id": collection_id, "file": path, "count": len(ids)})

    def test_legacy_indices_are_migrated_to_puzzle_keys(self):
        collection = self._collection("a.jsonl", ["p1", "p2", "p3"])
        puzzles.save_progress({"c1": [0, 2]}, base_dir=self.base)

        self.assertEqual(puzzles.solved_keys(collection, base_dir=self.base), {"p1", "p3"})
        self.assertEqual(puzzles.load_progress(self.base)["c1"], ["p1", "p3"])

    def test_progress_survives_reordering_after_migration(self):
        puzzles.save_progress({"c1": [0, 2]}, base_dir=self.base)
        puzzles.solved_keys(self._collection("a.jsonl", ["p1", "p2", "p3"]), base_dir=self.base)

        reordered = self._collection("b.jsonl", ["p3", "p2", "p1"])
        self.assertEqual(puzzles.solved_keys(reordered, base_dir=self.base), {"p1", "p3"})

    def test_mark_solved_key_is_deduplicated(self):
        collection = self._collection("a.jsonl", ["p1", "p2"])
        puzzles.mark_solved_key("c1", "p2", base_dir=self.base)
        puzzles.mark_solved_key("c1", "p2", base_dir=self.base)
        self.assertEqual(puzzles.solved_keys(collection, base_dir=self.base), {"p2"})

    def test_corrupt_progress_is_backed_up_before_being_replaced(self):
        path = puzzles._progress_path(self.base)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{broken")

        puzzles.mark_solved_key("c1", "p1", base_dir=self.base)

        self.assertEqual(puzzles.load_progress(self.base)["c1"], ["p1"])
        backups = [name for name in os.listdir(self.base) if ".corrupt-" in name]
        self.assertTrue(backups)

    def test_corrupt_index_is_backed_up_before_being_replaced(self):
        path = puzzles._index_path(self.base)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{broken")

        self.assertEqual(puzzles.load_index(self.base), [])
        puzzles.save_index([{"id": "c1"}], base_dir=self.base)

        self.assertEqual(puzzles.load_index(self.base), [{"id": "c1"}])
        backups = [name for name in os.listdir(self.base) if ".corrupt-" in name]
        self.assertTrue(backups)

    def test_collection_iterates_with_one_file_open(self):
        collection = self._collection("a.jsonl", ["p1", "p2", "p3"])
        self.assertEqual(
            [index for index, _puzzle in collection.iter_from(1)],
            [1, 2],
        )
        _index, puzzle = next(collection.iter_from(1))
        self.assertEqual(puzzle["id"], "p2")


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
        self.assertFalse(puzzles.delete_collection(puzzles.FAVORITES_ID, base_dir=self.base))

    def test_virtual_collection_tracks_count(self):
        collection = puzzles.PuzzleCollection(puzzles.favorites_collection(self.base))
        self.assertTrue(collection.favorite)
        self.assertEqual(collection.count, 0)
        puzzles.add_favorite(self._puzzle("a"), base_dir=self.base)
        puzzles.add_favorite(self._puzzle("b"), base_dir=self.base)
        refreshed = puzzles.PuzzleCollection(puzzles.favorites_collection(self.base))
        self.assertEqual(refreshed.count, 2)
        self.assertEqual(refreshed.get(0)["id"], "a")

    def test_unreadable_favorites_are_backed_up(self):
        path = puzzles.favorites_path(self.base)
        with open(path, "wb") as handle:
            handle.write(b"\xff\xfe\x00")

        self.assertEqual(puzzles.load_favorites(self.base), [])
        backups = [name for name in os.listdir(self.base) if ".corrupt-" in name]
        self.assertTrue(backups)

        puzzles.add_favorite(self._puzzle("a"), base_dir=self.base)
        self.assertTrue(puzzles.is_favorite(self._puzzle("a"), self.base))


class PuzzleAttemptTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def _puzzle(self, puzzle_id, rating=1200, themes=None):
        return {
            "id": puzzle_id,
            "fen": chess.STARTING_FEN,
            "moves": ["e2e4"],
            "rating": rating,
            "themes": themes or ["mate"],
            "opponent_first": False,
        }

    def test_record_and_load_attempt(self):
        entry = puzzles.record_attempt(
            self._puzzle("p1"),
            "solved",
            source_id="c1",
            duration_ms=4200,
            hinted=True,
            base_dir=self.base,
        )
        self.assertEqual(entry["result"], "solved")
        loaded = puzzles.load_attempts(self.base)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["key"], "p1")
        self.assertTrue(loaded[0]["hinted"])
        self.assertEqual(loaded[0]["source_id"], "c1")

    def test_summary_uses_unique_puzzles(self):
        puzzle = self._puzzle("p1", rating=1500)
        puzzles.record_attempt(puzzle, "failed", base_dir=self.base)
        puzzles.record_attempt(puzzle, "solved", base_dir=self.base)
        summary = puzzles.attempt_summary(base_dir=self.base)
        self.assertEqual(summary["attempts"], 2)
        self.assertEqual(summary["unique_attempted"], 1)
        self.assertEqual(summary["unique_solved"], 1)
        self.assertEqual(summary["accuracy"], 50)
        self.assertEqual(summary["retryable"], 0)

    def test_summary_tracks_streak_and_themes(self):
        puzzles.record_attempt(self._puzzle("a", themes=["mate"]), "solved", base_dir=self.base)
        puzzles.record_attempt(self._puzzle("b", themes=["fork"]), "solved", base_dir=self.base)
        puzzles.record_attempt(self._puzzle("c", themes=["fork"]), "failed", base_dir=self.base)
        summary = puzzles.attempt_summary(base_dir=self.base)
        self.assertEqual(summary["streak"], 0)
        self.assertEqual(summary["best_streak"], 2)
        self.assertEqual(summary["failed_avg_rating"], 1200)
        themes = {row["theme"]: row for row in summary["themes"]}
        self.assertEqual(themes["fork"]["attempts"], 2)
        self.assertEqual(themes["fork"]["accuracy"], 50)
        self.assertEqual(themes["mate"]["accuracy"], 100)

    def test_bad_lines_are_skipped(self):
        path = puzzles.attempts_path(self.base)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("not json\n")
            handle.write('{"key": "p1", "result": "solved"}\n')
        self.assertEqual(len(puzzles.load_attempts(self.base)), 1)

    def test_clear_attempts(self):
        puzzles.record_attempt(self._puzzle("p1"), "solved", base_dir=self.base)
        puzzles.clear_attempts(self.base)
        self.assertEqual(puzzles.attempt_summary(base_dir=self.base)["attempts"], 0)

    def test_attempts_record_whether_they_were_rated(self):
        entry = puzzles.record_attempt(
            self._puzzle("p1"),
            "solved",
            rated=True,
            base_dir=self.base,
        )
        self.assertTrue(entry["rated"])
        summary = puzzles.attempt_summary(base_dir=self.base)
        self.assertTrue(summary["recent"][0]["rated"])

    def test_mistakes_follow_the_latest_result(self):
        puzzles.record_attempt(self._puzzle("p1"), "failed", base_dir=self.base)
        puzzles.record_attempt(self._puzzle("p2"), "solved", base_dir=self.base)
        puzzles.record_attempt(self._puzzle("p2"), "failed", base_dir=self.base)

        mistakes = puzzles.mistake_puzzles(self.base)
        self.assertEqual([item["id"] for item in mistakes], ["p2", "p1"])

        puzzles.record_attempt(self._puzzle("p1"), "solved", base_dir=self.base)
        mistakes = puzzles.mistake_puzzles(self.base)
        self.assertEqual([item["id"] for item in mistakes], ["p2"])

    def test_puzzle_list_collection_reads_in_memory(self):
        collection = puzzles.PuzzleListCollection(
            {"id": "mistakes", "count": 2},
            [self._puzzle("p1"), self._puzzle("p2")],
        )
        self.assertEqual(collection.count, 2)
        self.assertEqual(collection.get(1)["id"], "p2")
        self.assertEqual([index for index, _ in collection.iter_from(1)], [1])


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


class OnlineOutboxTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def _entry(self, attempt_id="a1", **overrides):
        entry = {
            "puzzle_id": "p1",
            "result": "solved",
            "duration_ms": 1200,
            "hinted": False,
            "rated": True,
            "client_attempt_id": attempt_id,
            "account": "Player_One",
            "server_url": "https://example.test",
        }
        entry.update(overrides)
        return entry

    def test_append_and_load_keeps_the_account(self):
        self.assertTrue(puzzles.append_outbox(self._entry(), base_dir=self.base))
        loaded = puzzles.load_outbox(self.base)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["client_attempt_id"], "a1")
        self.assertEqual(loaded[0]["account"], "player_one")
        self.assertEqual(loaded[0]["result"], "solved")
        self.assertTrue(loaded[0]["created_at"])

    def test_append_is_idempotent_by_attempt_id(self):
        puzzles.append_outbox(self._entry(), base_dir=self.base)
        self.assertFalse(puzzles.append_outbox(self._entry(), base_dir=self.base))
        self.assertEqual(len(puzzles.load_outbox(self.base)), 1)

    def test_remove_only_the_named_attempt(self):
        puzzles.append_outbox(self._entry("a1"), base_dir=self.base)
        puzzles.append_outbox(self._entry("a2"), base_dir=self.base)
        self.assertTrue(puzzles.remove_outbox("a1", base_dir=self.base))
        self.assertFalse(puzzles.remove_outbox("missing", base_dir=self.base))
        loaded = puzzles.load_outbox(self.base)
        self.assertEqual([item["client_attempt_id"] for item in loaded], ["a2"])

    def test_unusable_entries_are_skipped(self):
        path = puzzles.outbox_path(self.base)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("not json\n")
            handle.write('{"puzzle_id": "p1", "result": "bogus"}\n')
            handle.write('{"puzzle_id": "p2", "result": "failed"}\n')
        self.assertEqual(puzzles.load_outbox(self.base), [])

    def test_clear_outbox(self):
        puzzles.append_outbox(self._entry(), base_dir=self.base)
        puzzles.clear_outbox(self.base)
        self.assertEqual(puzzles.load_outbox(self.base), [])

    def test_attach_account_id_stamps_legacy_entries(self):
        puzzles.append_outbox(self._entry("a1", account="player_one"), base_dir=self.base)
        self.assertEqual(puzzles.attach_outbox_account_id(42, "player_one", base_dir=self.base), 1)
        loaded = puzzles.load_outbox(self.base)
        self.assertEqual(loaded[0]["account_id"], "42")
        self.assertEqual(puzzles.attach_outbox_account_id(42, "player_one", base_dir=self.base), 0)

    def test_attach_without_a_username_does_not_guess(self):
        puzzles.append_outbox(self._entry("a1", account="player_one"), base_dir=self.base)
        self.assertEqual(puzzles.attach_outbox_account_id(42, "", base_dir=self.base), 0)
        self.assertEqual(puzzles.load_outbox(self.base)[0]["account_id"], "")


if __name__ == "__main__":
    unittest.main()
