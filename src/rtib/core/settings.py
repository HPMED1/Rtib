"""Runtime defaults. User-overridable later via GUI settings panel."""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "granite4.1:3b"
DEFAULT_CHUNK_SIZE = 25
DEFAULT_REQUEST_TIMEOUT_S = 120.0


@dataclass(frozen=True)
class AppSettings:
    ollama_url: str = DEFAULT_OLLAMA_URL
    model: str = DEFAULT_MODEL
    chunk_size: int = DEFAULT_CHUNK_SIZE
    request_timeout_s: float = DEFAULT_REQUEST_TIMEOUT_S
