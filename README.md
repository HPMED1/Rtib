# Rateb

> رتب — "arrange"

A local-first AI sorter/formatter. Feed it messy unstructured text (movie filenames, lab orders, scraped lists, anything where every line is shaped differently) and it returns clean JSON, CSV, or XLSX using a small local model via Ollama.

## Status

Skeleton stage. The GUI launches, lists installed Ollama models, and shows backend health. End-to-end sort/format flow is not implemented yet.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with at least one model pulled
- ~3 GB free VRAM recommended (or CPU mode, slower)

## Install (dev)

```powershell
pip install -e .
```

This registers the `rateb` command.

## Usage

```powershell
rateb                       # opens the GUI
rateb --help                # CLI usage
```

CLI batch mode (planned, not implemented yet):

```powershell
rateb --input unsorted.txt --output sorted.json
rateb --input unsorted.txt --output sorted.csv  --model granite4.1:3b
rateb --input unsorted.txt --output sorted.xlsx --hint "movie filenames"
```

## License

TBD.
