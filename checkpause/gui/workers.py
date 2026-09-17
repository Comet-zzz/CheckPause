import chess
import chess.engine
from PySide6.QtCore import QThread, Signal

from checkpause.config import play_engine_settings
from checkpause.core import cloud
from checkpause.core.ai import ChatRequestError, chat_with_model
from checkpause.core.cloud import CloudRequestError
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
    progress = Signal(int)
    move_done = Signal(int, int, str, str)
    done = Signal(list, float)
    failed = Signal(str)

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
    move_ready = Signal(str)
    failed = Signal(str)

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
    progress = Signal(int)
    done = Signal(dict)
    failed = Signal(str, str)

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
    chunk = Signal(str)
    done = Signal(str)
    failed = Signal(str)

    def __init__(self, messages, language="zh-CN", parent=None, cloud_request=None):
        """``cloud_request`` selects the paid path.

        It is a dict with server_url, token, pgn, analysis and history. The
        request then carries raw material only - the server builds the prompt -
        which is what keeps the tuned prompt off user machines. Passing None
        keeps the bring-your-own-key path.
        """
        super().__init__(parent)
        self.messages = list(messages)
        self.language = language
        self.cloud_request = dict(cloud_request) if cloud_request else None

    def _pieces(self):
        if not self.cloud_request:
            return chat_with_model(self.messages, self.language)
        return cloud.stream_reply(
            self.cloud_request.get("server_url", ""),
            self.cloud_request.get("token", ""),
            self.cloud_request.get("pgn", ""),
            self.cloud_request.get("analysis", ""),
            self.cloud_request.get("history", []),
            self.language,
        )

    def run(self):
        full_reply = ""
        try:
            for piece in self._pieces():
                full_reply += piece
                self.chunk.emit(piece)
        except (ChatRequestError, CloudRequestError) as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.done.emit(full_reply)


class AccountWorker(QThread):
    """Signs in, registers, or re-reads the balance without freezing the UI."""

    done = Signal(dict)
    failed = Signal(str)

    def __init__(
        self,
        action,
        server_url,
        language="zh-CN",
        username="",
        password="",
        token="",
        yuan=0,
        order_id="",
        parent=None,
    ):
        super().__init__(parent)
        self.action = action
        self.server_url = server_url
        self.language = language
        self.username = username
        self.password = password
        self.token = token
        self.yuan = yuan
        self.order_id = order_id

    def run(self):
        try:
            if self.action == "register":
                result = cloud.register(
                    self.server_url, self.username, self.password, self.language
                )
            elif self.action == "sign_in":
                result = cloud.sign_in(
                    self.server_url, self.username, self.password, self.language
                )
            elif self.action == "sign_out":
                cloud.sign_out(self.server_url, self.token, self.language)
                result = {"token": "", "account": {}}
            elif self.action == "packs":
                result = {
                    "packs": cloud.fetch_packs(self.server_url, self.language)
                }
            elif self.action == "open_order":
                result = {
                    "order": cloud.create_order(
                        self.server_url, self.token, self.yuan, self.language
                    )
                }
            elif self.action == "order_status":
                result = {
                    "order": cloud.order_status(
                        self.server_url,
                        self.token,
                        self.order_id,
                        self.language,
                    )
                }
            else:
                result = {
                    "token": self.token,
                    "account": cloud.fetch_account(
                        self.server_url, self.token, self.language
                    ),
                }
        except CloudRequestError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.done.emit(result)


class UpdateCheckWorker(QThread):
    """Looks for a newer release; reports the result and never raises."""

    checked = Signal(object)
    failed = Signal()

    def run(self):
        try:
            info = check_for_update(strict=True)
        except Exception:
            self.failed.emit()
            return
        self.checked.emit(info)
