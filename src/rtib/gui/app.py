"""QApplication bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rtib import __app_name__
from rtib.gui.main_window import MainWindow


def run_gui() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName(__app_name__)

    # MainWindow picks the theme from persisted settings (defaults to dark).
    window = MainWindow()
    window.show()
    return app.exec()
