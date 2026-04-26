import json
from typing import List

import flask

import util.convertion
from util.config import Config
from services.ocr import Ocr


class OcrServer(object):
    config: Config
    ocr: Ocr

    def __init__(self, app: flask.Flask, ocr: Ocr, root_path: str = "/ocr"):
        self.app = app
        self.ocr = ocr
        self.root_path = root_path
        self.app.add_url_rule(rule=f"{root_path}/read", methods=["POST"], view_func=self.read)

    def read(self):
        json_data = flask.request.get_json()
        if not "img" in json_data:
            return flask.abort(code=400, message="No image provided")

        img = util.convertion.base64_to_pil(json_data.pop("img"))
        data: List[List[str]] = self.ocr.read(img=img, **json_data)

        return flask.Response(response=json.dumps(data), status=200, mimetype="application/json")
