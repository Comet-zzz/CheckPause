import json
import os
import tempfile
import unittest

from checkpause.data import learn


class LearnProgressTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.base = self._tmp.name

    def test_missing_file_is_empty(self):
        self.assertEqual(learn.load_progress(self.base), {})

    def test_save_and_reload(self):
        entry = learn.save_lesson_progress("piece_rook", 1, 2, base_dir=self.base)
        self.assertEqual(entry, {"step": 1, "completed": False})
        self.assertEqual(
            learn.load_progress(self.base),
            {"piece_rook": {"step": 1, "completed": False}},
        )

    def test_step_is_clamped(self):
        lesson = learn.save_lesson_progress("x", 99, 5, base_dir=self.base)
        self.assertEqual(lesson["step"], 5)
        lesson = learn.save_lesson_progress("y", -3, 5, base_dir=self.base)
        self.assertEqual(lesson["step"], 0)

    def test_completed_flag_is_kept(self):
        learn.save_lesson_progress("x", 2, 2, completed=True, base_dir=self.base)
        self.assertEqual(
            learn.load_progress(self.base)["x"],
            {"step": 2, "completed": True},
        )

    def test_reset_clears_all_lessons(self):
        learn.save_lesson_progress("x", 1, 2, base_dir=self.base)
        learn.save_lesson_progress("y", 2, 2, completed=True, base_dir=self.base)
        self.assertEqual(learn.reset_progress(self.base), {})
        self.assertEqual(learn.load_progress(self.base), {})

    def test_malformed_file_is_ignored(self):
        path = os.path.join(self.base, learn.PROGRESS_NAME)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        self.assertEqual(learn.load_progress(self.base), {})

    def test_entries_are_normalised(self):
        path = os.path.join(self.base, learn.PROGRESS_NAME)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "lessons": {
                        "x": {"step": "2", "completed": 1},
                        "bad": "nope",
                        "y": {"step": "oops"},
                    }
                },
                handle,
            )
        self.assertEqual(
            learn.load_progress(self.base),
            {"x": {"step": 2, "completed": True}},
        )


if __name__ == "__main__":
    unittest.main()
