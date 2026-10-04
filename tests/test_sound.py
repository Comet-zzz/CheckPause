import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import chess

from checkpause.assets import DEFAULT_SOUND_SET, SOUND_SETS
from checkpause.gui.sound import SOUND_KINDS, SoundPlayer, move_sound_kind
from checkpause.resources import resource_path

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.gui.widgets.board import BoardWidget

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


def _play_uci(uci_moves):
    board = chess.Board()
    for uci in uci_moves:
        board.push_uci(uci)
    last = chess.Move.from_uci(uci_moves[-1])
    return board, last


class MoveSoundKindTests(unittest.TestCase):
    def test_quiet_move(self):
        board, move = _play_uci(["e2e4"])
        self.assertEqual(move_sound_kind(board, move, True), "move")

    def test_capture(self):
        board, move = _play_uci(["e2e4", "d7d5", "e4d5"])
        self.assertEqual(move_sound_kind(board, move, True), "capture")

    def test_en_passant_counts_as_capture(self):
        board, move = _play_uci(["e2e4", "a7a6", "e4e5", "d7d5", "e5d6"])
        self.assertEqual(move_sound_kind(board, move, True), "capture")

    def test_castling(self):
        board, move = _play_uci(
            ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "f8c5", "e1g1"]
        )
        self.assertEqual(move_sound_kind(board, move, True), "castle")

    def test_promotion(self):
        board = chess.Board("8/P7/8/8/8/8/8/4K2k w - - 0 1")
        move = chess.Move.from_uci("a7a8q")
        board.push(move)
        self.assertEqual(move_sound_kind(board, move, True), "promote")

    def test_check(self):
        board, move = _play_uci(["e2e4", "f7f5", "d1h5"])
        self.assertTrue(board.is_check())
        self.assertEqual(move_sound_kind(board, move, True), "check")

    def test_capture_that_also_checks_prefers_check(self):
        board, move = _play_uci(["e2e4", "e7e5", "f1c4", "g8f6", "c4f7"])
        self.assertTrue(board.is_capture(move))
        self.assertTrue(board.is_check())
        self.assertEqual(move_sound_kind(board, move, True), "check")

    def test_checkmate_outranks_the_capture(self):
        board, move = _play_uci(
            ["e2e4", "e7e5", "f1c4", "b8c6", "d1h5", "g8f6", "h5f7"]
        )
        self.assertTrue(board.is_checkmate())
        self.assertEqual(move_sound_kind(board, move, True), "checkmate")

    def test_stalemate_reads_as_a_draw(self):
        board = chess.Board("7k/3Q4/6K1/8/8/8/8/8 w - - 0 1")
        move = chess.Move.from_uci("d7f7")
        board.push(move)
        self.assertTrue(board.is_stalemate())
        self.assertEqual(move_sound_kind(board, move, True), "draw")

    def test_stepping_back_never_reports_check(self):
        board, move = _play_uci(["e2e4", "f7f5", "d1h5"])
        before = board.copy()
        before.pop()
        self.assertEqual(move_sound_kind(before, move, False), "move")

    def test_stepping_back_classifies_captures(self):
        board, move = _play_uci(["e2e4", "d7d5", "e4d5"])
        before = board.copy()
        before.pop()
        self.assertEqual(move_sound_kind(before, move, False), "capture")


class SoundPlayerTests(unittest.TestCase):
    def test_silent_by_default_and_safe_to_call(self):
        player = SoundPlayer()
        self.assertFalse(player.is_enabled())
        player.play("move")
        player.play("no_such_kind")

    def test_disabling_stays_disabled(self):
        player = SoundPlayer()
        player.set_enabled(True)
        player.set_enabled(False)
        self.assertFalse(player.is_enabled())

    def test_sets_are_selectable(self):
        player = SoundPlayer()
        for name in SOUND_SETS:
            player.set_set(name)
        player.set_set("nonsense")
        self.assertEqual(player._set, DEFAULT_SOUND_SET)


class SoundAssetTests(unittest.TestCase):
    def test_every_set_has_every_kind(self):
        for name in SOUND_SETS:
            for kind in SOUND_KINDS:
                path = resource_path(
                    "assets", "sounds", name, kind + ".wav"
                )
                self.assertTrue(os.path.isfile(path), path)


@unittest.skipUnless(_APP is not None, "Qt is not available")
class BoardSoundTests(unittest.TestCase):
    def test_board_starts_silent(self):
        board = BoardWidget()
        self.assertFalse(board._sound.is_enabled())

    def test_goto_accepts_the_sound_flag(self):
        board = BoardWidget()
        self.assertTrue(board.load_pgn("1. e4 e5 *")[0])
        board.goto(1, sound=False)
        self.assertIsNotNone(board._animation)


if __name__ == "__main__":
    unittest.main()
