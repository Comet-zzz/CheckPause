import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from checkpause.resources import resource_path


def main(argv=None):
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName("CheckPause")
    app.setWindowIcon(QIcon(resource_path("assets", "app.ico")))

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
