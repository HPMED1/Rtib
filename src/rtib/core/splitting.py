"""Split arbitrary text into individual rows.

Most messy inputs are line-per-row, but plenty aren't: comma-separated lists,
semicolon-separated phone exports, tab-separated dumps from spreadsheets,
even single-line pipe-separated logs. The user picks a separator (or lets
Auto choose), and we hand a clean list of rows to the rest of the pipeline.

Auto picks the candidate that yields the most items of reasonable length —
it can't handle the truly ambiguous "everything separated by single spaces"
case (e.g. contacts with first-and-last names where spaces appear both
inside and between records), but it gets the common cases right without
needing the user to think.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class SeparatorKind(StrEnum):
    AUTO = "auto"
    WHOLE = "whole"  # send the entire input as one chunk; the model finds records
    NEWLINE = "newline"
    COMMA = "comma"
    SEMICOLON = "semicolon"
    TAB = "tab"
    PIPE = "pipe"
    REGEX = "regex"  # user supplies a regex pattern as ``custom_pattern``


# Maps each named splitter to a regex that lets us share one code path.
_NAMED_PATTERNS: dict[SeparatorKind, str] = {
    SeparatorKind.NEWLINE: r"\r?\n",
    SeparatorKind.COMMA: r",",
    SeparatorKind.SEMICOLON: r";",
    SeparatorKind.TAB: r"\t",
    SeparatorKind.PIPE: r"\|",
}

# Order matters for Auto: newline first because most inputs are line-per-row.
_AUTO_CANDIDATES: list[SeparatorKind] = [
    SeparatorKind.NEWLINE,
    SeparatorKind.SEMICOLON,
    SeparatorKind.TAB,
    SeparatorKind.PIPE,
    SeparatorKind.COMMA,  # commas last because they appear inside content a lot
]


@dataclass(frozen=True)
class SplitResult:
    rows: list[str]
    chosen: SeparatorKind  # which separator was actually used


def split_input(
    text: str,
    separator: SeparatorKind = SeparatorKind.AUTO,
    custom_pattern: str | None = None,
) -> SplitResult:
    """Split ``text`` into rows using the named (or auto-detected) separator.

    ``custom_pattern`` is only consulted when ``separator == REGEX``.

    ``WHOLE`` means "don't split"; we hand the entire (stripped) text back as
    a single item. The caller is expected to route that single item through
    the bulk-extraction pipeline rather than treating it as one row.
    """
    if separator == SeparatorKind.WHOLE:
        stripped = (text or "").strip()
        return SplitResult(
            rows=[stripped] if stripped else [],
            chosen=SeparatorKind.WHOLE,
        )

    if separator == SeparatorKind.REGEX:
        pattern = (custom_pattern or "").strip()
        if not pattern:
            return SplitResult(rows=[], chosen=SeparatorKind.REGEX)
        try:
            rows = _split_with_pattern(text, pattern)
        except re.error:
            return SplitResult(rows=[], chosen=SeparatorKind.REGEX)
        return SplitResult(rows=rows, chosen=SeparatorKind.REGEX)

    if separator == SeparatorKind.AUTO:
        return _auto_split(text)

    pattern = _NAMED_PATTERNS[separator]
    return SplitResult(rows=_split_with_pattern(text, pattern), chosen=separator)


def _split_with_pattern(text: str, pattern: str) -> list[str]:
    parts = re.split(pattern, text)
    return [p.strip() for p in parts if p.strip()]


def _auto_split(text: str) -> SplitResult:
    """Detect the most likely row separator.

    Strong rule first: if newlines yield two or more rows, that's the row
    separator. Newlines are the most reliable signal we have — commas
    routinely appear *inside* row content ("Romeo, Juliet, 1996"), so we
    only consider non-newline separators when the whole input is one line.

    For single-line input, try each named candidate and pick the one that
    yields the most clean items (>= 3 chars after stripping). Ties favour
    the order in ``_AUTO_CANDIDATES``.
    """
    text = text or ""

    # Strong preference: newline if it yields multiple rows.
    newline_rows = _split_with_pattern(text, _NAMED_PATTERNS[SeparatorKind.NEWLINE])
    if len(newline_rows) >= 2:
        return SplitResult(rows=newline_rows, chosen=SeparatorKind.NEWLINE)

    # Single-line input: try non-newline candidates.
    best: tuple[int, SeparatorKind, list[str]] | None = None
    for kind in _AUTO_CANDIDATES:
        if kind == SeparatorKind.NEWLINE:
            continue
        rows = _split_with_pattern(text, _NAMED_PATTERNS[kind])
        if len(rows) < 2:
            continue
        clean_items = [r for r in rows if len(r) >= 3]
        score = len(clean_items)
        if score == 0:
            continue
        if best is None or score > best[0]:
            best = (score, kind, rows)

    if best is None:
        stripped = text.strip()
        return SplitResult(
            rows=[stripped] if stripped else [],
            chosen=SeparatorKind.NEWLINE,
        )
    return SplitResult(rows=best[2], chosen=best[1])
