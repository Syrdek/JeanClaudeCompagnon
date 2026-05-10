import sys
from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)


class TrayApp:
    """
    System tray application icon with a context menu.
    """

    def __init__(self,
                 app: QApplication):
        """
        Construct a TrayApp and initialize the tray icon and menu.

        :param app: The Qt application instance.
        """
        self.app = app

        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("The system tray is not available on this system.")

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("icon.ico"))  # replace with your icon file
        self.tray.setToolTip("Compagnon Jean-Claude")

        self.menu = QMenu()

        quit_action = QAction("Quitter", self.menu)
        quit_action.triggered.connect(self.app.quit)

        self.end_separator = self.menu.addSeparator()
        self.menu.addAction(quit_action)

        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()

    def add_action(self, name: str, action: Callable[[], None]):
        q_action = QAction(name)
        q_action.triggered.connect(action)
        self.menu.insertAction(self.end_separator, q_action)
        return q_action.triggered

    def on_tray_activated(self, reason):
        """
        Handle tray activation events.

        :param reason: The activation reason provided by Qt.
        """
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray_app = TrayApp(app, lambda *a: print(*a))

    sys.exit(app.exec())