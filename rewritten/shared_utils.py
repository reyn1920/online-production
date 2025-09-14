# utils.py - Shared utilities to avoid circular imports

import os
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx


@dataclass
class Provider:
    id: str
    name: str
    category: str
    docs_url: str
    signup_url: Optional[str] = None
    key_env: Optional[str] = None
    needs_key: bool = True
    enabled: bool = False
    status: str = "purple"
    last_ok: Optional[str] = None
    last_error: Optional[str] = None
    health_url: Optional[str] = None
    headers: Dict[str, str] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}


def gambling_enabled() -> bool:
    """Check if gambling features are enabled via environment variable."""
    v = get_secret("GAMBLING_FEATURES_ENABLED")
    return (str(v or "")).lower() in ("1", "true", "yes", "on")


def set_secret(name: str, value: str) -> None:
    """Store a secret (environment variable for now)"""
    os.environ[name] = value


def get_secret(name: str) -> Optional[str]:
    """Retrieve a secret from environment variables"""
    return os.environ.get(name)


async def http_with_fallback(
    category: str,
    func: Callable[[httpx.AsyncClient, Provider], Any],
    prefer: List[str] = None,
    timeout: float = 10.0,
) -> Any:
    """Execute HTTP requests with provider fallback logic"""
    # For now, just use a simple mock provider system
    # In a real implementation, this would load from the providers config
    mock_providers = {
        "news": [
            Provider(id=p, name=p.title(), category="news", docs_url="")
            for p in (prefer or ["guardian", "newsapi"])
        ],
        "tech": [
            Provider(id=p, name=p.title(), category="tech", docs_url="")
            for p in (prefer or ["github", "hackernews"])
        ],
        "knowledge": [
            Provider(id=p, name=p.title(), category="knowledge", docs_url="")
            for p in (prefer or ["arxiv", "paperswithcode"])
        ],
        "wellness": [
            Provider(id=p, name=p.title(), category="wellness", docs_url="")
            for p in (prefer or ["usda_fdc", "openfda"])
        ],
        "pets": [
            Provider(
                id=p,
                name=p.title(),
                category="pets",
                docs_url="",
                needs_key=False,
                enabled=True,
            )
            for p in (prefer or ["thedogapi", "thecatapi", "dog_ceo"])
        ],
        "pets_misc": [
            Provider(
                id=p,
                name=p.title(),
                category="pets_misc",
                docs_url="",
                needs_key=False,
                enabled=True,
            )
            for p in (prefer or ["zoo_animal_api", "dog_ceo"])
        ],
        "pets_birds": [
            Provider(
                id=p,
                name=p.title(),
                category="pets_birds",
                docs_url="",
                needs_key=True,
                enabled=False,
            )
            for p in (prefer or ["ebird"])
        ],
        "pets_fish": [
            Provider(
                id=p,
                name=p.title(),
                category="pets_fish",
                docs_url="",
                needs_key=False,
                enabled=True,
            )
            for p in (prefer or ["fishwatch"])
        ],
        "pets_care": [
            Provider(
                id=p,
                name=p.title(),
                category="pets_care",
                docs_url="",
                needs_key=True,
                enabled=False,
            )
            for p in (prefer or ["vetster", "pawp", "airvet"])
        ],
        "scheduling": [
            Provider(
                id=p,
                name=p.title(),
                category="scheduling",
                docs_url="",
                needs_key=True,
                enabled=False,
            )
            for p in (prefer or ["calendly"])
        ],
    }

    providers = mock_providers.get(category, [])
    if prefer:
        # Reorder providers based on preference
        preferred_providers = []
        for pref_id in prefer:
            for p in providers:
                if p.id == pref_id:
                    preferred_providers.append(p)
                    break
        providers = preferred_providers

    async with httpx.AsyncClient(timeout=timeout) as client:
        for provider in providers:
            try:
                result = await func(client, provider)
                return result
            except Exception as e:
                print(f"Provider {provider.id} failed: {e}")
                continue

    raise RuntimeError(f"All providers failed for category: {category}")
