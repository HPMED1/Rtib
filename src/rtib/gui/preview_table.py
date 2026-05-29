"""Streaming, editable table of sorted rows.

Rows arrive one at a time from ``SortWorker``. ``parse_error`` rows are
highlighted red. The user can double-click any cell to fix or fill in a
value before exporting.
"""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QHeaderView, QTableView

from rtib.core.pipeline import RowResult
from rtib.core.schema import Header

_RED_BG = QColor(220, 38, 38, 64)


class PreviewModel(QAbstractTableModel):
    def __init__(self, headers: list[Header]) -> None:
        super().__init__()
        self._headers = list(headers)
        self._rows: list[RowResult] = []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._headers)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        result = self._rows[index.row()]
        header = self._headers[index.column()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if result.values is None:
                return ""
            v = result.values.get(header.key)
            return "" if v is None else v
        if role == Qt.ItemDataRole.BackgroundRole and not result.ok:
            return _RED_BG
        if role == Qt.ItemDataRole.ToolTipRole:
            if not result.ok:
                return f"parse_error: {result.error or 'unknown'}\nraw: {result.raw}"
            return result.raw
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role != Qt.ItemDataRole.EditRole or not index.isValid():
            return False
        result = self._rows[index.row()]
        header = self._headers[index.column()]
        # Editing a parse_error cell promotes the row to ok with that one value.
        if result.values is None:
            result = RowResult(raw=result.raw, values={h.key: None for h in self._headers})
            self._rows[index.row()] = result
        new_value = str(value) if value not in ("", None) else None
        result.values[header.key] = new_value
        # Whole row may have flipped status — refresh every cell's background.
        left = self.index(index.row(), 0)
        right = self.index(index.row(), self.columnCount() - 1)
        self.dataChanged.emit(left, right, [role, Qt.ItemDataRole.BackgroundRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsEditable
        )

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section].name
        return section + 1

    def append_result(self, result: RowResult) -> None:
        row_index = len(self._rows)
        self.beginInsertRows(QModelIndex(), row_index, row_index)
        self._rows.append(result)
        self.endInsertRows()

    def results(self) -> list[RowResult]:
        return list(self._rows)

    def clear(self) -> None:
        if not self._rows:
            return
        self.beginResetModel()
        self._rows = []
        self.endResetModel()


class PreviewTable(QTableView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectItems)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(True)
        self.verticalHeader().setDefaultSectionSize(22)
        self._auto_scroll = True

    def set_model_with(self, headers: list[Header]) -> PreviewModel:
        model = PreviewModel(headers)
        self.setModel(model)
        return model

    def append_and_maybe_scroll(self, model: PreviewModel, result: RowResult) -> None:
        model.append_result(result)
        if self._auto_scroll:
            self.scrollToBottom()

    def set_auto_scroll(self, enabled: bool) -> None:
        self._auto_scroll = enabled
