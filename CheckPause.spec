# -*- mode: python ; coding: utf-8 -*-
import os
import re
import sys

sys.path.insert(0, SPECPATH)

from checkpause.config import STOCKFISH_RELATIVE  # noqa: E402

STOCKFISH_EXE = os.path.join(*STOCKFISH_RELATIVE)

# The .app bundle's Finder version comes from here; PyInstaller has no
# built-in source for it outside Windows' version_resource.
with open(
    os.path.join(SPECPATH, "checkpause", "__init__.py"), encoding="utf-8"
) as handle:
    APP_VERSION = re.search(
        r'APP_VERSION\s*=\s*"([^"]+)"', handle.read()
    ).group(1)

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

exe_options = {
    "name": "CheckPause",
    "debug": False,
    "bootloader_ignore_signals": False,
    "strip": False,
    "upx": False,
    "console": False,
    "disable_windowed_traceback": False,
}
if sys.platform == "win32":
    exe_options["version"] = "version_info.txt"
    exe_options["icon"] = "assets/app.ico"
elif sys.platform == "darwin":
    exe_options["icon"] = "assets/app.icns"

exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **exe_options)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="CheckPause",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="CheckPause.app",
        icon="assets/app.icns",
        bundle_identifier="com.cometzzz.checkpause",
        info_plist={
            "CFBundleName": "CheckPause",
            "CFBundleDisplayName": "CheckPause",
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleVersion": APP_VERSION,
            "CFBundlePackageType": "APPL",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSHumanReadableCopyright": "Copyright (C) 2026 CometZZZ",
        },
    )
