
#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "=================================="
echo "       Pomodoro Timer Build"
echo "             macOS"
echo "=================================="

# Проверяем виртуальное окружение.
if [[ ! -x ".venv/bin/python" ]]; then
    echo "Error: .venv not found."
    echo "Create it with: python3 -m venv .venv"
    exit 1
fi

source .venv/bin/activate

# Устанавливаем зависимости проекта.
python -m pip install -r requirements.txt

# Проверяем наличие PyInstaller.
if ! python -c "import PyInstaller" >/dev/null 2>&1; then
    python -m pip install pyinstaller
fi

echo
echo "Python version:"
python --version

echo
echo "Architecture:"
python -c "import platform; print(platform.machine())"

echo
echo "Building PomodoroTimer.app..."

# Используем единую конфигурацию PyInstaller.
python -m PyInstaller \
    --noconfirm \
    --clean \
    PomodoroTimer.spec

echo
echo "=================================="
echo "Build complete!"
echo "Output: dist/PomodoroTimer.app"
echo "=================================="

open dist
