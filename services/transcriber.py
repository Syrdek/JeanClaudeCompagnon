import logging
import abc
from pathlib import Path
from typing import Optional, Dict, Any

import numpy
import torch
from faster_whisper import WhisperModel, decode_audio
from scipy.io.wavfile import read

import util.convertion
from util.config import Config
from util.retry import MultipleUrlRemote

logger = logging.getLogger("transcriber")

class Transcriber(object, metaclass=abc.ABCMeta):
    """
    Abstract base class for sound transcribers.
    """
    @staticmethod
    def from_config(config: Config) -> "Transcriber":
        logger.info("Creating transcriber")
        trn_type = config.get("type", default="faster-whisper")

        if trn_type == "faster-whisper":
            return FasterWhisperTranscriber(
                model_name=config("model", default="small"),
                model_dir=config("model_path", default="models/faster-whisper"),
                device=config("device", default="auto"),
                compute_type=config("compute_type", default="int8"),
                download=config("download", default=True)
            )
        elif trn_type == "remote":
            return RemoteTranscriber(url=config("url", default="http://localhost:11111/stt"))

        raise AttributeError(f"Transcriber type not supported: {trn_type}")

    @abc.abstractmethod
    def transcribe( self, audio: str | Path | numpy.ndarray, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Transcribe an audio file or a mono float32 numpy array at 16 kHz.
        """


class FasterWhisperTranscriber(Transcriber):
    """
    Manages downloading/locating the faster-whisper model
    and transcribing a numpy audio array or an audio file.
    """

    def __init__(
        self,
        model_name: str = "small",
        model_dir: str = "models/faster-whisper",
        device: str = "auto",
        compute_type: str = "int8",
        download: bool = True
    ) -> None:
        self.model_name = model_name
        self.model_dir = Path(model_dir)
        self.compute_type = compute_type

        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
            download_root=str(self.model_dir),
            local_files_only=not download,
        )

    def transcribe(
        self,
        audio: str | Path | numpy.ndarray,
        language: Optional[str] = None,
        beam_size: int = 5,
        vad_filter: bool = True,
        word_timestamps: bool = True,
        min_silence_duration_ms: int = 500,
        condition_on_previous_text: bool = False,
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file or a mono float32 numpy array at 16 kHz.

        Returns a dict containing:
        - language
        - language_probability
        - segments
        - text
        """
        if isinstance(audio, numpy.ndarray):
            if audio.dtype != numpy.float32:
                audio = audio.astype(numpy.float32)

            if audio.ndim == 2 and audio.shape[1] == 1:
                audio = audio[:, 0]
            elif audio.ndim == 2:
                audio = numpy.mean(audio, axis=1).astype(numpy.float32)
        else:
            audio = str(audio)

        segments, info = self._model.transcribe(
            audio,
            language=language,
            beam_size=beam_size,
            vad_filter=vad_filter,
            vad_parameters=dict(min_silence_duration_ms=min_silence_duration_ms),
            word_timestamps=word_timestamps,
            condition_on_previous_text=condition_on_previous_text,
            task="transcribe",
        )

        result_segments = []
        full_text = []

        for segment in segments:
            seg = {
                "id": segment.id,
                "start": round(segment.start, 3),
                "end": round(segment.end, 3),
                "text": segment.text.strip(),
                "words": [],
            }

            if segment.words:
                for word in segment.words:
                    seg["words"].append(
                        {
                            "start": round(word.start, 3),
                            "end": round(word.end, 3),
                            "word": word.word,
                            "probability": round(word.probability, 4),
                        }
                    )

            result_segments.append(seg)
            full_text.append(seg["text"])

        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "duration_after_vad": info.duration_after_vad,
            "text": " ".join(full_text).strip(),
            "segments": result_segments,
        }


class RemoteTranscriber(MultipleUrlRemote, Transcriber):

    def transcribe(self,
                   audio: str | numpy.ndarray,
                   language: Optional[str] = None) -> Dict[str, Any]:
        if not isinstance(audio, numpy.ndarray):
            audio = decode_audio(audio)

        params: Dict[str, Any] = {
            "audio": util.convertion.ndarray_to_json_dict(audio)
        }

        if language:
            params["language"] = language

        return self.use_first_responding_url(suffix="/transcribe",
                                             method="POST",
                                             json=params)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    tr = FasterWhisperTranscriber(download=True)
    logging.info(tr.transcribe(audio="tests/audio.wav"))