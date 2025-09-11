#!/usr/bin/env python3
"""
TRAE AI Load Testing Script
Comprehensive load testing to validate automatic scaling performance and reliability

This script performs various load testing scenarios to ensure the monitoring
and scaling infrastructure works correctly under different conditions.
"""

import argparse
import asyncio
import concurrent.futures
import json
import logging
import random
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import aiohttp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/load-test.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Represents the result of a single HTTP request"""

    timestamp: float
    status_code: int
    response_time: float
    endpoint: str
    success: bool
    error: Optional[str] = None
    response_size: int = 0


@dataclass
class LoadTestConfig:
    """Configuration for load testing scenarios"""

    base_url: str = "http://localhost:8080"
    duration_seconds: int = 300  # 5 minutes
    concurrent_users: int = 10
    ramp_up_seconds: int = 60
    ramp_down_seconds: int = 60
    request_delay_ms: int = 1000
    timeout_seconds: int = 30


class LoadTestScenario:
    """Base class for load testing scenarios"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[TestResult] = []
        self.start_time = None
        self.end_time = None

    async def make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        method: str = "GET",
        data: Dict = None,
    ) -> TestResult:
        """Make a single HTTP request and record the result"""
        start_time = time.time()
        url = urljoin(self.config.base_url, endpoint)

        try:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)

            if method.upper() == "GET":
                async with session.get(url, timeout=timeout) as response:
                    content = await response.read()
                    response_time = time.time() - start_time

                    return TestResult(
                        timestamp=start_time,
                        status_code=response.status,
                        response_time=response_time,
                        endpoint=endpoint,
                        success=200 <= response.status < 400,
                        response_size=len(content),
                    )
            elif method.upper() == "POST":
                async with session.post(url, json=data, timeout=timeout) as response:
                    content = await response.read()
                    response_time = time.time() - start_time

                    return TestResult(
                        timestamp=start_time,
                        status_code=response.status,
                        response_time=response_time,
                        endpoint=endpoint,
                        success=200 <= response.status < 400,
                        response_size=len(content),
                    )

        except Exception as e:
            response_time = time.time() - start_time
            return TestResult(
                timestamp=start_time,
                status_code=0,
                response_time=response_time,
                endpoint=endpoint,
                success=False,
                error=str(e),
            )

    async def user_simulation(self, user_id: int, session: aiohttp.ClientSession):
        """Simulate a single user's behavior"""
        raise NotImplementedError("Subclasses must implement user_simulation")

    async def run(self) -> Dict[str, Any]:
        """Run the load test scenario"""
        logger.info(
            f"Starting load test with {
                self.config.concurrent_users} users for {
                self.config.duration_seconds}s"
        )

        self.start_time = time.time()

        # Create HTTP session with connection pooling
        connector = aiohttp.TCPConnector(
            limit=self.config.concurrent_users * 2,
            limit_per_host=self.config.concurrent_users * 2,
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            # Create tasks for all users
            tasks = []
            for user_id in range(self.config.concurrent_users):
                # Stagger user start times for ramp-up
                delay = (
                    user_id * self.config.ramp_up_seconds
                ) / self.config.concurrent_users
                task = asyncio.create_task(
                    self.delayed_user_simulation(user_id, session, delay)
                )
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        self.end_time = time.time()

        # Generate report
        return self.generate_report()

    async def delayed_user_simulation(
        self, user_id: int, session: aiohttp.ClientSession, delay: float
    ):
        """Start user simulation after a delay for ramp-up"""
        await asyncio.sleep(delay)
        await self.user_simulation(user_id, session)

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report"""
        if not self.results:
            return {"error": "No results to analyze"}

        successful_results = [r for r in self.results if r.success]
        failed_results = [r for r in self.results if not r.success]

        response_times = [r.response_time for r in successful_results]

        # Calculate statistics
        total_requests = len(self.results)
        successful_requests = len(successful_results)
        failed_requests = len(failed_results)
        success_rate = (
            (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        )

        # Response time statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = self.percentile(response_times, 95)
            p99_response_time = self.percentile(response_times, 99)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = (
                p99_response_time
            ) = 0
            min_response_time = max_response_time = 0

        # Calculate throughput
        test_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 1
        )
        requests_per_second = total_requests / test_duration

        # Error analysis
        error_types = {}
        status_codes = {}

        for result in self.results:
            # Count status codes
            status_codes[result.status_code] = (
                status_codes.get(result.status_code, 0) + 1
            )

            # Count error types
            if result.error:
                error_types[result.error] = error_types.get(result.error, 0) + 1

        # Endpoint performance
        endpoint_stats = {}
        for result in successful_results:
            if result.endpoint not in endpoint_stats:
                endpoint_stats[result.endpoint] = []
            endpoint_stats[result.endpoint].append(result.response_time)

        endpoint_performance = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_performance[endpoint] = {
                "avg_response_time": statistics.mean(times),
                "p95_response_time": self.percentile(times, 95),
                "request_count": len(times),
            }

        return {
            "test_config": asdict(self.config),
            "test_duration": test_duration,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "requests_per_second": requests_per_second,
            "response_time_stats": {
                "average": avg_response_time,
                "median": median_response_time,
                "p95": p95_response_time,
                "p99": p99_response_time,
                "min": min_response_time,
                "max": max_response_time,
            },
            "status_codes": status_codes,
            "error_types": error_types,
            "endpoint_performance": endpoint_performance,
            "timestamp": datetime.now().isoformat(),
        }

    @staticmethod
    def percentile(data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        if index.is_integer():
            return sorted_data[int(index)]
        else:
            lower = sorted_data[int(index)]
            upper = sorted_data[int(index) + 1]
            return lower + (upper - lower) * (index - int(index))


class BasicLoadTest(LoadTestScenario):
    """Basic load test scenario - simple GET requests"""

    async def user_simulation(self, user_id: int, session: aiohttp.ClientSession):
        """Simulate basic user behavior with GET requests"""
        end_time = self.start_time + self.config.duration_seconds

        endpoints = ["/health", "/api/status", "/api/version", "/api/config/status"]

        while time.time() < end_time:
            # Random endpoint selection
            endpoint = random.choice(endpoints)

            # Make request
            result = await self.make_request(session, endpoint)
            self.results.append(result)

            # Wait before next request
            await asyncio.sleep(self.config.request_delay_ms / 1000)


class ContentGenerationLoadTest(LoadTestScenario):
    """Load test for content generation endpoints"""

    async def user_simulation(self, user_id: int, session: aiohttp.ClientSession):
        """Simulate content generation requests"""
        end_time = self.start_time + self.config.duration_seconds

        content_requests = [
            {
                "endpoint": "/api/content/generate",
                "method": "POST",
                "data": {
                    "type": "blog_post",
                    "topic": f"AI Technology Trends {random.randint(1, 1000)}",
                    "length": random.choice(["short", "medium", "long"]),
                },
            },
            {
                "endpoint": "/api/content/generate",
                "method": "POST",
                "data": {
                    "type": "social_media",
                    "platform": random.choice(["twitter", "linkedin", "facebook"]),
                    "topic": f"Tech Update {random.randint(1, 1000)}",
                },
            },
            {
                "endpoint": "/api/marketing/campaign",
                "method": "POST",
                "data": {
                    "campaign_type": "email",
                    "target_audience": random.choice(
                        ["developers", "marketers", "executives"]
                    ),
                    "product": f"Product {random.randint(1, 100)}",
                },
            },
        ]

        while time.time() < end_time:
            # Random request selection
            request_config = random.choice(content_requests)

            # Make request
            result = await self.make_request(
                session,
                request_config["endpoint"],
                request_config["method"],
                request_config["data"],
            )
            self.results.append(result)

            # Longer wait for content generation
            await asyncio.sleep((self.config.request_delay_ms * 2) / 1000)


class SpikeLoadTest(LoadTestScenario):
    """Spike load test - sudden increase in traffic"""

    async def user_simulation(self, user_id: int, session: aiohttp.ClientSession):
        """Simulate spike traffic pattern"""
        # Normal load for first third
        normal_duration = self.config.duration_seconds // 3
        spike_duration = self.config.duration_seconds // 3
        recovery_duration = (
            self.config.duration_seconds - normal_duration - spike_duration
        )

        phases = [
            ("normal", normal_duration, self.config.request_delay_ms),
            (
                "spike",
                spike_duration,
                self.config.request_delay_ms // 5,
            ),  # 5x more requests
            ("recovery", recovery_duration, self.config.request_delay_ms),
        ]

        endpoints = ["/health", "/api/status", "/api/content/generate"]

        for phase_name, duration, delay in phases:
            phase_end = time.time() + duration
            logger.info(f"User {user_id}: Starting {phase_name} phase")

            while time.time() < phase_end:
                endpoint = random.choice(endpoints)

                if endpoint == "/api/content/generate":
                    result = await self.make_request(
                        session,
                        endpoint,
                        "POST",
                        {
                            "type": "quick_content",
                            "topic": f"Spike test {random.randint(1, 1000)}",
                        },
                    )
                else:
                    result = await self.make_request(session, endpoint)

                self.results.append(result)
                await asyncio.sleep(delay / 1000)


class ScalingValidationTest:
    """Test to validate that scaling actually occurs"""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.prometheus_url = "http://localhost:9090"

    async def check_scaling_metrics(self) -> Dict[str, Any]:
        """Check Prometheus metrics to validate scaling"""
        metrics_to_check = [
            "system_cpu_usage_percent",
            "system_memory_usage_percent",
            "http_requests_total",
            "scaling_events_total",
            "model_generation_queue_size",
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for metric in metrics_to_check:
                try:
                    url = f"{self.prometheus_url}/api/v1/query"
                    params = {"query": metric}

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            results[metric] = data.get("data", {}).get("result", [])
                        else:
                            results[metric] = {"error": f"HTTP {response.status}"}

                except Exception as e:
                    results[metric] = {"error": str(e)}

        return results

    async def run_scaling_validation(self) -> Dict[str, Any]:
        """Run a comprehensive scaling validation test"""
        logger.info("Starting scaling validation test")

        # Get baseline metrics
        baseline_metrics = await self.check_scaling_metrics()

        # Run spike load test to trigger scaling
        spike_config = LoadTestConfig(
            base_url=self.config.base_url,
            duration_seconds=600,  # 10 minutes
            concurrent_users=50,  # High load
            request_delay_ms=100,  # Aggressive requests
        )

        spike_test = SpikeLoadTest(spike_config)
        load_test_results = await spike_test.run()

        # Wait for scaling to settle
        await asyncio.sleep(120)  # 2 minutes

        # Get post-test metrics
        post_test_metrics = await self.check_scaling_metrics()

        return {
            "baseline_metrics": baseline_metrics,
            "load_test_results": load_test_results,
            "post_test_metrics": post_test_metrics,
            "scaling_detected": self.analyze_scaling_events(
                baseline_metrics, post_test_metrics
            ),
        }

    def analyze_scaling_events(self, baseline: Dict, post_test: Dict) -> Dict[str, Any]:
        """Analyze if scaling events occurred"""
        analysis = {
            "cpu_increase_detected": False,
            "memory_increase_detected": False,
            "scaling_events_detected": False,
            "recommendations": [],
        }

        # Check for CPU increase
        if (
            "system_cpu_usage_percent" in baseline
            and "system_cpu_usage_percent" in post_test
        ):
            baseline_cpu = baseline.get("system_cpu_usage_percent", [])
            post_cpu = post_test.get("system_cpu_usage_percent", [])

            if baseline_cpu and post_cpu:
                try:
                    baseline_val = (
                        float(baseline_cpu[0]["value"][1]) if baseline_cpu else 0
                    )
                    post_val = float(post_cpu[0]["value"][1]) if post_cpu else 0

                    if post_val > baseline_val * 1.5:  # 50% increase
                        analysis["cpu_increase_detected"] = True
                except (IndexError, ValueError, KeyError):
                    pass

        # Check for scaling events
        if "scaling_events_total" in post_test:
            scaling_events = post_test.get("scaling_events_total", [])
            if scaling_events:
                analysis["scaling_events_detected"] = True

        # Generate recommendations
        if not analysis["scaling_events_detected"]:
            analysis["recommendations"].append(
                "No scaling events detected. Check HPA configuration and metrics."
            )

        if not analysis["cpu_increase_detected"]:
            analysis["recommendations"].append(
                "CPU usage did not increase significantly. Consider increasing load test intensity."
            )

        return analysis


async def main():
    """Main function to run load tests"""
    parser = argparse.ArgumentParser(description="TRAE AI Load Testing Suite")
    parser.add_argument(
        "--base-url", default="http://localhost:8080", help="Base URL for testing"
    )
    parser.add_argument(
        "--duration", type=int, default=300, help="Test duration in seconds"
    )
    parser.add_argument(
        "--users", type=int, default=10, help="Number of concurrent users"
    )
    parser.add_argument(
        "--test-type",
        choices=["basic", "content", "spike", "scaling", "all"],
        default="all",
        help="Type of test to run",
    )
    parser.add_argument(
        "--output", default="load-test-results.json", help="Output file for results"
    )

    args = parser.parse_args()

    config = LoadTestConfig(
        base_url=args.base_url,
        duration_seconds=args.duration,
        concurrent_users=args.users,
    )

    results = {}

    if args.test_type in ["basic", "all"]:
        logger.info("Running basic load test...")
        basic_test = BasicLoadTest(config)
        results["basic_load_test"] = await basic_test.run()

    if args.test_type in ["content", "all"]:
        logger.info("Running content generation load test...")
        content_test = ContentGenerationLoadTest(config)
        results["content_load_test"] = await content_test.run()

    if args.test_type in ["spike", "all"]:
        logger.info("Running spike load test...")
        spike_test = SpikeLoadTest(config)
        results["spike_load_test"] = await spike_test.run()

    if args.test_type in ["scaling", "all"]:
        logger.info("Running scaling validation test...")
        scaling_test = ScalingValidationTest(config)
        results["scaling_validation"] = await scaling_test.run_scaling_validation()

    # Save results to file
    with open(args.output, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Print summary
    print("\n" + "=" * 50)
    print("TRAE AI LOAD TEST SUMMARY")
    print("=" * 50)

    for test_name, test_results in results.items():
        if "success_rate" in test_results:
            print(f"\n{test_name.upper()}:")
            print(f"  Success Rate: {test_results['success_rate']:.2f}%")
            print(f"  Total Requests: {test_results['total_requests']}")
            print(f"  Requests/sec: {test_results['requests_per_second']:.2f}")
            print(
                f"  Avg Response Time: {
                    test_results['response_time_stats']['average']:.3f}s"
            )
            print(
                f"  P95 Response Time: {
                    test_results['response_time_stats']['p95']:.3f}s"
            )

    print(f"\nDetailed results saved to: {args.output}")
    print("=" * 50)


if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    import os

    os.makedirs("logs", exist_ok=True)

    # Run the load tests
    asyncio.run(main())
