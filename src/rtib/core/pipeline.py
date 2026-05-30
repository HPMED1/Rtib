"""The two LLM-driven steps: header suggestion (one-shot) and row sorting.

Both go through ``OllamaClient.generate`` with a strict JSON schema. Kept
in one module because they share prompt-construction helpers and any
prompt-engineering tweak likely touches both.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from rtib.core.ollama_client import OllamaClient, OllamaError
from rtib.core.schema import (
    Header,
    bulk_records_schema,
    header_suggestion_schema,
    row_schema,
)

_HEADER_SUGGESTION_SYSTEM = """You are a data architect helping a user clean up messy unstructured text.

You are shown a small sample of rows and an optional one-line description of what the data is. Your job is to propose the **columns** (headers) the user should extract from this data — what fields a tidy CSV/JSON of this data would have.

Rules:
- Choose 3 to 10 headers, no more.
- Each header has a short ``name`` (1-3 words) and a one-sentence ``description`` explaining what value goes in that column.
- Prefer fields that are clearly present in the sample. It is OK to also suggest one or two reasonable derived columns (e.g. "decade" from a year) when the user's hint implies they want them.
- Output strictly matches the JSON schema you've been given.
"""


_ROW_SORT_SYSTEM = """You extract structured data from a single messy line of text.

You are given:
1. The list of headers (each with a description) that define the columns.
2. One raw input row.

Your job: return a JSON object with one key per header.

Rules:
- Extract directly when the value is present in the input.
- You MAY derive a value when it can be confidently computed from the input (e.g. uppercase a code, compose two parts).
- If you genuinely cannot determine a field from the input, set it to ``null``. Never invent values.
- Never copy a value into the wrong field.
- Output strictly matches the JSON schema you've been given.
"""


_BULK_SORT_SYSTEM = """You extract structured records from a chunk of unstructured text.

The text may contain MANY records separated by ANY mix of newlines, commas, semicolons, spaces, tabs, pipes, or other delimiters. Records may even appear on the same line.

For each distinct record you can identify, produce one JSON object matching the per-record schema. Put all of them into the ``records`` array.

Rules:
- Extract or derive each field for each record. Set a field to ``null`` if you genuinely can't determine it. Never invent values.
- Return EVERY distinct record you can find. Do not summarize, deduplicate semantically, or skip ones that look messy.
- Never copy a value into the wrong field of a record.
- Never repeat the same record twice.
- Output strictly matches the JSON schema you've been given.
"""


@dataclass
class RowResult:
    raw: str
    values: dict[str, str | None] | None  # None means parse_error
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.values is not None


def suggest_headers(
    client: OllamaClient,
    model: str,
    sample_rows: list[str],
    hint: str | None,
) -> list[Header]:
    """One-shot call. Returns the model's suggested headers."""
    hint_block = f"User's description of the data: {hint.strip()}\n\n" if hint else ""
    sample_block = "\n".join(sample_rows)
    prompt = (
        f"{hint_block}"
        f"Sample rows ({len(sample_rows)}):\n"
        f"---\n{sample_block}\n---\n\n"
        f"Propose the headers."
    )

    resp = client.generate(
        model=model,
        prompt=prompt,
        system=_HEADER_SUGGESTION_SYSTEM,
        schema=header_suggestion_schema(),
        options={"temperature": 0.2},
    )
    raw = resp.get("response", "")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise OllamaError(f"Header suggestion: model returned non-JSON: {exc}") from exc

    headers_raw = parsed.get("headers", [])
    out: list[Header] = []
    for item in headers_raw:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        desc = (item.get("description") or "").strip()
        out.append(Header(name=name, description=desc))
    return out


def sort_row(
    client: OllamaClient,
    model: str,
    row: str,
    headers: list[Header],
) -> RowResult:
    """Sort one row into the structured shape defined by ``headers``."""
    headers_block = "\n".join(
        f"- {h.key} ({h.name}): {h.description or 'no description'}"
        for h in headers
    )
    prompt = (
        f"Headers:\n{headers_block}\n\n"
        f"Input row:\n{row}\n\n"
        f"Return one JSON object that follows the schema."
    )

    try:
        resp = client.generate(
            model=model,
            prompt=prompt,
            system=_ROW_SORT_SYSTEM,
            schema=row_schema(headers),
            options={"temperature": 0.0},
        )
    except OllamaError as exc:
        return RowResult(raw=row, values=None, error=str(exc))

    raw_response = resp.get("response", "")
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return RowResult(raw=row, values=None, error=f"Invalid JSON: {exc}")

    values: dict[str, str | None] = {}
    for h in headers:
        v = parsed.get(h.key)
        if v is None or isinstance(v, str):
            values[h.key] = v
        else:
            # Schema should prevent this but be defensive.
            values[h.key] = str(v)
    return RowResult(raw=row, values=values)


def bulk_sort(
    client: OllamaClient,
    model: str,
    text: str,
    headers: list[Header],
) -> list[RowResult]:
    """One model call returning every record it finds in ``text``.

    Used when the input is too jumbled to split deterministically (mixed
    separators, multiple records per line, etc.). Returns one ``RowResult``
    per record. If the call itself failed, returns a single ``RowResult`` in
    parse-error state so the caller can show the user what went wrong.
    """
    headers_block = "\n".join(
        f"- {h.key} ({h.name}): {h.description or 'no description'}"
        for h in headers
    )
    prompt = (
        f"Headers:\n{headers_block}\n\n"
        f"Text:\n{text}\n\n"
        f"Find every distinct record in the text and return them under \"records\"."
    )

    try:
        resp = client.generate(
            model=model,
            prompt=prompt,
            system=_BULK_SORT_SYSTEM,
            schema=bulk_records_schema(headers),
            options={"temperature": 0.0},
        )
    except OllamaError as exc:
        return [RowResult(raw=text, values=None, error=str(exc))]

    raw_response = resp.get("response", "")
    try:
        parsed = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        return [RowResult(raw=text, values=None, error=f"Invalid JSON: {exc}")]

    records = parsed.get("records", [])
    if not isinstance(records, list):
        return [RowResult(raw=text, values=None, error="Expected an array under 'records'.")]

    results: list[RowResult] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        values: dict[str, str | None] = {}
        for h in headers:
            v = rec.get(h.key)
            if v is None or isinstance(v, str):
                values[h.key] = v
            else:
                values[h.key] = str(v)
        # We don't know which slice of the input produced each record, so leave
        # raw blank. The user knows it was bulk mode by context.
        results.append(RowResult(raw="", values=values))
    return results
