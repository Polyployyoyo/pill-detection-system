import os
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API base URL from environment variable with a sensible default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class DetectAPI:
    """Client service for interacting with the /detect endpoint.

    Example:
        api = DetectAPI()
        result = api.detect_image("path/to/image.jpg")
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize DetectAPI client.

        Args:
            base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.
        """
        effective_base_url = base_url or API_BASE_URL
        self.base_url = effective_base_url.rstrip("/")
        self.detect_endpoint = f"{self.base_url}/detect"

    def detect_image(self, image_path: str) -> Dict[str, Any]:
        """Send an image file to the /detect endpoint for object detection.

        Args:
            image_path: Path to the image file to upload.

        Returns:
            A dictionary containing detection results from the server.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            with open(image_path, "rb") as image_file:
                files = {"file": image_file}
                response = requests.post(self.detect_endpoint, files=files)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data: Dict[str, Any] = {}
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": str(e)}

            raise requests.RequestException(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}"
            )
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")


# Convenience function for direct usage


def detect_image(image_path: str, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to detect objects in an image.

    Args:
        image_path: Path to the image file to upload.
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        A dictionary containing detection results from the server.
    """
    api = DetectAPI(base_url=base_url)
    return api.detect_image(image_path)
