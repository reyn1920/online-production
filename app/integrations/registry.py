#!/usr/bin/env python3
"""
Integration Registry - Provider Management System

Manages provider configurations, status tracking, and integration metadata.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class Provider:
    """Provider configuration and status"""
    id: str
    name: str
    kind: str
    enabled: bool = False
    requires_key: bool = True
    status: str = "purple"  # "green" | "red" | "purple"
    docs_url: str = ""
    signup_url: str = ""
    key_env: Optional[str] = None
    base_url: str = ""
    health_url: Optional[str] = None
    last_check: Optional[str] = None
    error_message: Optional[str] = None
    # Additional fields from config file
    health: Optional[Dict[str, Any]] = None
    usage: Optional[Dict[str, Any]] = None
    last_error: Optional[str] = None
    required_envs: Optional[List[str]] = None
    last_ok: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class IntegrationRegistry:
    """Central registry for all integration providers"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.providers_file = self.config_dir / "integrations.providers.json"
        self.providers: Dict[str, Provider] = {}
        self._load_providers()
    
    def _load_providers(self):
        """Load providers from configuration file"""
        if self.providers_file.exists():
            try:
                with open(self.providers_file, 'r') as f:
                    data = json.load(f)
                    for provider_data in data.get('providers', []):
                        provider = Provider(**provider_data)
                        self.providers[provider.id] = provider
                logger.info(f"Loaded {len(self.providers)} providers from config")
            except Exception as e:
                logger.error(f"Error loading providers: {e}")
                self._create_default_providers()
        else:
            self._create_default_providers()
    
    def _create_default_providers(self):
        """Create default provider configurations"""
        default_providers = [
            {
                "id": "nominatim_osm",
                "name": "Nominatim OSM",
                "kind": "geocoding",
                "enabled": True,
                "requires_key": False,
                "status": "green",
                "docs_url": "https://nominatim.org/release-docs/develop/api/Overview/",
                "base_url": "https://nominatim.openstreetmap.org"
            },
            {
                "id": "opencage",
                "name": "OpenCage Geocoding",
                "kind": "geocoding",
                "enabled": False,
                "requires_key": True,
                "status": "purple",
                "docs_url": "https://opencagedata.com/api",
                "signup_url": "https://opencagedata.com/users/sign_up",
                "key_env": "OPENCAGE_API_KEY",
                "base_url": "https://api.opencagedata.com"
            },
            {
                "id": "overpass_main",
                "name": "Overpass API (Main)",
                "kind": "places",
                "enabled": True,
                "requires_key": False,
                "status": "green",
                "docs_url": "https://wiki.openstreetmap.org/wiki/Overpass_API",
                "base_url": "https://overpass-api.de/api"
            },
            {
                "id": "overpass_kumi",
                "name": "Overpass API (Kumi)",
                "kind": "places",
                "enabled": True,
                "requires_key": False,
                "status": "green",
                "docs_url": "https://wiki.openstreetmap.org/wiki/Overpass_API",
                "base_url": "https://overpass.kumi.systems/api"
            },
            {
                "id": "overpass_fr",
                "name": "Overpass API (France)",
                "kind": "places",
                "enabled": True,
                "requires_key": False,
                "status": "green",
                "docs_url": "https://wiki.openstreetmap.org/wiki/Overpass_API",
                "base_url": "https://overpass.openstreetmap.fr/api"
            },
            {
                "id": "foursquare",
                "name": "Foursquare Places",
                "kind": "places",
                "enabled": False,
                "requires_key": True,
                "status": "purple",
                "docs_url": "https://developer.foursquare.com/docs",
                "signup_url": "https://developer.foursquare.com/",
                "key_env": "FOURSQUARE_API_KEY",
                "base_url": "https://api.foursquare.com"
            },
            {
                "id": "google_places",
                "name": "Google Places",
                "kind": "places",
                "enabled": False,
                "requires_key": True,
                "status": "purple",
                "docs_url": "https://developers.google.com/maps/documentation/places/web-service",
                "signup_url": "https://console.cloud.google.com/",
                "key_env": "GOOGLE_PLACES_API_KEY",
                "base_url": "https://maps.googleapis.com"
            },
            {
                "id": "yelp",
                "name": "Yelp Fusion",
                "kind": "places",
                "enabled": False,
                "requires_key": True,
                "status": "purple",
                "docs_url": "https://www.yelp.com/developers/documentation/v3",
                "signup_url": "https://www.yelp.com/developers/v3/manage_app",
                "key_env": "YELP_API_KEY",
                "base_url": "https://api.yelp.com"
            }
        ]
        
        for provider_data in default_providers:
            provider = Provider(**provider_data)
            self.providers[provider.id] = provider
        
        self._save_providers()
        logger.info(f"Created {len(self.providers)} default providers")
    
    def _save_providers(self):
        """Save providers to configuration file"""
        try:
            data = {
                "providers": [provider.to_dict() for provider in self.providers.values()]
            }
            with open(self.providers_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving providers: {e}")
    
    def get_provider(self, provider_id: str) -> Optional[Provider]:
        """Get provider by ID"""
        return self.providers.get(provider_id)
    
    def update_provider_status(self, provider_id: str, status: str, error_message: Optional[str] = None):
        """Update provider status"""
        if provider_id in self.providers:
            self.providers[provider_id].status = status
            self.providers[provider_id].error_message = error_message
            self.providers[provider_id].last_check = str(int(time.time()))
            self._save_providers()
    
    def get_enabled_providers(self, kind: Optional[str] = None) -> List[Provider]:
        """Get all enabled providers, optionally filtered by kind"""
        providers = [p for p in self.providers.values() if p.enabled]
        if kind:
            providers = [p for p in providers if p.kind == kind]
        return providers
    
    def list_all_providers(self) -> List[Provider]:
        """Get all providers"""
        return list(self.providers.values())

# Global registry instance
_registry = None

def get_registry() -> IntegrationRegistry:
    """Get or create global registry instance"""
    global _registry
    if _registry is None:
        _registry = IntegrationRegistry()
    return _registry