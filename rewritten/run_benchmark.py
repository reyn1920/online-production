#!/usr/bin/env python3
"""
MacBook Air M1 Performance Benchmark Script
Based on the Docker System Tuning guide from paste_content.txt lines 1-345
"""

import asyncio
import statistics
import subprocess
import sys
import time
from typing import Any, Dict, List

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class AsyncBenchmark:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.results = []

    async def single_request(self, client: httpx.AsyncClient, endpoint: str) -> Dict[str, Any]:
        """Make a single HTTP request and measure timing"""
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

    async def run_concurrent_test(
        self, endpoint: str, concurrent_users: int = 50, duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """Run concurrent requests for specified duration"""
        
        print("🚀 Starting benchmark:")
        print(f"   Endpoint: {self.base_url}{endpoint}")
        print(f"   Concurrent users: {concurrent_users}")
        print(f"   Duration: {duration_seconds}s")
        print("   Target: MacBook Air M1")
        print()
        
        # Configure HTTP client for high concurrency
        limits = httpx.Limits(max_keepalive_connections=100, max_connections=200)
        timeout = httpx.Timeout(10.0)
        
        async with httpx.AsyncClient(limits=limits, timeout=timeout, verify=False) as client:
            start_time = time.perf_counter()
            end_time = start_time + duration_seconds
            
            tasks = []
            results = []
            
            # Run concurrent requests for the specified duration
            while time.perf_counter() < end_time:
                # Maintain concurrent user count
                if len(tasks) < concurrent_users:
                    task = asyncio.create_task(self.single_request(client, endpoint))
                    tasks.append(task)
                
                # Collect completed tasks
                done_tasks = [task for task in tasks if task.done()]
                for task in done_tasks:
                    result = await task
                    results.append(result)
                    tasks.remove(task)
                
                # Small delay to prevent CPU spinning
                await asyncio.sleep(0.1)
            
            # Wait for remaining tasks
            if tasks:
                remaining_results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in remaining_results:
                    if isinstance(result, dict):
                        results.append(result)
            
            actual_duration = time.perf_counter() - start_time
            
            return self.analyze_results(results, actual_duration)

    def analyze_results(self, results: List[Dict], duration: float) -> Dict[str, Any]:
        """Analyze benchmark results and return stats"""
        
        successful_requests = [r for r in results if r.get("success", False)]
        failed_requests = [r for r in results if not r.get("success", False)]
        
        if not successful_requests:
            return {
                "error": "No successful requests",
                "total_requests": len(results),
                "failed_requests": len(failed_requests),
            }
        
        durations = [r["duration"] for r in successful_requests]
        sizes = [r["size"] for r in successful_requests]
        
        stats = {
            "duration_seconds": round(duration, 2),
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "requests_per_second": round(len(successful_requests) / duration, 2),
            "success_rate": round(len(successful_requests) / len(results) * 100, 2),
            # Latency statistics in milliseconds
            "latency_ms": {
                "min": round(min(durations) * 1000, 2),
                "max": round(max(durations) * 1000, 2),
                "mean": round(statistics.mean(durations) * 1000, 2),
                "median": round(statistics.median(durations) * 1000, 2),
                "p95": (
                    round(statistics.quantiles(durations, n=20)[18] * 1000, 2)
                    if len(durations) > 20
                    else 0
                ),
                "p99": (
                    round(statistics.quantiles(durations, n=100)[98] * 1000, 2)
                    if len(durations) > 100
                    else 0
                ),
            },
            # Data transfer stats
            "total_bytes": sum(sizes),
            "avg_response_size": round(statistics.mean(sizes), 2) if sizes else 0,
        }
        
        return stats

    def print_results(self, stats: Dict[str, Any]):
        """Pretty print benchmark results"""
        
        if "error" in stats:
            print(f"❌ Benchmark failed: {stats['error']}")
            return
        
        print("📊 BENCHMARK RESULTS")
        print("=" * 50)
        print(f"Duration:           {stats['duration_seconds']}s")
        print(f"Total requests:     {stats['total_requests']:,}")
        print(f"Successful:         {stats['successful_requests']:,}")
        print(f"Failed:             {stats['failed_requests']:,}")
        print(f"Success rate:       {stats['success_rate']}%")
        print(f"Requests/sec:       {stats['requests_per_second']:,}")
        print()
        
        print("⏱️  LATENCY (milliseconds)")
        print("-" * 30)
        lat = stats["latency_ms"]
        print(f"Min:                {lat['min']}ms")
        print(f"Mean:               {lat['mean']}ms")
        print(f"Median:             {lat['median']}ms")
        print(f"95th percentile:    {lat['p95']}ms")
        print(f"99th percentile:    {lat['p99']}ms")
        print(f"Max:                {lat['max']}ms")
        print()
        
        print("📡 DATA TRANSFER")
        print("-" * 20)
        print(f"Total bytes:        {stats['total_bytes']:,}")
        print(f"Avg response size:  {stats['avg_response_size']:,} bytes")
        print()


async def main():
    """Run multiple benchmark scenarios for MacBook Air M1"""
    
    # Test against local nginx reverse proxy
    base_url = "http://localhost"  # Using nginx reverse proxy
    
    benchmark = AsyncBenchmark(base_url)
    
    scenarios = [
        # (endpoint, concurrent_users, duration_seconds, description)
        ("/api/status", 25, 20, "FastAPI Health Check via Nginx (light)"),
        ("/paste/", 20, 15, "Flask Paste App via Nginx (medium)"),
        ("/", 30, 25, "Root endpoint via Nginx (static)"),
    ]
    
    print("🔥 MacBook Air M1 Performance Benchmark")
    print("🐳 Testing Docker + Nginx + FastAPI + Flask Stack")
    print("=" * 60)
    print()
    
    for endpoint, users, duration, description in scenarios:
        print(f"🎯 {description}")
        stats = await benchmark.run_concurrent_test(endpoint, users, duration)
        benchmark.print_results(stats)
        print("\n" + "=" * 60 + "\n")
        
        # Brief pause between tests
        await asyncio.sleep(2)
    
    print("✅ All benchmarks complete!")
    print("\n📋 MacBook Air M1 Tuning Summary:")
    print("- Nginx: 2 workers, 1024 connections each")
    print("- FastAPI: 2-4 workers recommended")
    print("- Expected: 2-4k concurrent connections")
    print("- Memory: <8GB total for all containers")


if __name__ == "__main__":
    asyncio.run(main())
