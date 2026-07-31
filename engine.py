import io
import chess
import chess.pgn
import chess.engine
from config import STOCKFISH_PATH, ENGINE_LIMIT

engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

def analyze_with_stockfish(pgn_text):
    board = chess.Board()
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return None, "Invalid PGN", None
    moves = list(game.mainline_moves())
    total_moves = len(moves)
    if total_moves == 0:
        return None, "No moves in PGN", None

    results = []
    total_moves_analyzed = 0
    total_score = 0.0

    print("⚙️ Stockfish engine analyzing...")
    try:
        for idx, move in enumerate(moves, start=1):
            san = board.san(move)

            info_before = engine.analyse(board, ENGINE_LIMIT)
            score_before = info_before.get('score')
            best = info_before.get('pv')[0] if info_before.get('pv') else None

            board.push(move)

            info_after = engine.analyse(board, ENGINE_LIMIT)
            score_after = info_after.get('score')

            move_score = 0.0
            if score_before and score_before.is_mate():
                move_score = 1.0
            elif score_after and score_after.is_mate():
                move_score = 1.0
            else:
                try:
                    score_best = score_before.white().score() if score_before else None
                    score_user = score_after.white().score() if score_after else None
                    if score_best is not None and score_user is not None:
                        cpl = abs(score_best - score_user)
                        if cpl <= 20:
                            move_score = 1.0
                        elif cpl <= 80:
                            move_score = 0.75
                        elif cpl <= 180:
                            move_score = 0.5
                        elif cpl <= 300:
                            move_score = 0.25
                        else:
                            move_score = 0.0
                    else:
                        move_score = 0.5
                except Exception:
                    move_score = 0.5

            total_moves_analyzed += 1
            total_score += move_score

            if score_after:
                if score_after.is_mate():
                    try:
                        mate_steps = score_after.mate()
                        rel_score = f"Checkmate in {mate_steps}"
                    except AttributeError:
                        rel_score = "Checkmate"
                else:
                    rel_score = score_after.relative.score()
            else:
                rel_score = None

            if idx % 2 == 1:
                turn = (idx + 1) // 2
                color = "White"
            else:
                turn = idx // 2
                color = "Black"
            turn_desc = f"Turn {turn} {color}"

            results.append({
                "turn_color": turn_desc,
                "move": san,
                "engine_score": rel_score,
                "best_move": best.uci() if best else None
            })

            percent = int(idx / total_moves * 100)
            bar_length = 20
            filled = int(percent / 100 * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r  progress: [{bar}] {percent}%", end="")

        print("\n✅ Ready")
        if total_moves_analyzed > 0:
            accuracy = round((total_score / total_moves_analyzed) * 100, 1)
        else:
            accuracy = None
        return results, None, accuracy

    finally:
        engine.quit()