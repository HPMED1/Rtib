"""Headers, header validation, and JSON-schema builders for Ollama.

A Header is just a name + optional description. The schema we hand to
Ollama uses the header *name* as the JSON key, so names must be valid
identifiers (slug-style). Descriptions ride along for the model's context
but never become JSON keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


_SLUG_RE = re.compile(r"[^a-z0-9_]+")


def slugify(name: str) -> str:
    """Normalize a free-text header name into a JSON-key-safe slug."""
    s = name.strip().lower().replace("-", "_").replace(" ", "_")
    s = _SLUG_RE.sub("", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "field"


@dataclass
class Header:
    name: str  # display name as the user wrote it (e.g. "Release Year")
    description: str = ""  # optional one-line description for the model

    @property
    def key(self) -> str:
        return slugify(self.name)


def row_schema(headers: list[Header]) -> dict[str, Any]:
    """Build the JSON schema for a single sorted row.

    Every field is `string | null` — nullability is how we let the model
    say "I don't know this" instead of fabricating.
    """
    properties: dict[str, Any] = {}
    required: list[str] = []
    for h in headers:
        prop: dict[str, Any] = {"type": ["string", "null"]}
        if h.description:
            prop["description"] = h.description
        properties[h.key] = prop
        required.append(h.key)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def header_suggestion_schema() -> dict[str, Any]:
    """Schema for the auto-mode header suggestion call.

    Asks the model for a list of {name, description} pairs.
    """
    return {
        "type": "object",
        "properties": {
            "headers": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["name", "description"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["headers"],
        "additionalProperties": False,
    }
