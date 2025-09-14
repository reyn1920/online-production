"""Monetization platform integrations for automated revenue generation."""

from .base_monetization import (
    BaseMonetizationAPI,
    MonetizationError,
    Product,
    ProductResponse,
)

from .etsy_api import EtsyAPI
from .gumroad_api import GumroadAPI
from .monetization_manager import (
    MonetizationManager,
    MultiPlatformResult,
    PlatformConfig,
)

from .paddle_api import PaddleAPI
from .sendowl_api import SendOwlAPI

__all__ = [
    "EtsyAPI",
    "PaddleAPI",
    "SendOwlAPI",
    "GumroadAPI",
    "BaseMonetizationAPI",
    "Product",
    "ProductResponse",
    "MonetizationError",
    "MonetizationManager",
    "PlatformConfig",
    "MultiPlatformResult",
]
