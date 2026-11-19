import os
import threading
import time
import unittest
from types import SimpleNamespace
from unittest import mock

import chess

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.gui import workers

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


class _FakeOption:
    def __init__(self, minimum):
        self.min = minimum


class _FakeEngine:
    def __init__(self, moves):
        self.options = {"UCI_Elo": _FakeOption(1320)}
        self.moves = list(moves)
        self.plays = []
        self.quit_called = 0

    def play(self, board, limit, *, game=None, options=None, **_kwargs):
        self.plays.append(
            {
                "fen": board.fen(),
                "nodes": limit.nodes,
                "game": game,
                "options": dict(options or {}),
            }
        )
        if not self.moves:
            raise AssertionError("the fake engine ran out of moves")
        return SimpleNamespace(move=chess.Move.from_uci(self.moves.pop(0)))

    def quit(self):
        self.quit_called += 1


class _BlockingEngine(_FakeEngine):
    def __init__(self, moves):
        super().__init__(moves)
        self.started = threading.Event()
        self.release = threading.Event()

    def play(self, board, limit, *, game=None, options=None, **kwargs):
        self.started.set()
        self.release.wait(5)
        return super().play(board, limit, game=game, options=options, **kwargs)


class _SignalLog:
    """Record a cross-thread signal while spinning the Qt event loop."""

    def __init__(self, signal):
        self.items = []
        signal.connect(self._record)

    def _record(self, *args):
        self.items.append(args)

    def wait(self, count=1, timeout=5.0):
        deadline = time.monotonic() + timeout
        while len(self.items) < count and time.monotonic() < deadline:
            _APP.processEvents()
            time.sleep(0.005)
        _APP.processEvents()
        return self.items


@unittest.skipUnless(_APP is not None, "Qt is not available")
class PlayEngineWorkerTests(unittest.TestCase):
    def _worker(self, engine):
        worker = workers.PlayEngineWorker("zh-CN")
        patcher = mock.patch.object(workers, "open_stockfish", return_value=engine)
        self.addCleanup(patcher.stop)
        patcher.start()
        return worker

    def _start(self, worker):
        worker.start()
        self.addCleanup(self._stop, worker)
        return worker

    @staticmethod
    def _stop(worker):
        worker.stop()
        worker.wait(5000)

    def test_reuses_the_engine_across_moves_and_games(self):
        engine = _FakeEngine(["e2e4", "e7e5"])
        worker = self._start(self._worker(engine))
        moves = _SignalLog(worker.move_ready)

        first = worker.request(chess.STARTING_FEN, 1500, 1)
        self.assertEqual(moves.wait(1), [(first, "e2e4")])

        second = worker.request(chess.STARTING_FEN, 600, 2)
        self.assertEqual(moves.wait(2)[1], (second, "e7e5"))

        self.assertEqual(len(engine.plays), 2)
        self.assertEqual(engine.plays[0]["game"], 1)
        self.assertEqual(engine.plays[1]["game"], 2)
        self.assertTrue(engine.plays[0]["options"]["UCI_LimitStrength"])
        self.assertEqual(engine.plays[0]["options"]["UCI_Elo"], 1500)
        # Falling below the Elo floor must switch the limiter back off,
        # otherwise the old UCI_Elo keeps overriding Skill Level.
        self.assertFalse(engine.plays[1]["options"]["UCI_LimitStrength"])
        self.assertNotIn("UCI_Elo", engine.plays[1]["options"])

    def test_drops_a_move_the_user_already_replaced(self):
        engine = _BlockingEngine(["e2e4", "e7e5"])
        worker = self._start(self._worker(engine))
        moves = _SignalLog(worker.move_ready)

        stale = worker.request(chess.STARTING_FEN, 1500, 1)
        self.assertTrue(engine.started.wait(5))
        worker.cancel()
        current = worker.request(chess.STARTING_FEN, 1500, 2)
        engine.release.set()

        self.assertEqual(moves.wait(1), [(current, "e7e5")])
        self.assertNotEqual(current, stale)

    def test_reports_failures_with_the_request_token(self):
        worker = workers.PlayEngineWorker("zh-CN")
        patcher = mock.patch.object(
            workers, "open_stockfish", side_effect=RuntimeError("engine missing")
        )
        self.addCleanup(patcher.stop)
        patcher.start()
        worker = self._start(worker)
        failures = _SignalLog(worker.failed)

        token = worker.request(chess.STARTING_FEN, 1500, 1)
        self.assertEqual(failures.wait(1), [(token, "engine missing")])

        # The worker stays alive so a later turn can retry a fresh engine.
        retry = worker.request(chess.STARTING_FEN, 1500, 1)
        self.assertEqual(failures.wait(2)[1], (retry, "engine missing"))


if __name__ == "__main__":
    unittest.main()
