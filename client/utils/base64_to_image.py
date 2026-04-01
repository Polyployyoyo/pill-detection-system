import io
import base64
import numpy as np
from typing import Union
from PIL import Image


def base64_to_image(
    base64_string: str, return_format: str = "PIL"
) -> Union[Image.Image, np.ndarray]:
    """
    Convert base64 encoded string to image.

    Args:
        base64_string: Base64 encoded image string (with or without data URL prefix)
        return_format: Format to return image in. Options: "PIL" (default) or "numpy"

    Returns:
        PIL Image object if return_format="PIL", or numpy array if return_format="numpy"

    Example:
        # Convert base64 to PIL Image
        img = base64_to_image(base64_str, return_format="PIL")

        # Convert base64 to numpy array (for OpenCV)
        img_array = base64_to_image(base64_str, return_format="numpy")
    """
    # Remove data URL prefix if present (e.g., "data:image/jpeg;base64,")
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]

    # Decode base64 string to bytes
    image_bytes = base64.b64decode(base64_string)

    # Convert bytes to image
    image = Image.open(io.BytesIO(image_bytes))

    if return_format == "numpy":
        # Convert PIL Image to numpy array (RGB format)
        return np.array(image)
    else:
        # Return PIL Image
        return image


def base64_to_image_file(base64_string: str, output_path: str) -> None:
    """
    Convert base64 encoded string to image and save to file.

    Args:
        base64_string: Base64 encoded image string (with or without data URL prefix)
        output_path: Path where the image file should be saved

    Example:
        base64_to_image_file(base64_str, "output.jpg")
    """
    image = base64_to_image(base64_string, return_format="PIL")
    image.save(output_path)
