"""Classify analysed moves the way a game-review report does.

The engine stores, per ply, the evaluation of the position before and after the
move (white point of view) plus the top few candidate moves. This module turns
those numbers into the familiar move labels - Best, Inaccuracy, Blunder and so
on - using a win-probability loss model rather than raw centipawns, so a quiet
position is judged differently from a sharp one.

It is a heuristic approximation of a proprietary review: Brilliant, Great,
Only move and Miss are best-effort and will not always match other tools. The
thresholds below are the knobs to tune.
"""

import io
import math

import chess
import chess.pgn

# Win probability lost by a move, in "win percentage points". The cutoffs
# mirror the widely used review scale.
EXCELLENT_MAX = 2.0
GOOD_MAX = 5.0
INACCURACY_MAX = 10.0
MISTAKE_MAX = 20.0

# A move within this much of the engine's best counts as having played best.
BEST_MAX = 1.0

# How far the runner-up must fall behind before the played move counts as the
# only good one (Great / Only move).
SECOND_BEST_MIN = 20.0

# Win probability that separates "keeps a clear advantage" (Great) from "only
# move that saves the game" (Only move).
ADVANTAGE_MIN = 65.0

# A missed win: the mover was already winning heavily (or had mate) and threw
# most of it away.
MISS_BEFORE_MIN = 90.0
MISS_DROP_MIN = 15.0

# A sacrifice must still leave the mover at least this well off, and the
# position before it must not already be decided.
BRILLIANT_MIN_WIN = 50.0
BRILLIANT_MAX_WIN = 97.0

# Lichess' logistic fit from centipawns to white's win probability.
_WIN_SLOPE = 0.00368208

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}

# Every label, in the order the report should list them.
MOVE_LABELS = (
    "Brilliant",
    "Great",
    "Best",
    "Excellent",
    "Good",
    "Book",
    "Forced",
    "Only move",
    "Inaccuracy",
    "Mistake",
    "Miss",
    "Blunder",
)


def win_percent(cp, mate=None):
    """White's win probability (0..100) from centipawns or a mate score."""
    if mate is not None:
        return 100.0 if mate > 0 else 0.0
    if cp is None:
        return None
    return 50.0 + 50.0 * (2.0 / (1.0 + math.exp(-_WIN_SLOPE * cp)) - 1.0)


def _side_win(cp, mate, white_to_move):
    white = win_percent(cp, mate)
    if white is None:
        return None
    return white if white_to_move else 100.0 - white


def _mover_mate(mate, white_to_move):
    if mate is None:
        return None
    return mate if white_to_move else -mate


def _piece_value(board, square):
    piece = board.piece_at(square)
    if piece is None:
        return 0
    return PIECE_VALUES.get(piece.piece_type, 0)


def _is_sacrifice(board, move):
    """Heuristic: does the move leave material for the opponent to take?

    True when the moved piece lands on a square an enemy piece can capture for
    profit (cheaper attacker, or no defender). It deliberately over-approximates
    so the Brilliant label stays rare without needing a full search.
    """
    piece = board.piece_at(move.from_square)
    if piece is None:
        return False
    moved_value = PIECE_VALUES.get(piece.piece_type, 0)
    after = board.copy(stack=False)
    after.push(move)
    if after.is_checkmate():
        return False
    attackers = after.attackers(after.turn, move.to_square)
    if not attackers:
        return False
    cheapest = min(_piece_value(after, square) for square in attackers)
    defenders = after.attackers(not after.turn, move.to_square)
    if not defenders:
        return moved_value >= 1 and cheapest < moved_value
    cheapest_defender = min(_piece_value(after, square) for square in defenders)
    return cheapest < moved_value and cheapest < cheapest_defender


def _second_best_loss(record, win_before, white_to_move):
    alts = record.get("alts") or []
    wins = []
    for alt in alts:
        win = _side_win(alt.get("cp"), alt.get("mate"), white_to_move)
        if win is not None:
            wins.append(win)
    if len(wins) < 2:
        return None
    wins.sort(reverse=True)
    return win_before - wins[1]


def _is_miss(win_before, win_after, mate_before, mate_after):
    had_mate = mate_before is not None and mate_before > 0
    kept_mate = mate_after is not None and mate_after > 0
    if had_mate and not kept_mate:
        return True
    return win_before >= MISS_BEFORE_MIN and win_before - win_after >= MISS_DROP_MIN


def _is_brilliant(board, move, win_before, win_after):
    if win_before > BRILLIANT_MAX_WIN or win_after < BRILLIANT_MIN_WIN:
        return False
    if win_after > BRILLIANT_MAX_WIN:
        return False
    return _is_sacrifice(board, move)


