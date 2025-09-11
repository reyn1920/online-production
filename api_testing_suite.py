#!/usr/bin/env python3
"""
API Testing Suite
Comprehensive testing for all registered APIs

Usage:
    python api_testing_suite.py --test-all
    python api_testing_suite.py --test huggingface
    python api_testing_suite.py --health-check
"""

import argparse
import asyncio
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests
# Load environment variables
from dotenv import load_dotenv

load_dotenv()


@dataclass
class APITestResult:
    api_name: str
    status: str  # 'success', 'failed', 'no_key', 'error'
    response_time: float
    error_message: Optional[str] = None
    response_data: Optional[Dict] = None


class APITester:
    def __init__(self):
        self.results = []
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def test_huggingface_api(self) -> APITestResult:
        """Test Hugging Face API"""
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            return APITestResult("Hugging Face", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(
                "https://huggingface.co/api/whoami", headers=headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "Hugging Face",
                    "success",
                    response_time,
                    response_data=response.json(),
                )
            else:
                return APITestResult(
                    "Hugging Face",
                    "failed",
                    response_time,
                    f"HTTP {response.status_code}",
                )

        except Exception as e:
            return APITestResult("Hugging Face", "error", 0, str(e))

    def test_groq_api(self) -> APITestResult:
        """Test Groq API"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return APITestResult("Groq", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "messages": [{"role": "user", "content": "Hello"}],
                "model": "mixtral-8x7b-32768",
                "max_tokens": 10,
            }
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "Groq", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Groq", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Groq", "error", 0, str(e))

    def test_google_ai_api(self) -> APITestResult:
        """Test Google AI (Gemini) API"""
        api_key = os.getenv("GOOGLE_AI_API_KEY")
        if not api_key:
            return APITestResult("Google AI", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
            )
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "Google AI", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Google AI", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Google AI", "error", 0, str(e))

    def test_youtube_api(self) -> APITestResult:
        """Test YouTube Data API"""
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return APITestResult("YouTube", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key={api_key}&maxResults=1"
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "YouTube", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "YouTube", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("YouTube", "error", 0, str(e))

    def test_reddit_api(self) -> APITestResult:
        """Test Reddit API"""
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")

        if not client_id or not client_secret:
            return APITestResult("Reddit", "no_key", 0, "Client ID or secret not found")

        try:
            start_time = time.time()
            # Get access token
            auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
            data = {"grant_type": "client_credentials"}
            headers = {"User-Agent": "APITester/1.0"}

            token_response = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data=data,
                headers=headers,
                timeout=10,
            )

            if token_response.status_code == 200:
                token_data = token_response.json()
                access_token = token_data["access_token"]

                # Test API call
                headers["Authorization"] = f"Bearer {access_token}"
                response = requests.get(
                    "https://oauth.reddit.com/r/test/hot?limit=1",
                    headers=headers,
                    timeout=10,
                )
                response_time = time.time() - start_time

                if response.status_code == 200:
                    return APITestResult(
                        "Reddit",
                        "success",
                        response_time,
                        response_data=response.json(),
                    )
                else:
                    return APITestResult(
                        "Reddit",
                        "failed",
                        response_time,
                        f"HTTP {response.status_code}",
                    )
            else:
                return APITestResult("Reddit", "failed", 0, "Token request failed")

        except Exception as e:
            return APITestResult("Reddit", "error", 0, str(e))

    def test_github_api(self) -> APITestResult:
        """Test GitHub API"""
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return APITestResult("GitHub", "no_key", 0, "Token not found")

        try:
            start_time = time.time()
            headers = {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }
            response = requests.get(
                "https://api.github.com/user", headers=headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "GitHub", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "GitHub", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("GitHub", "error", 0, str(e))

    def test_netlify_api(self) -> APITestResult:
        """Test Netlify API"""
        token = os.getenv("NETLIFY_AUTH_TOKEN")
        if not token:
            return APITestResult("Netlify", "no_key", 0, "Auth token not found")

        try:
            start_time = time.time()
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(
                "https://api.netlify.com/api/v1/user", headers=headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "Netlify", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Netlify", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Netlify", "error", 0, str(e))

    def test_sendgrid_api(self) -> APITestResult:
        """Test SendGrid API"""
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            return APITestResult("SendGrid", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            response = requests.get(
                "https://api.sendgrid.com/v3/user/profile", headers=headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "SendGrid", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "SendGrid", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("SendGrid", "error", 0, str(e))

    def test_openweather_api(self) -> APITestResult:
        """Test OpenWeatherMap API"""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return APITestResult("OpenWeather", "no_key", 0, "API key not found")

        try:
            start_time = time.time()
            url = f"https://api.openweathermap.org/data/2.5/weather?q=London&appid={api_key}"
            response = requests.get(url, timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "OpenWeather",
                    "success",
                    response_time,
                    response_data=response.json(),
                )
            else:
                return APITestResult(
                    "OpenWeather",
                    "failed",
                    response_time,
                    f"HTTP {response.status_code}",
                )

        except Exception as e:
            return APITestResult("OpenWeather", "error", 0, str(e))

    def test_unsplash_api(self) -> APITestResult:
        """Test Unsplash API"""
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not access_key:
            return APITestResult("Unsplash", "no_key", 0, "Access key not found")

        try:
            start_time = time.time()
            headers = {"Authorization": f"Client-ID {access_key}"}
            response = requests.get(
                "https://api.unsplash.com/photos/random?count=1",
                headers=headers,
                timeout=10,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                return APITestResult(
                    "Unsplash", "success", response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Unsplash", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Unsplash", "error", 0, str(e))

    def test_dog_api(self) -> APITestResult:
        """Test Dog API"""
        api_key = os.getenv("DOG_API_KEY")

        try:
            start_time = time.time()
            headers = {}
            if api_key:
                headers["x-api-key"] = api_key

            response = requests.get(
                "https://api.thedogapi.com/v1/breeds?limit=1",
                headers=headers,
                timeout=10,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                status = "success" if api_key else "no_key"
                return APITestResult(
                    "Dog API", status, response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Dog API", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Dog API", "error", 0, str(e))

    def test_cat_api(self) -> APITestResult:
        """Test Cat API"""
        api_key = os.getenv("CAT_API_KEY")

        try:
            start_time = time.time()
            headers = {}
            if api_key:
                headers["x-api-key"] = api_key

            response = requests.get(
                "https://api.thecatapi.com/v1/breeds?limit=1",
                headers=headers,
                timeout=10,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                status = "success" if api_key else "no_key"
                return APITestResult(
                    "Cat API", status, response_time, response_data=response.json()
                )
            else:
                return APITestResult(
                    "Cat API", "failed", response_time, f"HTTP {response.status_code}"
                )

        except Exception as e:
            return APITestResult("Cat API", "error", 0, str(e))

    def run_all_tests(self) -> List[APITestResult]:
        """Run all available API tests"""
        test_methods = [
            self.test_huggingface_api,
            self.test_groq_api,
            self.test_google_ai_api,
            self.test_youtube_api,
            self.test_reddit_api,
            self.test_github_api,
            self.test_netlify_api,
            self.test_sendgrid_api,
            self.test_openweather_api,
            self.test_unsplash_api,
            self.test_dog_api,
            self.test_cat_api,
        ]

        results = []

        print("🧪 Running API tests...")

        # Run tests in parallel
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_test = {
                executor.submit(test): test.__name__ for test in test_methods
            }

            for future in as_completed(future_to_test):
                test_name = future_to_test[future]
                try:
                    result = future.result()
                    results.append(result)

                    # Print progress
                    status_emoji = {
                        "success": "✅",
                        "failed": "❌",
                        "no_key": "🔑",
                        "error": "💥",
                    }
                    print(
                        f"{status_emoji.get(result.status, '❓')} {result.api_name}: {result.status}"
                    )

                except Exception as e:
                    print(f"💥 {test_name}: Exception - {str(e)}")

        return results

    def run_specific_test(self, api_name: str) -> Optional[APITestResult]:
        """Run test for a specific API"""
        test_mapping = {
            "huggingface": self.test_huggingface_api,
            "groq": self.test_groq_api,
            "google_ai": self.test_google_ai_api,
            "youtube": self.test_youtube_api,
            "reddit": self.test_reddit_api,
            "github": self.test_github_api,
            "netlify": self.test_netlify_api,
            "sendgrid": self.test_sendgrid_api,
            "openweather": self.test_openweather_api,
            "unsplash": self.test_unsplash_api,
            "dog_api": self.test_dog_api,
            "cat_api": self.test_cat_api,
        }

        test_method = test_mapping.get(api_name.lower())
        if not test_method:
            print(f"❌ Unknown API: {api_name}")
            return None

        print(f"🧪 Testing {api_name}...")
        result = test_method()

        status_emoji = {"success": "✅", "failed": "❌", "no_key": "🔑", "error": "💥"}
        print(
            f"{status_emoji.get(result.status, '❓')} {result.api_name}: {result.status}"
        )

        if result.error_message:
            print(f"   Error: {result.error_message}")

        return result

    def generate_report(self, results: List[APITestResult]) -> str:
        """Generate a comprehensive test report"""
        report = []
        report.append("# API Testing Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("\n## Summary")

        # Count results by status
        status_counts = {}
        for result in results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        total_tests = len(results)
        success_rate = (
            (status_counts.get("success", 0) / total_tests * 100)
            if total_tests > 0
            else 0
        )

        report.append(f"- Total APIs tested: {total_tests}")
        report.append(f"- Success rate: {success_rate:.1f}%")
        report.append(f"- Successful: {status_counts.get('success', 0)}")
        report.append(f"- Failed: {status_counts.get('failed', 0)}")
        report.append(f"- No API key: {status_counts.get('no_key', 0)}")
        report.append(f"- Errors: {status_counts.get('error', 0)}")

        report.append("\n## Detailed Results")

        for result in sorted(results, key=lambda x: x.api_name):
            report.append(f"\n### {result.api_name}")
            report.append(f"- Status: {result.status.upper()}")
            report.append(f"- Response time: {result.response_time:.3f}s")

            if result.error_message:
                report.append(f"- Error: {result.error_message}")

            if result.response_data and result.status == "success":
                report.append(f"- Response: Available")

        report.append("\n## Recommendations")

        if status_counts.get("no_key", 0) > 0:
            report.append("- 🔑 Register for APIs with missing keys")

        if status_counts.get("failed", 0) > 0:
            report.append("- ❌ Check failed API configurations")

        if status_counts.get("error", 0) > 0:
            report.append("- 💥 Investigate API connection errors")

        return "\n".join(report)

    def health_check(self) -> Dict[str, any]:
        """Quick health check for critical APIs"""
        critical_apis = ["huggingface", "groq", "github", "netlify"]

        health_status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "apis": {},
        }

        for api in critical_apis:
            result = self.run_specific_test(api)
            if result:
                health_status["apis"][api] = {
                    "status": result.status,
                    "response_time": result.response_time,
                }

                if result.status not in ["success", "no_key"]:
                    health_status["overall_status"] = "degraded"

        return health_status


def main():
    parser = argparse.ArgumentParser(description="API Testing Suite")
    parser.add_argument("--test-all", action="store_true", help="Run all API tests")
    parser.add_argument("--test", type=str, help="Test a specific API")
    parser.add_argument(
        "--health-check", action="store_true", help="Quick health check"
    )
    parser.add_argument("--report", type=str, help="Generate report file")

    args = parser.parse_args()

    tester = APITester()

    if args.health_check:
        health = tester.health_check()
        print(json.dumps(health, indent=2))
    elif args.test:
        result = tester.run_specific_test(args.test)
    elif args.test_all:
        results = tester.run_all_tests()

        # Generate and display report
        report = tester.generate_report(results)
        print("\n" + "=" * 60)
        print(report)

        # Save report if requested
        if args.report:
            with open(args.report, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to {args.report}")
    else:
        print("🧪 API Testing Suite")
        print("Use --help for options")

        # Quick interactive test
        choice = input("\nRun quick health check? (y/n): ").lower()
        if choice == "y":
            health = tester.health_check()
            print(json.dumps(health, indent=2))


if __name__ == "__main__":
    main()
