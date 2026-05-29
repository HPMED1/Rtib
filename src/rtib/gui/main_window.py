"""Main window — brand bar on top, Sort/Settings tabs in the middle,
Ollama health in the status bar.

Drag-drop is wired at the window level: dropping a text file routes its
contents into the Sort tab's input area.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from rtib import __app_name__, __version__
from rtib.core.ollama_client import OllamaClient
from rtib.core.settings import SettingsStore
from rtib.gui.settings_tab import SettingsTab
from rtib.gui.sort_tab import SortTab
from rtib.gui.theme import Theme, stylesheet_for


class MainWindow(QMainWindow):
    def __init__(self, initial_theme: Theme = Theme.DARK) -> None:
        super().__init__()
        self.setWindowTitle(f"{__app_name__} — arrange messy text")
        self.resize(1100, 720)
        self.setAcceptDrops(True)

        self._settings_store = SettingsStore(self)
        self._theme = initial_theme
        self._last_health_ok = False

        self._build_ui()
        self._refresh_ollama_status()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(24, 20, 24, 20)
        outer.setSpacing(16)

        header = QHBoxLayout()
        brand = QLabel(__app_name__)
        brand.setObjectName("brand")
        subtitle = QLabel("— arrange messy text into clean JSON, CSV or XLSX")
        subtitle.setObjectName("muted")
        header.addWidget(brand)
        header.addWidget(subtitle)
        header.addStretch(1)

        self._theme_btn = QPushButton(self._theme_button_label())
        self._theme_btn.clicked.connect(self._toggle_theme)
        header.addWidget(self._theme_btn)
        outer.addLayout(header)

        self._tabs = QTabWidget()
        self._sort_tab = SortTab(self._settings_store)
        self._sort_tab.status_message.connect(self._show_status_message)
        self._settings_tab = SettingsTab(self._settings_store)
        self._tabs.addTab(self._sort_tab, "Sort")
        self._tabs.addTab(self._settings_tab, "Settings")
        outer.addWidget(self._tabs, 1)

        status = self.statusBar()
        self._status_dot = QLabel("●")
        self._status_text = QLabel("Checking Ollama…")
        status.addPermanentWidget(self._status_dot)
        status.addPermanentWidget(self._status_text)
        status.showMessage(f"v{__version__}")

        self._settings_store.changed.connect(self._on_settings_changed)

    def _theme_button_label(self) -> str:
        return "Light mode" if self._theme == Theme.DARK else "Dark mode"

    def _toggle_theme(self) -> None:
        self._theme = Theme.LIGHT if self._theme == Theme.DARK else Theme.DARK
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet_for(self._theme))
        self._theme_btn.setText(self._theme_button_label())
        self._restyle_status_dot(self._last_health_ok)

    def _show_status_message(self, msg: str) -> None:
        self.statusBar().showMessage(msg, 5000)

    def _on_settings_changed(self) -> None:
        self._refresh_ollama_status()
        self._show_status_message("Settings applied")

    def _refresh_ollama_status(self) -> None:
        url = self._settings_store.current.ollama_url
        client = OllamaClient(url, timeout_s=5.0)
        ok = client.health_check()
        self._last_health_ok = ok
        self._restyle_status_dot(ok)
        if ok:
            version = client.version() or "?"
            self._status_text.setText(f"Ollama {version}")
        else:
            self._status_text.setText("Ollama unreachable")

    def _restyle_status_dot(self, ok: bool) -> None:
        self._status_dot.setObjectName("statusDotOk" if ok else "statusDotBad")
        self._status_dot.style().unpolish(self._status_dot)
        self._status_dot.style().polish(self._status_dot)

    # ---------- Drag-drop ----------

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.isLocalFile():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        for url in urls:
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file():
                self._tabs.setCurrentWidget(self._sort_tab)
                self._sort_tab.load_text_from_path(path)
                event.acceptProposedAction()
                return
        event.ignore()
