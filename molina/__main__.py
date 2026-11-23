"""Start Molina: python -m molina"""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from molina import state
from molina.window import PetWindow

INSTANCE = "molina-single-instance"


def main():
    app = QApplication(sys.argv)
    probe = QLocalSocket()
    probe.connectToServer(INSTANCE)
    if probe.waitForConnected(300):  # Molina is already running: ask her to show herself, then quit
        probe.write(b"show")
        probe.waitForBytesWritten(300)
        return
    state.SESSIONS.mkdir(parents=True, exist_ok=True)
    app.setQuitOnLastWindowClosed(False)  # hiding her must not quit; Quit is in the tray/menu
    w = PetWindow()
    w.show()
    QLocalServer.removeServer(INSTANCE)  # clear a name left behind by a crash
    server = QLocalServer(app)
    server.listen(INSTANCE)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), w.show(), w.raise_()))
    app.aboutToQuit.connect(w.care.save)
    # Claude Chat has no hooks: a hidden PowerShell watcher reads its window and writes sessions/claude-chat.json
    watcher = subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(Path(__file__).with_name("chat_watch.ps1")),
         "-Out", str(state.SESSIONS / "claude-chat.json"), "-ParentPid", str(os.getpid())],
        creationflags=subprocess.CREATE_NO_WINDOW)
    app.aboutToQuit.connect(watcher.terminate)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
