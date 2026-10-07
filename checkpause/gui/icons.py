"""Vector icon helpers for the GUI.

Icons live in ``assets/icons`` as single-colour SVGs. They are rendered on
demand and re-tinted with ``CompositionMode_SourceIn`` so one file serves
both the light and the dark theme.
"""

from functools import cache, lru_cache

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from checkpause.resources import resource_path

ICON_DIR = ("assets", "icons")

NAV_COLORS = {
    "light": {"normal": "#2a2e33", "active": "#000000", "disabled": "#b7bbbf"},
    "dark": {"normal": "#d3d7db", "active": "#ffffff", "disabled": "#5f646a"},
}

RAIL_COLORS = {
    "light": "#4b4f57",
    "dark": "#b6bac1",
}

ON_ACCENT_COLORS = {
    "light": {"normal": "#ffffff", "active": "#ffffff", "disabled": "#d6d9dd"},
    "dark": {"normal": "#1b1e22", "active": "#111316", "disabled": "#8f9399"},
}

APP_ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 128, 256)

_SCALES = (1.0, 2.0)


@cache
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
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap


@cache
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


@cache
def action_icon(theme, name, size=16, on_accent=False):
    """Icon for ordinary action buttons, including disabled and hover states.

    ``on_accent`` picks the white variant for buttons painted in the accent
    colour, where the regular dark tint would disappear.
    """
    if on_accent:
        colors = ON_ACCENT_COLORS.get(theme, ON_ACCENT_COLORS["light"])
    else:
        colors = NAV_COLORS.get(theme, NAV_COLORS["light"])
    icon = QIcon()
    for scale in _SCALES:
        pixels = max(1, int(round(size * scale)))
        for mode, tint in (
            (QIcon.Mode.Normal, colors["normal"]),
            (QIcon.Mode.Active, colors["active"]),
            (QIcon.Mode.Disabled, colors["disabled"]),
        ):
            pixmap = _pixmap(name, pixels, tint)
            if pixmap is None:
                continue
            pixmap.setDevicePixelRatio(scale)
            icon.addPixmap(pixmap, mode)
    return icon


@cache
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


@cache
def app_logo(pixels):
    """The app mark at one size, for the welcome card."""
    return _pixmap("app_icon", pixels)


@lru_cache(maxsize=1)
def app_icon():
    """Window / taskbar icon, rendered at native sizes without re-tinting."""
    icon = QIcon()
    for size in APP_ICON_SIZES:
        pixmap = _pixmap("app_icon", size)
        if pixmap is not None:
            icon.addPixmap(pixmap)
    if icon.isNull():
        # Fallback to the bundled ICO file if SVG rendering failed.
        fallback = QIcon(resource_path("assets", "app.ico"))
        if not fallback.isNull():
            icon = fallback
    return icon
