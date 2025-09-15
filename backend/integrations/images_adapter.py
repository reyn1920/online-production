# backend/integrations/images_adapter.py

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests
from utils.http import http_get_with_backoff

logger = logging.getLogger(__name__)
BASE = "http://localhost:8000"  # or internal import if same process
TIMEOUT_S = 15


def get_active_image_provider() -> Dict:
    """
Get the currently active image provider from the registry.

    
"""
    try:
    """
        r = requests.get(f"{BASE}/integrations/active/images", timeout=10)
        r.raise_for_status()
    """

    try:
    

   
""""""
        return r.json()["active"]
    except Exception as e:
        logger.error(f"Failed to get active image provider: {e}")
        raise


def _get_credentials(provider_key: str) -> Dict[str, str]:
    """
Get credentials for a provider from environment or secret store.

   
""""""

    # Try environment variables first
   

    
   
"""
    creds = {}
   """

    
   

    # Try environment variables first
   
""""""
    if provider_key == "pexels":
        api_key = os.getenv("PEXELS_API_KEY")
        if api_key:
            creds["api_key"] = api_key
    elif provider_key == "unsplash":
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if access_key:
            creds["access_key"] = access_key
    elif provider_key == "pixabay":
        api_key = os.getenv("PIXABAY_API_KEY")
        if api_key:
            creds["api_key"] = api_key

    # Fallback to secure secret store if available
    try:
        from backend.security.secret_store import get_secret

        if provider_key == "pexels" and not creds.get("api_key"):
            secret_key = get_secret("pexels_api_key")
            if secret_key:
                creds["api_key"] = secret_key
        elif provider_key == "unsplash" and not creds.get("access_key"):
            secret_key = get_secret("unsplash_access_key")
            if secret_key:
                creds["access_key"] = secret_key
        elif provider_key == "pixabay" and not creds.get("api_key"):
            secret_key = get_secret("pixabay_api_key")
            if secret_key:
                creds["api_key"] = secret_key
    except ImportError:
        # Secret store not available, using environment variables only
        logger.debug("Secret store not available, using environment variables")
    except Exception as e:
        logger.warning(f"Failed to retrieve secrets from store: {e}")

    return creds


def _report_usage(
    provider_key: str,
    success: bool,
    error: Optional[str] = None,
    took_ms: Optional[int] = None,
    quota_remaining: Optional[int] = None,
# ):
    """
