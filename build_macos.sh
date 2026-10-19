#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 was not found. Install Python 3.10+ first."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller


python -m PyInstaller \
    --noconfirm \
    --clean \
    --windowed \
    --name PomodoroTimer \
    main.py


echo
echo "Build complete: dist/PomodoroTimer.app"
open dist
