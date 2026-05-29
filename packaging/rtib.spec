# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the console CLI build (rtib.exe).

Run from the project root:
    pyinstaller packaging/rtib.spec
"""

import os

SPECPATH = os.path.dirname(os.path.abspath(SPEC))
PROJECT_ROOT = os.path.dirname(SPECPATH)
ICON_PATH = os.path.join(PROJECT_ROOT, "src", "rtib", "resources", "icons", "rtib.ico")


a = Analysis(
    [os.path.join(PROJECT_ROOT, "src", "rtib", "__main__.py")],
    pathex=[os.path.join(PROJECT_ROOT, "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="rtib",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI: keep the console attached
    disable_windowed_traceback=False,
    icon=ICON_PATH,
)
