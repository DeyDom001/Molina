"""Build Molina.exe (PyInstaller one-folder) into dist\\Molina\\. Run with the venv python."""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
subprocess.run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--windowed", "--name", "Molina",
                "--paths", str(ROOT), "--distpath", str(ROOT / "dist"), "--workpath", str(ROOT / "build"),
                "--specpath", str(ROOT / "build"), str(ROOT / "molina" / "__main__.py")], check=True)
qt = ROOT / "dist" / "Molina" / "_internal" / "PySide6"
(qt / "opengl32sw.dll").unlink(missing_ok=True)  # software OpenGL fallback; plain widgets don't use it
shutil.rmtree(qt / "translations", ignore_errors=True)  # Qt's own UI translations; Molina is English only
print(f"Built {ROOT / 'dist' / 'Molina' / 'Molina.exe'}")
