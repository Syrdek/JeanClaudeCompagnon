import logging
import sys

from PySide6.QtWidgets import QApplication

from util.config import Config
from core.audio_chat import AudioChat
from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.language_detection import Detector
from services.ocr import Ocr
from services.llm import LlmClient
from services.recorder import MicrophoneRecorder
from services.screener import Screener
from services.speaker import TextReader, TTS
from services.transcriber import Transcriber
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
    logger.info("Creating application")
    app = QApplication(sys.argv)
    # Keep the application alive even when all windows are closed (e.g., system tray).
    app.setQuitOnLastWindowClosed(False)

    # Initialize all services from configuration.
    screener = Screener.from_config(config.get("screener"))
    detector = Detector.from_config(config.get("lang-detector"))
    llm = LlmClient.from_config(config.get("llm"))
    translator = Translator.from_config(config.get("translator"), llm)
    tts = TTS.from_config(config.get("tts"))
    speaker = TextReader(tts)
    hook = create_input_listener()
    ocr = Ocr.from_config(config.get("ocr"))

    # Audio and speech-to-text services for voice chat.
    audio_recorder = MicrophoneRecorder.from_config(config.get("microphone"))
    transcriber = Transcriber.from_config(config.get("stt"))

    # Create the processing overlay UI (progress bar, etc.).
    processing_bridge = create_processing_ui(config.get("processing-overlay", {}))

    # Screen reader: wire up area selection with a keyboard shortcut.
    area_bridge = create_screen_area_reader(detector, hook, ocr, processing_bridge, screener, speaker, translator)
    screen_listener_combination = CombinationListener(
        combination=config("keybind", "capture", "key", default="shift+f1"),
        strict=config("keybind", "capture", "strict", default=True))
    screen_listener_combination.on_combination_typed = area_bridge.show_overlay
    hook.listeners.append(screen_listener_combination)

    # Voice chat: configure key combination and link it to the audio chat toggle.
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

    # Start listening for keyboard events.
    hook.start()

    logging.info("Ready !")

    # System tray integration with area_bridge.show as the activation callback.
    tray_app = TrayApp(app=app, read_callback=area_bridge.show)

    # Enter the Qt event loop; will block until the application exits.
    sys.exit(app.exec())


def create_screen_area_reader(detector: Detector, hook: InputHook, ocr: Ocr, processing_bridge: ProcessingOverlayBridge,
                              screener: Screener, speaker: TextReader, translator: Translator) -> AreaSelectionOverlayBridge:
    """
    Compose a screen reader for area selection and return the overlay bridge.

    :param detector: Language detector used by the screen reader.
    :param hook: Input hook that listens for keyboard events.
    :param ocr: OCR engine used to extract text.
    :param processing_bridge: Processing overlay UI bridge.
    :param screener: Screen capture component.
    :param speaker: Text reader used for audio output.
    :param translator: Translator used for language handling.
    :return: The area selection overlay bridge.
    """
    reader = ScreenReader(screener, speaker, ocr, detector, translator, processing_bridge)
    area_bridge = AreaSelectionOverlayBridge(reader, hook)
    return area_bridge


def create_processing_ui(ui_conf: Config) -> ProcessingOverlayBridge:
    """
    Build the processing overlay UI from the provided UI configuration.

    :param ui_conf: Configuration object for processing overlay settings.
    :return: A processing overlay bridge with the configured dimensions and bar color.
    """
    processing_bridge = ProcessingOverlayBridge(
        width=ui_conf("width", default=200),
        height=ui_conf("height", default=20),
        bar_color=ui_conf("bar_color", default=(0, 140, 255)),
    )
    return processing_bridge


def create_input_listener() -> InputHook:
    """
    Initialize and return a new input hook instance.

    :return: A new InputHook for listening to keyboard input events.
    """
    logger.info("Creating input hook")
    hook = InputHook()
    return hook


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    config = Config()

    main()