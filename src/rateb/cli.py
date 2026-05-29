"""Command-line entry point.

`rateb` with no arguments opens the GUI. Batch flags (`--input`, `--output`)
will be implemented when the formatter lands; for now they print a notice.
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer

from rateb import __app_name__, __version__

app = typer.Typer(
    name="rateb",
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
        None, "--input", "-i", help="Path to messy input text file (batch mode)."
    ),
    output_path: Path | None = typer.Option(
        None, "--output", "-o", help="Path to write sorted output (.json, .csv, .xlsx)."
    ),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Ollama model tag to use (overrides default)."
    ),
    hint: str | None = typer.Option(
        None, "--hint", "-h", help="Optional one-line description of what the data is."
    ),
    version: bool = typer.Option(
        False, "--version", "-V", help="Show version and exit.", callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Default: open the GUI. With --input/--output, run a batch job."""
    if ctx.invoked_subcommand is not None:
        return

    batch_mode = input_path is not None or output_path is not None
    if batch_mode:
        if input_path is None or output_path is None:
            typer.echo("Batch mode requires both --input and --output.", err=True)
            raise typer.Exit(code=2)
        _run_batch(input_path, output_path, model=model, hint=hint)
        return

    _run_gui()


def _run_gui() -> None:
    # Lazy import — keeps CLI startup fast and avoids loading PySide6
    # when the user only wants --help or --version.
    from rateb.gui.app import run_gui

    sys.exit(run_gui())


def _run_batch(
    input_path: Path,
    output_path: Path,
    *,
    model: str | None,
    hint: str | None,
) -> None:
    typer.echo("Batch mode is not implemented yet — opening GUI instead.", err=True)
    typer.echo(
        f"  (requested: input={input_path}, output={output_path}, model={model}, hint={hint!r})",
        err=True,
    )
    _run_gui()


def main() -> None:
    app()


def gui_main() -> None:
    """Entry point for the windowed launcher (no console)."""
    _run_gui()


if __name__ == "__main__":
    main()
