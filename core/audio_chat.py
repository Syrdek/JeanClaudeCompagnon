import logging
import os.path
import threading

from services.llm import OllamaClient, LlmClient
from services.recorder import MicrophoneRecorder
from services.speaker import TTS, TextReader
from services.transcriber import FasterWhisperTranscriber
from ui.processing_bridge import ProcessingOverlayBridge

logger = logging.getLogger("core.audio_chat")

class AudioChat(object):
    """
    Manages voice chat interactions: records audio, transcribes it,
    sends the text to an LLM, and plays back the synthesized response.
    """
    _lock = threading.RLock()

    def __init__(self,
                 recorder: MicrophoneRecorder,
                 stt: FasterWhisperTranscriber,
                 llm: LlmClient,
                 speaker: TextReader,
                 processing_ui: ProcessingOverlayBridge):
        """
        Construct an AudioChat.

        :param recorder: Microphone recorder for capturing audio input.
        :param stt: Speech-to-text transcriber.
        :param llm: LLM client for generating responses.
        :param speaker: Text-to-speech reader for audio output.
        :param processing_ui: Processing overlay UI bridge for status feedback.
        """
        self.recorder = recorder
        self.stt = stt
        self.llm = llm
        self.speaker = speaker
        self.overlay = processing_ui
        self.recording = False

    def switch(self):
        """
        Toggle the recording state between started and stopped.
        """
        logger.info("Switched recording")
        with self._lock:
            if self.recording:
                self.stop_recording()
            else:
                self.start_recording()

    def start_recording(self):
        """
        Start recording audio from the microphone.
        """
        logger.info("Start recording")
        with self._lock:
            if self.recording:
                return

            self.recording = True
            self.overlay.wait()
            self.recorder.start()

    def stop_recording(self):
        """
        Stop recording, then transcribe, query the LLM, and play the response.
        """
        logger.info("Stop recording")
        with self._lock:
            if not self.recording:
                return

            self.recording = False

        self.overlay.load()

        logger.info(f"Collecting text...")
        audio_array = self.recorder.stop()
        if os.path.isdir("tests"):
            self.recorder.save("tests/audio.wav", audio_array)
        #audio_array = "tests/audio.wav"

        logger.info(f"Transcribing...")
        text = self.stt.transcribe(audio_array)["text"]

        logger.info(f"Asking LLM : {text}...")
        response = self.llm.request(message=text)

        logger.info(f"Generating samples for response: {response.message.content}...")
        audio, rate = self.speaker.generate(response.message.content)

        logger.info(f"Playing samples...")
        self.overlay.play()
        self.speaker.play(samples=audio, rate=rate, wait=True)
        self.overlay.close()
