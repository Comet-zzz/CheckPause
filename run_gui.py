import sys

from PyQt6.QtWidgets import QApplication, QMessageBox


def main(argv=None):
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("CheckPause")

    try:
        from checkpause.gui.main_window import MainWindow
    except Exception as exc:
        QMessageBox.critical(None, "CheckPause", str(exc))
        return 1

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
