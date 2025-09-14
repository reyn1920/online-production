import os
import requests
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from .base_api import BaseAPI, APIError, RateLimitError

logger = logging.getLogger(__name__)


class GuardianAPI(BaseAPI):
    """Guardian API integration for free news content"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Guardian API client

        Args:
            api_key: Guardian API key. If not provided, will try to get from environment
        """
        super().__init__()
        self.api_key = api_key or os.getenv("GUARDIAN_API_KEY")
        self.base_url = "https://content.guardianapis.com"
        self.name = "Guardian"
        self.category = "News"

        if not self.api_key:
            logger.warning("Guardian API key not provided. API access will not work.")

    def get_params(self, **kwargs) -> Dict[str, Any]:
        """Get base parameters for API requests"""
        params = {"api - key": self.api_key}
        params.update(kwargs)
        return params

    def search_content(
        self,
        query: str = None,
        section: str = None,
        page_size: int = 10,
        page: int = 1,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Search for content

        Args:
            query: Search query
            section: Section filter (e.g., 'technology', 'business')
            page_size: Number of results per page (max 50)
            page: Page number
            **kwargs: Additional parameters (from - date, to - date, order - by, etc.)

        Returns:
            Dict containing search results
        """
        if not self.api_key:
            raise APIError("Guardian API key not configured")

        url = f"{self.base_url}/search"

        params = self.get_params(
            **kwargs,
            **({"q": query} if query else {}),
            **({"section": section} if section else {}),
            **{"page - size": min(page_size, 50)},  # API limit
            **{"page": page},
        )

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("Guardian API rate limit exceeded")
            elif response.status_code == 403:
                raise APIError("Guardian API access forbidden - check API key")
            elif response.status_code != 200:
                raise APIError(f"Guardian API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_sections(self) -> Dict[str, Any]:
        """
        Get available sections

        Returns:
            Dict containing available sections
        """
        if not self.api_key:
            raise APIError("Guardian API key not configured")

        url = f"{self.base_url}/sections"

        try:
            response = requests.get(url, params=self.get_params())

            if response.status_code == 429:
                raise RateLimitError("Guardian API rate limit exceeded")
            elif response.status_code == 403:
                raise APIError("Guardian API access forbidden - check API key")
            elif response.status_code != 200:
                raise APIError(f"Guardian API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_tags(self, query: str = None, page_size: int = 10, page: int = 1) -> Dict[str, Any]:
        """
        Get available tags

        Args:
            query: Tag search query
            page_size: Number of results per page (max 50)
            page: Page number

        Returns:
            Dict containing available tags
        """
        if not self.api_key:
            raise APIError("Guardian API key not configured")

        url = f"{self.base_url}/tags"

        params = self.get_params(
            **({"q": query} if query else {}),
            **{"page - size": min(page_size, 50)},  # API limit
            **{"page": page},
        )

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("Guardian API rate limit exceeded")
            elif response.status_code == 403:
                raise APIError("Guardian API access forbidden - check API key")
            elif response.status_code != 200:
                raise APIError(f"Guardian API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_content_by_id(self, content_id: str, show_fields: str = "all") -> Dict[str, Any]:
        """
        Get specific content by ID

        Args:
            content_id: Content ID (e.g., 'technology/2023/jan/01/article - title')
            show_fields: Fields to include (e.g., 'body,headline,byline')

        Returns:
            Dict containing content details
        """
        if not self.api_key:
            raise APIError("Guardian API key not configured")

        url = f"{self.base_url}/{content_id}"

        params = self.get_params(**{"show - fields": show_fields})

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("Guardian API rate limit exceeded")
            elif response.status_code == 403:
                raise APIError("Guardian API access forbidden - check API key")
            elif response.status_code == 404:
                raise APIError(f"Content with ID '{content_id}' not found")
            elif response.status_code != 200:
                raise APIError(f"Guardian API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_latest_news(self, section: str = None, page_size: int = 10) -> Dict[str, Any]:
        """
        Get latest news articles

        Args:
            section: Section filter (optional)
            page_size: Number of results (max 50)

        Returns:
            Dict containing latest news
        """
        return self.search_content(section=section, page_size=page_size, **{"order - by": "newest"})

    def search_by_topic(self, topic: str, page_size: int = 10) -> Dict[str, Any]:
        """
        Search articles by topic/keyword

        Args:
            topic: Topic to search for
            page_size: Number of results (max 50)

        Returns:
            Dict containing search results
        """
        return self.search_content(query=topic, page_size=page_size, **{"order - by": "relevance"})

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
                "Content search",
                "Section listing",
                "Tag search",
                "Content by ID",
                "Latest news",
            ],
            "rate_limits": "5,000 calls per day for free tier",
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

            # Test with a simple sections request
            result = self.get_sections()

            return {
                "success": True,
                "message": "Connection successful",
                "sections_available": len(result.get("response", {}).get("results", [])),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
