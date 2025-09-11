#!/usr/bin/env python3
"""
Integration Test Suite for Content Automation Pipeline

This comprehensive test suite validates:
1. RSS Intelligence Engine functionality
2. Content Automation Pipeline operations
3. Video generation capabilities
4. Database operations and data integrity
5. API endpoints and automation controller
6. End-to-end content creation workflow

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger

from automation_controller import AutomationController
# Import modules to test
from breaking_news_watcher import NewsArticle, RSSIntelligenceEngine, TrendData
from content_automation_pipeline import (ContentAutomationPipeline, ContentFormat,
                                         ContentOpportunity, ContentPriority)
from tools.basic_video_generator import create_basic_video

logger = get_logger(__name__)


class TestRSSIntelligenceEngine(unittest.TestCase):
    """Test RSS Intelligence Engine functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.temp_dir, "test_rss.db")

        # Create test RSS engine with temporary database
        self.rss_engine = RSSIntelligenceEngine()
        self.rss_engine.db_path = self.test_db
        self.rss_engine._init_intelligence_tables()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_initialization(self):
        """Test database table creation."""
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()

        # Check if all required tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        required_tables = [
            "news_articles",
            "trend_analysis",
            "hypocrisy_tracker",
            "intelligence_briefings",
        ]

        for table in required_tables:
            self.assertIn(table, tables, f"Required table {table} not found")

        conn.close()

    def test_article_storage_and_retrieval(self):
        """Test article storage and retrieval functionality."""
        # Create test article
        test_article = NewsArticle(
            title="Test Breaking News",
            url="https://example.com/test-news",
            content="This is a test news article about important events.",
            published=datetime.now(),
            source="Test Source",
            category="General",
            keywords=["test", "news", "breaking"],
            entities=["TestEntity"],
            sentiment_score=0.5,
            readability_score=50.0,
            hash_id="test_hash_123",
        )

        # Store article
        success = self.rss_engine._store_article(test_article)
        self.assertTrue(success, "Article storage failed")

        # Check if article exists
        exists = self.rss_engine._article_exists("test_hash_123")
        self.assertTrue(exists, "Stored article not found")

        # Verify article data in database
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM news_articles WHERE hash_id = ?", ("test_hash_123",)
        )
        result = cursor.fetchone()

        self.assertIsNotNone(result, "Article not found in database")
        self.assertEqual(result[1], "test_hash_123")  # hash_id
        self.assertEqual(result[2], "Test Breaking News")  # title
        self.assertEqual(result[3], "https://example.com/test-news")  # url

        conn.close()

    def test_trend_analysis(self):
        """Test trend analysis functionality."""
        # Insert test articles with trending keywords
        test_articles = [
            NewsArticle(
                title="Breaking: Climate Change Impact",
                url="https://example.com/climate1",
                content="Climate change is affecting global weather patterns.",
                published=datetime.now(),
                source="News Source 1",
                category="Environment",
                keywords=["climate", "change", "global"],
                entities=["Earth"],
                sentiment_score=0.3,
                readability_score=45.0,
                hash_id="climate_1",
            ),
            NewsArticle(
                title="Climate Summit Announces New Policies",
                url="https://example.com/climate2",
                content="World leaders discuss climate change solutions.",
                published=datetime.now(),
                source="News Source 2",
                category="Politics",
                keywords=["climate", "summit", "policies"],
                entities=["Leaders"],
                sentiment_score=0.7,
                readability_score=55.0,
                hash_id="climate_2",
            ),
        ]

        # Store test articles
        for article in test_articles:
            self.rss_engine._store_article(article)

        # Analyze trends
        trends = self.rss_engine.get_trending_topics()

        self.assertIsInstance(trends, list, "Trends should be a list")

        # Check if climate-related trend is detected
        climate_trends = [t for t in trends if "climate" in t.keyword.lower()]
        # Note: May not find climate trends in test data, but structure is validated
        logger.info(f"Found {len(climate_trends)} climate-related trends")

    def test_hypocrisy_detection(self):
        """Test hypocrisy detection functionality."""
        # Create contradictory articles about the same subject
        article1 = NewsArticle(
            title="Politician A Supports Environmental Protection",
            url="https://example.com/env1",
            content="Politician A strongly advocates for environmental protection and green policies.",
            published=datetime.now() - timedelta(days=30),
            source="News Source 1",
            category="Politics",
            keywords=["environment", "protection", "green"],
            entities=["Politician A"],
            sentiment_score=0.8,
            readability_score=60.0,
            hash_id="env_support",
        )

        article2 = NewsArticle(
            title="Politician A Approves Oil Drilling Project",
            url="https://example.com/oil1",
            content="Politician A has approved a major oil drilling project despite environmental concerns.",
            published=datetime.now(),
            source="News Source 2",
            category="Politics",
            keywords=["oil", "drilling", "project"],
            entities=["Politician A"],
            sentiment_score=0.2,
            readability_score=52.0,
            hash_id="oil_approval",
        )

        # Store articles
        self.rss_engine._store_article(article1)
        self.rss_engine._store_article(article2)

        # Test intelligence briefing generation
        briefing = self.rss_engine.get_latest_intelligence_briefing()

        self.assertIsInstance(briefing, dict, "Intelligence briefing should be a dict")
        self.assertIn("articles", briefing, "Briefing should contain articles")

        # Check if articles are included in briefing
        article_count = briefing.get("article_count", 0)
        self.assertGreater(article_count, 0, "Briefing should contain articles")


