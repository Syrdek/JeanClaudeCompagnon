from typing import List

from lingua.lingua import LanguageDetectorBuilder, Language, LanguageDetector


class Detector(object):
    """
    Detects the language of input text.
    """

    def __init__(self, target_language: str = "french", source_languages: List[str] | str = ["french", "english"]):
        """
        Construct a language detector.

        :param target_language: The target language used for comparison.
        :param source_languages: List of languages the detector should recognize.
        """
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
    print(Detector().detect("Hello World"))