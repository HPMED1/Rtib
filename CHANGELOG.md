# Changelog

All notable changes to Rtib are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **Windows installer** (`scripts\build-installer.ps1`) — Inno Setup script
  bundles both `.exe`s plus `LICENSE`, `README.md`, `CHANGELOG.md`.
  Per-user vs system-wide install chosen at install time. Optional desktop
  shortcut and "add CLI to PATH" checkboxes. Standard Start-menu shortcut
  and Add/Remove-Programs uninstaller are always registered. Clean
  uninstall removes the PATH entry it added. Output:
  `dist\installer\Rtib-<version>-setup.exe` (~150 MB).

## [0.1.0] — 2026-05-30

First "ship-ready" release. The app handles the full flow end-to-end in both
GUI and CLI, has unit tests, builds as a standalone `.exe`, and ships under
MIT.

### Added

- **Auto-mode end-to-end** — paste/load/drag-drop input → optional one-line
  hint → model-suggested headers (editable) → streaming sort → JSON/CSV/XLSX
  export.
- **Manual mode** — "Enter headers manually" path on the input page lets you
  define the schema without calling the model.
- **CLI batch mode** — `rtib --input X --output Y` runs the full pipeline
  headlessly with a `rich`-style progress bar. Flags: `--schema`,
  `--save-schema`, `--hint`, `--model`, `--separator`.
- **Templates** — save the current headers (with the hint that suggested
  them) as a named template; reload from a dropdown menu on the input page.
  Same JSON file format as the CLI `--schema` flag, so templates are portable
  between GUI and CLI.
- **Multi-separator input** — Auto-detect, or pick from
  newline/comma/semicolon/tab/pipe/custom-regex. Auto prefers newline when it
  yields ≥2 rows (newlines are the most reliable signal), falls through to
  the rest for single-line input.
- **Bulk mode** (`--separator whole` / "Whole input — 1 call" in the GUI) —
  hand the entire input to the model as one call when records use mixed
  separators or share lines. Model finds every distinct record and returns
  them in one array.
- **Theme + window persistence** — dark/light choice and window geometry
  survive across launches.
- **Drag-drop visual feedback** — central widget gets a dashed blue outline
  and the status bar reads "Drop to load as input" while a valid drag is over
  the window.
- **App icon** in title bar, taskbar, and Explorer. Generated programmatically
  via Pillow.
- **Standalone .exe builds** via PyInstaller:
  `dist/Rtib.exe` (GUI, windowed) and `dist/cli/rtib.exe` (CLI, console).
  PowerShell + bash build scripts. Windows desktop-shortcut installer.
- **Type-aware XLSX export** — year columns write as integers, dates as
  Excel dates, floats as floats, leaving genuinely-string values
  (filenames, "1080p", phone numbers) untouched.
- **70 unit tests** covering schema construction, slugify edge cases, JSON/
  CSV/XLSX exporters (including the type coercion), templates, and the
  input splitter.
- **MIT License**.

### Fixed

- **Header suggestion auto-cancel** — `QProgressDialog.close()` synchronously
  emits `canceled`, which used to re-enter the cancel handler and crash the
  success path. The user would see the busy modal flash and the status bar
  read "Header suggestion cancelled" with no headers shown.
- **XLSX parse_error rows silently dropped** — openpyxl skips rows whose
  cells are all `None`; we now write empty strings on failed rows so they
  stay visible in the spreadsheet.

## [0.0.1] — 2026-05-29

### Added

- Initial PySide6 GUI skeleton with light/dark themes, Ollama health check
  in the status bar, and a populated model dropdown.
- Project scaffold: `pyproject.toml`, `src/rtib/` package layout,
  `rtib`/`rtib-gui` entry points, `.gitignore`, README.
- `OllamaClient`: health check, list models, schema-constrained generate.
