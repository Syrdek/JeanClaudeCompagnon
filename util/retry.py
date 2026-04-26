import logging
from typing import List, Any

import requests

logger = logging.getLogger(__name__)

class MultipleUrlRemote(object):
    """
    Utility class that tries multiple remote URLs and returns the first successful response.
    """

    def __init__(self, url: str | List[str]):
        """
        Construct a MultipleUrlRemote.

        :param url: A single URL string or a list of URL strings to try.
        """
        if isinstance(url, str):
            url = [url]

        if len(url) < 1:
            raise AttributeError("No URL provided")

        self.urls = url


    def use_first_responding_url(self, suffix: str, **kwargs) -> Any:
        """
        Send a request to each URL in order and return the first successful JSON response.

        :param suffix: URL path suffix to append to each base URL.
        :param kwargs: Additional keyword arguments forwarded to requests.request.
        :return: The JSON-decoded response from the first responding server.
        :raises requests.exceptions.RequestException: If all URLs fail.
        """
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