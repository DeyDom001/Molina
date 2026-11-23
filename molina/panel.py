"""Details panel (left click): every active session, stage bars, timers, last 5 actions."""
import json

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget

from molina import state
from molina.ui import ACCENT, BG, BORDER, MUTED, TEXT, stage_line

STYLE = f"""
QWidget {{ background: {BG}; color: {TEXT}; font-size: 9pt; }}
#panel {{ border: 1px solid {BORDER}; border-radius: 8px; }}
QLabel[muted="true"] {{ color: {MUTED}; }}
QLabel[title="true"] {{ color: {MUTED}; font-weight: bold; }}
QFrame[row="true"] {{ border: 1px solid {BORDER}; border-radius: 6px; }}
QFrame[sel="true"] {{ border-color: {ACCENT}; }}
QProgressBar {{ border: none; background: {BORDER}; max-height: 4px; border-radius: 2px; }}
QProgressBar::chunk {{ background: {ACCENT}; border-radius: 2px; }}
QPushButton {{ background: {BORDER}; border: none; padding: 4px 12px; border-radius: 4px; }}
QPushButton:hover {{ background: #3d3d3a; }}
QPushButton:disabled {{ color: {MUTED}; }}
"""


def label(text, muted=False, title=False):
    w = QLabel(text)
    w.setProperty("muted", muted)
    w.setProperty("title", title)
    w.setWordWrap(True)
    return w


def duration(iso):
    m = int(state.age(iso) // 60)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"


class Panel(QWidget):
    def __init__(self, pet):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint)  # Popup: closes on any outside click
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.pet = pet
        self.selected = None
        self.sig = None
        self.setFixedWidth(290)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        self.body = QFrame(objectName="panel")
        outer.addWidget(self.body)
        self.setStyleSheet(STYLE)
        self.timer = QTimer(self, interval=1000, timeout=self.refresh)

    def open(self):
        self.sig = None
        self.refresh()
        self.place()
        self.show()
        self.timer.start()

    def hideEvent(self, e):
        self.timer.stop()

    def place(self):
        self.adjustSize()
        pet = self.pet.frameGeometry()
        geo = QGuiApplication.screenAt(pet.center()).availableGeometry()
        x = pet.center().x() - self.width() // 2
        y = pet.top() + 40 - self.height()  # just above the bubble area
        if y < geo.top():
            y = pet.bottom() + 4
        self.move(max(geo.left(), min(x, geo.right() - self.width())), max(geo.top(), min(y, geo.bottom() - self.height())))

    def refresh(self):
        sessions = self.pet.sessions
        if self.selected not in [s["session_id"] for s in sessions]:
            self.selected = sessions[0]["session_id"] if sessions else None
        extra = self.pet.care.panel_sig()
        sig = json.dumps([sessions, self.selected, [duration(s["started"]) for s in sessions], extra], default=str)
        if sig == self.sig:  # rebuild only on change, so buttons are not swapped out mid-click
            return
        self.sig = sig
        old = self.body.layout()
        if old:
            QWidget().setLayout(old)  # reparent the old layout away so Qt deletes it
        lay = QVBoxLayout(self.body)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.addWidget(label("SESSIONS", title=True))
        if not sessions:
            lay.addWidget(label("No active Claude Code sessions.", muted=True))
        for s in sessions:
            lay.addWidget(self.row(s))
        sel = next((s for s in sessions if s["session_id"] == self.selected), None)
        if sel:
            lay.addWidget(label(f"LAST ACTIONS · {sel.get('project', '')}", title=True))
            for r in reversed(sel.get("recent", [])):
                lay.addWidget(label(f"{r['time'][11:16]}  {r['action']}", muted=True))
        lay.addWidget(label("MOLINA", title=True))
        self.pet.care.add_to(lay)
        if self.isVisible():
            self.place()

    def row(self, s):
        f = QFrame()
        f.setProperty("row", True)
        f.setProperty("sel", s["session_id"] == self.selected)
        f.mousePressEvent = lambda e, sid=s["session_id"]: self.select(sid)
        v = QVBoxLayout(f)
        v.setContentsMargins(8, 6, 8, 6)
        v.setSpacing(2)
        v.addWidget(label(f"<b>{s.get('project') or '?'}</b> · {s['state']} · {duration(s['started'])}"))
        v.addWidget(label(s.get("action", ""), muted=True))
        if s.get("stage_total"):
            bar = QProgressBar(maximum=s["stage_total"], value=s["stage_index"], textVisible=False)
            v.addWidget(bar)
            v.addWidget(label(stage_line(s), muted=True))
        return f

    def select(self, sid):
        self.selected = sid
        self.sig = None
        self.refresh()
