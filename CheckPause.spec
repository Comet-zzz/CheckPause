# -*- mode: python ; coding: utf-8 -*-
import os

STOCKFISH_EXE = os.path.join(
    "stockfish", "stockfish", "stockfish-windows-x86-64-universal.exe"
)
a = Analysis(
    ["run_gui.py"],
    pathex=[],
    binaries=[],
    datas=[
        (STOCKFISH_EXE, os.path.join("stockfish", "stockfish")),
        ("assets", "assets"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtWebEngineWidgets"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CheckPause",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    version="version_info.txt",
    icon="assets/app.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CheckPause",
)
