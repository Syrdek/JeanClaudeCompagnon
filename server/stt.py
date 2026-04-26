import base64
import io
import json
from io import StringIO, BytesIO
from typing import List, Any

import flask
import numpy
from PIL import Image

import util.convertion
from services.speaker import TTS
from services.transcriber import Transcriber
from util.config import Config


class SttServer(object):
    """
    Flask HTTP server endpoint for speech-to-text transcription.
    """
    config: Config
    transcriber: Transcriber

    def __init__(self, app: flask.Flask, transcriber: Transcriber, root_path: str = "/tts"):
        """
        Construct a SttServer and register the transcribe endpoint.

        :param app: The Flask application instance.
        :param transcriber: The transcriber to use for transcription.
        :param root_path: URL prefix for the STT endpoint.
        """
        self.app = app
        self.transcriber = transcriber
        self.root_path = root_path
        self.app.add_url_rule(rule=f"{root_path}/transcribe", methods=["POST"], view_func=self.transcribe)

    def transcribe(self):
        """
        Handle a POST request to transcribe audio.

        Expects a JSON body with an "audio" field containing a serialized
        numpy array. Returns a JSON response with the transcription result.

        :return: Flask JSON response with the transcription data.
        """
        json_data = flask.request.get_json()
        if not "audio" in json_data:
            return flask.abort(code=400, message="No audio provided")

        audio = util.convertion.json_dict_to_ndarray(json_data.pop("audio"))
        result = self.transcriber.transcribe(audio=audio, **json_data)

        return flask.Response(response=json.dumps(result), status=200, mimetype="application/json")
