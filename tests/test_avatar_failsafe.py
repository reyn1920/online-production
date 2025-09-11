#!/usr/bin/env python3
"""
Avatar Engine Failsafe Test Script

This script tests the bulletproof failsafe mechanism for avatar generation,
demonstrating automatic failover from Linly-Talker to Talking Heads.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add the backend directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

from api_orchestrator_enhanced import EnhancedAPIOrchestrator, OrchestrationRequest


class AvatarFailsafeTest:
    def __init__(self):
        self.orchestrator = EnhancedAPIOrchestrator()
        self.test_results = []

    async def test_normal_operation(self):
        """Test normal avatar generation with primary engine"""
        print("\n🧪 Test 1: Normal Operation (Primary Engine)")
        print("=" * 50)

        result = await self.orchestrator.request_avatar_generation(
            text="Hello! This is a test of the primary avatar engine.",
            voice_settings={"voice_type": "professional", "speed": 1.0},
            video_settings={"resolution": "1080p", "fps": 30},
        )

        self.test_results.append(
            {
                "test": "normal_operation",
                "success": result.status.value == "success",
                "api_used": result.api_used.api_name if result.api_used else None,
                "attempts": result.total_attempts,
                "response_time": result.total_time_ms / 1000.0,
            }
        )

        if result.status.value == "success":
            print(f"✅ SUCCESS: Avatar generated using {result.api_used.api_name}")
            print(f"   Response Time: {result.total_time_ms / 1000.0:.2f}s")
            print(f"   Attempts Made: {result.total_attempts}")

            if result.response_data and "_orchestration" in result.response_data:
                orch_info = result.response_data["_orchestration"]
                print(f"   Engine Priority: {orch_info.get('priority', 'unknown')}")
                print(
                    f"   Failover Triggered: {orch_info.get('failover_triggered', False)}"
                )
        else:
            print(f"❌ FAILED: {result.error_message}")

        return result.status.value == "success"

    async def test_primary_engine_failure(self):
        """Test failover when primary engine fails"""
        print("\n🧪 Test 2: Primary Engine Failure Simulation")
        print("=" * 50)

        # Temporarily disable the primary engine by updating its status
        import sqlite3

        with sqlite3.connect(self.orchestrator.db_path) as conn:
            # Set Linly-Talker to inactive to simulate failure
            conn.execute(
                """
                UPDATE api_registry 
                SET status = 'inactive' 
                WHERE api_name = 'linly-talker-enhanced'
            """
            )

        result = await self.orchestrator.request_avatar_generation(
            text="This should use the fallback engine due to primary failure.",
            voice_settings={"voice_type": "default", "speed": 1.1},
        )

        # Restore primary engine status
        with sqlite3.connect(self.orchestrator.db_path) as conn:
            conn.execute(
                """
                UPDATE api_registry 
                SET status = 'active' 
                WHERE api_name = 'linly-talker-enhanced'
            """
            )

        self.test_results.append(
            {
                "test": "primary_failure",
                "success": result.status.value == "success",
                "api_used": result.api_used.api_name if result.api_used else None,
                "attempts": result.total_attempts,
                "response_time": result.total_time_ms / 1000.0,
            }
        )

        if result.status.value == "success":
            print(
                f"✅ FAILOVER SUCCESS: Used fallback engine {result.api_used.api_name}"
            )
            print(f"   Response Time: {result.total_time_ms / 1000.0:.2f}s")
            print(f"   Attempts Made: {result.total_attempts}")

            if result.response_data and "_orchestration" in result.response_data:
                orch_info = result.response_data["_orchestration"]
                print(
                    f"   Failover Triggered: {orch_info.get('failover_triggered', False)}"
                )
                if result.api_used.api_name == "talking-heads-fallback":
                    print("   ✅ Correctly used secondary engine")
                else:
                    print(
                        f"   ⚠️  Expected talking-heads-fallback, got {result.api_used.api_name}"
                    )
        else:
            print(f"❌ FAILOVER FAILED: {result.error_message}")

        return (
            result.status.value == "success"
            and result.api_used
            and result.api_used.api_name == "talking-heads-fallback"
        )

    async def test_capability_query(self):
        """Test capability-based API discovery"""
        print("\n🧪 Test 3: Capability-Based API Discovery")
        print("=" * 50)

        # Get all avatar generation APIs
        apis = self.orchestrator.get_apis_by_capability("avatar-generation")

        print(f"Found {len(apis)} avatar generation engines:")
        for i, api in enumerate(apis, 1):
            print(
                f"   {i}. {api.api_name} (Priority: {api.priority}, Status: {api.status})"
            )

        # Verify we have both engines registered
        api_names = [api.api_name for api in apis]
        has_primary = "linly-talker-enhanced" in api_names
        has_fallback = "talking-heads-fallback" in api_names

        self.test_results.append(
            {
                "test": "capability_query",
                "success": has_primary and has_fallback,
                "engines_found": len(apis),
                "has_primary": has_primary,
                "has_fallback": has_fallback,
            }
        )

        if has_primary and has_fallback:
            print("✅ Both engines properly registered")
            return True
        else:
            print("❌ Missing engines in registry")
            return False

    async def test_priority_ordering(self):
        """Test that engines are selected in correct priority order"""
        print("\n🧪 Test 4: Priority Ordering Verification")
        print("=" * 50)

        # Get available APIs for avatar generation
        available_apis = await self.orchestrator.get_available_apis("avatar-generation")

        if not available_apis:
            print("❌ No available APIs found")
            return False

        print("API Priority Order:")
        for i, api in enumerate(available_apis, 1):
            print(f"   {i}. {api.api_name} (Priority: {api.priority})")

        # Verify Linly-Talker has higher priority (lower number)
        primary_priority = None
        fallback_priority = None

        for api in available_apis:
            if api.api_name == "linly-talker-enhanced":
                primary_priority = api.priority
            elif api.api_name == "talking-heads-fallback":
                fallback_priority = api.priority

        priority_correct = (
            primary_priority is not None
            and fallback_priority is not None
            and primary_priority < fallback_priority
        )

        self.test_results.append(
            {
                "test": "priority_ordering",
                "success": priority_correct,
                "primary_priority": primary_priority,
                "fallback_priority": fallback_priority,
            }
        )

        if priority_correct:
            print(
                f"✅ Priority ordering correct: Primary({primary_priority}) < Fallback({fallback_priority})"
            )
            return True
        else:
            print(
                f"❌ Priority ordering incorrect: Primary({primary_priority}) vs Fallback({fallback_priority})"
            )
            return False

    def print_test_summary(self):
        """Print comprehensive test results"""
        print("\n" + "=" * 60)
        print("🎯 AVATAR FAILSAFE TEST SUMMARY")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])

        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"   {status} - {result['test']}")

        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED - Bulletproof failsafe is working correctly!")
            print("\n✅ The avatar generation system will:")
            print("   • Automatically use Linly-Talker as the primary engine")
            print("   • Seamlessly failover to Talking Heads if primary fails")
            print("   • Maintain service availability even during engine failures")
            print("   • Provide detailed orchestration metadata for monitoring")
        else:
            print("\n⚠️  Some tests failed - please review the failsafe implementation")


async def main():
    """Run the complete avatar failsafe test suite"""
    print("🚀 Starting Avatar Engine Failsafe Test Suite")
    print("This will test the bulletproof failsafe mechanism for avatar generation.")

    tester = AvatarFailsafeTest()

    # Run all tests
    test_functions = [
        tester.test_capability_query,
        tester.test_priority_ordering,
        tester.test_normal_operation,
        tester.test_primary_engine_failure,
    ]

    for test_func in test_functions:
        try:
            await test_func()
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            tester.test_results.append(
                {"test": test_func.__name__, "success": False, "error": str(e)}
            )

    # Print final summary
    tester.print_test_summary()


if __name__ == "__main__":
    asyncio.run(main())
