"""Interactive lesson model for the learning module.

The model is deliberately Qt-free: the GUI renders a session and feeds moves
back. Each step owns a FEN so a lesson can jump between independent positions
without replaying a game.
"""

from dataclasses import dataclass, field

import chess

INFO = "info"
MOVE = "move"

KINDS = (INFO, MOVE)

GOALS = (
    "move_to",
    "capture",
    "check",
    "mate",
    "escape_check",
    "castle",
    "en_passant",
    "stalemate",
    "exact",
)


@dataclass(frozen=True)
class LessonStep:
    kind: str
    fen: str
    text_key: str
    text_params: dict = field(default_factory=dict)
    goal: str | None = None
    target: str | None = None
    accept: tuple[str, ...] = ()
    reply: str | None = None
    hint: str | None = None
    marks: tuple[str, ...] = ()
    arrows: tuple[str, ...] = ()
    success_key: str = "learn_success"


@dataclass(frozen=True)
class Lesson:
    id: str
    section: str
    title_key: str
    subtitle_key: str
    icon: str
    steps: tuple[LessonStep, ...]


def _probe(board, move):
    probe = board.copy()
    probe.push(move)
    return probe


def goal_accepts(step, board, move):
    """Whether ``move`` satisfies the step's teaching goal."""
    if step.goal not in GOALS:
        return False
    if step.goal == "exact":
        return move.uci() in step.accept
    if step.goal == "move_to":
        return chess.square_name(move.to_square) == step.target
    if step.goal == "capture":
        if not board.is_capture(move):
            return False
        return step.target is None or chess.square_name(move.to_square) == step.target
    if step.goal == "check":
        return board.gives_check(move)
    if step.goal == "escape_check":
        if not board.is_check():
            return False
        return not _probe(board, move).is_check()
    if step.goal == "castle":
        return board.is_castling(move)
    if step.goal == "en_passant":
        return board.is_en_passant(move)
    if step.goal == "mate":
        return _probe(board, move).is_checkmate()
    if step.goal == "stalemate":
        return _probe(board, move).is_stalemate()
    return False


class LessonSession:
    """Step cursor and move validation for one lesson."""

    def __init__(self, lesson, start_step=0):
        if not lesson.steps:
            raise ValueError("lesson has no steps")
        self.lesson = lesson
        self.index = max(0, min(int(start_step), len(lesson.steps) - 1))
        self.completed = False
        self._load()

    def _load(self):
        self.solved = False
        self._last_status = None
        self._display_moves = []
        self._board = chess.Board(self.current.fen)

    @property
    def current(self):
        return self.lesson.steps[self.index]

    @property
    def total_steps(self):
        return len(self.lesson.steps)

    @property
    def is_info(self):
        return self.current.kind == INFO

    @property
    def board(self):
        return self._board

    @property
    def display_moves(self):
        return tuple(self._display_moves)

    @property
    def last_status(self):
        return self._last_status

    @property
    def completed_steps(self):
        if self.completed:
            return self.total_steps
        return self.index + (1 if self.solved else 0)

    def play(self, move):
        step = self.current
        if step.kind != MOVE:
            return "invalid"
        if self.solved:
            return "invalid"
        board = chess.Board(step.fen)
        if move not in board.legal_moves:
            self._last_status = "illegal"
            return "illegal"
        if not goal_accepts(step, board, move):
            self._last_status = "wrong"
            return "wrong"

        board.push(move)
        moves = [move]
        if step.reply:
            reply = chess.Move.from_uci(step.reply)
            if reply not in board.legal_moves:
                raise ValueError(f"lesson reply is illegal: {step.reply}")
            board.push(reply)
            moves.append(reply)

        self._board = board
        self._display_moves = moves
        self.solved = True
        if self.index + 1 >= self.total_steps:
            self._last_status = "solved"
            return "solved"
        self._last_status = "correct"
        return "correct"

    def advance(self):
        step = self.current
        if step.kind == MOVE and not self.solved:
            return False
        if self.index + 1 >= self.total_steps:
            self.completed = True
            self._last_status = "complete"
            return True
        self.index += 1
        self._load()
        return True

    def retry(self):
        self._load()
