"""Molina's original chime: a marimba-like tone (sine + soft 4x partial, fast decay), synthesized once to WAV."""
import math
import struct
import wave

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QSoundEffect

from molina.state import HOME

RATE = 44100
D4, A3, A4, E5 = 293.66, 220.0, 440.0, 659.26
CHIMES = {"needs": [D4, A4, E5], "done": [E5, A4, D4], "error": [A3]}


def synth(notes, gap=0.16, ring=0.9, volume=0.35):
    n = int(RATE * (gap * (len(notes) - 1) + ring))
    out = [0.0] * n
    for k, f in enumerate(notes):
        start = int(RATE * gap * k)
        for i in range(n - start):
            t = i / RATE
            out[start + i] += math.exp(-6 * t) * (math.sin(2 * math.pi * f * t) + 0.25 * math.exp(-20 * t) * math.sin(8 * math.pi * f * t))
    peak = max(abs(v) for v in out) or 1
    return b"".join(struct.pack("<h", int(v / peak * volume * 32767)) for v in out)


class Sounds:
    def __init__(self):
        folder = HOME / "sounds"
        folder.mkdir(parents=True, exist_ok=True)
        self.effects = {}
        for name, notes in CHIMES.items():
            path = folder / f"{name}.wav"
            if not path.exists():
                with wave.open(str(path), "wb") as w:
                    w.setnchannels(1)
                    w.setsampwidth(2)
                    w.setframerate(RATE)
                    w.writeframes(synth(notes))
            fx = QSoundEffect()
            fx.setSource(QUrl.fromLocalFile(str(path)))
            self.effects[name] = fx

    def play(self, name):
        self.effects[name].play()
