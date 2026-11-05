import unittest

import chess

from checkpause.core.lesson import (
    INFO,
    MOVE,
    Lesson,
    LessonSession,
    LessonStep,
    goal_accepts,
)
from checkpause.data.lessons import LESSONS, SECTION_ORDER, SECTIONS, find_lesson
from checkpause.i18n import MESSAGES, t

ROOK_INFO = "4k3/8/8/8/8/8/8/R3K3 w - - 0 1"


def _lesson(steps):
    return Lesson(
        id="test",
        section="pieces",
        title_key="learn_rook_title",
        subtitle_key="learn_rook_subtitle",
        icon="learn_rook",
        steps=tuple(steps),
    )


class LessonSessionTests(unittest.TestCase):
    def test_info_then_move_to_target(self):
        session = LessonSession(
            _lesson(
                (
                    LessonStep(kind=INFO, fen=ROOK_INFO, text_key="learn_rook_intro"),
                    LessonStep(
                        kind=MOVE,
                        fen=ROOK_INFO,
                        text_key="learn_task_rook_move",
                        goal="move_to",
                        target="a8",
                        hint="a1a8",
                    ),
                )
            )
        )
        self.assertTrue(session.is_info)
        self.assertEqual(session.play(chess.Move.from_uci("a1a8")), "invalid")
        self.assertTrue(session.advance())
        self.assertEqual(session.index, 1)
        self.assertFalse(session.is_info)
        self.assertEqual(session.play(chess.Move.from_uci("a1a2")), "wrong")
        self.assertEqual(session.play(chess.Move.from_uci("a1a8")), "solved")
        self.assertTrue(session.solved)
        self.assertEqual(
            session.display_moves,
            (chess.Move.from_uci("a1a8"),),
        )
        self.assertTrue(session.advance())
        self.assertTrue(session.completed)
        self.assertEqual(session.completed_steps, 2)

    def test_start_step_is_clamped(self):
        lesson = _lesson(
            (
                LessonStep(kind=INFO, fen=ROOK_INFO, text_key="learn_rook_intro"),
                LessonStep(
                    kind=MOVE,
                    fen=ROOK_INFO,
                    text_key="learn_task_rook_move",
                    goal="move_to",
                    target="a8",
                    hint="a1a8",
                ),
            )
        )
        self.assertEqual(LessonSession(lesson, 99).index, 1)
        self.assertEqual(LessonSession(lesson, -5).index, 0)

    def test_smothered_reply_is_applied(self):
        lesson = find_lesson("mates_smothered")
        self.assertIsNotNone(lesson)
        session = LessonSession(lesson, 1)
        self.assertEqual(session.play(chess.Move.from_uci("d5g8")), "correct")
        self.assertEqual(
            session.display_moves,
            (chess.Move.from_uci("d5g8"), chess.Move.from_uci("f8g8")),
        )
        self.assertEqual(session.board.piece_at(chess.G8), chess.Piece(chess.ROOK, chess.BLACK))

    def test_goal_checks(self):
        checks = (
            ("basics_check", 1, "d1h5"),
            ("basics_escape", 1, "e1e2"),
            ("basics_mate1", 1, "e1e8"),
            ("advanced_castle", 1, "e1g1"),
            ("advanced_enpassant", 1, "e5d6"),
            ("advanced_stalemate", 1, "d7c7"),
            ("mates_tworooks", 1, "a1a8"),
        )
        for lesson_id, step_index, uci in checks:
            lesson = find_lesson(lesson_id)
            step = lesson.steps[step_index]
            board = chess.Board(step.fen)
            move = chess.Move.from_uci(uci)
            self.assertIn(move, board.legal_moves)
            self.assertTrue(goal_accepts(step, board, move), lesson_id)


class LessonContentTests(unittest.TestCase):
    def test_ids_are_unique_and_sections_are_ordered(self):
        ids = [lesson.id for lesson in LESSONS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(
            [section["id"] for section in SECTIONS],
            list(SECTION_ORDER),
        )
        self.assertEqual(
            {lesson.section for lesson in LESSONS},
            set(SECTION_ORDER),
        )

    def test_every_step_is_playable(self):
        for lesson in LESSONS:
            self.assertTrue(lesson.steps, lesson.id)
            for index, step in enumerate(lesson.steps):
                board = chess.Board(step.fen)
                self.assertTrue(board.is_valid(), f"{lesson.id}[{index}]")
                if step.kind == INFO:
                    self.assertIsNone(step.goal)
                    continue
                self.assertEqual(step.kind, MOVE, f"{lesson.id}[{index}]")
                self.assertIn(
                    step.goal,
                    (
                        "move_to",
                        "capture",
                        "check",
                        "mate",
                        "escape_check",
                        "castle",
                        "en_passant",
                        "stalemate",
                        "exact",
                    ),
                )
                legal = list(board.legal_moves)
                accepted = [move for move in legal if goal_accepts(step, board, move)]
                self.assertTrue(accepted, f"{lesson.id}[{index}] goal")
                if step.hint:
                    hint = chess.Move.from_uci(step.hint)
                    self.assertIn(hint, legal, f"{lesson.id}[{index}] hint")
                    self.assertTrue(
                        goal_accepts(step, board, hint),
                        f"{lesson.id}[{index}] hint goal",
                    )
                if step.goal == "exact":
                    for uci in step.accept:
                        self.assertIn(
                            chess.Move.from_uci(uci),
                            legal,
                            f"{lesson.id}[{index}] accept",
                        )
                if step.reply:
                    reference = (
                        chess.Move.from_uci(step.accept[0])
                        if step.accept
                        else chess.Move.from_uci(step.hint)
                    )
                    after = board.copy()
                    after.push(reference)
                    self.assertIn(
                        chess.Move.from_uci(step.reply),
                        after.legal_moves,
                        f"{lesson.id}[{index}] reply",
                    )

    def test_all_text_keys_exist_in_both_locales(self):
        for lesson in LESSONS:
            keys = [lesson.title_key, lesson.subtitle_key]
            for step in lesson.steps:
                keys.append(step.text_key)
                keys.append(step.success_key)
            for key in keys:
                self.assertIn(key, MESSAGES["zh-CN"], key)
                self.assertIn(key, MESSAGES["en-US"], key)
            for step in lesson.steps:
                t(step.text_key, "zh-CN", **step.text_params)
                t(step.text_key, "en-US", **step.text_params)


if __name__ == "__main__":
    unittest.main()
