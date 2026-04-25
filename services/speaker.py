import abc
import os
from abc import ABCMeta
from queue import Queue
from typing import Tuple

import numpy as np
import sounddevice
import torch
from omnivoice import OmniVoice



class TTS(object, metaclass=ABCMeta):
    """
    Abstract base class for text-to-speech engines.
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def generate(self, text: str):
        """
        Generate audio samples for the given text.

        :param text: The text to synthesize.
        :return: A tuple containing the generated audio samples and the sample rate.
        """
        pass



class OmnivoiceTTS(TTS):

    def __init__(self,
                 model_path: str = "models/OmniVoice",
                 ref_voice_path: str = None,
                 ref_voice_text: str = None,
                 repo_id: str = "k2-fsa/OmniVoice",
                 device: str = "auto",
                 download: bool = True):
        """
        Construct a TTS Omnivoice.

        :param model_path: Path to the model file.
        :param ref_voice_path: Path reference voice to clone. Optional.
        :param ref_voice_text: Path reference voice text. Optional.
        :param repo_id: The huggingface repo id. Optional.
        :param device: The device to use to run model. Optional.
        """
        super().__init__()

        self.repo_id = repo_id
        self.model_path = model_path
        self.ref_voice_path = ref_voice_path
        self.ref_voice_text = ref_voice_text

        if download and not os.path.isfile(os.path.join(self.model_path, "model.safetensors")):
            self.__download_model()

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model = OmniVoice.from_pretrained(
            model_path,
            device_map=self.device,
            dtype=torch.float16,
            local_files_only=not download
        )

    def __download_model(self):
        """
        Download the OmniVoice model files from the Hugging Face hub.
        """
        import huggingface_hub
        huggingface_hub.snapshot_download(
            repo_id=self.repo_id,
            local_dir=self.model_path
        )

    def generate(self, text: str) -> Tuple[np.typing.NDArray, int]:
        """
        Generate audio samples for the given text.

        :param text: The text to synthesize.
        :return: A tuple containing the generated audio samples and the sample rate.
        """
        audio = self.model.generate(
            text=text,
            ref_audio=self.ref_voice_path,
            ref_text=self.ref_voice_text,
        )
        return audio[0], 24000


class TextReader(object):
    """
    Reads a given text aloud using the Kokoro TTS engine.
    """
    audio_queue = Queue()
    tts: TTS

    def __init__(self,
                 tts: TTS | None = None):
        """
        Construct a TextReader.

        :param tts: The tts to use. Use a default TTS if not specified.
        """
        self.tts = tts if tts else OmnivoiceTTS()
        self.stopped = False

    def generate(self, text: str) -> Tuple[np.typing.NDArray, int]:
        """
        Generate audio samples for the given text.

        :param text: The text to synthesize.
        :return: A tuple containing the generated audio samples and the sample rate.
        """
        return self.tts.generate(text)

    @staticmethod
    def play(samples: np.typing.NDArray, rate: int = 24000, wait: bool = False) -> None:
        """
        Play the given audio samples.

        :param samples: The audio samples to play.
        :param rate: The sample rate of the audio.
        :param wait: If True, block until playback finishes; if False, play in the background.
        """
        sounddevice.stop()
        sounddevice.play(samples, samplerate=rate)
        if wait:
            sounddevice.wait()

    def read(self, text: str, wait: bool = False) -> None:
        """
        Read the given text aloud through the speakers.

        :param text: The text to read.
        :param wait: If True, block until playback finishes; if False, play in the background.
        """
        TextReader.play(*self.generate(text), wait=wait)



if __name__ == "__main__":
    print("Loading...")
    reader = TextReader()

    print("Generating...")
    reader.read("Bonjour Delphine ! Comment vas-tu après avoir lamentablement exploité tes pauvres développeur ?", wait=True)