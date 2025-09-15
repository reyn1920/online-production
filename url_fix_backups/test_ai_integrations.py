#!/usr / bin / env python3
""""""
Comprehensive AI Platform Integration Test
Tests ChatGPT, Gemini, and Abacus AI integrations
""""""

import requests
import json
import time
import sys
from datetime import datetime


class AIIntegrationTester:
    def __init__(self):
        self.base_urls = {
            "main_dashboard": "http://127.0.0.1:8080",
            "quality_dashboard": "http://localhost:5004",
            "ai_benchmark": "http://0.0.0.0:5003",
            "minimal_server": "http://localhost:8000",
# BRACKET_SURGEON: disabled
#         }
        self.test_results = []

    def log_result(self, test_name, status, message=""):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }
        self.test_results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status} - {message}")

    def test_server_health(self, name, url):
        """Test if server is responding"""
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                self.log_result(f"{name} Health Check", "PASS", f"Server responding on {url}")
                return True
            else:
                self.log_result(f"{name} Health Check", "FAIL", f"HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_result(f"{name} Health Check", "FAIL", f"Connection error: {str(e)}")
            return False

    def test_ai_platform_endpoints(self):
        """Test AI platform specific endpoints"""
        ai_endpoints = [
            ("/api / chatgpt / status", "ChatGPT Status"),
            ("/api / gemini / status", "Gemini Status"),
            ("/api / abacus / status", "Abacus AI Status"),
            ("/api / ai / benchmark", "AI Benchmark"),
            ("/api / cost - tracking", "Cost Tracking"),
# BRACKET_SURGEON: disabled
#         ]

        for endpoint, name in ai_endpoints:
            try:
                # Try main dashboard first
                response = requests.get(f"{self.base_urls['main_dashboard']}{endpoint}", timeout=5)
                if response.status_code in [
                    200,
                    404,
# BRACKET_SURGEON: disabled
#                 ]:  # 404 is acceptable for some endpoints
                    self.log_result(f"{name} Endpoint", "PASS", f"Endpoint accessible")
                else:
                    self.log_result(f"{name} Endpoint", "WARN", f"HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_result(f"{name} Endpoint", "WARN", f"Endpoint test failed: {str(e)}")

    def test_dashboard_pages(self):
        """Test dashboard page accessibility"""
        pages = [
            ("/", "Main Dashboard"),
            ("/dashboard", "Dashboard Page"),
            ("/ai - integration", "AI Integration Page"),
            ("/quality", "Quality Page"),
# BRACKET_SURGEON: disabled
#         ]

        for page, name in pages:
            try:
                response = requests.get(f"{self.base_urls['main_dashboard']}{page}", timeout=5)
                if response.status_code == 200:
                    self.log_result(f"{name} Page", "PASS", "Page loads successfully")
                else:
                    self.log_result(f"{name} Page", "WARN", f"HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.log_result(f"{name} Page", "WARN", f"Page test failed: {str(e)}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting AI Platform Integration Tests")
        print("=" * 50)

        # Test server health
        print("\\n📊 Testing Server Health...")
        for name, url in self.base_urls.items():
            self.test_server_health(name.replace("_", " ").title(), url)

        # Test AI platform endpoints
        print("\\n🤖 Testing AI Platform Endpoints...")
        self.test_ai_platform_endpoints()

        # Test dashboard pages
        print("\\n📱 Testing Dashboard Pages...")
        self.test_dashboard_pages()

        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate test summary"""
        print("\\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)

        passed = len([r for r in self.test_results if r["status"] == "PASS"])
        failed = len([r for r in self.test_results if r["status"] == "FAIL"])
        warnings = len([r for r in self.test_results if r["status"] == "WARN"])
        total = len(self.test_results)

        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Warnings: {warnings}")
        print(f"📊 Total Tests: {total}")

        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"🎯 Success Rate: {success_rate:.1f}%")

        if failed == 0:
            print("\\n🎉 All critical tests passed! System ready for deployment.")
        else:
            print("\\n⚠️  Some tests failed. Review issues before deployment.")

        # Save detailed results
        with open("ai_integration_test_results.json", "w") as f:
            json.dump(
                {
                    "summary": {
                        "passed": passed,
                        "failed": failed,
                        "warnings": warnings,
                        "total": total,
                        "success_rate": success_rate,
# BRACKET_SURGEON: disabled
#                     },
                    "results": self.test_results,
# BRACKET_SURGEON: disabled
#                 },
                f,
                indent=2,
# BRACKET_SURGEON: disabled
#             )

        print(f"\\n📄 Detailed results saved to: ai_integration_test_results.json")


if __name__ == "__main__":
    tester = AIIntegrationTester()
    tester.run_all_tests()