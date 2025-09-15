#!/usr / bin / env python3
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
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Import our custom modules
try:
    from api_registration_automation import API_REGISTRY, APIRegistrationManager
    from api_testing_suite import APITester, APITestResult

except ImportError:
    print(
        "⚠️  Required modules not found. Make sure api_registration_automation.py \"
#     and api_testing_suite.py are in the same directory."
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

        # Phase breakdown
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

        # Cost breakdown
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
            "registration_rate": ((registered_count / total_apis * 100) if total_apis > 0 else 0),
            "success_rate": ((working_count / tested_count * 100) if tested_count > 0 else 0),
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
        print(f"🔑 Has Keys: {stats['has_keys']}")
        print(f"🧪 Tested: {stats['tested']}")
        print(f"💚 Working: {stats['working']} ({stats['success_rate']:.1f}% success rate)")

        print("\\n📋 Phase Breakdown:")
        for phase, data in stats["phase_stats"].items():
            print(
                f"  Phase {phase}: {data['working']}/{data['registered']}/{data['total']} (Working / Registered / Total)"
# BRACKET_SURGEON: disabled
#             )

        print("\\n💰 Cost Breakdown:")
        for cost_tier, data in stats["cost_stats"].items():
            print(
                f"  {cost_tier}: {data['working']}/{data['registered']}/{data['total']} (Working / Registered / Total)"
# BRACKET_SURGEON: disabled
#             )

        # Recent activity
        recent_tests = [(k, v) for k, v in self.api_status.items() if v.last_tested]
        recent_tests.sort(key=lambda x: x[1].last_tested or "", reverse=True)

        if recent_tests:
            print("\\n🕒 Recent Test Results:")
            for api_key, status in recent_tests[:5]:
                status_emoji = {
                    "success": "✅",
                    "failed": "❌",
                    "no_key": "🔑",
                    "error": "💥",
                }.get(status.test_status, "❓")
                print(f"  {status_emoji} {status.name}: {status.test_status}")

    def show_api_details(self, api_key: str):
        """Show detailed information for a specific API"""
        if api_key not in self.api_status:
            print(f"❌ API '{api_key}' not found")
            return

        status = self.api_status[api_key]
        api_info = API_REGISTRY.get(api_key, {})

        print(f"\\n📋 {status.name} Details")
        print("=" * 40)
        print(f"🔧 API Key: {api_key}")
        print(f"📊 Phase: {status.phase}")
        print(f"⭐ Priority: {status.priority}")
        print(f"💰 Cost: {status.cost_tier}")
        print(f"✅ Registered: {'Yes' if status.registered else 'No'}")
        print(f"🔑 Has Key: {'Yes' if status.has_key else 'No'}")

        if status.last_tested:
            print(f"🧪 Last Tested: {status.last_tested}")
            print(f"📈 Test Status: {status.test_status}")
            if status.response_time:
                print(f"⚡ Response Time: {status.response_time:.3f}s")

        if status.last_error:
            print(f"❌ Last Error: {status.last_error}")

        if api_info:
            print(f"\\n🔗 Registration URL: {api_info.get('signup_url', 'N / A')}")
            print(f"🔗 Login URL: {api_info.get('login_url', 'N / A')}")
            print(f"🔧 Environment Variable: {api_info.get('env_var', 'N / A')}")
            print(f"📝 Instructions: {api_info.get('instructions', 'N / A')}")

    def register_api_interactive(self, api_key: str):
        """Interactive API registration"""
        if api_key not in API_REGISTRY:
            print(f"❌ Unknown API: {api_key}")
            return

        print(f"\\n🚀 Registering {API_REGISTRY[api_key]['name']}")
        success = self.registration_manager.open_registration_page(api_key)

        if success:
            # Update status
            if api_key in self.api_status:
                self.api_status[api_key].registered = True
                self.api_status[api_key].has_key = bool(os.getenv(API_REGISTRY[api_key]["env_var"]))
                self.save_status()

    def test_api_interactive(self, api_key: str):
        """Interactive API testing"""
        print(f"\\n🧪 Testing {api_key}...")
        result = self.tester.run_specific_test(api_key)

        if result:
            self.update_api_status(api_key, result)

            if result.status == "success":
                print(f"✅ {result.api_name} is working correctly!")
                if result.response_time:
                    print(f"⚡ Response time: {result.response_time:.3f}s")
            elif result.status == "no_key":
                print(f"🔑 {result.api_name} needs an API key")
                register = input("Would you like to register now? (y / n): ").lower()
                if register == "y":
                    self.register_api_interactive(api_key)
            else:
                print(f"❌ {result.api_name} test failed: {result.error_message}")

    def bulk_test_apis(self, phase: Optional[int] = None):
        """Test multiple APIs in bulk"""
        if phase:
            apis_to_test = [k for k, v in API_REGISTRY.items() if v["phase"] == phase]
            print(f"\\n🧪 Testing Phase {phase} APIs ({len(apis_to_test)} APIs)")
        else:
            apis_to_test = list(API_REGISTRY.keys())
            print(f"\\n🧪 Testing All APIs ({len(apis_to_test)} APIs)")

        results = []
        for i, api_key in enumerate(apis_to_test, 1):
            print(f"\\n[{i}/{len(apis_to_test)}] Testing {API_REGISTRY[api_key]['name']}...")
            result = self.tester.run_specific_test(api_key)
            if result:
                results.append(result)
                self.update_api_status(api_key, result)

        # Summary
        success_count = sum(1 for r in results if r.status == "success")
        print(f"\\n📊 Bulk Test Summary:")
        print(f"✅ Successful: {success_count}/{len(results)}")
        print(f"📈 Success Rate: {success_count / len(results)*100:.1f}%")

    def generate_registration_plan(self):
        """Generate a prioritized registration plan"""
        unregistered_apis = [(k, v) for k, v in self.api_status.items() if not v.registered]

        # Sort by phase and priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        unregistered_apis.sort(key=lambda x: (x[1].phase, priority_order.get(x[1].priority, 3)))

        print("\\n📋 Registration Plan (Prioritized)")
        print("=" * 50)

        current_phase = None
        for api_key, status in unregistered_apis:
            if status.phase != current_phase:
                current_phase = status.phase
                print(f"\\n🎯 Phase {current_phase}:")

            cost_emoji = {"FREE": "🟢", "FREEMIUM": "🟡", "PAID": "🔴"}
            priority_emoji = {"high": "🔥", "medium": "⭐", "low": "💡"}

            print(
                f"  {priority_emoji.get(status.priority, '❓')} {cost_emoji.get(status.cost_tier, '❓')} {status.name}"
# BRACKET_SURGEON: disabled
#             )

        print(f"\\n📊 Total unregistered: {len(unregistered_apis)} APIs")

    def export_env_template(self):
        """Export environment template with current status"""
        template_file = ".env.master_template"

        with open(template_file, "w") as f:
            f.write("# Master API Environment Template\\n")"
            f.write(f"# Generated: {datetime.now().isoformat()}\\n")"
            f.write(f"# Total APIs: {len(self.api_status)}\\n\\n")"

            # Group by phase
            phases = {}
            for api_key, status in self.api_status.items():
                if status.phase not in phases:
                    phases[status.phase] = []
                phases[status.phase].append((api_key, status))

            for phase in sorted(phases.keys()):
                f.write(f"\\n# ===== PHASE {phase} APIs =====\\n")"

                for api_key, status in phases[phase]:
                    api_info = API_REGISTRY.get(api_key, {})
                    env_var = api_info.get("env_var", f"{api_key.upper()}_API_KEY")

                    f.write(f"\\n# {status.name} ({status.cost_tier})\\n")"
                    f.write(
                        f"# Status: {'✅ Registered' if status.registered else '❌ Not registered'}""
# BRACKET_SURGEON: disabled
#                     )
                    if status.has_key:
                        f.write(" | 🔑 Has key")
                    if status.test_status == "success":
                        f.write(" | ✅ Working")
                    f.write("\\n")

                    if api_info.get("signup_url"):
                        f.write(f"# Signup: {api_info['signup_url']}\\n")"

                    current_value = os.getenv(env_var, "")
                    f.write(f"{env_var}={current_value}\\n")

        print(f"✅ Exported environment template to {template_file}")

    def run_health_monitor(self):
        """Run continuous health monitoring"""
        print("\\n🏥 Starting Health Monitor...")
        print("Press Ctrl + C to stop")

        try:
            while True:
                # Test critical APIs
                critical_apis = [
                    k for k, v in self.api_status.items() if v.priority == "high" and v.has_key
# BRACKET_SURGEON: disabled
#                 ]

                if critical_apis:
                    print(f"\\n🔍 Health check at {datetime.now().strftime('%H:%M:%S')}")

                    for api_key in critical_apis[:3]:  # Test top 3 critical APIs
                        result = self.tester.run_specific_test(api_key)
                        if result:
                            self.update_api_status(api_key, result)
                            status_emoji = {
                                "success": "✅",
                                "failed": "❌",
                                "no_key": "🔑",
                                "error": "💥",
                            }.get(result.status, "❓")
                            print(f"  {status_emoji} {result.api_name}: {result.status}")

                # Wait 5 minutes
                time.sleep(300)

        except KeyboardInterrupt:
            print("\\n🛑 Health monitor stopped")

    def interactive_menu(self):
        """Main interactive menu"""
        while True:
            self.display_dashboard()

            print("\\n🎛️  Actions:")
            print("1. 📋 View API details")
            print("2. 🚀 Register API")
            print("3. 🧪 Test API")
            print("4. 📊 Bulk test (by phase)")
            print("5. 📋 Registration plan")
            print("6. 📄 Export .env template")
            print("7. 🏥 Health monitor")
            print("8. 🔄 Refresh dashboard")
            print("9. ❌ Exit")

            choice = input("\\nSelect action (1 - 9): ").strip()

            if choice == "1":
                api_key = input("Enter API key: ").strip()
                self.show_api_details(api_key)
                input("\\nPress Enter to continue...")

            elif choice == "2":
                api_key = input("Enter API key to register: ").strip()
                self.register_api_interactive(api_key)
                input("\\nPress Enter to continue...")

            elif choice == "3":
                api_key = input("Enter API key to test: ").strip()
                self.test_api_interactive(api_key)
                input("\\nPress Enter to continue...")

            elif choice == "4":
                phase = input("Enter phase (1 - 4) or 'all': ").strip()
                if phase == "all":
                    self.bulk_test_apis()
                else:
                    try:
                        phase_num = int(phase)
                        if 1 <= phase_num <= 4:
                            self.bulk_test_apis(phase_num)
                        else:
                            print("❌ Invalid phase. Use 1 - 4 or 'all'")
                    except ValueError:
                        print("❌ Invalid input")
                input("\\nPress Enter to continue...")

            elif choice == "5":
                self.generate_registration_plan()
                input("\\nPress Enter to continue...")

            elif choice == "6":
                self.export_env_template()
                input("\\nPress Enter to continue...")

            elif choice == "7":
                self.run_health_monitor()

            elif choice == "8":
                continue  # Refresh dashboard

            elif choice == "9":
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice")
                time.sleep(1)


def main():
    """Main entry point"""
    try:
        dashboard = APIMasterDashboard()
        dashboard.interactive_menu()
    except KeyboardInterrupt:
        print("\\n👋 Dashboard closed")
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()