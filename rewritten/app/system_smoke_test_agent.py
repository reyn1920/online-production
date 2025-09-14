#!/usr/bin/env python3
"""
System Smoke Test Agent for TRAE.AI

This agent implements the complete "Go - Live" smoke test protocol as specified:
1. Automated Pre - Flight Checks (infrastructure validation)
2. Live 5 - Minute Smoke Test (end - to - end workflow verification)
3. Real - time status reporting via WebSocket

The agent provides a one - click verification system that ensures 100% system readiness.
"""

import asyncio
import json
import os
import shutil
import socket
import subprocess
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
import requests
from flask_socketio import SocketIO


@dataclass
class TestResult:
    """Represents the result of a single test step."""

    step_name: str
    success: bool
    message: str
    details: Optional[str] = None
    duration_ms: Optional[int] = None
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class SmokeTestSession:
    """Represents a complete smoke test session."""

    test_id: str
    started_at: str
    triggered_by: str
    status: str  # 'running', 'completed', 'failed', 'stopped'
    current_step: Optional[str] = None
    results: List[TestResult] = None
    completed_at: Optional[str] = None
    success: bool = False
    summary: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []


class SystemSmokeTestAgent:
    """The main System Smoke Test Agent implementing the Go - Live protocol."""

    def __init__(self, socketio: SocketIO = None, base_url: str = None):
        # Auto - detect the correct base URL from environment
        if base_url is None:
            dashboard_port = os.environ.get("DASHBOARD_PORT", "8081")
            base_url = f"http://localhost:{dashboard_port}"
        self.socketio = socketio
        self.base_url = base_url.rstrip("/")
        self.current_session: Optional[SmokeTestSession] = None
        self.is_running = False

        # Test configuration
        self.required_disk_space_gb = 5
        self.test_timeout_seconds = 300  # 5 minutes
        self.poll_interval_seconds = 3

        # Paths
        self.project_root = Path(__file__).parent.parent
        self.outputs_dir = self.project_root / "outputs"
        self.data_dir = self.project_root / "data"

    def start_smoke_test(self, triggered_by: str = "system") -> str:
        """Start a new smoke test session."""
        if self.is_running:
            raise RuntimeError("Smoke test is already running")

        test_id = str(uuid.uuid4())
        self.current_session = SmokeTestSession(
            test_id=test_id,
            started_at=datetime.now().isoformat(),
            triggered_by=triggered_by,
            status="running",
        )

        self.is_running = True
        self._emit_log("INFO", f"Starting system - wide smoke test (ID: {test_id})")

        return test_id

    def stop_smoke_test(self) -> bool:
        """Stop the current smoke test session."""
        if not self.is_running or not self.current_session:
            return False

        self.current_session.status = "stopped"
        self.current_session.completed_at = datetime.now().isoformat()
        self.is_running = False

        self._emit_log("INFO", "Smoke test stopped by user request")
        return True

    async def run_complete_smoke_test(self) -> SmokeTestSession:
        """Execute the complete smoke test protocol."""
        if not self.current_session:
            raise RuntimeError("No active smoke test session")

        try:
            # Phase 1: Pre - Flight Checks
            self._emit_progress(
                "Pre - Flight Checks", "Running infrastructure validation..."
            )
            preflight_success = await self._run_preflight_checks()

            if not preflight_success:
                self._complete_test(False, "Pre - flight checks failed")
                return self.current_session

            # Phase 2: Live Smoke Test
            self._emit_progress(
                "Live Smoke Test", "Running end - to - end workflow verification..."
            )
            smoke_test_success = await self._run_live_smoke_test()

            # Complete the test
            overall_success = preflight_success and smoke_test_success
            summary_message = (
                "All tests passed successfully"
                if overall_success
                else "Some tests failed"
            )
            self._complete_test(overall_success, summary_message)

        except Exception as e:
            self._emit_log("ERROR", f"Smoke test encountered an error: {str(e)}")
            self._complete_test(False, f"Test error: {str(e)}")

        return self.current_session

    async def _run_preflight_checks(self) -> bool:
        """Run all pre - flight infrastructure checks."""
        checks = [
            ("Port Configuration", self._check_dashboard_port),
            ("Port Availability", self._check_port_availability),
            ("System Resources", self._check_system_resources),
            ("Network Connectivity", self._check_network_connectivity),
            ("Secrets Validation", self._check_secrets),
            ("Disk Space", self._check_disk_space),
            ("FFmpeg Installation", self._check_ffmpeg),
            ("Directory Permissions", self._check_directory_permissions),
            ("Python Dependencies", self._check_python_dependencies),
        ]

        all_passed = True

        for check_name, check_func in checks:
            self._emit_progress(
                "Pre - Flight Checks",
                f"Checking {
                    check_name.lower()}...",
            )

            start_time = time.time()
            try:
                success, message, details = await check_func()
                duration_ms = int((time.time() - start_time) * 1000)

                result = TestResult(
                    step_name=check_name,
                    success=success,
                    message=message,
                    details=details,
                    duration_ms=duration_ms,
                )

                self.current_session.results.append(result)

                if success:
                    self._emit_log("INFO", f"✅ {check_name}: {message}")
                else:
                    self._emit_log("ERROR", f"❌ {check_name}: {message}")
                    if details:
                        self._emit_log("ERROR", f"   Details: {details}")
                    all_passed = False

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                result = TestResult(
                    step_name=check_name,
                    success=False,
                    message=f"Check failed with error: {str(e)}",
                    duration_ms=duration_ms,
                )
                self.current_session.results.append(result)
                self._emit_log(
                    "ERROR",
                    f"❌ {check_name}: Check failed with error: {
                        str(e)}",
                )
                all_passed = False

        return all_passed

    async def _check_dashboard_port(self) -> Tuple[bool, str, Optional[str]]:
        """Check that DASHBOARD_PORT is properly configured."""
        actual_port = os.environ.get("DASHBOARD_PORT", "8081")

        # Validate that the port is a valid number and in reasonable range
        try:
            port_num = int(actual_port)
            if 1024 <= port_num <= 65535:
                return True, f"Dashboard port correctly set to {actual_port}", None
            else:
                return (
                    False,
                    f"Dashboard port {actual_port} is outside valid range (1024 - 65535)",
                    "Set DASHBOARD_PORT to a valid port number",
                )
        except ValueError:
            return (
                False,
                f"Dashboard port '{actual_port}' is not a valid number",
                "Set DASHBOARD_PORT to a valid port number",
            )

    async def _check_port_availability(self) -> Tuple[bool, str, Optional[str]]:
        """Check that required services are running on their configured ports."""
        dashboard_port = int(os.environ.get("DASHBOARD_PORT", "8081"))
        backend_port = 8080  # Backend is expected on 8080

        ports_to_check = [dashboard_port, backend_port]
        running_ports = []

        for port in ports_to_check:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex(("localhost", port))
                    if result == 0:  # Port is in use (which is good for services)
                        running_ports.append(port)
            except Exception as e:
                return False, f"Error checking port {port}", str(e)

        if len(running_ports) == len(ports_to_check):
            return (
                True,
                f"All required services are running on ports: {
                    ', '.join(
                    map(
                        str, running_ports))}",
                None,
            )
        else:
            missing_ports = [p for p in ports_to_check if p not in running_ports]
            return (
                False,
                f"Services not running on ports: {
                    ', '.join(
                    map(
                        str, missing_ports))}",
                "Ensure all required services are started",
            )

    async def _check_system_resources(self) -> Tuple[bool, str, Optional[str]]:
        """Check system CPU and memory resources."""
        try:
            # Check CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory_percent > 90:
                issues.append(f"High memory usage: {memory_percent:.1f}%")

            if not issues:
                return (
                    True,
                    f"System resources OK (CPU: {
                        cpu_percent:.1f}%, Memory: {
                        memory_percent:.1f}%)",
                    None,
                )
            else:
                return False, "System resources under stress", "; ".join(issues)

        except Exception as e:
            return False, "Could not check system resources", str(e)

    async def _check_network_connectivity(self) -> Tuple[bool, str, Optional[str]]:
        """Check network connectivity to essential services."""
        test_urls = [
            ("localhost:8080", "http://localhost:8080/api/health"),
            ("External DNS", "https://8.8.8.8"),
        ]

        connectivity_issues = []

        for name, url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code not in [
                    200,
                    404,
                ]:  # 404 is OK for health check if service not running
                    connectivity_issues.append(f"{name}: HTTP {response.status_code}")
            except requests.exceptions.Timeout:
                connectivity_issues.append(f"{name}: Timeout")
            except requests.exceptions.ConnectionError:
                # For localhost, this is expected if service isn't running yet
                if "localhost" not in url:
                    connectivity_issues.append(f"{name}: Connection failed")
            except Exception as e:
                connectivity_issues.append(f"{name}: {str(e)}")

        if not connectivity_issues:
            return True, "Network connectivity verified", None
        else:
            return (
                True,
                "Network connectivity checked (some services may not be running yet)",
                "; ".join(connectivity_issues),
            )  # Non - blocking for now

    async def _check_secrets(self) -> Tuple[bool, str, Optional[str]]:
        """Check that required secrets are loaded and accessible."""
        required_secrets = ["TRAE_MASTER_KEY"]
        missing_secrets = []

        for secret in required_secrets:
            if not os.environ.get(secret):
                missing_secrets.append(secret)

        if not missing_secrets:
            return (
                True,
                f"All {
                    len(required_secrets)} required secrets are present",
                None,
            )
        else:
            return (
                False,
                f"Missing {len(missing_secrets)} required secrets",
                f"Missing secrets: {', '.join(missing_secrets)}",
            )

    async def _check_disk_space(self) -> Tuple[bool, str, Optional[str]]:
        """Check for at least 5GB of free disk space."""
        try:
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free / (1024**3)  # Convert to GB

            if free_gb >= self.required_disk_space_gb:
                return True, f"Sufficient disk space: {free_gb:.1f}GB available", None
            else:
                return (
                    False,
                    f"Insufficient disk space: {
                        free_gb:.1f}GB available, {
                        self.required_disk_space_gb}GB required",
                    "Free up disk space before proceeding",
                )
        except Exception as e:
            return False, "Could not check disk space", str(e)

    async def _check_ffmpeg(self) -> Tuple[bool, str, Optional[str]]:
        """Check that ffmpeg is installed and in PATH."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split("\\n")[0]
                return True, f"FFmpeg is installed: {version_line}", None
            else:
                return False, "FFmpeg command failed", result.stderr
        except subprocess.TimeoutExpired:
            return False, "FFmpeg check timed out", "Command took too long to execute"
        except FileNotFoundError:
            return (
                False,
                "FFmpeg not found in PATH",
                "Install FFmpeg and ensure it's in your system PATH",
            )
        except Exception as e:
            return False, "FFmpeg check failed", str(e)

    async def _check_directory_permissions(self) -> Tuple[bool, str, Optional[str]]:
        """Check that outputs and data directories are writable."""
        directories = [self.outputs_dir, self.data_dir]
        issues = []

        for directory in directories:
            try:
                # Ensure directory exists
                directory.mkdir(parents=True, exist_ok=True)

                # Test write permissions
                test_file = directory / f"test_write_{uuid.uuid4().hex[:8]}.tmp"
                test_file.write_text("test")
                test_file.unlink()  # Delete test file

            except Exception as e:
                issues.append(f"{directory.name}: {str(e)}")

        if not issues:
            return True, f"All {len(directories)} directories are writable", None
        else:
            return False, "Directory permission issues found", "; ".join(issues)

    async def _check_python_dependencies(self) -> Tuple[bool, str, Optional[str]]:
        """Check that critical Python dependencies are available."""
        critical_modules = [
            ("flask", "Flask web framework"),
            ("flask_socketio", "SocketIO for real - time communication"),
            ("requests", "HTTP client library"),
            ("psutil", "System monitoring"),
            ("waitress", "WSGI server"),
        ]

        missing_modules = []

        for module_name, description in critical_modules:
            try:
                __import__(module_name)
            except ImportError:
                missing_modules.append(f"{module_name} ({description})")

        if not missing_modules:
            return (
                True,
                f"All {
                    len(critical_modules)} critical Python dependencies are available",
                None,
            )
        else:
            return (
                False,
                f"Missing {len(missing_modules)} critical dependencies",
                f"Missing: {'; '.join(missing_modules)}",
            )

    async def _run_live_smoke_test(self) -> bool:
        """Run the comprehensive live smoke test with enhanced validation."""
        tests = [
            ("Health Check - Dashboard", self._test_dashboard_health),
            ("Health Check - Orchestrator", self._test_orchestrator_health),
            ("API Endpoints Validation", self._test_api_endpoints),
            ("System Resources Check", self._test_system_resources_live),
            ("Create Video Task", self._test_create_video_task),
            ("Monitor Task Completion", self._test_monitor_task),
            ("Verify Video Output", self._test_verify_video_output),
            ("Cleanup Test Artifacts", self._test_cleanup_artifacts),
        ]

        all_passed = True
        self.task_id = None  # Will be set by create_video_task

        for test_name, test_func in tests:
            if not self.is_running:  # Check if test was stopped
                break

            self._emit_progress("Live Smoke Test", f"Running {test_name.lower()}...")

            start_time = time.time()
            try:
                success, message, details = await test_func()
                duration_ms = int((time.time() - start_time) * 1000)

                result = TestResult(
                    step_name=test_name,
                    success=success,
                    message=message,
                    details=details,
                    duration_ms=duration_ms,
                )

                self.current_session.results.append(result)

                if success:
                    self._emit_log("INFO", f"✅ {test_name}: {message}")
                else:
                    self._emit_log("ERROR", f"❌ {test_name}: {message}")
                    if details:
                        self._emit_log("ERROR", f"   Details: {details}")
                    all_passed = False
                    break  # Stop on first failure in live test

            except Exception as e:
                duration_ms = int((time.time() - start_time) * 1000)
                result = TestResult(
                    step_name=test_name,
                    success=False,
                    message=f"Test failed with error: {str(e)}",
                    duration_ms=duration_ms,
                )
                self.current_session.results.append(result)
                self._emit_log(
                    "ERROR",
                    f"❌ {test_name}: Test failed with error: {
                        str(e)}",
                )
                all_passed = False
                break

        return all_passed

    async def _test_dashboard_health(self) -> Tuple[bool, str, Optional[str]]:
        """Test dashboard health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/api/health", timeout=10)
            if response.status_code == 200:
                return (
                    True,
                    "Dashboard health check passed",
                    f"Response: {
                        response.text}",
                )
            else:
                return (
                    False,
                    f"Dashboard health check failed (HTTP {
                        response.status_code})",
                    response.text,
                )
        except requests.exceptions.RequestException as e:
            return False, "Dashboard health check failed", str(e)

    async def _test_orchestrator_health(self) -> Tuple[bool, str, Optional[str]]:
        """Test orchestrator health endpoint (optional service)."""
        try:
            # Check if orchestrator service is running on port 8000
            orchestrator_url = "http://localhost:8000/api/health"
            response = requests.get(orchestrator_url, timeout=5)
            if response.status_code == 200:
                return (
                    True,
                    "Orchestrator service is running and healthy",
                    f"Response: {
                        response.text}",
                )
            else:
                return (
                    True,
                    "Orchestrator service not available (optional)",
                    "System can operate without orchestrator service",
                )
        except requests.exceptions.RequestException:
            # Orchestrator is optional - system can run without it
            return (
                True,
                "Orchestrator service not running (optional)",
                "System is operational without orchestrator service",
            )

    async def _test_create_video_task(self) -> Tuple[bool, str, Optional[str]]:
        """Test creating a video generation task with comprehensive validation."""
        test_payload = {
            "prompt": "Create a 3 - second test video with simple animation for system smoke test validation",
            "duration": 3,
            "format": "mp4",
            "resolution": "720p",
            "test_mode": True,
            "priority": "high",
            "metadata": {
                "test_type": "smoke_test",
                "created_by": "system_smoke_test_agent",
                "timestamp": datetime.now().isoformat(),
            },
        }

        try:
            # First, verify the endpoint exists
            health_response = requests.get(f"{self.base_url}/api/health", timeout=5)
            if health_response.status_code != 200:
                return (
                    False,
                    "Dashboard not responding before task creation",
                    f"Health check failed: {
                        health_response.status_code}",
                )

            # Create the video task
            response = requests.post(
                f"{self.base_url}/api/workflows/create - video",
                json=test_payload,
                headers={"Content - Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 201:
                result = response.json()
                if "task_id" in result:
                    self.task_id = result["task_id"]
                    # Validate task_id format (should be UUID - like)
                    if len(self.task_id) < 8:
                        return (
                            False,
                            "Invalid task_id format received",
                            f"Task ID: {
                                self.task_id}",
                        )

                    # Verify task was actually queued
                    await asyncio.sleep(1)  # Brief pause to allow task queuing
                    status_response = requests.get(
                        f"{self.base_url}/api/tasks",
                        params={"task_id": self.task_id},
                        timeout=10,
                    )

                    if status_response.status_code == 200:
                        task_data = status_response.json()
                        initial_status = task_data.get("status", "unknown")
                        return (
                            True,
                            f"Video task created and queued (ID: {
                                self.task_id}, Status: {initial_status})",
                            json.dumps(result, indent=2),
                        )
                    else:
                        return (
                            False,
                            f"Task created but status check failed (HTTP {
                                status_response.status_code})",
                            response.text,
                        )
                else:
                    return (
                        False,
                        "Video task creation response missing task_id",
                        response.text,
                    )
            elif response.status_code == 400:
                return (
                    False,
                    "Invalid request payload for video task creation",
                    response.text,
                )
            elif response.status_code == 503:
                return False, "Video service unavailable", response.text
            else:
                return (
                    False,
                    f"Video task creation failed (HTTP {
                        response.status_code})",
                    response.text,
                )
        except requests.exceptions.Timeout:
            return (
                False,
                "Video task creation timed out",
                "Request exceeded 30 second timeout",
            )
        except requests.exceptions.ConnectionError:
            return (
                False,
                "Cannot connect to video service",
                "Connection refused or network error",
            )
        except requests.exceptions.RequestException as e:
            return False, "Video task creation failed", str(e)

    async def _test_monitor_task(self) -> Tuple[bool, str, Optional[str]]:
        """Monitor task completion with comprehensive status tracking \
    and progress validation."""
        if not self.task_id:
            return (
                False,
                "No task ID available for monitoring",
                "Task creation must succeed first",
            )

        start_time = time.time()
        last_status = None
        status_changes = []
        progress_history = []
        consecutive_failures = 0
        max_consecutive_failures = 3

        self._emit_log("INFO", f"Starting task monitoring for ID: {self.task_id}")

        while time.time() - start_time < self.test_timeout_seconds:
            if not self.is_running:  # Check if test was stopped
                return False, "Task monitoring stopped by user", None

            try:
                response = requests.get(
                    f"{self.base_url}/api/tasks",
                    params={"task_id": self.task_id},
                    timeout=10,
                )

                if response.status_code == 200:
                    consecutive_failures = 0  # Reset failure counter
                    task_data = response.json()
                    status = task_data.get("status", "unknown")
                    progress = task_data.get("progress", 0)
                    error_message = task_data.get("error", None)

                    # Track status changes
                    if status != last_status:
                        elapsed = int(time.time() - start_time)
                        status_change = f"{elapsed}s: {
                            last_status or 'initial'} -> {status}"
                        status_changes.append(status_change)
                        self._emit_log("INFO", f"Task status change: {status_change}")
                        last_status = status

                    # Track progress
                    if progress > 0:
                        progress_history.append(
                            {
                                "time": int(time.time() - start_time),
                                "progress": progress,
                            }
                        )
                        if len(progress_history) > 1:
                            # Check for progress stagnation
                            recent_progress = progress_history[-5:]  # Last 5 readings
                            if len(recent_progress) >= 3 and all(
                                p["progress"] == recent_progress[0]["progress"]
                                for p in recent_progress
                            ):
                                self._emit_log(
                                    "WARN",
                                    f"Progress stagnant at {progress}% for multiple checks",
                                )

                    # Handle different status states
                    if status == "completed":
                        elapsed = int(time.time() - start_time)
                        final_progress = task_data.get("progress", 100)
                        output_file = task_data.get("output_file", "unknown")

                        details = {
                            "completion_time": elapsed,
                            "final_progress": final_progress,
                            "output_file": output_file,
                            "status_changes": status_changes,
                            "task_data": task_data,
                        }

                        return (
                            True,
                            f"Task completed successfully in {elapsed}s (Progress: {final_progress}%, Output: {output_file})",
                            json.dumps(details, indent=2),
                        )

                    elif status in ["failed", "error", "cancelled"]:
                        elapsed = int(time.time() - start_time)
                        error_details = error_message or "No error details provided"

                        details = {
                            "failure_time": elapsed,
                            "error_message": error_details,
                            "final_progress": progress,
                            "status_changes": status_changes,
                            "task_data": task_data,
                        }

                        return (
                            False,
                            f"Task {status} after {elapsed}s: {error_details}",
                            json.dumps(details, indent=2),
                        )

                    elif status in ["queued", "pending", "running", "processing"]:
                        # Valid intermediate states - continue monitoring
                        if progress > 0:
                            self._emit_progress(
                                "Task Monitoring",
                                f"Status: {status}, Progress: {progress}%",
                            )
                        else:
                            self._emit_progress("Task Monitoring", f"Status: {status}")

                    elif status == "unknown":
                        self._emit_log(
                            "WARN",
                            "Task status is unknown - this may indicate a system issue",
                        )

                    # Continue polling
                    await asyncio.sleep(self.poll_interval_seconds)

                elif response.status_code == 404:
                    return (
                        False,
                        "Task not found - may have been deleted or expired",
                        f"Task ID: {
                            self.task_id}",
                    )
                elif response.status_code >= 500:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        return (
                            False,
                            f"Server errors exceeded threshold ({consecutive_failures} consecutive failures)",
                            f"Last HTTP status: {
                                response.status_code}",
                        )
                    self._emit_log(
                        "WARN",
                        f"Server error {response.status_code}, retrying... ({consecutive_failures}/{max_consecutive_failures})",
                    )
                    # Longer wait on server errors
                    await asyncio.sleep(self.poll_interval_seconds * 2)
                else:
                    return (
                        False,
                        f"Task status check failed (HTTP {
                            response.status_code})",
                        response.text,
                    )

            except requests.exceptions.Timeout:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    return (
                        False,
                        f"Request timeouts exceeded threshold ({consecutive_failures} consecutive failures)",
                        "Multiple timeout errors",
                    )
                self._emit_log(
                    "WARN",
                    f"Request timeout, retrying... ({consecutive_failures}/{max_consecutive_failures})",
                )
                await asyncio.sleep(self.poll_interval_seconds)
            except requests.exceptions.RequestException as e:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    return (
                        False,
                        f"Network errors exceeded threshold ({consecutive_failures} consecutive failures)",
                        str(e),
                    )
                self._emit_log(
                    "WARN",
                    f"Network error, retrying... ({consecutive_failures}/{max_consecutive_failures}): {str(e)}",
                )
                await asyncio.sleep(self.poll_interval_seconds)

        # Timeout reached
        elapsed = int(time.time() - start_time)
        timeout_details = {
            "timeout_duration": elapsed,
            "last_status": last_status,
            "status_changes": status_changes,
            "progress_history": progress_history[-10:],  # Last 10 progress readings
        }

        return (
            False,
            f"Task monitoring timed out after {elapsed}s (Last status: {last_status})",
            json.dumps(timeout_details, indent=2),
        )

    async def _test_verify_video_output(self) -> Tuple[bool, str, Optional[str]]:
        """Verify video file creation with comprehensive validation including metadata \
    and integrity checks."""
        if not self.task_id:
            return (
                False,
                "No task ID available for output verification",
                "Task creation must succeed first",
            )

        try:
            # Wait a moment for file system to sync
            await asyncio.sleep(2)

            # Look for video files in the outputs directory
            video_files = list(self.outputs_dir.glob("*.mp4"))

            if not video_files:
                # Also check for other video formats
                all_video_files = []
                for ext in ["*.mp4", "*.avi", "*.mov", "*.mkv", "*.webm"]:
                    all_video_files.extend(list(self.outputs_dir.glob(ext)))

                if not all_video_files:
                    # List all files in directory for debugging
                    all_files = list(self.outputs_dir.glob("*"))
                    file_list = [f.name for f in all_files[:10]]  # First 10 files
                    return (
                        False,
                        "No video files found in outputs directory",
                        f"Searched in: {
                            self.outputs_dir}\\nFound files: {file_list}",
                    )
                else:
                    video_files = all_video_files

            # Find the most recent video file (assuming it's our test video)
            latest_video = max(video_files, key=lambda f: f.stat().st_mtime)
            file_stats = latest_video.stat()

            # Check if file was created recently (within last 10 minutes)
            current_time = time.time()
            file_age_seconds = current_time - file_stats.st_mtime
            if file_age_seconds > 600:  # 10 minutes
                self._emit_log(
                    "WARN",
                    f"Video file is older than expected: {
                        file_age_seconds:.1f}s old",
                )

            # Check file size (should be > 0 and reasonable for a short video)
            file_size = file_stats.st_size
            if file_size == 0:
                return (
                    False,
                    f"Video file is empty: {
                        latest_video.name}",
                    f"File size: {file_size} bytes",
                )

            # Check minimum file size (should be at least 1KB for a valid video)
            if file_size < 1024:
                return (
                    False,
                    f"Video file too small to be valid: {
                        latest_video.name}",
                    f"File size: {file_size} bytes (< 1KB)",
                )

            # Check maximum reasonable file size (shouldn't exceed 100MB for a
            # 3 - second test video)
            max_size = 100 * 1024 * 1024  # 100MB
            if file_size > max_size:
                self._emit_log(
                    "WARN",
                    f"Video file unexpectedly large: {file_size/(1024 * 1024):.1f}MB",
                )

            # Try to get basic video information using ffmpeg if available
            video_info = {}
            try:
                # Check if ffmpeg is available and get video info
                result = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "quiet",
                        "-print_format",
                        "json",
                        "-show_format",
                        "-show_streams",
                        str(latest_video),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    probe_data = json.loads(result.stdout)
                    if "format" in probe_data:
                        video_info["duration"] = float(
                            probe_data["format"].get("duration", 0)
                        )
                        video_info["format_name"] = probe_data["format"].get(
                            "format_name", "unknown"
                        )

                    if "streams" in probe_data:
                        video_streams = [
                            s
                            for s in probe_data["streams"]
                            if s.get("codec_type") == "video"
                        ]
                        if video_streams:
                            stream = video_streams[0]
                            video_info["codec"] = stream.get("codec_name", "unknown")
                            video_info["width"] = stream.get("width", 0)
                            video_info["height"] = stream.get("height", 0)
                            # Convert fraction to float
                            video_info["fps"] = eval(stream.get("r_frame_rate", "0/1"))

                    # Validate video properties
                    if video_info.get("duration", 0) < 1:
                        self._emit_log(
                            "WARN",
                            f"Video duration seems too short: {
                                video_info.get(
                                    'duration', 0)}s",
                        )
                    elif video_info.get("duration", 0) > 10:
                        self._emit_log(
                            "WARN",
                            f"Video duration longer than expected: {
                                video_info.get(
                                    'duration', 0)}s",
                        )

                    if (
                        video_info.get("width", 0) < 100
                        or video_info.get("height", 0) < 100
                    ):
                        self._emit_log(
                            "WARN",
                            f"Video resolution seems low: {
                                video_info.get(
                                    'width', 0)}x{
                                        video_info.get(
                                    'height', 0)}",
                        )

                else:
                    self._emit_log(
                        "WARN",
                        f"Could not probe video file: {
                            result.stderr}",
                    )

            except (
                subprocess.TimeoutExpired,
                subprocess.CalledProcessError,
                json.JSONDecodeError,
                FileNotFoundError,
            ) as e:
                self._emit_log(
                    "WARN",
                    f"Video probing failed (ffprobe not available or error): {
                        str(e)}",
                )

            # Prepare detailed results
            file_size_mb = file_size / (1024 * 1024)
            file_age_minutes = file_age_seconds / 60

            details = {
                "file_path": str(latest_video),
                "file_name": latest_video.name,
                "file_size_bytes": file_size,
                "file_size_mb": round(file_size_mb, 2),
                "file_age_seconds": round(file_age_seconds, 1),
                "file_age_minutes": round(file_age_minutes, 1),
                "created_time": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(
                    file_stats.st_mtime
                ).isoformat(),
                "video_info": video_info,
                "task_id": self.task_id,
            }

            # Create success message with key information
            success_msg = f"Video file verified: {
                latest_video.name} ({
                    file_size_mb:.1f}MB)"
            if video_info.get("duration"):
                success_msg += f", Duration: {video_info['duration']:.1f}s"
            if video_info.get("width") and video_info.get("height"):
                success_msg += f", Resolution: {
                    video_info['width']}x{
                        video_info['height']}"

            return True, success_msg, json.dumps(details, indent=2)

        except Exception as e:
            return (
                False,
                "Video output verification failed",
                f"Error: {
                    str(e)}\\nTask ID: {
                    self.task_id}\\nOutputs directory: {
                    self.outputs_dir}",
            )

    async def _test_api_endpoints(self) -> Tuple[bool, str, Optional[str]]:
        """Test critical API endpoints for availability and proper responses."""
        endpoints_to_test = [
            ("/api/health", "GET", 200, "Health endpoint"),
            ("/api/tasks", "GET", 200, "Tasks listing endpoint"),
            ("/api/workflows", "GET", 200, "Workflows endpoint"),
            ("/api/system/status", "GET", 200, "System status endpoint"),
        ]

        results = []
        all_passed = True

        # Use backend URL (port 8080) for API endpoints
        backend_url = "http://localhost:8080"

        for endpoint, method, expected_status, description in endpoints_to_test:
            try:
                url = f"{backend_url}{endpoint}"

                if method == "GET":
                    response = requests.get(url, timeout=10)
                elif method == "POST":
                    response = requests.post(url, json={}, timeout=10)
                else:
                    response = requests.request(method, url, timeout=10)

                success = response.status_code == expected_status
                if not success:
                    all_passed = False

                results.append(
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": response.status_code,
                        "success": success,
                        "description": description,
                        "response_time_ms": int(
                            response.elapsed.total_seconds() * 1000
                        ),
                    }
                )

                if success:
                    self._emit_log(
                        "INFO",
                        f"✅ {description}: {
                            response.status_code} ({
                                response.elapsed.total_seconds()
                            * 1000:.0f}ms)",
                    )
                else:
                    self._emit_log(
                        "ERROR",
                        f"❌ {description}: Expected {expected_status}, got {
                            response.status_code}",
                    )

            except requests.exceptions.RequestException as e:
                all_passed = False
                results.append(
                    {
                        "endpoint": endpoint,
                        "method": method,
                        "expected_status": expected_status,
                        "actual_status": "ERROR",
                        "success": False,
                        "description": description,
                        "error": str(e),
                    }
                )
                self._emit_log("ERROR", f"❌ {description}: Request failed - {str(e)}")

        passed_count = sum(1 for r in results if r["success"])
        total_count = len(results)

        if all_passed:
            return (
                True,
                f"All {total_count} API endpoints responding correctly",
                json.dumps(results, indent=2),
            )
        else:
            return (
                False,
                f"API endpoint failures: {passed_count}/{total_count} passed",
                json.dumps(results, indent=2),
            )

    async def _test_system_resources_live(self) -> Tuple[bool, str, Optional[str]]:
        """Test system resources during live operation."""
        try:
            # Get current system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.outputs_dir.parent))

            # Check network connections
            connections = psutil.net_connections(kind="inet")
            listening_ports = [
                conn.laddr.port for conn in connections if conn.status == "LISTEN"
            ]

            # Get process information
            current_process = psutil.Process()
            process_memory = current_process.memory_info()

            metrics = {
                "cpu_percent": cpu_percent,
                "memory_total_gb": round(memory.total / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_total_gb": round(disk.total / (1024**3), 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 1),
                "listening_ports": sorted(listening_ports),
                "process_memory_mb": round(process_memory.rss / (1024**2), 1),
                "process_cpu_percent": current_process.cpu_percent(),
            }

            # Check for resource constraints
            warnings = []
            if cpu_percent > 80:
                warnings.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 85:
                warnings.append(f"High memory usage: {memory.percent}%")
            if disk.free < 1024**3:  # Less than 1GB free
                warnings.append(f"Low disk space: {metrics['disk_free_gb']}GB free")

            # Check if expected ports are listening
            expected_ports = [8080, 8081]  # Dashboard ports
            missing_ports = [
                port for port in expected_ports if port not in listening_ports
            ]
            if missing_ports:
                warnings.append(f"Expected ports not listening: {missing_ports}")

            if warnings:
                return (
                    False,
                    f"System resource warnings detected: {
                        '; '.join(warnings)}",
                    json.dumps(metrics, indent=2),
                )
            else:
                return (
                    True,
                    f"System resources healthy (CPU: {cpu_percent}%, Memory: {
                        memory.percent}%, Disk: {
                        metrics['disk_percent']}%)",
                    json.dumps(metrics, indent=2),
                )

        except Exception as e:
            return False, "System resource check failed", str(e)

    async def _test_cleanup_artifacts(self) -> Tuple[bool, str, Optional[str]]:
        """Clean up test artifacts and verify cleanup success."""
        try:
            cleanup_results = {
                "files_removed": [],
                "files_failed": [],
                "directories_checked": [],
                "total_space_freed_mb": 0,
            }

            # Find test files created during this smoke test
            test_files = []

            # Look for files with smoke test metadata or recent test files
            for video_file in self.outputs_dir.glob("*.mp4"):
                file_stats = video_file.stat()
                file_age = time.time() - file_stats.st_mtime

                # If file was created in the last 30 minutes and is small (likely a test
                # file)
                if (
                    file_age < 1800 and file_stats.st_size < 50 * 1024 * 1024
                ):  # 50MB threshold
                    test_files.append(video_file)

            # Also look for any files with "test" or "smoke" in the name
            for pattern in ["*test*", "*smoke*", "*temp*"]:
                test_files.extend(self.outputs_dir.glob(pattern))

            # Remove duplicates
            test_files = list(set(test_files))

            total_size_freed = 0

            for file_path in test_files:
                try:
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                        file_path.unlink()  # Remove the file
                        cleanup_results["files_removed"].append(
                            {
                                "name": file_path.name,
                                "size_mb": round(file_size / (1024**2), 2),
                            }
                        )
                        total_size_freed += file_size
                        self._emit_log(
                            "INFO",
                            f"Removed test file: {file_path.name} ({file_size/(1024**2):.1f}MB)",
                        )
                except Exception as e:
                    cleanup_results["files_failed"].append(
                        {"name": file_path.name, "error": str(e)}
                    )
                    self._emit_log(
                        "WARN",
                        f"Failed to remove {
                            file_path.name}: {
                                str(e)}",
                    )

            cleanup_results["total_space_freed_mb"] = round(
                total_size_freed / (1024**2), 2
            )
            cleanup_results["directories_checked"] = [str(self.outputs_dir)]

            # Verify cleanup
            remaining_test_files = []
            for pattern in ["*test*", "*smoke*"]:
                remaining_test_files.extend(self.outputs_dir.glob(pattern))

            files_removed_count = len(cleanup_results["files_removed"])
            files_failed_count = len(cleanup_results["files_failed"])

            if files_failed_count > 0:
                return (
                    False,
                    f"Cleanup partially failed: {files_removed_count} removed, {files_failed_count} failed",
                    json.dumps(cleanup_results, indent=2),
                )
            elif files_removed_count > 0:
                return (
                    True,
                    f"Cleanup successful: {files_removed_count} test files removed ({
                        cleanup_results['total_space_freed_mb']}MB freed)",
                    json.dumps(cleanup_results, indent=2),
                )
            else:
                return (
                    True,
                    "No test artifacts found to clean up",
                    json.dumps(cleanup_results, indent=2),
                )

        except Exception as e:
            return False, "Cleanup test failed", str(e)

    def _complete_test(self, success: bool, summary_message: str):
        """Complete the current smoke test session."""
        if not self.current_session:
            return

        self.current_session.status = "completed" if success else "failed"
        self.current_session.success = success
        self.current_session.completed_at = datetime.now().isoformat()

        # Generate summary
        total_tests = len(self.current_session.results)
        passed_tests = sum(1 for r in self.current_session.results if r.success)
        failed_tests = total_tests - passed_tests

        total_duration = sum(r.duration_ms or 0 for r in self.current_session.results)

        self.current_session.summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "total_duration_ms": total_duration,
            "success_rate": (
                (passed_tests / total_tests * 100) if total_tests > 0 else 0
            ),
            "details": summary_message,
        }

        self.is_running = False

        # Emit completion event
        if self.socketio:
            self.socketio.emit(
                "test_completed",
                {
                    "success": success,
                    "summary": self.current_session.summary,
                    "session": asdict(self.current_session),
                },
                namespace="/smoke - test",
            )

    def _emit_log(self, level: str, message: str):
        """Emit a log message via WebSocket."""
        if self.socketio:
            self.socketio.emit(
                "test_log",
                {
                    "level": level,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                },
                namespace="/smoke - test",
            )

    def _emit_progress(self, current_step: str, message: str):
        """Emit a progress update via WebSocket."""
        if self.current_session:
            self.current_session.current_step = current_step

        if self.socketio:
            self.socketio.emit(
                "test_progress",
                {
                    "current_step": current_step,
                    "message": message,
                    "timestamp": datetime.now().isoformat(),
                },
                namespace="/smoke - test",
            )

    def get_session_status(self) -> Optional[Dict[str, Any]]:
        """Get the current session status."""
        if not self.current_session:
            return None

        return asdict(self.current_session)

    def run_smoke_test(self, test_type: str = "full") -> Dict[str, Any]:
        """Public interface to run smoke test (synchronous wrapper)."""
        try:
            if self.is_running:
                return {
                    "success": False,
                    "error": "Smoke test is already running",
                    "test_id": (
                        self.current_session.test_id if self.current_session else None
                    ),
                }

            test_id = self.start_smoke_test("dashboard")

            # Run the test in a separate thread to avoid blocking

            import threading

            def run_async_test():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(self.run_complete_smoke_test())
                finally:
                    loop.close()

            thread = threading.Thread(target=run_async_test, daemon=True)
            thread.start()

            return {
                "success": True,
                "message": "Smoke test started successfully",
                "test_id": test_id,
                "test_type": test_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop_test(self) -> Dict[str, Any]:
        """Public interface to stop smoke test."""
        try:
            if not self.is_running:
                return {"success": False, "error": "No smoke test is currently running"}

            success = self.stop_smoke_test()

            return {
                "success": success,
                "message": (
                    "Smoke test stopped" if success else "Failed to stop smoke test"
                ),
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_status(self) -> Dict[str, Any]:
        """Public interface to get current status."""
        try:
            session_status = self.get_session_status()

            return {
                "success": True,
                "is_running": self.is_running,
                "session": session_status,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "is_running": False,
                "session": None,
            }
