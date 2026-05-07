import logging
import sys
from typing import Tuple

from PySide6.QtGui import QMouseEvent, QKeyEvent, QPaintEvent, QIcon
from PySide6.QtCore import Qt, QRect, QPoint, QObject, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget

from core.screen_reader import ScreenReader
from input.hook import InputHook

logger = logging.getLogger("ui.area")

class AreaSelectionOverlay(QWidget):
    """
    Overlay to select a portion of the screen.

    Implement on_cancel and on_accept to handle cancellation and area selection..
    """
    # Start and end points of dragging area (widget logical coordinates).
    start: QPoint
    end: QPoint

    # Tells if a selection is occurring
    selecting: bool


    def __init__(self):
        """
        Initialize the selection overlay.
        """
        super().__init__()

        self.start = QPoint()
        self.end = QPoint()

        self.selecting = False

        # Always on top, borderless window
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint
        )

        # Allow transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Start in fullscreen
        self.setWindowState(Qt.WindowFullScreen)

        # Use a cross cursor for precise selection
        self.setCursor(Qt.CrossCursor)

        self.setWindowIcon(QIcon("icon.ico"))

    def on_cancel(self) -> None:
        """
        Called when selection is cancelled.
        """

    def on_accept(self, x: int, y: int, width: int, height: int) -> None:
        """
        Called when selection is accepted.
        :param x: The x position of the selection.
        :param y: The y position of the selection.
        :param width: The width of the selection.
        :param height: The height of the selection.
        """

    def on_start_dragging(self, x: int, y: int):
        """
        Called when selection starts.
        :param x: The x position of the selection.
        :param y: The y position of the selection.
        """

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Starts selection.
        :param event: The Qt mouse event.
        """
        if event.button() == Qt.LeftButton:
            self.start = event.position().toPoint()
            self.end = self.start
            self.selecting = True
            self.update()

            # Triggers event
            self.on_start_dragging(event.x(), event.y())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """
        Updates the selection.
        :param event: The Qt mouse event.
        """
        if self.selecting:
            self.end = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """
        Ends the selection.
        :param event: The Qt mouse event.
        """
        if event.button() == Qt.LeftButton:
            self.end = event.position().toPoint()
            self.selecting = False

            rect = QRect(self.start, self.end).normalized()

            # Triggers event
            self.on_accept(rect.x(), rect.y(), rect.width(), rect.height())

            self.close()

    def keyPressEvent(self, event : QKeyEvent) -> None:
        """
        Exits on escape key

        :param event: The keyboard event.
        """
        if event.key() == Qt.Key_Escape:
            self.close()

    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Paints the overlay
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        full_rect = self.rect()
        selection_rect = QRect(self.start, self.end).normalized()

        if selection_rect.isNull():
            # Paints the whole screen.
            painter.fillRect(full_rect, QColor(0, 0, 0, 80))
            return

        # Full screen
        screen_path = QPainterPath()
        screen_path.addRect(full_rect)

        # Selected area
        hole_path = QPainterPath()
        hole_path.addRect(selection_rect)

        # Removes the selected area from the screen
        overlay_path = screen_path.subtracted(hole_path)

        # Paints the overlay.
        painter.fillPath(overlay_path, QColor(0, 0, 0, 80))
        # Paints the selection.
        painter.setPen(QPen(QColor(0, 0, 0, 100), 1))
        painter.drawRect(selection_rect)




class AreaSelectionOverlayBridge(QObject):
    """
    Bridges the Qt area selection overlay with the screen reader.
    """
    __open_signal = Signal()
    __overlay: AreaSelectionOverlay | None = None
    __start_pos: Tuple[int, int] | None = None

    def __init__(self, reader: ScreenReader, hook: InputHook):
        """
        Construct an AreaSelectionOverlayBridge.

        :param reader: The screenshot reader utility.
        :param hook: The hook to use to collect mouse positions.
        """
        super().__init__()
        self.reader = reader
        self.hook = hook
        self.__start_pos = None
        self.__overlay = None
        self.__open_signal.connect(self.show)

    def show(self, *args) -> None:
        """
        Displays the Qt area selection overlay.
        """
        logger.info("Showing area selection overlay...")
        if self.__overlay is not None:
            self.__overlay.close()
            self.__overlay = None

        def capture_starting_pos(*args):
            self.__start_pos = self.hook.mouse_pos

        def capture_ending_pos(*args):
            self.reader.read_screen(self.__start_pos, self.hook.mouse_pos)

        self.__overlay = AreaSelectionOverlay()
        self.__overlay.on_start_dragging = capture_starting_pos
        self.__overlay.on_accept = capture_ending_pos
        self.__overlay.show()

    def show_overlay(self, *args):
        """
        Display the overlay on the screen.
        :param args: Any arguments (ignored).
        """
        self.__open_signal.emit()



if __name__ == "__main__":
    """
    Starts a selection overlay.
    """
    app = QApplication(sys.argv)
    overlay = AreaSelectionOverlay()
    overlay.show()
    sys.exit(app.exec())