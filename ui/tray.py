import sys
from typing import Callable

from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)


class TrayApp:
    def __init__(self,
                 app: QApplication,
                 read_callback: Callable[[], None]):
        self.app = app

        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("La zone de notification n'est pas disponible sur ce système.")

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("icon.png"))  # remplace par ton fichier
        self.tray.setToolTip("Compagnon Jean-Claude")

        menu = QMenu()

        open_action = QAction("Lire", menu)
        open_action.triggered.connect(read_callback)

        quit_action = QAction("Quitter", menu)
        quit_action.triggered.connect(self.app.quit)

        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(quit_action)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def on_tray_activated(self, reason):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_app = TrayApp(app, lambda *a: print(*a))

    sys.exit(app.exec())