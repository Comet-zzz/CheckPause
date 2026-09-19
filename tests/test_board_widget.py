import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import chess
import chess.pgn

try:
    from PySide6.QtWidgets import QApplication

    from checkpause.gui.widgets.board import BoardWidget
    from checkpause.gui.widgets.move_list import MoveListWidget

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


PGN = "1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 *"

CUSTOM_FEN = "8/8/8/8/8/8/4P3/4K2k w - - 0 1"


@unittest.skipUnless(_APP is not None, "Qt is not available")
class BoardWidgetTests(unittest.TestCase):
    def make_board(self, pgn=PGN):
        board = BoardWidget()
        self.assertTrue(board.load_pgn(pgn)[0])
        return board

    def test_goto_animates_single_steps_in_both_directions(self):
        board = self.make_board()
        self.assertIsNone(board._animation)

        board.goto(1)
        animation = board._animation
        self.assertEqual((animation["from"], animation["to"]), (chess.E2, chess.E4))
        self.assertFalse(animation["fade_in"])

        board.goto(2)
        animation = board._animation
        self.assertEqual((animation["from"], animation["to"]), (chess.E7, chess.E5))

        board.goto(1)
        animation = board._animation
        self.assertEqual((animation["from"], animation["to"]), (chess.E5, chess.E7))
        self.assertTrue(animation["fade_in"])

    def test_multi_step_jumps_do_not_animate(self):
        board = self.make_board()
        board.goto(4)
        self.assertIsNone(board._animation)

    def test_castling_animation_carries_the_rook(self):
        board = self.make_board()
        board.goto(8)
        board.goto(9)
        animation = board._animation
        self.assertEqual((animation["from"], animation["to"]), (chess.E1, chess.G1))
        self.assertEqual(animation["rook"], (chess.H1, chess.F1))

        board.goto(8)
        animation = board._animation
        self.assertEqual(animation["rook"], (chess.F1, chess.H1))

    def test_edit_places_moves_and_removes_pieces(self):
        board = BoardWidget()
        board.start_edit()
        self.assertTrue(board.is_editing())

        board.edit_place(chess.E4)
        self.assertIsNone(board.piece_at(chess.E4))

        board._on_palette(chess.Piece(chess.KNIGHT, chess.WHITE))
        board.edit_place(chess.E4)
        self.assertEqual(
            board.piece_at(chess.E4), chess.Piece(chess.KNIGHT, chess.WHITE)
        )
        board.edit_move_piece(chess.E4, chess.D5)
        self.assertIsNone(board.piece_at(chess.E4))
        self.assertEqual(board.piece_at(chess.D5).piece_type, chess.KNIGHT)
        board.edit_remove(chess.D5)
        self.assertIsNone(board.piece_at(chess.D5))

        board._on_palette("erase")
        board.edit_place(chess.E1)
        self.assertIsNone(board.piece_at(chess.E1))

    def test_apply_edit_keeps_the_position_and_clears_the_line(self):
        board = self.make_board()
        board.start_edit()
        board._on_palette(chess.Piece(chess.QUEEN, chess.BLACK))
        board.edit_place(chess.E4)
        applied = []
        board.position_applied.connect(applied.append)

        fen = board.apply_edit()

        self.assertFalse(board.is_editing())
        self.assertEqual(board._start_fen, fen)
        self.assertEqual(applied, [fen])
        self.assertEqual(board._moves, [])
        self.assertEqual(board.piece_at(chess.E4).piece_type, chess.QUEEN)
        self.assertEqual(board.piece_at(chess.E4).color, chess.BLACK)

    def test_apply_edit_normalises_the_standard_position(self):
        board = BoardWidget()
        board.start_edit()
        board.apply_edit()
        self.assertIsNone(board._start_fen)

    def test_cancel_edit_restores_start_position_and_line(self):
        board = self.make_board()
        self.assertIsNone(board._start_fen)
        moves = list(board._moves)
        board.goto(3)

        board.start_edit()
        board.edit_remove(chess.E1)
        board.cancel_edit()

        self.assertFalse(board.is_editing())
        self.assertEqual(board._moves, moves)
        self.assertEqual(board._index, 3)
        self.assertEqual(board.piece_at(chess.E1), chess.Piece(chess.KING, chess.WHITE))

    def test_edit_controls_make_legal_en_passant_squares_available(self):
        board = BoardWidget()
        board.set_start_fen(
            "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"
        )
        board.start_edit()
        self.assertEqual(board._ep_combo.count(), 2)
        self.assertEqual(board._ep_combo.itemData(1), chess.D6)

        board._edit_turn.setCurrentIndex(1)
        self.assertEqual(board._board.turn, chess.BLACK)
        self.assertEqual(board._ep_combo.count(), 1)

        board._edit_turn.setCurrentIndex(0)
        board._castling_boxes[0][0].setChecked(False)
        self.assertFalse(board._board.castling_rights & chess.BB_H1)
        self.assertTrue(board._board.castling_rights & chess.BB_A1)

    def test_play_move_appends_then_advances_without_replacement(self):
        board = BoardWidget()
        board.set_interactive(True, None)
        replaced = []
        board.line_changed.connect(replaced.append)

        self.assertTrue(board.play_move(chess.E2, chess.E4))
        self.assertEqual(board._moves, [chess.Move.from_uci("e2e4")])
        self.assertFalse(board.play_move(chess.E2, chess.E4))
        self.assertEqual(replaced, [False])

    def test_play_move_branches_and_reports_the_replacement(self):
        board = BoardWidget()
        board.set_interactive(True, None)
        board.play_move(chess.E2, chess.E4)
        board.play_move(chess.E7, chess.E5)
        board.goto(1)
        replaced = []
        board.line_changed.connect(replaced.append)

        self.assertTrue(board.play_move(chess.C7, chess.C5))

        self.assertEqual(replaced, [True])
        self.assertEqual(
            board._moves, [chess.Move.from_uci("e2e4"), chess.Move.from_uci("c7c5")]
        )
        self.assertEqual(board._index, 2)

    def test_line_pgn_round_trips_a_custom_start_position(self):
        board = BoardWidget()
        board.set_start_fen(CUSTOM_FEN)
        board.set_interactive(True, None)
        self.assertTrue(board.play_move(chess.E2, chess.E4))
        self.assertTrue(board.play_move(chess.H1, chess.H2))

        line = board.line_pgn()

        self.assertIn('[FEN "{}"]'.format(CUSTOM_FEN), line)
        self.assertIn('[SetUp "1"]', line)

        reloaded = BoardWidget()
        self.assertTrue(reloaded.load_pgn(line)[0])
        self.assertEqual(reloaded._start_fen, CUSTOM_FEN)
        self.assertEqual(reloaded._moves, board._moves)


