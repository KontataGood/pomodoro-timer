
from __future__ import annotations

import os
import plistlib
import subprocess
import sys
from pathlib import Path


WINDOWS_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_VALUE_NAME = "PomodoroTimer"

MACOS_AGENT_LABEL = "com.kontatagood.pomodorotimer"


def set_autostart(enabled: bool) -> None:
    """Включает или отключает автозапуск для текущего пользователя."""

    if sys.platform == "win32":
        _set_windows_autostart(enabled)
    elif sys.platform == "darwin":
        _set_macos_autostart(enabled)
    else:
        raise OSError("Autostart is not supported on this platform")


def _set_windows_autostart(enabled: bool) -> None:
    import winreg

    if enabled:
        if getattr(sys, "frozen", False):
            command = subprocess.list2cmdline([sys.executable])
        else:
            python_executable = Path(sys.executable)
            pythonw = python_executable.with_name("pythonw.exe")

            if not pythonw.exists():
                pythonw = python_executable

            entry_point = Path(__file__).resolve().parents[2] / "main.py"
            command = subprocess.list2cmdline(
                [str(pythonw), str(entry_point)]
            )

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            WINDOWS_RUN_KEY,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(
                key,
                WINDOWS_VALUE_NAME,
                0,
                winreg.REG_SZ,
                command,
            )
    else:
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                WINDOWS_RUN_KEY,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, WINDOWS_VALUE_NAME)
        except FileNotFoundError:
            pass


def _get_macos_launch_arguments() -> list[str]:
    """Возвращает команду запуска приложения на macOS."""

    if getattr(sys, "frozen", False):
        executable = Path(sys.executable).resolve()

        # Стандартная структура PyInstaller .app:
        # PomodoroTimer.app/Contents/MacOS/PomodoroTimer
        app_bundle = executable.parents[2]

        if app_bundle.suffix == ".app" and app_bundle.exists():
            return ["/usr/bin/open", "-a", str(app_bundle)]

        return [str(executable)]

    entry_point = Path(__file__).resolve().parents[2] / "main.py"

    return [sys.executable, str(entry_point)]


def _set_macos_autostart(enabled: bool) -> None:
    """Создаёт или удаляет Launch Agent текущего пользователя."""

    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    plist_path = launch_agents_dir / f"{MACOS_AGENT_LABEL}.plist"

    if enabled:
        launch_agents_dir.mkdir(parents=True, exist_ok=True)

        plist_data = {
            "Label": MACOS_AGENT_LABEL,
            "ProgramArguments": _get_macos_launch_arguments(),
            "RunAtLoad": True,
            "KeepAlive": False,
        }

        temporary_path = plist_path.with_suffix(".plist.tmp")

        try:
            with temporary_path.open("wb") as file:
                plistlib.dump(plist_data, file)

            temporary_path.replace(plist_path)
        except OSError:
            temporary_path.unlink(missing_ok=True)
            raise

    else:
        # Если агент уже загружен, просим launchd выгрузить его.
        subprocess.run(
            [
                "/bin/launchctl",
                "bootout",
                f"gui/{os.getuid()}",
                str(plist_path),
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        plist_path.unlink(missing_ok=True)
