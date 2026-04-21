import asyncio
import queue
import time
from queue import Queue
from threading import Thread
from typing import Any, Tuple

import numpy as np
import sounddevice
from kokoro_onnx import Kokoro

# Examples : https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/save.py
# Voices available : https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
# Voices creation : https://github.com/RobViren/kvoicewalk


class TextReader(object):
    """
    Reads a given text aloud using the Kokoro TTS engine.
    """
    audio_queue = Queue()
    kokoro: Kokoro

    def __init__(self,
                 model_path: str = "kokoro/kokoro-v1.0.onnx",
                 voices_path: str = "kokoro/voices-v1.0.bin",
                 voice: str = "ff_siwis",
                 speed: float = 1.0,
                 lang: str = "fr-fr"):
        """
        Construct a TextReader.

        :param model_path: Path to the Kokoro ONNX model file.
        :param voices_path: Path to the Kokoro voices binary file.
        :param voice: Voice identifier to use for synthesis.
        :param speed: Speech speed multiplier.
        :param lang: Language code for synthesis (e.g. "fr-fr").
        """
        self.kokoro = Kokoro(model_path, voices_path)
        self.voice = voice
        self.speed = speed
        self.lang = lang
        self.stopped = False

    def generate(self, text: str) -> Tuple[np.typing.NDArray, int]:
        """
        Generate audio samples for the given text.

        :param text: The text to synthesize.
        :return: A tuple containing the generated audio samples and the sample rate.
        """
        return self.kokoro.create(text, voice=self.voice, speed=self.speed, lang=self.lang)

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
    reader.read("Bonjour !", wait=True)