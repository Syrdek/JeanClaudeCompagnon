import logging
import sys

from PySide6.QtWidgets import QApplication

from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.ocr import Ocr
from services.screener import Screener
from services.speaker import TextReader

from services.translator import Translator
from ui.area_bridge import AreaSelectionOverlayBridge
from ui.processing_bridge import ProcessingOverlayBridge
from ui.tray import TrayApp

logger = logging.getLogger("main")

def main():
    """
    Entry point that wires up the screen reader with a keyboard listener
    and starts the input event capture loop.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    logger.info("Creating application")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.info("Creating screenshot maker")
    screener = Screener()

    logger.info("Creating translator")
    translator = Translator()

    logger.info("Creating text to speech reader")
    speaker = TextReader()

    logger.info("Creating input hook")
    hook = InputHook()

    logger.info("Creating ocr")
    ocr = Ocr()

    processing_bridge = ProcessingOverlayBridge()
    reader = ScreenReader(screener, speaker, ocr, translator, processing_bridge)
    area_bridge = AreaSelectionOverlayBridge(reader, hook)

    screen_listener = CombinationListener("ctrl+f1", strict=True)
    screen_listener.on_combination_typed = area_bridge.show_overlay

    hook.listeners.append(screen_listener)
    hook.start()

    logging.info("Ready !")

    tray_app = TrayApp(app=app, read_callback=area_bridge.show)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()