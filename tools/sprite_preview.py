"""Show every Molina animation in a grid.

  python tools/sprite_preview.py              # live preview at 3x
  python tools/sprite_preview.py 4            # live preview at 4x
  python tools/sprite_preview.py --png x.png  # save a sheet of every frame (rows = states)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QGridLayout, QLabel, QWidget

from molina import sprites

EXTRAS = [("idle blink", "idle", dict(blink=True)), ("hungry", "idle", dict(face="hungry")),
          ("sad", "idle", dict(face="sad")), ("tired", "idle", dict(face="tired")),
          ("level 8 (all)", "idle", dict(acc="scarf hat glow"))]
ROWS = [(s, s, {}) for s in sprites.STATES] + EXTRAS


def sheet(path, scale=3):
    w = max(sprites.frames(s) for _, s, _ in ROWS)
    cell = sprites.N * scale + 8
    pm = QPixmap(cell * (w + 1) + 40, cell * len(ROWS))
    pm.fill(QColor("#1F1E1D"))
    p = QPainter(pm)
    p.setPen(QColor("#9C9A92"))
    for r, (label, state, kw) in enumerate(ROWS):
        p.drawText(4, r * cell + cell // 2, label)
        for i in range(sprites.frames(state)):
            p.drawPixmap(cell + 40 + i * cell, r * cell + 4, sprites.pixmap(state, i, scale, **kw))
    p.end()
    pm.save(path)
    print(f"saved {path}")


def live(scale):
    win = QWidget()
    win.setWindowTitle("Molina sprite preview")
    win.setStyleSheet("background:#1F1E1D; color:#9C9A92;")
    lay = QGridLayout(win)
    cells = []
    for k, (label, state, kw) in enumerate(ROWS):
        img, text = QLabel(), QLabel(label, alignment=Qt.AlignCenter)
        lay.addWidget(img, (k // 6) * 2, k % 6)
        lay.addWidget(text, (k // 6) * 2 + 1, k % 6)
        cells.append((img, state, kw))
    tick = [0]

    def step():
        for img, state, kw in cells:
            img.setPixmap(sprites.pixmap(state, tick[0], scale, **kw))
        tick[0] += 1

    timer = QTimer(win, interval=1000 // sprites.FPS, timeout=step)
    timer.start()
    step()
    win.show()
    return win


if __name__ == "__main__":
    app = QApplication(sys.argv)
    if "--png" in sys.argv:
        sheet(sys.argv[sys.argv.index("--png") + 1])
    else:
        w = live(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
        sys.exit(app.exec())
