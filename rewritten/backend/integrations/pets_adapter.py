# backend/integrations/pets_adapter.py

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests
from utils.http import http_get_with_backoff

logger = logging.getLogger(__name__)
BASE = "http://localhost:8000"  # or internal import if same process
TIMEOUT_S = 15


def get_active_pets_provider() -> Dict:
    """Get the currently active pets provider from the registry."""
    try:
        r = http_get_with_backoff(f"{BASE}/integrations/active/pets", timeout=10)
        r.raise_for_status()
        return r.json()["active"]
    except Exception as e:
        logger.error(f"Failed to get active pets provider: {e}")
        raise


def _get_credentials(provider_key: str) -> Dict[str, str]:
    """Get credentials for a provider from environment or secret store."""
    # Try environment variables first
    creds = {}
    if provider_key == "thecatapi":
        api_key = os.getenv("THECATAPI_KEY")
        if api_key:
            creds["api_key"] = api_key
    elif provider_key == "thedogapi":
        api_key = os.getenv("THEDOGAPI_KEY")
        if api_key:
            creds["api_key"] = api_key
    # petfinder requires OAuth, more complex setup
    elif provider_key == "petfinder":
        api_key = os.getenv("PETFINDER_API_KEY")
        secret = os.getenv("PETFINDER_SECRET")
        if api_key and secret:
            creds["api_key"] = api_key
            creds["secret"] = secret

    # Fallback to secure secret store if available
    try:
        from backend.security.secret_store import get_secret

        if provider_key == "petfinder" and not creds.get("api_key"):
            secret_key = get_secret("petfinder_api_key")
            if secret_key:
                creds["api_key"] = secret_key
            secret_secret = get_secret("petfinder_secret")
            if secret_secret:
                creds["secret"] = secret_secret
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
# BRACKET_SURGEON: disabled
# ):
    """Report usage metrics to the integrations registry."""
    try:
        payload = {"key": provider_key, "success": success, "took_ms": took_ms}
        if error:
            payload["error"] = str(error)[:300]  # Truncate long errors
        if quota_remaining is not None:
            payload["quota_remaining"] = quota_remaining

        requests.post(f"{BASE}/integrations/report", json=payload, timeout=10)
    except Exception as e:
        logger.warning(f"Failed to report usage for {provider_key}: {e}")


