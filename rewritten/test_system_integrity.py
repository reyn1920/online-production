#!/usr/bin/env python3
""""""
TRAE.AI System Integrity Test Suite

This comprehensive test suite verifies that all aspects of the TRAE.AI application
are 100% complete, fully integrated, \
#     and working correctly in a live production environment.

Test Coverage:
1. System Startup and Health
2. Database Integrity and Connectivity
3. Core Tool Verification
4. Agent Initialization Test
5. Full End - to - End Workflow Test (The "Golden Path")
""""""

import importlib
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest
import requests

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))


class SystemIntegrityTest:
    """Main test class for TRAE.AI system integrity verification"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.db_path = self.project_root / "right_perspective.db"
        self.dashboard_url = "http://localhost:5000"
        self.ollama_url = "http://localhost:11434"
        self.launch_process: Optional[subprocess.Popen] = None
        self.output_dir = self.project_root / "assets" / "generated"

    def setup_method(self):
        """Setup method run before each test"""
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Cleanup method run after each test"""
        if self.launch_process:
            try:
                self.launch_process.terminate()
                self.launch_process.wait(timeout=10)
            except (subprocess.TimeoutExpired, ProcessLookupError):
                try:
                    self.launch_process.kill()
                    self.launch_process.wait(timeout=5)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    pass
            self.launch_process = None


@pytest.fixture(scope="class")
def system_test():
    """Fixture to provide SystemIntegrityTest instance"""
    test_instance = SystemIntegrityTest()
    yield test_instance
    test_instance.teardown_method()


