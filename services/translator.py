import abc
import os

import logging

from services.ollama_llm import OllamaClient


class Translator(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def translate(self, text: str) -> str:
        pass


class ArgosTranslator(object):
    """
    Translates text using argos translation.s
    """

    def __init__(self,
                 target_language: str = "fra",
                 source_language: str = "eng",
                 model_dir: str = "models/argos") -> None:
        """
        Construct a Translator with a French/English language detector.
        """
        self.source_language = source_language
        self.target_language = target_language

        argos_dir = f"{os.getcwd()}/{model_dir}"
        os.environ["ARGOS_PACKAGES_DIR"] = argos_dir
        if not os.path.isdir(argos_dir):
            os.makedirs(argos_dir, exist_ok=True)
            import argostranslate.translate

    def download_languages(self) -> None:
        """
        Download and install the English-to-French Argos Translate translation package.
        """
        import argostranslate.translate
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()

        package_to_install = next(
            p for p in available_packages
            if p.from_code == "en" and p.to_code == "fr"
        )

        download_path = package_to_install.download()
        argostranslate.package.install_from_path(download_path)

    def translate(self, text: str) -> str:
        """
        Translate the given text.

        :param text: The text to potentially translate.
        :return: The French-translated text.
        """
        import argostranslate.translate
        return argostranslate.translate.translate(text, "en", "fr")


class LlmTranslator(Translator):
    """
    Uses an LLM to translate text.
    """
    client: OllamaClient

    def __init__(self, ollama_client: OllamaClient, model: str = "gemma4:4b", prompt:str = "[TEXT]") -> None:
        self.client = ollama_client
        self.prompt = prompt
        self.model = model

    def translate(self, text: str ) -> str:
        """
        Translates the given text.
        :param text: The text to translate.
        :return: The translated text.
        """
        response = self.client.request(
            model=self.model,
            message=self.prompt.replace("[TEXT]", text),
            think=False
        )
        return response.message.content

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    text = "Press \"Haggle!\" when the arrow is inside the golden bonus areas to improve the terms ofthe deal. Hitting the bonus areas tips the scale in your favor but missing them does the opposite. The scale will also gradually tip out of your favor once haggling begins The bonus areas will shrink and get harder and harder to hit each time s0 don \'t haggle for too long Fo end haggling and set the terms ofthe deal, get the arrowin one ofthe green bonus areas on the sides"
    client = OllamaClient(url="http://localhost:11434",
                          api_key="",
                          system_prompt="Tu es un assistant qui aide un utilisateur mal-voyant à comprendre le texte affiché par une application ou un jeu vidéo. L'utilisateur pourra t'envoyer des textes issus de traitements OCR afin de les lire et/ou les traduire.")
    tran = LlmTranslator(client,
                            model="gemma4:e2b",
                            prompt="Traduis le texte suivant vers le français. Le texte peut contenir des erreurs car il a été construit par un OCR. Rectifie ces erreurs si possible. Le texte traduit sera lu à l'utilisateur via omnivoice. Tu peux donc ajouter les tags suivants dans le texte généré afin d'indiquer à omnivoice comment le lire parmi [laughter], [sigh], [confirmation-en], [question-en], [question-ah], [question-oh], [question-ei], [question-yi], [surprise-ah], [surprise-oh], [surprise-wa], [surprise-yo], [dissatisfaction-hnn]. Les tags ne sont pas nécessaires, et ne doivent pas être traduits s'ils sont présents. La réponse ne doit contenir que la traduction, et rien d'autre.\n[TEXT]")
    print(tran.translate(text))