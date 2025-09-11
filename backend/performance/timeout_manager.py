#!/usr/bin/env python3
"""
Timeout and Performance Manager for ChatGPT Integration
Implements Rule 6: Timeout Configuration and Rule 10: Performance Requirements
"""

import asyncio
import functools
import json
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union

import aiohttp
from audit_logger import AuditLevel, audit_logger


class TimeoutType(Enum):
    """Types of timeout configurations"""

    API_REQUEST = "api_request"
    WEBHOOK = "webhook"
    DATABASE = "database"
    CACHE = "cache"
    FILE_OPERATION = "file_operation"
    COMPUTATION = "computation"


class PerformanceLevel(Enum):
    """Performance requirement levels"""

    EXCELLENT = "excellent"  # < 1s
    GOOD = "good"  # 1-3s
    ACCEPTABLE = "acceptable"  # 3-5s
    SLOW = "slow"  # 5-10s
    CRITICAL = "critical"  # > 10s


@dataclass
class TimeoutConfig:
    """Timeout configuration for different operation types"""

    operation_type: TimeoutType
    default_timeout: float
    max_timeout: float
    retry_attempts: int
    retry_delay: float
    circuit_breaker_threshold: int
    performance_target: float


@dataclass
class PerformanceMetric:
    """Performance measurement data"""

    operation_id: str
    operation_type: TimeoutType
    start_time: float
    end_time: float
    duration: float
    success: bool
    timeout_occurred: bool
    retry_count: int
    error_message: Optional[str]
    performance_level: PerformanceLevel


