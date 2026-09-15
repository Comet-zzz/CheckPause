"""Pure game and clock state for the Play page.

``PlaySession`` has no Qt dependencies: it owns the chess board, the move
list, the result state, and both players' remaining time. The page drives
it from the GUI (timers, labels, engine workers).
"""

import chess


class PlaySession:
    def __init__(self, human_color=chess.WHITE):
        self.human_color = human_color
        self.board = chess.Board()
        self.moves = []
        self.start_fen = None
        self.opening_ply = 0
        self.game_over = False
        self.result_kind = None
        self.paused = False
        self.time_control = {"base": None, "increment": 0}
        self.clock_remaining = None
        self.clock_last = None

    # -- game setup -----------------------------------------------------
    def new_game(
        self,
        *,
        human_color=None,
        start_fen=None,
        opening_moves=(),
        time_control=None,
        now=None,
    ):
        if human_color is not None:
            self.human_color = human_color
        self.moves = []
        if start_fen:
            self.board = chess.Board(start_fen)
            self.start_fen = start_fen
        else:
            self.board = chess.Board()
            self.start_fen = None
            for move in opening_moves:
                if move not in self.board.legal_moves:
                    break
                self.board.push(move)
                self.moves.append(move)
        self.opening_ply = len(self.moves)
        self.game_over = False
        self.result_kind = None
        self.paused = False
        if time_control is not None:
            self.time_control = dict(time_control)
        self.reset_clock(now)

    def set_time_control(self, time_control):
        self.time_control = dict(time_control or {})

    # -- play -----------------------------------------------------------
    def push(self, move):
        color = self.board.turn
        self.board.push(move)
        self.moves.append(move)
        self._apply_increment(color)

    def can_undo(self):
        return len(self.moves) > self.opening_ply

    def undo(self):
        if not self.can_undo():
            return False
        self.board.pop()
        self.moves.pop()
        if (
            len(self.moves) > self.opening_ply
            and self.board.turn != self.human_color
        ):
            self.board.pop()
            self.moves.pop()
        self.result_kind = None
        return True

    def resign(self):
        self.game_over = True
        self.result_kind = "resign"

    def finish_if_over(self):
        if not self.board.is_game_over():
            return False
        self.game_over = True
        outcome = self.board.outcome()
        if outcome is None or outcome.winner is None:
            self.result_kind = "draw"
        elif outcome.winner == self.human_color:
            self.result_kind = "win"
        else:
            self.result_kind = "lose"
        return True

    def timeout(self, color):
        self.game_over = True
        self.result_kind = (
            "timeout_lose" if color == self.human_color else "timeout_win"
        )

    def toggle_pause(self):
        if self.game_over:
            return self.paused
        self.paused = not self.paused
        return self.paused

    # -- clock ----------------------------------------------------------
    @property
    def clock_enabled(self):
        return self.clock_remaining is not None

    def clock_should_run(self):
        return (
            self.clock_remaining is not None
            and not self.game_over
            and not self.paused
            and bool(self.moves)
        )

    def reset_clock(self, now=None):
        base = self.time_control.get("base")
        if base is None:
            self.clock_remaining = None
            self.clock_last = None
        else:
            self.clock_remaining = {
                chess.WHITE: float(base),
                chess.BLACK: float(base),
            }
            self.clock_last = now

    def start_clock(self, now):
        self.clock_last = now

    def tick(self, now):
        """Advance the running clock and return the side that flagged."""
        if self.clock_remaining is None or self.game_over:
            return None
        if self.clock_last is None:
            self.clock_last = now
            return None
        elapsed = now - self.clock_last
        self.clock_last = now
        turn = self.board.turn
        self.clock_remaining[turn] = max(
            0.0, self.clock_remaining[turn] - elapsed
        )
        if self.clock_remaining[turn] <= 0:
            return turn
        return None

    def _apply_increment(self, color):
        if self.clock_remaining is None:
            return
        self.clock_remaining[color] += self.time_control.get("increment", 0)

    @staticmethod
    def format_clock(seconds):
        seconds = max(0.0, seconds)
        if seconds < 10:
            return f"{seconds:.1f}"
        minutes, secs = divmod(int(seconds), 60)
        return f"{minutes}:{secs:02d}"