@unittest.skipUnless(_APP is not None, "Qt is not available")
class MoveListWidgetTests(unittest.TestCase):
    def test_white_to_move_list_is_unchanged(self):
        widget = MoveListWidget()
        self.assertTrue(widget.set_moves("1. e4 e5 *"))

        self.assertEqual(widget._table.item(0, 0).text(), "1.")
        self.assertEqual(widget._table.item(0, 1).text(), "e4")
        self.assertEqual(widget._table.item(0, 2).text(), "e5")
        self.assertIs(widget._table.item(0, 2), widget._item_for_ply(2))

    def test_black_to_move_start_shifts_the_columns(self):
        widget = MoveListWidget()
        pgn = (
            '[SetUp "1"]\n[FEN "4k3/8/8/8/8/8/8/4K3 b - - 0 7"]\n\n'
            "7... Kd7 8. Kd2 *"
        )
        self.assertTrue(widget.set_moves(pgn))

        self.assertEqual(widget._table.item(0, 0).text(), "7.")
        self.assertIsNone(widget._table.item(0, 1))
        self.assertEqual(widget._table.item(0, 2).text(), "Kd7")
        self.assertEqual(widget._table.item(1, 0).text(), "8.")
        self.assertEqual(widget._table.item(1, 1).text(), "Kd2")
        self.assertIs(widget._table.item(0, 2), widget._item_for_ply(1))
        self.assertIs(widget._table.item(1, 1), widget._item_for_ply(2))


if __name__ == "__main__":
    unittest.main()
