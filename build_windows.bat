@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    py -3 -m venv .venv
    if errorlevel 1 goto error
)

set "PYTHON=.venv\Scripts\python.exe"

"%PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto error

"%PYTHON%" -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto error

"%PYTHON%" -m PyInstaller --noconfirm --clean --distpath dist --workpath build PomodoroTimer_Windows.spec
if errorlevel 1 goto error

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
