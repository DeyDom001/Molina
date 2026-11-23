"""Molina's frameless, transparent, always-on-top window and tray icon."""
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QColor, QGuiApplication, QPainter, QPixmap, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QWidget

from molina import state

SPRITE = 32       # base sprite size in px
BUBBLE_H = 52     # room above her for the speech bubble
WIDTH = 300       # fixed width so the window never jumps; transparent pixels let clicks through


class PetWindow(QWidget):
    def __init__(self):
        super().__init__(None, Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.cfg = state.load_config()
        self._press = None
        self.apply_on_top()
        self.apply_scale()
        self.restore_position()
        self.tray = self.make_tray()

    # --- settings -------------------------------------------------------
    def save(self):
        self.cfg.update(x=self.x(), y=self.y())
        state.write_json(state.CONFIG, self.cfg)

    def apply_on_top(self):
        self.setWindowFlag(Qt.WindowStaysOnTopHint, self.cfg["on_top"])

    def apply_scale(self):
        self.setFixedSize(WIDTH, BUBBLE_H + SPRITE * self.cfg["scale"])

    def pet_rect(self):
        s = SPRITE * self.cfg["scale"]
        return (WIDTH - s) // 2, BUBBLE_H, s, s

    def restore_position(self):
        x, y = self.cfg["x"], self.cfg["y"]
        px, py, s, _ = self.pet_rect()
        if x is None or not QGuiApplication.screenAt(QPoint(x + px + s // 2, y + py + s // 2)):
            g = QGuiApplication.primaryScreen().availableGeometry()
            x, y = g.right() - self.width() - 16, g.bottom() - self.height() - 16
        self.move(x, y)

    # --- tray -----------------------------------------------------------
    def make_tray(self):
        tray = QSystemTrayIcon(self.tray_icon(), self)
        tray.setToolTip("Molina")
        menu = QMenu()
        menu.addAction("Show / Hide", lambda: self.setVisible(not self.isVisible()))
        menu.addAction("Quit", QApplication.quit)
        tray.setContextMenu(menu)
        tray.activated.connect(lambda r: r == QSystemTrayIcon.Trigger and self.setVisible(not self.isVisible()))
        tray.show()
        self._tray_menu = menu  # keep a reference
        return tray

    def tray_icon(self):
        pm = QPixmap(32, 32)
        pm.fill(Qt.transparent)
        self.paint_pet(QPainter(pm), 0, 0, 32)
        return QIcon(pm)

    # --- drawing --------------------------------------------------------
    def paint_pet(self, p, x, y, size):
        p.setBrush(QColor("#4A4845"))
        p.setPen(QColor("#141413"))
        p.drawEllipse(x + 2, y + 2, size - 4, size - 4)
        p.end()

    def paintEvent(self, _):
        self.paint_pet(QPainter(self), *self.pet_rect()[:3])

    # --- mouse ----------------------------------------------------------
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._press = (e.globalPosition().toPoint(), self.pos(), False)

    def mouseMoveEvent(self, e):
        if self._press:
            start, origin, moved = self._press
            delta = e.globalPosition().toPoint() - start
            if moved or delta.manhattanLength() > 4:
                self._press = (start, origin, True)
                self.move(origin + delta)

    def mouseReleaseEvent(self, e):
        if self._press and e.button() == Qt.LeftButton:
            moved = self._press[2]
            self._press = None
            if moved:
                self.save()
            else:
                self.clicked()

    def clicked(self):
        pass
