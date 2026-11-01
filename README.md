# Pomodoro Timer

A cross-platform Pomodoro desktop application built with Python and PySide6 for Windows and macOS.

Pomodoro Timer helps you organize focus sessions and breaks using a clean, minimal desktop interface.

## Features

- Pomodoro timer with configurable focus, short break, and long break durations.
- Automatic switching between focus and break sessions.
- Session counter.
- Local session history stored in SQLite.
- History dialog with completed sessions, timestamps, and durations.
- Session statistics.
- Russian and English localization.
- Multiple color themes.
- System tray integration.
- Application startup on system login.
- Custom application icons for Windows and macOS.

## Requirements

- Python 3.10+
- pip

## Run from source

Clone the repository:

```bash
git clone https://github.com/KontataGood/pomodoro-timer.git
cd pomodoro-timer
```

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies and run:

```bash
python -m pip install -r requirements.txt
python main.py
```

## Build for Windows

On Windows, run:

```powershell
.\build_windows.bat
```

The build uses `PomodoroTimer_Windows.spec`.

The resulting application is available at:

```text
dist/PomodoroTimer.exe
```

## Build for macOS

On macOS, run:

```bash
chmod +x build_macos.sh
./build_macos.sh
```

The resulting application bundle is:

```text
dist/PomodoroTimer.app
```

**macOS distribution notice:** The application is currently unsigned and not notarized. macOS may display a security warning when opening it. Public distribution should use Apple code signing and notarization.

## GitHub Actions

The GitHub Actions workflow at `.github/workflows/build-desktop.yml` builds Windows and macOS versions on their respective runners.

To build test artifacts:

1. Push your changes to GitHub.
2. Open the repository's **Actions** tab.
3. Run **Build Desktop Apps**.
4. Download the generated Windows or macOS artifact.

## GitHub Release

To publish a release, create and push a version tag.

For version `1.0.0`:

```bash
git tag v1.0.0
git push origin v1.0.0
```

The GitHub Actions workflow builds both platforms and attaches the packaged archives to the release:

- `PomodoroTimer-Windows.zip`
- `PomodoroTimer-macOS.zip`

## Tests

Install pytest:

```bash
python -m pip install pytest
```

Run the test suite:

```bash
python -m pytest -q
```

## Technologies

- Python
- PySide6 / Qt
- SQLite
- PyInstaller
- GitHub Actions

## Project Structure

```text
pomodoro-timer/
├── .github/
│   └── workflows/
│       └── build-desktop.yml
├── assets/
├── pomodoro_timer/
│   ├── core/
│   └── ui/
├── tests/
├── main.py
├── requirements.txt
├── build_windows.bat
├── build_macos.sh
├── PomodoroTimer_Windows.spec
├── PomodoroTimer.spec
├── README.md
└── CHANGELOG.md
```

## Roadmap

- Sound notifications.
- Desktop notifications.
- Persistent daily statistics.
- Code signing and notarization for macOS distribution.

## License

See the repository for license information.
