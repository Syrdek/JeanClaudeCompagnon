import sys
from typing import Callable

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
                 app: QApplication,
                 read_callback: Callable[[], None]):
        """
        Construct a TrayApp and initialize the tray icon and menu.

        :param app: The Qt application instance.
        :param read_callback: Callable invoked when the user selects the read action.
        """
        self.app = app

        if not QSystemTrayIcon.isSystemTrayAvailable():
            raise RuntimeError("The system tray is not available on this system.")

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(QIcon("icon.png"))  # replace with your icon file
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