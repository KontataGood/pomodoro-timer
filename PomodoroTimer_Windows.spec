# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

assets = Path("assets")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[
        (str(assets / "pomodoro_tray_64.png"), "assets"),
        (str(assets / "pomodoro_icon.ico"), "assets"),
        (str(assets / "pomodoro_icon_256.png"), "assets"),
        (str(assets / "pomodoro_icon_1024.png"), "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PomodoroTimer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(assets / "pomodoro_icon.ico"),
)
