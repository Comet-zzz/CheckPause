from PyQt6.QtCore import QThread, pyqtSignal

from checkpause.core.ai import ChatRequestError, chat_with_model
from checkpause.core.engine import StockfishAnalyzer


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
