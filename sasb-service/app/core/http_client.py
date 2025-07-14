import httpx
from typing import Any, Dict, Optional

class HttpApiClient:
    """
    A simple asynchronous HTTP client for making API requests.
    """
    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.headers = headers or {}

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Performs an asynchronous GET request.
        """
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers) as client:
            try:
                response = await client.get(endpoint, params=params)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Log the error or raise a custom exception
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                print(f"An error occurred while requesting {e.request.url!r}.")
                raise

    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Performs an asynchronous POST request.
        """
        async with httpx.AsyncClient(base_url=self.base_url, headers=self.headers) as client:
            try:
                response = await client.post(endpoint, json=json_data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                print(f"HTTP error occurred: {e.response.status_code} - {e.response.text}")
                raise
            except httpx.RequestError as e:
                print(f"An error occurred while requesting {e.request.url!r}.")
                raise 