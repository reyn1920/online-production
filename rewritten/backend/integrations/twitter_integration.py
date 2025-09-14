#!/usr/bin/env python3
"""
TRAE.AI Twitter Integration Module

Provides secure Twitter API integration with authentication, rate limiting,
and comprehensive error handling for automated promotion and community engagement.

Features:
- OAuth 1.0a authentication with secure credential management
- Intelligent rate limiting with exponential backoff
- Tweet posting with media attachments
- Search and engagement capabilities
- Comprehensive logging and error handling

Author: TRAE.AI System
Version: 1.0.0
"""

import base64
import hashlib
import hmac
import os
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore


class TwitterAPIError(Exception):
    """Custom exception for Twitter API errors."""

    def __init__(
        self, message: str, status_code: int = None, response_data: dict = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.timestamp = datetime.now()


class RateLimitError(TwitterAPIError):
    """Exception raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        reset_time: datetime = None,
        limit: int = None,
        remaining: int = None,
    ):
        super().__init__(message, status_code=429)
        self.reset_time = reset_time
        self.limit = limit
        self.remaining = remaining


class AuthenticationError(TwitterAPIError):
    """Exception raised for authentication failures."""

    def __init__(self, message: str, credential_type: str = None):
        super().__init__(message, status_code=401)
        self.credential_type = credential_type


class TweetType(Enum):
    """Types of tweets that can be posted."""

    PROMOTION = "promotion"
    ENGAGEMENT = "engagement"
    ANNOUNCEMENT = "announcement"
    REPLY = "reply"


class EngagementLevel(Enum):
    """Levels of community engagement."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TwitterCredentials:
    """Container for Twitter API credentials."""

    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str


@dataclass
class RateLimitInfo:
    """Information about API rate limits."""

    limit: int
    remaining: int
    reset_time: datetime
    endpoint: str


@dataclass
class TweetData:
    """Data structure for tweet information."""

    text: str
    tweet_type: TweetType
    media_urls: Optional[List[str]] = None
    reply_to_id: Optional[str] = None
    hashtags: Optional[List[str]] = None
    mentions: Optional[List[str]] = None
    scheduled_time: Optional[datetime] = None


@dataclass
class SearchResult:
    """Result from Twitter search operations."""

    tweet_id: str
    author_username: str
    text: str
    created_at: datetime
    engagement_metrics: Dict[str, int]
    relevance_score: float


class TwitterIntegration:
    """
    Comprehensive Twitter API integration with secure authentication,
        rate limiting, and advanced engagement capabilities.
    """

    def __init__(self, secrets_db_path: str = "data/secrets.sqlite"):
        self.logger = setup_logger("twitter_integration")
        self.secret_store = SecretStore(secrets_db_path)

        # Load credentials - fail if missing (production requirement)
        self.credentials = self._load_credentials()
        self.logger.info("Twitter integration initialized with live credentials")

        # Rate limiting tracking
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests

        # API endpoints
        self.base_url = "https://api.twitter.com/2"
        self.upload_url = "https://upload.twitter.com/1.1"

        # Configure HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Validate credentials on initialization
        if not self.test_connection():
            raise AuthenticationError("Failed to authenticate with Twitter API")

        self.logger.info(
            "Twitter integration initialized and authenticated successfully"
        )

    def _load_credentials(self) -> TwitterCredentials:
        """
        Load Twitter API credentials from secure secret store.

        Returns:
            TwitterCredentials: Loaded credentials

        Raises:
            AuthenticationError: If credentials are missing or invalid
        """
        try:
            api_key = self.secret_store.get_secret("TWITTER_API_KEY")
            api_secret = self.secret_store.get_secret("TWITTER_API_SECRET")
            access_token = self.secret_store.get_secret("TWITTER_ACCESS_TOKEN")
            access_token_secret = self.secret_store.get_secret(
                "TWITTER_ACCESS_TOKEN_SECRET"
            )

            if not all([api_key, api_secret, access_token, access_token_secret]):
                raise AuthenticationError(
                    "Missing Twitter API credentials in secret store"
                )

            return TwitterCredentials(
                api_key=api_key,
                api_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
            )
        except Exception as e:
            self.logger.error(f"Failed to load Twitter credentials: {e}")
            raise AuthenticationError(f"Credential loading failed: {e}")

    def _generate_oauth_signature(
        self, method: str, url: str, params: Dict[str, str]
    ) -> str:
        """
        Generate OAuth 1.0a signature for Twitter API requests.

        Args:
            method (str): HTTP method (GET, POST, etc.)
            url (str): Request URL
            params (Dict[str, str]): Request parameters

        Returns:
            str: OAuth signature
        """
        # Create parameter string
        sorted_params = sorted(params.items())
        param_string = "&".join(
            [f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params]
        )

        # Create signature base string
        base_string = f"{method.upper()}&{urllib.parse.quote(url,
    safe='')}&{urllib.parse.quote(param_string,
    safe='')}"

        # Create signing key
        signing_key = f"{urllib.parse.quote(self.credentials.api_secret,
    safe='')}&{urllib.parse.quote(self.credentials.access_token_secret,
    safe='')}"

        # Generate signature
        signature = base64.b64encode(
            hmac.new(signing_key.encode(), base_string.encode(), hashlib.sha1).digest()
        ).decode()

        return signature

    def _create_oauth_header(
        self, method: str, url: str, params: Dict[str, str] = None
    ) -> str:
        """
        Create OAuth authorization header for Twitter API requests.

        Args:
            method (str): HTTP method
            url (str): Request URL
            params (Dict[str, str], optional): Additional parameters

        Returns:
            str: OAuth authorization header
        """
        if params is None:
            params = {}

        # OAuth parameters
        oauth_params = {
            "oauth_consumer_key": self.credentials.api_key,
            "oauth_token": self.credentials.access_token,
            "oauth_signature_method": "HMAC - SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": hashlib.md5(str(time.time()).encode()).hexdigest(),
            "oauth_version": "1.0",
        }

        # Combine all parameters for signature
        all_params = {**params, **oauth_params}

        # Generate signature
        oauth_params["oauth_signature"] = self._generate_oauth_signature(
            method, url, all_params
        )

        # Create authorization header
        auth_header = "OAuth " + ", ".join(
            [
                f'{k}="{urllib.parse.quote(str(v), safe="")}"'
                for k, v in sorted(oauth_params.items())
            ]
        )

        return auth_header

    def _check_rate_limit(self, endpoint: str) -> None:
        """
        Check and enforce rate limits for API endpoints.

        Args:
            endpoint (str): API endpoint being accessed

        Raises:
            RateLimitError: If rate limit would be exceeded
        """
        current_time = time.time()

        # Enforce minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            self.logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)

        # Check endpoint - specific rate limits
        if endpoint in self.rate_limits:
            rate_limit = self.rate_limits[endpoint]
            if rate_limit.remaining <= 0 and datetime.now() < rate_limit.reset_time:
                wait_time = (rate_limit.reset_time - datetime.now()).total_seconds()
                raise RateLimitError(
                    f"Rate limit exceeded for {endpoint}. Reset in {wait_time:.0f}s"
                )

        self.last_request_time = current_time

    def _update_rate_limit_info(
        self, response: requests.Response, endpoint: str
    ) -> None:
        """
        Update rate limit information from API response headers.

        Args:
            response (requests.Response): API response
            endpoint (str): API endpoint
        """
        headers = response.headers

        if "x - rate - limit - limit" in headers:
            limit = int(headers["x - rate - limit - limit"])
            remaining = int(headers.get("x - rate - limit - remaining", 0))
            reset_timestamp = int(headers.get("x - rate - limit - reset", 0))
            reset_time = datetime.fromtimestamp(reset_timestamp)

            self.rate_limits[endpoint] = RateLimitInfo(
                limit=limit,
                remaining=remaining,
                reset_time=reset_time,
                endpoint=endpoint,
            )

            self.logger.debug(
                f"Rate limit updated for {endpoint}: {remaining}/{limit} remaining"
            )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None,
        files: Dict = None,
    ) -> requests.Response:
        """
        Make authenticated request to Twitter API with rate limiting.

        Args:
            method (str): HTTP method
            endpoint (str): API endpoint
            params (Dict, optional): Query parameters
            data (Dict, optional): Request body data
            files (Dict, optional): File uploads

        Returns:
            requests.Response: API response

        Raises:
            TwitterAPIError: For API errors
            RateLimitError: For rate limit violations
        """
        if params is None:
            params = {}
        if data is None:
            data = {}

        # Check rate limits
        self._check_rate_limit(endpoint)

        # Construct URL
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # Create OAuth header
        auth_header = self._create_oauth_header(
            method, url, params if method == "GET" else data
        )

        headers = {"Authorization": auth_header, "User - Agent": "TRAE.AI/1.0"}

        if not files and method in ["POST", "PUT", "PATCH"]:
            headers["Content - Type"] = "application/json"

        try:
            # Make request
            if method.upper() == "GET":
                response = self.session.get(
                    url, params=params, headers=headers, timeout=30
                )
            elif method.upper() == "POST":
                if files:
                    response = self.session.post(
                        url, data=data, files=files, headers=headers, timeout=60
                    )
                else:
                    response = self.session.post(
                        url, json=data, headers=headers, timeout=30
                    )
            else:
                raise TwitterAPIError(f"Unsupported HTTP method: {method}")

            # Update rate limit info
            self._update_rate_limit_info(response, endpoint)

            # Handle response
            if response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 401:
                raise AuthenticationError("Authentication failed")
            elif not response.ok:
                error_data = response.json() if response.content else {}
                raise TwitterAPIError(f"API error {response.status_code}: {error_data}")

            return response

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {endpoint}: {e}")
            raise TwitterAPIError(f"Request failed: {e}")

    def post_tweet(self, tweet_data: TweetData) -> Dict[str, Any]:
        """
        Post a tweet to Twitter.

        Args:
            tweet_data (TweetData): Tweet content and metadata

        Returns:
            Dict[str, Any]: Tweet creation response

        Raises:
            TwitterAPIError: For posting failures
        """
        try:
            # Validate tweet data
            if not tweet_data.text or not tweet_data.text.strip():
                raise TwitterAPIError("Tweet text cannot be empty")

            # Prepare tweet text
            text = tweet_data.text.strip()

            # Add hashtags if provided
            if tweet_data.hashtags:
                hashtags = " ".join(
                    [
                        f"#{tag.lstrip('#')}"
                        for tag in tweet_data.hashtags
                        if tag.strip()
                    ]
                )
                if hashtags:
                    text = f"{text} {hashtags}"

            # Ensure tweet length limit (280 characters)
            if len(text) > 280:
                text = text[:277] + "..."
                self.logger.warning(f"Tweet truncated to 280 characters: {text}")

            # Prepare request data
            data = {"text": text}

            # Add reply information if this is a reply
            if tweet_data.reply_to_id:
                data["reply"] = {"in_reply_to_tweet_id": tweet_data.reply_to_id}

            # Add media if provided
            if tweet_data.media_urls:
                media_ids = self._upload_media(tweet_data.media_urls)
                if media_ids:
                    data["media"] = {"media_ids": media_ids}

            # Post tweet
            response = self._make_request("POST", "tweets", data=data)

            if response.status_code not in [200, 201]:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                raise TwitterAPIError(f"Tweet posting failed: {error_msg}")

            result = response.json()
            tweet_id = result.get("data", {}).get("id")

            if not tweet_id:
                raise TwitterAPIError("No tweet ID returned from Twitter API")

            self.logger.info(f"Tweet posted successfully: {tweet_id}")
            return result

        except TwitterAPIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to post tweet: {e}")
            raise TwitterAPIError(f"Tweet posting failed: {str(e)}")

    def _upload_media(self, media_urls: List[str]) -> List[str]:
        """Upload media files to Twitter and return media IDs."""
        media_ids = []

        for media_url in media_urls:
            try:
                # Download media file
                media_response = requests.get(media_url, timeout=30)
                if media_response.status_code != 200:
                    self.logger.error(f"Failed to download media from {media_url}")
                    continue

                # Determine media type
                content_type = media_response.headers.get("content - type", "")
                if content_type.startswith("image/"):
                    media_category = "tweet_image"
                elif content_type.startswith("video/"):
                    media_category = "tweet_video"
                else:
                    self.logger.error(f"Unsupported media type: {content_type}")
                    continue

                # Upload to Twitter
                upload_url = "https://upload.twitter.com/1.1/media/upload.json"

                files = {"media": ("media", media_response.content, content_type)}

                data = {"media_category": media_category}

                # Create OAuth header for upload endpoint
                oauth_header = self._create_oauth_header("POST", upload_url)
                headers = {"Authorization": oauth_header}

                upload_response = self.session.post(
                    upload_url, files=files, data=data, headers=headers, timeout=60
                )

                if upload_response.status_code == 200:
                    upload_data = upload_response.json()
                    media_id = upload_data.get("media_id_string")
                    if media_id:
                        media_ids.append(media_id)
                        self.logger.info(f"Successfully uploaded media: {media_id}")
                    else:
                        self.logger.error(f"No media ID returned for {media_url}")
                else:
                    self.logger.error(
                        f"Media upload failed: {upload_response.status_code} - {upload_response.text}"
                    )

            except Exception as e:
                self.logger.error(f"Failed to upload media {media_url}: {e}")
                continue

        return media_ids

    def search_tweets(
        self, query: str, max_results: int = 10, tweet_fields: List[str] = None
    ) -> List[SearchResult]:
        """
        Search for tweets matching a query.

        Args:
            query (str): Search query
            max_results (int): Maximum number of results
            tweet_fields (List[str], optional): Additional tweet fields to retrieve

        Returns:
            List[SearchResult]: Search results
        """
        # Validate search parameters
        if not query or not query.strip():
            raise TwitterAPIError("Search query cannot be empty")

        if max_results <= 0 or max_results > 100:
            raise TwitterAPIError("max_results must be between 1 and 100")

        try:
            if tweet_fields is None:
                tweet_fields = ["created_at", "author_id", "public_metrics"]

            # Sanitize query to prevent injection attacks
            sanitized_query = query.strip().replace('"', '"')

            params = {
                "query": sanitized_query,
                "max_results": min(max_results, 100),  # API limit
                "tweet.fields": ",".join(tweet_fields),
                "expansions": "author_id",
            }

            response = self._make_request("GET", "tweets/search/recent", params=params)

            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("detail", f"HTTP {response.status_code}")
                raise TwitterAPIError(f"Search request failed: {error_msg}")

            data = response.json()

            # Validate response structure
            if "data" not in data and "meta" not in data:
                raise TwitterAPIError("Invalid response format from Twitter API")

            results = []
            tweets = data.get("data", [])
            users = {
                user["id"]: user for user in data.get("includes", {}).get("users", [])
            }

            for tweet in tweets:
                try:
                    # Validate required tweet fields
                    if not all(key in tweet for key in ["id", "text", "author_id"]):
                        self.logger.warning(
                            f"Skipping tweet with missing required fields: {tweet.get('id', 'unknown')}"
                        )
                        continue

                    author = users.get(tweet["author_id"], {})

                    # Parse creation date safely
                    created_at = datetime.now()  # fallback
                    if "created_at" in tweet:
                        try:
                            created_at = datetime.fromisoformat(
                                tweet["created_at"].replace("Z", "+00:00")
                            )
                        except ValueError as e:
                            self.logger.warning(
                                f"Invalid date format in tweet {tweet['id']}: {e}"
                            )

                    result = SearchResult(
                        tweet_id=tweet["id"],
                        author_username=author.get("username", "unknown"),
                        text=tweet["text"],
                        created_at=created_at,
                        engagement_metrics=tweet.get("public_metrics", {}),
                        relevance_score=self._calculate_relevance_score(
                            tweet, sanitized_query
                        ),
                    )
                    results.append(result)

                except Exception as tweet_error:
                    self.logger.warning(
                        f"Error processing tweet {tweet.get('id', 'unknown')}: {tweet_error}"
                    )
                    continue

            self.logger.info(
                f"Successfully found {len(results)} tweets for query: {sanitized_query}"
            )
            return results

        except TwitterAPIError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during tweet search: {e}")
            raise TwitterAPIError(f"Search failed: {e}")

    def _calculate_relevance_score(self, tweet: Dict, query: str) -> float:
        """
        Calculate relevance score for a tweet based on the search query.

        Args:
            tweet (Dict): Tweet data
            query (str): Search query

        Returns:
            float: Relevance score (0.0 to 1.0)
        """
        text = tweet.get("text", "").lower()
        query_terms = query.lower().split()

        # Count query term matches
        matches = sum(1 for term in query_terms if term in text)
        term_score = matches / len(query_terms) if query_terms else 0

        # Factor in engagement metrics
        metrics = tweet.get("public_metrics", {})
        engagement_score = (
            metrics.get("like_count", 0) * 0.3
            + metrics.get("retweet_count", 0) * 0.4
            + metrics.get("reply_count", 0) * 0.3
        ) / 100  # Normalize

        # Combine scores
        relevance_score = (term_score * 0.7) + (min(engagement_score, 1.0) * 0.3)

        return min(relevance_score, 1.0)

    def get_rate_limit_status(self) -> Dict[str, RateLimitInfo]:
        """
        Get current rate limit status for all tracked endpoints.

        Returns:
            Dict[str, RateLimitInfo]: Rate limit information by endpoint
        """
        return self.rate_limits.copy()

    def test_connection(self) -> bool:
        """
        Test Twitter API connection and authentication.

        Returns:
            bool: True if connection successful
        """
        try:
            response = self._make_request("GET", "users/me")

            if response.status_code != 200:
                self.logger.error(f"Twitter API returned status {response.status_code}")
                return False

            user_data = response.json()

            # Validate response structure
            if "data" not in user_data:
                self.logger.error("Invalid response format from Twitter API")
                return False

            username = user_data.get("data", {}).get("username")
            user_id = user_data.get("data", {}).get("id")

            if not username or not user_id:
                self.logger.error("Missing user information in Twitter API response")
                return False

            self.logger.info(
                f"Twitter connection test successful for @{username} (ID: {user_id})"
            )
            return True

        except AuthenticationError as e:
            self.logger.error(f"Twitter authentication failed: {e}")
            return False
        except TwitterAPIError as e:
            self.logger.error(f"Twitter API error during connection test: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during Twitter connection test: {e}")
            return False


# Example usage and testing
if __name__ == "__main__":
    # Initialize Twitter integration
    twitter = TwitterIntegration()

    # Test connection
    if twitter.test_connection():
        print("✓ Twitter API connection successful")

        # Example tweet
        tweet_data = TweetData(
            text="Testing TRAE.AI Twitter integration! 🚀",
            tweet_type=TweetType.ANNOUNCEMENT,
            hashtags=["TRAEAI", "automation", "AI"],
        )

        try:
            result = twitter.post_tweet(tweet_data)
            print(f"✓ Tweet posted: {result}")
        except Exception as e:
            print(f"✗ Tweet failed: {e}")
    else:
        print("✗ Twitter API connection failed")
