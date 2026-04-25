import logging
import os.path
import threading

from services.ollama_llm import OllamaClient
from services.recorder import MicrophoneRecorder
from services.speaker import TTS, TextReader
from services.transcriber import FasterWhisperTranscriber
from ui.processing_bridge import ProcessingOverlayBridge

logger = logging.getLogger("core.audio_chat")

class AudioChat(object):
    _lock = threading.RLock()


    def __init__(self,
                 recorder: MicrophoneRecorder,
                 stt: FasterWhisperTranscriber,
                 llm: OllamaClient,
                 speaker: TextReader,
                 processing_ui: ProcessingOverlayBridge):
        self.recorder = recorder
        self.stt = stt
        self.llm = llm
        self.speaker = speaker
        self.overlay = processing_ui
        self.recording = False

    def switch(self):
        logger.info("Switched recording")
        with self._lock:
            if self.recording:
                self.stop_recording()
            else:
                self.start_recording()

    def start_recording(self):
        logger.info("Start recording")
        with self._lock:
            if self.recording:
                return

            self.recording = True
            self.overlay.wait()
            self.recorder.start()

    def stop_recording(self):
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
