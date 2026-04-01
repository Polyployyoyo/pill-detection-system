import os

import requests
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables from .env file
load_dotenv()

# Get API base URL from environment variable with a sensible default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class DrugAPI:
    """
    Client service for interacting with the drug API endpoints.

    Example:
        api = DrugAPI(base_url="http://localhost:8000")
        all_drugs = api.get_drugs()
        drug = api.get_drug_by_id(1)
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize DrugAPI client.

        Args:
            base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.
        """
        # Use provided base_url if given, otherwise fall back to environment variable
        effective_base_url = base_url or API_BASE_URL
        self.base_url = effective_base_url.rstrip("/")
        self.drugs_endpoint = f"{self.base_url}/drugs"

    def get_drugs(self) -> List[Dict]:
        """
        Get all drugs from the server.

        Returns:
            List of drug dictionaries

        Raises:
            requests.RequestException: If the request fails

        Example:
            api = DrugAPI()
            drugs = api.get_drugs()
        """
        try:
            response = requests.get(self.drugs_endpoint)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (4xx, 5xx)
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"message": str(e)}
            raise requests.RequestException(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}"
            )
        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, etc.
            raise requests.RequestException(f"Request failed: {str(e)}")

    def get_drug_by_id(self, drug_id: int) -> Optional[Dict]:
        """
        Get a specific drug by ID from the server.

        Args:
            drug_id: The ID of the drug to retrieve

        Returns:
            Drug dictionary if found, None if not found

        Raises:
            requests.RequestException: If the request fails

        Example:
            api = DrugAPI()
            drug = api.get_drug_by_id(1)
        """
        try:
            response = requests.get(f"{self.drugs_endpoint}/{drug_id}")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors (4xx, 5xx)
            error_data = {}
            try:
                error_data = response.json()
            except:
                error_data = {"message": str(e)}

            if response.status_code == 404:
                return None

            raise requests.RequestException(
                f"HTTP {response.status_code}: {error_data.get('message', 'Unknown error')}"
            )
        except requests.exceptions.RequestException as e:
            # Handle connection errors, timeouts, etc.
            raise requests.RequestException(f"Request failed: {str(e)}")


# Convenience functions for direct usage
def get_drugs(base_url: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to get all drugs.

    Args:
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        List of drug dictionaries
    """
    api = DrugAPI(base_url=base_url)
    return api.get_drugs()


def get_drug_by_id(drug_id: int, base_url: Optional[str] = None) -> Optional[Dict]:
    """
    Convenience function to get a drug by ID.

    Args:
        drug_id: The ID of the drug to retrieve
        base_url: Optional base URL of the API server. If not provided, uses API_BASE_URL from .env.

    Returns:
        Drug dictionary if found, None if not found
    """
    api = DrugAPI(base_url=base_url)
    return api.get_drug_by_id(drug_id)
