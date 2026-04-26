import logging
import threading
import time

from baidubce.services.aihc.modules import service
from flask import Flask
from werkzeug.serving import make_server

from config.util import Config

logger = logging.getLogger(__name__)
app = Flask("jcc-server")

class BackgroundServer(threading.Thread):
    def __init__(self,
                 app,
                 host="127.0.0.1",
                 port=11111,
                 services=[]):

        super().__init__(daemon=True)
        logger.info(f"Creating server on {host}:{port} for services {services}")
        self.server = make_server(host, port, app)
        self.ctx = app.app_context()
        self.ctx.push()
        self.services = services

        for service in self.services:


    def run(self):
        logger.info(f"Starting server")
        self.server.serve_forever()

    def stop(self):
        logger.info(f"Stopping server")
        self.server.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    config = Config()

    BackgroundServer(app,
                     host=config("expose", "host", default="localhost"),
                     port=config("expose", "port", default=11111),
                     services=config("expose", "services", default=)).start()

    while True:
        time.sleep(1)