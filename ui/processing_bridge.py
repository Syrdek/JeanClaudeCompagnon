import logging
from typing import Tuple, Literal

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from ui import ProcessingOverlay

logger = logging.getLogger("bridge.processing")

type ProcessingOverlayAction = Literal["wait", "play", "close"]

class ProcessingOverlayBridge(QObject):
    """
    Links the Qt application with python script.
    """
    __wait_signal = Signal()
    __load_signal = Signal()
    __play_signal = Signal()
    __close_signal = Signal()
    __overlay: ProcessingOverlay | None = None

    def __init__(self):
        """
        Construct a ProcessingOverlayBridge.
        """
        super().__init__()
        self.__overlay = None
        self.__wait_signal.connect(self.__qt_wait)
        self.__load_signal.connect(self.__qt_load)
        self.__play_signal.connect(self.__qt_play)
        self.__close_signal.connect(self.__qt_close)

    def __qt_wait(self) -> None:
        """
        Displays the Qt area selection overlay.
        """
        logger.info("Setting processing overlay to wait...")
        if self.__overlay is None:
            self.__overlay = ProcessingOverlay()
            self.__overlay.show()

        self.__overlay.set_waiting()

    def __qt_load(self) -> None:
        """
        Displays the Qt area selection overlay.
        """
        logger.info("Setting processing overlay to wait...")
        if self.__overlay is None:
            self.__overlay = ProcessingOverlay()
            self.__overlay.show()

        self.__overlay.set_loading()

    def __qt_play(self) -> None:
        """
        Displays the Qt area selection overlay.
        """
        logger.info("Setting processing overlay to wait...")
        if self.__overlay is None:
            self.__overlay = ProcessingOverlay()
            self.__overlay.show()

        self.__overlay.set_playing()


    def __qt_close(self) -> None:
        """
        Displays the Qt area selection overlay.
        """
        logger.info("Closing processing overlay...")
        if self.__overlay is not None:
            self.__overlay.close()
            self.__overlay = None

    def wait(self, *args):
        """
        Display the overlay on the screen in wait mode.
        :param args: Any arguments (ignored).
        """
        self.__wait_signal.emit()

    def load(self, *args):
        """
        Display the overlay on the screen in load mode.
        :param args: Any arguments (ignored).
        """
        self.__load_signal.emit()

    def play(self, *args):
        """
        Display the overlay on the screen in play mode.
        :param args: Any arguments (ignored).
        """
        self.__play_signal.emit()

    def close(self, *args):
        """
        Closes the overlay.
        :param args: Any arguments (ignored).
        """
        self.__close_signal.emit()