"""Bundled beginner lessons.

The teaching order follows the classic learn sequence: pieces, fundamentals,
intermediate rules, then checkmate patterns. Every step owns its FEN so the
lesson model can jump between positions; text lives in the i18n catalog and is
referenced by key.
"""

import chess

from checkpause.core.lesson import INFO, MOVE, Lesson, LessonStep

SECTION_ORDER = ("pieces", "basics", "advanced", "mates")

SECTIONS = (
    {"id": "pieces", "title_key": "learn_section_pieces"},
    {"id": "basics", "title_key": "learn_section_basics"},
    {"id": "advanced", "title_key": "learn_section_advanced"},
    {"id": "mates", "title_key": "learn_section_mates"},
)


def _info(fen, text_key, arrows=(), marks=()):
    return LessonStep(
        kind=INFO,
        fen=fen,
        text_key=text_key,
        arrows=tuple(arrows),
        marks=tuple(marks),
    )


def _move(
    fen,
    text_key,
    goal,
    target=None,
    accept=(),
    reply=None,
    hint=None,
    marks=(),
    text_params=None,
    success_key="learn_success",
):
    return LessonStep(
        kind=MOVE,
        fen=fen,
        text_key=text_key,
        text_params=dict(text_params or {}),
        goal=goal,
        target=target,
        accept=tuple(accept),
        reply=reply,
        hint=hint,
        marks=tuple(marks),
        success_key=success_key,
    )


