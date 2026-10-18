@echo off
setlocal

cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python launcher ^(py^) was not found. Install Python 3.10+ and enable Add Python to PATH.
    pause
    exit /b 1
)

py -3 -m venv .venv
if errorlevel 1 goto :error

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
if errorlevel 1 goto :error
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

python -m PyInstaller --noconfirm --clean --onefile --windowed --name PomodoroTimer --collect-all PySide6 main.py
if errorlevel 1 goto :error

echo.
echo Build complete: dist\PomodoroTimer.exe
start "" "%CD%\dist"
pause
exit /b 0

:error
echo.
echo Build failed. Review the error above.
pause
exit /b 1
