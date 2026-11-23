"""Add Molina's hooks to ~/.claude/settings.json (backup first, keep everything else)."""
import json
import os
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "hook" / "molina_hook.py"
MOLINA_HOME = Path.home() / ".molina"
SETTINGS = Path(os.environ.get("MOLINA_SETTINGS") or Path.home() / ".claude" / "settings.json")
EVENTS = ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PostToolUseFailure",
          "Notification", "Stop", "StopFailure", "SessionEnd"]


def is_molina(handler):
    return "molina_hook.py" in str(handler.get("command", ""))


def load_settings():
    return json.loads(SETTINGS.read_text(encoding="utf-8")) if SETTINGS.exists() else {}


def backup():
    if SETTINGS.exists():
        dst = SETTINGS.with_name(f"settings.json.molina-backup-{time.strftime('%Y%m%d-%H%M')}")
        shutil.copy2(SETTINGS, dst)
        print(f"Backup: {dst}")


def save_settings(data):
    tmp = SETTINGS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, SETTINGS)


def remove_molina(data):
    """Drop Molina's handlers; drop groups/events left empty. Returns events touched."""
    touched = []
    hooks = data.get("hooks", {})
    for event in list(hooks):
        groups = []
        for g in hooks[event]:
            kept = [h for h in g.get("hooks", []) if not is_molina(h)]
            if len(kept) != len(g.get("hooks", [])):
                touched.append(event)
            if kept:
                groups.append({**g, "hooks": kept})
        if groups:
            hooks[event] = groups
        else:
            del hooks[event]
    if "hooks" in data and not hooks:
        del data["hooks"]
    return touched


def main():
    if sys.version_info < (3, 10):
        sys.exit("Molina needs Python 3.10+")
    try:
        import PySide6  # noqa: F401
    except ImportError:
        sys.exit("PySide6 is missing. Run this with the venv: .venv\\Scripts\\python setup\\install.py")
    # base interpreter: the venv python.exe is a launcher that would start a second process
    py = Path(getattr(sys, "_base_executable", sys.executable)).as_posix()
    cmd = f'"{py}" -S "{HOOK.as_posix()}"'

    data = load_settings()
    backup()
    remove_molina(data)  # re-install = replace, never duplicate
    for event in EVENTS:
        data.setdefault("hooks", {}).setdefault(event, []).append(
            {"matcher": "", "hooks": [{"type": "command", "command": cmd, "timeout": 5}]})
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    save_settings(data)
    (MOLINA_HOME / "sessions").mkdir(parents=True, exist_ok=True)
    print(f"Added Molina's hook to {len(EVENTS)} events in {SETTINGS}: {', '.join(EVENTS)}")
    print(f"Command: {cmd}")
    print(f"Data folder: {MOLINA_HOME}")


if __name__ == "__main__":
    main()
