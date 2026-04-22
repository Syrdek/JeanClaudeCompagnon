import abc
import asyncio
import os
import queue
import time
from abc import ABCMeta
from queue import Queue
from threading import Thread
from typing import Any, Tuple

import numpy as np
import sounddevice
import torch
from kokoro_onnx import Kokoro
from omnivoice import OmniVoice


# Examples : https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/save.py
# Voices available : https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
# Voices creation : https://github.com/RobViren/kvoicewalk


class TTS(object, metaclass=ABCMeta):
    def __init__(self):
        pass

    @abc.abstractmethod
    def generate(self, text: str):
        pass


class KokoroTTS(TTS):

    def __init__(self,
                 model_path: str = "models/kokoro/kokoro-v1.0.fp16.onnx",
                 voices_path: str = "models/kokoro/voices-v1.0.bin",
                 voice: str = "ff_siwis",
                 speed: float = 1.0,
                 lang: str = "fr-fr"):
        """
        Construct a TTS Kokoro.

        :param model_path: Path to the Kokoro ONNX model file.
        :param voices_path: Path to the Kokoro voices binary file.
        :param voice: Voice identifier to use for synthesis.
        :param speed: Speech speed multiplier.
        :param lang: Language code for synthesis (e.g. "fr-fr").
        """
        super().__init__()

        self.kokoro = Kokoro(model_path, voices_path)
        self.voice = voice
        self.speed = speed
        self.lang = lang

    def generate(self, text: str) -> Tuple[np.typing.NDArray, int]:
        """
        Generate audio samples for the given text.

        :param text: The text to synthesize.
        :return: A tuple containing the generated audio samples and the sample rate.
        """
        return self.kokoro.create(text, voice=self.voice, speed=self.speed, lang=self.lang)


class OmnivoiceTTS(TTS):

    def __init__(self,
                 model_path: str = "models/OmniVoice",
                 ref_voice_path: str = None,
                 ref_voice_text: str = None):
        """
        Construct a TTS Omnivoice.

        :param model_path: Path to the model file.
        :param ref_voice_path: Path reference voice to clone. Optional.
        :param ref_voice_text: Path reference voice text. Optional.
        """
        super().__init__()

        self.model_path = model_path
        self.ref_voice_path = ref_voice_path
        self.ref_voice_text = ref_voice_text

        if not os.path.isfile(os.path.join(self.model_path, "model.safetensors")):
            self.__download_model()

        self.model = OmniVoice.from_pretrained(
            "models/OmniVoice",
            device_map="cuda" if torch.cuda.is_available() else "cpu",
            dtype=torch.float16
        )

    def __download_model(self):
        import huggingface_hub
        huggingface_hub.snapshot_download(
            repo_id="k2-fsa/OmniVoice",
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
    kokoro: Kokoro

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