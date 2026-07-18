#!/usr/bin/env bash
# Build a standalone executable for Linux/macOS.
set -euo pipefail
cd "$(dirname "$0")"

python3 -m venv .buildenv
source .buildenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pyinstaller PatientManagement.spec --noconfirm

echo
echo "Build complete: dist/PatientManagement"
