import logging
import time
from typing import Optional
import threading

import numpy as np
import sounddevice as sd
import soundfile as sf

from util.config import Config


class MicrophoneRecorder:
    """
    Capture audio depuis le micro avec start()/stop().
    """

    @staticmethod
    def from_config(config: Config) -> "MicrophoneRecorder":
        """
        Configures an instance.
        :param config: The configuration to use.
        :return: The configured instance.
        """
        logging.info("Creating audio recorder")

        return MicrophoneRecorder(
            sample_rate=config("sample-rate", default=16000),
            channels=config("channels", default=1),
            dtype=config("dtype", default="float32"),
            device=config("device", default=None),
            blocksize=config("blocksize", default=1024),
        )

    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        dtype: str = "float32",
        device: Optional[int | str] = None,
        blocksize: int = 1024,
    ) -> None:
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.device = device
        self.blocksize = blocksize

        self._stream: Optional[sd.InputStream] = None
        self._frames: list[np.ndarray] = []
        self._lock = threading.Lock()
        self._is_recording = False

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def _audio_callback(self, indata, frames, time_info, status) -> None:
        if status:
            print(f"[Recorder status] {status}")

        with self._lock:
            if self._is_recording:
                self._frames.append(indata.copy())

    def start(self) -> None:
        """
        Démarre la capture micro.
        """
        if self._is_recording:
            raise RuntimeError("L'enregistrement est déjà en cours.")

        with self._lock:
            self._frames = []

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=self.blocksize,
            device=self.device,
            callback=self._audio_callback,
        )
        self._stream.start()
        self._is_recording = True

    def stop(self) -> np.ndarray:
        """
        Arrête la capture et retourne l'audio sous forme de numpy array mono float32.
        """
        if not self._is_recording:
            raise RuntimeError("Aucun enregistrement en cours.")

        self._is_recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._frames:
                return np.empty((0,), dtype=np.float32)

            audio = np.concatenate(self._frames, axis=0)

        if audio.ndim == 2 and audio.shape[1] == 1:
            audio = audio[:, 0]
        elif audio.ndim == 2:
            audio = np.mean(audio, axis=1)

        return audio.astype(np.float32, copy=False)

    def save(self, path: str, audio: np.ndarray) -> None:
        sf.write(path, audio, self.sample_rate, subtype="PCM_16")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mr = MicrophoneRecorder(sample_rate=16000, channels=1, dtype="float32")
    mr.start()
    logging.info("Recording...")
    time.sleep(5)
    logging.info("Finalizing...")
    arr = mr.stop()
    mr.save("tests/audio.wav", arr)