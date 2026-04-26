import logging
import os.path
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Tuple, NoReturn

from services.language_detection import Detector
from services.ocr import Ocr
from services.screener import Screener
from services.speaker import TextReader

from services.translator import Translator
from ui.processing_bridge import ProcessingOverlayBridge

logger = logging.getLogger("screen_reader")

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

    def __init__(self, screener: Screener, speaker: TextReader, ocr: Ocr, detector: Detector, translator: Translator, overlay: ProcessingOverlayBridge):
        """
        Construct a ScreenReader.

        :param screener: Screen capture utility.
        :param speaker: Text-to-speech reader.
        :param ocr: Optical character recognition engine.
        :param detector: Language detector.
        :param translator: Language translator.
        """
        self.overlay = overlay
        self.translator = translator
        self.detector = detector
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
        try:
            self.overlay.load()

            logger.info("Reading screen...")
            img = self.screener.screenshot(from_point, to_point)
            if os.path.isdir("tests"):
                img.save("tests/screenshot.png")

            logger.info("Extracting text...")
            texts = self.ocr.read(img)

            text = "\n\n".join([text.rstrip(" .") + "." for box, text in texts])

            logger.info(f"Text extracted : {text}")
            need_translate = not self.detector.is_target(text)
            if need_translate:
                logger.info(f"Text needs to be translated")
                text = self.translator.translate(text)
                logger.info(f"Text translated : {text}")
            logger.info(f"Generating samples...")
            audio, rate = self.speaker.generate(text)

            logger.info(f"Playing samples...")
            self.overlay.play()
            self.speaker.play(samples=audio, rate=rate, wait=True)

            self.overlay.close()
            logger.info(f"Finished !")
        except:
            logger.exception("Error occured !")

    def read_screen(self, from_point: Tuple[int, int], to_point: Tuple[int, int]) -> NoReturn:
        """
        Submit a screen-reading task to the thread pool for asynchronous execution.

        :param from_point: Top-left corner of the region to capture.
        :param to_point: Bottom-right corner of the region to capture.
        """
        logger.info(f"Captured fragment : {from_point}, {to_point}")
        pool.submit(self.__read_screen_task, from_point, to_point)