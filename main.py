import logging
import sys

from PySide6.QtWidgets import QApplication

from config.util import Config
from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.language_detection import Detector
from services.ocr import Ocr
from services.ollama_llm import OllamaClient
from services.screener import Screener
from services.speaker import TextReader, OmnivoiceTTS
from services.translator import LlmTranslator, ArgosTranslator

from ui.area_bridge import AreaSelectionOverlayBridge
from ui.processing_bridge import ProcessingOverlayBridge
from ui.tray import TrayApp

logger = logging.getLogger("main")

def main():
    """
    Entry point that wires up the screen reader with a keyboard listener
    and starts the input event capture loop.
    """
    logger.info("Creating application")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logger.info("Creating screenshot maker")
    screener = Screener(config("screener", "pixel_sensibility", default=0))

    logger.info("Creating language detector")
    detector = Detector(target_language=config("lang-detector", "target", default="french"),
                        source_languages=config("lang-detector", "source", default=["english"]))

    logger.info("Creating ollama client")
    llm = OllamaClient(
        url=config("llm", "url"),
        api_key=config("llm", "key"),
        system_prompt=config("llm", "system-prompt"),
        max_history=config("llm", "max-history", default=5)
    )

    logger.info("Creating translator")
    if config("translation", "use") == "argos":
        translator = ArgosTranslator(
            target_language=config("argos", "target", default="fra"),
            source_language=config("argos", "target", default="eng"),
            model_dir=config("argos", "model_dir", default="models/argos"),
        )
    else:
        translator = LlmTranslator(llm,
                                   model=config("translation", "model"),
                                   prompt=config("translation", "prompt"))

    logger.info("Creating text to speech reader")
    tts = OmnivoiceTTS(model_path=config("tts", "model_path", default=None),
                       ref_voice_path=config("tts", "ref_voice_path", default=None),
                       ref_voice_text=config("tts", "ref_voice_text", default=None))
    speaker = TextReader(tts)

    logger.info("Creating input hook")
    hook = InputHook()

    logger.info("Creating ocr")
    ocr = Ocr(model_path=config("ocr", "model_path", default=None),
              langs=config("ocr", "langs", default=[]),
              download=config("ocr", "download", default=True))

    processing_bridge = ProcessingOverlayBridge(
        width=config("processing-overlay", "width", default=200),
        height=config("processing-overlay", "height", default=20),
        bar_color=config("processing-overlay", "bar_color", default=(0, 140, 255)),
    )
    reader = ScreenReader(screener, speaker, ocr, detector, translator, processing_bridge)
    area_bridge = AreaSelectionOverlayBridge(reader, hook)

    screen_listener = CombinationListener(
        combination=config("keybind", "capture", "key", default="ctrl+f1"),
        strict=config("keybind", "capture", "strict", default=True))

    screen_listener.on_combination_typed = area_bridge.show_overlay

    hook.listeners.append(screen_listener)
    hook.start()

    logging.info("Ready !")

    tray_app = TrayApp(app=app, read_callback=area_bridge.show)

    sys.exit(app.exec())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    config = Config()

    main()