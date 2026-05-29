"""Editable list of headers shown after suggestion (or in manual mode).

Each header is a row: name field, description field, remove button.
Last row is a '+ Add header' affordance. Emits ``changed`` whenever the
list mutates.
"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from rtib.core.schema import Header


class _HeaderRow(QWidget):
    removed = Signal(object)  # self
    changed = Signal()

    def __init__(self, header: Header, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._name = QLineEdit(header.name)
        self._name.setPlaceholderText("Header name")
        self._name.setMinimumWidth(140)
        self._name.setMaximumWidth(220)
        self._name.textChanged.connect(self.changed.emit)

        self._desc = QLineEdit(header.description)
        self._desc.setPlaceholderText("What goes in this field (optional)")
        self._desc.textChanged.connect(self.changed.emit)

        remove_btn = QPushButton("✕")
        remove_btn.setFixedWidth(32)
        remove_btn.setToolTip("Remove this header")
        remove_btn.clicked.connect(lambda: self.removed.emit(self))

        layout.addWidget(self._name)
        layout.addWidget(self._desc, 1)
        layout.addWidget(remove_btn)

    @property
    def header(self) -> Header:
        return Header(name=self._name.text().strip(), description=self._desc.text().strip())


class HeadersPanel(QWidget):
    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._rows_holder = QWidget()
        self._rows_layout = QVBoxLayout(self._rows_holder)
        self._rows_layout.setContentsMargins(0, 0, 0, 0)
        self._rows_layout.setSpacing(6)
        self._rows_layout.addStretch(1)
        scroll.setWidget(self._rows_holder)
        outer.addWidget(scroll, 1)

        add_btn = QPushButton("+ Add header")
        add_btn.clicked.connect(self._add_blank)
        outer.addWidget(add_btn)

        self._row_widgets: list[_HeaderRow] = []

    def set_headers(self, headers: list[Header]) -> None:
        for w in list(self._row_widgets):
            self._remove_row_widget(w)
        for h in headers:
            self._append_row(h)
        self.changed.emit()

    def headers(self) -> list[Header]:
        out: list[Header] = []
        for w in self._row_widgets:
            h = w.header
            if h.name:
                out.append(h)
        return out

    def _add_blank(self) -> None:
        self._append_row(Header(name="", description=""))
        self.changed.emit()

    def _append_row(self, header: Header) -> None:
        row = _HeaderRow(header)
        row.removed.connect(self._remove_row_widget)
        row.changed.connect(self.changed.emit)
        # insert before the stretch
        self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)
        self._row_widgets.append(row)

    def _remove_row_widget(self, row: _HeaderRow) -> None:
        if row not in self._row_widgets:
            return
        self._row_widgets.remove(row)
        self._rows_layout.removeWidget(row)
        row.deleteLater()
        self.changed.emit()
