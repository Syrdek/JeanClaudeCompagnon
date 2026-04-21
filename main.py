import logging
import sys
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Tuple, NoReturn

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Signal

from input_hook import InputHook, CombinationListener
from ocr import Ocr
from screener import Screener
from speaker import TextReader

from translation import Translator
from ui.screen_overlay import AreaSelectionOverlay

logger = logging.getLogger("main")

pool = ThreadPoolExecutor()

class ScreenReader(object):
    """
    Orchestrates screen capture, OCR text extraction, translation to French,
    and text-to-speech playback for a given screen region.

    :param screener: Screen capture utility.
    :param speaker: Text-to-speech reader.
    :param ocr: Optical character recognition engine.
    :param translator: Language translator.
    """

    def __init__(self, screener: Screener, speaker: TextReader, ocr: Ocr, translator: Translator):
        """
        Construct a ScreenReader.

        :param screener: Screen capture utility.
        :param speaker: Text-to-speech reader.
        :param ocr: Optical character recognition engine.
        :param translator: Language translator.
        """
        self.translator = translator
        self.screener = screener
        self.speaker = speaker
        self.ocr = ocr

    def __read_screen_task(self, from_point: Tuple[int, int], to_point: Tuple[int, int]) -> NoReturn:
        """
        Background task that captures a screen region, extracts text via OCR,
        translates it to French, and reads it aloud.

        :param from_point: Top-left corner of the region to capture.
        :param to_point: Bottom-right corner of the region to capture.
        """
        logger.info("Reading screen...")
        img = self.screener.screenshot(from_point, to_point)
        img.save("screenshot.png")
        logger.info("Extracting text...")
        texts = self.ocr.read(img)
        logger.info(f"Text extracted : {texts}")
        for box, text in texts:
            logger.info(f"box: {box}, text: {text}")
            text = self.translator.to_french(text)
            logger.info(text)
            self.speaker.read(text, wait=True)
        logger.info(f"Finished !")

    def read_screen(self, from_point: Tuple[int, int], to_point: Tuple[int, int]) -> NoReturn:
        """
        Submit a screen-reading task to the thread pool for asynchronous execution.

        :param from_point: Top-left corner of the region to capture.
        :param to_point: Bottom-right corner of the region to capture.
        """
        pool.submit(self.__read_screen_task, from_point, to_point)


class OverlayBridge(QObject):
    __open_signal = Signal()
    __overlay: AreaSelectionOverlay | None = None

    def __init__(self, reader: ScreenReader):
        super().__init__()
        self.reader = reader
        self.__overlay = None
        self.__open_signal.connect(self.__qt_show)

    def __qt_show(self):
        logger.info("Showing area selection overlay...")
        if self.__overlay is not None:
            self.__overlay.close()
            self.__overlay = None

        self.__overlay = AreaSelectionOverlay()
        self.__overlay.on_accept = lambda x, y, w, h: self.reader.read_screen((x, y), (x + w, y + h))
        self.__overlay.show()

    def show_overlay(self, *args, **kwargs):
        self.__open_signal.emit()

def main():
    """
    Entry point that wires up the screen reader with a keyboard listener
    and starts the input event capture loop.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    screener = Screener()
    translator = Translator()
    speaker = TextReader()
    hook = InputHook()
    ocr = Ocr()

    reader = ScreenReader(screener, speaker, ocr, translator)
    bridge = OverlayBridge(reader)

    screen_listener = CombinationListener("ctrl+f1", strict=True)
    screen_listener.on_combination_typed = bridge.show_overlay

    hook.listeners.append(screen_listener)
    logging.info("Ready !")
    hook.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()