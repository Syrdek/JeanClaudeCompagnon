import logging
import sys

from PySide6.QtWidgets import QApplication

from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.ocr import Ocr
from services.screener import Screener
from services.speaker import TextReader

from services.translator import Translator
from ui.bridge import AreaSelectionOverlayBridge

logger = logging.getLogger("main")

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
    bridge = AreaSelectionOverlayBridge(reader, hook)

    screen_listener = CombinationListener("ctrl+f1", strict=True)
    screen_listener.on_combination_typed = bridge.show_overlay

    hook.listeners.append(screen_listener)
    logging.info("Ready !")
    hook.start()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()