class CircuitBreaker:
    """Circuit breaker for failing operations"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def can_execute(self) -> bool:
        """Check if operation can be executed"""
        if self.state == "closed":
            return True
        elif self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
                return True
            return False
        else:  # half-open
            return True

    def record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"


class TimeoutManager:
    """Comprehensive timeout and performance management system"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)

        self.timeout_configs = self._initialize_timeout_configs()
        self.circuit_breakers = {}
        self.performance_metrics = []
        self.active_operations = {}

        # Performance tracking
        self.response_times = {timeout_type: [] for timeout_type in TimeoutType}

        # Setup logging
        self.logger = logging.getLogger("timeout_manager")
        self.logger.setLevel(logging.INFO)

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default timeout configuration"""
        return {
            "chatgpt_api_timeout": 30.0,  # Rule 6: 30 second timeout
            "webhook_timeout": 10.0,
            "database_timeout": 5.0,
            "cache_timeout": 2.0,
            "file_operation_timeout": 15.0,
            "computation_timeout": 60.0,
            "performance_target_p95": 5.0,  # Rule 10: 5 second P95
            "performance_target_p99": 10.0,
            "circuit_breaker_enabled": True,
            "retry_enabled": True,
            "performance_monitoring": True,
            "alert_slow_operations": True,
        }

    def _initialize_timeout_configs(self) -> Dict[TimeoutType, TimeoutConfig]:
        """Initialize timeout configurations for different operation types"""
        configs = {
            TimeoutType.API_REQUEST: TimeoutConfig(
                operation_type=TimeoutType.API_REQUEST,
                default_timeout=self.config["chatgpt_api_timeout"],
                max_timeout=60.0,
                retry_attempts=3,
                retry_delay=1.0,
                circuit_breaker_threshold=5,
                performance_target=5.0,
            ),
            TimeoutType.WEBHOOK: TimeoutConfig(
                operation_type=TimeoutType.WEBHOOK,
                default_timeout=self.config["webhook_timeout"],
                max_timeout=30.0,
                retry_attempts=2,
                retry_delay=0.5,
                circuit_breaker_threshold=3,
                performance_target=3.0,
            ),
            TimeoutType.DATABASE: TimeoutConfig(
                operation_type=TimeoutType.DATABASE,
                default_timeout=self.config["database_timeout"],
                max_timeout=15.0,
                retry_attempts=2,
                retry_delay=0.1,
                circuit_breaker_threshold=5,
                performance_target=1.0,
            ),
            TimeoutType.CACHE: TimeoutConfig(
                operation_type=TimeoutType.CACHE,
                default_timeout=self.config["cache_timeout"],
                max_timeout=5.0,
                retry_attempts=1,
                retry_delay=0.05,
                circuit_breaker_threshold=3,
                performance_target=0.5,
            ),
            TimeoutType.FILE_OPERATION: TimeoutConfig(
                operation_type=TimeoutType.FILE_OPERATION,
                default_timeout=self.config["file_operation_timeout"],
                max_timeout=60.0,
                retry_attempts=2,
                retry_delay=0.2,
                circuit_breaker_threshold=3,
                performance_target=2.0,
            ),
            TimeoutType.COMPUTATION: TimeoutConfig(
                operation_type=TimeoutType.COMPUTATION,
                default_timeout=self.config["computation_timeout"],
                max_timeout=300.0,
                retry_attempts=1,
                retry_delay=1.0,
                circuit_breaker_threshold=2,
                performance_target=30.0,
            ),
        }

        return configs

    def _get_circuit_breaker(self, operation_type: TimeoutType) -> CircuitBreaker:
        """Get or create circuit breaker for operation type"""
        if operation_type not in self.circuit_breakers:
            config = self.timeout_configs[operation_type]
            self.circuit_breakers[operation_type] = CircuitBreaker(
                failure_threshold=config.circuit_breaker_threshold,
                recovery_timeout=30.0,
            )
        return self.circuit_breakers[operation_type]

    def _classify_performance(self, duration: float, target: float) -> PerformanceLevel:
        """Classify performance level based on duration"""
        if duration < target * 0.2:
            return PerformanceLevel.EXCELLENT
        elif duration < target * 0.6:
            return PerformanceLevel.GOOD
        elif duration <= target:
            return PerformanceLevel.ACCEPTABLE
        elif duration <= target * 2:
            return PerformanceLevel.SLOW
        else:
            return PerformanceLevel.CRITICAL

    @asynccontextmanager
    async def timeout_context(
        self,
        operation_type: TimeoutType,
        operation_id: Optional[str] = None,
        custom_timeout: Optional[float] = None,
    ):
        """Context manager for timeout-controlled operations"""

        config = self.timeout_configs[operation_type]
        timeout = custom_timeout or config.default_timeout
        operation_id = (
            operation_id or f"{operation_type.value}_{int(time.time() * 1000)}"
        )

        # Check circuit breaker
        circuit_breaker = self._get_circuit_breaker(operation_type)
        if not circuit_breaker.can_execute():
            raise TimeoutError(f"Circuit breaker open for {operation_type.value}")

        start_time = time.time()
        timeout_occurred = False
        error_message = None
        success = False

        try:
            # Register active operation
            self.active_operations[operation_id] = {
                "type": operation_type,
                "start_time": start_time,
                "timeout": timeout,
            }

            # Execute with timeout
            async with asyncio.timeout(timeout):
                yield operation_id

            success = True
            circuit_breaker.record_success()

        except asyncio.TimeoutError:
            timeout_occurred = True
            error_message = f"Operation timed out after {timeout}s"
            circuit_breaker.record_failure()

            # Log timeout event
            audit_logger.log_security_event(
                event_description=f"Timeout occurred: {operation_type.value}",
                severity=AuditLevel.WARNING,
                additional_data={
                    "operation_id": operation_id,
                    "timeout": timeout,
                    "duration": time.time() - start_time,
                },
            )

            raise

        except Exception as e:
            error_message = str(e)
            circuit_breaker.record_failure()
            raise

        finally:
            end_time = time.time()
            duration = end_time - start_time

            # Remove from active operations
            self.active_operations.pop(operation_id, None)

            # Record performance metric
            performance_level = self._classify_performance(
                duration, config.performance_target
            )

            metric = PerformanceMetric(
                operation_id=operation_id,
                operation_type=operation_type,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                success=success,
                timeout_occurred=timeout_occurred,
                retry_count=0,  # Will be updated by retry wrapper
                error_message=error_message,
                performance_level=performance_level,
            )

            self._record_performance_metric(metric)

    def _record_performance_metric(self, metric: PerformanceMetric):
        """Record performance metric for analysis"""
        self.performance_metrics.append(metric)
        self.response_times[metric.operation_type].append(metric.duration)

        # Keep only recent metrics (last 1000 per type)
        if len(self.response_times[metric.operation_type]) > 1000:
            self.response_times[metric.operation_type] = self.response_times[
                metric.operation_type
            ][-1000:]

        # Log performance if slow or critical
        if metric.performance_level in [
            PerformanceLevel.SLOW,
            PerformanceLevel.CRITICAL,
        ]:
            audit_logger.log_security_event(
                event_description=f"Slow operation detected: {metric.operation_type.value}",
                severity=(
                    AuditLevel.WARNING
                    if metric.performance_level == PerformanceLevel.SLOW
                    else AuditLevel.ERROR
                ),
                additional_data={
                    "operation_id": metric.operation_id,
                    "duration": metric.duration,
                    "performance_level": metric.performance_level.value,
                    "target": self.timeout_configs[
                        metric.operation_type
                    ].performance_target,
                },
            )

    def with_timeout(
        self,
        operation_type: TimeoutType,
        custom_timeout: Optional[float] = None,
        retry_attempts: Optional[int] = None,
    ):
        """Decorator for timeout-controlled functions"""

        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                config = self.timeout_configs[operation_type]
                attempts = retry_attempts or config.retry_attempts

                last_exception = None

                for attempt in range(attempts + 1):
                    try:
                        async with self.timeout_context(
                            operation_type=operation_type, custom_timeout=custom_timeout
                        ) as operation_id:
                            result = await func(*args, **kwargs)

                            # Update retry count in latest metric
                            if self.performance_metrics:
                                self.performance_metrics[-1].retry_count = attempt

                            return result

                    except (asyncio.TimeoutError, Exception) as e:
                        last_exception = e

                        if attempt < attempts:
                            # Wait before retry
                            await asyncio.sleep(config.retry_delay * (attempt + 1))

                            audit_logger.log_security_event(
                                event_description=f"Retrying operation: {operation_type.value}",
                                severity=AuditLevel.INFO,
                                additional_data={
                                    "attempt": attempt + 1,
                                    "max_attempts": attempts + 1,
                                    "error": str(e),
                                },
                            )
                        else:
                            # Final failure
                            audit_logger.log_security_event(
                                event_description=f"Operation failed after retries: {operation_type.value}",
                                severity=AuditLevel.ERROR,
                                additional_data={
                                    "total_attempts": attempts + 1,
                                    "final_error": str(e),
                                },
                            )

                raise last_exception

            return wrapper

        return decorator

    async def chatgpt_api_call(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Make ChatGPT API call with proper timeout handling"""

        @self.with_timeout(TimeoutType.API_REQUEST, custom_timeout=timeout)
        async def _make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=url, json=data, headers=headers or {}
                ) as response:
                    response.raise_for_status()
                    return await response.json()

        return await _make_request()

    async def webhook_call(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> bool:
        """Make webhook call with proper timeout handling"""

        @self.with_timeout(TimeoutType.WEBHOOK, custom_timeout=timeout)
        async def _make_webhook_call():
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=url, json=data, headers=headers or {}
                ) as response:
                    return response.status < 400

        return await _make_webhook_call()

    def get_performance_stats(
        self, operation_type: Optional[TimeoutType] = None
    ) -> Dict[str, Any]:
        """Get performance statistics"""

        if operation_type:
            response_times = self.response_times[operation_type]
            operation_types = [operation_type]
        else:
            response_times = []
            for times in self.response_times.values():
                response_times.extend(times)
            operation_types = list(TimeoutType)

        if not response_times:
            return {"error": "No performance data available"}

        response_times.sort()
        count = len(response_times)

        stats = {
            "count": count,
            "min": min(response_times),
            "max": max(response_times),
            "mean": sum(response_times) / count,
            "p50": response_times[int(0.5 * count)],
            "p95": response_times[int(0.95 * count)],
            "p99": response_times[int(0.99 * count)],
            "operation_types": [ot.value for ot in operation_types],
        }

        # Check compliance with Rule 10 (P95 < 5s)
        compliance_status = (
            "compliant"
            if stats["p95"] <= self.config["performance_target_p95"]
            else "violation"
        )
        stats["compliance_status"] = compliance_status

        return stats

    def get_active_operations(self) -> Dict[str, Any]:
        """Get currently active operations"""
        current_time = time.time()

        active = {}
        for op_id, op_info in self.active_operations.items():
            duration = current_time - op_info["start_time"]
            active[op_id] = {
                "type": op_info["type"].value,
                "duration": duration,
                "timeout": op_info["timeout"],
                "time_remaining": max(0, op_info["timeout"] - duration),
            }

        return active

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get circuit breaker status for all operation types"""
        status = {}

        for operation_type in TimeoutType:
            if operation_type in self.circuit_breakers:
                cb = self.circuit_breakers[operation_type]
                status[operation_type.value] = {
                    "state": cb.state,
                    "failure_count": cb.failure_count,
                    "can_execute": cb.can_execute(),
                }
            else:
                status[operation_type.value] = {
                    "state": "closed",
                    "failure_count": 0,
                    "can_execute": True,
                }

        return status

    def generate_timeout_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive timeout compliance report"""

        report = {
            "report_id": f"timeout_compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "chatgpt_api_timeout": self.config["chatgpt_api_timeout"],
                "performance_target_p95": self.config["performance_target_p95"],
                "circuit_breaker_enabled": self.config["circuit_breaker_enabled"],
                "retry_enabled": self.config["retry_enabled"],
            },
            "performance_stats": self.get_performance_stats(),
            "circuit_breaker_status": self.get_circuit_breaker_status(),
            "active_operations": self.get_active_operations(),
            "compliance_summary": {
                "rule_6_timeout_compliance": self.config["chatgpt_api_timeout"] == 30.0,
                "rule_10_performance_compliance": self.get_performance_stats().get(
                    "compliance_status"
                )
                == "compliant",
                "circuit_breakers_healthy": all(
                    status["state"] != "open"
                    for status in self.get_circuit_breaker_status().values()
                ),
            },
            "recommendations": self._generate_timeout_recommendations(),
        }

        return report

    def _generate_timeout_recommendations(self) -> List[str]:
        """Generate timeout-related recommendations"""
        recommendations = []

        stats = self.get_performance_stats()
        if stats.get("compliance_status") == "violation":
            recommendations.append(
                f"P95 response time ({stats['p95']:.2f}s) exceeds target (5s)"
            )

        cb_status = self.get_circuit_breaker_status()
        open_breakers = [
            op for op, status in cb_status.items() if status["state"] == "open"
        ]
        if open_breakers:
            recommendations.append(
                f"Circuit breakers open for: {', '.join(open_breakers)}"
            )

        active_ops = self.get_active_operations()
        long_running = [op for op, info in active_ops.items() if info["duration"] > 30]
        if long_running:
            recommendations.append(
                f"{len(long_running)} operations running longer than 30s"
            )

        return recommendations


# Global timeout manager instance
timeout_manager = TimeoutManager()


# Convenience decorators
def chatgpt_timeout(timeout: Optional[float] = None):
    """Decorator for ChatGPT API calls with timeout"""
    return timeout_manager.with_timeout(TimeoutType.API_REQUEST, custom_timeout=timeout)


def webhook_timeout(timeout: Optional[float] = None):
    """Decorator for webhook calls with timeout"""
    return timeout_manager.with_timeout(TimeoutType.WEBHOOK, custom_timeout=timeout)


def database_timeout(timeout: Optional[float] = None):
    """Decorator for database operations with timeout"""
    return timeout_manager.with_timeout(TimeoutType.DATABASE, custom_timeout=timeout)
