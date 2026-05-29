"""Thin Ollama HTTP client.

Only what the GUI skeleton needs right now: health check, list models, and a
schema-constrained generate() entry point that we'll flesh out when the
formatting flow lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class ModelInfo:
    name: str
    size_bytes: int
    modified_at: str


class OllamaError(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, timeout_s: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_s

    def health_check(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base_url}/api/version")
                return resp.status_code == 200
        except httpx.HTTPError:
            return False

    def version(self) -> str | None:
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(f"{self._base_url}/api/version")
                resp.raise_for_status()
                return resp.json().get("version")
        except httpx.HTTPError:
            return None

    def list_models(self) -> list[ModelInfo]:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{self._base_url}/api/tags")
            resp.raise_for_status()
            data = resp.json()
        models: list[ModelInfo] = []
        for entry in data.get("models", []):
            models.append(
                ModelInfo(
                    name=entry.get("name", ""),
                    size_bytes=int(entry.get("size", 0)),
                    modified_at=str(entry.get("modified_at", "")),
                )
            )
        return models

    def generate(
        self,
        model: str,
        prompt: str,
        *,
        schema: dict[str, Any] | None = None,
        system: str | None = None,
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Non-streaming generate. Returns the raw Ollama response dict.

        When ``schema`` is provided, Ollama constrains output to that JSON
        schema (Ollama 0.5+). Caller is responsible for parsing
        ``response["response"]`` as JSON.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if system is not None:
            payload["system"] = system
        if schema is not None:
            payload["format"] = schema
        if options is not None:
            payload["options"] = options

        with httpx.Client(timeout=self._timeout) as client:
            resp = client.post(f"{self._base_url}/api/generate", json=payload)
            if resp.status_code != 200:
                raise OllamaError(
                    f"Ollama generate failed ({resp.status_code}): {resp.text[:300]}"
                )
            return resp.json()
