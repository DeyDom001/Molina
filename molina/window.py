"""Molina's frameless, transparent, always-on-top window and tray icon."""
import random
import time

from PySide6.QtCore import QPoint, Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QPainter
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from molina import sprites, startup, state, ui
from molina.care import Care
from molina.panel import Panel
from molina.sound import Sounds

SPRITE = 32       # base sprite size in px
BUBBLE_H = 52     # room above her for the speech bubble
WIDTH = 300       # fixed width so the window never jumps; transparent pixels let clicks through


class PetWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.cfg = state.load_config()
        self._press = None
        self.anim = "idle"
        self.tick = 0
        self.next_blink = time.time() + 4
        self.timer = QTimer(self, interval=1000 // sprites.FPS, timeout=self.step)
        self.timer.start()
        self.sessions = []
        self.manual_sleep = False
        self.oneoff = None  # (anim, until) for eating / playing
        self.last_activity = time.time()
        self.poller = QTimer(self, interval=300, timeout=self.poll)
        self.poller.start()
        self.apply_on_top()
        self.apply_scale()
        self.restore_position()
        self.tray = self.make_tray()
        self.care = Care(self.play_oneoff)
        self.panel = Panel(self)
        self.sounds = Sounds()
        self.seen = None  # session id -> last state, to chime on changes
        self.last_needs = 0.0

    # --- settings -------------------------------------------------------
    def save(self):
        self.cfg.update(x=self.x(), y=self.y())
        state.write_json(state.CONFIG, self.cfg)

    def apply_on_top(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.cfg["on_top"])

    def apply_scale(self):
        bottom = self.y() + self.height()
        self.setFixedSize(WIDTH, BUBBLE_H + SPRITE * self.cfg["scale"])
        self.move(self.x(), bottom - self.height())  # keep her feet where they were

    def set(self, key, value):
        self.cfg[key] = value
        if key == "scale":
            self.apply_scale()
        if key == "on_top":
            self.apply_on_top()
            self.show()  # changing window flags hides the window
        self.save()

    # --- right-click menu -----------------------------------------------
    def contextMenuEvent(self, e):
        m = QMenu(self)
        m.addAction("Hide", self.hide)
        self.check(m, "Mute sounds", self.cfg["muted"], lambda on: self.set("muted", on))
        m.addAction("Wake" if self.manual_sleep else "Sleep", self.toggle_sleep)
        self.check(m, "Always on top", self.cfg["on_top"], lambda on: self.set("on_top", on))
        size = m.addMenu("Size")
        for n in (2, 3, 4, 5):
            self.check(size, f"{n}×", self.cfg["scale"] == n, lambda _, n=n: self.set("scale", n))
        self.check(m, "Start with Windows", startup.enabled(), startup.toggle)
        m.addSeparator()
        m.addAction("Quit", QApplication.quit)
        m.exec(e.globalPos())

    @staticmethod
    def check(menu, text, on, fn):
        a = menu.addAction(text)
        a.setCheckable(True)
        a.setChecked(on)
        a.toggled.connect(fn)

    def toggle_sleep(self):
        self.manual_sleep = not self.manual_sleep
        if not self.manual_sleep:
            self.last_activity = time.time()  # waking resets the 10-minute doze timer
        self.poll()

    def pet_rect(self):
        s = SPRITE * self.cfg["scale"]
        return (WIDTH - s) // 2, BUBBLE_H, s, s

    def restore_position(self):
        x, y = self.cfg["x"], self.cfg["y"]
        px, py, s, _ = self.pet_rect()
        if x is None or not QGuiApplication.screenAt(QPoint(x + px + s // 2, y + py + s // 2)):
            g = QGuiApplication.primaryScreen().availableGeometry()
            x, y = g.right() - self.width() - 16, g.bottom() - self.height() - 16
        self.move(x, y)

    # --- tray -----------------------------------------------------------
    def make_tray(self):
        tray = QSystemTrayIcon(self.tray_icon(), self)
        tray.setToolTip("Molina")
        menu = QMenu()
        menu.addAction("Show / Hide", lambda: self.setVisible(not self.isVisible()))
        menu.addAction("Quit", QApplication.quit)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda r: r == QSystemTrayIcon.Trigger and self.setVisible(not self.isVisible()))
        tray.show()
        self._tray_menu = menu  # keep a reference
        return tray

    def tray_icon(self):
        return QIcon(sprites.pixmap("idle", 0, 1))

    # --- live state -----------------------------------------------------
    def poll(self):
        self.sessions = state.sessions()
        if self.sessions:
            self.last_activity = max(self.last_activity, time.time() - state.age(self.sessions[0]["last_event"]))
        self.alerts()
        anim = self.pick_anim()
        if anim != self.anim:
            self.anim, self.tick = anim, 0
        self.care.update(self.anim)

    def play_oneoff(self, anim):
        self.oneoff = (anim, time.time() + 2 * sprites.frames(anim) / sprites.FPS)  # loop twice
        self.poll()

    def alerts(self):
        now = time.time()
        states = {s["session_id"]: s["state"] for s in self.sessions}
        for sid, st in states.items():
            if self.seen is not None and st != self.seen.get(sid) and st in ("waiting", "done", "error"):
                self.chime({"waiting": "needs"}.get(st, st))
                if st == "waiting":
                    self.last_needs = now
        if "waiting" in states.values() and now - self.last_needs >= 60:  # still waiting: remind once a minute
            self.chime("needs")
            self.last_needs = now
        self.seen = states

    def chime(self, name):
        if not self.cfg["muted"]:
            self.sounds.play(name)

    def current(self):
        """The session to show: one that needs the owner first, else the most recently active."""
        return next((s for s in self.sessions if s["state"] == "waiting"), self.sessions[0] if self.sessions else None)

    def pick_anim(self):
        if self.oneoff and time.time() < self.oneoff[1]:
            return self.oneoff[0]
        if self.manual_sleep or time.time() - self.last_activity > 600:
            return "asleep"
        s = self.current()
        if not s:
            return "idle"
        if s["state"] == "done" and state.age(s["last_event"]) > 10:
            return "idle"
        return s["state"] if s["state"] in sprites.STATES else "idle"

    # --- animation ------------------------------------------------------
    def step(self):
        self.tick += 1
        self.update()

    def blinking(self):
        now = time.time()
        if now > self.next_blink + 0.15:
            self.next_blink = now + random.uniform(3, 6)
        return now > self.next_blink

    def paintEvent(self, _):
        x, y, _, _ = self.pet_rect()
        p = QPainter(self)
        s = self.current()
        if s and self.anim != "asleep":
            fade = 11 - state.age(s["last_event"]) if s["state"] == "done" else 1  # fade out 10 s after done
            ui.paint_bubble(p, WIDTH, BUBBLE_H - 2, [s.get("action"), ui.stage_line(s)], min(1, fade))
        p.drawPixmap(x, y, sprites.pixmap(self.anim, self.tick, self.cfg["scale"], self.blinking(), self.care.face(), self.care.acc()))
        p.end()

    # --- mouse ----------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = (e.globalPosition().toPoint(), self.pos(), False)

    def mouseMoveEvent(self, e):
        if self._press:
            start, origin, moved = self._press
            delta = e.globalPosition().toPoint() - start
            if moved or delta.manhattanLength() > 4:
                self._press = (start, origin, True)
                self.move(origin + delta)

    def mouseReleaseEvent(self, e):
        if self._press and e.button() == Qt.LeftButton:
            moved = self._press[2]
            self._press = None
            if moved:
                self.save()
            else:
                self.clicked()

    def clicked(self):
        self.panel.open()
