"""Locate the bundled application icon.

Works in three contexts:
- Dev install (``pip install -e .``): icon lives next to the package source.
- PyInstaller one-file build: extracted to ``sys._MEIPASS`` at startup.
- PyInstaller one-folder build: the spec puts it at ``sys._MEIPASS`` too.
"""

from __future__ import annotations

import sys
from pathlib import Path


def resolve_icon_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "rtib" / "resources" / "icons" / "rtib.ico"
    # src/rtib/gui/icon.py -> src/rtib/resources/icons/rtib.ico
    return Path(__file__).resolve().parent.parent / "resources" / "icons" / "rtib.ico"
