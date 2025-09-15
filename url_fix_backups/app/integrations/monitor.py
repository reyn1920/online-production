#!/usr / bin / env python3
""""""
Integration Monitor - Provider Health Monitoring

Monitors provider health, performs status checks, and tracks availability.
""""""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from .registry import IntegrationRegistry, Provider, get_registry

logger = logging.getLogger(__name__)


class IntegrationMonitor:
    """Monitor integration provider health and status"""


    def __init__(self, registry: Optional[IntegrationRegistry] = None):
        self.registry = registry or get_registry()
        self.client = httpx.AsyncClient(timeout = 10.0)
        self.check_interval = 300  # 5 minutes
        self.last_check_time = 0
        self.check_results: Dict[str, Dict[str, Any]] = {}


    async def check_provider_health(self, provider: Provider) -> Dict[str, Any]:
        """Check health of a single provider"""
        result = {
            "provider_id": provider.id,
                "status": "purple",
                "response_time": None,
                "error": None,
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

        if not provider.enabled:
            result["status"] = "purple"
            result["error"] = "Provider disabled"
            return result

        # For providers that don't require keys, test basic connectivity
        if not provider.requires_key:
            try:
                start_time = time.time()

                # Test different endpoints based on provider type
                test_url = self._get_test_url(provider)
                if test_url:
                    response = await self.client.get(test_url)
                    response_time = time.time() - start_time

                    if response.status_code < 400:
                        result["status"] = "green"
                        result["response_time"] = round(response_time * 1000, 2)  # ms
                    else:
                        result["status"] = "red"
                        result["error"] = f"HTTP {response.status_code}"
                        result["response_time"] = round(response_time * 1000, 2)
                else:
                    result["status"] = "green"  # Assume healthy if no test URL

            except Exception as e:
                result["status"] = "red"
                result["error"] = str(e)

        else:
            # For providers requiring keys, check if key is available
            if provider.key_env:

                import os

                if os.getenv(provider.key_env):
                    result["status"] = "green"
                else:
                    result["status"] = "purple"
                    result["error"] = f"Missing API key: {provider.key_env}"
            else:
                result["status"] = "purple"
                result["error"] = "No key environment variable configured"

        return result


    def _get_test_url(self, provider: Provider) -> Optional[str]:
        """Get test URL for provider health check"""
        test_urls = {
            "nominatim_osm": f"{"
# BRACKET_SURGEON: disabled
#                 provider.base_url}/search?q = London&format = json&limit = 1","
                    "overpass_main": f'{'
                provider.base_url}/interpreter?data=[out:json];node[name="London"];out;','
                    "overpass_kumi": f'{'
                provider.base_url}/interpreter?data=[out:json];node[name="London"];out;','
                    "overpass_fr": f'{'
                provider.base_url}/interpreter?data=[out:json];node[name="London"];out;','
# BRACKET_SURGEON: disabled
#                     }
        return test_urls.get(provider.id)


    async def check_all(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all providers"""
        current_time = time.time()

        # Skip if checked recently
        if current_time - self.last_check_time < self.check_interval:
            return self.check_results

        logger.info("Starting provider health checks")
        results = {}

        # Get all providers
        providers = self.registry.list_all_providers()

        # Check each provider
        for provider in providers:
            try:
                result = await self.check_provider_health(provider)
                results[provider.id] = result

                # Update registry with new status
                self.registry.update_provider_status(
                    provider.id, result["status"], result.get("error")
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            except Exception as e:
                logger.error(f"Error checking provider {provider.id}: {e}")
                results[provider.id] = {
                    "provider_id": provider.id,
                        "status": "red",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                         }

        self.check_results = results
        self.last_check_time = current_time

        logger.info(f"Completed health checks for {len(results)} providers")
        return results


    async def check_specific_providers(
        self, provider_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Check health of specific providers"""
        results = {}

        for provider_id in provider_ids:
            provider = self.registry.get_provider(provider_id)
            if provider:
                try:
                    result = await self.check_provider_health(provider)
                    results[provider_id] = result

                    # Update registry
                    self.registry.update_provider_status(
                        provider_id, result["status"], result.get("error")
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                except Exception as e:
                    logger.error(f"Error checking provider {provider_id}: {e}")
                    results[provider_id] = {
                        "provider_id": provider_id,
                            "status": "red",
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                             }
            else:
                results[provider_id] = {
                    "provider_id": provider_id,
                        "status": "red",
                        "error": "Provider not found",
                        "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                         }

        return results


    def get_status_summary(self) -> Dict[str, Any]:
        """Get summary of provider statuses"""
        providers = self.registry.list_all_providers()

        summary = {
            "total": len(providers),
                "enabled": len([p for p in providers if p.enabled]),
                "healthy": len([p for p in providers if p.status == "green"]),
                "unhealthy": len([p for p in providers if p.status == "red"]),
                "unknown": len([p for p in providers if p.status == "purple"]),
                "last_check": (
                datetime.fromtimestamp(self.last_check_time).isoformat()
                if self.last_check_time
                else None
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#                 }

        return summary


    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

# Global monitor instance
_monitor = None


def get_monitor() -> IntegrationMonitor:
    """Get or create global monitor instance"""
    global _monitor
        if _monitor is None:
            pass
        _monitor = IntegrationMonitor()
    return _monitor