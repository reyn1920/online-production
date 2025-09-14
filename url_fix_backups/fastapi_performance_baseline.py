#!/usr / bin / env python3
"""
FastAPI Performance Baseline for MacBook Air M1 (16GB)
Comprehensive performance testing and optimization toolkit
"""

import asyncio
import json
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:

    import httpx
    import psutil

except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "psutil"])

    import httpx
    import psutil


class MacBookAirM1Benchmark:
    """Performance baseline testing for FastAPI on MacBook Air M1"""


    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.system_info = self.get_system_info()


    def get_system_info(self) -> Dict[str, Any]:
        """Collect MacBook Air M1 system information"""
        return {
            "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical = True),
                "memory_total_gb": round(psutil.virtual_memory().total/(1024**3), 2),
                "memory_available_gb": round(
                psutil.virtual_memory().available/(1024**3), 2
            ),
                "platform": "MacBook Air M1",
                }


    def check_hey_installation(self) -> bool:
        """Check if hey is installed, install if needed"""
        try:
            result = subprocess.run(["hey", "-h"], capture_output = True, text = True)
            return result.returncode == 0
        except FileNotFoundError:
            print("📦 Installing hey load testing tool...")
            try:
                subprocess.run(["brew", "install", "hey"], check = True)
                print("✅ hey installed successfully")
                return True
            except subprocess.CalledProcessError:
                print(
                    "❌ Failed to install hey. Please install manually: brew install hey"
                )
                return False


    def run_hey_benchmark(
        self, endpoint: str, duration: str = "30s", concurrency: int = 50
    ) -> Dict[str, Any]:
        """Run hey load test and parse results"""
        if not self.check_hey_installation():
            return {"error": "hey not available"}

        url = f"{self.base_url}{endpoint}"
        cmd = ["hey", "-z", duration, "-c", str(concurrency), "-o", "json", url]

        print(f"🚀 Running hey benchmark: {url}")
        print(f"   Duration: {duration}, Concurrency: {concurrency}")

        try:
            result = subprocess.run(cmd,
    capture_output = True,
    text = True,
    timeout = 120)
            if result.returncode == 0:
                # Parse hey JSON output
                data = json.loads(result.stdout)
                return {
                    "tool": "hey",
                        "endpoint": endpoint,
                        "duration": duration,
                        "concurrency": concurrency,
                        "total_requests": data.get("summary", {}).get("total", 0),
                        "requests_per_sec": data.get("summary", {}).get("rps", 0),
                        "avg_latency_ms": data.get("summary", {}).get("average",
    0) * 1000,
                        "fastest_ms": data.get("summary", {}).get("fastest", 0) * 1000,
                        "slowest_ms": data.get("summary", {}).get("slowest", 0) * 1000,
                        "success_rate": (1 - data.get("summary", {}).get("errorRate",
    0))
                    * 100,
                        "status_codes": data.get("statusCodeDist", {}),
                        }
            else:
                return {"error": f"hey failed: {result.stderr}"}
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            return {"error": f"hey execution failed: {str(e)}"}


    async def async_benchmark(
        self, endpoint: str, concurrent_users: int = 50, duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """Custom async Python benchmark"""
        print(f"🐍 Running async Python benchmark: {self.base_url}{endpoint}")
        print(f"   Concurrent users: {concurrent_users}, Duration: {duration_seconds}s")

        limits = httpx.Limits(max_keepalive_connections = 200, max_connections = 400)
        timeout = httpx.Timeout(10.0)

        async with httpx.AsyncClient(
            limits = limits, timeout = timeout, verify = False
        ) as client:
            start_time = time.perf_counter()
            end_time = start_time + duration_seconds

            tasks = []
            results = []

            while time.perf_counter() < end_time:
                if len(tasks) < concurrent_users:
                    task = asyncio.create_task(self.single_request(client, endpoint))
                    tasks.append(task)

                done_tasks = [task for task in tasks if task.done()]
                for task in done_tasks:
                    result = await task
                    results.append(result)
                    tasks.remove(task)

                await asyncio.sleep(0.001)

            # Wait for remaining tasks
            if tasks:
                remaining = await asyncio.gather(*tasks, return_exceptions = True)
                for result in remaining:
                    if isinstance(result, dict):
                        results.append(result)

            actual_duration = time.perf_counter() - start_time
            return self.analyze_async_results(results, actual_duration, endpoint)


    async def single_request(
        self, client: httpx.AsyncClient, endpoint: str
    ) -> Dict[str, Any]:
        """Make single HTTP request with timing"""
        start_time = time.perf_counter()
        try:
            response = await client.get(f"{self.base_url}{endpoint}")
            end_time = time.perf_counter()

            return {
                "status": response.status_code,
                    "duration": end_time - start_time,
                    "success": response.status_code == 200,
                    "size": len(response.content),
                    }
        except Exception as e:
            end_time = time.perf_counter()
            return {
                "status": 0,
                    "duration": end_time - start_time,
                    "success": False,
                    "error": str(e),
                    "size": 0,
                    }


    def analyze_async_results(
        self, results: List[Dict], duration: float, endpoint: str
    ) -> Dict[str, Any]:
        """Analyze async benchmark results"""
        successful = [r for r in results if r.get("success", False)]
        failed = [r for r in results if not r.get("success", False)]

        if not successful:
            return {
                "tool": "async_python",
                    "endpoint": endpoint,
                    "error": "No successful requests",
                    "total_requests": len(results),
                    "failed_requests": len(failed),
                    }

        durations = [r["duration"] for r in successful]

        return {
            "tool": "async_python",
                "endpoint": endpoint,
                "duration_seconds": round(duration, 2),
                "total_requests": len(results),
                "successful_requests": len(successful),
                "failed_requests": len(failed),
                "requests_per_sec": round(len(successful) / duration, 2),
                "success_rate": round(len(successful) / len(results) * 100, 2),
                "avg_latency_ms": round(statistics.mean(durations) * 1000, 2),
                "median_latency_ms": round(statistics.median(durations) * 1000, 2),
                "p95_latency_ms": (
                round(statistics.quantiles(durations, n = 20)[18] * 1000, 2)
                if len(durations) > 20
                else 0
            ),
                "p99_latency_ms": (
                round(statistics.quantiles(durations, n = 100)[98] * 1000, 2)
                if len(durations) > 100
                else 0
            ),
                "fastest_ms": round(min(durations) * 1000, 2),
                "slowest_ms": round(max(durations) * 1000, 2),
                }


    def check_nginx_config(self) -> Dict[str, Any]:
        """Check Nginx configuration for M1 optimization"""
        nginx_config_path = Path("nginx / nginx.conf")

        if not nginx_config_path.exists():
            return {"error": "nginx.conf not found"}

        try:
            with open(nginx_config_path, "r") as f:
                config = f.read()

            checks = {
                "worker_processes_2": "worker_processes 2" in config
                or "worker_processes auto" in config,
                    "worker_connections_1024": "worker_connections 1024" in config,
                    "gzip_enabled": "gzip on" in config,
                    "http2_enabled": "http2" in config,
                    "keepalive_timeout": "keepalive_timeout" in config,
                    }

            return {
                "nginx_config_found": True,
                    "optimizations": checks,
                    "score": sum(checks.values())/len(checks) * 100,
                    }
        except Exception as e:
            return {"error": f"Failed to read nginx config: {str(e)}"}


    def get_performance_targets(self) -> Dict[str, Any]:
        """MacBook Air M1 performance targets"""
        return {
            "simple_endpoints_rps": {"min": 2000, "target": 5000},
                "p95_latency_ms": {"max": 50, "target": 20},
                "frontend_assets_ms": {"max": 10, "target": 5},
                "concurrent_clients": {"max": 200, "recommended": 100},
                "memory_usage_gb": {"max": 2, "recommended": 1},
                }


    def print_results(self, results: Dict[str, Any]):
        """Pretty print benchmark results"""
        if "error" in results:
            tool_name = results.get("tool", "BENCHMARK").upper()
            print(f"❌ {tool_name} failed: {results['error']}")
            return

        tool = results.get("tool", "unknown").upper()
        endpoint = results.get("endpoint", "unknown")

        print(f"\\n📊 {tool} RESULTS - {endpoint}")
        print("=" * 60)

        if "duration_seconds" in results:
            print(f"Duration:           {results['duration_seconds']}s")
        elif "duration" in results:
            print(f"Duration:           {results['duration']}")

        print(f"Total requests:     {results.get('total_requests', 0):,}")
        print(
            f"Successful:         {results.get('successful_requests',
    results.get('total_requests',
    0)):,}"
        )
        print(f"Failed:             {results.get('failed_requests', 0):,}")
        print(f"Success rate:       {results.get('success_rate', 0):.1f}%")
        print(f"Requests / sec:       {results.get('requests_per_sec', 0):,.1f}")

        print(f"\\n⏱️  LATENCY")
        print("-" * 20)
        if "avg_latency_ms" in results:
            print(f"Average:            {results['avg_latency_ms']:.2f}ms")
        if "median_latency_ms" in results:
            print(f"Median:             {results['median_latency_ms']:.2f}ms")
        if "p95_latency_ms" in results:
            print(f"95th percentile:    {results['p95_latency_ms']:.2f}ms")
        if "p99_latency_ms" in results:
            print(f"99th percentile:    {results['p99_latency_ms']:.2f}ms")
        if "fastest_ms" in results:
            print(f"Fastest:            {results['fastest_ms']:.2f}ms")
        if "slowest_ms" in results:
            print(f"Slowest:            {results['slowest_ms']:.2f}ms")


    def print_system_info(self):
        """Print MacBook Air M1 system information"""
        print("🖥️  SYSTEM INFO - MacBook Air M1")
        print("=" * 40)
        print(
            f"CPU Cores:          {self.system_info['cpu_count']} physical, {self.system_info['cpu_count_logical']} logical"
        )
        print(f"Total Memory:       {self.system_info['memory_total_gb']} GB")
        print(f"Available Memory:   {self.system_info['memory_available_gb']} GB")
        print(f"Platform:           {self.system_info['platform']}")
        print()


    def print_nginx_analysis(self, nginx_results: Dict[str, Any]):
        """Print Nginx configuration analysis"""
        print("🔧 NGINX CONFIGURATION ANALYSIS")
        print("=" * 40)

        if "error" in nginx_results:
            print(f"❌ {nginx_results['error']}")
            return

        if nginx_results.get("nginx_config_found"):
            optimizations = nginx_results.get("optimizations", {})
            score = nginx_results.get("score", 0)

            print(f"Configuration Score: {score:.0f}%")
            print("\\nOptimizations:")
            for check, passed in optimizations.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check.replace('_', ' ').title()}")

            if score < 80:
                print("\\n💡 Recommendations:")
                if not optimizations.get("worker_processes_2"):
                    print("  - Set worker_processes 2 (optimal for M1)")
                if not optimizations.get("worker_connections_1024"):
                    print("  - Set worker_connections 1024")
                if not optimizations.get("gzip_enabled"):
                    print("  - Enable gzip compression")
                if not optimizations.get("http2_enabled"):
                    print("  - Enable HTTP / 2 support")
        print()


    def print_performance_analysis(self, results: List[Dict[str, Any]]):
        """Analyze results against MacBook Air M1 targets"""
        targets = self.get_performance_targets()

        print("🎯 PERFORMANCE ANALYSIS - MacBook Air M1 Targets")
        print("=" * 60)

        for result in results:
            if "error" in result:
                continue

            endpoint = result.get("endpoint", "unknown")
            rps = result.get("requests_per_sec", 0)
            p95 = result.get("p95_latency_ms", result.get("avg_latency_ms", 0))

            print(f"\\n📍 {endpoint}")

            # RPS Analysis
            rps_target = targets["simple_endpoints_rps"]
            if rps >= rps_target["target"]:
                print(
                    f"  ✅ RPS: {rps:,.0f} (Excellent - above {rps_target['target']:,} target)"
                )
            elif rps >= rps_target["min"]:
                print(
                    f"  ⚠️  RPS: {rps:,.0f} (Good - above {rps_target['min']:,} minimum)"
                )
            else:
                print(f"  ❌ RPS: {rps:,.0f} (Below {rps_target['min']:,} minimum)")

            # Latency Analysis
            latency_target = targets["p95_latency_ms"]
            if p95 <= latency_target["target"]:
                print(
                    f"  ✅ Latency: {p95:.1f}ms (Excellent - under {latency_target['target']}ms target)"
                )
            elif p95 <= latency_target["max"]:
                print(
                    f"  ⚠️  Latency: {p95:.1f}ms (Acceptable - under {latency_target['max']}ms max)"
                )
            else:
                print(
                    f"  ❌ Latency: {p95:.1f}ms (Above {latency_target['max']}ms maximum)"
                )

        print(f"\\n📋 MacBook Air M1 Optimization Summary:")
        print(f"  • Target: 2k - 5k req / sec for simple endpoints")
        print(f"  • Target: <50ms p95 latency up to 200 concurrent clients")
        print(f"  • Memory: Keep under 2GB total")
        print(f"  • Nginx: 2 workers, 1024 connections each")
        print(f"  • FastAPI: 2 - 4 Uvicorn workers recommended")


