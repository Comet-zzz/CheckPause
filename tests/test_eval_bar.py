import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from checkpause.gui.widgets.eval_bar import EvalBar

_APP = QApplication.instance() or QApplication([])


class EvalBarTest(unittest.TestCase):
    def test_ratio_is_clamped(self):
        bar = EvalBar()
        bar.set_ratio(-1.0)
        self.assertEqual(bar._ratio, 0.0)
        bar.set_ratio(2.0)
        self.assertEqual(bar._ratio, 1.0)
        bar.set_ratio(0.25)
        self.assertEqual(bar._ratio, 0.25)

    def test_bar_is_a_thin_strip(self):
        bar = EvalBar()
        self.assertLessEqual(bar.width(), 12)
        bar.set_colors("#ffffff", "#000000", "#000000")
        self.assertEqual(bar._light, "#ffffff")


if __name__ == "__main__":
    unittest.main()
