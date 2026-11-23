"""Molina's pixel art. Every frame is a 32x32 grid composed from small pixel arrays.

Colour keys: o outline, b body, l belly, c cheeks, g gills, t gill tips, e eyes/highlights, . transparent.
Empty pixels next to gills, tips and highlights get a dark outline automatically (see `outline`).
"""
from functools import lru_cache

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage, QPixmap

PALETTE = {"o": "#141413", "b": "#F2B8B2", "l": "#FADBD6", "c": "#D97757",
           "g": "#D97757", "t": "#E8A387", "e": "#F0EEE6"}
N = 32
FPS = 8


def mirror(rows):
    return [r + r[::-1] for r in rows]


# Left half of the head + body (rows 6..28), mirrored into a symmetric 32-wide body.
BODY = mirror([
    "...........ooooo",
    ".........oobbbbb",
    ".......oobbbbbbb",
    "......obbbbbbbbb",
    "......obbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    ".....obbbbbbbbbb",
    "......obbbbbbbbb",
    "......obbbbbbbbb",
    ".......oobbbbbbb",
    ".........obbbbbb",
    "........obbbllll",
    ".......obbbbllll",
    "......obbobbllll",
    ".......oobbbllll",
    "........obbbllll",
    "........obbbbbbb",
    ".........obboooo",
    ".........oooo...",
])
BODY_Y = 6

# Left gills: three feathery fronds, drawn under the head so they always connect; mirrored for the right.
GILLS = [
    "..t.......",
    ".tgt......",
    "..tgt.....",
    "...tgg....",
    "....tggg..",
    "......gggg",
    "..........",
    "tt........",
    "tgggggg...",
    "ttgggggggg",
    "tt........",
    "..........",
    "...ggggggg",
    ".tgggt....",
    "tgt.......",
    ".t........",
]
GILLS_Y = 3

# Tail with a fin on the right; the top four rows swish sideways.
TAIL = ["......t.", ".....tgt", "....obbo", "...obbo.", "..obbo..", "bbbbo...", "bbbo....", "ooo....."]
TAIL_X, TAIL_Y = 23, 19

EYES = {  # 2 wide x 3 tall
    "open": ["oe", "oo", "oo"],
    "left": ["eo", "oo", "oo"],
    "blink": ["bb", "bb", "oo"],
    "happy": ["oo", "bb", "bb"],
    "tired": ["bb", "oo", "oe"],
}
EYE_POS = ((9, 12), (21, 12))
MOUTHS = {
    "line": [(15, 16), (16, 16)],
    "smile": [(14, 15), (15, 16), (16, 16), (17, 15)],
    "open": [(15, 16), (16, 16), (15, 17), (16, 17)],
    "frown": [(14, 17), (15, 16), (16, 16), (17, 17)],
}
BROWS = [(9, 11), (10, 10), (21, 10), (22, 11)]  # worried: raised in the middle
CHEEKS = [(7, 15), (8, 15), (23, 15), (24, 15)]

BOOK = [".oooo..oooo.", "oeeeeooeeeeo", "oeeeeooeeeeo", "oelleooelleo", "gggggggggggg"]
PAPER = ["oooooooo", "oeeeeeeo", "oelllleo", "oeeeeeeo", "oooooooo"]
PENCIL = ["....oo", "...oto", "..ogo.", ".ogo..", "oeo...", "oo...."]
LENS = [".eee...", "e...e..", "e...e..", "e...e..", ".eeeg..", "....gg.", ".....gg"]
GLOBE = [".ggg.", "gtgtg", "ggttg", "gtggg", ".ggg."]
BUBBLE = [".e.", "e.e", ".e."]
DOT = ["ee", "ee"]
ZED = ["eee", ".e.", "eee"]
SPARK = [".t.", "tet", ".t."]
DROP = [".e.", "eee", "eee"]
PELLET = ["tt", "tt"]
BALL = [".gg.", "gttg", "gtgg", ".gg."]
SCARF = [".gggggggggggg.", "..........gg..", "..........gg.."]
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
        s.update(gl=wave[i % 6], gr=wave[(i + 2) % 6], props=[(DOT, 10 + 5 * k, 0) for k in range(i // 2 + 1)])
    elif state == "reading":
        s.update(eyes="left" if i < 3 else "open", props=[(BOOK, 10, 21)])
    elif state == "writing":
        s.update(props=[(PAPER, 12, 22), (PENCIL, 18 + i % 2, 17 + (i // 2) % 2)])
    elif state == "running":
        s.update(tail=(-1, 0, 1, 0)[i], breathe=i % 2 == 1,
                 props=[(BUBBLE, 28, 16 - 3 * i), (BUBBLE, 26, 28 - 3 * ((i + 2) % 4))])
    elif state == "searching":
        left = i < 3
        s.update(eyes="left" if left else "open", props=[(LENS, 7 if left else 19, 10)])
    elif state == "browsing":
        s.update(eyes="left" if i < 3 else "open", props=[(GLOBE, 24 - 4 * i, 0)])
    elif state == "waiting":
        s.update(lift=(0, 2, 3, 1)[i], flash=i % 2 == 0, mouth="open", gl=-1, gr=-1)
    elif state == "done":
        s.update(lift=(0, 2, 3, 2, 0, 0)[i], eyes="happy", mouth="smile",
                 props=[(SPARK, 1 if i % 2 else 28, 20 + (i % 3) * 2)])
    elif state == "error":
        s.update(gl=1, gr=1, eyes="open", brows=True, mouth="frown", props=[(DROP, 26, 7 + i % 2)])
    elif state == "asleep":
        s.update(eyes="blink", gl=1, gr=1, breathe=i >= 8, props=[(ZED, 25 + i // 8, 4 - (i % 8) // 2)])
    elif state == "eating":
        s.update(mouth="open" if i % 2 == 0 else "line", eyes="happy" if i >= 4 else "open",
                 props=[(PELLET, 21 - i, 13 + i // 2)] if i < 4 else [])
    elif state == "playing":
        s.update(lift=(0, 2, 3, 2, 0, 0)[i], mouth="smile", props=[(BALL, 14, (0, 1, 2, 1, 0, 0)[i])])
    return s


def outline(rows):
    """Dark outline on empty pixels touching gills, tips or highlights, so she shows on any desktop."""
    g = [list(r) for r in rows]
    for y in range(N):
        for x in range(N):
            if rows[y][x] == "." and any(0 <= x + dx < N and 0 <= y + dy < N and rows[y + dy][x + dx] in "gte"
                                         for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                g[y][x] = "o"
    return tuple("".join(r) for r in g)


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
        g[y][x] = "c"

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
        put(SCARF, 9, 20)
    if "hat" in acc:
        put(HAT, 12, 2)

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
    return outline(rows)


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
