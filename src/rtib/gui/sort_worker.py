"""Background workers for the two LLM-driven steps.

Both run on QThreads so the GUI stays responsive and so the user can
cancel. Each emits signals carrying typed results — the GUI never touches
the ``OllamaClient`` directly.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from rtib.core.ollama_client import OllamaClient, OllamaError
from rtib.core.pipeline import RowResult, sort_row, suggest_headers
from rtib.core.schema import Header


class HeaderSuggestionWorker(QThread):
    """One-shot worker: sends a sample to the model, emits the suggested headers."""

    succeeded = Signal(list)  # list[Header]
    failed = Signal(str)

    def __init__(
        self,
        client: OllamaClient,
        model: str,
        sample_rows: list[str],
        hint: str | None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._client = client
        self._model = model
        self._sample_rows = sample_rows
        self._hint = hint

    def run(self) -> None:
        try:
            headers = suggest_headers(self._client, self._model, self._sample_rows, self._hint)
        except OllamaError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:  # last-resort guard so the thread can't crash silently
            self.failed.emit(f"Unexpected error: {exc}")
            return
        if not headers:
            self.failed.emit("Model returned no headers.")
            return
        self.succeeded.emit(headers)


class SortWorker(QThread):
    """Streams ``sort_row`` calls. Emits one signal per finished row."""

    row_done = Signal(int, RowResult)  # index, result
    progress = Signal(int, int)  # done, total
    finished_ok = Signal()
    failed = Signal(str)

    def __init__(
        self,
        client: OllamaClient,
        model: str,
        rows: list[str],
        headers: list[Header],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._client = client
        self._model = model
        self._rows = rows
        self._headers = headers
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def run(self) -> None:
        total = len(self._rows)
        for i, row in enumerate(self._rows):
            if self._cancelled:
                return
            try:
                result = sort_row(self._client, self._model, row, self._headers)
            except Exception as exc:
                result = RowResult(raw=row, values=None, error=f"Unexpected: {exc}")
            self.row_done.emit(i, result)
            self.progress.emit(i + 1, total)
        self.finished_ok.emit()
