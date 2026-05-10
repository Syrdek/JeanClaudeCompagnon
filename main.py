import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from setuptools.logging import configure

import input.hook
from server.http_server import HttpServer
from ui.controller import GuiController
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
from ui.tray import TrayApp

logger = logging.getLogger("main")

def main():
    """
    Entry point that wires up the screen reader with a keyboard listener
    and starts the input event capture loop.
    """
    # Initialize all services from configuration.
    screener = Screener.from_config(config.get("screener"))
    detector = Detector.from_config(config.get("lang-detector"))
    llm = LlmClient.from_config(config.get("llm"))
    translator = Translator.from_config(config.get("translator"), llm)
    tts = TTS.from_config(config.get("tts"))
    speaker = TextReader(tts)
    ocr = Ocr.from_config(config.get("ocr"))

    # Starts the hook in a QThread
    hook = InputHook(start=False)
    GuiController().pool_start(hook.run)

    # Audio and speech-to-text services for voice chat.
    audio_recorder = MicrophoneRecorder.from_config(config.get("microphone"))
    transcriber = Transcriber.from_config(config.get("stt"))

    # Create the processing overlay UI (progress bar, etc.).
    create_processing_ui(config.get("processing-overlay", {}))

    # Screen reader: wire up area selection with a keyboard shortcut.
    reader = ScreenReader(screener, speaker, ocr, detector, translator)
    reader_action = lambda: GuiController().open_area_selection(reader.read_screen)

    # Voice chat: configure key combination and link it to the audio chat toggle.
    audio_chat = AudioChat(recorder=audio_recorder,
                           stt=transcriber,
                           llm=llm,
                           speaker=speaker)

    # Exposes services if enabled.
    if config("expose", "enabled", default=False):
        server = HttpServer.from_config(config("expose"))
        server.start()


    logger.info("Creating application")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    # Keep the application alive even when all windows are closed (e.g., system tray).
    app.setQuitOnLastWindowClosed(False)

    tray_app = TrayApp(app=app)

    # Configures actions
    configure_action("screenshot", reader_action, hook, tray_app)
    configure_action("ask", audio_chat.switch, hook, tray_app)

    # Start listening for keyboard events.
    hook.start()

    logging.info("Ready !")

    # Enter the Qt event loop; will block until the application exits.
    sys.exit(app.exec())


def configure_action(action_name: str, action_type: Callable[[], None], hook: InputHook, tray_app: TrayApp) -> Signal:
    """
    Creates the given action in the tray menu.
    If the action has key combination bound, adds a global key combination listener.

    :param action_name: The name of the action as it is defined in configuration.
    :param action_type: The callable invoked to perform the action.
    :param hook: The hook that will listen for key combinations.
    :param tray_app: The tray icon app.
    :return: The created signal.
    """
    action_conf = config("action", action_name)
    action_signal = tray_app.add_action(action_conf("menu-text"), action_type)

    key = action_conf("key", default=None)
    if key:
        combination = CombinationListener(
            combination=key,
            strict=action_conf("strict", default=True))
        combination.on_combination_typed = lambda *a: action_signal.emit()
        hook.listeners.append(combination)
    return action_signal

def create_processing_ui(ui_conf: Config):
    """
    Build the processing overlay UI from the provided UI configuration.

    :param ui_conf: Configuration object for processing overlay settings.
    :return: A processing overlay bridge with the configured dimensions and bar color.
    """
    GuiController().configure_processing_overlay(
        width=ui_conf("width", default=200),
        height=ui_conf("height", default=20),
        bar_color=ui_conf("bar_color", default=(0, 140, 255)),
    )


if __name__ == '__main__':
    config_path = Path.cwd() / "logging.json"

    with config_path.open("r", encoding="utf-8") as f:
        config = json.load(f)

    logging.config.dictConfig(config)

    config = Config()

    main()