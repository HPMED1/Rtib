# Rtib

> رتِّب — "arrange!"

A local-first AI sorter/formatter. Feed it messy unstructured text (movie filenames, lab orders, scraped lists, anything where every line is shaped differently) and it returns clean JSON, CSV, or XLSX using a small local model via Ollama.

## Status

Functional. GUI auto-mode end-to-end works: paste/load/drag-drop input → optional one-line hint → model-suggested headers (editable) → streaming sort → JSON/CSV/XLSX export. CLI batch mode is wired up. Distribution as a standalone .exe is not built yet.

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

## License

TBD.
