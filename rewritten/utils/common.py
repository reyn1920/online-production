"""Common utilities to break circular imports between modules."""

import logging
import os
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class Provider:
    """Provider configuration dataclass."""

    name: str
    url: str
    needs_key: bool = False
    key_env: Optional[str] = None
    affiliate_id: Optional[str] = None
    status: str = "unknown"
    last_checked: Optional[str] = None
    response_time: Optional[float] = None
    error: Optional[str] = None


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get secret from environment variables."""

    Args:
        key: Environment variable name
        default: Default value if not found

    Returns:
        Secret value or default
    """"""
    return os.getenv(key, default)


async def http_with_fallback(
    url: str,
    method: str = "GET",
    headers: Optional[dict] = None,
    json_data: Optional[dict] = None,
    timeout: float = 10.0,
    **kwargs,
) -> Optional[dict]:
    """Make HTTP request with error handling and fallback."""

    Args:
        url: Request URL
        method: HTTP method
        headers: Request headers
        json_data: JSON payload for POST/PUT requests
        timeout: Request timeout in seconds
        **kwargs: Additional httpx client arguments

    Returns:
        Response JSON or None on error
    """"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, **kwargs)
            elif method.upper() == "POST":
                response = await client.post(url, headers=headers, json=json_data, **kwargs)
            elif method.upper() == "PUT":
                response = await client.put(url, headers=headers, json=json_data, **kwargs)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, **kwargs)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            return response.json()

    except httpx.TimeoutException:
        logger.warning(f"Request timeout for {url}")
        return None
    except httpx.HTTPStatusError as e:
        logger.warning(f"HTTP error {e.response.status_code} for {url}: {e.response.text}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error for {url}: {str(e)}")
        return None