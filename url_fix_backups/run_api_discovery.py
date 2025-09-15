#!/usr / bin / env python3
""""""
API Discovery Integration Runner

Comprehensive script that:
- Runs the full API discovery engine
- Integrates with the database
- Updates the API management table
- Provides detailed reporting
- Manages free API detection and integration
""""""

import asyncio
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(
    level = logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )
logger = logging.getLogger(__name__)

# Import our API discovery components
try:

    from backend.agents.api_discovery_engine import APIDiscoveryEngine, APIDiscoveryConfig, APICategory
    from backend.services.api_discovery_service import APIDiscoveryService
    from backend.services.api_integration_service import APIIntegrationService

except ImportError as e:
    logger.error(f"Failed to import API discovery components: {e}")
    sys.exit(1)

class APIDiscoveryRunner:
    """Main runner for API discovery integration"""

    def __init__(self, db_path: str = "databases / master.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)

        # Initialize components
        self.discovery_engine = None
        self.discovery_service = None
        self.integration_service = None

        # Results storage
        self.discovery_results = {}
        self.integration_results = {}

    async def initialize(self):
        """Initialize all discovery components"""
        try:
            # Configure discovery engine for free APIs only
            config = APIDiscoveryConfig(
                max_apis_per_source = 100,
                validate_endpoints = True,
                generate_integration_code = True,
                free_only = True,  # Focus on free APIs
                min_validation_score = 0.6,
                categories_filter=[
                    APICategory.SOCIAL_MEDIA,
                    APICategory.NEWS,
                    APICategory.FINANCE,
                    APICategory.WEATHER,
                    APICategory.ENTERTAINMENT,
                    APICategory.PRODUCTIVITY,
                    APICategory.DEVELOPER_TOOLS,
                    APICategory.DATA_SCIENCE,
                    APICategory.BUSINESS,
                    APICategory.UTILITIES
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Initialize discovery engine
            self.discovery_engine = APIDiscoveryEngine(config)

            # Initialize discovery service
            self.discovery_service = APIDiscoveryService(self.db_path)

            # Initialize integration service
            self.integration_service = APIIntegrationService(self.db_path)

            self.logger.info("✅ All API discovery components initialized")
            return True

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize components: {e}")
            return False

    async def run_full_discovery(self) -> Dict[str, Any]:
        """Run complete API discovery process"""
        start_time = time.time()

        try:
            self.logger.info("🔍 Starting comprehensive API discovery...")

            # Step 1: Run discovery engine
            self.logger.info("📡 Running API discovery engine...")
            engine_results = await self.discovery_engine.run_full_discovery()

            # Step 2: Run channel - specific discovery
            self.logger.info("🎯 Running channel - specific discovery...")
            channel_results = await self._discover_by_channels()

            # Step 3: Integrate discovered APIs
            self.logger.info("🔗 Integrating discovered APIs...")
            integration_results = await self._integrate_apis()

            # Step 4: Update database
            self.logger.info("💾 Updating database...")
            await self._update_database()

            # Step 5: Generate reports
            self.logger.info("📊 Generating reports...")
            reports = await self._generate_reports()

            end_time = time.time()

            final_results = {
                "success": True,
                "execution_time": end_time - start_time,
                "engine_results": engine_results,
                "channel_results": channel_results,
                "integration_results": integration_results,
                "reports": reports,
                "timestamp": datetime.now().isoformat()
# BRACKET_SURGEON: disabled
#             }

            self.logger.info(f"✅ API discovery completed in {end_time - start_time:.2f} seconds")
            return final_results

        except Exception as e:
            self.logger.error(f"❌ API discovery failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
# BRACKET_SURGEON: disabled
#             }

    async def _discover_by_channels(self) -> Dict[str, Any]:
        """Discover APIs for specific marketing channels"""
        channels = [
            "youtube", "tiktok", "instagram", "twitter",
            "affiliate", "email", "analytics", "content"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        channel_results = {}

        async with self.discovery_service:
            for channel in channels:
                try:
                    self.logger.info(f"🔍 Discovering APIs for {channel}...")
                    candidates = await self.discovery_service.discover_apis_for_channel(channel)

                    # Filter for free APIs only
                    free_candidates = [
                        api for api in candidates
                        if api.cost_model in ['free', 'freemium']
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]

                    channel_results[channel] = {
                        "total_found": len(candidates),
                        "free_apis": len(free_candidates),
                        "candidates": free_candidates
# BRACKET_SURGEON: disabled
#                     }

                    self.logger.info(
                        f"✅ {channel}: {len(free_candidates)} free APIs found "
                        f"(out of {len(candidates)} total)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                except Exception as e:
                    self.logger.error(f"❌ Failed to discover APIs for {channel}: {e}")
                    channel_results[channel] = {
                        "error": str(e),
                        "total_found": 0,
                        "free_apis": 0,
                        "candidates": []
# BRACKET_SURGEON: disabled
#                     }

        return channel_results

    async def _integrate_apis(self) -> Dict[str, Any]:
        """Integrate discovered APIs into the system"""
        integration_results = {
            "total_integrated": 0,
            "by_channel": {},
            "errors": []
# BRACKET_SURGEON: disabled
#         }

        try:
            # Get all discovered APIs from the engine
            discovered_apis = self.discovery_engine.get_free_apis()

            for api in discovered_apis:
                try:
                    # Save to database
                    await self._save_api_to_database(api)
                    integration_results["total_integrated"] += 1

                    # Track by category
                    category = api.category.value
                    if category not in integration_results["by_channel"]:
                        integration_results["by_channel"][category] = 0
                    integration_results["by_channel"][category] += 1

                except Exception as e:
                    error_msg = f"Failed to integrate {api.name}: {e}"
                    self.logger.error(error_msg)
                    integration_results["errors"].append(error_msg)

            return integration_results

        except Exception as e:
            self.logger.error(f"Integration process failed: {e}")
            integration_results["errors"].append(str(e))
            return integration_results

    async def _save_api_to_database(self, api):
        """Save API to the master database"""
        with sqlite3.connect(self.db_path) as conn:
            # Insert into api_discovery_tasks table
            conn.execute(""""""
                INSERT OR REPLACE INTO api_discovery_tasks (
                    task_name, task_type, target_capability, search_parameters,
                    capability_gap, search_keywords, priority, status,
                    assigned_agent, progress_notes, apis_found, created_at, updated_at
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("""
                f"Discovered: {api.name}",
                "api_integration",
                api.category.value,
                json.dumps({
                    "base_url": api.base_url,
                    "auth_type": api.auth_type.value,
                    "is_free": api.is_free
# BRACKET_SURGEON: disabled
#                 }),
                "Free API integration",
                json.dumps([api.name, api.category.value]),
                5,  # Medium priority
                "completed",
                "api_discovery_runner",
                f"Successfully integrated free API: {api.name}",
                1,
                datetime.now().isoformat(),
                datetime.now().isoformat()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ))

            # Insert into api_suggestions table
            conn.execute(""""""
                INSERT OR REPLACE INTO api_suggestions (
                    api_name, provider, category, description, signup_url,
                    documentation_url, pricing_model, free_tier_limits,
                    integration_complexity, estimated_setup_time, quality_score,
                    use_cases, required_credentials, rate_limits, status,
                    discovery_source, created_at, updated_at
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, ("""
                api.name,
                "Auto - discovered",
                api.category.value,
                api.description,
                api.base_url,
                api.documentation_url or api.base_url,
                "free" if api.is_free else "unknown",
                api.rate_limit or "Unknown",
                "low",  # Assume low complexity for free APIs
                "15 minutes",
                api.validation_score,
                json.dumps([api.category.value, "automation", "integration"]),
                json.dumps([api.auth_type.value]) if api.auth_type.value != "none" else json.dumps([]),
                api.rate_limit or "Standard",
                "discovered",
                "api_discovery_engine",
                datetime.now().isoformat(),
                datetime.now().isoformat()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ))

            conn.commit()

    async def _update_database(self):
        """Update database with discovery results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update system_config with discovery status
                conn.execute(""""""
                    INSERT OR REPLACE INTO system_config (key,
    value,
    description,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     updated_at)
                    VALUES (?, ?, ?, ?)
                """, ("""
                    "last_api_discovery",
                    datetime.now().isoformat(),
                    "Last successful API discovery run",
                    datetime.now().isoformat()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ))

                # Count total discovered APIs
                cursor = conn.execute("SELECT COUNT(*) FROM api_suggestions WHERE status = 'discovered'")
                total_apis = cursor.fetchone()[0]

                conn.execute(""""""
                    INSERT OR REPLACE INTO system_config (key,
    value,
    description,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     updated_at)
                    VALUES (?, ?, ?, ?)
                """, ("""
                    "total_discovered_apis",
                    str(total_apis),
                    "Total number of discovered APIs",
                    datetime.now().isoformat()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ))

                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to update database: {e}")

    async def _generate_reports(self) -> Dict[str, Any]:
        """Generate comprehensive discovery reports"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get API statistics
                cursor = conn.execute(""""""
                    SELECT
                        category,
                        COUNT(*) as count,
                        AVG(quality_score) as avg_score
                    FROM api_suggestions
                    WHERE status = 'discovered'
                    GROUP BY category
                    ORDER BY count DESC
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 """)"""

                category_stats = [dict(row) for row in cursor.fetchall()]

                # Get free APIs count
                cursor = conn.execute(""""""
                    SELECT COUNT(*) as free_count
                    FROM api_suggestions
                    WHERE pricing_model = 'free' AND status = 'discovered'
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 """)"""

                free_count = cursor.fetchone()[0]

                # Get total APIs count
                cursor = conn.execute(""""""
                    SELECT COUNT(*) as total_count
                    FROM api_suggestions
                    WHERE status = 'discovered'
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 """)"""

                total_count = cursor.fetchone()[0]

                # Get recent discoveries
                cursor = conn.execute(""""""
                    SELECT api_name, category, quality_score, created_at
                    FROM api_suggestions
                    WHERE status = 'discovered'
                    ORDER BY created_at DESC
                    LIMIT 10
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 """)"""

                recent_discoveries = [dict(row) for row in cursor.fetchall()]

                return {
                    "summary": {
                        "total_apis": total_count,
                        "free_apis": free_count,
                        "free_percentage": (free_count / total_count * 100) if total_count > 0 else 0
# BRACKET_SURGEON: disabled
#                     },
                    "by_category": category_stats,
                    "recent_discoveries": recent_discoveries
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            self.logger.error(f"Failed to generate reports: {e}")
            return {"error": str(e)}

    def print_results(self, results: Dict[str, Any]):
        """Print formatted discovery results"""
        if not results.get("success"):
            print(f"❌ Discovery failed: {results.get('error')}")
            return

        print("\\n" + "="*60)
        print("🔍 API DISCOVERY RESULTS")
        print("="*60)

        # Execution summary
        print(f"⏱️  Execution time: {results['execution_time']:.2f} seconds")
        print(f"📅 Completed at: {results['timestamp']}")

        # Engine results
        if "engine_results" in results:
            engine = results["engine_results"]
            print(f"\\n📡 DISCOVERY ENGINE:")
            print(f"   • Total discovered: {engine.get('total_discovered', 0)}")
            print(f"   • Unique APIs: {engine.get('unique_apis', 0)}")
            print(f"   • Validated APIs: {engine.get('validated_apis', 0)}")

        # Channel results
        if "channel_results" in results:
            print(f"\\n🎯 CHANNEL DISCOVERY:")
            for channel, data in results["channel_results"].items():
                if "error" not in data:
                    print(f"   • {channel.capitalize()}: {data['free_apis']} free APIs")
                else:
                    print(f"   • {channel.capitalize()}: Error - {data['error']}")

        # Integration results
        if "integration_results" in results:
            integration = results["integration_results"]
            print(f"\\n🔗 INTEGRATION:")
            print(f"   • Total integrated: {integration.get('total_integrated', 0)}")
            if integration.get("errors"):
                print(f"   • Errors: {len(integration['errors'])}")

        # Reports
        if "reports" in results and "summary" in results["reports"]:
            summary = results["reports"]["summary"]
            print(f"\\n📊 SUMMARY:")
            print(f"   • Total APIs in database: {summary.get('total_apis', 0)}")
            print(f"   • Free APIs: {summary.get('free_apis',"
    0)} ({summary.get('free_percentage',
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     0):.1f}%)")

        print("\\n✅ API discovery completed successfully!")
        print("="*60)

async def main():
    """Main entry point"""
    print("🚀 Starting API Discovery Integration")
    print("=====================================")

    runner = APIDiscoveryRunner()

    # Initialize components
    if not await runner.initialize():
        print("❌ Failed to initialize API discovery components")
        sys.exit(1)

    # Run discovery
    results = await runner.run_full_discovery()

    # Print results
    runner.print_results(results)

    # Save results to file
    results_file = f"api_discovery_results_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent = 2, default = str)

    print(f"\\n💾 Results saved to: {results_file}")

    return results["success"]

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)