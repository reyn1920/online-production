#!/usr / bin / env python3
"""
TRAE.AI System Smoke Test Agent

A comprehensive automated testing agent that implements the complete go - live checklist
for verifying system integrity and operational readiness. This agent provides one - click
verification of all critical system components and workflows.

Features:
- Automated pre - flight infrastructure checks
- Live 5 - minute smoke test protocol
- Real - time test result streaming
- Complete end - to - end workflow verification

Author: TRAE.AI System
Version: 1.0.0 - Go - Live Integration
"""

import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from ...utils.logger import get_logger
from ..secret_store import SecretStore
from ..task_queue_manager import TaskQueueManager, TaskStatus
from .base_agents import AgentCapability, AgentStatus, BaseAgent

# Import dashboard action decorator
try:
    import sys

    sys.path.append(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    from app.dashboard import dashboard_action
except ImportError:
    # Fallback decorator if dashboard not available


    def dashboard_action(
        name = None, description = None, category = None, requires_auth = False
    ):


        def decorator(func):
            return func

        return decorator


class TestStatus(Enum):
    """Test execution status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TestSeverity(Enum):
    """Test failure severity levels."""

    CRITICAL = "critical"  # System cannot go live
    WARNING = "warning"  # Should be addressed but not blocking
    INFO = "info"  # Informational only

@dataclass


class TestResult:
    """Individual test result data structure."""

    test_id: str
    name: str
    status: TestStatus
    severity: TestSeverity
    duration_ms: int
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[datetime] = None


    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass


class SmokeTestReport:
    """Complete smoke test execution report."""

    test_run_id: str
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_ms: int
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    critical_failures: int
    overall_status: TestStatus
    test_results: List[TestResult]
    system_info: Dict[str, Any]


class SystemSmokeTestAgent(BaseAgent):
    """
    Advanced system smoke test agent implementing the complete go - live checklist.

    This agent provides comprehensive automated testing capabilities including:
    - Infrastructure sanity checks
    - Service health verification
    - End - to - end workflow testing
    - Real - time result streaming
    """


    def __init__(self, agent_id: str = "system - smoke - test - agent"):
        super().__init__(agent_id)
        self.logger = get_logger(f"trae_ai.agents.{agent_id}")
        self.secret_store = SecretStore()
        self.task_queue = TaskQueueManager("trae_ai.db")

        # Test configuration
        self.dashboard_port = int(os.getenv("DASHBOARD_PORT", "8080"))
        self.orchestrator_port = int(os.getenv("ORCHESTRATOR_PORT", "8081"))
        self.base_url = f"http://localhost:{self.dashboard_port}"
        self.orchestrator_url = f"http://localhost:{self.orchestrator_port}"

        # Test timeouts and intervals
        self.health_check_timeout = 10  # seconds
        self.task_poll_interval = 5  # seconds
        self.max_task_wait_time = 300  # 5 minutes

        # Test result streaming callback
        self.result_callback: Optional[Callable[[TestResult], None]] = None

        # Current test run state
        self.current_test_run: Optional[SmokeTestReport] = None
        self.test_start_time: Optional[datetime] = None

    @property


    def capabilities(self) -> List[AgentCapability]:
        return [AgentCapability.AUDITING, AgentCapability.EXECUTION]


    def set_result_callback(self, callback: Callable[[TestResult], None]):
        """Set callback function for real - time test result streaming."""
        self.result_callback = callback


    def _emit_test_result(self, result: TestResult):
        """Emit test result to callback if configured."""
        if self.result_callback:
            try:
                self.result_callback(result)
            except Exception as e:
                self.logger.error(f"Error in result callback: {e}")


    def _run_test(
        self,
            test_id: str,
            name: str,
            test_func: Callable,
            severity: TestSeverity = TestSeverity.CRITICAL,
            ) -> TestResult:
        """Execute a single test with timing and error handling."""
        start_time = time.time()

        try:
            self.logger.info(f"Running test: {name}")
            success, message, details = test_func()

            duration_ms = int((time.time() - start_time) * 1000)
            status = TestStatus.PASSED if success else TestStatus.FAILED

            result = TestResult(
                test_id = test_id,
                    name = name,
                    status = status,
                    severity = severity,
                    duration_ms = duration_ms,
                    message = message,
                    details = details,
                    )

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            result = TestResult(
                test_id = test_id,
                    name = name,
                    status = TestStatus.FAILED,
                    severity = severity,
                    duration_ms = duration_ms,
                    message = f"Test execution failed: {str(e)}",
                    details={"exception": str(e), "type": type(e).__name__},
                    )

        self._emit_test_result(result)
        return result

    # ========================================================================
        # PRE - FLIGHT INFRASTRUCTURE CHECKS
    # ========================================================================


    def _test_dashboard_port_configuration(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify dashboard is configured for correct port."""
        expected_port = 8080
        actual_port = self.dashboard_port

        if actual_port == expected_port:
            return (
                True,
                    f"Dashboard port correctly configured: {actual_port}",
                    {"port": actual_port},
                    )
        else:
            return (
                False,
                    f"Dashboard port misconfigured. Expected: {expected_port}, Actual: {actual_port}",
                    {"expected_port": expected_port, "actual_port": actual_port},
                    )


    def _test_secrets_availability(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify all required secrets are loaded and accessible."""
        required_secrets = ["TRAE_MASTER_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]

        missing_secrets = []
        available_secrets = []

        for secret_name in required_secrets:
            try:
                value = self.secret_store.get_secret(secret_name)
                if value and len(value.strip()) > 0:
                    available_secrets.append(secret_name)
                else:
                    missing_secrets.append(secret_name)
            except Exception:
                missing_secrets.append(secret_name)

        if not missing_secrets:
            return (
                True,
                    f"All {len(available_secrets)} required secrets are available",
                    {
                    "available_secrets": available_secrets,
                        "total_count": len(available_secrets),
                        },
                    )
        else:
            return (
                False,
                    f"Missing {len(missing_secrets)} required secrets: {', '.join(missing_secrets)}",
                    {
                    "missing_secrets": missing_secrets,
                        "available_secrets": available_secrets,
                        },
                    )


    def _test_disk_space_availability(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify at least 5GB of free disk space is available."""
        try:
            # Get disk usage for current directory
            total, used, free = shutil.disk_usage(".")

            # Convert to GB
            free_gb = free / (1024**3)
            total_gb = total / (1024**3)
            used_gb = used / (1024**3)

            required_gb = 5.0

            if free_gb >= required_gb:
                return (
                    True,
                        f"Sufficient disk space available: {free_gb:.2f}GB free",
                        {
                        "free_gb": round(free_gb, 2),
                            "total_gb": round(total_gb, 2),
                            "used_gb": round(used_gb, 2),
                            "required_gb": required_gb,
                            },
                        )
            else:
                return (
                    False,
                        f"Insufficient disk space. Required: {required_gb}GB, Available: {free_gb:.2f}GB",
                        {
                        "free_gb": round(free_gb, 2),
                            "required_gb": required_gb,
                            "deficit_gb": round(required_gb - free_gb, 2),
                            },
                        )

        except Exception as e:
            return False, f"Failed to check disk space: {str(e)}", {"error": str(e)}


    def _test_ffmpeg_installation(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output = True, text = True, timeout = 10
            )

            if result.returncode == 0:
                # Extract version info from output
                version_line = (
                    result.stdout.split("\n")[0] if result.stdout else "Unknown version"
                )
                return (
                    True,
                        f"FFmpeg is installed and accessible: {version_line}",
                        {"version_output": version_line, "return_code": result.returncode},
                        )
            else:
                return (
                    False,
                        f"FFmpeg command failed with return code: {result.returncode}",
                        {"return_code": result.returncode, "stderr": result.stderr},
                        )

        except subprocess.TimeoutExpired:
            return False, "FFmpeg command timed out", {"error": "timeout"}
        except FileNotFoundError:
            return False, "FFmpeg not found in system PATH", {"error": "not_found"}
        except Exception as e:
            return False, f"Failed to check FFmpeg: {str(e)}", {"error": str(e)}


    def _test_directory_permissions(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify write permissions for critical directories."""
        critical_dirs = ["outputs", "data", "assets / generated"]
        test_results = {}
        failed_dirs = []

        for dir_name in critical_dirs:
            dir_path = Path(dir_name)

            try:
                # Ensure directory exists
                dir_path.mkdir(parents = True, exist_ok = True)

                # Test write permission with temporary file
                with tempfile.NamedTemporaryFile(dir = dir_path, delete = True) as tmp_file:
                    tmp_file.write(b"test data")
                    tmp_file.flush()

                test_results[dir_name] = "writable"

            except Exception as e:
                test_results[dir_name] = f"failed: {str(e)}"
                failed_dirs.append(dir_name)

        if not failed_dirs:
            return (
                True,
                    f"All {len(critical_dirs)} critical directories are writable",
                    {"test_results": test_results, "directories_tested": critical_dirs},
                    )
        else:
            return (
                False,
                    f"Write permission failed for {len(failed_dirs)} directories: {', '.join(failed_dirs)}",
                    {"test_results": test_results, "failed_directories": failed_dirs},
                    )

    # ========================================================================
        # LIVE SYSTEM HEALTH CHECKS
    # ========================================================================


    def _test_dashboard_health_endpoint(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify dashboard health endpoint responds correctly."""
        try:
            response = requests.get(
                f"{self.base_url}/api / health", timeout = self.health_check_timeout
            )

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    return (
                        True,
                            "Dashboard health endpoint is responding correctly",
                            {
                            "status_code": response.status_code,
                                "response_time_ms": int(
                                response.elapsed.total_seconds() * 1000
                            ),
                                "health_data": health_data,
                                },
                            )
                except json.JSONDecodeError:
                    return (
                        True,
                            "Dashboard health endpoint is responding (non - JSON)",
                            {
                            "status_code": response.status_code,
                                "response_time_ms": int(
                                response.elapsed.total_seconds() * 1000
                            ),
                                },
                            )
            else:
                return (
                    False,
                        f"Dashboard health endpoint returned status {response.status_code}",
                        {
                        "status_code": response.status_code,
                            "response_text": response.text[:200],
                            },
                        )

        except ConnectionError:
            return (
                False,
                    f"Cannot connect to dashboard at {self.base_url}",
                    {"url": f"{self.base_url}/api / health", "error": "connection_refused"},
                    )
        except Timeout:
            return (
                False,
                    f"Dashboard health check timed out after {self.health_check_timeout}s",
                    {"timeout_seconds": self.health_check_timeout},
                    )
        except Exception as e:
            return False, f"Dashboard health check failed: {str(e)}", {"error": str(e)}


    def _test_orchestrator_health_endpoint(self) -> tuple[bool, str, Dict[str, Any]]:
        """Verify orchestrator health endpoint responds correctly."""
        try:
            response = requests.get(
                f"{self.orchestrator_url}/api / health", timeout = self.health_check_timeout
            )

            if response.status_code == 200:
                try:
                    health_data = response.json()
                    return (
                        True,
                            "Orchestrator health endpoint is responding correctly",
                            {
                            "status_code": response.status_code,
                                "response_time_ms": int(
                                response.elapsed.total_seconds() * 1000
                            ),
                                "health_data": health_data,
                                },
                            )
                except json.JSONDecodeError:
                    return (
                        True,
                            "Orchestrator health endpoint is responding (non - JSON)",
                            {
                            "status_code": response.status_code,
                                "response_time_ms": int(
                                response.elapsed.total_seconds() * 1000
                            ),
                                },
                            )
            else:
                return (
                    False,
                        f"Orchestrator health endpoint returned status {response.status_code}",
                        {
                        "status_code": response.status_code,
                            "response_text": response.text[:200],
                            },
                        )

        except ConnectionError:
            return (
                False,
                    f"Cannot connect to orchestrator at {self.orchestrator_url}",
                    {
                    "url": f"{self.orchestrator_url}/api / health",
                        "error": "connection_refused",
                        },
                    )
        except Timeout:
            return (
                False,
                    f"Orchestrator health check timed out after {self.health_check_timeout}s",
                    {"timeout_seconds": self.health_check_timeout},
                    )
        except Exception as e:
            return (
                False,
                    f"Orchestrator health check failed: {str(e)}",
                    {"error": str(e)},
                    )

    # ========================================================================
        # END - TO - END WORKFLOW TESTING
    # ========================================================================


    def _test_video_creation_workflow(self) -> tuple[bool, str, Dict[str, Any]]:
        """Execute complete end - to - end video creation workflow test."""
        workflow_start_time = time.time()

        # Step 1: Create video task
        task_creation_result = self._create_test_video_task()
        if not task_creation_result[0]:
            return task_creation_result

        task_id = task_creation_result[2].get("task_id")
        if not task_id:
            return False, "No task ID returned from video creation", {}

        # Step 2: Poll task status until completion
        polling_result = self._poll_task_until_completion(task_id)
        if not polling_result[0]:
            return polling_result

        # Step 3: Verify output file exists
        file_verification_result = self._verify_video_output_file(task_id)
        if not file_verification_result[0]:
            return file_verification_result

        total_duration = int((time.time() - workflow_start_time) * 1000)

        return (
            True,
                f"Complete video creation workflow successful in {total_duration}ms",
                {
                "task_id": task_id,
                    "total_duration_ms": total_duration,
                    "task_creation": task_creation_result[2],
                    "polling_result": polling_result[2],
                    "file_verification": file_verification_result[2],
                    },
                )


    def _create_test_video_task(self) -> tuple[bool, str, Dict[str, Any]]:
        """Create a test video creation task."""
        test_payload = {
            "topic": "TRAE.AI System Smoke Test",
                "style": "professional",
                "duration": 30,
                "priority": "high",
                "test_mode": True,
                }

        try:
            response = requests.post(
                f"{self.base_url}/api / workflows / create - video",
                    json = test_payload,
                    timeout = 30,
                    )

            if response.status_code in [200, 201]:
                try:
                    response_data = response.json()
                    task_id = response_data.get("task_id") or response_data.get("id")

                    if task_id:
                        return (
                            True,
                                f"Video task created successfully: {task_id}",
                                {
                                "task_id": task_id,
                                    "status_code": response.status_code,
                                    "response_data": response_data,
                                    },
                                )
                    else:
                        return (
                            False,
                                "Video task created but no task ID returned",
                                {
                                "status_code": response.status_code,
                                    "response_data": response_data,
                                    },
                                )

                except json.JSONDecodeError:
                    return (
                        False,
                            "Video task endpoint returned invalid JSON",
                            {
                            "status_code": response.status_code,
                                "response_text": response.text[:200],
                                },
                            )
            else:
                return (
                    False,
                        f"Video task creation failed with status {response.status_code}",
                        {
                        "status_code": response.status_code,
                            "response_text": response.text[:200],
                            },
                        )

        except Exception as e:
            return False, f"Failed to create video task: {str(e)}", {"error": str(e)}


    def _poll_task_until_completion(
        self, task_id: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Poll task status until completion or timeout."""
        start_time = time.time()
        poll_count = 0
        last_status = None

        while (time.time() - start_time) < self.max_task_wait_time:
            poll_count += 1

            try:
                response = requests.get(
                    f"{self.base_url}/api / tasks",
                        params={"task_id": task_id},
                        timeout = 10,
                        )

                if response.status_code == 200:
                    try:
                        tasks_data = response.json()

                        # Handle different response formats
                        if isinstance(tasks_data, list) and tasks_data:
                            task_data = tasks_data[0]
                        elif isinstance(tasks_data, dict):
                            task_data = tasks_data
                        else:
                            return (
                                False,
                                    "Invalid task data format received",
                                    {"response_data": tasks_data},
                                    )

                        current_status = task_data.get("status", "unknown")
                        last_status = current_status

                        if current_status == TaskStatus.COMPLETED:
                            duration = int((time.time() - start_time) * 1000)
                            return (
                                True,
                                    f"Task completed successfully after {poll_count} polls in {duration}ms",
                                    {
                                    "task_id": task_id,
                                        "final_status": current_status,
                                        "poll_count": poll_count,
                                        "duration_ms": duration,
                                        "task_data": task_data,
                                        },
                                    )
                        elif current_status == TaskStatus.FAILED:
                            return (
                                False,
                                    f"Task failed with status: {current_status}",
                                    {
                                    "task_id": task_id,
                                        "final_status": current_status,
                                        "poll_count": poll_count,
                                        "task_data": task_data,
                                        },
                                    )

                        # Task still in progress, continue polling
                        time.sleep(self.task_poll_interval)

                    except json.JSONDecodeError:
                        return (
                            False,
                                "Task status endpoint returned invalid JSON",
                                {"status_code": response.status_code},
                                )
                else:
                    return (
                        False,
                            f"Task status check failed with status {response.status_code}",
                            {"status_code": response.status_code},
                            )

            except Exception as e:
                return (
                    False,
                        f"Error polling task status: {str(e)}",
                        {"error": str(e), "poll_count": poll_count},
                        )

        # Timeout reached
        return (
            False,
                f"Task polling timed out after {self.max_task_wait_time}s. Last status: {last_status}",
                {
                "task_id": task_id,
                    "timeout_seconds": self.max_task_wait_time,
                    "poll_count": poll_count,
                    "last_status": last_status,
                    },
                )


    def _verify_video_output_file(
        self, task_id: str
    ) -> tuple[bool, str, Dict[str, Any]]:
        """Verify that the video output file exists and is valid."""
        outputs_dir = Path("outputs")

        if not outputs_dir.exists():
            return (
                False,
                    "Outputs directory does not exist",
                    {"outputs_dir": str(outputs_dir)},
                    )

        # Look for video files related to this task
        video_extensions = [".mp4", ".avi", ".mov", ".mkv"]
        found_files = []

        for ext in video_extensions:
            # Look for files containing the task ID or recent files
            pattern_files = list(outputs_dir.glob(f"*{task_id}*{ext}"))
            found_files.extend(pattern_files)

            # Also check for recent video files (last 10 minutes)
            all_videos = list(outputs_dir.glob(f"*{ext}"))
            recent_videos = [
                f
                for f in all_videos
                if f.stat().st_mtime > (time.time() - 600)  # 10 minutes
            ]
            found_files.extend(recent_videos)

        # Remove duplicates
        found_files = list(set(found_files))

        if not found_files:
            return (
                False,
                    "No video output files found",
                    {
                    "outputs_dir": str(outputs_dir),
                        "searched_extensions": video_extensions,
                        "task_id": task_id,
                        },
                    )

        # Check the most recent file
        most_recent_file = max(found_files, key = lambda f: f.stat().st_mtime)
        file_size = most_recent_file.stat().st_size

        if file_size == 0:
            return (
                False,
                    f"Video output file is empty: {most_recent_file.name}",
                    {"file_path": str(most_recent_file), "file_size": file_size},
                    )

        return (
            True,
                f"Video output file verified: {most_recent_file.name} ({file_size} bytes)",
                {
                "file_path": str(most_recent_file),
                    "file_size": file_size,
                    "file_count": len(found_files),
                    "all_found_files": [str(f) for f in found_files],
                    },
                )

    # ========================================================================
        # MAIN SMOKE TEST EXECUTION
    # ========================================================================

    @dashboard_action(
        "Run Complete Smoke Test", "Execute comprehensive system smoke test protocol"
    )


    async def run_complete_smoke_test(self) -> SmokeTestReport:
        """
        Execute the complete system smoke test protocol.

        Returns:
            SmokeTestReport: Comprehensive test execution report
        """
        test_run_id = f"smoke - test-{int(time.time())}"
        start_time = datetime.now()
        self.test_start_time = start_time

        self.logger.info(f"Starting complete system smoke test: {test_run_id}")

        # Initialize test report
        test_results = []

        # Define all tests to execute
        test_suite = [
            # Pre - flight infrastructure checks
            (
                "port_config",
                    "Dashboard Port Configuration",
                    self._test_dashboard_port_configuration,
                    TestSeverity.CRITICAL,
                    ),
                (
                "secrets_check",
                    "Required Secrets Availability",
                    self._test_secrets_availability,
                    TestSeverity.CRITICAL,
                    ),
                (
                "disk_space",
                    "Disk Space Availability",
                    self._test_disk_space_availability,
                    TestSeverity.WARNING,
                    ),
                (
                "ffmpeg_install",
                    "FFmpeg Installation",
                    self._test_ffmpeg_installation,
                    TestSeverity.CRITICAL,
                    ),
                (
                "dir_permissions",
                    "Directory Write Permissions",
                    self._test_directory_permissions,
                    TestSeverity.CRITICAL,
                    ),
                # Live system health checks
            (
                "dashboard_health",
                    "Dashboard Health Endpoint",
                    self._test_dashboard_health_endpoint,
                    TestSeverity.CRITICAL,
                    ),
                (
                "orchestrator_health",
                    "Orchestrator Health Endpoint",
                    self._test_orchestrator_health_endpoint,
                    TestSeverity.WARNING,
                    ),
                # End - to - end workflow testing
            (
                "video_workflow",
                    "Complete Video Creation Workflow",
                    self._test_video_creation_workflow,
                    TestSeverity.CRITICAL,
                    ),
                ]

        # Execute all tests
        for test_id, test_name, test_func, severity in test_suite:
            result = self._run_test(test_id, test_name, test_func, severity)
            test_results.append(result)

            # Short pause between tests
            await asyncio.sleep(0.5)

        # Calculate final statistics
        end_time = datetime.now()
        total_duration_ms = int((end_time - start_time).total_seconds() * 1000)

        passed_tests = sum(1 for r in test_results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in test_results if r.status == TestStatus.FAILED)
        skipped_tests = sum(1 for r in test_results if r.status == TestStatus.SKIPPED)
        critical_failures = sum(
            1
            for r in test_results
            if r.status == TestStatus.FAILED and r.severity == TestSeverity.CRITICAL
        )

        # Determine overall status
        if critical_failures > 0:
            overall_status = TestStatus.FAILED
        elif failed_tests > 0:
            overall_status = (
                TestStatus.FAILED
            )  # Any failure is considered overall failure
        else:
            overall_status = TestStatus.PASSED

        # Gather system information
        system_info = {
            "dashboard_port": self.dashboard_port,
                "orchestrator_port": self.orchestrator_port,
                "python_version": os.sys.version,
                "platform": os.name,
                "working_directory": os.getcwd(),
                "environment_variables": {
                "DASHBOARD_PORT": os.getenv("DASHBOARD_PORT"),
                    "ORCHESTRATOR_PORT": os.getenv("ORCHESTRATOR_PORT"),
                    "TRAE_MASTER_KEY": "***" if os.getenv("TRAE_MASTER_KEY") else None,
                    },
                }

        # Create final report
        report = SmokeTestReport(
            test_run_id = test_run_id,
                start_time = start_time,
                end_time = end_time,
                total_duration_ms = total_duration_ms,
                total_tests = len(test_results),
                passed_tests = passed_tests,
                failed_tests = failed_tests,
                skipped_tests = skipped_tests,
                critical_failures = critical_failures,
                overall_status = overall_status,
                test_results = test_results,
                system_info = system_info,
                )

        self.current_test_run = report

        # Log final results
        if overall_status == TestStatus.PASSED:
            self.logger.info(
                f"✅ ALL TESTS PASSED. The TRAE.AI system is 100% live and fully operational."
            )
        else:
            self.logger.error(
                f"❌ SMOKE TEST FAILED. {critical_failures} critical failures, {failed_tests} total failures."
            )

        return report

    @dashboard_action(
        name="Get Test Summary",
            description="Retrieve summary of recent smoke test results and system status",
            category="System Testing",
            requires_auth = False,
            )


    def get_test_summary(self) -> Dict[str, Any]:
        """Get a summary of the current or last test run."""
        if not self.current_test_run:
            return {
                "status": "no_test_run",
                    "message": "No smoke test has been executed yet",
                    }

        report = self.current_test_run

        return {
            "test_run_id": report.test_run_id,
                "overall_status": report.overall_status.value,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat() if report.end_time else None,
                "duration_ms": report.total_duration_ms,
                "statistics": {
                "total_tests": report.total_tests,
                    "passed_tests": report.passed_tests,
                    "failed_tests": report.failed_tests,
                    "skipped_tests": report.skipped_tests,
                    "critical_failures": report.critical_failures,
                    },
                "test_results": [
                {
                    "test_id": r.test_id,
                        "name": r.name,
                        "status": r.status.value,
                        "severity": r.severity.value,
                        "duration_ms": r.duration_ms,
                        "message": r.message,
                        }
                for r in report.test_results
            ],
                }

    # ========================================================================
        # BASE AGENT IMPLEMENTATION
    # ========================================================================


    async def _execute_with_monitoring(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute smoke test with monitoring."""
        task_type = task_data.get("type", "smoke_test")

        if task_type == "smoke_test":
            report = await self.run_complete_smoke_test()
            return asdict(report)
        else:
            raise ValueError(f"Unknown task type: {task_type}")


    def _rephrase_task(self, task: str, context: Dict[str, Any]) -> str:
        """Rephrase task for smoke testing context."""
        return f"Execute system smoke test: {task}"


    def _validate_rephrase_accuracy(
        self, original: str, rephrased: str, context: Dict[str, Any]
    ) -> bool:
        """Validate rephrased task accuracy."""
        return "smoke test" in rephrased.lower() or "system test" in rephrased.lower()
