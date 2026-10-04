"""Synthesise the move sound sets under assets/sounds/.

The clips are generated here rather than downloaded so the shipped assets
carry no third-party licence. QSoundEffect only accepts uncompressed PCM WAV,
so every file is mono 16-bit at 44.1 kHz and stays well under a quarter of a
second.

    .venv\\Scripts\\python.exe tools\\make_sounds.py
"""

import math
import os
import random
import struct
import wave

SAMPLE_RATE = 44100
OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets",
    "sounds",
)


def _samples(duration):
    return max(1, int(SAMPLE_RATE * duration))


def _tone(
    start_hz,
    end_hz,
    duration,
    decay=18.0,
    gain=0.9,
    harmonics=(1.0,),
    attack=0.0,
):
    """A short blip that sweeps from start_hz to end_hz and fades out.

    ``attack`` is the fraction of the clip spent ramping up; a small value
    keeps a click strict but stops the waveform from starting on a hard edge.
    """
    count = _samples(duration)
    out = []
    phase = 0.0
    for i in range(count):
        frac = i / count
        freq = start_hz + (end_hz - start_hz) * frac
        phase += 2.0 * math.pi * freq / SAMPLE_RATE
        value = 0.0
        for index, amp in enumerate(harmonics, start=1):
            value += amp * math.sin(phase * index)
        envelope = math.exp(-decay * frac)
        if attack > 0.0:
            envelope *= min(1.0, frac / attack)
        out.append(gain * envelope * value)
    return out


def _click(duration=0.012, decay=120.0, gain=0.6):
    count = _samples(duration)
    return [
        gain * math.exp(-decay * (i / count)) * (random.random() * 2.0 - 1.0) for i in range(count)
    ]


def _mix(*tracks):
    length = max(len(track) for track in tracks)
    out = [0.0] * length
    for track in tracks:
        for i, value in enumerate(track):
            out[i] += value
    return out


def _double(tock, gap):
    """The same knock twice, used for castling."""
    total = _samples(gap) + len(tock)
    out = [0.0] * total
    for i, value in enumerate(tock):
        out[i] += value
    offset = _samples(gap)
    for i, value in enumerate(tock):
        out[offset + i] += value
    return out


def _arpeggio(freqs, blip_duration, gap, decay, gain):
    """A short rising run, used for promotion."""
    total = _samples(gap * (len(freqs) - 1) + blip_duration)
    out = [0.0] * total
    for index, freq in enumerate(freqs):
        blip = _tone(freq, freq, blip_duration, decay=decay, gain=gain)
        offset = _samples(gap * index)
        for i, value in enumerate(blip):
            out[offset + i] += value
    return out


def _digital():
    """Clean sine beeps, no body noise."""
    move = _mix(
        _tone(880.0, 880.0, 0.07, decay=26.0, gain=0.7),
        _click(duration=0.006, decay=300.0, gain=0.12),
    )
    return {
        "move": move,
        "capture": _mix(
            _tone(720.0, 440.0, 0.12, decay=20.0, gain=0.75),
            _click(duration=0.006, decay=300.0, gain=0.12),
        ),
        "check": _tone(990.0, 1320.0, 0.16, decay=6.0, gain=0.6),
        "castle": _double(_tone(880.0, 880.0, 0.06, decay=30.0, gain=0.7), 0.09),
        "promote": _arpeggio((659.25, 880.0, 1174.66), 0.08, 0.055, 16.0, 0.55),
        "checkmate": _arpeggio((1174.66, 987.77, 783.99), 0.13, 0.10, 9.0, 0.6),
        "draw": _arpeggio((587.33, 587.33), 0.15, 0.17, 11.0, 0.5),
    }


SETS = {
    "digital": _digital,
}


def _write(path, samples):
    peak = max(abs(value) for value in samples) or 1.0
    scale = 0.82 / peak
    frames = bytearray()
    for value in samples:
        clipped = max(-1.0, min(1.0, value * scale))
        frames += struct.pack("<h", int(clipped * 32767))
    with wave.open(path, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(frames))
    return path


def build():
    random.seed(0)
    written = []
    for set_name, factory in SETS.items():
        directory = os.path.join(OUT_DIR, set_name)
        os.makedirs(directory, exist_ok=True)
        for kind, samples in factory().items():
            written.append(_write(os.path.join(directory, kind + ".wav"), samples))
    return written


if __name__ == "__main__":
    for path in build():
        print(path)
