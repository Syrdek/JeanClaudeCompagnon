import logging
from typing import Tuple, Literal

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from core.screen_reader import ScreenReader
from input.hook import InputHook
from ui.area_overlay import AreaSelectionOverlay

logger = logging.getLogger("bridge.area")

class AreaSelectionOverlayBridge(QObject):
    """
    Links the Qt application with python script.
    """
    __open_signal = Signal()
    __overlay: AreaSelectionOverlay | None = None
    __start_pos: Tuple[int, int] | None = None

    def __init__(self, reader: ScreenReader, hook: InputHook):
        """
        Construct a AreaSelectionOverlayBridge.
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
