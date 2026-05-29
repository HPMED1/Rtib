"""File exporters for sorted rows.

Each exporter takes the headers, the row results, and a path. ``parse_error``
rows are kept; their fields are written as empty/null and the status column
marks them. Whether to include the ``_status`` column is the caller's choice.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from openpyxl import Workbook

from rtib.core.pipeline import RowResult
from rtib.core.schema import Header


def _row_to_dict(
    headers: list[Header],
    result: RowResult,
    include_status: bool,
    include_raw: bool,
) -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for h in headers:
        out[h.key] = result.values.get(h.key) if result.values else None
    if include_status:
        out["_status"] = "ok" if result.ok else "parse_error"
    if include_raw:
        out["_raw"] = result.raw
    return out


def export_json(
    path: Path,
    headers: list[Header],
    results: list[RowResult],
    *,
    include_status: bool = False,
    include_raw: bool = False,
) -> None:
    payload = [
        _row_to_dict(headers, r, include_status, include_raw) for r in results
    ]
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def export_csv(
    path: Path,
    headers: list[Header],
    results: list[RowResult],
    *,
    include_status: bool = False,
    include_raw: bool = False,
) -> None:
    fieldnames = [h.key for h in headers]
    if include_status:
        fieldnames.append("_status")
    if include_raw:
        fieldnames.append("_raw")
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow(_row_to_dict(headers, r, include_status, include_raw))


def export_xlsx(
    path: Path,
    headers: list[Header],
    results: list[RowResult],
    *,
    include_status: bool = False,
    include_raw: bool = False,
) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Rtib"

    header_row = [h.name for h in headers]
    if include_status:
        header_row.append("_status")
    if include_raw:
        header_row.append("_raw")
    ws.append(header_row)

    for r in results:
        if r.values is None:
            # openpyxl skips rows whose cells are all None, which would make
            # parse_error rows invisible in Excel. Use empty strings instead so
            # the row is persisted and the user can see (and fix) what failed.
            row: list = ["" for _ in headers]
        else:
            row = [r.values.get(h.key) for h in headers]
        if include_status:
            row.append("ok" if r.ok else "parse_error")
        if include_raw:
            row.append(r.raw)
        ws.append(row)

    wb.save(str(path))
