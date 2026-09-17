"""Build ``assets/app.ico`` (multi-size) from the queen vector icon.

PyInstaller only accepts ``.ico`` files for the executable icon, so this
script renders ``assets/icons/app_icon.svg`` with Qt's SVG engine and packs
the bitmaps into a PNG-compressed ICO container. No extra dependency is
needed: PySide6 is already required by the GUI.

Usage:
    python tools/make_icon.py [source.svg] [output.ico]
"""

import argparse
import os
import struct
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer

SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def render_png(renderer, size):
    image = QImage(size, size, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, size, size))
    painter.end()

    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    if not image.save(buffer, "PNG"):
        raise RuntimeError(f"Failed to encode {size}x{size} PNG")
    buffer.close()
    return bytes(data)


def build_ico(images):
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = []
    payload = b""
    for size, data in images:
        dimension = 0 if size >= 256 else size
        entries.append(
            struct.pack(
                "<BBBBHHII",
                dimension,
                dimension,
                0,
                0,
                1,
                32,
                len(data),
                offset,
            )
        )
        offset += len(data)
        payload += data
    return header + b"".join(entries) + payload


def main(argv=None):
    parser = argparse.ArgumentParser(description="Render the CheckPause icon")
    parser.add_argument(
        "source",
        nargs="?",
        default=os.path.join(ROOT, "assets", "icons", "app_icon.svg"),
    )
    parser.add_argument(
        "output", nargs="?", default=os.path.join(ROOT, "assets", "app.ico")
    )
    args = parser.parse_args(argv)

    app = QGuiApplication([])
    renderer = QSvgRenderer(args.source)
    if not renderer.isValid():
        raise SystemExit(f"Invalid or missing SVG: {args.source}")

    images = [(size, render_png(renderer, size)) for size in SIZES]
    with open(args.output, "wb") as handle:
        handle.write(build_ico(images))

    print(
        "Wrote {} ({} bytes, sizes: {})".format(
            args.output,
            os.path.getsize(args.output),
            ", ".join(str(size) for size in SIZES),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