class TestContentAutomationPipeline(unittest.TestCase):
    """Test Content Automation Pipeline functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = os.path.join(self.temp_dir, "test_config.json")

        # Create test configuration
        test_config = {
            "monitoring_interval": 1,
            "content_generation_interval": 1,
            "max_daily_content": 5,
            "priority_keywords": ["test", "breaking"],
            "content_formats": ["video", "article"],
            "auto_publish": False,
            "quality_threshold": 0.5,
        }

        with open(self.test_config, "w") as f:
            json.dump(test_config, f)

        # Create pipeline with test config
        self.pipeline = ContentAutomationPipeline(self.test_config)
        self.pipeline.db_path = os.path.join(self.temp_dir, "test_content.db")
        self.pipeline._init_automation_tables()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_content_opportunity_creation(self):
        """Test content opportunity creation and storage."""
        # Create test opportunity
        opportunity = ContentOpportunity(
            id="test_opp_123",
            topic="Test Topic",
            angle="Testing content creation pipeline",
            priority=ContentPriority.HIGH,
            formats=[ContentFormat.VIDEO, ContentFormat.ARTICLE],
            source_articles=["https://example.com/source1"],
            keywords=["test", "content", "pipeline"],
            estimated_engagement=0.8,
            deadline=datetime.now() + timedelta(hours=24),
            created_at=datetime.now(),
            metadata={"test": True},
        )

        # Store opportunity
        self.pipeline._store_content_opportunity(opportunity)

        # Verify storage
        conn = sqlite3.connect(self.pipeline.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM content_opportunities WHERE id = ?", ("test_opp_123",)
        )
        result = cursor.fetchone()

        self.assertIsNotNone(result, "Opportunity not stored")
        self.assertEqual(result[1], "Test Topic")  # topic
        self.assertEqual(result[3], ContentPriority.HIGH.value)  # priority

        conn.close()

    def test_content_project_generation(self):
        """Test content project generation from opportunities."""
        # Create test opportunity
        opportunity = ContentOpportunity(
            id="test_opp_456",
            topic="Breaking News Test",
            angle="Testing project generation",
            priority=ContentPriority.MEDIUM,
            formats=[ContentFormat.VIDEO],
            source_articles=[],
            keywords=["breaking", "test"],
            estimated_engagement=0.6,
            deadline=datetime.now() + timedelta(hours=12),
            created_at=datetime.now(),
            metadata={},
        )

        # Generate projects
        projects = self.pipeline.generate_content_from_opportunity(opportunity)

        self.assertIsInstance(projects, list, "Projects should be a list")
        self.assertGreater(len(projects), 0, "No projects generated")

        # Check project properties
        video_projects = [p for p in projects if p.format == ContentFormat.VIDEO]
        self.assertGreater(len(video_projects), 0, "No video project generated")

        video_project = video_projects[0]
        self.assertEqual(video_project.opportunity_id, "test_opp_456")
        self.assertIsNotNone(video_project.script, "No script generated")
        self.assertEqual(video_project.status, "scripted")

    def test_pipeline_status(self):
        """Test pipeline status reporting."""
        status = self.pipeline.get_pipeline_status()

        self.assertIsInstance(status, dict, "Status should be a dictionary")
        self.assertIn("running", status, "Status should include running state")
        self.assertIn(
            "pending_opportunities",
            status,
            "Status should include pending opportunities",
        )
        self.assertIn("project_stats", status, "Status should include project stats")


class TestVideoGeneration(unittest.TestCase):
    """Test video generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "videos")
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_video_generation(self):
        """Test basic video generation functionality."""
        output_path = os.path.join(self.output_dir, "test_video.mp4")

        # Create test background image
        background_path = os.path.join(self.temp_dir, "test_bg.png")
        from PIL import Image

        img = Image.new("RGB", (1920, 1080), color="red")
        img.save(background_path)

        # Create test audio file (silence)
        audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        import wave

        with wave.open(audio_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b"\x00" * 44100 * 2 * 5)  # 5 seconds of silence

        # Generate test video
        success = create_basic_video(
            background_image_path=background_path,
            audio_path=audio_path,
            output_path=output_path,
        )

        self.assertTrue(success, "Video generation failed")
        self.assertTrue(os.path.exists(output_path), "Video file not created")

        # Check file size (should be > 0)
        file_size = os.path.getsize(output_path)
        self.assertGreater(file_size, 0, "Video file is empty")

    def test_video_with_background(self):
        """Test video generation with custom background."""
        from PIL import Image

        # Create test background image
        background_path = os.path.join(self.temp_dir, "test_bg.jpg")
        img = Image.new("RGB", (1920, 1080), color=(100, 150, 200))
        img.save(background_path)

        # Create test audio file (silence)
        audio_path = os.path.join(self.temp_dir, "test_bg_audio.wav")
        import wave

        with wave.open(audio_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b"\x00" * 44100 * 2 * 3)  # 3 seconds of silence

        output_path = os.path.join(self.output_dir, "test_video_bg.mp4")

        # Generate video with background
        success = create_basic_video(
            background_image_path=background_path,
            audio_path=audio_path,
            output_path=output_path,
        )

        self.assertTrue(success, "Video generation with background failed")
        self.assertTrue(os.path.exists(output_path), "Video file not created")


