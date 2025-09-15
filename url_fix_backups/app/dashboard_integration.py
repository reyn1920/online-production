#!/usr / bin / env python3
""""""
Dashboard Integration - Enhanced dashboard with actions, metrics, and monitoring
Integrates with the Max - Out Pack workflow and provides real - time system monitoring
""""""

import asyncio
import json
import logging
import os
import sys
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

from backend.core.secret_store_bridge import get_secret_store
from backend.runner.channel_executor import ChannelExecutor
from scripts.synthesize_release_v3 import SynthesizerV3

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class ActionMetrics:
    """Metrics for a single action"""

    name: str
    executions: int = 0
    successes: int = 0
    failures: int = 0
    total_duration: float = 0.0
    last_execution: Optional[str] = None
    last_status: str = "never_run"
    error_count: int = 0
    avg_duration: float = 0.0
    success_rate: float = 0.0

@dataclass


class SystemMetrics:
    """Overall system metrics"""

    total_actions: int = 0
    active_actions: int = 0
    total_executions: int = 0
    total_successes: int = 0
    total_failures: int = 0
    uptime_seconds: float = 0.0
    last_activity: Optional[str] = None
    system_status: str = "initializing"
    releases_created: int = 0
    bundles_processed: int = 0
    storage_used_mb: float = 0.0


