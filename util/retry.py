import logging
from typing import List, Any

import requests

logger = logging.getLogger(__name__)

class MultipleUrlRemote(object):
    def __init__(self, url: str | List[str]):
        if isinstance(url, str):
            url = [url]

        if len(url) < 1:
            raise AttributeError("No URL provided")

        self.urls = url


    def use_first_responding_url(self, suffix: str, **kwargs) -> Any:
        error = AttributeError("No url was given")
        for url in self.urls:
            try:
                r = requests.request(url=url + suffix, **kwargs)
                r.raise_for_status()
                return r.json()
            except requests.exceptions.RequestException as e:
                error = e
                logger.warning(f"Remote server {url} failed : {str(e)}")
        raise error