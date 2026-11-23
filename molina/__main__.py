"""Start Molina, or control the running one:

  python -m molina [show|hide|sleep|wake|mute|unmute|status|quit]

No argument means show (start her if she isn't running).
"""
import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from molina import state
from molina.window import COMMANDS, PetWindow

INSTANCE = "molina-single-instance"


def main():
    cmd = sys.argv[1].lower() if len(sys.argv) > 1 else "show"
    if cmd not in COMMANDS:
        print(__doc__.strip())
        return 2
    if sys.stdout:  # None under pythonw (no console)
        sys.stdout.reconfigure(encoding="utf-8")  # replies can hold any character; callers read UTF-8
    app = QApplication(sys.argv[:1])
    probe = QLocalSocket()
    probe.connectToServer(INSTANCE)
    if probe.waitForConnected(300):  # Molina is already running: pass the command on and print her reply
        probe.write(cmd.encode())
        probe.waitForBytesWritten(300)
        if probe.waitForReadyRead(2000):
            print(bytes(probe.readAll()).decode("utf-8", "replace"))
        return 0
    if cmd != "show":
        print("Molina isn't running.")
        return 1
    state.SESSIONS.mkdir(parents=True, exist_ok=True)
    app.setQuitOnLastWindowClosed(False)  # hiding her must not quit; Quit is in the tray/menu
    w = PetWindow()
    w.show()
    QLocalServer.removeServer(INSTANCE)  # clear a name left behind by a crash
    server = QLocalServer(app)
    server.listen(INSTANCE)

    def serve():
        sock = server.nextPendingConnection()

        def reply():
            text = w.command(bytes(sock.readAll()).decode("utf-8", "replace").strip().lower())
            sock.write(text.encode())
            sock.flush()
            sock.disconnectFromServer()

        sock.readyRead.connect(reply)

    server.newConnection.connect(serve)
    app.aboutToQuit.connect(w.care.save)
    # Claude Chat has no hooks: a hidden PowerShell watcher reads its window and writes sessions/claude-chat.json
    watcher = subprocess.Popen(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(Path(__file__).with_name("chat_watch.ps1")),
         "-Out", str(state.SESSIONS / "claude-chat.json"), "-ParentPid", str(os.getpid())],
        creationflags=subprocess.CREATE_NO_WINDOW)
    app.aboutToQuit.connect(watcher.terminate)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
