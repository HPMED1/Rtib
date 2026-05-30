"""Command-line entry point.

`rtib` with no arguments opens the GUI. With `--input` and `--output` it runs
the same auto-mode pipeline headlessly, with a progress bar in the terminal.

Schema files (JSON) are forward-compatible with the template format the GUI
will save in a future slice:

    {
      "name": "Movie filenames",          # optional, ignored by CLI batch
      "hint": "movie filenames",          # optional, ignored when --schema used
      "headers": [
        {"name": "Title", "description": "..."},
        ...
      ]
    }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from rtib import __app_name__, __version__
from rtib.core.exporters import export_csv, export_json, export_xlsx
from rtib.core.ollama_client import OllamaClient, OllamaError
from rtib.core.pipeline import bulk_sort, sort_row, suggest_headers
from rtib.core.schema import Header
from rtib.core.settings import AppSettings
from rtib.core.splitting import SeparatorKind, split_input

_CONSOLE = Console(stderr=True)
_SUPPORTED_FORMATS = {".json", ".csv", ".xlsx"}


app = typer.Typer(
    name="rtib",
    help="Local-first AI sorter/formatter for messy unstructured text.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} {__version__}")
        raise typer.Exit()


@app.callback()
def root(
    ctx: typer.Context,
    input_path: Path | None = typer.Option(
        None, "--input", "-i", help="Path to messy input text file (one row per line)."
    ),
    output_path: Path | None = typer.Option(
        None, "--output", "-o", help="Path to write sorted output (.json, .csv, .xlsx)."
    ),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Ollama model tag for row sorting (overrides default)."
    ),
    hint: str | None = typer.Option(
        None, "--hint", "-H", help="Optional one-line description of the data (auto-mode only)."
    ),
    schema_path: Path | None = typer.Option(
        None, "--schema", "-s",
        help="Path to a schema JSON file with predefined headers (skips auto-suggestion).",
    ),
    save_schema_path: Path | None = typer.Option(
        None, "--save-schema",
        help="After auto-suggestion, save the headers to this file for reuse with --schema.",
    ),
    separator: str = typer.Option(
        "auto", "--separator",
        help="How to split the input into rows: auto | whole | newline | comma | semicolon | tab | pipe | <regex>. "
             "`whole` sends the entire input as one model call (bulk extraction).",
    ),
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit.",
        callback=_version_callback, is_eager=True,
    ),
) -> None:
    """Default: open the GUI. With --input/--output, run a batch job."""
    if ctx.invoked_subcommand is not None:
        return

    batch_mode = input_path is not None or output_path is not None
    if batch_mode:
        if input_path is None or output_path is None:
            _CONSOLE.print("[red]Batch mode requires both --input and --output.[/red]")
            raise typer.Exit(code=2)
        _run_batch(
            input_path=input_path,
            output_path=output_path,
            model=model,
            hint=hint,
            schema_path=schema_path,
            save_schema_path=save_schema_path,
            separator=separator,
        )
        return

    _run_gui()


def _run_gui() -> None:
    from rtib.gui.app import run_gui

    sys.exit(run_gui())


def gui_main() -> None:
    """Entry point for the windowed launcher (no console)."""
    _run_gui()


def main() -> None:
    app()


# ---------- Batch ----------

def _run_batch(
    *,
    input_path: Path,
    output_path: Path,
    model: str | None,
    hint: str | None,
    schema_path: Path | None,
    save_schema_path: Path | None,
    separator: str = "auto",
) -> None:
    settings = AppSettings()
    sort_model = model or settings.sort_model
    header_model = model or settings.auto_header_model

    if not input_path.is_file():
        _CONSOLE.print(f"[red]Input file not found:[/red] {input_path}")
        raise typer.Exit(code=2)

    ext = output_path.suffix.lower()
    if ext not in _SUPPORTED_FORMATS:
        _CONSOLE.print(
            f"[red]Unsupported output format[/red] '{ext}'. "
            f"Use one of: {', '.join(sorted(_SUPPORTED_FORMATS))}"
        )
        raise typer.Exit(code=2)

    rows, chosen, bulk_mode = _read_rows(input_path, separator)
    if not rows:
        _CONSOLE.print(f"[red]Input file is empty or unsplittable:[/red] {input_path}")
        raise typer.Exit(code=2)
    if bulk_mode:
        _CONSOLE.print(
            f"Read [green]{len(rows[0]):,} chars[/green] from "
            f"[cyan]{input_path.name}[/cyan] (bulk mode: model decides record count)"
        )
    else:
        _CONSOLE.print(
            f"Read [green]{len(rows)} rows[/green] from [cyan]{input_path.name}[/cyan] "
            f"(separator: {chosen})"
        )

    client = OllamaClient(settings.ollama_url, timeout_s=settings.request_timeout_s)
    if not client.health_check():
        _CONSOLE.print(
            f"[red]Ollama unreachable at {settings.ollama_url}[/red] — "
            f"is it running? (try `ollama serve`)"
        )
        raise typer.Exit(code=2)

    if schema_path is not None:
        headers = _load_schema(schema_path)
        _CONSOLE.print(f"Using {len(headers)} headers from [cyan]{schema_path}[/cyan]")
    else:
        headers = _auto_suggest(client, header_model, rows, hint, settings)
        if save_schema_path is not None:
            _save_schema(save_schema_path, headers, hint)
            _CONSOLE.print(f"Saved schema to [cyan]{save_schema_path}[/cyan]")

    if bulk_mode:
        results = _bulk_extract(client, sort_model, rows[0], headers)
    else:
        results = _sort_all(client, sort_model, rows, headers)

    bad = sum(1 for r in results if not r.ok)
    include_status = bad > 0
    _write_output(output_path, ext, headers, results, include_status=include_status)

    _CONSOLE.print()
    summary = f"[green]{len(results) - bad} OK[/green]"
    if bad:
        summary += f" / [red]{bad} failed[/red]"
    _CONSOLE.print(f"Done: {summary} -> [cyan]{output_path}[/cyan]")
    if include_status:
        _CONSOLE.print("(_status column added because some rows failed)")


_NAMED_SEPARATORS: dict[str, SeparatorKind] = {
    "auto": SeparatorKind.AUTO,
    "whole": SeparatorKind.WHOLE,
    "newline": SeparatorKind.NEWLINE,
    "comma": SeparatorKind.COMMA,
    "semicolon": SeparatorKind.SEMICOLON,
    "tab": SeparatorKind.TAB,
    "pipe": SeparatorKind.PIPE,
}


def _read_rows(path: Path, separator: str) -> tuple[list[str], str, bool]:
    """Read and split the input file.

    Returns (rows, label of separator used, bulk_mode flag).
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    sep_key = separator.lower().strip()
    if sep_key in _NAMED_SEPARATORS:
        kind = _NAMED_SEPARATORS[sep_key]
        result = split_input(text, kind)
    else:
        # Treat unknown values as a custom regex.
        result = split_input(text, SeparatorKind.REGEX, custom_pattern=separator)
    label = result.chosen.value if result.chosen != SeparatorKind.REGEX else f"regex {separator!r}"
    bulk_mode = result.chosen == SeparatorKind.WHOLE
    return result.rows, label, bulk_mode


