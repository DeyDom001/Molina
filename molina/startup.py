"""'Start with Windows': a Molina shortcut in the user's Startup folder."""
import os
import subprocess
import sys
from pathlib import Path

LINK = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "Molina.lnk"
ROOT = Path(__file__).resolve().parent.parent


def enabled():
    return LINK.exists()


def toggle(on):
    if not on:
        LINK.unlink(missing_ok=True)
        return
    if getattr(sys, "frozen", False):  # Molina.exe
        target, args, cwd = sys.executable, "", Path(sys.executable).parent
    else:  # pythonw: no console window
        target, args, cwd = Path(sys.executable).with_name("pythonw.exe"), "-m molina", ROOT
    q = lambda s: str(s).replace("'", "''")  # PowerShell single-quote escaping
    ps = (f"$s=(New-Object -ComObject WScript.Shell).CreateShortcut('{q(LINK)}');"
          f"$s.TargetPath='{q(target)}';$s.Arguments='{q(args)}';$s.WorkingDirectory='{q(cwd)}';$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], creationflags=subprocess.CREATE_NO_WINDOW, check=False)
