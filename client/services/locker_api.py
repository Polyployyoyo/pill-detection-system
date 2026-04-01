import os
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API base URL from environment variable with a sensible default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class LockerAPI:
    """Client service for interacting with the /lockers endpoints.

    Example:
        api = InventoryAPI()
        inventories = api.get_lockers()
    """

    def __init__(self, base_url: Optional[str] = None) -> None:
        """Initialize InventoryAPI client.

        Args:
            base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.
        """
        effective_base_url = base_url or API_BASE_URL
        self.base_url = effective_base_url.rstrip("/")
        self.lockers_endpoint = f"{self.base_url}/lockers"

    def get_lockers(self, keyword: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all locker inventories from the server.

        Returns:
            A list of inventory dictionaries.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            params = {"keyword": keyword} if keyword and keyword.strip() else None
            response = requests.get(self.lockers_endpoint, params=params)
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

    def get_lockers_by_drug_id(self, drug_id: int) -> List[Dict[str, Any]]:
        """Get inventories for a specific drug ID.

        Args:
            drug_id: The ID of the drug.

        Returns:
            A list of inventory dictionaries for the given drug.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            url = f"{self.lockers_endpoint}/drug/{drug_id}"
            response = requests.get(url)

            if response.status_code == 404:
                return []

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_data: Dict[str, Any] = {}
            try:
                error_data = response.json()
            except Exception:
                error_data = {"message": str(e)}

            if response.status_code == 404:
                return []

            raise requests.RequestException(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}"
            )
        except requests.exceptions.RequestException as e:
            raise requests.RequestException(f"Request failed: {str(e)}")

    def add_quantity(
        self, locker_id: int, drug_id: int, quantity: int
    ) -> Dict[str, Any]:
        """Increase quantity for a specific drug in locker.

        Args:
            drug_id: The ID of the drug record to update.
            quantity: The quantity to add.

        Returns:
            The updated inventory record as a dictionary.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            url = f"{self.lockers_endpoint}/{locker_id}/drug/{drug_id}/add/{quantity}"
            response = requests.put(url)

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

    def subtract_quantity(
        self, locker_id: int, drug_id: int, quantity: int
    ) -> Dict[str, Any]:
        """Decrease quantity for a specific drug in locker.

        Args:
            drug_id: The ID of the drug record to update.
            quantity: The quantity to subtract.

        Returns:
            The updated inventory record as a dictionary.

        Raises:
            requests.RequestException: If the request fails.
        """
        try:
            url = f"{self.lockers_endpoint}/{locker_id}/drug/{drug_id}/subtract/{quantity}"
            response = requests.put(url)

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

    def transfer_quantity(
        self,
        source_locker_id: int,
        destination_locker_id: int,
        drug_id: int,
        quantity: int,
    ) -> Dict[str, Any]:
        """Transfer quantity between lockers for the same drug."""
        payload = {
            "source_locker_id": source_locker_id,
            "destination_locker_id": destination_locker_id,
            "drug_id": drug_id,
            "quantity": quantity,
        }

        try:
            url = f"{self.lockers_endpoint}/transfer"
            response = requests.put(url, json=payload)
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


def get_lockers(
    keyword: Optional[str] = None, base_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Convenience function to get all drug inventories.

    Args:
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        A list of inventory dictionaries.
    """
    api = LockerAPI(base_url=base_url)
    return api.get_lockers(keyword=keyword)


def get_lockers_by_drug_id(
    drug_id: int, base_url: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Convenience function to get inventories by drug ID.

    Args:
        drug_id: The ID of the drug.
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        A list of inventory dictionaries for the given drug.
    """
    api = LockerAPI(base_url=base_url)
    return api.get_lockers_by_drug_id(drug_id)


def add_quantity(
    locker_id: int, drug_id: int, quantity: int, base_url: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to increase drug quantity in locker.

    Args:
        drug_id: The ID of the drug record to update.
        quantity: The quantity to add.
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        The updated inventory record as a dictionary.
    """
    api = LockerAPI(base_url=base_url)
    return api.add_quantity(locker_id, drug_id, quantity)


def subtract_quantity(
    locker_id: int, drug_id: int, quantity: int, base_url: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function to decrease drug quantity in locker.

    Args:
        drug_id: The ID of the drug record to update.
        quantity: The quantity to subtract.
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        The updated inventory record as a dictionary.
    """
    api = LockerAPI(base_url=base_url)
    return api.subtract_quantity(locker_id, drug_id, quantity)


def transfer_quantity(
    source_locker_id: int,
    destination_locker_id: int,
    drug_id: int,
    quantity: int,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Convenience function to transfer stock between two lockers."""
    api = LockerAPI(base_url=base_url)
    return api.transfer_quantity(
        source_locker_id=source_locker_id,
        destination_locker_id=destination_locker_id,
        drug_id=drug_id,
        quantity=quantity,
    )
