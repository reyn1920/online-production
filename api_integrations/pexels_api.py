import os
import requests
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from .base_api import BaseAPI, APIError, RateLimitError

logger = logging.getLogger(__name__)


class PexelsAPI(BaseAPI):
    """Pexels API integration for free stock photos and videos"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Pexels API client

        Args:
            api_key: Pexels API key. If not provided, will try to get from environment
        """
        super().__init__()
        self.api_key = api_key or os.getenv("PEXELS_API_KEY")
        self.base_url = "https://api.pexels.com/v1"
        self.name = "Pexels"
        self.category = "Media"

        if not self.api_key:
            logger.warning("Pexels API key not provided. API access will not work.")

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {"Authorization": self.api_key, "Content - Type": "application/json"}

    def search_photos(
        self, query: str, per_page: int = 15, page: int = 1, **kwargs
    ) -> Dict[str, Any]:
        """
        Search for photos

        Args:
            query: Search query
            per_page: Number of results per page (max 80)
            page: Page number
            **kwargs: Additional parameters (orientation, size, color, locale)

        Returns:
            Dict containing search results
        """
        if not self.api_key:
            raise APIError("Pexels API key not configured")

        url = f"{self.base_url}/search"

        params = {
            "query": query,
            "per_page": min(per_page, 80),  # API limit
            "page": page,
            **kwargs,
        }

        try:
            response = requests.get(url, params=params, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Pexels API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Pexels API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def search_videos(
        self, query: str, per_page: int = 15, page: int = 1, **kwargs
    ) -> Dict[str, Any]:
        """
        Search for videos

        Args:
            query: Search query
            per_page: Number of results per page (max 80)
            page: Page number
            **kwargs: Additional parameters (orientation, size, locale)

        Returns:
            Dict containing video search results
        """
        if not self.api_key:
            raise APIError("Pexels API key not configured")

        url = f"{self.base_url}/videos/search"

        params = {
            "query": query,
            "per_page": min(per_page, 80),  # API limit
            "page": page,
            **kwargs,
        }

        try:
            response = requests.get(url, params=params, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Pexels API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Pexels API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_curated_photos(self, per_page: int = 15, page: int = 1) -> Dict[str, Any]:
        """
        Get curated photos

        Args:
            per_page: Number of results per page (max 80)
            page: Page number

        Returns:
            Dict containing curated photos
        """
        if not self.api_key:
            raise APIError("Pexels API key not configured")

        url = f"{self.base_url}/curated"

        params = {"per_page": min(per_page, 80), "page": page}  # API limit

        try:
            response = requests.get(url, params=params, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Pexels API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Pexels API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_popular_videos(self, per_page: int = 15, page: int = 1) -> Dict[str, Any]:
        """
        Get popular videos

        Args:
            per_page: Number of results per page (max 80)
            page: Page number

        Returns:
            Dict containing popular videos
        """
        if not self.api_key:
            raise APIError("Pexels API key not configured")

        url = f"{self.base_url}/videos/popular"

        params = {"per_page": min(per_page, 80), "page": page}  # API limit

        try:
            response = requests.get(url, params=params, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Pexels API rate limit exceeded")
            elif response.status_code != 200:
                raise APIError(f"Pexels API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_photo_by_id(self, photo_id: int) -> Dict[str, Any]:
        """
        Get a specific photo by ID

        Args:
            photo_id: Photo ID

        Returns:
            Dict containing photo details
        """
        if not self.api_key:
            raise APIError("Pexels API key not configured")

        url = f"{self.base_url}/photos/{photo_id}"

        try:
            response = requests.get(url, headers=self.get_headers())

            if response.status_code == 429:
                raise RateLimitError("Pexels API rate limit exceeded")
            elif response.status_code == 404:
                raise APIError(f"Photo with ID {photo_id} not found")
            elif response.status_code != 200:
                raise APIError(f"Pexels API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get API status and configuration

        Returns:
            Dict containing status information
        """
        return {
            "name": self.name,
            "category": self.category,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "features": [
                "Photo search",
                "Video search",
                "Curated photos",
                "Popular videos",
                "Photo by ID",
            ],
            "rate_limits": "200 requests/hour for free accounts",
            "last_checked": datetime.now().isoformat(),
        }

    def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection

        Returns:
            Dict containing test results
        """
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "API key not configured",
                    "timestamp": datetime.now().isoformat(),
                }

            # Test with a simple curated photos request
            result = self.get_curated_photos(per_page=1)

            return {
                "success": True,
                "message": "Connection successful",
                "photos_available": len(result.get("photos", [])),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
