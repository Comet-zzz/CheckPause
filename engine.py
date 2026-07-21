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
    accurate_moves = 0

    print("⚙️ Stockfish engine analyzing...")
    try:
        for idx, move in enumerate(moves, start=1):
            san = board.san(move)
            info = engine.analyse(board, ENGINE_LIMIT)
            best = info.get('pv')[0] if info.get('pv') else None
            if best is not None and move == best:
                accurate_moves += 1.0
            board.push(move)

            score = info.get('score')
            if score:
                if score.is_mate():
                    try:
                        mate_steps = score.mate()
                        rel_score = f"将杀 (第{mate_steps}步)"
                    except AttributeError:
                        rel_score = "将杀"
                else:
                    rel_score = score.relative.score()
            else:
                rel_score = None

            if idx % 2 == 1:
                turn = (idx + 1) // 2
                color = "白方"
            else:
                turn = idx // 2
                color = "黑方"
            turn_desc = f"第{turn}回合{color}"

            results.append({
                "回合_颜色": turn_desc,
                "走法": san,
                "引擎评分": rel_score,
                "最佳走法": best.uci() if best else None
            })

            total_moves_analyzed += 1

            percent = int(idx / total_moves * 100)
            bar_length = 20
            filled = int(percent / 100 * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            print(f"\r  progress: [{bar}] {percent}%", end="")

        print("\n✅ Ready")
        if total_moves_analyzed > 0:
            accuracy = round((accurate_moves / total_moves_analyzed) * 100, 1)
        else:
            accuracy = None
        return results, None, accuracy

    finally:
        engine.quit()