#!/usr / bin / env python3
"""
API Manager - Central CLI for API Discovery and Management

This script provides a unified interface for managing APIs, discovering new ones,
and maintaining the API management table.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:

    from backend.services.api_integration_service import APIIntegrationService
    from backend.services.auto_discovery_service import AutoDiscoveryService
    from backend.services.cost_tracking_service import CostTrackingService
    from backend.services.web_search_service import WebSearchService

except ImportError as e:
    print(f"Error importing services: {e}")
    print("Make sure all service files are in backend / services/")
    sys.exit(1)


class APIManager:
    """Central API management system."""


    def __init__(self):
        self.logger = self._setup_logging()
        self.integration_service = APIIntegrationService()
        self.auto_discovery = AutoDiscoveryService()
        self.web_search = WebSearchService()
        self.cost_tracking = CostTrackingService()

        # Marketing channels we support
        self.supported_channels = [
            "youtube",
                "tiktok",
                "instagram",
                "twitter",
                "linkedin",
                "pinterest",
                "email",
                "sms",
                "whatsapp",
                "telegram",
                "discord",
                "ai_content",
                "analytics",
                "payment",
                "storage",
                "auth",
                ]


    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logging.basicConfig(
            level = logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                logging.FileHandler("api_manager.log"),
                    logging.StreamHandler(sys.stdout),
                    ],
                )
        return logging.getLogger(__name__)


    def discover_channel_apis(
        self, channel: str, budget_limit: float = 25.0
    ) -> Dict[str, Any]:
        """Discover and integrate APIs for a specific channel."""
        try:
            if channel not in self.supported_channels:
                return {
                    "success": False,
                        "error": f'Unsupported channel: {channel}. Supported: {", ".join(self.supported_channels)}',
                        }

            self.logger.info(f"🔍 Discovering APIs for channel: {channel}")

            # Run discovery and integration
            result = self.integration_service.add_channel_and_discover(
                channel, budget_limit
            )

            if result.get("success"):
                self.logger.info(
                    f"✅ Successfully discovered {result.get('apis_integrated',
    0)} APIs for {channel}"
                )

                # Update the management table
                self.integration_service._update_management_table_file()

                # Print summary
                self._print_discovery_summary(result)
            else:
                self.logger.error(
                    f"❌ Discovery failed for {channel}: {result.get('error')}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error discovering APIs for {channel}: {e}")
            return {"success": False, "error": str(e)}


    def discover_all_channels(self, budget_limit: float = 25.0) -> Dict[str, Any]:
        """Discover APIs for all supported channels."""
        try:
            self.logger.info("🚀 Starting comprehensive API discovery for all channels")

            results = {}
            total_apis = 0
            total_cost = 0.0

            for channel in self.supported_channels:
                self.logger.info(f"\\n📡 Processing channel: {channel.upper()}")

                result = self.discover_channel_apis(channel, budget_limit)
                results[channel] = result

                if result.get("success"):
                    total_apis += result.get("apis_integrated", 0)
                    if "cost_analysis" in result:
                        total_cost += result["cost_analysis"].get(
                            "total_monthly_cost", 0
                        )

                # Small delay between channels

                import time

                time.sleep(1)

            # Generate final summary
            summary = {
                "success": True,
                    "channels_processed": len(self.supported_channels),
                    "total_apis_discovered": total_apis,
                    "estimated_monthly_cost": total_cost,
                    "results_by_channel": results,
                    "timestamp": datetime.now().isoformat(),
                    }

            self.logger.info(
                f"\\n🎉 Discovery complete! Found {total_apis} APIs across {len(self.supported_channels)} channels"
            )
            self.logger.info(f"💰 Estimated monthly cost: ${total_cost:.2f}")

            return summary

        except Exception as e:
            self.logger.error(f"Error in comprehensive discovery: {e}")
            return {"success": False, "error": str(e)}


    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the API management system."""
        try:
            stats = self.integration_service.get_integration_stats()

            # Add additional stats
            stats["supported_channels"] = self.supported_channels
            stats["channels_count"] = len(self.supported_channels)

            return stats

        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}


    def search_apis(self, query: str, channel: str = None) -> Dict[str, Any]:
        """Search for APIs using the web search service."""
        try:
            self.logger.info(f"🔎 Searching for APIs: {query}")

            if channel:
                # Channel - specific search
                results = self.web_search.search_apis_by_channel(channel)
            else:
                # General search - use trending discovery
                results = self.web_search.discover_trending_apis()

            return {
                "success": True,
                    "query": query,
                    "channel": channel,
                    "results": results,
                    "timestamp": datetime.now().isoformat(),
                    }

        except Exception as e:
            self.logger.error(f"Error searching APIs: {e}")
            return {"success": False, "error": str(e)}


    def update_table(self) -> bool:
        """Update the API management table file."""
        try:
            self.logger.info("📝 Updating API management table")
            self.integration_service._update_management_table_file()
            self.logger.info("✅ API management table updated successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error updating table: {e}")
            return False


    def track_costs(self) -> Dict[str, Any]:
        """Get cost tracking information."""
        try:
            # This would integrate with the cost tracking service
            stats = self.get_stats()

            cost_info = {
                "total_monthly_cost": stats.get("total_monthly_cost", 0),
                    "free_apis": stats.get("by_status", {}).get("free", 0),
                    "freemium_apis": stats.get("by_status", {}).get("freemium", 0),
                    "paid_apis": stats.get("by_status", {}).get("paid", 0),
                    "budget_status": (
                    "within_budget"
                    if stats.get("total_monthly_cost", 0) <= 25.0
                    else "over_budget"
                ),
                    "recommendations": self._get_cost_recommendations(stats),
                    }

            return cost_info

        except Exception as e:
            self.logger.error(f"Error tracking costs: {e}")
            return {"error": str(e)}


    def _get_cost_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get cost optimization recommendations."""
        recommendations = []

        total_cost = stats.get("total_monthly_cost", 0)
        paid_apis = stats.get("by_status", {}).get("paid", 0)

        if total_cost > 25.0:
            recommendations.append("⚠️ Monthly cost exceeds $25 budget limit")
            recommendations.append(
                "💡 Consider switching to free / freemium alternatives"
            )

        if paid_apis > 0:
            recommendations.append(
                f"💰 You have {paid_apis} paid APIs - review if all are necessary"
            )

        if total_cost == 0:
            recommendations.append("🎉 All APIs are free! Great cost optimization")

        recommendations.append(
            "📊 Regularly monitor API usage to avoid unexpected charges"
        )
        recommendations.append("🔄 Review and optimize API usage monthly")

        return recommendations


    def _print_discovery_summary(self, result: Dict[str, Any]):
        """Print a formatted summary of discovery results."""
        if not result.get("success"):
            return

        print(f"\\n📊 Discovery Summary for {result.get('channel', 'Unknown').upper()}:")
        print(f"   • APIs Discovered: {result.get('apis_discovered', 0)}")
        print(f"   • APIs Integrated: {result.get('apis_integrated', 0)}")

        if "cost_analysis" in result:
            cost = result["cost_analysis"].get("total_monthly_cost", 0)
            print(f"   • Estimated Cost: ${cost:.2f}/month")

        if "integrated_apis" in result:
            print("   • Top APIs Found:")
            for api in result["integrated_apis"][:3]:  # Show top 3
                status_emoji = {"free": "🟢", "freemium": "🟡", "paid": "🔴"}.get(
                    api["status"], "⚪"
                )
                print(
                    f"     {status_emoji} {api['name']} ({api['provider']}) - Score: {api['quality_score']:.2f}"
                )


    def interactive_mode(self):
        """Run in interactive mode for easy API management."""
        print("\\n🚀 API Manager - Interactive Mode")
        print("==================================\\n")

        while True:
            print("\\nAvailable commands:")
            print("1. discover <channel> - Discover APIs for a specific channel")
            print("2. discover - all - Discover APIs for all channels")
            print("3. search <query> - Search for APIs")
            print("4. stats - Show system statistics")
            print("5. costs - Show cost tracking information")
            print("6. update - Update API management table")
            print("7. channels - List supported channels")
            print("8. quit - Exit interactive mode")

            try:
                command = input("\\n> ").strip().lower()

                if command == "quit" or command == "exit":
                    print("👋 Goodbye!")
                    break

                elif command.startswith("discover "):
                    channel = command.split(" ", 1)[1]
                    result = self.discover_channel_apis(channel)
                    if not result.get("success"):
                        print(f"❌ Error: {result.get('error')}")

                elif command == "discover - all":
                    print("🚀 Starting comprehensive discovery...")
                    result = self.discover_all_channels()
                    if result.get("success"):
                        print(
                            f"✅ Discovery complete! Check api_management_table.md for results"
                        )
                    else:
                        print(f"❌ Error: {result.get('error')}")

                elif command.startswith("search "):
                    query = command.split(" ", 1)[1]
                    result = self.search_apis(query)
                    if result.get("success"):
                        print(
                            f"🔍 Search results for '{query}': {len(result.get('results', []))} found"
                        )
                    else:
                        print(f"❌ Error: {result.get('error')}")

                elif command == "stats":
                    stats = self.get_stats()
                    if "error" not in stats:
                        print(f"\\n📊 System Statistics:")
                        print(f"   • Total APIs: {stats.get('total_apis', 0)}")
                        print(
                            f"   • Free APIs: {stats.get('by_status', {}).get('free',
    0)}"
                        )
                        print(
                            f"   • Freemium APIs: {stats.get('by_status', {}).get('freemium',
    0)}"
                        )
                        print(
                            f"   • Paid APIs: {stats.get('by_status', {}).get('paid',
    0)}"
                        )
                        print(
                            f"   • Monthly Cost: ${stats.get('total_monthly_cost',
    0):.2f}"
                        )
                        print(
                            f"   • Auto - discovered: {stats.get('auto_discovered_count',
    0)}"
                        )
                    else:
                        print(f"❌ Error: {stats.get('error')}")

                elif command == "costs":
                    costs = self.track_costs()
                    if "error" not in costs:
                        print(f"\\n💰 Cost Analysis:")
                        print(
                            f"   • Monthly Cost: ${costs.get('total_monthly_cost',
    0):.2f}"
                        )
                        print(
                            f"   • Budget Status: {costs.get('budget_status', 'unknown').replace('_', ' ').title()}"
                        )
                        print(f"   • Free APIs: {costs.get('free_apis', 0)}")
                        print(f"   • Freemium APIs: {costs.get('freemium_apis', 0)}")
                        print(f"   • Paid APIs: {costs.get('paid_apis', 0)}")

                        recommendations = costs.get("recommendations", [])
                        if recommendations:
                            print("\\n   Recommendations:")
                            for rec in recommendations:
                                print(f"     {rec}")
                    else:
                        print(f"❌ Error: {costs.get('error')}")

                elif command == "update":
                    if self.update_table():
                        print("✅ API management table updated")
                    else:
                        print("❌ Failed to update table")

                elif command == "channels":
                    print(f"\\n📡 Supported Channels ({len(self.supported_channels)}):")
                    for i, channel in enumerate(self.supported_channels, 1):
                        print(f"   {i:2d}. {channel}")

                else:
                    print("❓ Unknown command. Type a number or command name.")

            except KeyboardInterrupt:
                print("\\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="API Manager - Discover and manage APIs for marketing channels",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python api_manager.py discover youtube
  python api_manager.py discover - all
  python api_manager.py search "email marketing APIs"
  python api_manager.py stats
  python api_manager.py interactive
        """,
            )

    parser.add_argument(
        "command",
            nargs="?",
            choices=[
            "discover",
                "discover - all",
                "search",
                "stats",
                "costs",
                "update",
                "channels",
                "interactive",
                ],
            help="Command to execute",
            )

    parser.add_argument(
        "target",
            nargs="?",
            help="Target for the command (e.g., channel name, search query)",
            )
    parser.add_argument(
        "--budget",
            type = float,
            default = 25.0,
            help="Budget limit for API costs (default: $25)",
            )
    parser.add_argument(
        "--output", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    manager = APIManager()

    try:
        if not args.command or args.command == "interactive":
            manager.interactive_mode()
            return

        result = None

        if args.command == "discover":
            if not args.target:
                print("❌ Error: Channel name required for discover command")
                print(f"Supported channels: {", ".join(manager.supported_channels)}")
                return
            result = manager.discover_channel_apis(args.target, args.budget)

        elif args.command == "discover - all":
            result = manager.discover_all_channels(args.budget)

        elif args.command == "search":
            if not args.target:
                print("❌ Error: Search query required")
                return
            result = manager.search_apis(args.target)

        elif args.command == "stats":
            result = manager.get_stats()

        elif args.command == "costs":
            result = manager.track_costs()

        elif args.command == "update":
            success = manager.update_table()
            result = {"success": success}

        elif args.command == "channels":
            result = {
                "supported_channels": manager.supported_channels,
                    "count": len(manager.supported_channels),
                    }

        # Output result
        if result:
            if args.output == "json":
                print(json.dumps(result, indent = 2, default = str))
            else:
                if result.get("success", True):
                    print("✅ Command completed successfully")
                    if args.command == "channels":
                        print(f"\\n📡 Supported Channels ({result['count']}):")
                        for i, channel in enumerate(result["supported_channels"], 1):
                            print(f"   {i:2d}. {channel}")
                else:
                    print(f"❌ Error: {result.get('error', 'Unknown error')}")

    except KeyboardInterrupt:
        print("\\n👋 Operation cancelled")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:

            import traceback

            traceback.print_exc()

if __name__ == "__main__":
    main()