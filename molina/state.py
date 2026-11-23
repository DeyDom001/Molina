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
    if path not in _save_failed:  # say so once per file; callers save again soon with newer data
        _save_failed.add(path)
        with open(HOME / "hook_errors.log", "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} Molina could not save {path} (locked, e.g. by antivirus)\n")
    return False


_save_failed = set()


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
        try:
            a = age(s["last_event"])
        except (TypeError, KeyError, ValueError):  # not a session file, or a timestamp we can't read
            continue
        # ended: gone after 2 min; never ended (terminal closed, crash): gone after 12 h
        if a > (120 if s.get("ended") else 12 * 3600):
            p.unlink(missing_ok=True)
        if s.get("ended") or a > 12 * 3600:
            continue
        out.append(s)
    return sorted(out, key=lambda s: age(s["last_event"]))
