"""Monetization Manager for orchestrating multiple platform integrations."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from .base_monetization import Product, ProductResponse
from .etsy_api import EtsyAPI
from .gumroad_api import GumroadAPI
from .paddle_api import PaddleAPI
from .sendowl_api import SendOwlAPI

logger = logging.getLogger(__name__)

@dataclass


class PlatformConfig:
    """Configuration for a monetization platform."""

    name: str
    api_class: type
    credentials: Dict[str, str]
    enabled: bool = True
    priority: int = 1  # 1 = highest priority
    product_types: List[str] = None  # Supported product types


    def __post_init__(self):
        if self.product_types is None:
            self.product_types = ["digital", "physical", "service"]

@dataclass


class MultiPlatformResult:
    """Result from multi - platform operation."""

    success_count: int
    failure_count: int
    results: Dict[str, Any]
    errors: Dict[str, str]
    total_platforms: int

    @property


    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_platforms == 0:
            return 0.0
        return (self.success_count / self.total_platforms) * 100


class MonetizationManager:
    """Manager for orchestrating multiple monetization platforms."""


    def __init__(self, config_file: Optional[str] = None):
        self.platforms: Dict[str, Any] = {}
        self.configs: Dict[str, PlatformConfig] = {}
        self.health_status: Dict[str, bool] = {}
        self.last_health_check: Optional[datetime] = None

        # Default platform configurations
        self._setup_default_configs()

        if config_file:
            self._load_config(config_file)


    def _setup_default_configs(self):
        """Setup default platform configurations."""
        self.platform_classes = {
            "etsy": EtsyAPI,
                "paddle": PaddleAPI,
                "sendowl": SendOwlAPI,
                "gumroad": GumroadAPI,
                }


    def add_platform(
        self,
            name: str,
            api_class: type,
            credentials: Dict[str, str],
            enabled: bool = True,
            priority: int = 1,
            product_types: List[str] = None,
            ) -> bool:
        """Add a monetization platform."""
        try:
            config = PlatformConfig(
                name = name,
                    api_class = api_class,
                    credentials = credentials,
                    enabled = enabled,
                    priority = priority,
                    product_types = product_types or ["digital", "physical", "service"],
                    )

            # Initialize the API client
            if name == "etsy":
                api_client = api_class(
                    api_key = credentials.get("api_key"),
                        shared_secret = credentials.get("shared_secret"),
                        oauth_token = credentials.get("oauth_token"),
                        oauth_token_secret = credentials.get("oauth_token_secret"),
                        )
            elif name == "paddle":
                api_client = api_class(
                    vendor_id = credentials.get("vendor_id"),
                        vendor_auth_code = credentials.get("vendor_auth_code"),
                        )
            elif name in ["sendowl", "gumroad"]:
                api_client = api_class(access_token = credentials.get("access_token"))
            else:
                # Generic initialization
                api_client = api_class(**credentials)

            self.platforms[name] = api_client
            self.configs[name] = config

            logger.info(f"Added monetization platform: {name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add platform {name}: {e}")
            return False


    def remove_platform(self, name: str) -> bool:
        """Remove a monetization platform."""
        try:
            if name in self.platforms:
                del self.platforms[name]
                del self.configs[name]
                if name in self.health_status:
                    del self.health_status[name]
                logger.info(f"Removed monetization platform: {name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove platform {name}: {e}")
            return False


    def get_enabled_platforms(self, product_type: str = None) -> List[str]:
        """Get list of enabled platforms, optionally filtered by product type."""
        enabled = []
        for name, config in self.configs.items():
            if not config.enabled:
                continue

            if product_type and product_type not in config.product_types:
                continue

            enabled.append(name)

        # Sort by priority (lower number = higher priority)
        enabled.sort(key = lambda x: self.configs[x].priority)
        return enabled


    def create_product_multi_platform(
        self,
            product: Product,
            platforms: Optional[List[str]] = None,
            parallel: bool = True,
            ) -> MultiPlatformResult:
        """Create a product across multiple platforms."""
        if platforms is None:
            platforms = self.get_enabled_platforms(product.category)

        results = {}
        errors = {}

        if parallel and len(platforms) > 1:
            # Parallel execution
            with ThreadPoolExecutor(max_workers = min(len(platforms), 5)) as executor:
                future_to_platform = {
                    executor.submit(
                        self._create_product_single, platform, product
                    ): platform
                    for platform in platforms
                    if platform in self.platforms
                }

                for future in as_completed(future_to_platform):
                    platform = future_to_platform[future]
                    try:
                        result = future.result(timeout = 30)
                        results[platform] = result
                    except Exception as e:
                        errors[platform] = str(e)
                        logger.error(f"Failed to create product on {platform}: {e}")
        else:
            # Sequential execution
            for platform in platforms:
                if platform not in self.platforms:
                    errors[platform] = "Platform not configured"
                    continue

                try:
                    result = self._create_product_single(platform, product)
                    results[platform] = result
                except Exception as e:
                    errors[platform] = str(e)
                    logger.error(f"Failed to create product on {platform}: {e}")

        success_count = sum(1 for r in results.values() if r.success)
        failure_count = len(platforms) - success_count

        return MultiPlatformResult(
            success_count = success_count,
                failure_count = failure_count,
                results = results,
                errors = errors,
                total_platforms = len(platforms),
                )


    def _create_product_single(
        self, platform: str, product: Product
    ) -> ProductResponse:
        """Create product on a single platform."""
        api_client = self.platforms[platform]
        return api_client.create_product(product)


    def get_sales_data_multi_platform(
        self,
            start_date: datetime,
            end_date: datetime,
            platforms: Optional[List[str]] = None,
            ) -> Dict[str, Any]:
        """Get sales data from multiple platforms."""
        if platforms is None:
            platforms = self.get_enabled_platforms()

        all_sales_data = {}
        total_revenue = 0.0
        total_sales = 0

        with ThreadPoolExecutor(max_workers = min(len(platforms), 5)) as executor:
            future_to_platform = {
                executor.submit(
                    self._get_sales_data_single, platform, start_date, end_date
                ): platform
                for platform in platforms
                if platform in self.platforms
            }

            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    sales_data = future.result(timeout = 30)
                    all_sales_data[platform] = sales_data

                    # Aggregate totals
                    if "total_revenue" in sales_data:
                        total_revenue += sales_data["total_revenue"]
                    if "total_sales" in sales_data:
                        total_sales += sales_data["total_sales"]

                except Exception as e:
                    logger.error(f"Failed to get sales data from {platform}: {e}")
                    all_sales_data[platform] = {"error": str(e)}

        return {
            "period": f"{start_date.date()} to {end_date.date()}",
                "total_revenue": total_revenue,
                "total_sales": total_sales,
                "platforms": all_sales_data,
                "generated_at": datetime.now().isoformat(),
                }


    def _get_sales_data_single(
        self, platform: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get sales data from a single platform."""
        api_client = self.platforms[platform]
        return api_client.get_sales_data(start_date, end_date)


    def health_check_all_platforms(
        self, force_refresh: bool = False
    ) -> Dict[str, bool]:
        """Check health of all configured platforms."""
        # Check if we need to refresh (cache for 5 minutes)
        if (
            not force_refresh
            and self.last_health_check
            and datetime.now() - self.last_health_check < timedelta(minutes = 5)
        ):
            return self.health_status

        health_results = {}

        with ThreadPoolExecutor(max_workers = min(len(self.platforms), 5)) as executor:
            future_to_platform = {
                executor.submit(self._health_check_single, platform): platform
                for platform in self.platforms.keys()
            }

            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    is_healthy = future.result(timeout = 10)
                    health_results[platform] = is_healthy
                except Exception as e:
                    logger.error(f"Health check failed for {platform}: {e}")
                    health_results[platform] = False

        self.health_status = health_results
        self.last_health_check = datetime.now()
        return health_results


    def _health_check_single(self, platform: str) -> bool:
        """Health check for a single platform."""
        api_client = self.platforms[platform]
        return api_client.health_check()


    def get_platform_analytics(self, platform: str) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific platform."""
        if platform not in self.platforms:
            return {"error": f"Platform {platform} not configured"}

        try:
            api_client = self.platforms[platform]

            # Get recent sales data (last 30 days)
            end_date = datetime.now()
            start_date = end_date - timedelta(days = 30)
            sales_data = api_client.get_sales_data(start_date, end_date)

            # Get product count
            products = api_client.list_products(limit = 1)

            analytics = {
                "platform": platform,
                    "health_status": self._health_check_single(platform),
                    "recent_sales": sales_data,
                    "product_count": len(products) if isinstance(products, list) else 0,
                    "generated_at": datetime.now().isoformat(),
                    }

            # Platform - specific analytics
            if hasattr(api_client, "get_analytics_summary"):
                platform_analytics = api_client.get_analytics_summary()
                analytics["platform_specific"] = platform_analytics

            return analytics

        except Exception as e:
            logger.error(f"Failed to get analytics for {platform}: {e}")
            return {"error": str(e)}


    def get_comprehensive_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data from all platforms."""
        dashboard = {
            "generated_at": datetime.now().isoformat(),
                "platforms": {},
                "summary": {
                "total_platforms": len(self.platforms),
                    "healthy_platforms": 0,
                    "total_revenue_30d": 0.0,
                    "total_sales_30d": 0,
                    },
                }

        # Health check all platforms
        health_status = self.health_check_all_platforms()
        dashboard["summary"]["healthy_platforms"] = sum(health_status.values())

        # Get analytics for each platform
        for platform in self.platforms.keys():
            analytics = self.get_platform_analytics(platform)
            dashboard["platforms"][platform] = analytics

            # Aggregate summary data
            if (
                "recent_sales" in analytics
                and "total_revenue" in analytics["recent_sales"]
            ):
                dashboard["summary"]["total_revenue_30d"] += analytics["recent_sales"][
                    "total_revenue"
                ]
            if (
                "recent_sales" in analytics
                and "total_sales" in analytics["recent_sales"]
            ):
                dashboard["summary"]["total_sales_30d"] += analytics["recent_sales"][
                    "total_sales"
                ]

        return dashboard


    def optimize_product_distribution(self, product: Product) -> Dict[str, Any]:
        """Analyze and recommend optimal platform distribution for a product."""
        recommendations = {
            "product_type": product.category,
                "recommended_platforms": [],
                "analysis": {},
                "generated_at": datetime.now().isoformat(),
                }

        # Platform suitability analysis
        platform_scores = {}

        for platform_name, config in self.configs.items():
            if not config.enabled:
                continue

            score = 0
            analysis = {"reasons": []}

            # Check product type compatibility
            if product.category in config.product_types:
                score += 30
                analysis["reasons"].append(f"Supports {product.category} products")

            # Platform - specific scoring
            if platform_name == "etsy":
                if product.category in ["handmade", "vintage", "craft_supplies"]:
                    score += 40
                    analysis["reasons"].append("Excellent for handmade / vintage items")
                if product.tags and any(
                    tag in ["handmade", "vintage", "craft"] for tag in product.tags
                ):
                    score += 20

            elif platform_name == "gumroad":
                if product.category == "digital":
                    score += 40
                    analysis["reasons"].append("Optimized for digital products")
                if product.digital_files:
                    score += 20
                    analysis["reasons"].append("Has digital files to deliver")

            elif platform_name == "paddle":
                if product.category in ["software", "saas", "digital"]:
                    score += 35
                    analysis["reasons"].append("Great for software / SaaS products")
                if product.price > 10:  # Higher - value products
                    score += 15
                    analysis["reasons"].append("Good for higher - value products")

            elif platform_name == "sendowl":
                if product.category == "digital":
                    score += 35
                    analysis["reasons"].append("Strong digital product platform")
                if product.metadata.get("affiliate_program"):
                    score += 25
                    analysis["reasons"].append("Excellent affiliate management")

            # Health status bonus
            if self.health_status.get(platform_name, False):
                score += 10
                analysis["reasons"].append("Platform is healthy and operational")

            # Priority bonus (lower number = higher priority)
            priority_bonus = max(0, 10 - config.priority)
            score += priority_bonus

            platform_scores[platform_name] = {"score": score, "analysis": analysis}

        # Sort by score and recommend top platforms
        sorted_platforms = sorted(
            platform_scores.items(), key = lambda x: x[1]["score"], reverse = True
        )

        recommendations["recommended_platforms"] = [
            {
                "platform": platform,
                    "score": data["score"],
                    "reasons": data["analysis"]["reasons"],
                    }
            for platform, data in sorted_platforms[:3]  # Top 3 recommendations
            if data["score"] > 20  # Minimum viable score
        ]

        recommendations["analysis"] = platform_scores

        return recommendations


    def _load_config(self, config_file: str):
        """Load configuration from file (JSON / YAML)."""
        # Implementation would load from config file
        # For now, this is a placeholder
        logger.info(f"Would load configuration from {config_file}")


    def get_status_summary(self) -> Dict[str, Any]:
        """Get a quick status summary of the monetization manager."""
        return {
            "total_platforms": len(self.platforms),
                "enabled_platforms": len(self.get_enabled_platforms()),
                "healthy_platforms": (
                sum(self.health_status.values()) if self.health_status else 0
            ),
                "last_health_check": (
                self.last_health_check.isoformat() if self.last_health_check else None
            ),
                "configured_platforms": list(self.platforms.keys()),
                }
