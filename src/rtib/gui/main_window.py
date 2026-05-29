"""Skeleton main window.

Shows: brand, theme toggle, model dropdown populated from Ollama, and a status
indicator. The actual sort/format flow lands in a follow-up.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from rtib import __app_name__, __version__
from rtib.core.ollama_client import OllamaClient
from rtib.core.settings import AppSettings
from rtib.gui.theme import Theme, stylesheet_for


class MainWindow(QMainWindow):
    def __init__(self, initial_theme: Theme = Theme.DARK) -> None:
        super().__init__()
        self.setWindowTitle(f"{__app_name__} — arrange messy text")
        self.resize(900, 600)

        self._settings = AppSettings()
        self._ollama = OllamaClient(self._settings.ollama_url)
        self._theme = initial_theme

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

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))
        self._model_combo = QComboBox()
        self._model_combo.setMinimumWidth(260)
        model_row.addWidget(self._model_combo)
        model_row.addStretch(1)
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_ollama_status)
        model_row.addWidget(refresh_btn)
        outer.addLayout(model_row)

        placeholder = QLabel(
            "End-to-end flow coming next:\n"
            "  1. Load or paste your messy data\n"
            "  2. Describe what it is (optional hint)\n"
            "  3. Review suggested headers, edit/remove\n"
            "  4. Sort with Ollama → editable preview → export"
        )
        placeholder.setObjectName("muted")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        placeholder.setWordWrap(True)
        outer.addWidget(placeholder, 1)

        status = self.statusBar()
        self._status_dot = QLabel("●")
        self._status_text = QLabel("Checking Ollama…")
        status.addPermanentWidget(self._status_dot)
        status.addPermanentWidget(self._status_text)
        status.showMessage(f"v{__version__}")

    def _theme_button_label(self) -> str:
        return "Light mode" if self._theme == Theme.DARK else "Dark mode"

    def _toggle_theme(self) -> None:
        self._theme = Theme.LIGHT if self._theme == Theme.DARK else Theme.DARK
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(stylesheet_for(self._theme))
        self._theme_btn.setText(self._theme_button_label())
        self._restyle_status_dot(self._last_health_ok)

    _last_health_ok: bool = False

    def _refresh_ollama_status(self) -> None:
        ok = self._ollama.health_check()
        self._last_health_ok = ok
        self._restyle_status_dot(ok)
        if ok:
            version = self._ollama.version() or "?"
            self._status_text.setText(f"Ollama {version}")
            self._populate_models()
        else:
            self._status_text.setText("Ollama unreachable")
            self._model_combo.clear()
            self._model_combo.addItem("— Ollama not running —")
            self._model_combo.setEnabled(False)

    def _restyle_status_dot(self, ok: bool) -> None:
        self._status_dot.setObjectName("statusDotOk" if ok else "statusDotBad")
        self._status_dot.style().unpolish(self._status_dot)
        self._status_dot.style().polish(self._status_dot)

    def _populate_models(self) -> None:
        try:
            models = self._ollama.list_models()
        except Exception as exc:
            self._model_combo.clear()
            self._model_combo.addItem(f"— error: {exc} —")
            self._model_combo.setEnabled(False)
            return

        self._model_combo.clear()
        self._model_combo.setEnabled(True)
        names = sorted(m.name for m in models)
        for name in names:
            self._model_combo.addItem(name)

        default = self._settings.model
        idx = self._model_combo.findText(default)
        if idx >= 0:
            self._model_combo.setCurrentIndex(idx)