def _fallback_label(record):
    score = record.get("move_score")
    if score is None:
        return "Good"
    if score >= 1.0:
        return "Best"
    if score >= 0.75:
        return "Excellent"
    if score >= 0.5:
        return "Good"
    if score >= 0.25:
        return "Inaccuracy"
    return "Mistake"


def _mating_label(board, move, record, white_to_move):
    before = record.get("eval_before") or {}
    win_before = _side_win(before.get("cp"), before.get("mate"), white_to_move)
    if win_before is not None and _is_brilliant(board, move, win_before, 100.0):
        return "Brilliant"
    return "Best"


def classify_move(board, move, record):
    """Label one played move from its pre/post evaluations and candidates."""
    if record.get("book"):
        return "Book"

    legal = record.get("legal_count")
    if legal is None:
        legal = board.legal_moves.count()
    if legal == 1:
        return "Forced"

    white_to_move = board.turn == chess.WHITE

    # Delivering checkmate is never a mistake, whatever the engine reports for
    # the (already finished) position after it.
    board_after = board.copy(stack=False)
    board_after.push(move)
    if board_after.is_checkmate():
        return _mating_label(board, move, record, white_to_move)

    before = record.get("eval_before") or {}
    after = record.get("eval_after") or {}
    win_before = _side_win(before.get("cp"), before.get("mate"), white_to_move)
    win_after = _side_win(after.get("cp"), after.get("mate"), white_to_move)
    if win_before is None or win_after is None:
        return _fallback_label(record)

    loss = max(0.0, win_before - win_after)
    best_uci = record.get("best_move")
    is_best = best_uci is not None and move.uci() == best_uci

    if is_best and loss <= BEST_MAX:
        if _is_brilliant(board, move, win_before, win_after):
            return "Brilliant"
        second_loss = _second_best_loss(record, win_before, white_to_move)
        if second_loss is not None and second_loss >= SECOND_BEST_MIN:
            if win_after >= ADVANTAGE_MIN:
                return "Great"
            return "Only move"
        return "Best"

    mate_before = _mover_mate(before.get("mate"), white_to_move)
    mate_after = _mover_mate(after.get("mate"), white_to_move)
    if _is_miss(win_before, win_after, mate_before, mate_after):
        return "Miss"

    if loss <= EXCELLENT_MAX:
        return "Excellent"
    if loss <= GOOD_MAX:
        return "Good"
    if loss <= INACCURACY_MAX:
        return "Inaccuracy"
    if loss <= MISTAKE_MAX:
        return "Mistake"
    return "Blunder"


def classify(results, pgn_text):
    """Annotate every analysed ply with a label and return a summary.

    ``results`` are the engine records for the game; ``pgn_text`` supplies the
    board states (side to move, material) that the records do not carry. The
    original records are not modified - each is copied before a ``label`` key is
    added - and any record without a matching move is kept with a null label.
    """
    annotated = []
    counts = {label: 0 for label in MOVE_LABELS}
    if not results:
        return [], {"counts": counts, "total": 0}

    game = chess.pgn.read_game(io.StringIO(pgn_text or ""))
    moves = list(game.mainline_moves()) if game is not None else []
    board = game.board() if game is not None else None

    for index, record in enumerate(results):
        annotated_record = dict(record)
        if board is not None and index < len(moves):
            move = moves[index]
            side = "white" if board.turn == chess.WHITE else "black"
            annotated_record["label"] = classify_move(board, move, record)
            annotated_record["side"] = side
            board.push(move)
        else:
            annotated_record["label"] = None
            annotated_record["side"] = None
        annotated.append(annotated_record)
        label = annotated_record["label"]
        if label is not None:
            counts[label] = counts.get(label, 0) + 1

    return annotated, {"counts": counts, "total": len(annotated)}


def labels_for(annotated, side="all"):
    """The labels to show, or ``None`` for moves outside the chosen side."""
    if side == "all":
        return [record.get("label") for record in annotated]
    return [record.get("label") if record.get("side") == side else None for record in annotated]


def summary_for(annotated, side="all"):
    """Recount the labels, keeping only moves played by the chosen side."""
    counts = {label: 0 for label in MOVE_LABELS}
    total = 0
    for record in annotated:
        if side != "all" and record.get("side") != side:
            continue
        total += 1
        label = record.get("label")
        if label is not None:
            counts[label] = counts.get(label, 0) + 1
    return {"counts": counts, "total": total}


def format_summary(summary):
    """Render the label counts as a single report line, in report order."""
    counts = (summary or {}).get("counts") or {}
    parts = [f"{label} {counts[label]}" for label in MOVE_LABELS if counts.get(label)]
    return " \u00b7 ".join(parts)
