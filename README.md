# Pomodoro Timer

A small cross-platform Pomodoro desktop app built with Python and PySide6 for Windows and macOS.

## MVP features

- 25-minute focus sessions
- 5-minute short breaks
- 15-minute long break after every 4 completed focus sessions
- Start, pause, resume, and reset
- Session counter
- Dark, minimal desktop interface
- Countdown based on a monotonic clock to avoid accumulating timing drift

## Requirements

- Python 3.10+
- pip

## Run from source

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS**
```bash
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r requirements.txt
python main.py
```

## Build for Windows

On Windows, double-click `build_windows.bat`. The resulting executable is `dist/PomodoroTimer.exe`.

## Build for macOS

On a Mac, run from Terminal:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

The resulting application bundle is `dist/PomodoroTimer.app`.

The macOS build produced by this project is unsigned and not notarized. macOS may show a security warning when opening it. Public distribution should use code signing and notarization.

## Build both platforms on GitHub

The GitHub Actions workflow at `.github/workflows/build-desktop.yml` builds the Windows and macOS versions on their respective runners.

1. Push the project to GitHub.
2. Open **Actions** and run **Build Desktop Apps** to build test artifacts.
3. Download `PomodoroTimer-Windows` or `PomodoroTimer-macOS` from the completed workflow run.

To create a GitHub Release with both packaged builds attached, push a version tag:

```bash
git tag v0.2.0
git push origin v0.2.0
```

The workflow builds both platforms and attaches `PomodoroTimer-Windows.zip` and `PomodoroTimer-macOS.zip` to the release.

## Tests

```bash
python -m pip install pytest
python -m pytest
```

## Project structure

```text
pomodoro-timer/
├── main.py
├── requirements.txt
├── build_windows.bat
├── build_macos.sh
├── pomodoro_timer/
│   ├── core/timer.py
│   └── ui/main_window.py
├── tests/
└── .github/workflows/build-desktop.yml
```

## Roadmap

- Custom work and break durations
- Sound and desktop notifications
- Persistent daily statistics
- Optional system-tray mode
- Signed and notarized macOS distribution
