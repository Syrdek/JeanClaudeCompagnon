import base64
import json
import logging
import threading
import time
from io import BytesIO
from typing import Dict, Any

import flask
import requests
from PIL import Image
from flask import Flask
from werkzeug.serving import make_server

from services.ocr import Ocr
from services.speaker import TTS, TextReader
from services.transcriber import Transcriber
from util.config import Config

logger = logging.getLogger(__name__)

class HttpServer(threading.Thread):

    @staticmethod
    def from_config(conf: Config):
        return HttpServer(host=conf("host", default="localhost"),
                          port=conf("port", default=11111),
                          services=conf("services", default=[]))

    host: str
    port: int

    def __init__(self,
                 services: Dict[str, Any],
                 host: str = "127.0.0.1",
                 port: int = 11111):

        super().__init__(daemon=True)
        logger.info(f"Creating server on {host}:{port} for services {[s for s in services.keys()]}")
        self.app = Flask("jcc-server")
        self.server = make_server(host, port, self.app)
        self.ctx = self.app.app_context()
        self.services = services
        self.host = host
        self.port = port

        self.app.add_url_rule(rule="/", view_func=self.list_services, methods=["GET"])
        for service_name in self.services:
            if service_name == "ocr":
                logger.info(f"Starting OCR server on {host}:{port}")
                from server.ocr import OcrServer
                OcrServer(self.app, Ocr.from_config(self.services.get(service_name)), "/ocr")
            elif service_name == "tts":
                logger.info(f"Starting TTS server on {host}:{port}")
                from server.tts import TtsServer
                TtsServer(self.app, TTS.from_config(self.services.get(service_name)), "/tts")
            elif service_name == "stt":
                logger.info(f"Starting STT server on {host}:{port}")
                from server.stt import SttServer
                SttServer(self.app, Transcriber.from_config(self.services.get(service_name)), "/stt")
            else:
                logger.warning(f"Unknown service name : {service_name}")

    def list_services(self):
        return flask.Response(status=200, content_type="application/json", response=self.services.json())

    def run(self):
        logger.info(f"Starting server")
        self.server.serve_forever()

    def stop(self):
        logger.info(f"Stopping server")
        self.server.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    server = HttpServer.from_config(Config()("expose"))
    server.start()


    # TEST OCR
    from services.ocr import RemoteOcr
    res = Ocr.from_config(Config({"type": "remote", "url": f"http://127.0.0.1:{server.port}/ocr"})).read("tests/potion_craft_simple.png")
    logging.info(json.dumps(res, indent=2))

    # TEST TTS
    tts = TTS.from_config(Config({"type": "remote", "url": f"http://127.0.0.1:{server.port}/tts"}))
    samples, rate = tts.generate("Bonjour, comment allez vous ?")

    text = Transcriber.from_config(Config({"type": "remote", "url": f"http://127.0.0.1:{server.port}/stt"})).transcribe(samples)
    logging.info(text)

    # TEST STT
    text = Transcriber.from_config(Config({"type": "remote", "url": f"http://127.0.0.1:{server.port}/stt"})).transcribe("tests/audio.wav")
    logging.info(text)

    time.sleep(2)