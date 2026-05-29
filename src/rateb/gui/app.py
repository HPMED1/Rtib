"""QApplication bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from rateb import __app_name__
from rateb.gui.main_window import MainWindow
from rateb.gui.theme import Theme, stylesheet_for


def run_gui() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName(__app_name__)

    initial_theme = Theme.DARK
    app.setStyleSheet(stylesheet_for(initial_theme))

    window = MainWindow(initial_theme=initial_theme)
    window.show()
    return app.exec()