Report usage metrics to the integrations registry.

    
"""
    try:
    """
        payload = {"key": provider_key, "success": success, "took_ms": took_ms}
    """

    try:
    

   
""""""
        if error:
            payload["error"] = str(error)[:300]  # Truncate long errors
        if quota_remaining is not None:
            payload["quota_remaining"] = quota_remaining

        requests.post(f"{BASE}/integrations/report", json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Failed to report usage for {provider_key}: {e}")


def _fetch_pexels_images(query: str, limit: int, api_key: str) -> Dict[str, Any]:
    """Fetch images from Pexels API."""
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": min(limit, 80),  # Pexels max is 80
        "orientation": "all",
     }

    resp = http_get_with_backoff(
        "https://api.pexels.com/v1/search",
        headers=headers,
        params=params,
        timeout=TIMEOUT_S,
     )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        images = []
        for photo in data.get("photos", []):
            images.append(
                {
                    "id": str(photo["id"]),
                    "url": photo["src"]["large"],
                    "thumbnail": photo["src"]["medium"],
                    "title": photo.get("alt", query),
                    "author": photo["photographer"],
                    "source": "pexels",
                    "source_url": photo["url"],
                 }
             )

        return {
            "success": True,
            "images": images,
            "total": data.get("total_results", len(images)),
            "quota_remaining": None,  # Pexels doesn't provide quota info in response
         }
    else:
        return {
            "success": False,
            "error": f"Pexels API error: {resp.status_code} - {resp.text[:200]}",
         }


def _fetch_unsplash_images(query: str, limit: int, access_key: str) -> Dict[str, Any]:
    """Fetch images from Unsplash API."""
    headers = {"Authorization": f"Client - ID {access_key}"}
    params = {
        "query": query,
        "per_page": min(limit, 30),  # Unsplash max is 30
        "orientation": "landscape",
     }

    resp = http_get_with_backoff(
        "https://api.unsplash.com/search/photos",
        headers=headers,
        params=params,
        timeout=TIMEOUT_S,
     )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        images = []
        for photo in data.get("results", []):
            images.append(
                {
                    "id": photo["id"],
                    "url": photo["urls"]["regular"],
                    "thumbnail": photo["urls"]["small"],
                    "title": photo.get("alt_description", query),
                    "author": photo["user"]["name"],
                    "source": "unsplash",
                    "source_url": photo["links"]["html"],
                 }
             )

        return {
            "success": True,
            "images": images,
            "total": data.get("total", len(images)),
            "quota_remaining": None,  # Check rate limit headers if needed
         }
    else:
        return {
            "success": False,
            "error": f"Unsplash API error: {resp.status_code} - {resp.text[:200]}",
         }


def _fetch_pixabay_images(query: str, limit: int, api_key: str) -> Dict[str, Any]:
    """Fetch images from Pixabay API."""
    params = {
        "key": api_key,
        "q": query,
        "per_page": min(limit, 200),  # Pixabay max is 200
        "safesearch": "true",
        "image_type": "photo",
     }

    resp = http_get_with_backoff("https://pixabay.com/api/", params=params, timeout=TIMEOUT_S)

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        images = []
        for hit in data.get("hits", []):
            images.append(
                {
                    "id": str(hit["id"]),
                    "url": hit["largeImageURL"],
                    "thumbnail": hit["webformatURL"],
                    "title": hit.get("tags", query),
                    "author": hit["user"],
                    "source": "pixabay",
                    "source_url": hit["pageURL"],
                 }
             )

        return {
            "success": True,
            "images": images,
            "total": data.get("totalHits", len(images)),
            "quota_remaining": None,  # Pixabay doesn't provide quota info
         }
    else:
        return {
            "success": False,
            "error": f"Pixabay API error: {resp.status_code} - {resp.text[:200]}",
         }


def fetch_images(query: str, limit: int = 10, max_retries: int = 1) -> Dict[str, Any]:
    """
Fetch images using the active provider with automatic failover.

   
""""""

    start_time = time.time()
   

    
   
"""
    for attempt in range(max_retries + 1):
        try:
            # Get active provider
   """

    
   

    start_time = time.time()
   
""""""
            active = get_active_image_provider()
            provider_key = active["key"]

            logger.info(f"Fetching images from {provider_key} (attempt {attempt + 1})")

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
            if provider_key == "pexels" and "api_key" in creds:
                result = _fetch_pexels_images(query, limit, creds["api_key"])
            elif provider_key == "unsplash" and "access_key" in creds:
                result = _fetch_unsplash_images(query, limit, creds["access_key"])
            elif provider_key == "pixabay" and "api_key" in creds:
                result = _fetch_pixabay_images(query, limit, creds["api_key"])
            else:
                result = {
                    "success": False,
                    "error": f"No adapter implementation for {provider_key}",
                 }

            took_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                # Success - report and return
                _report_usage(provider_key, True, None, took_ms, result.get("quota_remaining"))
                return {
                    "provider": provider_key,
                    "ok": True,
                    "data": result["images"],
                    "total": result.get("total", len(result["images"])),
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
                            f"{BASE}/integrations/rotate?category = images", timeout=10
                         )
                        if rotate_resp.status_code == 200:
                            rotation_data = rotate_resp.json()
                            logger.info(f"Rotated to {rotation_data.get('rotated_to', 'unknown')}")
                            continue  # Try again with new provider
                        else:
                            logger.warning(f"Failed to rotate providers: {rotate_resp.status_code}")
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
                active = get_active_image_provider()
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


# Convenience function for backward compatibility


def search_images(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for images and return just the image list."""
    result = fetch_images(query, limit)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Image search failed: {result['error']}")
        return []