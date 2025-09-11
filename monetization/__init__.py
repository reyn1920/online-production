"""Monetization platform integrations for automated revenue generation."""

from .etsy_api import EtsyAPI
from .paddle_api import PaddleAPI
from .sendowl_api import SendOwlAPI
from .gumroad_api import GumroadAPI
from .base_monetization import BaseMonetizationAPI, Product, ProductResponse, MonetizationError
from .monetization_manager import MonetizationManager, PlatformConfig, MultiPlatformResult

__all__ = [
    'EtsyAPI',
    'PaddleAPI', 
    'SendOwlAPI',
    'GumroadAPI',
    'BaseMonetizationAPI',
    'Product',
    'ProductResponse',
    'MonetizationError',
    'MonetizationManager',
    'PlatformConfig',
    'MultiPlatformResult'
]