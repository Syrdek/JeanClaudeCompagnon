import logging
import sys

from PySide6.QtWidgets import QApplication

from config.util import Config
from core.audio_chat import AudioChat
from core.screen_reader import ScreenReader
from input.hook import InputHook, CombinationListener
from services.language_detection import Detector
from services.ocr import Ocr
from services.ollama_llm import OllamaClient
from services.recorder import MicrophoneRecorder
from services.screener import Screener
from services.speaker import TextReader, OmnivoiceTTS
from services.transcriber import FasterWhisperTranscriber
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

    screener = create_screenshoter()
    detector = create_language_detector()
    llm = create_llm()
    translator = create_translator(llm)
    speaker = create_tts()
    hook = create_input_listener()
    ocr = create_ocr()

    logging.info("Creating audio recorder")
    audio_recorder = MicrophoneRecorder(
        sample_rate=config("microphone", "sample-rate", default=16000),
        channels=config("microphone", "channels", default=1),
        dtype=config("microphone", "dtype", default="float32"),
        device=config("microphone", "device", default=None),
        blocksize=config("microphone", "blocksize", default=1024),
    )

    logging.info("Creating transcriber")
    transcriber = FasterWhisperTranscriber(
        model_name=config("stt", "model", default="small"),
        model_dir=config("stt", "model_path", default="models/faster-whisper"),
        device=config("stt", "device", default="auto"),
        compute_type=config("stt", "compute_type", default="int8"),
        download=config("stt", "download", default=True)
    )

    processing_bridge = create_processing_ui()

    area_bridge = create_screen_area_reader(detector, hook, ocr, processing_bridge, screener, speaker, translator)
    screen_listener_combination = CombinationListener(
        combination=config("keybind", "capture", "key", default="ctrl+f1"),
        strict=config("keybind", "capture", "strict", default=True))
    screen_listener_combination.on_combination_typed = area_bridge.show_overlay
    hook.listeners.append(screen_listener_combination)

    audio_chat = AudioChat(recorder=audio_recorder,
                           stt=transcriber,
                           llm=llm,
                           speaker=speaker,
                           processing_ui=processing_bridge)
    audio_chat_combination = CombinationListener(
        combination=config("keybind", "ask", "key", default="ctrl+f2"),
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


def create_processing_ui() -> ProcessingOverlayBridge:
    processing_bridge = ProcessingOverlayBridge(
        width=config("processing-overlay", "width", default=200),
        height=config("processing-overlay", "height", default=20),
        bar_color=config("processing-overlay", "bar_color", default=(0, 140, 255)),
    )
    return processing_bridge


def create_ocr() -> Ocr:
    logger.info("Creating ocr")
    ocr = Ocr(model_path=config("ocr", "model_path", default=None),
              langs=config("ocr", "langs", default=[]),
              download=config("ocr", "download", default=True))
    return ocr


def create_input_listener() -> InputHook:
    logger.info("Creating input hook")
    hook = InputHook()
    return hook


def create_tts() -> TextReader:
    logger.info("Creating text to speech reader")
    tts = OmnivoiceTTS(model_path=config("tts", "model_path", default=None),
                       ref_voice_path=config("tts", "ref_voice_path", default=None),
                       ref_voice_text=config("tts", "ref_voice_text", default=None),
                       repo_id=config("tts", "repo_id", default="k2-fsa/OmniVoice"),
                       device=config("tts", "device", default="auto"),
                       download=config("tts", "download", default=True))
    speaker = TextReader(tts)
    return speaker


def create_translator(llm: OllamaClient) -> Translator:
    logger.info("Creating translator")
    if config("translation", "use") == "argos":
        return ArgosTranslator(
            target_language=config("argos", "target", default="fra"),
            source_language=config("argos", "target", default="eng"),
            model_dir=config("argos", "model_path", default="models/argos"),
        )
    else:
        return LlmTranslator(llm,
                            model=config("translation", "model"),
                            prompt=config("translation", "prompt"))


def create_llm() -> OllamaClient:
    logger.info("Creating ollama client")
    llm = OllamaClient(
        url=config("llm", "url"),
        api_key=config("llm", "key"),
        system_prompt=config("llm", "system-prompt"),
        max_history=config("llm", "max-history", default=5),
        default_model=config("llm", "model", default=None),
    )
    return llm


def create_language_detector() -> Detector:
    logger.info("Creating language detector")
    detector = Detector(target_language=config("lang-detector", "target", default="french"),
                        source_languages=config("lang-detector", "source", default=["english"]))
    return detector


def create_screenshoter() -> Screener:
    logger.info("Creating screenshot maker")
    screener = Screener(config("screener", "pixel_sensibility", default=0))
    return screener


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("argostranslate.utils").setLevel(logging.WARNING)

    config = Config()

    main()