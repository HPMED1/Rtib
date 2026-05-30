# Rtib

> رتِّب — "arrange!"

A local-first AI sorter/formatter. Feed it messy unstructured text (movie filenames, lab orders, scraped lists, anything where every line is shaped differently) and it returns clean JSON, CSV, or XLSX using a small local model via Ollama.

## Status

Functional. GUI auto-mode end-to-end works: paste/load/drag-drop input → optional one-line hint → model-suggested headers (editable, saveable as templates) → streaming sort → JSON/CSV/XLSX export. CLI batch mode and standalone-binary builds (`.exe`) are wired up. 41 unit tests cover schema/templates/exporters.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with at least one model pulled
- ~3 GB free VRAM recommended (or CPU mode, slower)

## Install (dev)

```powershell
pip install -e .
```

This registers the `rtib` command.

## Usage

### GUI

```powershell
rtib                       # opens the GUI
```

The window has two tabs:

- **Sort** — paste or load your messy text, optionally describe what it is, review/edit the headers the model suggests, then sort. Failed rows are highlighted red; you can fix any cell before exporting.
- **Settings** — point Rtib at your Ollama, pick a default sort model, and (separately) pick the model + sample size used for the one-shot auto-header suggestion.

### CLI batch mode

Auto-suggest headers and sort to JSON:

```powershell
rtib --input movies.txt --output sorted.json --hint "movie filenames"
```

Save the auto-suggested headers as a schema file you can reuse later (skips the suggestion call next time):

```powershell
rtib --input movies.txt --output sorted.json --hint "movie filenames" `
     --save-schema movies.schema.json
```

Sort using a saved schema (no auto-suggestion, faster):

```powershell
rtib --input movies.txt --output sorted.csv  --schema movies.schema.json
rtib --input movies.txt --output sorted.xlsx --schema movies.schema.json
```

Override the model for a single run:

```powershell
rtib --input movies.txt --output sorted.json --model qwen3:4b --hint "movies"
```

Output format is detected from the file extension (`.json`, `.csv`, `.xlsx`). The CLI always exits 0 on a completed run; if any rows failed to parse, a `_status` column is added to the output so you can filter them.

### Input row separator

Rtib doesn't assume your data is one-row-per-line. By default it **auto-detects** the separator (newlines, commas, semicolons, tabs, pipes). If your file has 200 comma-separated movie titles on a single line, Auto picks `comma` and you get 200 rows; if it's one record per line, Auto picks `newline`.

The GUI has a **Split by** dropdown above the row count that shows the detected choice. The CLI has `--separator`:

```powershell
rtib --input contacts.txt --output sorted.csv --separator semicolon
rtib --input dump.txt     --output sorted.csv --separator tab
rtib --input flat.txt     --output sorted.csv --separator "\s{2,}"        # custom regex
rtib --input phones.txt   --output sorted.csv --separator "(?<=\d{4})\s+" # split after 4-digit numbers
```

Anything that isn't one of the named separators is treated as a regex pattern, so you can handle awkward cases where commas live inside fields or records are separated by something exotic.

### Schema file format

A minimal forward-compatible JSON file:

```json
{
  "headers": [
    {"name": "Title", "description": "The movie title."},
    {"name": "Year", "description": "Release year."}
  ],
  "hint": "movie filenames from torrent sites"
}
```

Only `headers` is required. `hint` and other future fields are ignored by the CLI when used with `--schema`.

The GUI's **Templates** dropdown is backed by exactly this file format. Templates live in your user app data dir (e.g. `%APPDATA%\Rtib\Rtib\templates\*.json` on Windows) so they're shared between GUI and CLI runs.

## Build a standalone .exe

For sharing with someone who doesn't have Python:

```powershell
pip install -e .[dev]                                # gets PyInstaller + Pillow
python scripts/generate-icon.py                      # one-time; produces the .ico
powershell -ExecutionPolicy Bypass -File scripts/build-dist.ps1
```

Produces two single-file executables in `dist/`:

- **`dist/Rtib.exe`** — the GUI app. Double-click to launch. No console window.
- **`dist/cli/rtib.exe`** — the CLI. Add `dist/cli/` to PATH if you want `rtib --input X --output Y` from anywhere.

Build script is also available for macOS/Linux:

```bash
bash scripts/build-dist.sh
```

To put an `Rtib` shortcut on your desktop:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-shortcut.ps1
```

Each `.exe` is around 75 MB (Qt is the bulk). First launch is slower than subsequent ones because the one-file binary unpacks to temp.

## Tests

```powershell
pytest tests/ --ignore=tests/test_e2e_pipeline.py    # ~1s, no Ollama
python tests/test_e2e_pipeline.py                    # live, needs Ollama running
```

## License

TBD.
