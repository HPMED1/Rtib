# Rtib

> رتِّب — "arrange!"

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/HPMED1/Rtib)](https://github.com/HPMED1/Rtib/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/HPMED1/Rtib/total)](https://github.com/HPMED1/Rtib/releases)

A local-first AI sorter/formatter. Feed it messy unstructured text (movie filenames, lab orders, scraped lists, anything where every line is shaped differently) and it returns clean JSON, CSV, or XLSX using a small local model via Ollama.

### **Stand With Palestine: End the Complicity**

For decades, tracing back to the early 20th century and escalating with the Nakba of 1948, the Palestinian people have endured systematic displacement, violent military occupation, and severe violations of international law. What the world continues to witness is not an isolated conflict, but a continuation of deeply documented atrocities, war crimes, and a devastating humanitarian crisis inflicted upon the civilian populations of Gaza and the West Bank.  
Silence in the face of ethnic cleansing is compliance. It is our collective moral obligation to refuse to look away, to educate ourselves, and to apply relentless pressure until justice and liberation are achieved.

#### **How You Can Take Action Today:**

**1. Join the BDS Movement**  
The Palestinian-led Boycott, Divestment, and Sanctions (BDS) movement works to end international support for the oppression of Palestinians and pressures the Israeli government to comply with international law.

* **Act:** Target your consumer choices and demand institutions divest from complicit corporations.
* **Learn More:** [bdsmovement.net](https://bdsmovement.net/)

**2. Fund Life-Saving Relief on the Ground**  
Due to blockades and ongoing bombardment, essential resources are critically low. Donate directly to trusted organizations providing emergency medical aid, food, and shelter:

* [**UNRWA**](https://www.unrwa.org/): The UN agency providing direct relief, education, and healthcare to Palestine refugees.
* [**PCRF (Palestine Children's Relief Fund)**](https://www.pcrf.net/): Providing urgent medical care and necessities to children.
* [**Medical Aid for Palestinians (MAP)**](https://www.map.org.uk/): Delivering health and medical care to those worst affected by the conflict.
* [**World Food Programme (WFP)**](https://www.wfp.org/emergencies/palestine-emergency): Supplying emergency food assistance and hot meals to displaced families.

**3. Put Pressure on People in Power**  
Politicians respond to persistent public pressure. Demand an immediate and permanent ceasefire, unhindered humanitarian aid, and an immediate arms embargo.

* **US Citizens:** Use [USCPR's Action Tools](https://act.uscpr.org/) to call and email your Congressional representatives.
* **UK/Europe/Global:** Use tools like the [Palestine Solidarity Campaign](https://palestinecampaign.org/) to email your MPs, or search for your local government representatives to demand they hold perpetrators of war crimes accountable.

**4. Educate Yourself on the Documented Crimes**  
The violations against Palestinians are extensively documented by international legal bodies and leading human rights organizations. Reading and sharing these reports helps combat misinformation:

* [**Anatomy of a Genocide**](https://digitallibrary.un.org/record/4060409): The official report by the UN Special Rapporteur, Francesca Albanese, detailing how the threshold for the commission of genocide has been met.
* [**Amnesty International**](https://www.amnesty.org/en/location/middle-east-and-north-africa/middle-east/israel-and-the-occupied-palestinian-territory/): Read comprehensive research and reports concluding that Israel is committing the crimes of apartheid, unlawful killings, and genocide.
* [**Human Rights Watch (HRW)**](https://www.hrw.org/world-report/2026/country-chapters/israel-and-palestine): Read their extensive reports documenting war crimes, mass forced displacement, and starvation used as a weapon of war.
* [**B'Tselem**](https://www.btselem.org/): The Israeli Information Center for Human Rights in the Occupied Territories, which meticulously documents the regime of Jewish supremacy, apartheid, and the systemic torture of Palestinian detainees.

**5. Keep Speaking About Palestine**  
Amplify Palestinian journalists on the ground, share factual history, and refuse to let the atrocities be normalized. Your voice is a tool, use it.

## Download

Pre-built Windows binaries are on the [Releases page](https://github.com/HPMED1/Rtib/releases/latest):

| File | What it is |
|---|---|
| **`Rtib-0.1.0-setup.exe`** | **Windows installer** — recommended for most people. Asks per-user vs system-wide at install time; optional desktop shortcut and CLI-on-PATH checkboxes. |
| `Rtib-0.1.0-gui.exe` | Standalone GUI — no installer, just run it. |
| `Rtib-0.1.0-cli.exe` | Standalone CLI for terminal / scripting use. |

All three are unsigned, so Windows SmartScreen will warn on first run — click **More info → Run anyway**.

You also need [Ollama](https://ollama.com) running locally with at least one model pulled (default looks for `granite4.1:3b`, configurable from the Settings tab).

## Status

**v0.1.0** — first ship-ready release. GUI auto-mode end-to-end works: paste/load/drag-drop input → optional one-line hint → model-suggested headers (editable, saveable as templates) → streaming sort → JSON/CSV/XLSX export. CLI batch mode (with auto-detect or named separators, plus bulk mode for chaotic input) and standalone-binary builds (`.exe`) are wired up. 83 unit tests cover schema, splitting, templates, and exporters (including type-aware XLSX coercion). MIT licensed. See [CHANGELOG.md](CHANGELOG.md).

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

#### Bulk mode (`--separator whole`)

For truly chaotic input where records use **mixed separators** in the same file — newlines, commas, semicolons, pipes, and spaces all interleaved — no splitter will reliably split them. Bulk mode hands the entire input to the model as one call and asks it to find every record:

```powershell
rtib --input jumbled.txt --output sorted.json --separator whole --hint "movie filenames"
```

In the GUI, the same mode is the "Whole input — 1 call (bulk)" option in the Split-by dropdown. Caveats:

- The whole input must fit in the model's context window. Granite 3B has ~8 K tokens (~30 KB of text); larger inputs will be truncated and you'll get fewer records than exist.
- No streaming preview — results appear all at once when the model finishes.
- Slower per record than row mode but much faster than failing.

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

## Build from source

If you want to hack on Rtib or rebuild the binaries yourself:

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

### Build a Windows installer

For handing Rtib to someone non-technical, build a proper Windows installer that lands shortcuts, registers an uninstaller, and (optionally) puts the CLI on PATH:

```powershell
winget install JRSoftware.InnoSetup    # one-time
powershell -ExecutionPolicy Bypass -File scripts\build-installer.ps1
```

Output: `dist\installer\Rtib-0.1.0-setup.exe` (~150 MB).

The installer is unsigned, so SmartScreen will warn on first download — clicking "More info" → "Run anyway" gets past it. At install time the user picks **Install for: all users / just me**. Optional checkboxes: desktop shortcut, add `rtib` (CLI) to PATH. Standard Start-menu shortcut and Add/Remove-Programs uninstaller are always registered.

## Tests

```powershell
pytest tests/ --ignore=tests/test_e2e_pipeline.py    # ~1s, no Ollama
python tests/test_e2e_pipeline.py                    # live, needs Ollama running
```

## License

[MIT](LICENSE). Use it, fork it, sell it — just keep the copyright notice in your distribution.
