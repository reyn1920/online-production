#!/usr/bin/env python3
""""""
API Master Dashboard
Unified interface for managing 100+ APIs

Features:
- Registration automation
- API testing and monitoring
- Environment management
- Cost tracking
- Health monitoring

Usage:
    python api_master_dashboard.py
""""""

import json
import os
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, Optional

# Import our custom modules
try:
    from api_registration_automation import API_REGISTRY, APIRegistrationManager
    from api_testing_suite import APITester, APITestResult
except ImportError:
    print(
        "⚠️  Required modules not found. Make sure api_registration_automation.py "
        "and api_testing_suite.py are in the same directory."
# BRACKET_SURGEON: disabled
#     )
    sys.exit(1)


@dataclass
class APIStatus:
    name: str
    registered: bool
    has_key: bool
    last_tested: Optional[str]
    test_status: Optional[str]
    response_time: Optional[float]
    cost_tier: str
    phase: int
    priority: str
    usage_count: int = 0
    last_error: Optional[str] = None


class APIMasterDashboard:
    def __init__(self):
        self.registration_manager = APIRegistrationManager()
        self.tester = APITester()
        self.status_file = "api_status_dashboard.json"
        self.usage_file = "api_usage_tracking.json"
        self.load_status()
        self.load_usage()

    def load_status(self):
        """Load API status from file"""
        try:
            with open(self.status_file, "r") as f:
                data = json.load(f)
                self.api_status = {k: APIStatus(**v) for k, v in data.items()}
        except FileNotFoundError:
            self.api_status = {}
            self.initialize_status()

    def save_status(self):
        """Save API status to file"""
        data = {k: asdict(v) for k, v in self.api_status.items()}
        with open(self.status_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_usage(self):
        """Load API usage tracking"""
        try:
            with open(self.usage_file, "r") as f:
                self.usage_data = json.load(f)
        except FileNotFoundError:
            self.usage_data = {
                "daily_usage": {},
                "monthly_costs": {},
                "rate_limits": {},
                "last_updated": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

    def save_usage(self):
        """Save API usage tracking"""
        self.usage_data["last_updated"] = datetime.now().isoformat()
        with open(self.usage_file, "w") as f:
            json.dump(self.usage_data, f, indent=2)

    def initialize_status(self):
        """Initialize API status from registry"""
        for api_key, api_info in API_REGISTRY.items():
            self.api_status[api_key] = APIStatus(
                name=api_info["name"],
                registered=self.registration_manager.is_registered(api_key),
                has_key=bool(os.getenv(api_info["env_var"])),
                last_tested=None,
                test_status=None,
                response_time=None,
                cost_tier=api_info["cost"],
                phase=api_info["phase"],
                priority=api_info["priority"],
# BRACKET_SURGEON: disabled
#             )
        self.save_status()

    def update_api_status(self, api_key: str, test_result: APITestResult):
        """Update API status with test results"""
        if api_key in self.api_status:
            status = self.api_status[api_key]
            status.last_tested = datetime.now().isoformat()
            status.test_status = test_result.status
            status.response_time = test_result.response_time
            if test_result.error_message:
                status.last_error = test_result.error_message
            self.save_status()

    def get_dashboard_stats(self) -> Dict:
        """Get comprehensive dashboard statistics"""
        total_apis = len(self.api_status)
        registered_count = sum(1 for status in self.api_status.values() if status.registered)
        has_key_count = sum(1 for status in self.api_status.values() if status.has_key)
        tested_count = sum(1 for status in self.api_status.values() if status.last_tested)
        working_count = sum(
            1 for status in self.api_status.values() if status.test_status == "success"
# BRACKET_SURGEON: disabled
#         )

        # Phase statistics
        phase_stats = {}
        for phase in [1, 2, 3, 4]:
            phase_apis = [s for s in self.api_status.values() if s.phase == phase]
            phase_stats[phase] = {
                "total": len(phase_apis),
                "registered": sum(1 for s in phase_apis if s.registered),
                "has_key": sum(1 for s in phase_apis if s.has_key),
                "working": sum(1 for s in phase_apis if s.test_status == "success"),
# BRACKET_SURGEON: disabled
#             }

        # Cost statistics
        cost_stats = {}
        for cost_tier in ["FREE", "FREEMIUM", "PAID"]:
            cost_apis = [s for s in self.api_status.values() if s.cost_tier == cost_tier]
            cost_stats[cost_tier] = {
                "total": len(cost_apis),
                "registered": sum(1 for s in cost_apis if s.registered),
                "working": sum(1 for s in cost_apis if s.test_status == "success"),
# BRACKET_SURGEON: disabled
#             }

        return {
            "total_apis": total_apis,
            "registered": registered_count,
            "has_keys": has_key_count,
            "tested": tested_count,
            "working": working_count,
            "registration_rate": (registered_count / total_apis * 100) if total_apis > 0 else 0,
            "success_rate": (working_count / tested_count * 100) if tested_count > 0 else 0,
            "phase_stats": phase_stats,
            "cost_stats": cost_stats,
# BRACKET_SURGEON: disabled
#         }

    def display_dashboard(self):
        """Display the main dashboard"""
        os.system("clear" if os.name == "posix" else "cls")

        stats = self.get_dashboard_stats()

        print("🚀 API Master Dashboard")
        print("=" * 60)
        print(f"📊 Total APIs: {stats['total_apis']}")
        print(f"✅ Registered: {stats['registered']} ({stats['registration_rate']:.1f}%)")
        print(f"🔑 Have Keys: {stats['has_keys']}")
        print(f"🧪 Tested: {stats['tested']}")
        print(f"🟢 Working: {stats['working']} ({stats['success_rate']:.1f}%)")
        print()

        # Phase breakdown
        print("📈 Phase Breakdown:")
        for phase, data in stats["phase_stats"].items():
            print(f"  Phase {phase}: {data['working']}/{data['total']} working")
        print()

        # Cost breakdown
        print("💰 Cost Breakdown:")
        for tier, data in stats["cost_stats"].items():
            print(f"  {tier}: {data['working']}/{data['total']} working")
        print()

        # Recent test results
        recent_tests = [
            (k, v) for k, v in self.api_status.items() if v.last_tested and v.test_status
# BRACKET_SURGEON: disabled
#         ]
        recent_tests.sort(key=lambda x: x[1].last_tested or "", reverse=True)

        if recent_tests:
            print("🕒 Recent Test Results:")
            for api_key, status in recent_tests[:5]:
                status_icon = "✅" if status.test_status == "success" else "❌"
                time_str = status.last_tested[:19] if status.last_tested else "Never"
                print(f"  {status_icon} {status.name} - {time_str}")
        print()

    def show_api_details(self, api_key: str):
        """Show detailed information for a specific API"""
        if api_key not in self.api_status:
            print(f"❌ API '{api_key}' not found")
            return

        status = self.api_status[api_key]
        api_info = API_REGISTRY.get(api_key, {})

        print(f"\n📋 API Details: {status.name}")
        print("=" * 40)
        print(f"Key: {api_key}")
        print(f"Phase: {status.phase}")
        print(f"Priority: {status.priority}")
        print(f"Cost Tier: {status.cost_tier}")
        print(f"Registered: {'✅' if status.registered else '❌'}")
        print(f"Has API Key: {'✅' if status.has_key else '❌'}")
        print(f"Last Tested: {status.last_tested or 'Never'}")
        print(f"Test Status: {status.test_status or 'Not tested'}")
        if status.response_time:
            print(f"Response Time: {status.response_time:.2f}s")
        if status.last_error:
            print(f"Last Error: {status.last_error}")
        print(f"Usage Count: {status.usage_count}")

        if api_info:
            print(f"\nRegistration URL: {api_info.get('url', 'N/A')}")
            print(f"Environment Variable: {api_info.get('env_var', 'N/A')}")
            if api_info.get("notes"):
                print(f"Notes: {api_info['notes']}")
        print()

    def register_api_interactive(self, api_key: str):
        """Interactive API registration"""
        if api_key not in API_REGISTRY:
            print(f"❌ API '{api_key}' not found in registry")
            return

        print(f"\n🔧 Registering API: {API_REGISTRY[api_key]['name']}")
        print(f"URL: {API_REGISTRY[api_key]['url']}")
        print("\nOpening registration page in browser...")

        try:
            webbrowser.open(API_REGISTRY[api_key]["url"])
            input("\nPress Enter after completing registration...")

            # Update registration status
            self.api_status[api_key].registered = True
            self.save_status()
            print("✅ Registration status updated")
        except Exception as e:
            print(f"❌ Error during registration: {e}")

    def test_api_interactive(self, api_key: str):
        """Interactive API testing"""
        if api_key not in self.api_status:
            print(f"❌ API '{api_key}' not found")
            return

        status = self.api_status[api_key]
        if not status.has_key:
            print(f"❌ No API key found for {status.name}")
            print(f"Set environment variable: {API_REGISTRY[api_key]['env_var']}")
            return

        print(f"\n🧪 Testing API: {status.name}")
        print("Running test...")

        try:
            result = self.tester.test_api(api_key)
            self.update_api_status(api_key, result)

            if result.status == "success":
                print(f"✅ Test successful! Response time: {result.response_time:.2f}s")
            else:
                print(f"❌ Test failed: {result.error_message}")
        except Exception as e:
            print(f"❌ Error during testing: {e}")

    def bulk_test_apis(self, phase: Optional[int] = None):
        """Test multiple APIs in bulk"""
        apis_to_test = [
            (k, v)
            for k, v in self.api_status.items()
            if v.has_key and (phase is None or v.phase == phase)
# BRACKET_SURGEON: disabled
#         ]

        if not apis_to_test:
            print("❌ No APIs available for testing")
            return

        print(f"\n🧪 Bulk testing {len(apis_to_test)} APIs...")
        print("=" * 40)

        results = {"success": 0, "failed": 0}

        for api_key, status in apis_to_test:
            print(f"Testing {status.name}...", end=" ")
            try:
                result = self.tester.test_api(api_key)
                self.update_api_status(api_key, result)

                if result.status == "success":
                    print(f"✅ ({result.response_time:.2f}s)")
                    results["success"] += 1
                else:
                    print(f"❌ {result.error_message}")
                    results["failed"] += 1
            except Exception as e:
                print(f"❌ Error: {e}")
                results["failed"] += 1

            time.sleep(0.5)  # Rate limiting

        print("\n📊 Bulk Test Results:")
        print(f"✅ Successful: {results['success']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"Success Rate: {results['success'] / len(apis_to_test) * 100:.1f}%")

    def generate_registration_plan(self):
        """Generate a prioritized registration plan"""
        unregistered = [(k, v) for k, v in self.api_status.items() if not v.registered]

        if not unregistered:
            print("✅ All APIs are registered!")
            return

        # Sort by phase, then priority
        priority_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        unregistered.sort(key=lambda x: (x[1].phase, priority_order.get(x[1].priority, 4)))

        print("\n📋 Registration Plan (Prioritized):")
        print("=" * 50)

        current_phase = None
        for api_key, status in unregistered:
            if current_phase != status.phase:
                current_phase = status.phase
                print(f"\n🎯 Phase {current_phase}:")

            priority_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(status.priority, "⚪")

            cost_icon = {"FREE": "🆓", "FREEMIUM": "💰", "PAID": "💳"}.get(status.cost_tier, "❓")

            print(f"  {priority_icon} {cost_icon} {status.name} ({api_key})")
            if API_REGISTRY.get(api_key, {}).get("notes"):
                print(f"    📝 {API_REGISTRY[api_key]['notes']}")

        print(f"\n📊 Total unregistered: {len(unregistered)}")

    def export_env_template(self):
        """Export environment variable template"""
        template_file = ".env.template"

        print(f"\n📄 Generating environment template: {template_file}")

        with open(template_file, "w") as f:
            f.write("# API Master Dashboard - Environment Variables Template\n")"
            f.write(f"# Generated on {datetime.now().isoformat()}\n\n")"

            # Group by phase
            for phase in [1, 2, 3, 4]:
                phase_apis = [(k, v) for k, v in self.api_status.items() if v.phase == phase]

                if phase_apis:
                    f.write(f"# Phase {phase} APIs\n")"
                    for api_key, status in sorted(phase_apis):
                        api_info = API_REGISTRY.get(api_key, {})
                        env_var = api_info.get("env_var", f"{api_key.upper()}_API_KEY")

                        f.write(f"# {status.name} ({status.cost_tier})\n")"
                        if status.has_key:
                            f.write(f"{env_var}=your_api_key_here\n")
                        else:
                            f.write(f"# {env_var}=your_api_key_here\n")"
                        f.write("\n")

            # Additional configuration
            f.write("# Usage Tracking (Optional)\n")"
            f.write("API_USAGE_TRACKING=true\n")
            f.write("API_RATE_LIMIT_ALERTS=true\n")
            f.write("API_COST_MONITORING=true\n")

        print(f"✅ Template exported to {template_file}")

        # Also create example file
        example_file = ".env.example"
        with open(example_file, "w") as f:
            f.write("# Copy this file to .env and add your actual API keys\n")"
            f.write("# Never commit .env to version control!\n\n")"

            for phase in [1, 2, 3, 4]:
                phase_apis = [
                    (k, v)
                    for k, v in self.api_status.items()
                    if v.phase == phase and v.cost_tier == "FREE"
# BRACKET_SURGEON: disabled
#                 ]

                if phase_apis:
                    f.write(f"# Phase {phase} - Free APIs (Start here!)\n")"
                    for api_key, status in sorted(phase_apis):
                        api_info = API_REGISTRY.get(api_key, {})
                        env_var = api_info.get("env_var", f"{api_key.upper()}_API_KEY")
                        f.write(f"{env_var}=\n")
                    f.write("\n")

        print(f"✅ Example file created: {example_file}")

    def run_health_monitor(self):
        """Run continuous health monitoring"""
        print("\n🏥 Starting API Health Monitor")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Get testable APIs
                testable_apis = [
                    k for k, v in self.api_status.items() if v.has_key and v.registered
# BRACKET_SURGEON: disabled
#                 ]

                if testable_apis:
                    import random

                    api_to_test = random.choice(testable_apis)
                    status = self.api_status[api_to_test]

                    print(f"🔍 Testing {status.name}...", end=" ")

                    try:
                        result = self.tester.test_api(api_to_test)
                        self.update_api_status(api_to_test, result)

                        if result.status == "success":
                            print(f"✅ OK ({result.response_time:.2f}s)")
                        else:
                            print(f"❌ FAILED: {result.error_message}")
                    except Exception as e:
                        print(f"❌ ERROR: {e}")
                else:
                    print("⚠️  No APIs available for monitoring")

                # Wait before next check
                time.sleep(30)  # Check every 30 seconds

        except KeyboardInterrupt:
            print("\n🛑 Health monitor stopped")

    def interactive_menu(self):
        """Main interactive menu"""
        while True:
            self.display_dashboard()

            print("🎛️  Main Menu:")
            print("1. 📋 Show API Details")
            print("2. 🔧 Register API")
            print("3. 🧪 Test API")
            print("4. 🚀 Bulk Test APIs")
            print("5. 📊 Registration Plan")
            print("6. 📄 Export Environment Template")
            print("7. 🏥 Health Monitor")
            print("8. 🔄 Refresh Dashboard")
            print("9. 🚪 Exit")
            print()

            choice = input("Select option (1-9): ").strip()

            if choice == "1":
                api_key = input("Enter API key: ").strip()
                self.show_api_details(api_key)
                input("\nPress Enter to continue...")

            elif choice == "2":
                api_key = input("Enter API key to register: ").strip()
                self.register_api_interactive(api_key)

            elif choice == "3":
                api_key = input("Enter API key to test: ").strip()
                self.test_api_interactive(api_key)
                input("\nPress Enter to continue...")

            elif choice == "4":
                phase_input = input("Enter phase (1-4) or press Enter for all: ").strip()
                phase = int(phase_input) if phase_input.isdigit() else None
                self.bulk_test_apis(phase)
                input("\nPress Enter to continue...")

            elif choice == "5":
                self.generate_registration_plan()
                input("\nPress Enter to continue...")

            elif choice == "6":
                self.export_env_template()
                input("\nPress Enter to continue...")

            elif choice == "7":
                self.run_health_monitor()

            elif choice == "8":
                continue  # Refresh dashboard

            elif choice == "9":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid option. Please try again.")
                time.sleep(1)


def main():
    """Main entry point"""
    try:
        dashboard = APIMasterDashboard()
        dashboard.interactive_menu()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()