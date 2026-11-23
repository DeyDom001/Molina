"""Molina's pixel art. Every frame is a 32x32 grid composed from small pixel arrays.

Colour keys: o outline, b body, l belly, g gills, t gill tips, e eyes/highlights, . transparent.
"""
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap

PALETTE = {"o": "#141413", "b": "#4A4845", "l": "#6B6862", "g": "#D97757", "t": "#E8A387", "e": "#F0EEE6"}
N = 32
FPS = 8


def mirror(rows):
    return [r + r[::-1] for r in rows]


# Left half of the head + body (rows 8..27), mirrored into a symmetric 32-wide body.
BODY = mirror([
    "..........oooooo",
    "........oobbbbbb",
    ".......obbbbbbbb",
    "......obbbbbbbbb",
    "......obbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    "......obbbbbbbbb",
    ".......obbbbbbbb",
    "........oobbbbbb",
    ".........obbllll",
    "........obbbllll",
    ".......obbbbllll",
    ".......oobbbllll",
    "........obbbllll",
    ".........obbbbbb",
    "..........obbooo",
    "..........oooo..",
])
BODY_Y = 8

# Left gills (three fronds), drawn under the head so they always connect; mirrored for the right.
GILLS = [
    ".oo.......",
    "ottoo.....",
    ".oggggoo..",
    "..ooooggg.",
    "..........",
    "oooo......",
    "ottggggg..",
    ".ooooo....",
    "..........",
    ".ooo......",
    "ottgggg...",
    ".oooo.....",
]
GILLS_Y = 6

# Tail on the right; the top four rows swish sideways.
TAIL = [
    "....oo..",
    "...obbo.",
    "...obbo.",
    "..obbo..",
    "..obbo..",
    "bbbbo...",
    "bbbo....",
    "ooo.....",
]
TAIL_X, TAIL_Y = 22, 18

EYES = {
    "open": ["oe", "oo"],
    "left": ["eo", "oo"],
    "blink": ["bb", "oo"],
    "happy": ["oo", "bb"],
    "tired": ["oo", "oe"],
}
EYE_POS = ((10, 13), (20, 13))
MOUTHS = {  # pixel lists around the mouth centre (15..16, 17)
    "line": [(15, 17), (16, 17)],
    "smile": [(14, 16), (15, 17), (16, 17), (17, 16)],
    "open": [(15, 17), (16, 17), (15, 18), (16, 18)],
    "frown": [(14, 18), (15, 17), (16, 17), (17, 18)],
}
BROWS = [(10, 12), (11, 11), (20, 11), (21, 12)]  # worried: raised in the middle
CHEEKS = [(8, 15), (9, 15), (22, 15), (23, 15)]

BOOK = [".oooo.oooo.", "oeeeeoeeeeo", "oelleolleeo", "oeeeeoeeeeo", ".ooooooooo."]
PAPER = ["oooooooo", "oeeeeeeo", "oelllleo", "oeeeeeeo", "oooooooo"]
PENCIL = ["....og", "...oto", "..oto.", ".oto..", "oeo...", "o....."]
LENS = [".ooo...", "oeelo..", "olllo..", "olllo..", ".oooo..", "....oo.", ".....oo"]
GLOBE = [".ooo.", "ogleo", "olggo", "oglgo", ".ooo."]
BUBBLE = [".e.", "e.e", ".e."]
DOT = ["ee", "ee"]
ZED = ["eee", ".e.", "eee"]
SPARK = [".t.", "tet", ".t."]
DROP = [".e.", "eee", ".e."]
PELLET = ["tt", "tt"]
BALL = [".oo.", "oggo", "ogto", ".oo."]
SCARF = ["..............", ".gggggggggggg.", "..........gg..", "..........gg.."]
HAT = ["..oooo..", "..oooo..", "..gggg..", "oooooooo"]


def frames(state):
    """Number of frames in a state's loop."""
    return {"idle": 16, "asleep": 16, "writing": 4, "running": 4, "waiting": 4, "error": 4}.get(state, 6)


