import sys

from PySide6.QtGui import QMouseEvent, QKeyEvent, QPaintEvent
from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QPainterPath
from PySide6.QtWidgets import QApplication, QWidget


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



if __name__ == "__main__":
    """
    Starts a selection overlay.
    """
    app = QApplication(sys.argv)
    overlay = AreaSelectionOverlay()
    overlay.show()
    sys.exit(app.exec())