async def main():
    """Run comprehensive FastAPI performance baseline"""
    print("🚀 FastAPI Performance Baseline - MacBook Air M1 (16GB)")
    print("=" * 70)

    # Initialize benchmark
    benchmark = MacBookAirM1Benchmark("http://localhost:8000")
    benchmark.print_system_info()

    # Check Nginx configuration
    nginx_results = benchmark.check_nginx_config()
    benchmark.print_nginx_analysis(nginx_results)

    # Test scenarios for MacBook Air M1
    scenarios = [
        # (endpoint, test_type, params)
        ("/api / status", "hey", {"duration": "30s", "concurrency": 50}),
            ("/api / status", "async", {"concurrent_users": 50, "duration_seconds": 20}),
            ("/places / health", "hey", {"duration": "20s", "concurrency": 25}),
            ("/", "async", {"concurrent_users": 30, "duration_seconds": 15}),
            ]

    all_results = []

    for endpoint, test_type, params in scenarios:
        print(f"\\n🎯 Testing {endpoint} with {test_type}...")

        if test_type == "hey":
            result = benchmark.run_hey_benchmark(endpoint, **params)
        elif test_type == "async":
            result = await benchmark.async_benchmark(endpoint, **params)

        benchmark.print_results(result)
        all_results.append(result)

        # Cool down between tests
        await asyncio.sleep(2)

    # Performance analysis
    benchmark.print_performance_analysis(all_results)

    print("\\n" + "=" * 70)
    print("✅ FastAPI Performance Baseline Complete!")
    print("\\n📋 Next Steps:")
    print("  1. If RPS < 2k: Scale Uvicorn workers (--workers 4)")
    print("  2. If latency > 50ms: Check database queries, add caching")
    print("  3. For production: Consider Gunicorn + Uvicorn workers")
    print("  4. Monitor CPU / memory usage with htop during tests")
    print("\\n💡 Production Optimization Checklist:")
    print("  • Gunicorn with multiple Uvicorn workers")
    print("  • Redis caching for frequent queries")
    print("  • Database connection pooling")
    print("  • CDN for static assets")
    print("  • Load balancer for multiple instances")

if __name__ == "__main__":
    asyncio.run(main())