def _load_schema(path: Path) -> list[Header]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _CONSOLE.print(f"[red]Could not read schema file {path}:[/red] {exc}")
        raise typer.Exit(code=2) from exc

    raw_headers = data.get("headers", []) if isinstance(data, dict) else []
    if not raw_headers:
        _CONSOLE.print(f"[red]Schema file has no `headers` array:[/red] {path}")
        raise typer.Exit(code=2)

    out: list[Header] = []
    for item in raw_headers:
        name = (item.get("name") or "").strip() if isinstance(item, dict) else ""
        if not name:
            continue
        desc = (item.get("description") or "").strip()
        out.append(Header(name=name, description=desc))
    if not out:
        _CONSOLE.print(f"[red]Schema file has no usable headers:[/red] {path}")
        raise typer.Exit(code=2)
    return out


def _save_schema(path: Path, headers: list[Header], hint: str | None) -> None:
    payload: dict[str, object] = {
        "headers": [{"name": h.name, "description": h.description} for h in headers],
    }
    if hint:
        payload["hint"] = hint
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _auto_suggest(
    client: OllamaClient,
    model: str,
    rows: list[str],
    hint: str | None,
    settings: AppSettings,
) -> list[Header]:
    sample = rows[: max(1, settings.auto_header_sample_rows)]
    _CONSOLE.print(
        f"Asking [cyan]{model}[/cyan] for headers "
        f"({len(sample)} sample row{'s' if len(sample) != 1 else ''}"
        + (f", hint: {hint!r}" if hint else "")
        + ")..."
    )
    try:
        headers = suggest_headers(client, model, sample, hint)
    except OllamaError as exc:
        _CONSOLE.print(f"[red]Header suggestion failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    if not headers:
        _CONSOLE.print("[red]Model returned no headers.[/red]")
        raise typer.Exit(code=1)

    _CONSOLE.print(f"Suggested {len(headers)} headers:")
    for h in headers:
        _CONSOLE.print(f"  • [bold]{h.name}[/bold] — {h.description}")
    return headers


def _bulk_extract(
    client: OllamaClient,
    model: str,
    text: str,
    headers: list[Header],
) -> list:
    """Bulk-mode CLI driver: indeterminate spinner for the one big call."""
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=_CONSOLE,
        transient=False,
    )
    with progress:
        task = progress.add_task(
            f"Bulk extracting with [cyan]{model}[/cyan]", total=None
        )
        results = bulk_sort(client, model, text, headers)
        progress.update(task, completed=1, total=1)
    bad = sum(1 for r in results if not r.ok)
    _CONSOLE.print(
        f"Model returned [green]{len(results) - bad}[/green] records"
        + (f" ([red]{bad} failed[/red])" if bad else "")
    )
    return results


def _sort_all(
    client: OllamaClient,
    model: str,
    rows: list[str],
    headers: list[Header],
) -> list:
    results = []
    progress = Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=_CONSOLE,
        transient=False,
    )
    with progress:
        task = progress.add_task(f"Sorting with [cyan]{model}[/cyan]", total=len(rows))
        for row in rows:
            result = sort_row(client, model, row, headers)
            results.append(result)
            preview = row if len(row) <= 60 else row[:57] + "..."
            status_tag = "[green]OK[/green]" if result.ok else "[red]ERR[/red]"
            progress.update(
                task,
                advance=1,
                description=f"{status_tag} {preview}",
            )
    return results


def _write_output(
    path: Path,
    ext: str,
    headers: list[Header],
    results: list,
    *,
    include_status: bool,
) -> None:
    if ext == ".json":
        export_json(path, headers, results, include_status=include_status)
    elif ext == ".csv":
        export_csv(path, headers, results, include_status=include_status)
    elif ext == ".xlsx":
        export_xlsx(path, headers, results, include_status=include_status)


if __name__ == "__main__":
    main()
