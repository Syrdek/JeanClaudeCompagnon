from typing import Any

import easyocr
import numpy
from PIL.Image import Image


class Ocr(object):
    """
    Optical character recognition wrapper around the EasyOCR engine.

    Supports French and English text extraction from images.
    """

    def __init__(self):
        """
        Construct an Ocr instance with a French/English EasyOCR reader.

        The reader uses locally stored models and does not download them.
        """
        self.ocr = easyocr.Reader(lang_list=["fr", "en"], model_storage_directory="models/easy_ocr", download_enabled=False)

    def read(self, img: Any, **kwargs) -> Any:
        """
        Extract text from the given image using OCR.

        If the input is a PIL Image, it is converted to a NumPy array
        before being passed to the OCR engine.

        :param img: Image to process (file path string, NumPy array, or PIL Image).
        :param kwargs: Additional keyword arguments forwarded to EasyOCR readtext.
        :return: List of detected text regions with bounding boxes and text.
        """
        if isinstance(img, Image):
            img = numpy.array(img)

        return self.ocr.readtext(img, paragraph=True, slope_ths=0.14, **kwargs)


if __name__ == "__main__":
    ocr = Ocr()
    res = ocr.read("tests/potion_craft_simple.png")
    print(res)
    res = ocr.read("tests/potion_craft.png")
    print(res)