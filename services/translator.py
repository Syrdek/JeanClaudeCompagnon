
from pathlib import Path
import os
from typing import NoReturn

ARGOS_DIR = f"{os.getcwd()}/models/argos"
os.makedirs(ARGOS_DIR, exist_ok=True)
os.environ["ARGOS_PACKAGES_DIR"] = ARGOS_DIR

import logging
from lingua import Language, LanguageDetectorBuilder

import argostranslate.translate


class Translator(object):
    """
    Detects the language of input text and translates English content to French
    using Argos Translate and Lingua language detection.
    """

    def __init__(self):
        """
        Construct a Translator with a French/English language detector.
        """
        self.detector = LanguageDetectorBuilder.from_languages(
            Language.ENGLISH,
            Language.FRENCH,
        ).build()

    def download_languages(self) -> NoReturn:
        """
        Download and install the English-to-French Argos Translate translation package.
        """
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        package_to_install = next(
            p for p in available_packages
            if p.from_code == "en" and p.to_code == "fr"
        )

        download_path = package_to_install.download()
        argostranslate.package.install_from_path(download_path)

    def to_french(self, text: str) -> str:
        """
        Translate the given text to French if it is detected as English.

        If the language cannot be determined or is already French,
        the original text is returned unchanged.

        :param text: The text to potentially translate.
        :return: The French-translated text, or the original text if no translation is needed.
        """
        lang = self.detector.detect_language_of(text)

        if lang is None:
            return text

        if lang == Language.FRENCH:
            return text

        if lang == Language.ENGLISH:
            translated = argostranslate.translate.translate(text, "en", "fr")
            return translated

        return text


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    text = "Press \"Haggle!\" when the arrow is inside the golden bonus areas to improve the terms ofthe deal. Hitting the bonus areas tips the scale in your favor but missing them does the opposite. The scale will also gradually tip out of your favor once haggling begins The bonus areas will shrink and get harder and harder to hit each time s0 don \'t haggle for too long Fo end haggling and set the terms ofthe deal, get the arrowin one ofthe green bonus areas on the sides"
    print(Translator().to_french(text))