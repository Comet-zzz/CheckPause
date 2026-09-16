"""Vector icon helpers for the GUI.

Icons live in ``assets/icons`` as single-colour SVGs. They are rendered on
demand and re-tinted with ``CompositionMode_SourceIn`` so one file serves
both the light and the dark theme.
"""

from functools import lru_cache

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer

from checkpause.resources import resource_path

ICON_DIR = ("assets", "icons")

NAV_COLORS = {
    "light": {"normal": "#33363b", "disabled": "#b4b7bc"},
    "dark": {"normal": "#d6d8dc", "disabled": "#5c6066"},
}

RAIL_COLORS = {
    "light": "#4b4f57",
    "dark": "#b6bac1",
}

APP_ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)

_SCALES = (1.0, 2.0)


@lru_cache(maxsize=None)
def _renderer(name):
    renderer = QSvgRenderer(resource_path(*ICON_DIR, name + ".svg"))
    return renderer if renderer.isValid() else None


def _pixmap(name, pixels, color=None):
    renderer = _renderer(name)
    if renderer is None:
        return None

    pixmap = QPixmap(pixels, pixels)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    renderer.render(painter, QRectF(0, 0, pixels, pixels))
    if color is not None:
        painter.setCompositionMode(
            QPainter.CompositionMode.CompositionMode_SourceIn
        )
        painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap


@lru_cache(maxsize=None)
def nav_icon(theme, name, size=16):
    """Icon for the board navigation buttons, including a disabled state."""
    colors = NAV_COLORS.get(theme, NAV_COLORS["light"])
    icon = QIcon()
    for scale in _SCALES:
        pixels = max(1, int(round(size * scale)))
        for mode, tint in (
            (QIcon.Mode.Normal, colors["normal"]),
            (QIcon.Mode.Disabled, colors["disabled"]),
        ):
            pixmap = _pixmap(name, pixels, tint)
            if pixmap is None:
                continue
            pixmap.setDevicePixelRatio(scale)
            icon.addPixmap(pixmap, mode)
    return icon


@lru_cache(maxsize=None)
def rail_icon(theme, name, size=20):
    """Icon for the module rail buttons."""
    color = RAIL_COLORS.get(theme, RAIL_COLORS["light"])
    icon = QIcon()
    for scale in _SCALES:
        pixmap = _pixmap(name, max(1, int(round(size * scale))), color)
        if pixmap is None:
            continue
        pixmap.setDevicePixelRatio(scale)
        icon.addPixmap(pixmap)
    return icon


@lru_cache(maxsize=1)
def app_icon():
    """Window / taskbar icon, rendered at native sizes without re-tinting."""
    icon = QIcon()
    for size in APP_ICON_SIZES:
        pixmap = _pixmap("app_icon", size)
        if pixmap is not None:
            icon.addPixmap(pixmap)
    return icon
