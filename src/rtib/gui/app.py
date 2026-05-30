"""QApplication bootstrap."""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from rtib import __app_name__, __version__
from rtib.gui.icon import resolve_icon_path
from rtib.gui.main_window import MainWindow


def _setup_windows_taskbar_id() -> None:
    """Tell Windows we're our own app, not Python.

    Without an explicit AppUserModelID, Windows groups our window under the
    Python interpreter's taskbar entry and uses Python's icon instead of ours.
    This MUST be called before creating any windows.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes

        app_id = f"rtib.gui.{__version__}"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:  # noqa: BLE001 — taskbar grouping is cosmetic
        pass


def run_gui() -> int:
    _setup_windows_taskbar_id()
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName(__app_name__)

    icon_path = resolve_icon_path()
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # MainWindow picks the theme from persisted settings (defaults to dark).
    window = MainWindow()
    window.show()
    return app.exec()
