"""App settings — defaults and the persistence-backed store.

Sort model: used for the actual row-by-row formatting pass.
Auto-mode keys: only consulted when the user clicks "Suggest headers" —
the model and sample size for that one-shot call are separate so the user
can pick a smarter (slower) model for header suggestion without paying
that cost on every row.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QObject, QSettings, Signal


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_SORT_MODEL = "granite4.1:3b"
DEFAULT_AUTO_HEADER_MODEL = "granite4.1:3b"
DEFAULT_AUTO_HEADER_SAMPLE_ROWS = 20
DEFAULT_CHUNK_SIZE = 25
DEFAULT_REQUEST_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class AppSettings:
    ollama_url: str = DEFAULT_OLLAMA_URL
    sort_model: str = DEFAULT_SORT_MODEL
    auto_header_model: str = DEFAULT_AUTO_HEADER_MODEL
    auto_header_sample_rows: int = DEFAULT_AUTO_HEADER_SAMPLE_ROWS
    chunk_size: int = DEFAULT_CHUNK_SIZE
    request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S


class SettingsStore(QObject):
    """QSettings-backed store. Single source of truth for the running app.

    Cross-platform: registry on Windows, plist on macOS, INI on Linux.
    Anyone can subscribe to ``changed`` to react to user-applied edits.
    """

    changed = Signal(AppSettings)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._qs = QSettings()
        self._current = self._load()

    @property
    def current(self) -> AppSettings:
        return self._current

    def update(self, new: AppSettings) -> None:
        if new == self._current:
            return
        self._current = new
        self._persist(new)
        self.changed.emit(new)

    def _load(self) -> AppSettings:
        q = self._qs
        return AppSettings(
            ollama_url=str(q.value("ollama_url", DEFAULT_OLLAMA_URL)),
            sort_model=str(q.value("sort_model", DEFAULT_SORT_MODEL)),
            auto_header_model=str(q.value("auto/header_model", DEFAULT_AUTO_HEADER_MODEL)),
            auto_header_sample_rows=int(
                q.value("auto/header_sample_rows", DEFAULT_AUTO_HEADER_SAMPLE_ROWS)
            ),
            chunk_size=int(q.value("chunk_size", DEFAULT_CHUNK_SIZE)),
            request_timeout_s=float(
                q.value("request_timeout_s", DEFAULT_REQUEST_TIMEOUT_S)
            ),
        )

    def _persist(self, s: AppSettings) -> None:
        q = self._qs
        q.setValue("ollama_url", s.ollama_url)
        q.setValue("sort_model", s.sort_model)
        q.setValue("auto/header_model", s.auto_header_model)
        q.setValue("auto/header_sample_rows", s.auto_header_sample_rows)
        q.setValue("chunk_size", s.chunk_size)
        q.setValue("request_timeout_s", s.request_timeout_s)
        q.sync()
