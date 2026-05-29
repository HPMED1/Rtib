"""The main Sort tab — the user's workflow from messy input to exported file.

Three pages in a QStackedWidget:
  0. Input  — paste / load / drag-drop. Choose Auto, Manual, or load a Template.
  1. Headers — review/edit the columns. "Save as template…" persists them for reuse.
  2. Preview — streaming results, then export.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from rtib.core.exporters import export_csv, export_json, export_xlsx
from rtib.core.ollama_client import OllamaClient
from rtib.core.pipeline import RowResult
from rtib.core.schema import Header
from rtib.core.settings import SettingsStore
from rtib.core.templates import (
    list_templates,
    load_template,
    save_template,
    template_exists,
)
from rtib.gui.headers_panel import HeadersPanel
from rtib.gui.hint_dialog import HintDialog
from rtib.gui.preview_table import PreviewModel, PreviewTable
from rtib.gui.sort_worker import HeaderSuggestionWorker, SortWorker


PAGE_INPUT = 0
PAGE_HEADERS = 1
PAGE_PREVIEW = 2


class SortTab(QWidget):
    status_message = Signal(str)

    def __init__(self, settings: SettingsStore, parent=None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._headers: list[Header] = []
        self._current_hint: str | None = None
        self._suggest_worker: HeaderSuggestionWorker | None = None
        self._sort_worker: SortWorker | None = None
        self._preview_model: PreviewModel | None = None

        self._stack = QStackedWidget()
        self._stack.addWidget(self._build_input_page())
        self._stack.addWidget(self._build_headers_page())
        self._stack.addWidget(self._build_preview_page())

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(self._stack)

    # ---------- Input page ----------

    def _build_input_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        intro = QLabel(
            "Paste your messy text below (one item per line), load a file, "
            "or drag a text file onto this window."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self._input_edit = QTextEdit()
        self._input_edit.setPlaceholderText("e.g. one movie filename per line")
        self._input_edit.setAcceptRichText(False)
        self._input_edit.textChanged.connect(self._on_input_changed)
        layout.addWidget(self._input_edit, 1)

        self._row_count = QLabel("0 rows")
        self._row_count.setObjectName("muted")
        layout.addWidget(self._row_count)

        row = QHBoxLayout()
        load_btn = QPushButton("Load file…")
        load_btn.clicked.connect(self._on_load_file)
        row.addWidget(load_btn)
        row.addStretch(1)

        manual_btn = QPushButton("Enter headers manually")
        manual_btn.clicked.connect(self._go_manual)
        row.addWidget(manual_btn)

        templates_btn = QPushButton("Templates ▾")
        templates_btn.setToolTip("Load a previously saved set of headers")
        self._templates_menu = QMenu(templates_btn)
        self._templates_menu.aboutToShow.connect(self._rebuild_templates_menu)
        templates_btn.setMenu(self._templates_menu)
        row.addWidget(templates_btn)

        suggest_btn = QPushButton("Suggest headers")
        suggest_btn.setObjectName("primary")
        suggest_btn.clicked.connect(self._on_suggest_headers)
        row.addWidget(suggest_btn)

        self._suggest_btn = suggest_btn
        self._manual_btn = manual_btn
        self._templates_btn = templates_btn

        layout.addLayout(row)
        return page

    def _on_input_changed(self) -> None:
        n = len(self._current_rows())
        self._row_count.setText(f"{n} rows")

    def _current_rows(self) -> list[str]:
        text = self._input_edit.toPlainText()
        return [line for line in (raw.strip() for raw in text.splitlines()) if line]

    def _on_load_file(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Load text file",
            "",
            "Text files (*.txt *.log *.csv *.tsv);;All files (*.*)",
        )
        if not path_str:
            return
        self.load_text_from_path(Path(path_str))

    def load_text_from_path(self, path: Path) -> None:
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            QMessageBox.warning(self, "Couldn't open file", str(exc))
            return
        self._input_edit.setPlainText(content)
        self.status_message.emit(f"Loaded {path.name}")

    def _go_manual(self) -> None:
        rows = self._current_rows()
        if not rows:
            QMessageBox.information(
                self,
                "No input",
                "Paste some text or load a file before defining headers.",
            )
            return
        self._current_hint = None
        self._set_headers([Header(name="", description="")])
        self._stack.setCurrentIndex(PAGE_HEADERS)

    def _on_suggest_headers(self) -> None:
        rows = self._current_rows()
        if not rows:
            QMessageBox.information(
                self,
                "No input",
                "Paste some text or load a file first.",
            )
            return

        dlg = HintDialog(self)
        if dlg.exec() != HintDialog.DialogCode.Accepted:
            return
        hint = dlg.hint or None
        self._current_hint = hint

        s = self._settings.current
        sample = rows[: max(1, s.auto_header_sample_rows)]
        client = OllamaClient(s.ollama_url, timeout_s=s.request_timeout_s)

        self._suggest_btn.setEnabled(False)
        self._manual_btn.setEnabled(False)
        self.status_message.emit("Asking the model for headers…")

        self._suggest_worker = HeaderSuggestionWorker(
            client=client,
            model=s.auto_header_model,
            sample_rows=sample,
            hint=hint,
            parent=self,
        )
        self._suggest_worker.succeeded.connect(self._on_suggest_succeeded)
        self._suggest_worker.failed.connect(self._on_suggest_failed)
        self._suggest_worker.finished.connect(self._suggest_worker.deleteLater)
        self._suggest_worker.start()

    def _on_suggest_succeeded(self, headers: list[Header]) -> None:
        self._suggest_btn.setEnabled(True)
        self._manual_btn.setEnabled(True)
        self._set_headers(headers)
        self._stack.setCurrentIndex(PAGE_HEADERS)
        self.status_message.emit(f"Suggested {len(headers)} headers")

    def _on_suggest_failed(self, msg: str) -> None:
        self._suggest_btn.setEnabled(True)
        self._manual_btn.setEnabled(True)
        QMessageBox.warning(self, "Header suggestion failed", msg)
        self.status_message.emit("Header suggestion failed")

    # ---------- Templates menu ----------

    def _rebuild_templates_menu(self) -> None:
        self._templates_menu.clear()
        templates = list_templates()
        if not templates:
            action = self._templates_menu.addAction("No saved templates")
            action.setEnabled(False)
            return
        for t in templates:
            action = self._templates_menu.addAction(t.name)
            # Default arg captures the name in this iteration's scope.
            action.triggered.connect(lambda _checked=False, n=t.name: self._on_use_template(n))

    def _on_use_template(self, name: str) -> None:
        rows = self._current_rows()
        if not rows:
            QMessageBox.information(
                self,
                "No input",
                "Paste some text or load a file before loading a template.",
            )
            return
        tpl = load_template(name)
        if tpl is None or not tpl.headers:
            QMessageBox.warning(self, "Template missing", f"Could not load template '{name}'.")
            return
        self._current_hint = tpl.hint
        self._set_headers(tpl.headers)
        self._stack.setCurrentIndex(PAGE_HEADERS)
        self.status_message.emit(f"Loaded template '{tpl.name}' ({len(tpl.headers)} headers)")

    # ---------- Headers page ----------

    def _build_headers_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        info = QLabel(
            "Review the columns Rtib will extract. Edit the names and "
            "descriptions, remove anything you don't want, or add your own."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self._headers_panel = HeadersPanel()
        layout.addWidget(self._headers_panel, 1)

        row = QHBoxLayout()
        back_btn = QPushButton("← Back")
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_INPUT))
        row.addWidget(back_btn)
        row.addStretch(1)

        save_tpl_btn = QPushButton("Save as template…")
        save_tpl_btn.clicked.connect(self._on_save_template)
        row.addWidget(save_tpl_btn)

        sort_btn = QPushButton("Sort →")
        sort_btn.setObjectName("primary")
        sort_btn.clicked.connect(self._on_sort_clicked)
        row.addWidget(sort_btn)

        layout.addLayout(row)
        return page

    def _set_headers(self, headers: list[Header]) -> None:
        self._headers = list(headers)
        self._headers_panel.set_headers(self._headers)

    def _on_save_template(self) -> None:
        headers = self._headers_panel.headers()
        if not headers:
            QMessageBox.information(self, "Nothing to save", "Define at least one header first.")
            return
        name, ok = QInputDialog.getText(
            self,
            "Save template",
            "Template name:",
            QLineEdit.EchoMode.Normal,
            "",
        )
        name = name.strip()
        if not ok or not name:
            return
        if template_exists(name):
            reply = QMessageBox.question(
                self,
                "Overwrite template?",
                f"A template named '{name}' already exists. Overwrite it?",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        tpl = save_template(name, headers, self._current_hint)
        self.status_message.emit(f"Saved template '{tpl.name}'")

    def _on_sort_clicked(self) -> None:
        headers = self._headers_panel.headers()
        if not headers:
            QMessageBox.information(self, "No headers", "Define at least one header before sorting.")
            return
        rows = self._current_rows()
        if not rows:
            QMessageBox.information(self, "No input", "The input is empty.")
            return

        self._headers = headers
        self._preview_model = self._preview_table.set_model_with(headers)
        self._progress.setMaximum(len(rows))
        self._progress.setValue(0)
        self._set_export_enabled(False)
        self._cancel_btn.setEnabled(True)

        s = self._settings.current
        client = OllamaClient(s.ollama_url, timeout_s=s.request_timeout_s)
        self._sort_worker = SortWorker(
            client=client,
            model=s.sort_model,
            rows=rows,
            headers=headers,
            parent=self,
        )
        self._sort_worker.row_done.connect(self._on_row_done)
        self._sort_worker.progress.connect(self._on_progress)
        self._sort_worker.finished_ok.connect(self._on_sort_finished)
        self._sort_worker.failed.connect(self._on_sort_failed)
        self._sort_worker.finished.connect(self._sort_worker.deleteLater)
        self._stack.setCurrentIndex(PAGE_PREVIEW)
        self._sort_worker.start()
        self.status_message.emit("Sorting…")

    # ---------- Preview / Export page ----------

    def _build_preview_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        top = QHBoxLayout()
        self._progress = QProgressBar()
        self._progress.setRange(0, 1)
        top.addWidget(self._progress, 1)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self._on_cancel)
        top.addWidget(self._cancel_btn)
        layout.addLayout(top)

        self._preview_table = PreviewTable()
        layout.addWidget(self._preview_table, 1)

        bottom = QHBoxLayout()
        back_btn = QPushButton("← Back to headers")
        back_btn.clicked.connect(lambda: self._stack.setCurrentIndex(PAGE_HEADERS))
        bottom.addWidget(back_btn)
        bottom.addStretch(1)

        self._json_btn = QPushButton("Export JSON")
        self._csv_btn = QPushButton("Export CSV")
        self._xlsx_btn = QPushButton("Export XLSX")
        self._json_btn.clicked.connect(lambda: self._on_export("json"))
        self._csv_btn.clicked.connect(lambda: self._on_export("csv"))
        self._xlsx_btn.clicked.connect(lambda: self._on_export("xlsx"))
        for b in (self._json_btn, self._csv_btn, self._xlsx_btn):
            bottom.addWidget(b)
        self._set_export_enabled(False)

        layout.addLayout(bottom)
        return page

    def _set_export_enabled(self, enabled: bool) -> None:
        for b in (self._json_btn, self._csv_btn, self._xlsx_btn):
            b.setEnabled(enabled)

    def _on_row_done(self, _index: int, result: RowResult) -> None:
        if self._preview_model is not None:
            self._preview_table.append_and_maybe_scroll(self._preview_model, result)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress.setRange(0, total)
        self._progress.setValue(done)

    def _on_sort_finished(self) -> None:
        self._cancel_btn.setEnabled(False)
        self._set_export_enabled(True)
        if self._preview_model is None:
            return
        results = self._preview_model.results()
        ok = sum(1 for r in results if r.ok)
        bad = len(results) - ok
        self.status_message.emit(f"Sort complete: {ok} ok, {bad} failed")

    def _on_sort_failed(self, msg: str) -> None:
        self._cancel_btn.setEnabled(False)
        QMessageBox.warning(self, "Sort failed", msg)

    def _on_cancel(self) -> None:
        if self._sort_worker is not None:
            self._sort_worker.cancel()
            self.status_message.emit("Cancelling…")

    def _on_export(self, fmt: str) -> None:
        if self._preview_model is None:
            return
        results = self._preview_model.results()
        bad = sum(1 for r in results if not r.ok)
        if bad:
            reply = QMessageBox.question(
                self,
                "Some rows failed",
                f"{bad} of {len(results)} rows had parse errors. Export anyway?",
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        ext_filter = {"json": "JSON (*.json)", "csv": "CSV (*.csv)", "xlsx": "Excel (*.xlsx)"}[fmt]
        path_str, _ = QFileDialog.getSaveFileName(self, "Export sorted data", f"sorted.{fmt}", ext_filter)
        if not path_str:
            return
        path = Path(path_str)

        try:
            include_status = bad > 0
            if fmt == "json":
                export_json(path, self._headers, results, include_status=include_status)
            elif fmt == "csv":
                export_csv(path, self._headers, results, include_status=include_status)
            else:
                export_xlsx(path, self._headers, results, include_status=include_status)
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
            return
        self.status_message.emit(f"Exported to {path.name}")
