#!/usr/bin/env bash
# Build both Rtib executables on macOS or Linux.
#
# Usage:
#     bash scripts/build-dist.sh
#
# Output:
#     dist/rtib   (CLI)
#     dist/Rtib   (GUI)

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v pyinstaller >/dev/null 2>&1; then
    echo "PyInstaller not found. Install dev deps: pip install -e .[dev]" >&2
    exit 1
fi

echo "Building dist/cli/rtib (CLI)..."
pyinstaller --noconfirm --distpath dist/cli packaging/rtib.spec

echo
echo "Building dist/Rtib (GUI)..."
pyinstaller --noconfirm packaging/rtib-gui.spec

echo
echo "Done. Artifacts:"
find dist -type f -maxdepth 2 \( -name "rtib*" -o -name "Rtib*" \) -exec ls -lh {} \;
