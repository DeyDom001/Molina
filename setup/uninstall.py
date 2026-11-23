"""Remove only Molina's hooks from ~/.claude/settings.json; optionally delete ~/.molina."""
import shutil
import sys

from install import MOLINA_HOME, SETTINGS, backup, load_settings, remove_molina, save_settings


def main():
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
