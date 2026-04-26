import json
import os
from typing import Dict, Any, List

import jsonmerge
import pyjson5


class Config(object):
    """
    Application configuration.
    """
    def __init__(self, configuration: List[str] | Dict[str, Any] = None):
        """
        Creates a configuration by merging the given configuration files.
        :param configuration: The configurations to merge.
        """
        if not configuration:
            configuration = ["default-config.json5", "config.json5", "config.json"]

        if isinstance(configuration, Dict):
            self.data = configuration
        else:
            self.data: Dict[str, Any] = {}

            for conf_file in configuration:
                if os.path.exists(conf_file):
                    with open(conf_file, "r") as f:
                        self.data = jsonmerge.merge(self.data, pyjson5.load(f))

    def __iter__(self):
        """
        Iterate over the top-level keys in the configuration.

        :return: An iterator of the top-level keys.
        """
        return iter(self.data)

    def __getitem__(self, key: str) -> Any:
        """
        Retrieve a configuration value by its top-level key.

        :param key: The top-level key to retrieve.
        :return: The corresponding configuration value.
        """
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve a configuration value by key with an optional default.

        If the value is a dictionary, it is wrapped into a Config instance.

        :param key: The top-level key to retrieve.
        :param default: Default value to return if the key is absent.
        :return: The corresponding configuration value or the default.
        """
        res = self.data.get(key, default)
        if isinstance(res, Dict):
            return Config(res)
        return res

    def keys(self) -> List[str]:
        """
        Return the list of top-level configuration keys.

        :return: List of key names.
        """
        return list(self.data.keys())

    def json(self, *args, **kwargs) -> str:
        """
        Serialize the configuration data to a JSON string.

        :param args: Positional arguments forwarded to json.dumps.
        :param kwargs: Keyword arguments forwarded to json.dumps.
        :return: JSON string representation of the configuration.
        """
        return json.dumps(self.data, *args, **kwargs)

    def __call__(self, *args: str, default: Any = None) -> Any:
        """
        Navigate through nested configuration values using a sequence of keys.

        :param args: Sequence of nested keys to traverse.
        :param default: Default value to return if any key is absent.
        :return: The value found at the end of the path, or the default if a key is missing.
        """
        not_found = object()
        d = self
        for arg in args:
            d = d.get(arg, not_found)
            if d == not_found:
                return default
        return d