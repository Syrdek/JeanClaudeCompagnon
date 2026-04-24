import json
import os
from typing import Dict, Any, List

import jsonmerge

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
            configuration = ["default-config.json", "config.json"]

        if isinstance(configuration, Dict):
            self.data = configuration
        else:
            self.data: Dict[str, Any] = {}

            for conf_file in configuration:
                if os.path.exists(conf_file):
                    with open(conf_file, "r") as f:
                        self.data = jsonmerge.merge(self.data, json.load(f))

    def __iter__(self):
        return iter(self.data)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        res = self.data.get(key, default)
        if isinstance(res, Dict):
            return Config(res)
        return res

    def __call__(self, *args: str, default: Any = None) -> Any:
        d = self.data
        for arg in args:
            if arg in d:
                d = d.get(arg)
            else:
                return default
        return d