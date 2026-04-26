import base64
import io
import json
from io import StringIO, BytesIO
from typing import List, Any

import flask
import numpy
from PIL import Image

import util.convertion
from services.speaker import TTS, TextReader
from util.config import Config


class TtsServer(object):
    config: Config
    tts: TTS

    def __init__(self, app: flask.Flask, tts: TTS, root_path: str = "/tts"):
        self.app = app
        self.tts = tts
        self.root_path = root_path
        self.app.add_url_rule(rule=f"{root_path}/generate", methods=["POST"], view_func=self.generate)

    def generate(self):
        json_data = flask.request.get_json()
        if not "text" in json_data:
            return flask.abort(code=400, message="No text provided")

        samples, rate = self.tts.generate(**json_data)

        response = {
            "samples": util.convertion.ndarray_to_json_dict(samples),
            "rate": rate,
        }

        return flask.Response(response=json.dumps(response), status=200, mimetype="application/json")