def spec(state, i):
    """What to draw for frame i of a state."""
    wave = (0, -1, -1, 0, 1, 1)
    s = dict(gl=0, gr=0, tail=0, eyes="open", mouth="line", props=[], lift=0, breathe=False, flash=False, brows=False)
    if state == "idle":
        s.update(breathe=4 <= i < 12, gl=(0, -1, 0, 1)[i // 4], gr=(0, -1, 0, 1)[i // 4], mouth="smile")
    elif state == "thinking":
        s.update(gl=wave[i % 6], gr=wave[(i + 2) % 6], props=[(DOT, 10 + 5 * k, 2) for k in range(i // 2 + 1)])
    elif state == "reading":
        s.update(eyes="left" if i < 3 else "open", props=[(BOOK, 10, 20)])
    elif state == "writing":
        s.update(props=[(PAPER, 12, 21), (PENCIL, 17 + i % 2, 16 + (i // 2) % 2)])
    elif state == "running":
        s.update(tail=(-1, 0, 1, 0)[i], breathe=i % 2 == 1,
                 props=[(BUBBLE, 27, 12 - 3 * i), (BUBBLE, 28, 24 - 3 * ((i + 2) % 4))])
    elif state == "searching":
        left = i < 3
        s.update(eyes="left" if left else "open", props=[(LENS, 7 if left else 19, 11)])
    elif state == "browsing":
        s.update(eyes="left" if i < 3 else "open", props=[(GLOBE, 24 - 4 * i, 1)])
    elif state == "waiting":
        s.update(lift=(0, 2, 3, 1)[i], flash=i % 2 == 0, mouth="open", gl=-1, gr=-1)
    elif state == "done":
        s.update(lift=(0, 2, 3, 2, 0, 0)[i], eyes="happy", mouth="smile",
                 props=[(SPARK, 3 if i % 2 else 26, 4 + (i % 3) * 2)])
    elif state == "error":
        s.update(gl=1, gr=1, eyes="open", brows=True, mouth="frown", props=[(DROP, 25, 9 + i % 2)])
    elif state == "asleep":
        s.update(eyes="blink", gl=1, gr=1, breathe=i >= 8, props=[(ZED, 24 + i // 8, 6 - (i % 8) // 2)])
    elif state == "eating":
        s.update(mouth="open" if i % 2 == 0 else "line", eyes="happy" if i >= 4 else "open",
                 props=[(PELLET, 20 - i, 13 + i // 2)] if i < 4 else [])
    elif state == "playing":
        s.update(lift=(0, 2, 3, 2, 0, 0)[i], mouth="smile", props=[(BALL, 14, (0, 1, 3, 1, 0, 0)[i])])
    return s


@lru_cache(maxsize=512)
def grid(state, i, blink=False, face="", acc=""):
    """Compose one frame as a tuple of 32-char strings.

    face: "" | hungry | sad | tired   acc: any of "scarf hat glow"
    """
    s = spec(state, i % frames(state))
    g = [["."] * N for _ in range(N)]

    def put(art, x, y, swap=None):
        for dy, row in enumerate(art):
            for dx, c in enumerate(row):
                if c != "." and 0 <= x + dx < N and 0 <= y + dy < N:
                    g[y + dy][x + dx] = (swap or {}).get(c, c)

    gill_swap = {"g": "t"} if s["flash"] else {}
    if "glow" in acc:
        gill_swap["t"] = "e"
    put(GILLS, 0, GILLS_Y + s["gl"], gill_swap)
    put([r[::-1] for r in GILLS], N - len(GILLS[0]), GILLS_Y + s["gr"], gill_swap)
    put(BODY, 0, BODY_Y)
    put(["." * s["tail"] + r if s["tail"] > 0 else r[-s["tail"]:] for r in TAIL[:4]], TAIL_X, TAIL_Y)
    put(TAIL[4:], TAIL_X, TAIL_Y + 4)
    for x, y in CHEEKS:
        g[y][x] = "t"

    eyes, mouth, brows = s["eyes"], s["mouth"], s["brows"]
    if face == "tired" and eyes == "open":
        eyes = "tired"
    if face == "sad" and state in ("idle", "asleep"):
        mouth, brows = "frown", True
    if face == "hungry" and mouth in ("line", "smile"):
        mouth = "open"
    if blink and eyes in ("open", "left", "tired"):
        eyes = "blink"
    for x, y in EYE_POS:
        put(EYES[eyes], x, y)
    for x, y in MOUTHS[mouth]:
        g[y][x] = "o"
    if brows:
        for x, y in BROWS:
            g[y][x] = "o"
    if "scarf" in acc:
        put(SCARF, 9, 19)
    if "hat" in acc:
        put(HAT, 12, 4)

    rows = ["".join(r) for r in g]
    if s["breathe"]:  # inhale: head up 1 px, body stretches, feet stay
        rows = rows[1:23] + [rows[22]] + rows[23:]
    if s["lift"]:
        rows = rows[s["lift"]:] + ["." * N] * s["lift"]
    for art, x, y in s["props"]:  # props are not lifted with her
        for dy, row in enumerate(art):
            if 0 <= y + dy < N:
                r = list(rows[y + dy])
                for dx, c in enumerate(row):
                    if c != "." and 0 <= x + dx < N:
                        r[x + dx] = c
                rows[y + dy] = "".join(r)
    return tuple(rows)


@lru_cache(maxsize=512)
def pixmap(state, i, scale, blink=False, face="", acc=""):
    img = QImage(N, N, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    colors = {k: QColor(v).rgba() for k, v in PALETTE.items()}
    for y, row in enumerate(grid(state, i, blink, face, acc)):
        for x, c in enumerate(row):
            if c in colors:
                img.setPixel(x, y, colors[c])
    return QPixmap.fromImage(img.scaled(N * scale, N * scale, Qt.IgnoreAspectRatio, Qt.FastTransformation))


STATES = ["idle", "thinking", "reading", "writing", "running", "searching", "browsing",
          "waiting", "done", "error", "asleep", "eating", "playing"]
