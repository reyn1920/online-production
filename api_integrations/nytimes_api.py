import os
import requests
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from .base_api import BaseAPI, APIError, RateLimitError

logger = logging.getLogger(__name__)


class NYTimesAPI(BaseAPI):
    """New York Times API integration for news content"""

    def __init__(self, api_key: Optional[str] = None):
        """"""
        Initialize NY Times API client

        Args:
            api_key: NY Times API key. If not provided, will try to get from environment
        """"""
        super().__init__()
        self.api_key = api_key or os.getenv("NYTIMES_API_KEY")
        self.base_url = "https://api.nytimes.com/svc"
        self.name = "NY Times"
        self.category = "News"

        if not self.api_key:
            logger.warning("NY Times API key not provided. API access will not work.")

    def get_params(self, **kwargs) -> Dict[str, Any]:
        """Get base parameters for API requests"""
        params = {"api - key": self.api_key}
        params.update(kwargs)
        return params

    def search_articles(
        self, query: str, page: int = 0, sort: str = "newest", **kwargs
    ) -> Dict[str, Any]:
        """"""
        Search for articles using Article Search API

        Args:
            query: Search query
            page: Page number (0 - based)
            sort: Sort order ('newest', 'oldest', 'relevance')
            **kwargs: Additional parameters (begin_date, end_date, fq, etc.)

        Returns:
            Dict containing search results
        """"""
        if not self.api_key:
            raise APIError("NY Times API key not configured")

        url = f"{self.base_url}/search/v2/articlesearch.json"

        params = self.get_params(q=query, page=page, sort=sort, **kwargs)

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("NY Times API rate limit exceeded")
            elif response.status_code == 401:
                raise APIError("NY Times API authentication failed - check API key")
            elif response.status_code != 200:
                raise APIError(f"NY Times API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_top_stories(self, section: str = "home") -> Dict[str, Any]:
        """"""
        Get top stories from a specific section

        Args:
            section: Section name (e.g., 'home', 'world', 'business', 'technology')

        Returns:
            Dict containing top stories
        """"""
        if not self.api_key:
            raise APIError("NY Times API key not configured")

        url = f"{self.base_url}/topstories/v2/{section}.json"

        try:
            response = requests.get(url, params=self.get_params())

            if response.status_code == 429:
                raise RateLimitError("NY Times API rate limit exceeded")
            elif response.status_code == 401:
                raise APIError("NY Times API authentication failed - check API key")
            elif response.status_code == 404:
                raise APIError(f"Section '{section}' not found")
            elif response.status_code != 200:
                raise APIError(f"NY Times API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_most_popular(self, period: int = 1, share_type: str = "viewed") -> Dict[str, Any]:
        """"""
        Get most popular articles

        Args:
            period: Time period (1, 7, or 30 days)
            share_type: Type of popularity ('viewed', 'shared', 'emailed')

        Returns:
            Dict containing most popular articles
        """"""
        if not self.api_key:
            raise APIError("NY Times API key not configured")

        if period not in [1, 7, 30]:
            raise APIError("Period must be 1, 7, or 30 days")

        if share_type not in ["viewed", "shared", "emailed"]:
            raise APIError("Share type must be 'viewed', 'shared', or 'emailed'")

        url = f"{self.base_url}/mostpopular/v2/{share_type}/{period}.json"

        try:
            response = requests.get(url, params=self.get_params())

            if response.status_code == 429:
                raise RateLimitError("NY Times API rate limit exceeded")
            elif response.status_code == 401:
                raise APIError("NY Times API authentication failed - check API key")
            elif response.status_code != 200:
                raise APIError(f"NY Times API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_book_reviews(
        self, author: str = None, isbn: str = None, title: str = None
    ) -> Dict[str, Any]:
        """"""
        Get book reviews

        Args:
            author: Author name
            isbn: Book ISBN
            title: Book title

        Returns:
            Dict containing book reviews
        """"""
        if not self.api_key:
            raise APIError("NY Times API key not configured")

        if not any([author, isbn, title]):
            raise APIError("At least one of author, isbn, or title must be provided")

        url = f"{self.base_url}/books/v3/reviews.json"

        params = self.get_params()
        if author:
            params["author"] = author
        if isbn:
            params["isbn"] = isbn
        if title:
            params["title"] = title

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("NY Times API rate limit exceeded")
            elif response.status_code == 401:
                raise APIError("NY Times API authentication failed - check API key")
            elif response.status_code != 200:
                raise APIError(f"NY Times API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_movie_reviews(
        self, query: str = None, critics_pick: bool = None, offset: int = 0
    ) -> Dict[str, Any]:
        """"""
        Get movie reviews

        Args:
            query: Search query for movie title or reviewer
            critics_pick: Filter for critics' picks (True/False)'
            offset: Offset for pagination

        Returns:
            Dict containing movie reviews
        """"""
        if not self.api_key:
            raise APIError("NY Times API key not configured")

        url = f"{self.base_url}/movies/v2/reviews/search.json"

        params = self.get_params(offset=offset)
        if query:
            params["query"] = query
        if critics_pick is not None:
            params["critics - pick"] = "Y" if critics_pick else "N"

        try:
            response = requests.get(url, params=params)

            if response.status_code == 429:
                raise RateLimitError("NY Times API rate limit exceeded")
            elif response.status_code == 401:
                raise APIError("NY Times API authentication failed - check API key")
            elif response.status_code != 200:
                raise APIError(f"NY Times API error: {response.status_code} - {response.text}")

            return response.json()

        except requests.RequestException as e:
            raise APIError(f"Request failed: {str(e)}")

    def get_status(self) -> Dict[str, Any]:
        """"""
        Get API status and configuration

        Returns:
            Dict containing status information
        """"""
        return {
            "name": self.name,
            "category": self.category,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "features": [
                "Article search",
                "Top stories",
                "Most popular articles",
                "Book reviews",
                "Movie reviews",
# BRACKET_SURGEON: disabled
#             ],
            "available_sections": [
                "home",
                "world",
                "national",
                "politics",
                "business",
                "technology",
                "science",
                "health",
                "sports",
                "arts",
                "books",
                "movies",
                "theater",
                "fashion",
                "food",
                "travel",
                "magazine",
                "realestate",
                "automobiles",
# BRACKET_SURGEON: disabled
#             ],
            "rate_limits": "4,000 requests per day, 10 per minute",
            "last_checked": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def test_connection(self) -> Dict[str, Any]:
        """"""
        Test the API connection

        Returns:
            Dict containing test results
        """"""
        try:
            if not self.api_key:
                return {
                    "success": False,
                    "error": "API key not configured",
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

            # Test with a simple top stories request
            result = self.get_top_stories("home")

            return {
                "success": True,
                "message": "Connection successful",
                "stories_available": len(result.get("results", [])),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }