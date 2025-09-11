# backend / integrations / news_adapter.py
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from utils.http import http_get_with_backoff

logger = logging.getLogger(__name__)
BASE = "http://localhost:8000"  # or internal import if same process
TIMEOUT_S = 15


def get_active_news_provider() -> Dict:
    """Get the currently active news provider from the registry."""
    try:
        r = requests.get(f"{BASE}/integrations / active / news", timeout = 10)
        r.raise_for_status()
        return r.json()["active"]
    except Exception as e:
        logger.error(f"Failed to get active news provider: {e}")
        raise


def _get_credentials(provider_key: str) -> Dict[str, str]:
    """Get credentials for a provider from environment or secret store."""
    # Try environment variables first
    creds = {}
    if provider_key == "newsapi":
        api_key = os.getenv("NEWSAPI_KEY")
        if api_key:
            creds["api_key"] = api_key
    elif provider_key == "guardian":
        api_key = os.getenv("GUARDIAN_API_KEY")
        if api_key:
            creds["api_key"] = api_key
    elif provider_key == "nytimes":
        api_key = os.getenv("NYTIMES_API_KEY")
        if api_key:
            creds["api_key"] = api_key

    # TODO: Add secret store fallback when available
    return creds


def _report_usage(
    provider_key: str,
        success: bool,
        error: Optional[str] = None,
        took_ms: Optional[int] = None,
        quota_remaining: Optional[int] = None,
):
    """Report usage metrics to the integrations registry."""
    try:
        payload = {"key": provider_key, "success": success, "took_ms": took_ms}
        if error:
            payload["error"] = str(error)[:300]  # Truncate long errors
        if quota_remaining is not None:
            payload["quota_remaining"] = quota_remaining

        requests.post(f"{BASE}/integrations / report", json = payload, timeout = 10)
    except Exception as e:
        logger.warning(f"Failed to report usage for {provider_key}: {e}")


def _fetch_newsapi_articles(
    query: str, limit: int, api_key: str, category: Optional[str] = None
) -> Dict[str, Any]:
    """Fetch articles from NewsAPI."""
    headers = {"X - API - Key": api_key}

    # Use different endpoint based on whether we have a query or category
    if query:
        url = "https://newsapi.org / v2 / everything"
        params = {
            "q": query,
                "pageSize": min(limit, 100),  # NewsAPI max is 100
            "sortBy": "publishedAt",
                "language": "en",
                }
    else:
        url = "https://newsapi.org / v2 / top - headlines"
        params = {"pageSize": min(limit, 100), "country": "us", "language": "en"}
        if category:
            params["category"] = category

    resp = http_get_with_backoff(url, headers = headers, params = params, timeout = TIMEOUT_S)

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        articles = []
        for article in data.get("articles", []):
            # Skip articles with removed content
            if article.get("title") == "[Removed]":
                continue

            articles.append(
                {
                    "id": article["url"],  # Use URL as ID
                    "title": article["title"],
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "url": article["url"],
                        "image_url": article.get("urlToImage"),
                        "published_at": article["publishedAt"],
                        "source": article["source"]["name"],
                        "author": article.get("author"),
                        "provider": "newsapi",
                        }
            )

        return {
            "success": True,
                "articles": articles,
                "total": data.get("totalResults", len(articles)),
                "quota_remaining": None,  # NewsAPI doesn't provide quota in response
        }
    else:
        return {
            "success": False,
                "error": f"NewsAPI error: {resp.status_code} - {resp.text[:200]}",
                }


def _fetch_guardian_articles(query: str, limit: int, api_key: str) -> Dict[str, Any]:
    """Fetch articles from The Guardian API."""
    params = {
        "api - key": api_key,
            "page - size": min(limit, 50),  # Guardian max is 50
        "show - fields": "thumbnail,trailText,body",
            "order - by": "newest",
            }

    if query:
        params["q"] = query

    resp = http_get_with_backoff(
        "https://content.guardianapis.com / search", params = params, timeout = TIMEOUT_S
    )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        articles = []
        for article in data["response"].get("results", []):
            fields = article.get("fields", {})
            articles.append(
                {
                    "id": article["id"],
                        "title": article["webTitle"],
                        "description": fields.get("trailText", ""),
                        "content": fields.get("body", ""),
                        "url": article["webUrl"],
                        "image_url": fields.get("thumbnail"),
                        "published_at": article["webPublicationDate"],
                        "source": "The Guardian",
                        "author": None,  # Guardian doesn't always provide author in this endpoint
                    "provider": "guardian",
                        }
            )

        return {
            "success": True,
                "articles": articles,
                "total": data["response"].get("total", len(articles)),
                "quota_remaining": None,
                }
    else:
        return {
            "success": False,
                "error": f"Guardian API error: {resp.status_code} - {resp.text[:200]}",
                }


def _fetch_nytimes_articles(query: str, limit: int, api_key: str) -> Dict[str, Any]:
    """Fetch articles from NY Times API."""
    params = {"api - key": api_key, "sort": "newest"}

    if query:
        params["q"] = query
        url = "https://api.nytimes.com / svc / search / v2 / articlesearch.json"
    else:
        # Use top stories if no query
        url = "https://api.nytimes.com / svc / topstories / v2 / home.json"

    resp = http_get_with_backoff(url, params = params, timeout = TIMEOUT_S)

    if resp.status_code == 200:
        data = resp.json()
        articles = []

        if query:
            # Article search response format
            docs = data["response"].get("docs", [])
            for doc in docs[:limit]:  # Limit results
                # Get the best image
                image_url = None
                multimedia = doc.get("multimedia", [])
                for media in multimedia:
                    if media.get("type") == "image":
                        image_url = f"https://www.nytimes.com/{media['url']}"
                        break

                articles.append(
                    {
                        "id": doc["_id"],
                            "title": doc["headline"]["main"],
                            "description": doc.get("abstract", ""),
                            "content": doc.get("lead_paragraph", ""),
                            "url": doc["web_url"],
                            "image_url": image_url,
                            "published_at": doc["pub_date"],
                            "source": "The New York Times",
                            "author": doc.get("byline", {}).get("original"),
                            "provider": "nytimes",
                            }
                )
        else:
            # Top stories response format
            results = data.get("results", [])
            for article in results[:limit]:  # Limit results
                # Get the best image
                image_url = None
                multimedia = article.get("multimedia", [])
                for media in multimedia:
                    if media.get("type") == "image":
                        image_url = media.get("url")
                        break

                articles.append(
                    {
                        "id": article["url"],
                            "title": article["title"],
                            "description": article.get("abstract", ""),
                            "content": "",  # Top stories don't include full content
                        "url": article["url"],
                            "image_url": image_url,
                            "published_at": article["published_date"],
                            "source": "The New York Times",
                            "author": article.get("byline"),
                            "provider": "nytimes",
                            }
                )

        return {
            "success": True,
                "articles": articles,
                "total": len(articles),  # NYT doesn't always provide total count
            "quota_remaining": None,
                }
    else:
        return {
            "success": False,
                "error": f"NY Times API error: {resp.status_code} - {resp.text[:200]}",
                }


def fetch_news(
    query: Optional[str] = None,
        limit: int = 10,
        category: Optional[str] = None,
        max_retries: int = 1,
) -> Dict[str, Any]:
    """Fetch news articles using the active provider with automatic failover."""
    start_time = time.time()

    for attempt in range(max_retries + 1):
        try:
            # Get active provider
            active = get_active_news_provider()
            provider_key = active["key"]

            logger.info(f"Fetching news from {provider_key} (attempt {attempt + 1})")

            # Get credentials
            creds = _get_credentials(provider_key)
            if active.get("needs_key", False) and not creds:
                error_msg = f"No credentials found for {provider_key}"
                _report_usage(
                    provider_key,
                        False,
                        error_msg,
                        int((time.time() - start_time) * 1000),
                        )
                return {"provider": provider_key, "ok": False, "error": error_msg}

            # Call appropriate provider
            result = None
            if provider_key == "newsapi" and "api_key" in creds:
                result = _fetch_newsapi_articles(
                    query or "", limit, creds["api_key"], category
                )
            elif provider_key == "guardian" and "api_key" in creds:
                result = _fetch_guardian_articles(query or "", limit, creds["api_key"])
            elif provider_key == "nytimes" and "api_key" in creds:
                result = _fetch_nytimes_articles(query or "", limit, creds["api_key"])
            else:
                result = {
                    "success": False,
                        "error": f"No adapter implementation for {provider_key}",
                        }

            took_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                # Success - report and return
                _report_usage(
                    provider_key, True, None, took_ms, result.get("quota_remaining")
                )
                return {
                    "provider": provider_key,
                        "ok": True,
                        "data": result["articles"],
                        "total": result.get("total", len(result["articles"])),
                        "took_ms": took_ms,
                        }
            else:
                # Failure - report and potentially rotate
                error_msg = result.get("error", "Unknown error")
                _report_usage(provider_key, False, error_msg, took_ms)

                # Try rotation if this is not the last attempt
                if attempt < max_retries:
                    try:
                        logger.info(f"Rotating from failed provider {provider_key}")
                        rotate_resp = requests.post(
                            f"{BASE}/integrations / rotate?category = news", timeout = 10
                        )
                        if rotate_resp.status_code == 200:
                            rotation_data = rotate_resp.json()
                            logger.info(
                                f"Rotated to {rotation_data.get('rotated_to', 'unknown')}"
                            )
                            continue  # Try again with new provider
                        else:
                            logger.warning(
                                f"Failed to rotate providers: {rotate_resp.status_code}"
                            )
                    except Exception as e:
                        logger.warning(f"Error during provider rotation: {e}")

                # Return error if no more retries
                return {
                    "provider": provider_key,
                        "ok": False,
                        "error": error_msg,
                        "took_ms": took_ms,
                        }

        except Exception as e:
            took_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Adapter error: {str(e)}"
            logger.error(error_msg)

            # Try to report if we have a provider key
            try:
                active = get_active_news_provider()
                _report_usage(active["key"], False, error_msg, took_ms)
            except Exception:
                pass

            return {
                "provider": "unknown",
                    "ok": False,
                    "error": error_msg,
                    "took_ms": took_ms,
                    }

    # Should not reach here
    return {
        "provider": "unknown",
            "ok": False,
            "error": "Max retries exceeded",
            "took_ms": int((time.time() - start_time) * 1000),
            }

# Convenience functions for backward compatibility


def get_top_headlines(
    limit: int = 10, category: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Get top headlines and return just the article list."""
    result = fetch_news(query = None, limit = limit, category = category)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Headlines fetch failed: {result['error']}")
        return []


def search_news(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for news articles and return just the article list."""
    result = fetch_news(query = query, limit = limit)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"News search failed: {result['error']}")
        return []