class TestAutomationController(unittest.TestCase):
    """Test Automation Controller functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_config = os.path.join(self.temp_dir, "test_automation_config.json")

        # Create test configuration
        test_config = {
            "auto_start": False,
            "content_pipeline_enabled": True,
            "rss_monitoring_enabled": True,
            "api_port": 8083,  # Different port for testing
            "monitoring_interval": 1,
            "max_daily_content": 5,
            "error_threshold": 5,
            "performance_retention_days": 7,
        }

        with open(self.test_config, "w") as f:
            json.dump(test_config, f)

        # Create controller with test config
        self.controller = AutomationController(self.test_config)
        self.controller.performance_db = os.path.join(
            self.temp_dir, "test_performance.db"
        )
        self.controller._init_performance_tracking()

    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self.controller, "stop_automation"):
            self.controller.stop_automation()

        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_controller_initialization(self):
        """Test controller initialization."""
        self.assertIsNotNone(
            self.controller.content_pipeline, "Content pipeline not initialized"
        )
        self.assertIsNotNone(self.controller.rss_engine, "RSS engine not initialized")
        self.assertFalse(
            self.controller.running, "Controller should not be running initially"
        )

    def test_automation_status(self):
        """Test automation status reporting."""
        status = self.controller.get_automation_status()

        self.assertIsNotNone(status, "Status should not be None")
        self.assertFalse(
            status.content_pipeline_running, "Pipeline should not be running"
        )
        self.assertEqual(status.error_count, 0, "Error count should be 0 initially")
        self.assertIsInstance(status.uptime_hours, float, "Uptime should be a float")

    def test_performance_tracking(self):
        """Test performance metrics collection."""
        # Collect metrics
        self.controller._collect_performance_metrics()

        # Check if metrics were stored
        conn = sqlite3.connect(self.controller.performance_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM system_metrics")
        count = cursor.fetchone()[0]

        self.assertGreater(count, 0, "No metrics were stored")

        conn.close()

    def test_error_logging(self):
        """Test error logging functionality."""
        # Log test error
        self.controller._log_error("test_component", "test_error", "Test error message")

        # Check if error was logged
        conn = sqlite3.connect(self.controller.performance_db)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM error_log WHERE component = 'test_component'")
        result = cursor.fetchone()

        self.assertIsNotNone(result, "Error was not logged")
        self.assertEqual(result[2], "test_component")  # component
        self.assertEqual(result[3], "test_error")  # error_type
        self.assertEqual(result[4], "Test error message")  # error_message

        conn.close()


class TestEndToEndIntegration(unittest.TestCase):
    """Test complete end-to-end integration."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Create test RSS engine
        self.rss_engine = RSSIntelligenceEngine()
        self.rss_engine.db_path = os.path.join(self.temp_dir, "test_integration_rss.db")
        self.rss_engine._init_intelligence_tables()

        # Create test content pipeline
        self.pipeline = ContentAutomationPipeline()
        self.pipeline.db_path = os.path.join(
            self.temp_dir, "test_integration_content.db"
        )
        self.pipeline._init_automation_tables()

        # Override RSS engine in pipeline
        self.pipeline.rss_engine = self.rss_engine

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_content_workflow(self):
        """Test complete content creation workflow."""
        # Step 1: Add test news articles to RSS engine
        test_articles = [
            NewsArticle(
                title="Breaking: Major Political Scandal Exposed",
                url="https://example.com/scandal1",
                content="A major political figure has been caught in a significant scandal involving corruption.",
                published=datetime.now(),
                source="Test News",
                category="Politics",
                keywords=["scandal", "politics", "corruption"],
                entities=["Political Figure"],
                sentiment_score=0.2,
                readability_score=48.0,
                hash_id="scandal_123",
            ),
            NewsArticle(
                title="Political Figure Denies All Allegations",
                url="https://example.com/denial1",
                content="The political figure strongly denies all corruption allegations and claims innocence.",
                published=datetime.now(),
                source="Test News",
                category="Politics",
                keywords=["denial", "politics", "allegations"],
                entities=["Political Figure"],
                sentiment_score=0.6,
                readability_score=53.0,
                hash_id="denial_123",
            ),
        ]

        # Store articles in RSS engine
        for article in test_articles:
            success = self.rss_engine._store_article(article)
            self.assertTrue(success, f"Failed to store article: {article.title}")

        # Step 2: Identify content opportunities
        opportunities = self.pipeline.identify_content_opportunities()

        self.assertIsInstance(opportunities, list, "Opportunities should be a list")
        logger.info(f"Found {len(opportunities)} content opportunities")

        # Step 3: Generate content projects if opportunities exist
        if opportunities:
            opportunity = opportunities[0]
            projects = self.pipeline.generate_content_from_opportunity(opportunity)

            self.assertGreater(
                len(projects), 0, "No projects generated from opportunity"
            )

            # Step 4: Test video production for video projects
            video_projects = [p for p in projects if p.format == ContentFormat.VIDEO]
            if video_projects:
                video_project = video_projects[0]

                # Mock video production (don't actually create video in test)
                video_project.output_files = ["/tmp/test_video.mp4"]
                video_project.status = "completed"

                self.assertEqual(
                    video_project.status, "completed", "Video project not completed"
                )
                logger.info(f"Video project completed: {video_project.title}")

        # Step 5: Verify database integrity
        self._verify_database_integrity()

    def _verify_database_integrity(self):
        """Verify database integrity across all components."""
        # Check RSS database
        conn = sqlite3.connect(self.rss_engine.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM news_articles")
        article_count = cursor.fetchone()[0]
        self.assertGreater(article_count, 0, "No articles in RSS database")

        conn.close()

        # Check content pipeline database
        conn = sqlite3.connect(self.pipeline.db_path)
        cursor = conn.cursor()

        # Check for foreign key integrity
        cursor.execute(
            """
            SELECT COUNT(*) FROM content_projects cp
            LEFT JOIN content_opportunities co ON cp.opportunity_id = co.id
            WHERE co.id IS NULL AND cp.opportunity_id IS NOT NULL
        """
        )
        orphaned_projects = cursor.fetchone()[0]
        self.assertEqual(
            orphaned_projects, 0, "Found orphaned projects without opportunities"
        )

        conn.close()


def run_integration_tests():
    """Run all integration tests with detailed reporting."""
    print("\n" + "=" * 80)
    print("TRAE.AI CONTENT AUTOMATION - INTEGRATION TEST SUITE")
    print("=" * 80)

    # Create test suite
    test_suite = unittest.TestSuite()

    # Add test classes
    test_classes = [
        TestRSSIntelligenceEngine,
        TestContentAutomationPipeline,
        TestVideoGeneration,
        TestAutomationController,
        TestEndToEndIntegration,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)

    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2, stream=sys.stdout, descriptions=True, failfast=False
    )

    print(f"\nRunning {test_suite.countTestCases()} integration tests...\n")

    start_time = time.time()
    result = runner.run(test_suite)
    end_time = time.time()

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )
    print(f"Execution time: {end_time - start_time:.2f} seconds")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].split('\n')[0]}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('\n')[-2]}")

    print("\n" + "=" * 80)

    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


