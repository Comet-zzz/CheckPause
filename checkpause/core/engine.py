import io
import chess
import chess.pgn
import chess.engine
import chess.polyglot
from checkpause.config import BOOK_MAX_PLIES, BOOK_MIN_WEIGHT, ENGINE_LIMIT
from checkpause.i18n import t
from checkpause.resources import get_opening_book_path, get_stockfish_path


class StockfishAnalyzer:
    def __init__(self, path=None, limit=ENGINE_LIMIT, book_path=None):
        self.path = path
        self.limit = limit
        self.book_path = book_path
        self._engine = None
        self._book = None

    def _start(self, language="zh-CN"):
        if self._engine is None:
            path = self.path or get_stockfish_path(language)
            self._engine = chess.engine.SimpleEngine.popen_uci(path)
        return self._engine

    def _open_book(self):
        if self._book is None:
            path = self.book_path or get_opening_book_path()
            if path:
                try:
                    self._book = chess.polyglot.open_reader(path)
                except Exception:
                    self._book = False
            else:
                self._book = False
        return self._book or None

    def _is_book_move(self, book, board, move):
        try:
            entries = book.find_all(board, minimum_weight=BOOK_MIN_WEIGHT)
        except Exception:
            return False
        for entry in entries:
            if entry.move == move:
                return True
        return False

    def close(self):
        if self._engine is not None:
            try:
                self._engine.quit()
            finally:
                self._engine = None
        if self._book:
            try:
                self._book.close()
            finally:
                self._book = None

    def analyze(self, pgn_text, language="zh-CN", on_progress=None,
                on_move=None, should_stop=None):
        board = chess.Board()
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None:
            return None, t("pgn_invalid", language), None
        moves = list(game.mainline_moves())
        total_moves = len(moves)
        if total_moves == 0:
            return None, t("pgn_no_moves", language), None

        book = self._open_book()
        book_active = book is not None

        results = []
        total_moves_analyzed = 0
        total_score = 0.0

        try:
            for idx, move in enumerate(moves, start=1):
                if should_stop is not None and should_stop():
                    break

                san = board.san(move)

                if idx % 2 == 1:
                    turn = (idx + 1) // 2
                    color = "White"
                else:
                    turn = idx // 2
                    color = "Black"
                turn_desc = f"Turn {turn} {color}"

                is_book = (
                    book_active
                    and idx <= BOOK_MAX_PLIES
                    and self._is_book_move(book, board, move)
                )

                if is_book:
                    board.push(move)
                    move_score = 1.0
                    rel_score = None
                    best = None
                else:
                    try:
                        engine = self._start(language)
                    except Exception as exc:
                        return None, str(exc), None

                    info_before = engine.analyse(board, self.limit)
                    score_before = info_before.get('score')
                    best = info_before.get('pv')[0] if info_before.get('pv') else None

                    board.push(move)

                    info_after = engine.analyse(board, self.limit)
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

                total_moves_analyzed += 1
                total_score += move_score

                record = {
                    "turn_color": turn_desc,
                    "move": san,
                    "engine_score": rel_score,
                    "best_move": best.uci() if best else None,
                    "fen_after": board.fen(),
                    "move_score": move_score,
                    "book": is_book,
                }
                results.append(record)

                if on_move is not None:
                    on_move(idx, total_moves, san, board.fen(), record)
                if on_progress is not None:
                    on_progress(int(idx / total_moves * 100))

            if total_moves_analyzed > 0:
                accuracy = round((total_score / total_moves_analyzed) * 100, 1)
            else:
                accuracy = None
            return results, None, accuracy

        finally:
            self.close()


def compact_analysis(results):
    lines = []
    for r in results:
        move = r['move']
        if r.get("book"):
            lines.append(f"{move}(book)")
            continue
        score = r['engine_score']
        best = r.get('best_move')
        if best and best != move:
            lines.append(f"{move}(score:{score}, best:{best})")
        else:
            lines.append(f"{move}(score:{score})")
    return "; ".join(lines)
