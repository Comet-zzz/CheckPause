"""Regenerate assets/app.icns from assets/app.ico.

Run after the icon changes:  python tools/make_icns.py
Requires Pillow (see requirements-build.txt). It works on any OS: Pillow
writes the ic07/ic08/ic09/ic10 representations a macOS icon needs, resizing
the source as required.
"""

import os

from PIL import Image

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(BASE_DIR, "assets", "app.ico")
TARGET = os.path.join(BASE_DIR, "assets", "app.icns")


def main():
    image = Image.open(SOURCE).convert("RGBA")
    image.save(TARGET, format="ICNS")
    print(f"wrote {TARGET}")


if __name__ == "__main__":
    main()
