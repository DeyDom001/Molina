"""Start Molina: python -m molina"""
import sys

from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

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
    app.setQuitOnLastWindowClosed(False)  # hiding her must not quit; Quit is in the tray/menu
    w = PetWindow()
    w.show()
    QLocalServer.removeServer(INSTANCE)  # clear a name left behind by a crash
    server = QLocalServer(app)
    server.listen(INSTANCE)
    server.newConnection.connect(lambda: (server.nextPendingConnection(), w.show(), w.raise_()))
    app.aboutToQuit.connect(w.care.save)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
