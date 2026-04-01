import os
from typing import Dict, Any, Optional, List

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API base URL from environment variable with a sensible default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class LogAPI:
    """Client service for interacting with the /logs endpoints.

    Example:
        api = LogAPI()
        log = api.create_log(drug_id=1, detected_quantity=10, confidence=0.85)
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize LogAPI client.

        Args:
            base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.
        """
        effective_base_url = base_url or API_BASE_URL
        self.base_url = effective_base_url.rstrip("/")
        self.logs_endpoint = f"{self.base_url}/logs"

    def create_log(
        self, drug_id: int, detected_quantity: int, confidence: float
    ) -> Dict[str, Any]:
        """Create a new detection log entry.

        Args:
            drug_id: ID of the detected drug.
            detected_quantity: Detected quantity of pills.
            confidence: Average confidence score (0.0–1.0).

        Returns:
            The created log record as a dictionary.

        Raises:
            requests.RequestException: If the request fails.
        """
        payload = {
            "drug_id": drug_id,
            "detected_quantity": detected_quantity,
            "confidence": confidence,
        }

        try:
            response = requests.post(self.logs_endpoint, json=payload)
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

    def get_logs(self) -> List[Dict[str, Any]]:
        """Get all detection log entries.

        Returns:
            A list of log records.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            response = requests.get(self.logs_endpoint)
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

    def delete_log(self, log_id: int) -> Dict[str, Any]:
        """Delete a detection log entry by ID.

        Args:
            log_id: ID of the log to delete.

        Returns:
            The deleted log record as a dictionary.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            response = requests.delete(f"{self.logs_endpoint}/{log_id}")
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


def create_log(
    drug_id: int,
    detected_quantity: int,
    confidence: float,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to create a detection log.

    Args:
        drug_id: ID of the detected drug.
        detected_quantity: Detected quantity of pills.
        confidence: Average confidence score (0.0–1.0).
        base_url: Optional base URL override.

    Returns:
        The created log record as a dictionary.
    """
    api = LogAPI(base_url=base_url)
    return api.create_log(drug_id, detected_quantity, confidence)


def get_logs(base_url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Convenience function to get all detection logs.

    Args:
        base_url: Optional base URL override.

    Returns:
        A list of log records.
    """
    api = LogAPI(base_url=base_url)
    return api.get_logs()


def delete_log(log_id: int, base_url: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to delete a detection log by ID.

    Args:
        log_id: ID of the log to delete.
        base_url: Optional base URL override.

    Returns:
        The deleted log record as a dictionary.
    """
    api = LogAPI(base_url=base_url)
    return api.delete_log(log_id)
