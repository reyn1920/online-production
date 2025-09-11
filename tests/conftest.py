#!/usr/bin/env python3
"""
Pytest configuration and shared fixtures for TRAE.AI test suite.
"""

import asyncio
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator
from unittest.mock import AsyncMock, Mock

import httpx
import numpy as np
import psutil
import pytest
from PIL import Image

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_CONFIG = {
    "base_url": os.getenv("TEST_BASE_URL", "http://localhost:8080"),
    "dashboard_url": os.getenv("TEST_DASHBOARD_URL", "http://localhost:8081"),
    "timeout": int(os.getenv("TEST_TIMEOUT", "30")),
    "test_output_dir": Path("tests/output"),
    "test_data_dir": Path("tests/data"),
    "test_artifacts_dir": Path("tests/artifacts"),
    "max_retries": int(os.getenv("TEST_MAX_RETRIES", "3")),
    "retry_delay": float(os.getenv("TEST_RETRY_DELAY", "1.0")),
    "parallel_workers": int(os.getenv("TEST_PARALLEL_WORKERS", "4")),
    "enable_real_services": os.getenv("TEST_ENABLE_REAL_SERVICES", "false").lower()
    == "true",
    "mock_external_apis": os.getenv("TEST_MOCK_EXTERNAL_APIS", "true").lower()
    == "true",
    "log_level": os.getenv("TEST_LOG_LEVEL", "INFO"),
    "save_artifacts": os.getenv("TEST_SAVE_ARTIFACTS", "true").lower() == "true",
    "cleanup_after_tests": os.getenv("TEST_CLEANUP_AFTER_TESTS", "true").lower()
    == "true",
}

# Ensure test directories exist
for directory in [
    TEST_CONFIG["test_output_dir"],
    TEST_CONFIG["test_data_dir"],
    TEST_CONFIG["test_artifacts_dir"],
]:
    directory.mkdir(parents=True, exist_ok=True)

pytest_plugins = []


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Provide test configuration to all tests."""
    return TEST_CONFIG.copy()


@pytest.fixture(scope="session")
async def http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an HTTP client for API testing."""
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(TEST_CONFIG["timeout"]), follow_redirects=True
    ) as client:
        yield client


@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(scope="function")
def test_image() -> Generator[Path, None, None]:
    """Create a test image file."""
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        img.save(tmp_file.name)
        yield Path(tmp_file.name)
        # Cleanup
        if Path(tmp_file.name).exists():
            Path(tmp_file.name).unlink()


@pytest.fixture(scope="function")
def test_video_data() -> Dict[str, Any]:
    """Provide test data for video generation."""
    return {
        "script": "This is a test video script for automated testing.",
        "duration": 30,
        "style": "professional",
        "voice": "neutral",
        "background_music": False,
        "resolution": "720p",
        "format": "mp4",
    }


@pytest.fixture(scope="function")
def test_content_data() -> Dict[str, Any]:
    """Provide test data for content generation."""
    return {
        "blog_post": {
            "topic": "AI in Software Development",
            "tone": "professional",
            "length": "medium",
            "target_audience": "developers",
        },
        "social_media": {
            "platform": "twitter",
            "message": "Test social media content",
            "hashtags": ["#AI", "#Testing"],
            "include_image": False,
        },
        "newsletter": {
            "subject": "Weekly AI Updates",
            "sections": ["news", "tutorials", "tools"],
            "tone": "friendly",
        },
    }


@pytest.fixture(scope="function")
def test_campaign_data() -> Dict[str, Any]:
    """Provide test data for marketing campaigns."""
    return {
        "name": f'Test Campaign {datetime.now().strftime("%Y%m%d_%H%M%S")}',
        "campaign_type": "brand_awareness",
        "channels": ["social_media", "email"],
        "target_audience": "tech enthusiasts",
        "budget": 1000.0,
        "duration_days": 30,
        "objectives": ["increase_brand_awareness", "generate_leads"],
        "content_themes": ["innovation", "technology"],
        "geographic_targets": ["US", "CA", "UK"],
    }


@pytest.fixture(scope="function")
def mock_external_services():
    """Mock external API services for testing."""
    mocks = {
        "openai_client": Mock(),
        "youtube_api": Mock(),
        "mailchimp_api": Mock(),
        "gumroad_api": Mock(),
        "stripe_api": Mock(),
        "twitter_api": Mock(),
        "instagram_api": Mock(),
        "tiktok_api": Mock(),
    }

    # Configure mock responses
    mocks["openai_client"].chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content="Mock AI response"))]
    )

    mocks[
        "youtube_api"
    ].videos.return_value.insert.return_value.execute.return_value = {
        "id": "mock_video_id",
        "snippet": {"title": "Mock Video"},
    }

    mocks["mailchimp_api"].lists.get_all_members.return_value = {
        "members": [{"email_address": "test@example.com"}]
    }

    return mocks


