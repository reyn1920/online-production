# Example: Fetch free stock images with automatic fallback
# Tries Unsplash -> Pexels -> Pixabay in order

import asyncio

from integrations_hub import get_secret, http_with_fallback


async def get_images_for_query(query: str):
    """Fetch stock images for a given query using multiple providers with fallback.

    This function demonstrates the power of the http_with_fallback system:
    - Automatically tries providers in preferred order
    - Falls back to next provider if one fails
    - Handles API key management securely
    - Returns consistent results regardless of which provider succeeds

    Args:
        query: Search term for images

    Returns:
        JSON response from the first successful provider
    """

    async def do_request(client, prov):
        """Handle requests for different image providers."""
        if prov.id == "unsplash":
            key = get_secret("UNSPLASH_KEY")
            if not key:
                raise RuntimeError("UNSPLASH_KEY not configured")
            r = await client.get(
                "https://api.unsplash.com/search/photos",
                headers={"Authorization": f"Client-ID {key}"},
                params={"query": query, "per_page": 6},
            )
            r.raise_for_status()
            return r.json()

        elif prov.id == "pexels":
            key = get_secret("PEXELS_KEY")
            if not key:
                raise RuntimeError("PEXELS_KEY not configured")
            r = await client.get(
                "https://api.pexels.com/v1/search",
                headers={"Authorization": key},
                params={"query": query, "per_page": 6},
            )
            r.raise_for_status()
            return r.json()

        elif prov.id == "pixabay":
            key = get_secret("PIXABAY_KEY")
            if not key:
                raise RuntimeError("PIXABAY_KEY not configured")
            r = await client.get(
                "https://pixabay.com/api/",
                params={"key": key, "q": query, "per_page": 6},
            )
            r.raise_for_status()
            return r.json()

        else:
            raise RuntimeError(f"Unknown provider for images: {prov.id}")

    # Use http_with_fallback to try providers in order with automatic fallback
    return await http_with_fallback(
        "images", do_request, prefer=["unsplash", "pexels", "pixabay"]
    )


# Example usage:
# import asyncio
#
# async def main():
#     results = await get_images_for_query("nature")
#     print(f"Found {len(results.get('results', []))} images")
#
# if __name__ == "__main__":
#     asyncio.run(main())
