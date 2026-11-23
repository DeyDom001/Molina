"""Quit Molina, remove her Startup shortcut and only her hooks from ~/.claude/settings.json; optionally delete ~/.molina."""
import shutil
import subprocess
import sys

from install import MOLINA_HOME, ROOT, SETTINGS, backup, load_settings, remove_molina, save_settings

sys.path.insert(0, str(ROOT))
from molina.startup import LINK  # noqa: E402  (plain stdlib module: no PySide6 needed)


def main():
    try:  # needs the venv's PySide6; without it she isn't running from this folder anyway
        out = subprocess.run([sys.executable, "-m", "molina", "quit"], cwd=ROOT, capture_output=True, text=True, timeout=15)
        print(out.stdout.strip() or "Molina wasn't running.")
    except (OSError, subprocess.TimeoutExpired):
        pass
    if LINK.exists():
        LINK.unlink()
        print(f"Removed {LINK}")
    data = load_settings()
    if SETTINGS.exists():
        backup()
        touched = remove_molina(data)
        save_settings(data)
        print(f"Removed Molina's hook from: {', '.join(touched) or 'nothing (not installed)'}")
    if MOLINA_HOME.exists():
        answer = "y" if "--delete-data" in sys.argv else ""
        try:
            answer = answer or input(f"Delete {MOLINA_HOME} (pet stats, logs, sounds)? [y/N] ").strip().lower()
        except EOFError:
            pass
        if answer == "y":
            shutil.rmtree(MOLINA_HOME, ignore_errors=True)
            print("Deleted.")
        else:
            print("Kept.")


if __name__ == "__main__":
    main()
