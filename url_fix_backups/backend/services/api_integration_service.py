#!/usr / bin / env python3
""""""
API Integration Service

Integrates all discovery services and updates the API management table with
discovered APIs, login information, and cost tracking.
""""""

import json
import logging
import os
import re
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from .api_discovery_service import APIDiscoveryService

# Import our services

from .auto_discovery_service import AutoDiscoveryService
from .cost_tracking_service import CostTrackingService
from .web_search_service import WebSearchService

@dataclass


class APIEntry:
    """Complete API entry for the management table."""

    category: str
    api_name: str
    provider: str
    status: str  # 'free', 'freemium', 'paid', 'disabled'
    cost_monthly: float
    environment_variables: List[str]
    signup_url: str
    login_url: str
    documentation_url: str
    api_url: str
    features: List[str]
    rate_limits: Optional[str]
    quality_score: float
    notes: str
    last_updated: datetime
    auto_discovered: bool = False


class APIIntegrationService:
    """Service for integrating all API discovery and management functionality."""


    def __init__(self, db_path: str = "api_integration.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path

        # Initialize component services
        self.auto_discovery = AutoDiscoveryService()
        self.web_search = WebSearchService()
        self.api_discovery = APIDiscoveryService()
        self.cost_tracking = CostTrackingService()

        # Initialize database
        self._init_database()

        # Load existing API management data
        self._load_existing_apis()


    def _init_database(self):
        """Initialize the integration database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Main API management table
                cursor.execute(
                    """"""
                    CREATE TABLE IF NOT EXISTS api_management (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            category TEXT NOT NULL,
                            api_name TEXT NOT NULL,
                            provider TEXT NOT NULL,
                            status TEXT NOT NULL,
                            cost_monthly REAL NOT NULL DEFAULT 0.0,
                            environment_variables TEXT NOT NULL,
                            signup_url TEXT NOT NULL,
                            login_url TEXT NOT NULL,
                            documentation_url TEXT NOT NULL,
                            api_url TEXT NOT NULL,
                            features TEXT NOT NULL,
                            rate_limits TEXT,
                            quality_score REAL NOT NULL DEFAULT 0.0,
                            notes TEXT NOT NULL DEFAULT '',
                            last_updated TEXT NOT NULL,
                            auto_discovered BOOLEAN DEFAULT 0,
                            UNIQUE(category, api_name, provider)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                # Login credentials table (encrypted in production)
                cursor.execute(
                    """"""
                    CREATE TABLE IF NOT EXISTS api_credentials (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                            api_id INTEGER NOT NULL,
                            credential_type TEXT NOT NULL,
                            credential_name TEXT NOT NULL,
                            credential_value TEXT,
                            is_environment_variable BOOLEAN DEFAULT 1,
                            notes TEXT,
                            created_at TEXT NOT NULL,
                            updated_at TEXT NOT NULL,
                            FOREIGN KEY (api_id) REFERENCES api_management (id)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                conn.commit()
                self.logger.info("API integration database initialized")

        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")


    def _load_existing_apis(self):
        """Load existing APIs from the management table."""
        try:
            # Pre - populate with known free APIs from conversation history
            existing_apis = [
                APIEntry(
                    category="AI & Language Models",
                        api_name="OpenAI GPT - 4 Free Tier",
                        provider="OpenAI",
                        status="freemium",
                        cost_monthly = 0.0,
                        environment_variables=["OPENAI_API_KEY"],
                        signup_url="https://platform.openai.com / signup",
                        login_url="https://platform.openai.com / login",
                        documentation_url="https://platform.openai.com / docs",
                        api_url="https://api.openai.com / v1",
                        features=["text_generation", "chat_completion", "embeddings"],
                        rate_limits="3 RPM, 200 RPD for free tier",
                        quality_score = 0.95,
                        notes="Free tier with limited requests. Upgrade for production use.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
                    APIEntry(
                    category="AI & Language Models",
                        api_name="Hugging Face Inference API",
                        provider="Hugging Face",
                        status="freemium",
                        cost_monthly = 0.0,
                        environment_variables=["HUGGINGFACE_API_KEY"],
                        signup_url="https://huggingface.co / join",
                        login_url="https://huggingface.co / login",
                        documentation_url="https://huggingface.co / docs / api - inference",
                        api_url="https://api - inference.huggingface.co",
                        features=["text_generation", "sentiment_analysis", "translation"],
                        rate_limits="1000 requests / month free",
                        quality_score = 0.85,
                        notes="Free tier for testing. Many open - source models available.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
                    APIEntry(
                    category="Email Marketing",
                        api_name="Mailgun Free Tier",
                        provider="Mailgun",
                        status="freemium",
                        cost_monthly = 0.0,
                        environment_variables=["MAILGUN_API_KEY", "MAILGUN_DOMAIN"],
                        signup_url="https://signup.mailgun.com / new / signup",
                        login_url="https://login.mailgun.com / login",
                        documentation_url="https://documentation.mailgun.com",
                        api_url="https://api.mailgun.net / v3",
                        features=["transactional_email", "analytics", "webhooks"],
                        rate_limits="5,000 emails / month free",
                        quality_score = 0.90,
                        notes="Reliable email delivery with good free tier.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
                    APIEntry(
                    category="SMS Marketing",
                        api_name="Twilio Free Trial",
                        provider="Twilio",
                        status="freemium",
                        cost_monthly = 0.0,
                        environment_variables=["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"],
                        signup_url="https://www.twilio.com / try - twilio",
                        login_url="https://www.twilio.com / login",
                        documentation_url="https://www.twilio.com / docs",
                        api_url="https://api.twilio.com",
                        features=["sms", "voice", "whatsapp", "verification"],
                        rate_limits="$15.50 free trial credit",
                        quality_score = 0.92,
                        notes="Industry standard for SMS. Free trial credit included.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
                    APIEntry(
                    category="Social Media Platforms",
                        api_name="YouTube Data API v3",
                        provider="Google",
                        status="freemium",
                        cost_monthly = 0.0,
                        environment_variables=["YOUTUBE_API_KEY"],
                        signup_url="https://console.developers.google.com",
                        login_url="https://accounts.google.com / signin",
                        documentation_url="https://developers.google.com / youtube / v3",
                        api_url="https://www.googleapis.com / youtube / v3",
                        features=["video_data", "channel_info", "analytics", "search"],
                        rate_limits="10,000 units / day free",
                        quality_score = 0.88,
                        notes="Official YouTube API with generous free tier.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
                    APIEntry(
                    category="Social Media Platforms",
                        api_name="Instagram Basic Display API",
                        provider="Meta",
                        status="free",
                        cost_monthly = 0.0,
                        environment_variables=[
                        "INSTAGRAM_ACCESS_TOKEN",
                            "INSTAGRAM_CLIENT_ID",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ],
                        signup_url="https://developers.facebook.com / apps",
                        login_url="https://www.facebook.com / login",
                        documentation_url="https://developers.facebook.com / docs / instagram - basic - display - api",
                        api_url="https://graph.instagram.com",
                        features=["user_media", "user_profile", "media_insights"],
                        rate_limits="200 requests / hour per user",
                        quality_score = 0.75,
                        notes="Basic access to Instagram data. Limited functionality.",
                        last_updated = datetime.now(),
# BRACKET_SURGEON: disabled
#                         ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]

            # Save to database
            for api in existing_apis:
                self._save_api_entry(api)

            self.logger.info(f"Loaded {len(existing_apis)} existing APIs")

        except Exception as e:
            self.logger.error(f"Error loading existing APIs: {e}")


    def discover_and_integrate_apis(self, channel: str) -> Dict[str, Any]:
        """Discover APIs for a channel and integrate them into the management table."""
        try:
            self.logger.info(
                f"Starting API discovery and integration for channel: {channel}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Step 1: Run auto - discovery
            discovery_result = self.auto_discovery.discover_apis_for_channel(channel)

            if not discovery_result:
                return {"success": False, "error": "Discovery failed"}

            # Step 2: Process discovered APIs
            integrated_apis = []

            for api_candidate in discovery_result.recommended_apis:
                # Convert to API entry
                api_entry = self._convert_candidate_to_entry(api_candidate, channel)

                # Add login information
                api_entry = self._enhance_with_login_info(api_entry)

                # Save to management table
                self._save_api_entry(api_entry)

                # Track costs
                self._track_api_costs(api_entry)

                integrated_apis.append(api_entry)

            # Step 3: Update API management table file
            self._update_management_table_file()

            result = {
                "success": True,
                    "channel": channel,
                    "apis_discovered": len(discovery_result.discovered_apis),
                    "apis_integrated": len(integrated_apis),
                    "cost_analysis": discovery_result.cost_analysis,
                    "integrated_apis": [
                    {
                        "name": api.api_name,
                            "provider": api.provider,
                            "status": api.status,
                            "signup_url": api.signup_url,
                            "quality_score": api.quality_score,
# BRACKET_SURGEON: disabled
#                             }
                    for api in integrated_apis
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ],
# BRACKET_SURGEON: disabled
#                     }

            self.logger.info(
                f"Successfully integrated {len(integrated_apis)} APIs for {channel}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return result

        except Exception as e:
            self.logger.error(f"Error in discover_and_integrate_apis: {e}")
            return {"success": False, "error": str(e)}


    def _convert_candidate_to_entry(self, candidate, channel: str) -> APIEntry:
        """Convert an API candidate to a complete API entry."""
        # Map channel to category
        category_mapping = {
            "youtube": "Social Media Platforms",
                "tiktok": "Social Media Platforms",
                "instagram": "Social Media Platforms",
                "email": "Email Marketing",
                "sms": "SMS Marketing",
                "ai_content": "AI & Language Models",
# BRACKET_SURGEON: disabled
#                 }

        category = category_mapping.get(channel.lower(), "Other Services")

        # Generate environment variables
        env_vars = self._generate_environment_variables(
            candidate.name, candidate.provider
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Generate login URL from signup URL
        login_url = self._generate_login_url(candidate.signup_url)

        return APIEntry(
            category = category,
                api_name = candidate.name,
                provider = candidate.provider,
                status = candidate.pricing_model,
                cost_monthly = self._extract_monthly_cost(candidate.cost_estimate),
                environment_variables = env_vars,
                signup_url = candidate.signup_url,
                login_url = login_url,
                documentation_url = candidate.documentation_url,
                api_url = candidate.api_url,
                features = candidate.features,
                rate_limits = candidate.rate_limits,
                quality_score = candidate.quality_score,
                notes = f"Auto - discovered API. {candidate.pricing_model.title()} pricing model.",
                last_updated = datetime.now(),
                auto_discovered = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )


    def _enhance_with_login_info(self, api_entry: APIEntry) -> APIEntry:
        """Enhance API entry with login information and credentials."""
        try:
            # Common login URL patterns
            base_domain = self._extract_base_domain(api_entry.signup_url)

            if not api_entry.login_url or api_entry.login_url == api_entry.signup_url:
                # Generate likely login URL
                login_patterns = [
                    f"{base_domain}/login",
                        f"{base_domain}/signin",
                        f"{base_domain}/auth / login",
                        f"{base_domain}/account / login",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ]

                # Use the first pattern (in production, verify these exist)
                api_entry.login_url = login_patterns[0]

            # Add credential information
            self._add_credential_info(api_entry)

            return api_entry

        except Exception as e:
            self.logger.error(f"Error enhancing login info: {e}")
            return api_entry


    def _generate_environment_variables(
        self, api_name: str, provider: str
    ) -> List[str]:
        """Generate likely environment variable names for an API."""
        # Clean names for environment variables
        clean_provider = re.sub(r"[^a - zA - Z0 - 9]", "_", provider.upper())
        clean_api = re.sub(r"[^a - zA - Z0 - 9]", "_", api_name.upper())

        # Common patterns
        env_vars = [
            f"{clean_provider}_API_KEY",
                f"{clean_provider}_SECRET_KEY",
                f"{clean_api}_API_KEY",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        # Remove duplicates and return
        return list(set(env_vars))


    def _generate_login_url(self, signup_url: str) -> str:
        """Generate login URL from signup URL."""
        try:
            base_domain = self._extract_base_domain(signup_url)
            return f"{base_domain}/login"
        except Exception:
            return signup_url


    def _extract_base_domain(self, url: str) -> str:
        """Extract base domain from URL."""

        from urllib.parse import urlparse

        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"


    def _extract_monthly_cost(self, cost_estimate: Optional[str]) -> float:
        """Extract monthly cost from cost estimate string."""
        if not cost_estimate:
            return 0.0

        # Look for dollar amounts

        import re

        match = re.search(r"\\$([0 - 9,]+(?:\\.[0 - 9]{2})?)", cost_estimate)
        if match:
            return float(match.group(1).replace(",", ""))

        return 0.0


    def _add_credential_info(self, api_entry: APIEntry):
        """Add credential information for an API."""
        try:
            # This would be expanded with actual credential management
            # For now, just log the environment variables needed
            self.logger.info(
                f"API {api_entry.api_name} requires: {', '.join(api_entry.environment_variables)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        except Exception as e:
            self.logger.error(f"Error adding credential info: {e}")


    def _save_api_entry(self, api_entry: APIEntry):
        """Save API entry to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    INSERT OR REPLACE INTO api_management
                    (category,
    api_name,
    provider,
    status,
    cost_monthly,
    environment_variables,
                        signup_url, login_url, documentation_url, api_url, features, rate_limits,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                          quality_score, notes, last_updated, auto_discovered)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        api_entry.category,
                            api_entry.api_name,
                            api_entry.provider,
                            api_entry.status,
                            api_entry.cost_monthly,
                            json.dumps(api_entry.environment_variables),
                            api_entry.signup_url,
                            api_entry.login_url,
                            api_entry.documentation_url,
                            api_entry.api_url,
                            json.dumps(api_entry.features),
                            api_entry.rate_limits,
                            api_entry.quality_score,
                            api_entry.notes,
                            api_entry.last_updated.isoformat(),
                            api_entry.auto_discovered,
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                conn.commit()

        except Exception as e:
            self.logger.error(f"Error saving API entry: {e}")


    def _track_api_costs(self, api_entry: APIEntry):
        """Track API costs using the cost tracking service."""
        try:
            if api_entry.cost_monthly > 0:
                # This would integrate with the cost tracking service
                self.logger.info(
                    f"Tracking costs for {api_entry.api_name}: ${api_entry.cost_monthly}/month"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        except Exception as e:
            self.logger.error(f"Error tracking API costs: {e}")


    def _update_management_table_file(self):
        """Update the API management table markdown file."""
        try:
            # Get all APIs from database
            apis = self._get_all_apis()

            # Generate markdown content
            markdown_content = self._generate_markdown_table(apis)

            # Write to file
            table_file_path = (
                "/Users / thomasbrianreynolds / online production / api_management_table.md"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            with open(table_file_path, "w") as f:
                f.write(markdown_content)

            self.logger.info(f"Updated API management table file with {len(apis)} APIs")

        except Exception as e:
            self.logger.error(f"Error updating management table file: {e}")


    def _get_all_apis(self) -> List[APIEntry]:
        """Get all APIs from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    SELECT category, api_name, provider, status, cost_monthly, environment_variables,
                        signup_url, login_url, documentation_url, api_url, features, rate_limits,
                               quality_score, notes, last_updated, auto_discovered
                    FROM api_management
                    ORDER BY category, quality_score DESC
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                apis = []
                for row in cursor.fetchall():
                    api = APIEntry(
                        category = row[0],
                            api_name = row[1],
                            provider = row[2],
                            status = row[3],
                            cost_monthly = row[4],
                            environment_variables = json.loads(row[5]),
                            signup_url = row[6],
                            login_url = row[7],
                            documentation_url = row[8],
                            api_url = row[9],
                            features = json.loads(row[10]),
                            rate_limits = row[11],
                            quality_score = row[12],
                            notes = row[13],
                            last_updated = datetime.fromisoformat(row[14]),
                            auto_discovered = bool(row[15]),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                    apis.append(api)

                return apis

        except Exception as e:
            self.logger.error(f"Error getting all APIs: {e}")
            return []


    def _generate_markdown_table(self, apis: List[APIEntry]) -> str:
        """Generate markdown table from API entries."""
        content = "# API Management Table\\n\\n""
        content += "*Last updated: {}*\\n\\n".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Group by category
        categories = {}
        for api in apis:
            if api.category not in categories:
                categories[api.category] = []
            categories[api.category].append(api)

        for category, category_apis in categories.items():
            content += f"## {category}\\n\\n""

            # Table header
            content += "| API Name | Provider | Status | Cost / Month | Signup | Login | Documentation | Environment Variables | Rate Limits | Quality Score | Notes |\\n"
            content += "|----------|----------|--------|------------|--------|-------|---------------|---------------------|-------------|---------------|-------|\\n"

            # Table rows
            for api in category_apis:
                status_badge = self._get_status_badge(api.status)
                cost_display = (
                    f"${api.cost_monthly:.2f}" if api.cost_monthly > 0 else "Free"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                env_vars = ", ".join(api.environment_variables[:2])  # Show first 2
                if len(api.environment_variables) > 2:
                    env_vars += "..."

                quality_display = f"{api.quality_score:.2f}⭐"

                content += f"| [{api.api_name}]({api.api_url}) | {api.provider} | {status_badge} | {cost_display} | [Signup]({api.signup_url}) | [Login]({api.login_url}) | [Docs]({api.documentation_url}) | `{env_vars}` | {api.rate_limits \"
#     or 'N / A'} | {quality_display} | {api.notes[:50]}{'...' if len(api.notes) > 50 else ''} |\\n"

            content += "\\n"

        # Add summary section
        content += "## Summary\\n\\n""

        total_apis = len(apis)
        free_apis = len([api for api in apis if api.status == "free"])
        freemium_apis = len([api for api in apis if api.status == "freemium"])
        paid_apis = len([api for api in apis if api.status == "paid"])
        total_cost = sum(api.cost_monthly for api in apis)
        auto_discovered = len([api for api in apis if api.auto_discovered])

        content += f"- **Total APIs**: {total_apis}\\n"
        content += f"- **Free APIs**: {free_apis}\\n"
        content += f"- **Freemium APIs**: {freemium_apis}\\n"
        content += f"- **Paid APIs**: {paid_apis}\\n"
        content += f"- **Auto - discovered**: {auto_discovered}\\n"
        content += f"- **Total Monthly Cost**: ${total_cost:.2f}\\n\\n"

        # Add environment variables checklist
        content += "## Environment Variables Checklist\\n\\n""
        all_env_vars = set()
        for api in apis:
            all_env_vars.update(api.environment_variables)

        for env_var in sorted(all_env_vars):
            content += f"- [ ] `{env_var}`\\n"

        content += "\\n## Cost Management Strategy\\n\\n""
        content += "1. **Free Tier First**: Always start with free tiers to test functionality\\n"
        content += "2. **Monitor Usage**: Track API usage to avoid unexpected charges\\n"
        content += "3. **Set Alerts**: Configure billing alerts for paid services\\n"
        content += "4. **Regular Review**: Review and optimize API usage monthly\\n"
        content += "5. **Budget Limits**: Set strict budget limits for each service\\n\\n"

        content += "## Action Items\\n\\n""
        content += "- [ ] Set up environment variables for all APIs\\n"
        content += "- [ ] Configure billing alerts for paid services\\n"
        content += "- [ ] Test all free tier APIs\\n"
        content += "- [ ] Document API integration patterns\\n"
        content += "- [ ] Set up monitoring for API health and costs\\n"

        return content


    def _get_status_badge(self, status: str) -> str:
        """Get status badge for markdown."""
        badges = {
            "free": "🟢 Free",
                "freemium": "🟡 Freemium",
                "paid": "🔴 Paid",
                "disabled": "⚫ Disabled",
# BRACKET_SURGEON: disabled
#                 }
        return badges.get(status, status)


    def add_channel_and_discover(
        self, channel_name: str, budget_limit: float = 25.0
    ) -> Dict[str, Any]:
        """Add a new channel and automatically discover APIs for it."""
        try:
            # Add channel to auto - discovery service
            success = self.auto_discovery.add_channel(channel_name)

            if success:
                # Run discovery and integration
                result = self.discover_and_integrate_apis(channel_name)
                return result
            else:
                return {"success": False, "error": "Failed to add channel"}

        except Exception as e:
            self.logger.error(f"Error in add_channel_and_discover: {e}")
            return {"success": False, "error": str(e)}


    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics."""
        try:
            apis = self._get_all_apis()

            stats = {
                "total_apis": len(apis),
                    "by_status": {},
                    "by_category": {},
                    "total_monthly_cost": sum(api.cost_monthly for api in apis),
                    "auto_discovered_count": len(
                    [api for api in apis if api.auto_discovered]
# BRACKET_SURGEON: disabled
#                 ),
                    "average_quality_score": (
                    sum(api.quality_score for api in apis) / len(apis) if apis else 0
# BRACKET_SURGEON: disabled
#                 ),
                    "last_updated": (
                    max(api.last_updated for api in apis).isoformat() if apis else None
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#                     }

            # Count by status
            for api in apis:
                stats["by_status"][api.status] = (
                    stats["by_status"].get(api.status, 0) + 1
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Count by category
            for api in apis:
                stats["by_category"][api.category] = (
                    stats["by_category"].get(api.category, 0) + 1
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            return stats

        except Exception as e:
            self.logger.error(f"Error getting integration stats: {e}")
            return {}

# CLI interface
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(description="API Integration Service CLI")
    parser.add_argument(
        "--action",
            choices=["discover", "add - channel", "update - table", "stats"],
            required = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument("--channel", help="Channel name")
    parser.add_argument("--budget", type = float, default = 25.0, help="Budget limit")

    args = parser.parse_args()

    service = APIIntegrationService()

    if args.action == "discover" and args.channel:
        result = service.discover_and_integrate_apis(args.channel)
        print(json.dumps(result, indent = 2, default = str))

    elif args.action == "add - channel" and args.channel:
        result = service.add_channel_and_discover(args.channel, args.budget)
        print(json.dumps(result, indent = 2, default = str))

    elif args.action == "update - table":
        service._update_management_table_file()
        print("API management table updated")

    elif args.action == "stats":
        stats = service.get_integration_stats()
        print(json.dumps(stats, indent = 2, default = str))

    else:
        parser.print_help()