LESSONS = (
    Lesson(
        id="piece_rook",
        section="pieces",
        title_key="learn_rook_title",
        subtitle_key="learn_rook_subtitle",
        icon="learn_rook",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/R3K3 w - - 0 1",
                "learn_rook_intro",
                arrows=("a1a8",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/R3K3 w - - 0 1",
                "learn_task_rook_move",
                "move_to",
                target="a8",
                hint="a1a8",
                marks=("a8",),
            ),
        ),
    ),
    Lesson(
        id="piece_bishop",
        section="pieces",
        title_key="learn_bishop_title",
        subtitle_key="learn_bishop_subtitle",
        icon="learn_bishop",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
                "learn_bishop_intro",
                arrows=("c1h6",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/2B1K3 w - - 0 1",
                "learn_task_bishop_move",
                "move_to",
                target="h6",
                hint="c1h6",
                marks=("h6",),
            ),
        ),
    ),
    Lesson(
        id="piece_queen",
        section="pieces",
        title_key="learn_queen_title",
        subtitle_key="learn_queen_subtitle",
        icon="learn_queen",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/3QK3 w - - 0 1",
                "learn_queen_intro",
                arrows=("d1d6",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/3QK3 w - - 0 1",
                "learn_task_queen_move",
                "move_to",
                target="d6",
                hint="d1d6",
                marks=("d6",),
            ),
        ),
    ),
    Lesson(
        id="piece_king",
        section="pieces",
        title_key="learn_king_title",
        subtitle_key="learn_king_subtitle",
        icon="learn_king",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
                "learn_king_intro",
                arrows=("e1e2",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
                "learn_task_king_move",
                "move_to",
                target="e2",
                hint="e1e2",
                marks=("e2",),
            ),
        ),
    ),
    Lesson(
        id="piece_knight",
        section="pieces",
        title_key="learn_knight_title",
        subtitle_key="learn_knight_subtitle",
        icon="learn_knight",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/1N2K3 w - - 0 1",
                "learn_knight_intro",
                arrows=("b1c3",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/1N2K3 w - - 0 1",
                "learn_task_knight_move",
                "move_to",
                target="c3",
                hint="b1c3",
                marks=("c3",),
            ),
        ),
    ),
    Lesson(
        id="piece_pawn",
        section="pieces",
        title_key="learn_pawn_title",
        subtitle_key="learn_pawn_subtitle",
        icon="learn_pawn",
        steps=(
            _info(
                "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
                "learn_pawn_intro",
                arrows=("e2e4",),
            ),
            _move(
                "4k3/8/8/8/8/8/4P3/4K3 w - - 0 1",
                "learn_task_pawn_move",
                "move_to",
                target="e4",
                hint="e2e4",
                marks=("e4",),
            ),
            _move(
                "4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1",
                "learn_task_capture",
                "capture",
                target="d5",
                hint="e4d5",
                text_params={"target": "d5"},
            ),
        ),
    ),
    Lesson(
        id="basics_capture",
        section="basics",
        title_key="learn_capture_title",
        subtitle_key="learn_capture_subtitle",
        icon="learn_capture",
        steps=(
            _info(
                "4k3/8/8/n7/8/8/8/R3K3 w - - 0 1",
                "learn_capture_intro",
                arrows=("a1a5",),
            ),
            _move(
                "k7/8/8/4b3/8/8/8/4R1K1 w - - 0 1",
                "learn_task_capture",
                "capture",
                target="e5",
                hint="e1e5",
                text_params={"target": "e5"},
            ),
        ),
    ),
    Lesson(
        id="basics_protect",
        section="basics",
        title_key="learn_protect_title",
        subtitle_key="learn_protect_subtitle",
        icon="learn_shield",
        steps=(
            _info(
                "4r1k1/8/8/8/4R3/8/8/1B2K3 w - - 0 1",
                "learn_protect_intro",
                arrows=("e8e4",),
            ),
            _move(
                "4r1k1/8/8/8/4R3/8/8/1B2K3 w - - 0 1",
                "learn_task_protect",
                "move_to",
                target="d3",
                hint="b1d3",
                marks=("d3",),
                success_key="learn_success_protect",
            ),
        ),
    ),
    Lesson(
        id="basics_combat",
        section="basics",
        title_key="learn_combat_title",
        subtitle_key="learn_combat_subtitle",
        icon="learn_swords",
        steps=(
            _info(
                "4r1k1/8/8/8/4R3/8/8/1B2K3 w - - 0 1",
                "learn_combat_intro",
                arrows=("e8e4",),
            ),
            _info(
                "4r1k1/8/8/8/4R3/8/8/1B2K3 w - - 0 1",
                "learn_combat_intro2",
                arrows=("b1e4",),
            ),
        ),
    ),
    Lesson(
        id="basics_check",
        section="basics",
        title_key="learn_check_title",
        subtitle_key="learn_check_subtitle",
        icon="learn_check",
        steps=(
            _info(
                "4k3/8/8/8/8/8/8/3QK3 w - - 0 1",
                "learn_check_intro",
                arrows=("d1h5",),
            ),
            _move(
                "4k3/8/8/8/8/8/8/3QK3 w - - 0 1",
                "learn_task_check",
                "check",
                hint="d1h5",
                success_key="learn_success_check",
            ),
        ),
    ),
    Lesson(
        id="basics_escape",
        section="basics",
        title_key="learn_escape_title",
        subtitle_key="learn_escape_subtitle",
        icon="learn_shield",
        steps=(
            _info(
                "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",
                "learn_escape_intro",
                arrows=("e1e2",),
            ),
            _move(
                "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",
                "learn_task_escape",
                "escape_check",
                hint="e1e2",
                success_key="learn_success_escape",
            ),
        ),
    ),
    Lesson(
        id="basics_mate1",
        section="basics",
        title_key="learn_mate1_title",
        subtitle_key="learn_mate1_subtitle",
        icon="learn_mate",
        steps=(
            _info(
                "6k1/5ppp/8/8/8/8/8/K3R3 w - - 0 1",
                "learn_mate1_intro",
                arrows=("e1e8",),
            ),
            _move(
                "6k1/5ppp/8/8/8/8/8/K3R3 w - - 0 1",
                "learn_task_mate",
                "mate",
                hint="e1e8",
                success_key="learn_success_mate",
            ),
        ),
    ),
    Lesson(
        id="advanced_setup",
        section="advanced",
        title_key="learn_setup_title",
        subtitle_key="learn_setup_subtitle",
        icon="learn_board",
        steps=(
            _info(chess.STARTING_FEN, "learn_setup_intro"),
            _info(chess.STARTING_FEN, "learn_setup_intro2"),
        ),
    ),
    Lesson(
        id="advanced_castle",
        section="advanced",
        title_key="learn_castle_title",
        subtitle_key="learn_castle_subtitle",
        icon="learn_castle",
        steps=(
            _info(
                "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                "learn_castle_intro",
                arrows=("e1g1",),
            ),
            _move(
                "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
                "learn_task_castle",
                "castle",
                hint="e1g1",
                marks=("g1",),
                success_key="learn_success_castle",
            ),
        ),
    ),
    Lesson(
        id="advanced_enpassant",
        section="advanced",
        title_key="learn_enpassant_title",
        subtitle_key="learn_enpassant_subtitle",
        icon="learn_enpassant",
        steps=(
            _info(
                "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
                "learn_enpassant_intro",
                arrows=("e5d6",),
            ),
            _move(
                "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1",
                "learn_task_en_passant",
                "en_passant",
                hint="e5d6",
                marks=("d6",),
                success_key="learn_success_en_passant",
            ),
        ),
    ),
    Lesson(
        id="advanced_stalemate",
        section="advanced",
        title_key="learn_stalemate_title",
        subtitle_key="learn_stalemate_subtitle",
        icon="learn_stalemate",
        steps=(
            _info("k7/2Q5/2K5/8/8/8/8/8 b - - 0 1", "learn_stalemate_intro"),
            _move(
                "k7/3Q4/2K5/8/8/8/8/8 w - - 0 1",
                "learn_task_stalemate",
                "stalemate",
                hint="d7c7",
                marks=("c7",),
                success_key="learn_success_stalemate",
            ),
        ),
    ),
    Lesson(
        id="mates_backrank",
        section="mates",
        title_key="learn_backrank_title",
        subtitle_key="learn_backrank_subtitle",
        icon="learn_backrank",
        steps=(
            _info(
                "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",
                "learn_backrank_intro",
                arrows=("e1e8",),
            ),
            _move(
                "6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 0 1",
                "learn_task_mate",
                "mate",
                hint="e1e8",
                success_key="learn_success_mate",
            ),
        ),
    ),
    Lesson(
        id="mates_smothered",
        section="mates",
        title_key="learn_smothered_title",
        subtitle_key="learn_smothered_subtitle",
        icon="learn_knight",
        steps=(
            _info(
                "5r1k/6pp/7N/3Q4/8/8/8/6K1 w - - 0 1",
                "learn_smothered_intro",
                arrows=("d5g8",),
            ),
            _move(
                "5r1k/6pp/7N/3Q4/8/8/8/6K1 w - - 0 1",
                "learn_task_smothered_sac",
                "exact",
                accept=("d5g8",),
                reply="f8g8",
                hint="d5g8",
                success_key="learn_success_check",
            ),
            _move(
                "6rk/6pp/7N/8/8/8/8/6K1 w - - 0 1",
                "learn_task_smothered_mate",
                "mate",
                hint="h6f7",
                success_key="learn_success_mate",
            ),
        ),
    ),
    Lesson(
        id="mates_tworooks",
        section="mates",
        title_key="learn_tworooks_title",
        subtitle_key="learn_tworooks_subtitle",
        icon="learn_two_rooks",
        steps=(
            _info(
                "7k/1R6/8/8/8/8/8/R5K1 w - - 0 1",
                "learn_tworooks_intro",
                arrows=("a1a8",),
            ),
            _move(
                "7k/1R6/8/8/8/8/8/R5K1 w - - 0 1",
                "learn_task_mate",
                "mate",
                hint="a1a8",
                success_key="learn_success_mate",
            ),
        ),
    ),
    Lesson(
        id="mates_queen",
        section="mates",
        title_key="learn_queenmate_title",
        subtitle_key="learn_queenmate_subtitle",
        icon="learn_queen",
        steps=(
            _info(
                "7k/8/5KQ1/8/8/8/8/8 w - - 0 1",
                "learn_queenmate_intro",
                arrows=("g6g7",),
            ),
            _move(
                "7k/8/5KQ1/8/8/8/8/8 w - - 0 1",
                "learn_task_mate",
                "mate",
                hint="g6g7",
                success_key="learn_success_mate",
            ),
        ),
    ),
)


def load_lessons():
    """Return the bundled lessons in teaching order."""
    return list(LESSONS)


def find_lesson(lesson_id):
    for lesson in LESSONS:
        if lesson.id == lesson_id:
            return lesson
    return None
