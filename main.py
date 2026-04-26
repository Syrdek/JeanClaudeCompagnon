import logging
import sys

from PySide6.QtWidgets import QApplication

from config.util import Config
from core.audio_chat import AudioChat
from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.language_detection import Detector
from services.ocr import Ocr
from services.llm import OllamaClient, LlmClient
from services.recorder import MicrophoneRecorder
from services.screener import Screener
from services.speaker import TextReader, OmnivoiceTTS, TTS
from services.transcriber import FasterWhisperTranscriber, Transcriber
from services.translator import LlmTranslator, ArgosTranslator, Translator

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

    screener = Screener.from_config(config.get("screener"))
    detector = Detector.from_config(config.get("lang-detector"))
    llm = LlmClient.from_config(config.get("llm"))
    translator = Translator.from_config(config.get("translator"), llm)
    tts = TTS.from_config(config.get("tts"))
    speaker = TextReader(tts)
    hook = create_input_listener()
    ocr = Ocr.from_config(config.get("ocr"))

    audio_recorder = MicrophoneRecorder.from_config(config.get("microphone"))
    transcriber = Transcriber.from_config(config.get("stt"))

    processing_bridge = create_processing_ui(config.get("processing-overlay", {}))

    # Screen reader
    area_bridge = create_screen_area_reader(detector, hook, ocr, processing_bridge, screener, speaker, translator)
    screen_listener_combination = CombinationListener(
        combination=config("keybind", "capture", "key", default="shift+f1"),
        strict=config("keybind", "capture", "strict", default=True))
    screen_listener_combination.on_combination_typed = area_bridge.show_overlay
    hook.listeners.append(screen_listener_combination)

    # Voice chat
    audio_chat = AudioChat(recorder=audio_recorder,
                           stt=transcriber,
                           llm=llm,
                           speaker=speaker,
                           processing_ui=processing_bridge)
    audio_chat_combination = CombinationListener(
        combination=config("keybind", "ask", "key", default="shift+f2"),
        strict=config("keybind", "ask", "strict", default=True)
    )
    audio_chat_combination.on_combination_typed = lambda *a: audio_chat.switch()
    hook.listeners.append(audio_chat_combination)

    hook.start()

    logging.info("Ready !")

    tray_app = TrayApp(app=app, read_callback=area_bridge.show)

    sys.exit(app.exec())


def create_screen_area_reader(detector: Detector, hook: InputHook, ocr: Ocr, processing_bridge: ProcessingOverlayBridge,
                              screener: Screener, speaker: TextReader, translator: Translator) -> AreaSelectionOverlayBridge:
    reader = ScreenReader(screener, speaker, ocr, detector, translator, processing_bridge)
    area_bridge = AreaSelectionOverlayBridge(reader, hook)
    return area_bridge


def create_processing_ui(ui_conf: Config) -> ProcessingOverlayBridge:
    processing_bridge = ProcessingOverlayBridge(
        width=ui_conf("width", default=200),
        height=ui_conf("height", default=20),
        bar_color=ui_conf("bar_color", default=(0, 140, 255)),
    )
    return processing_bridge


def create_input_listener() -> InputHook:
    logger.info("Creating input hook")
    hook = InputHook()
    return hook


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    config = Config()

    main()