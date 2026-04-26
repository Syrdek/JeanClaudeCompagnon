import json
from typing import List

import flask

import util.convertion
from util.config import Config
from services.ocr import Ocr


class OcrServer(object):
    """
    Flask HTTP server endpoint for optical character recognition.
    """
    config: Config
    ocr: Ocr

    def __init__(self, app: flask.Flask, ocr: Ocr, root_path: str = "/ocr"):
        """
        Construct an OcrServer and register the read endpoint.

        :param app: The Flask application instance.
        :param ocr: The OCR engine to use for text extraction.
        :param root_path: URL prefix for the OCR endpoint.
        """
        self.app = app
        self.ocr = ocr
        self.root_path = root_path
        self.app.add_url_rule(rule=f"{root_path}/read", methods=["POST"], view_func=self.read)

    def read(self):
        """
        Handle a POST request to extract text from an image.

        Expects a JSON body with an "img" field containing a base64-encoded image.
        Returns a JSON response with the detected text regions.

        :return: Flask JSON response with the OCR result data.
        """
        json_data = flask.request.get_json()
        if not "img" in json_data:
            return flask.abort(code=400, message="No image provided")

        img = util.convertion.base64_to_pil(json_data.pop("img"))
        data: List[List[str]] = self.ocr.read(img=img, **json_data)

        return flask.Response(response=json.dumps(data), status=200, mimetype="application/json")
