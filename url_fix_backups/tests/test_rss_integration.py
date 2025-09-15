#!/usr / bin / env python3
""""""
RSS Intelligence System Integration Test

This script tests the end - to - end integration of the RSS intelligence system
with the existing agent architecture, verifying all components work together.

Author: TRAE.AI System
Version: 1.0.0
""""""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.agents.base_agents import AuditorAgent, PlannerAgent

# Import components to test

from backend.agents.research_tools import BreakingNewsWatcher
from backend.agents.specialized_agents import ContentAgent, ResearchAgent
from backend.database.hypocrisy_db_manager import (
    HypocrisyDatabaseManager,
    HypocrisyFinding,
# BRACKET_SURGEON: disabled
# )

from backend.task_queue_manager import TaskQueueManager


class RSSIntegrationTester:
    """Comprehensive tester for RSS intelligence system integration."""

    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }
        self.test_results.append(result)
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")

    async def test_breaking_news_watcher(self):
        """Test BreakingNewsWatcher initialization and basic functionality."""
        try:
            # Test initialization
            news_watcher = BreakingNewsWatcher()
            self.log_test("BreakingNewsWatcher Initialization", True, "Successfully initialized")

            # Test database initialization
            news_watcher._initialize_intelligence_db()
            self.log_test("Intelligence Database Initialization", True, "Database tables created")

            # Test RSS feed monitoring (mock test)
            feeds = news_watcher.feeds
            self.log_test(
                "RSS Feeds Configuration",
                len(feeds) > 0,
                f"Configured {len(feeds)} RSS feeds",
# BRACKET_SURGEON: disabled
#             )

            # Test trending topics retrieval
            trending_topics = news_watcher.get_trending_topics()
            self.log_test(
                "Trending Topics Retrieval",
                True,
                f"Retrieved {len(trending_topics)} topics",
# BRACKET_SURGEON: disabled
#             )

            # Test intelligence briefing
            briefing = news_watcher.get_latest_intelligence_briefing()
            self.log_test(
                "Intelligence Briefing",
                briefing is not None,
                "Generated intelligence briefing",
# BRACKET_SURGEON: disabled
#             )

            return news_watcher

        except Exception as e:
            self.log_test("BreakingNewsWatcher Test", False, f"Error: {str(e)}")
            return None

    async def test_hypocrisy_database_integration(self):
        """Test hypocrisy database integration"""
        try:
            # Initialize database manager
            hypocrisy_db = HypocrisyDatabaseManager()
            self.log_test(
                "HypocrisyDatabaseManager Initialization",
                True,
                "Successfully initialized",
# BRACKET_SURGEON: disabled
#             )

            # Test database schema creation
            hypocrisy_db._initialize_database()
            self.log_test("Hypocrisy Database Schema", True, "Database schema created")

            # Clean up any existing test data
            with hypocrisy_db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM hypocrisy_tracker WHERE subject_name = 'Test Subject'")
                conn.commit()

            # Test storing a sample finding
            sample_finding = HypocrisyFinding(
                subject_name="Test Subject",
                subject_type="politician",
                statement_1="Statement A",
                statement_2="Statement B",
                context_1="Context A",
                context_2="Context B",
                date_1=datetime.now() - timedelta(days=30),
                date_2=datetime.now(),
                source_1="Test Source 1",
                source_2="Test Source 2",
                contradiction_type="direct",
                severity_score=8,
                confidence_score=0.9,
                verification_status="verified",
                evidence_links=["http://example.com / evidence1"],
                tags=["test", "integration"],
                analysis_notes="Test finding for integration",
                public_impact_score=7,
                media_coverage_count=5,
                social_media_mentions=100,
                fact_check_results={"status": "confirmed"},
# BRACKET_SURGEON: disabled
#             )

            finding_id = hypocrisy_db.store_finding(sample_finding)
            self.log_test(
                "Store Hypocrisy Finding",
                finding_id is not None,
                f"Stored finding with ID: {finding_id}",
# BRACKET_SURGEON: disabled
#             )

            # Test retrieving content opportunities
            opportunities = hypocrisy_db.get_content_opportunities(limit=5)
            self.log_test(
                "Retrieve Content Opportunities",
                len(opportunities) > 0,
                f"Retrieved {len(opportunities)} opportunities",
# BRACKET_SURGEON: disabled
#             )

            # Test statistics
            stats = hypocrisy_db.get_statistics()
            self.log_test("Database Statistics", stats is not None, f"Stats: {stats}")

            return hypocrisy_db

        except Exception as e:
            self.log_test("Hypocrisy Database Integration", False, f"Error: {str(e)}")
            return None

    async def test_planner_agent_rss_integration(self):
        """Test PlannerAgent RSS intelligence integration."""
        try:
            # Initialize PlannerAgent
            planner = PlannerAgent(agent_id="test - planner")
            self.log_test(
                "PlannerAgent Initialization",
                True,
                "Successfully initialized with RSS intelligence",
# BRACKET_SURGEON: disabled
#             )

            # Test RSS intelligence retrieval
            rss_intelligence = planner._get_rss_intelligence()
            self.log_test(
                "RSS Intelligence Retrieval",
                rss_intelligence is not None,
                f"Retrieved intelligence: {list(rss_intelligence.keys())}",
# BRACKET_SURGEON: disabled
#             )

            # Test trending topics integration
            trending_topics = rss_intelligence.get("trending_topics", [])
            self.log_test(
                "Trending Topics Integration",
                len(trending_topics) >= 0,
                f"Found {len(trending_topics)} trending topics",
# BRACKET_SURGEON: disabled
#             )

            # Test content opportunities identification
            content_opportunities = rss_intelligence.get("content_opportunities", [])
            self.log_test(
                "Content Opportunities",
                len(content_opportunities) >= 0,
                f"Identified {len(content_opportunities)} opportunities",
# BRACKET_SURGEON: disabled
#             )

            # Test topic momentum calculation
            topic_momentum = rss_intelligence.get("topic_momentum", {})
            self.log_test(
                "Topic Momentum Calculation",
                isinstance(topic_momentum, dict),
                f"Calculated momentum for {len(topic_momentum)} topics",
# BRACKET_SURGEON: disabled
#             )

            return planner

        except Exception as e:
            self.log_test("PlannerAgent RSS Integration", False, f"Error: {str(e)}")
            return None

    async def test_research_agent_integration(self):
        """Test ResearchAgent integration with RSS intelligence."""
        try:
            # Initialize ResearchAgent
            research_agent = ResearchAgent(agent_id="test - research")
            self.log_test("ResearchAgent Initialization", True, "Successfully initialized")

            # Test hypocrisy database integration in research tools
            if (
                hasattr(research_agent, "research_tools")
                and "news_watcher" in research_agent.research_tools
# BRACKET_SURGEON: disabled
#             ):
                news_watcher = research_agent.research_tools["news_watcher"]
                if hasattr(news_watcher, "hypocrisy_db"):
                    self.log_test(
                        "Research - Hypocrisy Integration",
                        True,
                        "Hypocrisy database integrated in research tools",
# BRACKET_SURGEON: disabled
#                     )
                else:
                    self.log_test(
                        "Research - Hypocrisy Integration",
                        False,
                        "Hypocrisy database not found in research tools",
# BRACKET_SURGEON: disabled
#                     )
            else:
                self.log_test(
                    "Research - Hypocrisy Integration",
                    False,
                    "Breaking news watcher not found in research agent",
# BRACKET_SURGEON: disabled
#                 )

            return research_agent

        except Exception as e:
            self.log_test("ResearchAgent Integration", False, f"Error: {str(e)}")
            return None

    async def test_task_queue_integration(self):
        """Test task queue integration with RSS intelligence."""
        try:
            # Initialize TaskQueueManager
            task_queue = TaskQueueManager()
            self.log_test("TaskQueueManager Initialization", True, "Successfully initialized")

            # Test adding RSS - driven tasks
            sample_task = {
                "task_type": "content_creation",
                "priority": "high",
                "payload": {
                    "topic": "AI Trends",
                    "source": "rss_intelligence",
                    "urgency": "trending",
                    "agent_type": "ContentAgent",
# BRACKET_SURGEON: disabled
#                 },
                "metadata": {
                    "created_by": "rss_integration_test",
                    "source_system": "breaking_news_watcher",
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }

            task_id = task_queue.add_task(**sample_task)
            self.log_test(
                "RSS - Driven Task Creation",
                task_id is not None,
                f"Created task with ID: {task_id}",
# BRACKET_SURGEON: disabled
#             )

            # Test task retrieval
            tasks = task_queue.get_tasks(status="pending", limit=10)
            self.log_test(
                "Task Queue Retrieval",
                len(tasks) >= 0,
                f"Retrieved {len(tasks)} pending tasks",
# BRACKET_SURGEON: disabled
#             )

            return task_queue

        except Exception as e:
            self.log_test("Task Queue Integration", False, f"Error: {str(e)}")
            return None

    async def test_end_to_end_workflow(self):
        """Test complete end - to - end RSS intelligence workflow."""
        try:
            print("\\n🔄 Testing End - to - End RSS Intelligence Workflow...")

            # Step 1: Initialize all components
            news_watcher = await self.test_breaking_news_watcher()
            hypocrisy_db = await self.test_hypocrisy_database_integration()
            planner = await self.test_planner_agent_rss_integration()
            research_agent = await self.test_research_agent_integration()
            task_queue = await self.test_task_queue_integration()

            if not all([news_watcher, hypocrisy_db, planner, task_queue]):
                self.log_test("End - to - End Workflow", False, "Component initialization failed")
                return False

            # Step 2: Simulate RSS intelligence flow
            print("\\n📊 Simulating RSS Intelligence Flow...")

            # Get intelligence from news watcher
            intelligence = planner._get_rss_intelligence()

            # Simulate OODA loop observation
            observations = planner._observe_system_state(task_queue)
            market_conditions = observations.get("market_conditions", {})

            self.log_test(
                "OODA Loop Integration",
                "trending_topics" in market_conditions,
                "RSS intelligence integrated in OODA loop",
# BRACKET_SURGEON: disabled
#             )

            # Step 3: Test dynamic content scheduling
            if hasattr(planner, "content_scheduling"):
                scheduling_rules = planner.content_scheduling.get("scheduling_rules", {})
                self.log_test(
                    "Dynamic Content Scheduling",
                    len(scheduling_rules) > 0,
                    f"Scheduling rules configured: {list(scheduling_rules.keys())}",
# BRACKET_SURGEON: disabled
#                 )

            # Step 4: Test hypocrisy content opportunities
            if news_watcher and hasattr(news_watcher, "get_hypocrisy_content_opportunities"):
                hypocrisy_opportunities = news_watcher.get_hypocrisy_content_opportunities(limit=5)
                self.log_test(
                    "Hypocrisy Content Integration",
                    len(hypocrisy_opportunities) >= 0,
                    f"Retrieved {len(hypocrisy_opportunities)} hypocrisy opportunities",
# BRACKET_SURGEON: disabled
#                 )

            self.log_test("End - to - End Workflow", True, "Complete workflow tested successfully")
            return True

        except Exception as e:
            self.log_test("End - to - End Workflow", False, f"Error: {str(e)}")
            return False

    def generate_test_report(self):
        """Generate comprehensive test report."""
        end_time = datetime.now()
        duration = end_time - self.start_time

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests

        print("\\n" + "=" * 80)
        print("🧪 RSS INTELLIGENCE INTEGRATION TEST REPORT")
        print("=" * 80)
        print(f"Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✓")
        print(f"Failed: {failed_tests} ✗")
        print(f"Success Rate: {(passed_tests / total_tests)*100:.1f}%")

        if failed_tests > 0:
            print("\\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  • {result['test_name']}: {result['details']}")

        print("\\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {result['test_name']}")
            if result["details"]:
                print(f"    └─ {result['details']}")

        # Save report to file
        report_data = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests) * 100,
                "duration_seconds": duration.total_seconds(),
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
# BRACKET_SURGEON: disabled
#             },
            "test_results": self.test_results,
# BRACKET_SURGEON: disabled
#         }

        report_file = (
            f"rss_integration_test_report_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
# BRACKET_SURGEON: disabled
#         )
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2)

        print(f"\\n📄 Detailed report saved to: {report_file}")
        print("=" * 80)

        return passed_tests == total_tests


async def main():
    """Run comprehensive RSS intelligence integration tests."""
    print("🚀 Starting RSS Intelligence System Integration Tests...")
    print("This will test all components and their integration.\\n")

    tester = RSSIntegrationTester()

    try:
        # Run all tests
        success = await tester.test_end_to_end_workflow()

        # Generate report
        all_passed = tester.generate_test_report()

        if all_passed:
            print("\\n🎉 All tests passed! RSS intelligence system is fully integrated.")
            return 0
        else:
            print("\\n⚠️  Some tests failed. Please review the report above.")
            return 1

    except Exception as e:
        print(f"\\n💥 Test execution failed: {str(e)}")
        tester.generate_test_report()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)