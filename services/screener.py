

import logging
import typing
from typing import Tuple, NoReturn

from PIL import Image
from mss import mss
from mss.base import MSSBase

from config.util import Config

logger = logging.getLogger(__name__)

class Screener(object):
    """
    Captures screenshots of the entire display or a specific region.
    """
    @staticmethod
    def from_config(config: Config) -> "Screener":
        logger.info("Creating screenshot maker")
        return Screener(config("pixel_sensibility", default=0))

    def __init__(self, pixel_sensibility=0):
        """
        Construct a Screener instance.

        :param pixel_sensibility: minimum width and height (in pixels) below which a region is considered too small and the full display is captured instead.
        """
        self.last_region = None
        self.pixel_sensibility = pixel_sensibility


    @staticmethod
    def _get_full_display_size(screener: MSSBase) -> typing.Dict[str, int]:
        """
        Compute a bounding region that covers all connected monitors.

        :param screener: MSS instance used to query monitor information
        :return: dict with left, top, width, and height keys describing the bounding region
        """
        monitors = screener.monitors
        left = monitors[0]["left"]
        top = monitors[0]["top"]
        width = monitors[0]["width"]
        height = monitors[0]["height"]
        for i in range(1, len(monitors)):
            left = min(left, monitors[i]["left"])
            top = min(top, monitors[i]["top"])
            width = max(width, monitors[i]["width"])
            height = max(height, monitors[i]["height"])
        return {"left": left, "top": top, "width": width, "height": height}


    def _get_region(self,
                    screener: MSSBase, from_pos: tuple[int, int] | None,
                    to_pos: tuple[int, int] | None) -> dict[str, int]:
        """
        Determine the capture region from two corner positions, or fall back to the full display.

        :param screener: MSS instance used to query monitor information
        :param from_pos: top-left corner coordinates, or None to capture the full display
        :param to_pos: bottom-right corner coordinates, or None to capture the full display
        :return: dict with left, top, width, and height keys describing the capture region
        """
        if from_pos is None or to_pos is None:
            return Screener._get_full_display_size(screener)

        region = {
            "left": min(from_pos[0], to_pos[0]),
            "top": min(from_pos[1], to_pos[1]),
            "right": max(from_pos[0], to_pos[0]),
            "bottom": max(from_pos[1], to_pos[1])
        }
        region["width"] = region["right"] - region["left"]
        region["height"] = region["bottom"] - region["top"]

        if region["width"] < self.pixel_sensibility and region["height"] < self.pixel_sensibility:
            return Screener._get_full_display_size(screener)
        return region


    def screenshot(self, from_pos: Tuple[int, int] = None, to_pos: Tuple[int, int] = None) -> Image.Image:
        """
        Capture a screenshot of the specified region, or the entire display if no positions are given.

        :param from_pos: top-left corner coordinates of the region to capture
        :param to_pos: bottom-right corner coordinates of the region to capture
        :return: PIL Image of the captured screen area
        """
        with mss() as screener:
            region = self._get_region(screener, from_pos, to_pos)
            logging.debug(f"Capturing region {region}...")
            sct_img = screener.grab(region)
            return Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")


if __name__ == '__main__':
    screen = Screener(pixel_sensibility=10)
    screen.screenshot((30, 30), (100, 100)).save("potion_craft.png")
