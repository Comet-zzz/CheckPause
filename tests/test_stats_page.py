import os
import unittest
from datetime import date, timedelta

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

try:
    from PySide6.QtWidgets import QApplication, QLabel

    from checkpause.gui.pages.stats_page import StatsPage

    _APP = QApplication.instance() or QApplication([])
except Exception:
    _APP = None


@unittest.skipUnless(_APP is not None, "Qt is not available")
class StatsPageTests(unittest.TestCase):
    def _profile(self):
        today = date.today().strftime("%Y-%m-%d")
        older = (date.today() - timedelta(days=40)).strftime("%Y-%m-%d")
        return {
            "username": "Tester",
            "total_games": 3,
            "latest_accuracy": 90,
            "history": [
                {"date": f"{older} 10:00:00", "accuracy": 60},
                {"date": f"{today} 11:00:00", "accuracy": 80},
                {"date": f"{today} 12:00:00", "accuracy": 90},
            ],
        }

    def test_rows_are_newest_first_and_keep_history_indices(self):
        page = StatsPage()
        page.refresh(self._profile())
        self.assertEqual([row.index for row in page._history_rows], [2, 1, 0])

    def test_rows_are_grouped_by_relative_date(self):
        page = StatsPage()
        page.refresh(self._profile())
        labels = [
            label.text()
            for label in page.findChildren(QLabel)
            if label.objectName() == "historyGroupLabel"
        ]
        self.assertEqual(labels, ["今天", "更早"])

    def test_selection_circles_are_hidden_until_the_select_button_is_clicked(self):
        page = StatsPage()
        page.refresh(self._profile())
        self.assertFalse(page._history_rows[0]._check.isVisibleTo(page))
        self.assertFalse(page._delete_selected_button.isVisibleTo(page))

        page._select_button.click()
        self.assertTrue(page._history_rows[0]._check.isVisibleTo(page))
        self.assertTrue(page._delete_selected_button.isVisibleTo(page))

        page._history_rows[0].set_checked(True)
        page._select_button.click()
        self.assertFalse(page._history_rows[0].is_checked())
        self.assertFalse(page._history_rows[0]._check.isVisibleTo(page))
        self.assertFalse(page._delete_selected_button.isVisibleTo(page))

    def test_delete_button_tracks_the_checked_rows(self):
        page = StatsPage()
        page.refresh(self._profile())
        page._select_button.click()
        self.assertFalse(page._delete_selected_button.isEnabled())

        page._history_rows[0].set_checked(True)
        page._history_rows[2].set_checked(True)
        self.assertTrue(page._delete_selected_button.isEnabled())

        page._history_rows[0].set_checked(False)
        page._history_rows[2].set_checked(False)
        self.assertFalse(page._delete_selected_button.isEnabled())

    def test_emits_every_checked_history_index(self):
        page = StatsPage()
        page.refresh(self._profile())
        page._select_button.click()
        page._history_rows[0].set_checked(True)
        page._history_rows[2].set_checked(True)
        received = []
        page.history_delete_requested.connect(received.append)
        page._emit_delete_selected()
        self.assertEqual(received, [[2, 0]])


if __name__ == "__main__":
    unittest.main()