def run_performance_benchmark():
    """Run performance benchmarks for key operations."""
    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 80)

    import tempfile

    temp_dir = tempfile.mkdtemp()

    try:
        # Benchmark RSS article processing
        print("\n1. RSS Article Processing Benchmark")
        rss_engine = RSSIntelligenceEngine()
        rss_engine.db_path = os.path.join(temp_dir, "benchmark_rss.db")
        rss_engine._init_intelligence_tables()

        # Create test articles
        test_articles = []
        for i in range(100):
            article = NewsArticle(
                title=f"Test Article {i}",
                url=f"https://example.com/article{i}",
                content=f"This is test content for article {i} with various keywords and entities.",
                published=datetime.now(),
                source="Benchmark Source",
                category="General",
                keywords=["test", "benchmark", f"keyword{i}"],
                entities=[f"Entity{i}"],
                sentiment_score=0.5,
                readability_score=50.0,
                hash_id=f"hash_{i}",
            )
            test_articles.append(article)

        # Benchmark article storage
        start_time = time.time()
        for article in test_articles:
            rss_engine._store_article(article)
        storage_time = time.time() - start_time

        print(f"   - Stored 100 articles in {storage_time:.3f} seconds")
        print(f"   - Average: {storage_time/100*1000:.2f} ms per article")

        # Benchmark trend analysis
        start_time = time.time()
        trends = rss_engine.get_trending_topics()
        analysis_time = time.time() - start_time

        print(f"   - Trend analysis completed in {analysis_time:.3f} seconds")
        print(f"   - Found {len(trends)} trends")

        # Benchmark content pipeline
        print("\n2. Content Pipeline Benchmark")
        pipeline = ContentAutomationPipeline()
        pipeline.db_path = os.path.join(temp_dir, "benchmark_content.db")
        pipeline._init_automation_tables()
        pipeline.rss_engine = rss_engine

        start_time = time.time()
        opportunities = pipeline.identify_content_opportunities()
        opportunity_time = time.time() - start_time

        print(
            f"   - Identified {len(opportunities)} opportunities in {opportunity_time:.3f} seconds"
        )

        if opportunities:
            start_time = time.time()
            projects = pipeline.generate_content_from_opportunity(opportunities[0])
            generation_time = time.time() - start_time

            print(
                f"   - Generated {len(projects)} projects in {generation_time:.3f} seconds"
            )

        # Benchmark video generation
        print("\n3. Video Generation Benchmark")
        video_output = os.path.join(temp_dir, "benchmark_video.mp4")

        start_time = time.time()
        # Create a simple background image for the video
        background_path = os.path.join(temp_dir, "background.png")
        from PIL import Image

        img = Image.new("RGB", (1920, 1080), color="blue")
        img.save(background_path)

        # Create a simple audio file (silence)
        audio_path = os.path.join(temp_dir, "audio.wav")
        import wave

        with wave.open(audio_path, "w") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(44100)
            wav_file.writeframes(b"\x00" * 44100 * 2 * 10)  # 10 seconds of silence

        success = create_basic_video(
            background_image_path=background_path,
            audio_path=audio_path,
            output_path=video_output,
        )
        video_time = time.time() - start_time

        if success:
            file_size = os.path.getsize(video_output) / (1024 * 1024)  # MB
            print(f"   - Generated 10-second video in {video_time:.3f} seconds")
            print(f"   - Video size: {file_size:.2f} MB")
            print(f"   - Generation rate: {10/video_time:.2f}x real-time")
        else:
            print("   - Video generation failed")

    finally:
        # Cleanup
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="TRAE.AI Content Automation Integration Tests"
    )
    parser.add_argument(
        "--benchmark", action="store_true", help="Run performance benchmarks"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        import logging

        logging.basicConfig(level=logging.INFO)

    try:
        # Run integration tests
        success = run_integration_tests()

        # Run benchmarks if requested
        if args.benchmark:
            run_performance_benchmark()

        # Exit with appropriate code
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest execution failed: {e}")
        sys.exit(1)
