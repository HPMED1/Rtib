"""Settings tab — Ollama config, default sort model, and Auto-mode tuning.

The Auto-mode section is clearly labeled so the user understands it only
affects the one-shot header suggestion call, not every row.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from rtib.core.ollama_client import OllamaClient
from rtib.core.settings import AppSettings, SettingsStore


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("brand")
    return lbl


def _sub_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("muted")
    lbl.setWordWrap(True)
    return lbl


def _hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFrameShadow(QFrame.Shadow.Sunken)
    return line


class SettingsTab(QWidget):
    def __init__(self, settings: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(16)

        outer.addWidget(_section_label("Connection"))
        outer.addWidget(_sub_label("Where Rtib looks for Ollama."))

        conn_form = QFormLayout()
        self._url_edit = QLineEdit()
        conn_form.addRow("Ollama URL", self._url_edit)
        outer.addLayout(conn_form)

        outer.addWidget(_hline())
        outer.addWidget(_section_label("Sort model"))
        outer.addWidget(_sub_label("Used for every row when you click Sort."))

        sort_form = QFormLayout()
        self._sort_model_combo = QComboBox()
        self._sort_model_combo.setEditable(True)
        sort_form.addRow("Model", self._sort_model_combo)

        self._chunk_spin = QSpinBox()
        self._chunk_spin.setRange(1, 500)
        self._chunk_spin.setSuffix(" rows / batch")
        sort_form.addRow("Chunk size", self._chunk_spin)
        outer.addLayout(sort_form)

        outer.addWidget(_hline())
        outer.addWidget(_section_label("Auto mode (header suggestion only)"))
        outer.addWidget(
            _sub_label(
                "These settings affect the one-shot call that suggests headers when you "
                "click \"Suggest headers\". They do NOT change how individual rows are sorted."
            )
        )

        auto_form = QFormLayout()
        self._auto_model_combo = QComboBox()
        self._auto_model_combo.setEditable(True)
        auto_form.addRow("Header model", self._auto_model_combo)

        self._auto_sample_spin = QSpinBox()
        self._auto_sample_spin.setRange(1, 500)
        self._auto_sample_spin.setSuffix(" rows sent for analysis")
        auto_form.addRow("Sample size", self._auto_sample_spin)
        outer.addLayout(auto_form)

        outer.addStretch(1)

        row = QHBoxLayout()
        row.addStretch(1)
        refresh_btn = QPushButton("Refresh models from Ollama")
        refresh_btn.clicked.connect(self._refresh_models)
        row.addWidget(refresh_btn)

        save_btn = QPushButton("Apply")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._on_apply)
        row.addWidget(save_btn)
        outer.addLayout(row)

        self._load_from_settings(self._settings.current)
        self._refresh_models()

    def _load_from_settings(self, s: AppSettings) -> None:
        self._url_edit.setText(s.ollama_url)
        if self._sort_model_combo.findText(s.sort_model) < 0:
            self._sort_model_combo.addItem(s.sort_model)
        self._sort_model_combo.setCurrentText(s.sort_model)
        if self._auto_model_combo.findText(s.auto_header_model) < 0:
            self._auto_model_combo.addItem(s.auto_header_model)
        self._auto_model_combo.setCurrentText(s.auto_header_model)
        self._chunk_spin.setValue(s.chunk_size)
        self._auto_sample_spin.setValue(s.auto_header_sample_rows)

    def _refresh_models(self) -> None:
        url = self._url_edit.text().strip() or self._settings.current.ollama_url
        client = OllamaClient(url, timeout_s=10.0)
        try:
            models = client.list_models()
        except Exception:
            return
        names = sorted({m.name for m in models})
        current_sort = self._sort_model_combo.currentText()
        current_auto = self._auto_model_combo.currentText()
        self._sort_model_combo.clear()
        self._auto_model_combo.clear()
        for n in names:
            self._sort_model_combo.addItem(n)
            self._auto_model_combo.addItem(n)
        if current_sort:
            if self._sort_model_combo.findText(current_sort) < 0:
                self._sort_model_combo.addItem(current_sort)
            self._sort_model_combo.setCurrentText(current_sort)
        if current_auto:
            if self._auto_model_combo.findText(current_auto) < 0:
                self._auto_model_combo.addItem(current_auto)
            self._auto_model_combo.setCurrentText(current_auto)

    def _on_apply(self) -> None:
        new = AppSettings(
            ollama_url=self._url_edit.text().strip() or self._settings.current.ollama_url,
            sort_model=self._sort_model_combo.currentText().strip()
            or self._settings.current.sort_model,
            auto_header_model=self._auto_model_combo.currentText().strip()
            or self._settings.current.auto_header_model,
            auto_header_sample_rows=self._auto_sample_spin.value(),
            chunk_size=self._chunk_spin.value(),
            request_timeout_s=self._settings.current.request_timeout_s,
        )
        self._settings.update(new)
