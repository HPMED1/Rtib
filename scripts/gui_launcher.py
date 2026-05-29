"""Entry script for the windowed Rtib build.

PyInstaller needs a script (not an entry point name) to bundle. This file
exists only to give the windowed build a clean, CLI-arg-free entry point.
"""

from __future__ import annotations

from rtib.cli import gui_main


if __name__ == "__main__":
    gui_main()