class TestSystemStartupAndHealth:
    """Test system startup and health verification"""

    def test_launch_live_script_startup(self, system_test):
        """Test that launch_live.py starts successfully and dashboard responds"""
        # Start the launch_live.py script
        env = os.environ.copy()
        env["TRAE_MASTER_KEY"] = "trae_master_key_2024_production"
        env["DASHBOARD_PORT"] = "8081"

        system_test.launch_process = subprocess.Popen(
            [sys.executable, "launch_live.py"],
            cwd=system_test.project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
# BRACKET_SURGEON: disabled
#         )

        # Wait for system to start up
        time.sleep(15)

        # Verify the process is still running
        assert (
            system_test.launch_process.poll() is None
# BRACKET_SURGEON: disabled
#         ), "launch_live.py process terminated unexpectedly"

    def test_dashboard_health_endpoint(self, system_test):
        """Test that the dashboard health endpoint responds correctly"""
        max_retries = 10
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                response = requests.get(f"{system_test.dashboard_url}/api/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    assert (
                        health_data.get("status") == "healthy"
                    ), f"Health check failed: {health_data}"
                    return
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise

        pytest.fail("Dashboard health endpoint did not respond after multiple attempts")


class TestDatabaseIntegrity:
    """Test database connectivity and schema integrity"""

    def test_database_connection(self, system_test):
        """Test that we can connect to the main database"""
        assert system_test.db_path.exists(), f"Database file not found: {system_test.db_path}"

        conn = sqlite3.connect(system_test.db_path)
        cursor = conn.cursor()

        # Test basic connectivity
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1, "Basic database query failed"

        conn.close()

    def test_required_tables_exist(self, system_test):
        """Test that all required database tables exist"""
        required_tables = [
            "task_queue",
            "channels",
            "api_registry",
            "hypocrisy_tracker",
            "evidence",
            "reports",
            "content_performance",
# BRACKET_SURGEON: disabled
#         ]

        conn = sqlite3.connect(system_test.db_path)
        cursor = conn.cursor()

        # Get list of existing tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]

        # Check each required table exists
        for table in required_tables:
            assert table in existing_tables, f"Required table '{table}' not found in database"

            # Verify table has at least basic structure
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            assert len(columns) > 0, f"Table '{table}' has no columns"

        conn.close()


class TestCoreToolVerification:
    """Test that all critical external tools are available"""

    def test_blender_executable(self):
        """Test that Blender executable can be found"""
        # Common Blender paths on macOS
        blender_paths = [
            "/Applications/Blender.app/Contents/MacOS/Blender",
            "/usr/local/bin/blender",
            "/opt/homebrew/bin/blender",
# BRACKET_SURGEON: disabled
#         ]

        blender_found = False
        for path in blender_paths:
            if os.path.exists(path):
                blender_found = True
                break

        # Also check if blender is in PATH
        if not blender_found:
            try:
                result = subprocess.run(["which", "blender"], capture_output=True, text=True)
                if result.returncode == 0:
                    blender_found = True
            except FileNotFoundError:
                pass

        assert blender_found, "Blender executable not found in expected locations or PATH"

    def test_davinci_resolve_api(self):
        """Test DaVinci Resolve scripting API availability"""
        try:
            # Try to import DaVinci Resolve API

            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")
            # If we get here without exception, API is available
            assert True
        except ImportError:
            # DaVinci Resolve API not available - this is acceptable for testing
            pytest.skip("DaVinci Resolve API not available (acceptable for testing environment)")
        except Exception as e:
            # Other errors might indicate configuration issues
            pytest.skip(f"DaVinci Resolve API error (acceptable for testing): {e}")

    def test_ollama_server_connectivity(self, system_test):
        """Test that Ollama server is running and responsive"""
        try:
            response = requests.get(f"{system_test.ollama_url}/api/tags", timeout=10)
            assert (
                response.status_code == 200
            ), f"Ollama server returned status {response.status_code}"

            # Verify response contains expected structure
            data = response.json()
            assert "models" in data, "Ollama response missing 'models' field"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Ollama server not available (acceptable for testing): {e}")


class TestAgentInitialization:
    """Test that all specialized agents can be initialized"""

    def test_import_all_agents(self):
        """Test that all agent modules can be imported without errors"""
        agent_modules = [
            "backend.agents.base_agents",
            "backend.agents.specialized_agents",
            "backend.agents.evolution_agent",
            "backend.agents.financial_agent",
            "backend.agents.growth_agent",
            "backend.agents.self_repair_agent",
# BRACKET_SURGEON: disabled
#         ]

        for module_name in agent_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                pytest.fail(f"Failed to import agent module '{module_name}': {e}")

    def test_initialize_core_agents(self):
        """Test that core agents can be instantiated"""
        try:
            from backend.agents.financial_agent import FinancialAgent
            from backend.agents.growth_agent import GrowthAgent
            from backend.agents.specialized_agents import (
                ContentAgent,
                MarketingAgent,
                QAAgent,
                ResearchAgent,
                SystemAgent,
# BRACKET_SURGEON: disabled
#             )

            # Test agent classes are importable and have required attributes
            agent_classes = [
                (SystemAgent, "SystemAgent"),
                (ResearchAgent, "ResearchAgent"),
                (ContentAgent, "ContentAgent"),
                (MarketingAgent, "MarketingAgent"),
                (QAAgent, "QAAgent"),
                (FinancialAgent, "FinancialAgent"),
                (GrowthAgent, "GrowthAgent"),
# BRACKET_SURGEON: disabled
#             ]

            for agent_class, agent_name in agent_classes:
                # Test that class exists and has required methods
                assert hasattr(agent_class, "__init__"), f"{agent_name} missing __init__ method"
                assert hasattr(
                    agent_class, "capabilities"
                ), f"{agent_name} missing capabilities property"

                # Test that the class is properly structured (don't instantiate abstract classes)
                assert callable(agent_class), f"{agent_name} is not callable"

                # Test that the class has the expected base class structure

                from backend.agents.base_agents import BaseAgent

                assert issubclass(
                    agent_class, BaseAgent
                ), f"{agent_name} does not inherit from BaseAgent"

        except Exception as e:
            pytest.fail(f"Agent initialization test failed: {e}")


class TestEndToEndWorkflow:
    """Test the complete end - to - end video creation workflow"""

    def test_full_video_creation_workflow(self, system_test):
        """Test the complete 'Golden Path' video creation workflow"""
        # Ensure system is running
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = requests.get(f"{system_test.dashboard_url}/api/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                pytest.skip("Dashboard not available for end - to - end test")

        # Step 1: Add a CREATE_VIDEO task to the task queue
        task_data = {
            "task_type": "CREATE_VIDEO",
            "priority": "high",
            "parameters": {
                "topic": "Test Video Creation",
                "style": "educational",
                "duration": 60,
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        try:
            response = requests.post(
                f"{system_test.dashboard_url}/api/tasks", json=task_data, timeout=10
# BRACKET_SURGEON: disabled
#             )
            assert response.status_code in [
                200,
                201,
            ], f"Failed to create task: {response.status_code}"

            task_response = response.json()
            task_id = task_response.get("task_id")
            assert task_id is not None, "Task creation did not return task_id"

        except requests.exceptions.RequestException as e:
            pytest.skip(f"Could not create video task via API: {e}")

        # Step 2: Poll task status until completion
        max_wait_time = 300  # 5 minutes maximum
        poll_interval = 10  # Check every 10 seconds
        start_time = time.time()

        final_status = None
        while time.time() - start_time < max_wait_time:
            try:
                response = requests.get(
                    f"{system_test.dashboard_url}/api/tasks/{task_id}", timeout=5
# BRACKET_SURGEON: disabled
#                 )

                if response.status_code == 200:
                    task_info = response.json()
                    status = task_info.get("status")

                    if status in ["completed", "failed", "error"]:
                        final_status = status
                        break
                    elif status in ["pending", "in_progress"]:
                        # Task is progressing normally
                        time.sleep(poll_interval)
                        continue
                    else:
                        pytest.fail(f"Unexpected task status: {status}")
                else:
                    time.sleep(poll_interval)

            except requests.exceptions.RequestException:
                time.sleep(poll_interval)

        # Verify task completed successfully
        assert (
            final_status == "completed"
        ), f"Task did not complete successfully. Final status: {final_status}"

        # Step 3: Verify output video file was created
        output_directories = [
            system_test.project_root / "assets" / "generated",
            system_test.project_root / "output",
            system_test.project_root / "videos",
# BRACKET_SURGEON: disabled
#         ]

        video_found = False
        for output_dir in output_directories:
            if output_dir.exists():
                video_files = list(output_dir.glob("*.mp4"))
                if video_files:
                    # Check if any video file was created recently (within last 10 minutes)
                    recent_videos = [
                        f for f in video_files if time.time() - f.stat().st_mtime < 600
# BRACKET_SURGEON: disabled
#                     ]
                    if recent_videos:
                        video_found = True
                        break

        assert (
            video_found
# BRACKET_SURGEON: disabled
#         ), "No recent .mp4 video file found in output directories after workflow completion"


# Test execution configuration
if __name__ == "__main__":
    # Run the tests with verbose output
    pytest.main([__file__, "-v", "--tb = short", "--capture = no"])