#!/usr / bin / env python3
"""
API Orchestrator Usage Example

This file demonstrates how to use the APIOrchestrator for intelligent API management
with automatic failover, health monitoring, and request routing.
"""

import asyncio
import json
from typing import Any, Dict

from api_orchestrator import APIOrchestrator, APIRequest, FailoverStrategy


class ExampleService:
    """Example service showing how to integrate API orchestrator"""


    def __init__(self, db_path: str = "right_perspective.db"):
        self.api_orchestrator = APIOrchestrator(
            db_path = db_path,
                health_check_interval = 300,  # 5 minutes
            failover_strategy = FailoverStrategy.PRIORITY_BASED,
                )


    async def initialize(self):
        """Initialize the service and start health monitoring"""
        await self.api_orchestrator.start_health_monitoring()
        print("✅ API Orchestrator initialized and health monitoring started")


    async def make_llm_request(
        self, prompt: str, model: str = "gpt - 3.5 - turbo"
    ) -> Dict[str, Any]:
        """Example: Make a request to an LLM API with automatic failover"""
        request = APIRequest(
            service_type="llm",
                endpoint="/chat / completions",
                method="POST",
                data={
                "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150,
                    },
                headers={"Content - Type": "application / json"},
                timeout = 30,
                )

        try:
            response = await self.api_orchestrator.make_request(request)
            if response.success:
                print(f"✅ LLM request successful via {response.endpoint_used}")
                return response.data
            else:
                print(f"❌ LLM request failed: {response.error}")
                return {"error": response.error}
        except Exception as e:
            print(f"❌ LLM request exception: {e}")
            return {"error": str(e)}


    async def make_search_request(self, query: str) -> Dict[str, Any]:
        """Example: Make a search API request with failover"""
        request = APIRequest(
            service_type="search",
                endpoint="/search",
                method="GET",
                params={"q": query, "limit": 10},
                timeout = 15,
                )

        try:
            response = await self.api_orchestrator.make_request(request)
            if response.success:
                print(f"✅ Search request successful via {response.endpoint_used}")
                return response.data
            else:
                print(f"❌ Search request failed: {response.error}")
                return {"error": response.error}
        except Exception as e:
            print(f"❌ Search request exception: {e}")
            return {"error": str(e)}


    async def get_api_health_status(self) -> Dict[str, Any]:
        """Get current health status of all APIs"""
        endpoints = await self.api_orchestrator.get_healthy_endpoints()

        status = {
            "total_endpoints": len(self.api_orchestrator.endpoints),
                "healthy_endpoints": len(endpoints),
                "endpoints_by_service": {},
                }

        # Group by service type
        for endpoint in self.api_orchestrator.endpoints.values():
            service = endpoint.service_type
            if service not in status["endpoints_by_service"]:
                status["endpoints_by_service"][service] = {
                    "total": 0,
                        "healthy": 0,
                        "endpoints": [],
                        }

            status["endpoints_by_service"][service]["total"] += 1

            if endpoint.api_name in [e.api_name for e in endpoints]:
                status["endpoints_by_service"][service]["healthy"] += 1

            status["endpoints_by_service"][service]["endpoints"].append(
                {
                    "name": endpoint.api_name,
                        "url": endpoint.base_url,
                        "status": endpoint.status.value,
                        "priority": endpoint.failover_priority,
                        }
            )

        return status


    async def shutdown(self):
        """Shutdown the service gracefully"""
        await self.api_orchestrator.stop_health_monitoring()
        print("✅ API Orchestrator shutdown complete")


async def main():
    """Example usage of the API orchestrator"""
    print("🚀 API Orchestrator Example")
    print("=" * 50)

    # Initialize service
    service = ExampleService()
    await service.initialize()

    try:
        # Example 1: Check API health status
        print("\n📊 Checking API Health Status:")
        health_status = await service.get_api_health_status()
        print(json.dumps(health_status, indent = 2))

        # Example 2: Make LLM request with failover
        print("\n🤖 Making LLM Request:")
        llm_response = await service.make_llm_request(
            "Explain the benefits of API failover in one sentence."
        )
        print(f"Response: {llm_response}")

        # Example 3: Make search request with failover
        print("\n🔍 Making Search Request:")
        search_response = await service.make_search_request(
            "API orchestration best practices"
        )
        print(f"Search results: {search_response}")

        # Example 4: Simulate some time passing for health checks
        print("\n⏱️  Waiting for health check cycle...")
        await asyncio.sleep(10)

        # Check status again
        print("\n📊 Updated API Health Status:")
        updated_status = await service.get_api_health_status()
        print(json.dumps(updated_status, indent = 2))

    except KeyboardInterrupt:
        print("\n🛑 Received interrupt signal")
    except Exception as e:
        print(f"\n❌ Error in example: {e}")
    finally:
        # Cleanup
        await service.shutdown()
        print("\n✅ Example completed")

if __name__ == "__main__":
    asyncio.run(main())
