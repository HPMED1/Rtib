"""End-to-end pipeline test against a live Ollama.

Runs: header suggestion -> row sort for every line -> all three exporters.
Slow (~30-60s on a 3B model). Marked as 'live' so it can be excluded.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from rtib.core.exporters import export_csv, export_json, export_xlsx
from rtib.core.ollama_client import OllamaClient
from rtib.core.pipeline import sort_row, suggest_headers
from rtib.core.settings import AppSettings


def main() -> int:
    settings = AppSettings()
    client = OllamaClient(settings.ollama_url, timeout_s=settings.request_timeout_s)
    if not client.health_check():
        print("Ollama unreachable; skipping live test.", file=sys.stderr)
        return 1

    sample_path = Path(__file__).resolve().parent.parent / "sample-data" / "movies.txt"
    rows = [line.strip() for line in sample_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"Loaded {len(rows)} rows from {sample_path.name}")

    print(f"\n[1] Suggesting headers via {settings.auto_header_model}...")
    headers = suggest_headers(
        client=client,
        model=settings.auto_header_model,
        sample_rows=rows[: settings.auto_header_sample_rows],
        hint="movie filenames from various release groups",
    )
    print(f"  Got {len(headers)} headers:")
    for h in headers:
        print(f"    - {h.key} ({h.name}): {h.description}")

    print(f"\n[2] Sorting {len(rows)} rows via {settings.sort_model}...")
    results = []
    for i, row in enumerate(rows):
        result = sort_row(client, settings.sort_model, row, headers)
        status = "OK" if result.ok else f"ERR: {result.error}"
        print(f"  [{i + 1:>2}] {status}  {row[:60]}")
        if result.ok:
            for h in headers:
                v = result.values.get(h.key)
                print(f"        {h.key:<20} = {v!r}")
        results.append(result)

    ok = sum(1 for r in results if r.ok)
    print(f"\n  Summary: {ok}/{len(results)} rows succeeded")

    print("\n[3] Exporting to all three formats...")
    out_dir = Path(tempfile.mkdtemp(prefix="rtib_e2e_"))
    json_path = out_dir / "out.json"
    csv_path = out_dir / "out.csv"
    xlsx_path = out_dir / "out.xlsx"
    export_json(json_path, headers, results, include_status=True)
    export_csv(csv_path, headers, results, include_status=True)
    export_xlsx(xlsx_path, headers, results, include_status=True)
    print(f"  Files in {out_dir}:")
    for p in (json_path, csv_path, xlsx_path):
        print(f"    {p.name}  ({p.stat().st_size} bytes)")

    print("\n[4] JSON preview:")
    print(json.dumps(json.loads(json_path.read_text(encoding="utf-8"))[:2], indent=2, ensure_ascii=False))

    return 0 if ok > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
