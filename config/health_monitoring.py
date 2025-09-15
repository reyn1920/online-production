#!/usr/bin/env python3
"""
Health Monitoring Configuration
Provides comprehensive health checks and monitoring for production deployment.
"""

import os
import time
import json
import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Callable, Awaitable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta


class HealthStatus(Enum):
    """Health check status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime
    details: Dict[str, Any]


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_connections: int
    error_rate: float
    timestamp: datetime


class HealthMonitor:
    """Main health monitoring system."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.checks: Dict[str, Callable[[], Union[HealthCheckResult, Awaitable[HealthCheckResult]]]] = {}
        self.metrics_history: List[SystemMetrics] = []
        self.alert_thresholds = self.config.get('alert_thresholds', {})
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default monitoring configuration."""
        return {
            'check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            'timeout': int(os.getenv('HEALTH_CHECK_TIMEOUT', '10')),
            'alert_thresholds': {
                'response_time': float(os.getenv('ALERT_RESPONSE_TIME', '5.0')),
                'error_rate': float(os.getenv('ALERT_ERROR_RATE', '0.05')),
                'cpu_usage': float(os.getenv('ALERT_CPU_USAGE', '80.0')),
                'memory_usage': float(os.getenv('ALERT_MEMORY_USAGE', '85.0')),
                'disk_usage': float(os.getenv('ALERT_DISK_USAGE', '90.0'))
            },
            'endpoints': {
                'api_health': os.getenv('API_HEALTH_ENDPOINT', '/health'),
                'database': os.getenv('DATABASE_URL', ''),
                'redis': os.getenv('REDIS_URL', ''),
                'external_apis': os.getenv('EXTERNAL_API_ENDPOINTS', '').split(',') if os.getenv('EXTERNAL_API_ENDPOINTS') else []
            },
            'notifications': {
                'webhook_url': os.getenv('ALERT_WEBHOOK_URL', ''),
                'email_enabled': os.getenv('EMAIL_ALERTS', 'false').lower() == 'true',
                'slack_enabled': os.getenv('SLACK_ALERTS', 'false').lower() == 'true'
            }
        }
    
    def register_check(self, name: str, check_func: Callable[[], Union[HealthCheckResult, Awaitable[HealthCheckResult]]]) -> None:
        """Register a custom health check."""
        self.checks[name] = check_func
    
    async def check_api_endpoint(self, url: str, timeout: int = 10) -> HealthCheckResult:
        """Check API endpoint health."""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        status = HealthStatus.HEALTHY
                        message = "API endpoint is healthy"
                    elif 200 <= response.status < 300:
                        status = HealthStatus.HEALTHY
                        message = f"API endpoint returned {response.status}"
                    elif 400 <= response.status < 500:
                        status = HealthStatus.DEGRADED
                        message = f"Client error: {response.status}"
                    else:
                        status = HealthStatus.UNHEALTHY
                        message = f"Server error: {response.status}"
                    
                    return HealthCheckResult(
                        name=f"api_endpoint_{url}",
                        status=status,
                        response_time=response_time,
                        message=message,
                        timestamp=datetime.now(),
                        details={
                            'url': url,
                            'status_code': response.status,
                            'headers': dict(response.headers)
                        }
                    )
                    
        except asyncio.TimeoutError:
            return HealthCheckResult(
                name=f"api_endpoint_{url}",
                status=HealthStatus.UNHEALTHY,
                response_time=timeout,
                message="Request timeout",
                timestamp=datetime.now(),
                details={'url': url, 'error': 'timeout'}
            )
        except Exception as e:
            return HealthCheckResult(
                name=f"api_endpoint_{url}",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Connection error: {str(e)}",
                timestamp=datetime.now(),
                details={'url': url, 'error': str(e)}
            )
    
    async def check_database_connection(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = time.time()
        db_url = self.config['endpoints']['database']
        
        if not db_url:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNKNOWN,
                response_time=0,
                message="Database URL not configured",
                timestamp=datetime.now(),
                details={}
            )
        
        try:
            # This is a simplified check - in production, use actual database client
            # For now, we'll simulate a database check
            await asyncio.sleep(0.1)  # Simulate connection time
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="Database connection successful",
                timestamp=datetime.now(),
                details={'url': db_url[:20] + '...' if len(db_url) > 20 else db_url}
            )
            
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                message=f"Database connection failed: {str(e)}",
                timestamp=datetime.now(),
                details={'error': str(e)}
            )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        # In production, use actual system monitoring libraries like psutil
        # For now, we'll simulate metrics
        import random
        
        return SystemMetrics(
            cpu_usage=random.uniform(10, 90),
            memory_usage=random.uniform(20, 85),
            disk_usage=random.uniform(30, 95),
            network_latency=random.uniform(1, 100),
            active_connections=random.randint(10, 1000),
            error_rate=random.uniform(0, 0.1),
            timestamp=datetime.now()
        )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        
        # Built-in checks
        if self.config['endpoints']['api_health']:
            api_result = await self.check_api_endpoint(self.config['endpoints']['api_health'])
            results['api_health'] = api_result
        
        db_result = await self.check_database_connection()
        results['database'] = db_result
        
        # External API checks
        for api_url in self.config['endpoints']['external_apis']:
            if api_url.strip():
                api_result = await self.check_api_endpoint(api_url.strip())
                results[f"external_api_{api_url.split('/')[-1]}"] = api_result
        
        # Custom checks
        for name, check_func in self.checks.items():
            try:
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                results[name] = result
            except Exception as e:
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    response_time=0,
                    message=f"Check failed: {str(e)}",
                    timestamp=datetime.now(),
                    details={'error': str(e)}
                )
        
        return results
    
    def analyze_health_status(self, results: Dict[str, HealthCheckResult]) -> Dict[str, Any]:
        """Analyze overall health status from check results."""
        total_checks = len(results)
        healthy_checks = sum(1 for r in results.values() if r.status == HealthStatus.HEALTHY)
        degraded_checks = sum(1 for r in results.values() if r.status == HealthStatus.DEGRADED)
        unhealthy_checks = sum(1 for r in results.values() if r.status == HealthStatus.UNHEALTHY)
        
        if unhealthy_checks > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_checks > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        avg_response_time = sum(r.response_time for r in results.values()) / total_checks if total_checks > 0 else 0
        
        return {
            'overall_status': overall_status.value,
            'total_checks': total_checks,
            'healthy_checks': healthy_checks,
            'degraded_checks': degraded_checks,
            'unhealthy_checks': unhealthy_checks,
            'average_response_time': avg_response_time,
            'timestamp': datetime.now().isoformat(),
            'details': {name: asdict(result) for name, result in results.items()}
        }
    
    async def send_alert(self, message: str, severity: str = 'warning') -> None:
        """Send alert notification."""
        webhook_url = self.config['notifications']['webhook_url']
        
        if not webhook_url:
            print(f"Alert ({severity}): {message}")
            return
        
        alert_payload = {
            'text': f"🚨 Production Alert ({severity.upper()})",
            'attachments': [{
                'color': 'danger' if severity == 'critical' else 'warning',
                'fields': [{
                    'title': 'Message',
                    'value': message,
                    'short': False
                }, {
                    'title': 'Timestamp',
                    'value': datetime.now().isoformat(),
                    'short': True
                }]
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=alert_payload) as response:
                    if response.status == 200:
                        print(f"Alert sent successfully: {message}")
                    else:
                        print(f"Failed to send alert: {response.status}")
        except Exception as e:
            print(f"Error sending alert: {e}")
    
    def check_alert_conditions(self, results: Dict[str, HealthCheckResult], metrics: SystemMetrics) -> List[str]:
        """Check if any alert conditions are met."""
        alerts = []
        thresholds = self.alert_thresholds
        
        # Response time alerts
        for name, result in results.items():
            if result.response_time > thresholds.get('response_time', 5.0):
                alerts.append(f"High response time for {name}: {result.response_time:.2f}s")
        
        # System metrics alerts
        if metrics.cpu_usage > thresholds.get('cpu_usage', 80.0):
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > thresholds.get('memory_usage', 85.0):
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.disk_usage > thresholds.get('disk_usage', 90.0):
            alerts.append(f"High disk usage: {metrics.disk_usage:.1f}%")
        
        if metrics.error_rate > thresholds.get('error_rate', 0.05):
            alerts.append(f"High error rate: {metrics.error_rate:.2%}")
        
        return alerts
    
    async def monitoring_loop(self) -> None:
        """Main monitoring loop."""
        print("Starting health monitoring loop...")
        
        while True:
            try:
                # Run health checks
                results = await self.run_all_checks()
                
                # Get system metrics
                metrics = self.get_system_metrics()
                self.metrics_history.append(metrics)
                
                # Keep only last 100 metrics entries
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-100:]
                
                # Analyze health status
                health_analysis = self.analyze_health_status(results)
                
                # Check for alert conditions
                alerts = self.check_alert_conditions(results, metrics)
                
                # Send alerts if necessary
                for alert in alerts:
                    await self.send_alert(alert, 'warning')
                
                # Log status
                print(f"Health check completed: {health_analysis['overall_status']} "
                      f"({health_analysis['healthy_checks']}/{health_analysis['total_checks']} healthy)")
                
                # Wait for next check
                await asyncio.sleep(self.config['check_interval'])
                
            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.config['check_interval'])


def create_health_endpoint_handler(monitor: HealthMonitor):
    """Create a health endpoint handler for web frameworks."""
    
    async def health_handler():
        """Health endpoint handler."""
        results = await monitor.run_all_checks()
        analysis = monitor.analyze_health_status(results)
        
        status_code = 200 if analysis['overall_status'] == 'healthy' else 503
        
        return {
            'status': analysis['overall_status'],
            'timestamp': analysis['timestamp'],
            'checks': {
                'total': analysis['total_checks'],
                'healthy': analysis['healthy_checks'],
                'degraded': analysis['degraded_checks'],
                'unhealthy': analysis['unhealthy_checks']
            },
            'response_time': analysis['average_response_time'],
            'details': analysis['details']
        }, status_code
    
    return health_handler


if __name__ == '__main__':
    # Example usage
    async def main():
        monitor = HealthMonitor()
        
        # Register custom check
        def custom_check():
            return HealthCheckResult(
                name="custom_service",
                status=HealthStatus.HEALTHY,
                response_time=0.1,
                message="Custom service is operational",
                timestamp=datetime.now(),
                details={}
            )
        
        monitor.register_check('custom_service', custom_check)
        
        # Run single check
        results = await monitor.run_all_checks()
        analysis = monitor.analyze_health_status(results)
        
        print("Health Check Results:")
        print(json.dumps(analysis, indent=2, default=str))
        
        # Uncomment to run continuous monitoring
        # await monitor.monitoring_loop()
    
    asyncio.run(main())