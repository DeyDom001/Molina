"""Start Molina: python -m molina"""
import sys

from PySide6.QtWidgets import QApplication

from molina.window import PetWindow


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # hiding her must not quit; Quit is in the tray/menu
    w = PetWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
