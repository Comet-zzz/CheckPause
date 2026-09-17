import chess
import chess.engine
from PyQt6.QtCore import QThread, pyqtSignal

from checkpause.config import play_engine_settings
from checkpause.core.ai import ChatRequestError, chat_with_model
from checkpause.core.engine import StockfishAnalyzer, open_stockfish
from checkpause.core.updater import check_for_update
from checkpause.data.puzzles import PuzzleImportError, import_collection
from checkpause.i18n import t
from checkpause.resources import get_stockfish_path


def _engine_elo_floor(engine):
    """Return ``(has_uci_elo, floor)`` for the running engine."""
    option = engine.options.get("UCI_Elo")
    if option is None:
        return False, None
    try:
        return True, int(option.min)
    except (TypeError, ValueError):
        return True, None


class AnalysisWorker(QThread):
    progress = pyqtSignal(int)
    move_done = pyqtSignal(int, int, str, str)
    done = pyqtSignal(list, float)
    failed = pyqtSignal(str)

    def __init__(self, pgn_text, language="zh-CN", parent=None):
        super().__init__(parent)
        self.pgn_text = pgn_text
        self.language = language

    def run(self):
        analyzer = StockfishAnalyzer()
        try:
            results, err, accuracy = analyzer.analyze(
                self.pgn_text,
                self.language,
                on_progress=self.progress.emit,
                on_move=self._emit_move,
                should_stop=self.isInterruptionRequested,
            )
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        if err:
            self.failed.emit(err)
            return

        self.done.emit(results, accuracy if accuracy is not None else 0.0)

    def _emit_move(self, index, total, san, fen, record):
        self.move_done.emit(index, total, san, fen)


class EngineMoveWorker(QThread):
    move_ready = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, fen, rating, language="zh-CN", parent=None):
        super().__init__(parent)
        self.fen = fen
        self.rating = rating
        self.language = language

    def run(self):
        try:
            path = get_stockfish_path(self.language)
            engine = open_stockfish(path)
        except Exception as exc:
            self.failed.emit(str(exc))
            return

        try:
            supports_elo, floor = _engine_elo_floor(engine)
            settings = play_engine_settings(
                self.rating, elo_floor=floor, supports_elo=supports_elo
            )
            try:
                engine.configure(settings["options"])
            except chess.engine.EngineError:
                pass
            limit = chess.engine.Limit(nodes=settings["nodes"])
            result = engine.play(chess.Board(self.fen), limit)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        finally:
            try:
                engine.quit()
            except Exception:
                pass

        if result.move is None:
            self.failed.emit(t("play_no_move", self.language))
            return
        self.move_ready.emit(result.move.uci())


class PuzzleImportWorker(QThread):
    progress = pyqtSignal(int)
    done = pyqtSignal(dict)
    failed = pyqtSignal(str, str)

    def __init__(self, path, name=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.name = name

    def run(self):
        try:
            meta = import_collection(
                self.path, self.name, self._emit_progress
            )
        except PuzzleImportError as exc:
            self.failed.emit(exc.code, exc.detail)
            return
        except Exception as exc:
            self.failed.emit("read_error", str(exc))
            return
        self.done.emit(meta)

    def _emit_progress(self, count):
        self.progress.emit(count)


class ChatWorker(QThread):
    chunk = pyqtSignal(str)
    done = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, messages, language="zh-CN", parent=None):
        super().__init__(parent)
        self.messages = list(messages)
        self.language = language

    def run(self):
        full_reply = ""
        try:
            for piece in chat_with_model(self.messages, self.language):
                full_reply += piece
                self.chunk.emit(piece)
        except ChatRequestError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.done.emit(full_reply)


class UpdateCheckWorker(QThread):
    """Looks for a newer release; reports the result and never raises."""

    checked = pyqtSignal(object)
    failed = pyqtSignal()

    def run(self):
        try:
            info = check_for_update(strict=True)
        except Exception:
            self.failed.emit()
            return
        self.checked.emit(info)
