import chess


class PuzzleSession:
    """Tracks progress while solving a single puzzle.

    ``moves`` is a full UCI line. When ``opponent_first`` is true (the Lichess
    format) the first move is the opponent's setup move and the remaining line
    alternates solver / opponent, starting with the solver.
    """

    def __init__(self, fen, moves, opponent_first=False):
        self._solution = list(moves or [])
        self._played = []
        self.board = chess.Board(fen)
        if opponent_first and self._solution:
            try:
                setup = chess.Move.from_uci(self._solution[0])
            except ValueError:
                setup = None
            if setup is not None and setup in self.board.legal_moves:
                self.board.push(setup)
                self._played.append(setup)
                self._solution = self._solution[1:]
        self.human_color = self.board.turn
        self.progress = 0
        self.solved = False

    @property
    def solution(self):
        return list(self._solution)

    @property
    def applied_moves(self):
        return list(self._played)

    @property
    def is_human_turn(self):
        return not self.solved and self.progress % 2 == 0

    @property
    def expected_move(self):
        if self.solved or self.progress >= len(self._solution):
            return None
        return self._solution[self.progress]

    @property
    def total_moves(self):
        return (len(self._solution) + 1) // 2

    @property
    def solved_moves(self):
        return (self.progress + 1) // 2

    def play(self, move):
        if self.solved:
            return "solved"
        if not self.is_human_turn:
            return "not_your_turn"
        if self.progress >= len(self._solution):
            self.solved = True
            return "solved"
        expected = self._solution[self.progress]
        if move.uci() != expected and not self._is_alternative_mate(move):
            return "wrong"
        self._push(move)
        if self.progress >= len(self._solution):
            self.solved = True
            return "solved"
        return "correct"

    def opponent_reply(self):
        if self.solved or self.progress >= len(self._solution):
            return None
        if self.is_human_turn:
            return None
        try:
            move = chess.Move.from_uci(self._solution[self.progress])
        except ValueError:
            return None
        if move not in self.board.legal_moves:
            return None
        self._push(move)
        if self.progress >= len(self._solution):
            self.solved = True
        return move

    def _push(self, move):
        self.board.push(move)
        self._played.append(move)
        self.progress += 1

    def _is_alternative_mate(self, move):
        if move not in self.board.legal_moves:
            return False
        probe = self.board.copy()
        probe.push(move)
        return probe.is_checkmate()
