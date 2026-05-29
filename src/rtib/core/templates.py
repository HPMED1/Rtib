"""Named header templates persisted as JSON in the user's app data dir.

A template is just a saved schema (headers + optional hint). The file
format is the same one the CLI's ``--schema`` flag accepts, so a template
can be exported, version-controlled, or passed to ``rtib`` directly:

    {
      "name": "Movie filenames",
      "hint": "movie filenames from torrent sites",
      "headers": [
        {"name": "Title", "description": "..."},
        ...
      ]
    }

Filenames are slugified for filesystem safety; the display ``name`` inside
the JSON is what the GUI shows.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QStandardPaths

from rtib.core.schema import Header, slugify


@dataclass(frozen=True)
class Template:
    name: str
    headers: list[Header] = field(default_factory=list)
    hint: str | None = None
    path: Path | None = None


def templates_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
    if not base:
        # Fallback if QApplication isn't initialised (e.g. unit tests).
        base = str(Path.home() / ".rtib")
    path = Path(base) / "templates"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path_for(name: str) -> Path:
    slug = slugify(name)
    return templates_dir() / f"{slug}.json"


def _from_json(data: dict, path: Path | None) -> Template | None:
    name = (data.get("name") or "").strip() if isinstance(data, dict) else ""
    if not name and path is not None:
        name = path.stem
    if not name:
        return None
    headers_raw = data.get("headers", []) if isinstance(data, dict) else []
    headers: list[Header] = []
    for item in headers_raw:
        if not isinstance(item, dict):
            continue
        h_name = (item.get("name") or "").strip()
        if not h_name:
            continue
        headers.append(Header(name=h_name, description=(item.get("description") or "").strip()))
    hint = (data.get("hint") or "").strip() or None
    return Template(name=name, headers=headers, hint=hint, path=path)


def list_templates() -> list[Template]:
    out: list[Template] = []
    for f in sorted(templates_dir().glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        t = _from_json(data, f)
        if t is not None:
            out.append(t)
    return out


def load_template(name: str) -> Template | None:
    path = _path_for(name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return _from_json(data, path)


def save_template(name: str, headers: list[Header], hint: str | None = None) -> Template:
    cleaned_headers = [h for h in headers if h.name]
    payload: dict[str, object] = {
        "name": name,
        "headers": [
            {"name": h.name, "description": h.description} for h in cleaned_headers
        ],
    }
    if hint:
        payload["hint"] = hint
    path = _path_for(name)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return Template(name=name, headers=cleaned_headers, hint=hint, path=path)


def delete_template(name: str) -> bool:
    path = _path_for(name)
    if not path.exists():
        return False
    path.unlink()
    return True


def template_exists(name: str) -> bool:
    return _path_for(name).exists()
