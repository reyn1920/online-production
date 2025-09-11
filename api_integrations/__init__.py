# API Integrations Module
# Comprehensive integration layer for external services

from .arxiv_api import ArxivAPI
from .base_api import APIError, BaseAPI, RateLimitError
from .github_api import GitHubAPI
from .google_trends import GoogleTrendsAPI
from .reddit_api import RedditAPI
from .youtube_api import YouTubeAPI

__all__ = [
    "GoogleTrendsAPI",
        "RedditAPI",
        "GitHubAPI",
        "ArxivAPI",
        "YouTubeAPI",
        "BaseAPI",
        "APIError",
        "RateLimitError",
]
