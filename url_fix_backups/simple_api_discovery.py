#!/usr / bin / env python3
"""
Simple API Discovery Script

Standalone script to discover and integrate free APIs without complex dependencies.
"""

import json
import sqlite3
import requests
import time
from datetime import datetime
from typing import Dict, List, Any


class SimpleAPIDiscovery:
    """Simple API discovery without complex dependencies"""

    def __init__(self, db_path: str = "databases / master.db"):
        self.db_path = db_path
        self.discovered_apis = []

    def discover_free_apis(self) -> List[Dict[str, Any]]:
        """Discover free APIs from PublicAPIs.org"""
        print("🔍 Discovering free APIs from PublicAPIs.org...")

        try:
            # Get APIs from PublicAPIs.org
            response = requests.get("https://api.publicapis.org / entries", timeout=30)
            if response.status_code == 200:
                data = response.json()
                all_apis = data.get("entries", [])

                # Filter for free APIs only
                free_apis = [
                    api
                    for api in all_apis
                    if api.get("Auth", "").lower() in ["", "no", "none"]
                    or "free" in api.get("Description", "").lower()
                ]

                print(f"✅ Found {len(free_apis)} free APIs out of {len(all_apis)} total")
                return free_apis[:50]  # Limit to first 50 for processing

        except Exception as e:
            print(f"❌ Error discovering APIs: {e}")
            return []

    def categorize_apis(self, apis: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize APIs by their category"""
        categorized = {}

        for api in apis:
            category = api.get("Category", "Other")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(api)

        return categorized

    def save_to_database(self, apis: List[Dict[str, Any]]) -> int:
        """Save discovered APIs to database"""
        print("💾 Saving APIs to database...")

        try:
            with sqlite3.connect(self.db_path) as conn:
                saved_count = 0

                for api in apis:
                    # Insert into api_suggestions table
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO api_suggestions (
                            api_name, provider, category, description, signup_url,
                            documentation_url, pricing_model, free_tier_limits,
                            integration_complexity, estimated_setup_time, quality_score,
                            use_cases, required_credentials, rate_limits, status,
                            discovery_source, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            api.get("API", "Unknown"),
                            "PublicAPIs.org",
                            api.get("Category", "Other"),
                            api.get("Description", ""),
                            api.get("Link", ""),
                            api.get("Link", ""),
                            "free",
                            "Varies by API",
                            "low"
                            if api.get("Auth", "").lower() in ["", "no", "none"]
                            else "medium",
                            "15 minutes",
                            8.5,  # Default quality score
                            json.dumps(
                                [
                                    api.get("Category", "Other"),
                                    "automation",
                                    "integration",
                                ]
                            ),
                            json.dumps([api.get("Auth", "none")])
                            if api.get("Auth")
                            else json.dumps([]),
                            "Standard",
                            "discovered",
                            "simple_api_discovery",
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

                    # Insert into api_discovery_tasks table
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO api_discovery_tasks (
                            task_name, task_type, target_capability, search_parameters,
                            capability_gap, search_keywords, priority, status,
                            assigned_agent, progress_notes, apis_found, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            f"Discovered: {api.get('API', 'Unknown')}",
                            "api_integration",
                            api.get("Category", "Other"),
                            json.dumps(
                                {
                                    "link": api.get("Link", ""),
                                    "auth": api.get("Auth", "none"),
                                    "https": api.get("HTTPS", False),
                                }
                            ),
                            "Free API integration",
                            json.dumps(
                                [
                                    api.get("API", "Unknown"),
                                    api.get("Category", "Other"),
                                ]
                            ),
                            5,  # Medium priority
                            "completed",
                            "simple_api_discovery",
                            f"Successfully discovered free API: {api.get('API', 'Unknown')}",
                            1,
                            datetime.now().isoformat(),
                            datetime.now().isoformat(),
                        ),
                    )

                    saved_count += 1

                conn.commit()
                print(f"✅ Saved {saved_count} APIs to database")
                return saved_count

        except Exception as e:
            print(f"❌ Error saving to database: {e}")
            return 0

    def update_system_config(self, total_apis: int):
        """Update system configuration with discovery results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update last discovery time
                conn.execute(
                    """
                    INSERT OR REPLACE INTO system_config (key,
    value,
    description,
    updated_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "last_api_discovery",
                        datetime.now().isoformat(),
                        "Last successful API discovery run",
                        datetime.now().isoformat(),
                    ),
                )

                # Update total discovered APIs count
                conn.execute(
                    """
                    INSERT OR REPLACE INTO system_config (key,
    value,
    description,
    updated_at)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "total_discovered_apis",
                        str(total_apis),
                        "Total number of discovered APIs",
                        datetime.now().isoformat(),
                    ),
                )

                conn.commit()

        except Exception as e:
            print(f"❌ Error updating system config: {e}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate discovery report"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                # Get API statistics by category
                cursor = conn.execute(
                    """
                    SELECT
                        category,
                        COUNT(*) as count,
                        AVG(quality_score) as avg_score
                    FROM api_suggestions
                    WHERE status = 'discovered'
                    GROUP BY category
                    ORDER BY count DESC
                """
                )

                category_stats = [dict(row) for row in cursor.fetchall()]

                # Get total count
                cursor = conn.execute(
                    """
                    SELECT COUNT(*) as total_count
                    FROM api_suggestions
                    WHERE status = 'discovered'
                """
                )

                total_count = cursor.fetchone()[0]

                # Get recent discoveries
                cursor = conn.execute(
                    """
                    SELECT api_name, category, quality_score, created_at
                    FROM api_suggestions
                    WHERE status = 'discovered'
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                )

                recent_discoveries = [dict(row) for row in cursor.fetchall()]

                return {
                    "total_apis": total_count,
                    "by_category": category_stats,
                    "recent_discoveries": recent_discoveries,
                }

        except Exception as e:
            print(f"❌ Error generating report: {e}")
            return {"error": str(e)}

    def run_discovery(self) -> Dict[str, Any]:
        """Run complete discovery process"""
        start_time = time.time()

        print("🚀 Starting Simple API Discovery")
        print("=" * 40)

        # Step 1: Discover APIs
        apis = self.discover_free_apis()
        if not apis:
            return {"success": False, "error": "No APIs discovered"}

        # Step 2: Categorize APIs
        print("📊 Categorizing APIs...")
        categorized = self.categorize_apis(apis)

        for category, api_list in categorized.items():
            print(f"   • {category}: {len(api_list)} APIs")

        # Step 3: Save to database
        saved_count = self.save_to_database(apis)

        # Step 4: Update system config
        self.update_system_config(saved_count)

        # Step 5: Generate report
        print("📈 Generating report...")
        report = self.generate_report()

        end_time = time.time()

        results = {
            "success": True,
            "execution_time": end_time - start_time,
            "apis_discovered": len(apis),
            "apis_saved": saved_count,
            "categories": list(categorized.keys()),
            "report": report,
            "timestamp": datetime.now().isoformat(),
        }

        # Print summary
        print("\\n" + "=" * 40)
        print("✅ API DISCOVERY COMPLETED")
        print("=" * 40)
        print(f"⏱️  Execution time: {results['execution_time']:.2f} seconds")
        print(f"🔍 APIs discovered: {results['apis_discovered']}")
        print(f"💾 APIs saved: {results['apis_saved']}")
        print(f"📂 Categories: {len(results['categories'])}")
        print(f"📊 Total in database: {report.get('total_apis', 0)}")
        print("=" * 40)

        return results


def main():
    """Main entry point"""
    discovery = SimpleAPIDiscovery()
    results = discovery.run_discovery()

    # Save results to file
    results_file = (
        f"simple_api_discovery_results_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
    )
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\\n💾 Results saved to: {results_file}")

    return results["success"]


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
