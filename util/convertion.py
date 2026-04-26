import base64
import io

import numpy
from PIL import Image

def pil_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """
    Encode an image to a base64 string.

    :param img: The image to encode.
    :param format: The image format.
    :return: The base64 encoded image string.
    """
    buf = io.BytesIO()
    img.save(buf, format=format)
    return base64.b64encode(buf.getvalue()).decode("utf8")

def base64_to_pil(data: str) -> Image.Image:
    """
    Decode a base64 encoded image string to a PIL Image.

    :param data: The base64 encoded image string.
    :return: The decoded PIL Image.
    """
    img_bytes = base64.b64decode(data)
    return Image.open(io.BytesIO(img_bytes))

def ndarray_to_json_dict(arr: numpy.ndarray) -> dict:
    """
    Serialize a numpy ndarray to a JSON-compatible dictionary.

    :param arr: The numpy array to serialize.
    :return: Dictionary with base64-encoded data, dtype, and shape.
    """
    return {
        "data": base64.b64encode(arr.tobytes()).decode("ascii"),
        "dtype": str(arr.dtype),
        "shape": arr.shape,
    }

def json_dict_to_ndarray(obj: dict) -> numpy.ndarray:
    """
    Deserialize a JSON-compatible dictionary back to a numpy ndarray.

    :param obj: Dictionary containing base64-encoded data, dtype, and shape.
    :return: The reconstructed numpy array.
    """
    raw = base64.b64decode(obj["data"])
    arr = numpy.frombuffer(raw, dtype=numpy.dtype(obj["dtype"]))
    return arr.reshape(obj["shape"])


if __name__ == "__main__":
    a = numpy.ndarray((10, 10))
    print(a)
    b = ndarray_to_json_dict(a)
    print(b)
    c = json_dict_to_ndarray(b)
    print(c)