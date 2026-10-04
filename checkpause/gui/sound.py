"""Move sound effects.

Isolated from the board widget so the QtMultimedia dependency stays optional:
if the module or an audio device is missing, the player silently does nothing
and the rest of the app is unaffected. The player is silent until MainWindow
turns it on from the saved preference, which also keeps widget tests quiet.

Every clip is synthesised by tools/make_sounds.py, so the shipped sounds carry
no third-party licence.
"""

import os

from checkpause.assets import DEFAULT_SOUND_SET, SOUND_SETS
from checkpause.resources import resource_path

SOUND_KINDS = (
    "move",
    "capture",
    "check",
    "checkmate",
    "castle",
    "promote",
    "draw",
)
DEFAULT_VOLUME = 0.6


def move_sound_kind(board, move, forward=True):
    """Pick the effect that fits ``move`` on ``board``.

    ``board`` is the position the widget is showing: after the move when
    playing forward, before it when stepping back. A game-ending move is
    announced as such, and a capture that also gives check sounds like the
    check. Only forward moves announce a check, a mate or a draw; browsing
    backwards still names what the move did (capture, castle, promotion).
    """
    try:
        if forward:
            before = board.copy()
            before.pop()
            after = board
        else:
            before = board
            after = board.copy()
            after.push(move)
    except (IndexError, ValueError, AssertionError):
        return "move"
    if forward and after.is_checkmate():
        return "checkmate"
    if forward and after.is_game_over():
        return "draw"
    if before.is_castling(move):
        return "castle"
    if move.promotion is not None:
        return "promote"
    if forward and after.is_check():
        return "check"
    if before.is_capture(move):
        return "capture"
    return "move"


class SoundPlayer:
    """Plays the bundled move effects, and shrugs when it cannot."""

    def __init__(self):
        self._enabled = False
        self._set = DEFAULT_SOUND_SET
        self._loaded_set = None
        self._effects = {}
        self._available = self._probe()

    @staticmethod
    def _probe():
        try:
            from PySide6.QtMultimedia import QSoundEffect  # noqa: F401
        except Exception:
            return False
        return True

    def _ensure_loaded(self):
        if not self._available or self._loaded_set == self._set:
            return
        from PySide6.QtCore import QUrl
        from PySide6.QtMultimedia import QSoundEffect

        self._effects = {}
        self._loaded_set = self._set
        for kind in SOUND_KINDS:
            path = resource_path("assets", "sounds", self._set, kind + ".wav")
            if not os.path.isfile(path):
                continue
            effect = QSoundEffect()
            effect.setSource(QUrl.fromLocalFile(path))
            effect.setVolume(DEFAULT_VOLUME)
            self._effects[kind] = effect

    def set_enabled(self, enabled):
        self._enabled = bool(enabled) and self._available
        if self._enabled:
            self._ensure_loaded()

    def set_set(self, name):
        if name not in SOUND_SETS:
            name = DEFAULT_SOUND_SET
        if name == self._set:
            return
        self._set = name
        if self._enabled:
            self._ensure_loaded()

    def is_enabled(self):
        return self._enabled

    def play(self, kind):
        if not self._enabled:
            return
        self._ensure_loaded()
        effect = self._effects.get(kind) or self._effects.get("move")
        if effect is not None:
            effect.play()
