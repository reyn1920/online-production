#!/usr/bin/env python3
""""""
Auto Discovery Service

Automatically researches and adds new APIs when marketing channels are added.
Integrates web search, API discovery, and cost tracking services.
""""""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .api_discovery_service import APIDiscoveryService
from .cost_tracking_service import CostTrackingService

# Import our custom services

from .web_search_service import APICandidate, WebSearchService


@dataclass
class ChannelProfile:
    """Profile for a marketing channel with discovery preferences."""

    name: str
    category: str
    priority_features: List[str]
    budget_limit: float
    preferred_pricing: str  # 'free', 'freemium', 'paid'
    auto_discovery_enabled: bool
    last_discovery_run: Optional[datetime] = None
    discovery_frequency_days: int = 7


@dataclass
class DiscoveryResult:
    """Result of an auto - discovery operation."""

    channel: str
    discovered_apis: List[APICandidate]
    recommended_apis: List[APICandidate]
    cost_analysis: Dict[str, Any]
    discovery_timestamp: datetime
    next_discovery_date: datetime


class AutoDiscoveryService:
    """Service for automatically discovering and managing APIs for channels."""

    def __init__(self, db_path: str = "auto_discovery.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path

        # Initialize component services
        self.web_search = WebSearchService()
        self.api_discovery = APIDiscoveryService()
        self.cost_tracking = CostTrackingService()

        # Initialize database
        self._init_database()

        # Default channel profiles
        self.default_profiles = {
            "youtube": ChannelProfile(
                name="YouTube",
                category="video_marketing",
                priority_features=["analytics", "upload", "monetization"],
                budget_limit=50.0,
                preferred_pricing="freemium",
                auto_discovery_enabled=True,
                discovery_frequency_days=14,
# BRACKET_SURGEON: disabled
#             ),
            "tiktok": ChannelProfile(
                name="TikTok",
                category="short_video",
                priority_features=["trending", "hashtags", "analytics"],
                budget_limit=30.0,
                preferred_pricing="free",
                auto_discovery_enabled=True,
                discovery_frequency_days=7,
# BRACKET_SURGEON: disabled
#             ),
            "instagram": ChannelProfile(
                name="Instagram",
                category="social_media",
                priority_features=["stories", "reels", "analytics"],
                budget_limit=40.0,
                preferred_pricing="freemium",
                auto_discovery_enabled=True,
                discovery_frequency_days=10,
# BRACKET_SURGEON: disabled
#             ),
            "email": ChannelProfile(
                name="Email Marketing",
                category="email",
                priority_features=["automation", "templates", "analytics"],
                budget_limit=25.0,
                preferred_pricing="freemium",
                auto_discovery_enabled=True,
                discovery_frequency_days=30,
# BRACKET_SURGEON: disabled
#             ),
            "sms": ChannelProfile(
                name="SMS Marketing",
                category="messaging",
                priority_features=["bulk_send", "automation", "delivery_reports"],
                budget_limit=20.0,
                preferred_pricing="freemium",
                auto_discovery_enabled=True,
                discovery_frequency_days=21,
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

    def _init_database(self):
        """Initialize the auto - discovery database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Channel profiles table
                cursor.execute(
                    """"""
                    CREATE TABLE IF NOT EXISTS channel_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT UNIQUE NOT NULL,
                            category TEXT NOT NULL,
                            priority_features TEXT NOT NULL,
                            budget_limit REAL NOT NULL,
                            preferred_pricing TEXT NOT NULL,
                            auto_discovery_enabled BOOLEAN NOT NULL,
                            last_discovery_run TEXT,
                            discovery_frequency_days INTEGER NOT NULL,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                # Discovery history table
                cursor.execute(
                    """"""
                    CREATE TABLE IF NOT EXISTS discovery_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            channel TEXT NOT NULL,
                            discovery_timestamp TEXT NOT NULL,
                            apis_discovered INTEGER NOT NULL,
                            apis_recommended INTEGER NOT NULL,
                            total_cost_estimate REAL,
                            discovery_data TEXT NOT NULL,
                            created_at TEXT NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                # API recommendations table
                cursor.execute(
                    """"""
                    CREATE TABLE IF NOT EXISTS api_recommendations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            channel TEXT NOT NULL,
                            api_name TEXT NOT NULL,
                            provider TEXT NOT NULL,
                            pricing_model TEXT NOT NULL,
                            quality_score REAL NOT NULL,
                            recommendation_reason TEXT,
                            status TEXT DEFAULT 'pending',
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                conn.commit()
                self.logger.info("Auto - discovery database initialized")

        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")

    def add_channel(
        self, channel_name: str, custom_profile: Optional[ChannelProfile] = None
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Add a new channel and automatically discover APIs for it."""
        try:
            # Use custom profile or default
            if custom_profile:
                profile = custom_profile
            else:
                profile = self.default_profiles.get(
                    channel_name.lower(),
                    ChannelProfile(
                        name=channel_name,
                        category="general",
                        priority_features=["api_access", "documentation"],
                        budget_limit=25.0,
                        preferred_pricing="freemium",
                        auto_discovery_enabled=True,
# BRACKET_SURGEON: disabled
#                     ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Save profile to database
            self._save_channel_profile(profile)

            # Immediately run discovery for new channel
            if profile.auto_discovery_enabled:
                self.logger.info(
                    f"Running initial API discovery for new channel: {channel_name}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                discovery_result = self.discover_apis_for_channel(channel_name)

                if discovery_result:
                    self.logger.info(
                        f"Discovered {len(discovery_result.discovered_apis)} APIs for {channel_name}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    return True

            return True

        except Exception as e:
            self.logger.error(f"Error adding channel {channel_name}: {e}")
            return False

    def discover_apis_for_channel(self, channel_name: str) -> Optional[DiscoveryResult]:
        """Discover APIs for a specific channel."""
        try:
            # Get channel profile
            profile = self._get_channel_profile(channel_name)
            if not profile:
                self.logger.error(f"No profile found for channel: {channel_name}")
                return None

            self.logger.info(f"Starting API discovery for channel: {channel_name}")

            # Step 1: Web search for APIs
            discovered_apis = self.web_search.search_apis_for_channel(
                channel_name.lower(), max_results=15
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Step 2: Use API discovery service for additional candidates
            additional_apis = self.api_discovery.discover_channel_apis(channel_name)

            # Combine and deduplicate
            all_apis = discovered_apis + additional_apis
            unique_apis = self._deduplicate_apis(all_apis)

            # Step 3: Filter and rank based on channel preferences
            recommended_apis = self._filter_and_rank_apis(unique_apis, profile)

            # Step 4: Cost analysis
            cost_analysis = self._analyze_costs(recommended_apis, profile.budget_limit)

            # Step 5: Create discovery result
            discovery_result = DiscoveryResult(
                channel=channel_name,
                discovered_apis=unique_apis,
                recommended_apis=recommended_apis,
                cost_analysis=cost_analysis,
                discovery_timestamp=datetime.now(),
                next_discovery_date=datetime.now()
                + timedelta(days=profile.discovery_frequency_days),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Step 6: Save results
            self._save_discovery_result(discovery_result)
            self._save_api_recommendations(discovery_result)

            # Step 7: Update channel profile
            profile.last_discovery_run = datetime.now()
            self._save_channel_profile(profile)

            self.logger.info(
                f"Discovery completed for {channel_name}: {len(recommended_apis)} recommended APIs"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return discovery_result

        except Exception as e:
            self.logger.error(f"Error discovering APIs for channel {channel_name}: {e}")
            return None

    def run_scheduled_discovery(self) -> Dict[str, DiscoveryResult]:
        """Run discovery for all channels that are due for updates."""
        results = {}

        try:
            # Get all channels due for discovery
            due_channels = self._get_channels_due_for_discovery()

            self.logger.info(
                f"Running scheduled discovery for {len(due_channels)} channels"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            for channel_name in due_channels:
                result = self.discover_apis_for_channel(channel_name)
                if result:
                    results[channel_name] = result

            return results

        except Exception as e:
            self.logger.error(f"Error running scheduled discovery: {e}")
            return results

    def _deduplicate_apis(self, apis: List[APICandidate]) -> List[APICandidate]:
        """Remove duplicate APIs from the list."""
        seen = set()
        unique_apis = []

        for api in apis:
            key = f"{api.provider.lower()}_{api.name.lower()}"
            if key not in seen:
                seen.add(key)
                unique_apis.append(api)

        return unique_apis

    def _filter_and_rank_apis(
        self, apis: List[APICandidate], profile: ChannelProfile
    ) -> List[APICandidate]:
        """Filter and rank APIs based on channel preferences."""
        filtered_apis = []

        for api in apis:
            # Filter by pricing preference
            if profile.preferred_pricing == "free" and api.pricing_model != "free":
                continue
            elif (
                profile.preferred_pricing == "freemium" and api.pricing_model == "paid"
# BRACKET_SURGEON: disabled
#             ):
                continue

            # Calculate preference score
            preference_score = self._calculate_preference_score(api, profile)

            # Add preference score to quality score
            api.quality_score = (api.quality_score + preference_score) / 2

            filtered_apis.append(api)

        # Sort by quality score
        return sorted(filtered_apis, key=lambda x: x.quality_score, reverse=True)

    def _calculate_preference_score(
        self, api: APICandidate, profile: ChannelProfile
# BRACKET_SURGEON: disabled
#     ) -> float:
        """Calculate how well an API matches channel preferences."""
        score = 0.5  # Base score

        # Check for priority features
        matching_features = set(api.features) & set(profile.priority_features)
        if matching_features:
            score += 0.3 * (len(matching_features) / len(profile.priority_features))

        # Pricing model preference
        pricing_scores = {
            "free": {"free": 0.3, "freemium": 0.1, "paid": 0.0},
            "freemium": {"free": 0.3, "freemium": 0.2, "paid": 0.1},
            "paid": {"free": 0.2, "freemium": 0.2, "paid": 0.2},
# BRACKET_SURGEON: disabled
#         }

        score += pricing_scores.get(profile.preferred_pricing, {}).get(
            api.pricing_model, 0.0
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        return min(1.0, score)

    def _analyze_costs(
        self, apis: List[APICandidate], budget_limit: float
    ) -> Dict[str, Any]:
        """Analyze costs of recommended APIs."""
        analysis = {
            "total_free_apis": len(
                [api for api in apis if api.pricing_model == "free"]
# BRACKET_SURGEON: disabled
#             ),
            "total_freemium_apis": len(
                [api for api in apis if api.pricing_model == "freemium"]
# BRACKET_SURGEON: disabled
#             ),
            "total_paid_apis": len(
                [api for api in apis if api.pricing_model == "paid"]
# BRACKET_SURGEON: disabled
#             ),
            "estimated_monthly_cost": 0.0,
            "within_budget": True,
            "budget_limit": budget_limit,
            "cost_breakdown": [],
# BRACKET_SURGEON: disabled
#         }

        # Estimate costs (simplified)
        for api in apis:
            if api.pricing_model == "paid" and api.cost_estimate:
                # Extract numeric cost (simplified)

                import re

                cost_match = re.search(
                    r"\\$([0 - 9,]+(?:\\.[0 - 9]{2})?)", api.cost_estimate or ""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                if cost_match:
                    cost = float(cost_match.group(1).replace(",", ""))
                    analysis["estimated_monthly_cost"] += cost
                    analysis["cost_breakdown"].append(
                        {
                            "api": api.name,
                            "cost": cost,
                            "pricing_model": api.pricing_model,
# BRACKET_SURGEON: disabled
#                         }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        analysis["within_budget"] = analysis["estimated_monthly_cost"] <= budget_limit

        return analysis

    def _save_channel_profile(self, profile: ChannelProfile):
        """Save channel profile to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                now = datetime.now().isoformat()

                cursor.execute(
                    """"""
                    INSERT OR REPLACE INTO channel_profiles
                    (name, category, priority_features, budget_limit, preferred_pricing,
                        auto_discovery_enabled, last_discovery_run, discovery_frequency_days,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                          created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        profile.name,
                        profile.category,
                        json.dumps(profile.priority_features),
                        profile.budget_limit,
                        profile.preferred_pricing,
                        profile.auto_discovery_enabled,
                        (
                            profile.last_discovery_run.isoformat()
                            if profile.last_discovery_run
                            else None
# BRACKET_SURGEON: disabled
#                         ),
                        profile.discovery_frequency_days,
                        now,
                        now,
# BRACKET_SURGEON: disabled
#                     ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error saving channel profile: {e}")

    def _get_channel_profile(self, channel_name: str) -> Optional[ChannelProfile]:
        """Get channel profile from database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM channel_profiles WHERE name = ?", (channel_name,)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                row = cursor.fetchone()
                if row:
                    return ChannelProfile(
                        name=row[1],
                        category=row[2],
                        priority_features=json.loads(row[3]),
                        budget_limit=row[4],
                        preferred_pricing=row[5],
                        auto_discovery_enabled=bool(row[6]),
                        last_discovery_run=(
                            datetime.fromisoformat(row[7]) if row[7] else None
# BRACKET_SURGEON: disabled
#                         ),
                        discovery_frequency_days=row[8],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                return None

        except Exception as e:
            self.logger.error(f"Error getting channel profile: {e}")
            return None

    def _save_discovery_result(self, result: DiscoveryResult):
        """Save discovery result to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    INSERT INTO discovery_history
                    (channel, discovery_timestamp, apis_discovered, apis_recommended,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         total_cost_estimate, discovery_data, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        result.channel,
                        result.discovery_timestamp.isoformat(),
                        len(result.discovered_apis),
                        len(result.recommended_apis),
                        result.cost_analysis.get("estimated_monthly_cost", 0.0),
                        json.dumps(asdict(result), default=str),
                        datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error saving discovery result: {e}")

    def _save_api_recommendations(self, result: DiscoveryResult):
        """Save API recommendations to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                now = datetime.now().isoformat()

                for api in result.recommended_apis[:5]:  # Save top 5 recommendations
                    cursor.execute(
                        """"""
                        INSERT OR REPLACE INTO api_recommendations
                        (channel, api_name, provider, pricing_model, quality_score,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             recommendation_reason, status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ""","""
                        (
                            result.channel,
                            api.name,
                            api.provider,
                            api.pricing_model,
                            api.quality_score,
                            f"High quality score ({api.quality_score:.2f}) with {api.pricing_model} pricing",
                            "pending",
                            now,
                            now,
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error saving API recommendations: {e}")

    def _get_channels_due_for_discovery(self) -> List[str]:
        """Get channels that are due for discovery updates."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                now = datetime.now()

                cursor.execute(
                    """"""
                    SELECT name, last_discovery_run, discovery_frequency_days
                    FROM channel_profiles
                    WHERE auto_discovery_enabled = 1
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                due_channels = []

                for row in cursor.fetchall():
                    name, last_run_str, frequency_days = row

                    if not last_run_str:
                        # Never run before
                        due_channels.append(name)
                    else:
                        last_run = datetime.fromisoformat(last_run_str)
                        next_run = last_run + timedelta(days=frequency_days)

                        if now >= next_run:
                            due_channels.append(name)

                return due_channels

        except Exception as e:
            self.logger.error(f"Error getting channels due for discovery: {e}")
            return []

    def get_channel_recommendations(self, channel_name: str) -> List[Dict[str, Any]]:
        """Get API recommendations for a channel."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    SELECT api_name, provider, pricing_model, quality_score,
                        recommendation_reason, status, created_at
                    FROM api_recommendations
                    WHERE channel = ?
                    ORDER BY quality_score DESC
                ""","""
                    (channel_name,),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                recommendations = []
                for row in cursor.fetchall():
                    recommendations.append(
                        {
                            "api_name": row[0],
                            "provider": row[1],
                            "pricing_model": row[2],
                            "quality_score": row[3],
                            "recommendation_reason": row[4],
                            "status": row[5],
                            "created_at": row[6],
# BRACKET_SURGEON: disabled
#                         }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                return recommendations

        except Exception as e:
            self.logger.error(f"Error getting channel recommendations: {e}")
            return []

    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get overall discovery statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Total channels
                cursor.execute("SELECT COUNT(*) FROM channel_profiles")
                total_channels = cursor.fetchone()[0]

                # Active channels
                cursor.execute(
                    "SELECT COUNT(*) FROM channel_profiles WHERE auto_discovery_enabled = 1"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                active_channels = cursor.fetchone()[0]

                # Total discoveries
                cursor.execute("SELECT COUNT(*) FROM discovery_history")
                total_discoveries = cursor.fetchone()[0]

                # Total recommendations
                cursor.execute("SELECT COUNT(*) FROM api_recommendations")
                total_recommendations = cursor.fetchone()[0]

                # Recent activity
                cursor.execute(
                    """"""
                    SELECT COUNT(*) FROM discovery_history
                    WHERE created_at > datetime('now', '-7 days')
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                recent_discoveries = cursor.fetchone()[0]

                return {
                    "total_channels": total_channels,
                    "active_channels": active_channels,
                    "total_discoveries": total_discoveries,
                    "total_recommendations": total_recommendations,
                    "recent_discoveries": recent_discoveries,
                    "discovery_rate": (
                        recent_discoveries / 7 if recent_discoveries > 0 else 0
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            self.logger.error(f"Error getting discovery stats: {e}")
            return {}


# CLI interface for auto - discovery service
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="Auto Discovery Service CLI")
    parser.add_argument(
        "--action",
        choices=["add - channel", "discover", "scheduled", "stats", "recommendations"],
        required=True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--channel", help="Channel name")
    parser.add_argument("--budget", type=float, help="Budget limit for channel")
    parser.add_argument(
        "--pricing",
        choices=["free", "freemium", "paid"],
        help="Preferred pricing model",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    args = parser.parse_args()

    service = AutoDiscoveryService()

    if args.action == "add - channel" and args.channel:
        # Create custom profile if budget/pricing specified
        profile = None
        if args.budget or args.pricing:
            profile = ChannelProfile(
                name=args.channel,
                category="custom",
                priority_features=["api_access", "documentation"],
                budget_limit=args.budget or 25.0,
                preferred_pricing=args.pricing or "freemium",
                auto_discovery_enabled=True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        success = service.add_channel(args.channel, profile)
        print(
            f"Channel '{args.channel}' {'added successfully' if success else 'failed to add'}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

    elif args.action == "discover" and args.channel:
        result = service.discover_apis_for_channel(args.channel)
        if result:
            print(f"\\nDiscovery Results for {args.channel}:")
            print(f"Discovered APIs: {len(result.discovered_apis)}")
            print(f"Recommended APIs: {len(result.recommended_apis)}")
            print(
                f"Estimated Monthly Cost: ${result.cost_analysis.get('estimated_monthly_cost',"
# BRACKET_SURGEON: disabled
#     0):.2f}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            print(
                f"Within Budget: {result.cost_analysis.get('within_budget', 'Unknown')}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            print("\\nTop Recommendations:")
            for api in result.recommended_apis[:3]:
                print(
                    f"  {api.name} ({api.provider}) - {api.pricing_model} - Score: {api.quality_score:.2f}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

    elif args.action == "scheduled":
        results = service.run_scheduled_discovery()
        print(f"Scheduled discovery completed for {len(results)} channels:")
        for channel, result in results.items():
            print(f"  {channel}: {len(result.recommended_apis)} recommendations")

    elif args.action == "stats":
        stats = service.get_discovery_stats()
        print("\\nDiscovery Statistics:")
        for key, value in stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")

    elif args.action == "recommendations" and args.channel:
        recommendations = service.get_channel_recommendations(args.channel)
        print(f"\\nRecommendations for {args.channel}:")
        for rec in recommendations:
            print(
                f"  {rec['api_name']} ({rec['provider']}) - {rec['pricing_model']} - Score: {rec['quality_score']:.2f}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    else:
        parser.print_help()