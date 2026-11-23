"""Speech bubble drawing and shared UI colours (Claude Code dark theme)."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainterPath, QPen

BG, BORDER, TEXT, MUTED, ACCENT = "#1F1E1D", "#30302E", "#F0EEE6", "#9C9A92", "#D97757"


def stage_line(s):
    if not s.get("stage_total"):
        return None
    return f"Stage {s['stage_index']}/{s['stage_total']} · {s.get('stage_text') or ''}".rstrip(" ·")


def paint_bubble(p, width, bottom, lines, opacity=1.0):
    """Rounded bubble centred in `width`, its tail tip at y=`bottom`. First line bright, rest muted."""
    lines = [t for t in lines if t]
    if not lines or opacity <= 0:
        return
    font = p.font()
    font.setPointSizeF(9)
    p.setFont(font)
    fm = QFontMetrics(font)
    lines = [fm.elidedText(t, Qt.ElideRight, width - 24) for t in lines]
    w = max(fm.horizontalAdvance(t) for t in lines) + 16
    h = fm.height() * len(lines) + 8
    x, y = (width - w) / 2, bottom - h - 5
    path = QPainterPath()
    path.addRoundedRect(QRectF(x, y, w, h), 6, 6)
    tail = QPainterPath()
    cx = width / 2
    tail.moveTo(cx - 5, y + h - 1)
    tail.lineTo(cx, bottom)
    tail.lineTo(cx + 5, y + h - 1)
    path = path.united(tail)
    p.save()
    p.setOpacity(opacity)
    p.setRenderHint(p.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(BORDER), 1))
    p.setBrush(QColor(BG))
    p.drawPath(path)
    for k, t in enumerate(lines):
        p.setPen(QColor(TEXT if k == 0 else MUTED))
        p.drawText(int(x + 8), int(y + 4 + fm.ascent() + k * fm.height()), t)
    p.restore()
