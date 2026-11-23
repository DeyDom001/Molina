"""Pet care: XP/levels from events.jsonl, hunger/happiness/energy, Feed and Play. Nothing is ever lost."""
import json
import time

from PySide6.QtWidgets import QHBoxLayout, QLabel, QProgressBar, QPushButton

from molina import state

PET = state.HOME / "pet.json"
EVENTS = state.HOME / "events.jsonl"
DEFAULT = {"level": 1, "xp": 0, "hunger": 80.0, "happiness": 80.0, "energy": 80.0,
           "feeds": [], "events_pos": None, "last_line": "", "last_tick": None}
WORKING = {"thinking", "reading", "writing", "running", "searching", "browsing"}
EDITS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}


def clamp(v):
    return max(0.0, min(100.0, v))


class Care:
    def __init__(self, on_anim=lambda anim: None):
        self.p = {**DEFAULT, **state.read_json(PET, {})}
        self.on_anim = on_anim
        self.saved_at = 0
        if self.p["events_pos"] is None:  # first run: only count events from now on
            self.p["events_pos"] = EVENTS.stat().st_size if EVENTS.exists() else 0

    # --- rules -----------------------------------------------------------
    def add_xp(self, n):
        p = self.p
        p["xp"] += n
        while p["level"] < 10 and p["xp"] >= 50 * p["level"]:  # level n needs 50 x n XP
            p["xp"] -= 50 * p["level"]
            p["level"] += 1
        if p["level"] == 10:
            p["xp"] = min(p["xp"], 500)

    def read_events(self):
        if not EVENTS.exists() or EVENTS.stat().st_size == self.p["events_pos"]:
            return []  # nothing new (checked every 300 ms, so skip the read)
        data = EVENTS.read_bytes()
        pos = self.p["events_pos"]
        if pos > len(data):  # the hook trimmed the file: continue after the last line we counted
            k = data.rfind(self.p["last_line"].encode()) if self.p["last_line"] else -1
            pos = k + len(self.p["last_line"].encode()) + 1 if k >= 0 else len(data)
        new = data[pos:]
        cut = new.rfind(b"\n") + 1  # only whole lines
        self.p["events_pos"] = pos + cut
        lines = new[:cut].decode("utf-8", "replace").splitlines()
        if lines:
            self.p["last_line"] = lines[-1]
        out = []
        for line in lines:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
        return out

    def update(self, anim):
        p, now = self.p, time.time()
        for ev in self.read_events():
            e, tool = ev.get("event"), ev.get("tool")
            if e == "PreToolUse" and tool in EDITS:
                self.add_xp(2)
            elif e == "PreToolUse" and tool in ("Bash", "PowerShell"):
                self.add_xp(1)
            elif e == "Stop":
                self.add_xp(10)
                p["happiness"] = clamp(p["happiness"] + 1)
            elif e in ("PostToolUseFailure", "StopFailure"):
                p["happiness"] = clamp(p["happiness"] - 3)
        dt = now - (p["last_tick"] or now)
        if dt > 120:  # PC was off or asleep: only count time while it is on
            dt = 0
        p["last_tick"] = now
        hours = dt / 3600
        p["hunger"] = clamp(p["hunger"] - 5 * hours)
        if anim in WORKING:
            p["energy"] = clamp(p["energy"] - 8 * hours)
        elif anim == "asleep":
            p["energy"] = clamp(p["energy"] + 25 * hours)
        if now - self.saved_at > 10:
            self.save()

    def save(self):
        self.saved_at = time.time()
        state.write_json(PET, self.p)

    def feeds_left(self):
        self.p["feeds"] = [t for t in self.p["feeds"] if time.time() - t < 3600]
        return 3 - len(self.p["feeds"])

    def feed(self):
        if self.feeds_left() > 0:
            self.p["feeds"].append(time.time())
            self.p["hunger"] = clamp(self.p["hunger"] + 30)
            self.save()
            self.on_anim("eating")

    def play(self):
        self.p["happiness"] = clamp(self.p["happiness"] + 15)
        self.save()
        self.on_anim("playing")

    # --- looks -----------------------------------------------------------
    def face(self):
        p = self.p
        return "hungry" if p["hunger"] < 25 else "sad" if p["happiness"] < 25 else "tired" if p["energy"] < 20 else ""

    def acc(self):
        lv = self.p["level"]
        return " ".join(a for a, need in (("scarf", 3), ("hat", 5), ("glow", 8)) if lv >= need)

    # --- panel -----------------------------------------------------------
    def panel_sig(self):
        p = self.p
        return [p["level"], p["xp"], round(p["hunger"]), round(p["happiness"]), round(p["energy"]), self.feeds_left()]

    def add_to(self, lay):
        p = self.p
        need = 50 * p["level"]
        rows = [(f"Level {p['level']}" + (" (max)" if p["level"] == 10 else f" · XP {p['xp']}/{need}"), p["xp"], need)]
        rows += [(name.capitalize(), round(p[name]), 100) for name in ("hunger", "happiness", "energy")]
        for text, value, top in rows:
            h = QHBoxLayout()
            lbl = QLabel(text)
            lbl.setProperty("muted", True)
            lbl.setFixedWidth(120)
            bar = QProgressBar(maximum=top, value=min(value, top), textVisible=False)
            h.addWidget(lbl)
            h.addWidget(bar)
            lay.addLayout(h)
        buttons = QHBoxLayout()
        left = self.feeds_left()
        feed = QPushButton(f"Feed ({left} left this hour)" if left else "Full (try later)")
        feed.setEnabled(left > 0)
        feed.clicked.connect(self.feed)
        play = QPushButton("Play")
        play.clicked.connect(self.play)
        buttons.addWidget(feed)
        buttons.addWidget(play)
        lay.addLayout(buttons)