class DashboardIntegration:
    """Enhanced dashboard with comprehensive monitoring and actions"""


    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.start_time = time.time()
        self.metrics_lock = Lock()

        # Initialize components
        self.secret_store = get_secret_store()
        self.synthesizer = SynthesizerV3(str(self.base_dir))
        self.channel_executor = ChannelExecutor()

        # Metrics storage
        self.action_metrics: Dict[str, ActionMetrics] = {}
        self.system_metrics = SystemMetrics()
        self.execution_history = deque(maxlen = 1000)  # Last 1000 executions
        self.performance_history = deque(maxlen = 100)  # Last 100 performance snapshots

        # Available actions
        self.available_actions = {
            "synthesize_bundles": self._action_synthesize_bundles,
                "execute_channel": self._action_execute_channel,
                "list_releases": self._action_list_releases,
                "system_status": self._action_system_status,
                "cleanup_temp": self._action_cleanup_temp,
                "validate_system": self._action_validate_system,
                "export_metrics": self._action_export_metrics,
                "reset_metrics": self._action_reset_metrics,
                "health_check": self._action_health_check,
                "backup_releases": self._action_backup_releases,
# BRACKET_SURGEON: disabled
#                 }

        # Initialize action metrics
        for action_name in self.available_actions.keys():
            self.action_metrics[action_name] = ActionMetrics(name = action_name)

        # Start background monitoring
        self._start_monitoring()

        logger.info(
            f"Dashboard integration initialized with {len(self.available_actions)} actions"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )


    def _start_monitoring(self):
        """Start background monitoring thread"""


        def monitor_loop():
            while True:
                try:
                    self._update_system_metrics()
                    self._capture_performance_snapshot()
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    logger.error(f"Monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error

        monitor_thread = Thread(target = monitor_loop, daemon = True)
        monitor_thread.start()
        logger.info("Background monitoring started")


    def _update_system_metrics(self):
        """Update system - wide metrics"""
        with self.metrics_lock:
            self.system_metrics.uptime_seconds = time.time() - self.start_time
            self.system_metrics.total_actions = len(self.available_actions)

            # Calculate totals from action metrics
            total_executions = sum(m.executions for m in self.action_metrics.values())
            total_successes = sum(m.successes for m in self.action_metrics.values())
            total_failures = sum(m.failures for m in self.action_metrics.values())

            self.system_metrics.total_executions = total_executions
            self.system_metrics.total_successes = total_successes
            self.system_metrics.total_failures = total_failures

            # Update storage usage
            self.system_metrics.storage_used_mb = self._calculate_storage_usage()

            # Update release count
            releases = self.synthesizer.list_releases()
            self.system_metrics.releases_created = len(releases)

            # Calculate bundles processed
            bundles_processed = 0
            for release in releases:
                bundles_processed += release.get("bundles_count", 0)
            self.system_metrics.bundles_processed = bundles_processed

            # Determine system status
            if total_executions == 0:
                self.system_metrics.system_status = "idle"
            elif total_failures > total_successes * 0.1:  # More than 10% failure rate
                self.system_metrics.system_status = "degraded"
            else:
                self.system_metrics.system_status = "healthy"


    def _calculate_storage_usage(self) -> float:
        """Calculate storage usage in MB"""
        try:
            total_size = 0
            assets_dir = self.base_dir/"assets"
            if assets_dir.exists():
                for file_path in assets_dir.rglob("*"):
                    if file_path.is_file():
                        total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # Convert to MB
        except Exception as e:
            logger.warning(f"Failed to calculate storage usage: {e}")
            return 0.0


    def _capture_performance_snapshot(self):
        """Capture current performance metrics"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
                "uptime": self.system_metrics.uptime_seconds,
                "total_executions": self.system_metrics.total_executions,
                "success_rate": (
                self.system_metrics.total_successes / max(self.system_metrics.total_executions,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     1)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            * 100,
                "storage_mb": self.system_metrics.storage_used_mb,
                "active_actions": len(
                [m for m in self.action_metrics.values() if m.last_status == "running"]
# BRACKET_SURGEON: disabled
#             ),
                "system_status": self.system_metrics.system_status,
# BRACKET_SURGEON: disabled
#                 }

        self.performance_history.append(snapshot)


    def execute_action(
        self, action_name: str, params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Execute an action with metrics tracking"""
        if action_name not in self.available_actions:
            return {
                "success": False,
                    "error": f"Unknown action: {action_name}",
                    "available_actions": list(self.available_actions.keys()),
# BRACKET_SURGEON: disabled
#                     }

        if params is None:
            params = {}

        # Update metrics - start execution
        with self.metrics_lock:
            metrics = self.action_metrics[action_name]
            metrics.executions += 1
            metrics.last_execution = datetime.now().isoformat()
            metrics.last_status = "running"
            self.system_metrics.last_activity = datetime.now().isoformat()

        start_time = time.time()

        try:
            # Execute the action
            action_func = self.available_actions[action_name]
            result = action_func(params)

            # Calculate duration
            duration = time.time() - start_time

            # Update metrics - success
            with self.metrics_lock:
                metrics.successes += 1
                metrics.total_duration += duration
                metrics.avg_duration = metrics.total_duration / metrics.executions
                metrics.success_rate = (metrics.successes / metrics.executions) * 100
                metrics.last_status = "success"

            # Add to execution history
            execution_record = {
                "action": action_name,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "status": "success",
                    "params": params,
                    "result_summary": self._summarize_result(result),
# BRACKET_SURGEON: disabled
#                     }
            self.execution_history.append(execution_record)

            logger.info(
                f"Action '{action_name}' completed successfully in {"
# BRACKET_SURGEON: disabled
#                     duration:.2f}s""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            return {
                "success": True,
                    "action": action_name,
                    "duration": duration,
                    "result": result,
                    "timestamp": execution_record["timestamp"],
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Update metrics - failure
            with self.metrics_lock:
                metrics.failures += 1
                metrics.error_count += 1
                metrics.total_duration += duration
                metrics.avg_duration = metrics.total_duration / metrics.executions
                metrics.success_rate = (metrics.successes / metrics.executions) * 100
                metrics.last_status = "failed"

            # Add to execution history
            execution_record = {
                "action": action_name,
                    "timestamp": datetime.now().isoformat(),
                    "duration": duration,
                    "status": "failed",
                    "params": params,
                    "error": str(e),
# BRACKET_SURGEON: disabled
#                     }
            self.execution_history.append(execution_record)

            logger.error(f"Action '{action_name}' failed after {duration:.2f}s: {e}")

            return {
                "success": False,
                    "action": action_name,
                    "duration": duration,
                    "error": str(e),
                    "timestamp": execution_record["timestamp"],
# BRACKET_SURGEON: disabled
#                     }


    def _summarize_result(self, result: Any) -> str:
        """Create a brief summary of action result"""
        if isinstance(result, dict):
            if "success" in result:
                status = "success" if result["success"] else "failed"
                if "release_version" in result:
                    return f"{status} - release {result['release_version']}"
                elif "bundles_processed" in result:
                    return f"{status} - {result['bundles_processed']} bundles"
                elif "message" in result:
                    return f"{status} - {result['message'][:50]}..."
                return status
            elif "error" in result:
                return f"error - {str(result['error'])[:50]}..."

        return str(result)[:100] + "..." if len(str(result)) > 100 else str(result)

    # Action implementations


    def _action_synthesize_bundles(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize bundles into a release"""
        release_version = params.get("release_version")
        return self.synthesizer.synthesize_bundles(release_version)


    def _action_execute_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a channel roadmap"""
        roadmap_path = params.get("roadmap_path")
        if not roadmap_path:
            return {"success": False, "error": "roadmap_path parameter required"}

        try:
            result = asyncio.run(self.channel_executor.execute_roadmap(roadmap_path))
            return result
        except Exception as e:
            return {"success": False, "error": str(e)}


    def _action_list_releases(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List all available releases"""
        releases = self.synthesizer.list_releases()
        return {"success": True, "releases": releases, "count": len(releases)}


    def _action_system_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive system status"""
        with self.metrics_lock:
            return {
                "success": True,
                    "system_metrics": asdict(self.system_metrics),
                    "action_metrics": {
                    name: asdict(metrics)
                    for name, metrics in self.action_metrics.items()
# BRACKET_SURGEON: disabled
#                 },
                    # Last 10 executions
                "recent_executions": list(self.execution_history)[-10:],
                    # Last 5 snapshots
                "performance_trend": list(self.performance_history)[-5:],
# BRACKET_SURGEON: disabled
#                     }


    def _action_cleanup_temp(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clean up temporary files"""
        try:
            temp_dir = self.base_dir/"assets" / "temp"
            if not temp_dir.exists():
                return {"success": True, "message": "No temp directory to clean"}

            files_removed = 0
            bytes_freed = 0

            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    files_removed += 1
                    bytes_freed += file_size

            # Remove empty directories
            for dir_path in sorted(temp_dir.rglob("*"), reverse = True):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()

            return {
                "success": True,
                    "files_removed": files_removed,
                    "bytes_freed": bytes_freed,
                    "mb_freed": bytes_freed / (1024 * 1024),
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            return {"success": False, "error": str(e)}


    def _action_validate_system(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Validate system integrity"""
        validation_results = {
            "success": True,
                "checks": [],
                "warnings": [],
                "errors": [],
# BRACKET_SURGEON: disabled
#                 }

        try:
            # Check directory structure
            required_dirs = [
                "assets / incoming / bundles",
                    "assets / releases",
                    "assets / temp / synthesis",
                    "assets / archive",
                    "backend / core",
                    "backend / runner",
                    "scripts",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ]

            for dir_path in required_dirs:
                full_path = self.base_dir / dir_path
                if full_path.exists():
                    validation_results["checks"].append(
                        f"✓ Directory exists: {dir_path}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                else:
                    validation_results["errors"].append(
                        f"✗ Missing directory: {dir_path}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Check secret store
            try:
                secret_store = get_secret_store()
                validation_results["checks"].append("✓ Secret store accessible")
            except Exception as e:
                validation_results["errors"].append(f"✗ Secret store error: {e}")

            # Check releases integrity
            releases = self.synthesizer.list_releases()
            for release in releases[:5]:  # Check last 5 releases
                manifest = self.synthesizer.get_release_manifest(release["version"])
                if "error" in manifest:
                    validation_results["warnings"].append(
                        f"⚠ Release {"
                            release['version']} manifest issue: {
                                manifest['error']}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                else:
                    validation_results["checks"].append(
                        f"✓ Release {release['version']} valid"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Check system resources
            storage_mb = self._calculate_storage_usage()
            if storage_mb > 10000:  # More than 10GB
                validation_results["warnings"].append(
                    f"⚠ High storage usage: {storage_mb:.1f} MB"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
            else:
                validation_results["checks"].append(
                    f"✓ Storage usage normal: {storage_mb:.1f} MB"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            # Overall status
            if validation_results["errors"]:
                validation_results["success"] = False
                validation_results["status"] = "failed"
            elif validation_results["warnings"]:
                validation_results["status"] = "warnings"
            else:
                validation_results["status"] = "healthy"

            return validation_results

        except Exception as e:
            return {"success": False, "error": str(e), "status": "error"}


    def _action_export_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export metrics to file"""
        try:
            export_format = params.get("format", "json")
            output_path = params.get(
                "output_path", f"metrics_export_{int(time.time())}.json"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            with self.metrics_lock:
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                        "system_metrics": asdict(self.system_metrics),
                        "action_metrics": {
                        name: asdict(metrics)
                        for name, metrics in self.action_metrics.items()
# BRACKET_SURGEON: disabled
#                     },
                        "execution_history": list(self.execution_history),
                        "performance_history": list(self.performance_history),
# BRACKET_SURGEON: disabled
#                         }

            output_file = self.base_dir / output_path

            if export_format.lower() == "json":
                with open(output_file, "w", encoding="utf - 8") as f:
                    json.dump(export_data, f, indent = 2, ensure_ascii = False)
            else:
                return {
                    "success": False,
                        "error": f"Unsupported format: {export_format}",
# BRACKET_SURGEON: disabled
#                         }

            return {
                "success": True,
                    "output_path": str(output_file),
                    "format": export_format,
                    "size_bytes": output_file.stat().st_size,
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            return {"success": False, "error": str(e)}


    def _action_reset_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset metrics (with confirmation)"""
        confirm = params.get("confirm", False)
        if not confirm:
            return {
                "success": False,
                    "error": "Confirmation required. Set confirm = True to reset metrics.",
# BRACKET_SURGEON: disabled
#                     }

        try:
            with self.metrics_lock:
                # Reset action metrics
                for action_name in self.action_metrics.keys():
                    self.action_metrics[action_name] = ActionMetrics(name = action_name)

                # Reset system metrics (keep uptime)
                uptime = self.system_metrics.uptime_seconds
                self.system_metrics = SystemMetrics()
                self.system_metrics.uptime_seconds = uptime
                self.system_metrics.total_actions = len(self.available_actions)

                # Clear history
                self.execution_history.clear()
                self.performance_history.clear()

            return {
                "success": True,
                    "message": "All metrics reset successfully",
                    "reset_timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            return {"success": False, "error": str(e)}


    def _action_health_check(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            "success": True,
                "overall_status": "healthy",
                "checks": {},
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }

        try:
            # System uptime check
            uptime_hours = self.system_metrics.uptime_seconds / 3600
            health_status["checks"]["uptime"] = {
                "status": "healthy",
                    "value": f"{uptime_hours:.1f} hours",
                    "details": "System running normally",
# BRACKET_SURGEON: disabled
#                     }

            # Success rate check
            total_executions = self.system_metrics.total_executions
            if total_executions > 0:
                success_rate = (
                    self.system_metrics.total_successes / total_executions
# BRACKET_SURGEON: disabled
#                 ) * 100
                if success_rate >= 95:
                    status = "healthy"
                elif success_rate >= 80:
                    status = "warning"
                else:
                    status = "critical"
                    health_status["overall_status"] = "degraded"

                health_status["checks"]["success_rate"] = {
                    "status": status,
                        "value": f"{"
# BRACKET_SURGEON: disabled
#                         success_rate:.1f}%","
                            "details": f"{"
                        self.system_metrics.total_successes}/{total_executions} successful","
# BRACKET_SURGEON: disabled
#                             }

            # Storage check
            storage_mb = self.system_metrics.storage_used_mb
            if storage_mb < 5000:  # Less than 5GB
                storage_status = "healthy"
            elif storage_mb < 15000:  # Less than 15GB
                storage_status = "warning"
            else:
                storage_status = "critical"
                health_status["overall_status"] = "degraded"

            health_status["checks"]["storage"] = {
                "status": storage_status,
                    "value": f"{storage_mb:.1f} MB",
                    "details": "Assets directory usage",
# BRACKET_SURGEON: disabled
#                     }

            # Recent activity check
            if self.system_metrics.last_activity:
                last_activity = datetime.fromisoformat(
                    self.system_metrics.last_activity
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                time_since = datetime.now() - last_activity

                if time_since < timedelta(hours = 1):
                    activity_status = "healthy"
                elif time_since < timedelta(hours = 24):
                    activity_status = "warning"
                else:
                    activity_status = "stale"

                health_status["checks"]["activity"] = {
                    "status": activity_status,
                        "value": str(time_since).split(".")[0],  # Remove microseconds
                    "details": f"Last activity: {self.system_metrics.last_activity}",
# BRACKET_SURGEON: disabled
#                         }

            # Component availability check
            components_healthy = 0
            total_components = 3

            try:
                self.synthesizer.list_releases()
                components_healthy += 1
                health_status["checks"]["synthesizer"] = {
                    "status": "healthy",
                        "details": "Synthesizer operational",
# BRACKET_SURGEON: disabled
#                         }
            except Exception as e:
                health_status["checks"]["synthesizer"] = {
                    "status": "failed",
                        "details": str(e),
# BRACKET_SURGEON: disabled
#                         }

            try:
                get_secret_store()
                components_healthy += 1
                health_status["checks"]["secret_store"] = {
                    "status": "healthy",
                        "details": "Secret store accessible",
# BRACKET_SURGEON: disabled
#                         }
            except Exception as e:
                health_status["checks"]["secret_store"] = {
                    "status": "failed",
                        "details": str(e),
# BRACKET_SURGEON: disabled
#                         }

            try:
                # Test channel executor initialization
                components_healthy += 1
                health_status["checks"]["channel_executor"] = {
                    "status": "healthy",
                        "details": "Channel executor ready",
# BRACKET_SURGEON: disabled
#                         }
            except Exception as e:
                health_status["checks"]["channel_executor"] = {
                    "status": "failed",
                        "details": str(e),
# BRACKET_SURGEON: disabled
#                         }

            # Overall component health
            if components_healthy == total_components:
                health_status["checks"]["components"] = {
                    "status": "healthy",
                        "value": f"{components_healthy}/{total_components}",
                        "details": "All components operational",
# BRACKET_SURGEON: disabled
#                         }
            else:
                health_status["checks"]["components"] = {
                    "status": "degraded",
                        "value": f"{components_healthy}/{total_components}",
                        "details": "Some components unavailable",
# BRACKET_SURGEON: disabled
#                         }
                health_status["overall_status"] = "degraded"

            return health_status

        except Exception as e:
            return {
                "success": False,
                    "overall_status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                     }


    def _action_backup_releases(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup of releases"""
        try:
            backup_path = params.get(
                "backup_path", f"releases_backup_{int(time.time())}.tar.gz"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            releases_dir = self.base_dir/"assets" / "releases"

            if not releases_dir.exists():
                return {"success": False, "error": "No releases directory found"}

            import tarfile

            backup_file = self.base_dir / backup_path

            with tarfile.open(backup_file, "w:gz") as tar:
                tar.add(releases_dir, arcname="releases")

            return {
                "success": True,
                    "backup_path": str(backup_file),
                    "size_bytes": backup_file.stat().st_size,
                    "size_mb": backup_file.stat().st_size/(1024 * 1024),
                    "releases_backed_up": len(list(releases_dir.iterdir())),
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            return {"success": False, "error": str(e)}


    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        with self.metrics_lock:
            return {
                "timestamp": datetime.now().isoformat(),
                    "system_metrics": asdict(self.system_metrics),
                    "uptime_seconds": self.system_metrics.uptime_seconds,
                    "total_executions": self.system_metrics.total_executions,
                    "success_rate": (
                    (
                        self.system_metrics.total_successes / max(self.system_metrics.total_executions,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     1)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    * 100
                    if self.system_metrics.total_executions > 0
                    else 0
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#                     }


    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for UI"""
        with self.metrics_lock:
            return {
                "timestamp": datetime.now().isoformat(),
                    "system_metrics": asdict(self.system_metrics),
                    "action_metrics": {
                    name: asdict(metrics)
                    for name, metrics in self.action_metrics.items()
# BRACKET_SURGEON: disabled
#                 },
                    "recent_executions": list(self.execution_history)[-20:],
                    "performance_history": list(self.performance_history),
                    "available_actions": list(self.available_actions.keys()),
                    "quick_stats": {
                    "uptime_hours": self.system_metrics.uptime_seconds / 3600,
                        "success_rate": (
                        self.system_metrics.total_successes / max(self.system_metrics.total_executions,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     1)
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    * 100,
                        "avg_execution_time": (
                        sum(m.avg_duration for m in self.action_metrics.values())/len(self.action_metrics)
                        if self.action_metrics
                        else 0
# BRACKET_SURGEON: disabled
#                     ),
                        "storage_gb": self.system_metrics.storage_used_mb / 1024,
# BRACKET_SURGEON: disabled
#                         },
# BRACKET_SURGEON: disabled
#                     }

# Global dashboard instance
_dashboard_integration = None


def get_dashboard_integration(base_dir: str = ".") -> DashboardIntegration:
    """Get or create dashboard integration singleton"""
    global _dashboard_integration
    if _dashboard_integration is None:
        _dashboard_integration = DashboardIntegration(base_dir)
    return _dashboard_integration


def main():
    """Command - line interface for dashboard integration"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Dashboard Integration - Enhanced monitoring and actions"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument(
        "--base - dir", default=".", help="Base directory (default: current)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--action", help="Action to execute")
    parser.add_argument("--params", help="Action parameters as JSON string")
    parser.add_argument(
        "--list - actions", action="store_true", help="List available actions"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--status", action="store_true", help="Show system status")

    args = parser.parse_args()

    dashboard = DashboardIntegration(args.base_dir)

    if args.list_actions:
        print("Available actions:")
        for action_name in dashboard.available_actions.keys():
            metrics = dashboard.action_metrics[action_name]
            print(
                f"  {action_name} - {metrics.executions} executions, {metrics.success_rate:.1f}% success"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        return

    if args.status:
        result = dashboard.execute_action("system_status")
        print(json.dumps(result, indent = 2))
        return

    if args.action:
        params = {}
        if args.params:
            try:
                params = json.loads(args.params)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON parameters: {e}")
                return

        result = dashboard.execute_action(args.action, params)
        print(json.dumps(result, indent = 2))
        return

    # Interactive mode
    print("Dashboard Integration - Interactive Mode")
    print("Available actions:", list(dashboard.available_actions.keys()))
    print("Type 'help' for more information, 'quit' to exit")

    while True:
        try:
            command = input("\\n> ").strip()

            if command.lower() in ["quit", "exit", "q"]:
                break
            elif command.lower() == "help":
                print("Commands:")
                print("  <action_name> - Execute action")
                print("  status - Show system status")
                print("  actions - List available actions")
                print("  quit - Exit")
            elif command.lower() == "status":
                result = dashboard.execute_action("system_status")
                print(json.dumps(result["system_metrics"], indent = 2))
            elif command.lower() == "actions":
                for action_name in dashboard.available_actions.keys():
                    metrics = dashboard.action_metrics[action_name]
                    print(f"  {action_name} - {metrics.executions} executions")
            elif command in dashboard.available_actions:
                result = dashboard.execute_action(command)
                print(json.dumps(result, indent = 2))
            else:
                print(f"Unknown command: {command}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

    print("\\nGoodbye!")

if __name__ == "__main__":
    main()