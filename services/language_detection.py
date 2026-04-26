import abc
import logging
from typing import List, Any

from lingua.lingua import LanguageDetectorBuilder, Language, LanguageDetector

from config.util import Config

logger = logging.getLogger(__name__)

class Detector(object, metaclass=abc.ABCMeta):
    """
    Detects the language of input text.
    """
    @staticmethod
    def from_config(config: Config) -> "Detector":
        """
        Configures an instance.
        :param config: The configuration to use.
        :return: The configured instance.
        """
        logger.info("Creating language detector")

        det_type = config("type", default="lingua")
        if det_type == "lingua":
            return LinguaDetector(target_language=config("target", default="french"),
                                  source_languages=config("source", default=["english"]))

        raise AttributeError(f"Language detector type not supported : {det_type}.")

    @abc.abstractmethod
    def detect(self, text: str) -> Any:
        """
        Detect the input text language.
        :param text: The text.
        :return: The language detected.
        """

    @abc.abstractmethod
    def is_target(self, text: str) -> bool:
        """
        Determine if the input text language is target language.
        :param text: The text.
        :return: True if the input text language is target language, False otherwise.
        """


class LinguaDetector(Detector):

    def __init__(self, target_language: str = "french", source_languages: List[str] | str = ["french", "english"]):
        """
        Construct a language detector.

        :param target_language: The target language used for comparison.
        :param source_languages: List of languages the detector should recognize.
        """
        super().__init__()

        if isinstance(source_languages, str):
            source_languages = [source_languages]

        self.target_language = Language.from_str(target_language.upper())
        self.source_languages = [Language.from_str(l.upper()) for l in source_languages]

        if self.target_language not in self.source_languages:
            self.source_languages.append(self.target_language)

        self.detector = LanguageDetectorBuilder.from_languages(
            *self.source_languages
        ).build()

    def detect(self, text: str) -> Language:
        """
        Detect the input text language.
        :param text: The text.
        :return: The language detected.
        """
        return self.detector.detect_language_of(text)

    def is_target(self, text: str) -> bool:
        """
        Determine if the input text language is target language.
        :param text: The text.
        :return: True if the input text language is target language, False otherwise.
        """
        return self.detect(text) == self.target_language

if __name__ == "__main__":
    print(Detector.from_config(Config()).detect("Hello World"))