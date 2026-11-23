"""Files Molina reads and writes under ~/.molina."""
import json
import os
import time
from datetime import datetime
from pathlib import Path

HOME = Path(os.environ.get("MOLINA_HOME") or Path.home() / ".molina")
SESSIONS = HOME / "sessions"
CONFIG = HOME / "window.json"
DEFAULTS = {"x": None, "y": None, "scale": 3, "muted": False, "on_top": True}


def read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
    for _ in range(5):  # antivirus or a reader can hold the file for a moment
        try:
            os.replace(tmp, path)
            return True
        except PermissionError:
            time.sleep(0.05)
    return False  # skip this save; callers save again soon with newer data


def load_config():
    return {**DEFAULTS, **read_json(CONFIG, {})}


def age(iso):
    """Seconds since an ISO timestamp."""
    return time.time() - datetime.fromisoformat(iso).timestamp()


def sessions():
    """Active sessions, most recent first. Deletes ended session files after 2 min."""
    out = []
    for p in SESSIONS.glob("*.json"):
        s = read_json(p, None)
        if not isinstance(s, dict) or "last_event" not in s:
            continue
        a = age(s["last_event"])
        if s.get("ended"):
            if a > 120:
                p.unlink(missing_ok=True)
            continue
        if a > 12 * 3600:  # shortcut: a crashed session never sends SessionEnd; hide it after 12 h
            continue
        out.append(s)
    return sorted(out, key=lambda s: age(s["last_event"]))