def _fetch_thecatapi_images(limit: int, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Fetch cat images from TheCatAPI."""
    headers = {}
    if api_key:
        headers["x - api - key"] = api_key

    params = {
        "limit": min(limit, 100),  # TheCatAPI max is 100
        "size": "med",
        "mime_types": "jpg,png",
        "format": "json",
        "has_breeds": "true",
        "order": "RANDOM",
# BRACKET_SURGEON: disabled
#     }

    resp = http_get_with_backoff(
        "https://api.thecatapi.com/v1/images/search",
        headers=headers,
        params=params,
        timeout=TIMEOUT_S,
# BRACKET_SURGEON: disabled
#     )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        pets = []
        for cat in data:
            breed_info = cat.get("breeds", [{}])[0] if cat.get("breeds") else {}
            pets.append(
                {
                    "id": cat["id"],
                    "type": "cat",
                    "image_url": cat["url"],
                    "width": cat.get("width"),
                    "height": cat.get("height"),
                    "breed": breed_info.get("name", "Mixed"),
                    "breed_info": (
                        {
                            "name": breed_info.get("name"),
                            "temperament": breed_info.get("temperament"),
                            "origin": breed_info.get("origin"),
                            "description": breed_info.get("description"),
                            "life_span": breed_info.get("life_span"),
                            "weight": breed_info.get("weight", {}).get("metric"),
# BRACKET_SURGEON: disabled
#                         }
                        if breed_info
                        else None
# BRACKET_SURGEON: disabled
#                     ),
                    "source": "thecatapi",
                    "provider": "thecatapi",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        return {
            "success": True,
            "pets": pets,
            "total": len(pets),
            "quota_remaining": None,  # TheCatAPI doesn't provide quota info
# BRACKET_SURGEON: disabled
#         }
    else:
        return {
            "success": False,
            "error": f"TheCatAPI error: {resp.status_code} - {resp.text[:200]}",
# BRACKET_SURGEON: disabled
#         }


def _fetch_thedogapi_images(limit: int, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Fetch dog images from TheDogAPI."""
    headers = {}
    if api_key:
        headers["x - api - key"] = api_key

    params = {
        "limit": min(limit, 100),  # TheDogAPI max is 100
        "size": "med",
        "mime_types": "jpg,png",
        "format": "json",
        "has_breeds": "true",
        "order": "RANDOM",
# BRACKET_SURGEON: disabled
#     }

    resp = http_get_with_backoff(
        "https://api.thedogapi.com/v1/images/search",
        headers=headers,
        params=params,
        timeout=TIMEOUT_S,
# BRACKET_SURGEON: disabled
#     )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        pets = []
        for dog in data:
            breed_info = dog.get("breeds", [{}])[0] if dog.get("breeds") else {}
            pets.append(
                {
                    "id": dog["id"],
                    "type": "dog",
                    "image_url": dog["url"],
                    "width": dog.get("width"),
                    "height": dog.get("height"),
                    "breed": breed_info.get("name", "Mixed"),
                    "breed_info": (
                        {
                            "name": breed_info.get("name"),
                            "temperament": breed_info.get("temperament"),
                            "origin": breed_info.get("origin"),
                            "description": breed_info.get("description"),
                            "life_span": breed_info.get("life_span"),
                            "weight": breed_info.get("weight", {}).get("metric"),
                            "height": breed_info.get("height", {}).get("metric"),
                            "bred_for": breed_info.get("bred_for"),
                            "breed_group": breed_info.get("breed_group"),
# BRACKET_SURGEON: disabled
#                         }
                        if breed_info
                        else None
# BRACKET_SURGEON: disabled
#                     ),
                    "source": "thedogapi",
                    "provider": "thedogapi",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        return {
            "success": True,
            "pets": pets,
            "total": len(pets),
            "quota_remaining": None,  # TheDogAPI doesn't provide quota info
# BRACKET_SURGEON: disabled
#         }
    else:
        return {
            "success": False,
            "error": f"TheDogAPI error: {resp.status_code} - {resp.text[:200]}",
# BRACKET_SURGEON: disabled
#         }


def _get_petfinder_token(api_key: str, secret: str) -> Optional[str]:
    """Get OAuth token for Petfinder API."""
    try:
        data = {
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": secret,
# BRACKET_SURGEON: disabled
#         }

        resp = requests.post(
            "https://api.petfinder.com/v2/oauth2/token", data=data, timeout=TIMEOUT_S
# BRACKET_SURGEON: disabled
#         )

        if resp.status_code == 200:
            token_data = resp.json()
            return token_data.get("access_token")
        else:
            logger.error(f"Petfinder token error: {resp.status_code} - {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Petfinder token request failed: {e}")
        return None


def _fetch_petfinder_animals(
    limit: int, api_key: str, secret: str, animal_type: str = "dog"
) -> Dict[str, Any]:
    """Fetch animals from Petfinder API."""
    # Get OAuth token
    token = _get_petfinder_token(api_key, secret)
    if not token:
        return {"success": False, "error": "Failed to get Petfinder OAuth token"}

    headers = {"Authorization": f"Bearer {token}"}

    params = {
        "type": animal_type,
        "limit": min(limit, 100),  # Petfinder max is 100
        "status": "adoptable",
        "sort": "random",
# BRACKET_SURGEON: disabled
#     }

    resp = http_get_with_backoff(
        "https://api.petfinder.com/v2/animals",
        headers=headers,
        params=params,
        timeout=TIMEOUT_S,
# BRACKET_SURGEON: disabled
#     )

    if resp.status_code == 200:
        data = resp.json()
        # Transform to standard format
        pets = []
        for animal in data.get("animals", []):
            # Get primary photo
            photos = animal.get("photos", [])
            image_url = photos[0].get("large") if photos else None

            pets.append(
                {
                    "id": str(animal["id"]),
                    "type": animal["type"].lower(),
                    "image_url": image_url,
                    "width": None,  # Not provided by Petfinder
                    "height": None,  # Not provided by Petfinder
                    "breed": animal.get("breeds", {}).get("primary", "Mixed"),
                    "name": animal.get("name"),
                    "age": animal.get("age"),
                    "gender": animal.get("gender"),
                    "size": animal.get("size"),
                    "description": animal.get("description"),
                    "status": animal.get("status"),
                    "organization_id": animal.get("organization_id"),
                    "contact": animal.get("contact"),
                    "breed_info": {
                        "primary": animal.get("breeds", {}).get("primary"),
                        "secondary": animal.get("breeds", {}).get("secondary"),
                        "mixed": animal.get("breeds", {}).get("mixed"),
                        "unknown": animal.get("breeds", {}).get("unknown"),
# BRACKET_SURGEON: disabled
#                     },
                    "attributes": animal.get("attributes", {}),
                    "environment": animal.get("environment", {}),
                    "source": "petfinder",
                    "provider": "petfinder",
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        return {
            "success": True,
            "pets": pets,
            "total": data.get("pagination", {}).get("total_count", len(pets)),
            "quota_remaining": None,  # Petfinder doesn't provide quota info
# BRACKET_SURGEON: disabled
#         }
    else:
        return {
            "success": False,
            "error": f"Petfinder API error: {resp.status_code} - {resp.text[:200]}",
# BRACKET_SURGEON: disabled
#         }


def fetch_pets(pet_type: str = "random", limit: int = 10, max_retries: int = 1) -> Dict[str, Any]:
    """Fetch pet data using the active provider with automatic failover."""
    start_time = time.time()

    for attempt in range(max_retries + 1):
        try:
            # Get active provider
            active = get_active_pets_provider()
            provider_key = active["key"]

            logger.info(f"Fetching pets from {provider_key} (attempt {attempt + 1})")

            # Get credentials
            creds = _get_credentials(provider_key)
            if active.get("needs_key", False) and not creds:
                error_msg = f"No credentials found for {provider_key}"
                _report_usage(
                    provider_key,
                    False,
                    error_msg,
                    int((time.time() - start_time) * 1000),
# BRACKET_SURGEON: disabled
#                 )
                return {"provider": provider_key, "ok": False, "error": error_msg}

            # Call appropriate provider
            result = None
            if provider_key == "thecatapi":
                if pet_type in ["cat", "random"]:
                    result = _fetch_thecatapi_images(limit, creds.get("api_key"))
                else:
                    result = {
                        "success": False,
                        "error": f"TheCatAPI doesn't support {pet_type}",'
# BRACKET_SURGEON: disabled
#                     }
            elif provider_key == "thedogapi":
                if pet_type in ["dog", "random"]:
                    result = _fetch_thedogapi_images(limit, creds.get("api_key"))
                else:
                    result = {
                        "success": False,
                        "error": f"TheDogAPI doesn't support {pet_type}",'
# BRACKET_SURGEON: disabled
#                     }
            elif provider_key == "petfinder" and "api_key" in creds and "secret" in creds:
                # Petfinder supports multiple animal types
                animal_type = pet_type if pet_type != "random" else "dog"
                result = _fetch_petfinder_animals(
                    limit, creds["api_key"], creds["secret"], animal_type
# BRACKET_SURGEON: disabled
#                 )
            else:
                result = {
                    "success": False,
                    "error": f"No adapter implementation for {provider_key}",
# BRACKET_SURGEON: disabled
#                 }

            took_ms = int((time.time() - start_time) * 1000)

            if result["success"]:
                # Success - report and return
                _report_usage(provider_key, True, None, took_ms, result.get("quota_remaining"))
                return {
                    "provider": provider_key,
                    "ok": True,
                    "data": result["pets"],
                    "total": result.get("total", len(result["pets"])),
                    "took_ms": took_ms,
# BRACKET_SURGEON: disabled
#                 }
            else:
                # Failure - report and potentially rotate
                error_msg = result.get("error", "Unknown error")
                _report_usage(provider_key, False, error_msg, took_ms)

                # Try rotation if this is not the last attempt
                if attempt < max_retries:
                    try:
                        logger.info(f"Rotating from failed provider {provider_key}")
                        rotate_resp = requests.post(
                            f"{BASE}/integrations/rotate?category = pets", timeout=10
# BRACKET_SURGEON: disabled
#                         )
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
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            took_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Adapter error: {str(e)}"
            logger.error(error_msg)

            # Try to report if we have a provider key
            try:
                active = get_active_pets_provider()
                _report_usage(active["key"], False, error_msg, took_ms)
            except Exception:
                pass

            return {
                "provider": "unknown",
                "ok": False,
                "error": error_msg,
                "took_ms": took_ms,
# BRACKET_SURGEON: disabled
#             }

    # Should not reach here
    return {
        "provider": "unknown",
        "ok": False,
        "error": "Max retries exceeded",
        "took_ms": int((time.time() - start_time) * 1000),
# BRACKET_SURGEON: disabled
#     }


# Convenience functions for backward compatibility


def get_random_pets(limit: int = 10) -> List[Dict[str, Any]]:
    """Get random pet images and return just the pet list."""
    result = fetch_pets("random", limit)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Random pets fetch failed: {result['error']}")
        return []


def get_cats(limit: int = 10) -> List[Dict[str, Any]]:
    """Get cat images and return just the cat list."""
    result = fetch_pets("cat", limit)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Cats fetch failed: {result['error']}")
        return []


def get_dogs(limit: int = 10) -> List[Dict[str, Any]]:
    """Get dog images and return just the dog list."""
    result = fetch_pets("dog", limit)
    if result["ok"]:
        return result["data"]
    else:
        logger.error(f"Dogs fetch failed: {result['error']}")
        return []