@pytest.fixture(scope="function")
async def mock_database():
    """Mock database for testing."""
    # In-memory mock database
    mock_db = {
        "campaigns": [],
        "content": [],
        "analytics": [],
        "users": [],
        "videos": [],
        "revenue": [],
    }

    class MockDB:
        def __init__(self, data):
            self.data = data

        async def insert(self, table: str, record: Dict[str, Any]) -> str:
            record_id = f"mock_{len(self.data[table]) + 1}"
            record["id"] = record_id
            record["created_at"] = datetime.now().isoformat()
            self.data[table].append(record)
            return record_id

        async def find(self, table: str, query: Dict[str, Any] = None) -> list:
            if query is None:
                return self.data[table]
            # Simple query matching
            results = []
            for record in self.data[table]:
                match = True
                for key, value in query.items():
                    if record.get(key) != value:
                        match = False
                        break
                if match:
                    results.append(record)
            return results

        async def update(
            self, table: str, record_id: str, updates: Dict[str, Any]
        ) -> bool:
            for record in self.data[table]:
                if record.get("id") == record_id:
                    record.update(updates)
                    record["updated_at"] = datetime.now().isoformat()
                    return True
            return False

        async def delete(self, table: str, record_id: str) -> bool:
            for i, record in enumerate(self.data[table]):
                if record.get("id") == record_id:
                    del self.data[table][i]
                    return True
            return False

    return MockDB(mock_db)


@pytest.fixture(scope="function")
def cleanup_test_data():
    """Clean up test data after each test."""
    yield

    if TEST_CONFIG["cleanup_after_tests"]:
        # Clean up test output files
        test_files = list(TEST_CONFIG["test_output_dir"].glob("test_*"))
        for file_path in test_files:
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)


@pytest.fixture(scope="function")
def test_artifacts_collector():
    """Collect test artifacts for debugging."""
    artifacts = {
        "screenshots": [],
        "logs": [],
        "api_responses": [],
        "generated_files": [],
        "performance_metrics": {},
        "error_traces": [],
    }

    def add_artifact(artifact_type: str, data: Any, filename: str = None):
        if TEST_CONFIG["save_artifacts"]:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            if filename is None:
                filename = f"{artifact_type}_{timestamp}"

            artifact_path = TEST_CONFIG["test_artifacts_dir"] / filename

            if artifact_type == "screenshot" and hasattr(data, "save"):
                data.save(artifact_path.with_suffix(".png"))
            elif artifact_type in ["log", "api_response", "error_trace"]:
                with open(artifact_path.with_suffix(".json"), "w") as f:
                    json.dump(data, f, indent=2, default=str)
            elif artifact_type == "generated_file":
                if isinstance(data, (str, bytes)):
                    mode = "w" if isinstance(data, str) else "wb"
                    with open(artifact_path, mode) as f:
                        f.write(data)

            artifacts[f"{artifact_type}s"].append(str(artifact_path))

    artifacts["add"] = add_artifact
    return artifacts


@pytest.fixture(scope="function")
async def health_checker(http_client: httpx.AsyncClient):
    """Check system health before tests."""

    async def check_service(url: str, timeout: int = 5) -> bool:
        try:
            response = await http_client.get(f"{url}/health", timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    return check_service


@pytest.fixture(scope="function")
def performance_monitor():
    """Monitor test performance metrics."""
    metrics = {
        "start_time": time.time(),
        "start_memory": psutil.Process().memory_info().rss,
        "api_calls": 0,
        "file_operations": 0,
    }

    def record_api_call():
        metrics["api_calls"] += 1

    def record_file_operation():
        metrics["file_operations"] += 1

    def get_metrics():
        current_time = time.time()
        current_memory = psutil.Process().memory_info().rss

        return {
            "duration": current_time - metrics["start_time"],
            "memory_delta": current_memory - metrics["start_memory"],
            "api_calls": metrics["api_calls"],
            "file_operations": metrics["file_operations"],
        }

    metrics["record_api_call"] = record_api_call
    metrics["record_file_operation"] = record_file_operation
    metrics["get_metrics"] = get_metrics

    return metrics


@pytest.fixture(scope="session")
def project_root_path():
    """Provide project root path to all tests."""
    return project_root


@pytest.fixture(scope="session")
def test_database_path():
    """Provide test database path."""
    return project_root / "test_database.db"


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment before each test."""
    # Set test environment variables
    os.environ["TESTING"] = "true"
    os.environ["TRAE_MASTER_KEY"] = "test_key_2024"

    yield

    # Cleanup after test
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture
def mock_agents():
    """Mock agent instances for testing."""

    class MockAgent:
        def __init__(self, name):
            self.name = name
            self.status = "active"
            self.health = "healthy"

        def get_status(self):
            return {"status": self.status, "health": self.health}

    return {
        "system": MockAgent("SystemAgent"),
        "research": MockAgent("ResearchAgent"),
        "marketing": MockAgent("MarketingAgent"),
        "content": MockAgent("ContentAgent"),
    }


@pytest.fixture
def sample_test_data():
    """Provide sample test data for all tests."""
    return {
        "test_user": {"id": 1, "name": "Test User", "email": "test@example.com"},
        "test_project": {"id": "proj-test", "name": "Test Project", "status": "active"},
        "test_agent_status": {
            "agent_id": "test-agent",
            "status": "running",
            "health": "good",
        },
    }


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.system = pytest.mark.system
pytest.mark.slow = pytest.mark.slow
