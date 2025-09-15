#!/usr/bin/env python3
"""
Monitoring Dashboard
Provides a real-time dashboard for monitoring application health and performance.
"""

import os
import sys
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from health_monitoring import HealthMonitor, HealthStatus, SystemMetrics
    has_health_monitoring = True
except ImportError:
    print("Warning: health_monitoring module not found. Using mock implementations.")
    has_health_monitoring = False
    
    class HealthStatus:
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"
    
    @dataclass
    class SystemMetrics:
        cpu_usage: float
        memory_usage: float
        disk_usage: float
        network_latency: float
        active_connections: int
        error_rate: float
        timestamp: datetime
    
    class HealthMonitor:
        def __init__(self, config=None):
            self.config = config or {}
        
        async def run_all_checks(self):
            return {}
        
        def get_system_metrics(self):
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


@dataclass
class DashboardConfig:
    """Configuration for monitoring dashboard."""
    refresh_interval: int = 30
    history_retention: int = 100
    alert_webhook: str = ""
    display_mode: str = "console"  # console, web, json
    metrics_endpoint: str = "/metrics"
    health_endpoint: str = "/health"


class MonitoringDashboard:
    """Real-time monitoring dashboard."""
    
    def __init__(self, config: Optional[DashboardConfig] = None):
        self.config = config or DashboardConfig()
        self.monitor = HealthMonitor()
        self.metrics_history: List[SystemMetrics] = []
        self.alerts_history: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
        
    def clear_screen(self) -> None:
        """Clear the console screen."""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def format_uptime(self) -> str:
        """Format application uptime."""
        uptime = datetime.now() - self.start_time
        days = uptime.days
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        else:
            return f"{minutes}m {seconds}s"
    
    def get_status_color(self, status: str) -> str:
        """Get ANSI color code for status."""
        colors = {
            'healthy': '\033[92m',    # Green
            'degraded': '\033[93m',   # Yellow
            'unhealthy': '\033[91m',  # Red
            'unknown': '\033[94m'     # Blue
        }
        return colors.get(status.lower(), '\033[0m')
    
    def format_metric_bar(self, value: float, max_value: float = 100, width: int = 20) -> str:
        """Format a metric as a progress bar."""
        percentage = min(value / max_value, 1.0)
        filled = int(percentage * width)
        bar = '█' * filled + '░' * (width - filled)
        
        if percentage < 0.5:
            color = '\033[92m'  # Green
        elif percentage < 0.8:
            color = '\033[93m'  # Yellow
        else:
            color = '\033[91m'  # Red
        
        return f"{color}{bar}\033[0m {value:.1f}%"
    
    def render_header(self) -> str:
        """Render dashboard header."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        uptime = self.format_uptime()
        
        header = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                           🚀 PRODUCTION MONITORING DASHBOARD                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║ Time: {now:<20} │ Uptime: {uptime:<25} ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        return header
    
    def render_system_metrics(self, metrics: SystemMetrics) -> str:
        """Render system metrics section."""
        cpu_bar = self.format_metric_bar(metrics.cpu_usage)
        memory_bar = self.format_metric_bar(metrics.memory_usage)
        disk_bar = self.format_metric_bar(metrics.disk_usage)
        
        section = f"""
┌─ SYSTEM METRICS ─────────────────────────────────────────────────────────────┐
│ CPU Usage:    {cpu_bar}                                    │
│ Memory Usage: {memory_bar}                                    │
│ Disk Usage:   {disk_bar}                                    │
│ Network Latency: {metrics.network_latency:>6.1f} ms                                        │
│ Active Connections: {metrics.active_connections:>4d}                                            │
│ Error Rate: {metrics.error_rate:>8.2%}                                                │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        return section
    
    def render_health_checks(self, results: Dict[str, Any]) -> str:
        """Render health checks section."""
        if not results:
            return """
┌─ HEALTH CHECKS ──────────────────────────────────────────────────────────────┐
│ No health check results available                                           │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        
        section = "┌─ HEALTH CHECKS ──────────────────────────────────────────────────────────────┐\n"
        
        for name, result in results.items():
            if isinstance(result, dict) and 'status' in result:
                status = result['status']
                response_time = result.get('response_time', 0)
            else:
                status = 'unknown'
                response_time = 0
            
            color = self.get_status_color(status)
            status_display = f"{color}{status.upper():>10}\033[0m"
            
            section += f"│ {name:<30} {status_display} {response_time:>8.3f}s │\n"
        
        section += "└──────────────────────────────────────────────────────────────────────────────┘\n"
        return section
    
    def render_recent_alerts(self) -> str:
        """Render recent alerts section."""
        if not self.alerts_history:
            return """
┌─ RECENT ALERTS ──────────────────────────────────────────────────────────────┐
│ No recent alerts                                                            │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        
        section = "┌─ RECENT ALERTS ──────────────────────────────────────────────────────────────┐\n"
        
        # Show last 5 alerts
        recent_alerts = self.alerts_history[-5:]
        for alert in recent_alerts:
            timestamp = alert['timestamp'].strftime("%H:%M:%S")
            severity = alert['severity'].upper()
            message = alert['message'][:50] + "..." if len(alert['message']) > 50 else alert['message']
            
            color = '\033[91m' if severity == 'CRITICAL' else '\033[93m'
            section += f"│ {timestamp} {color}{severity:>8}\033[0m {message:<45} │\n"
        
        section += "└──────────────────────────────────────────────────────────────────────────────┘\n"
        return section
    
    def render_performance_trends(self) -> str:
        """Render performance trends section."""
        if len(self.metrics_history) < 2:
            return """
┌─ PERFORMANCE TRENDS ─────────────────────────────────────────────────────────┐
│ Insufficient data for trends                                                │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        
        # Calculate trends from last 10 metrics
        recent_metrics = self.metrics_history[-10:]
        
        cpu_trend = self._calculate_trend([m.cpu_usage for m in recent_metrics])
        memory_trend = self._calculate_trend([m.memory_usage for m in recent_metrics])
        error_trend = self._calculate_trend([m.error_rate for m in recent_metrics])
        
        cpu_arrow = self._get_trend_arrow(cpu_trend)
        memory_arrow = self._get_trend_arrow(memory_trend)
        error_arrow = self._get_trend_arrow(error_trend)
        
        section = f"""
┌─ PERFORMANCE TRENDS ─────────────────────────────────────────────────────────┐
│ CPU Usage:    {cpu_arrow} {cpu_trend:>+6.1f}%                                        │
│ Memory Usage: {memory_arrow} {memory_trend:>+6.1f}%                                        │
│ Error Rate:   {error_arrow} {error_trend:>+6.2%}                                        │
└──────────────────────────────────────────────────────────────────────────────┘
"""
        return section
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend from a list of values."""
        if len(values) < 2:
            return 0.0
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        if n * x2_sum - x_sum * x_sum == 0:
            return 0.0
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        return slope * (n - 1)  # Trend over the period
    
    def _get_trend_arrow(self, trend: float) -> str:
        """Get trend arrow with color."""
        if trend > 1:
            return '\033[91m↗\033[0m'  # Red up arrow
        elif trend < -1:
            return '\033[92m↘\033[0m'  # Green down arrow
        else:
            return '\033[94m→\033[0m'  # Blue right arrow
    
    async def collect_data(self) -> Dict[str, Any]:
        """Collect monitoring data."""
        # Get health check results
        health_results = await self.monitor.run_all_checks()
        
        # Get system metrics
        metrics = self.monitor.get_system_metrics()
        self.metrics_history.append(metrics)
        
        # Keep only recent metrics
        if len(self.metrics_history) > self.config.history_retention:
            self.metrics_history = self.metrics_history[-self.config.history_retention:]
        
        # Check for alerts
        alerts = self._check_alert_conditions(metrics, health_results)
        for alert in alerts:
            self.alerts_history.append({
                'timestamp': datetime.now(),
                'severity': alert['severity'],
                'message': alert['message']
            })
        
        # Keep only recent alerts
        if len(self.alerts_history) > 50:
            self.alerts_history = self.alerts_history[-50:]
        
        return {
            'health_results': health_results,
            'metrics': metrics,
            'alerts': alerts
        }
    
    def _check_alert_conditions(self, metrics: SystemMetrics, health_results: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for alert conditions."""
        alerts = []
        
        # System metrics alerts
        if metrics.cpu_usage > 80:
            alerts.append({
                'severity': 'warning',
                'message': f'High CPU usage: {metrics.cpu_usage:.1f}%'
            })
        
        if metrics.memory_usage > 85:
            alerts.append({
                'severity': 'warning',
                'message': f'High memory usage: {metrics.memory_usage:.1f}%'
            })
        
        if metrics.disk_usage > 90:
            alerts.append({
                'severity': 'critical',
                'message': f'Critical disk usage: {metrics.disk_usage:.1f}%'
            })
        
        if metrics.error_rate > 0.05:
            alerts.append({
                'severity': 'warning',
                'message': f'High error rate: {metrics.error_rate:.2%}'
            })
        
        # Health check alerts
        for name, result in health_results.items():
            if isinstance(result, dict) and result.get('status') == 'unhealthy':
                alerts.append({
                    'severity': 'critical',
                    'message': f'Health check failed: {name}'
                })
        
        return alerts
    
    def render_console_dashboard(self, data: Dict[str, Any]) -> str:
        """Render complete console dashboard."""
        dashboard = self.render_header()
        dashboard += self.render_system_metrics(data['metrics'])
        dashboard += self.render_health_checks(data['health_results'])
        dashboard += self.render_performance_trends()
        dashboard += self.render_recent_alerts()
        
        return dashboard
    
    def render_json_output(self, data: Dict[str, Any]) -> str:
        """Render data as JSON."""
        output = {
            'timestamp': datetime.now().isoformat(),
            'uptime': self.format_uptime(),
            'system_metrics': asdict(data['metrics']),
            'health_checks': data['health_results'],
            'recent_alerts': [alert if isinstance(alert, dict) else asdict(alert) for alert in self.alerts_history[-10:]],
            'performance_trends': {
                'cpu_trend': self._calculate_trend([m.cpu_usage for m in self.metrics_history[-10:]]) if len(self.metrics_history) >= 2 else 0,
                'memory_trend': self._calculate_trend([m.memory_usage for m in self.metrics_history[-10:]]) if len(self.metrics_history) >= 2 else 0,
                'error_trend': self._calculate_trend([m.error_rate for m in self.metrics_history[-10:]]) if len(self.metrics_history) >= 2 else 0
            }
        }
        
        return json.dumps(output, indent=2, default=str)
    
    async def run_dashboard(self) -> None:
        """Run the monitoring dashboard."""
        print("Starting monitoring dashboard...")
        print(f"Display mode: {self.config.display_mode}")
        print(f"Refresh interval: {self.config.refresh_interval}s")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                # Collect monitoring data
                data = await self.collect_data()
                
                if self.config.display_mode == "console":
                    self.clear_screen()
                    dashboard = self.render_console_dashboard(data)
                    print(dashboard)
                elif self.config.display_mode == "json":
                    json_output = self.render_json_output(data)
                    print(json_output)
                    print("\n" + "="*80 + "\n")
                
                # Wait for next refresh
                await asyncio.sleep(self.config.refresh_interval)
                
        except KeyboardInterrupt:
            print("\n\nMonitoring dashboard stopped.")
        except Exception as e:
            print(f"\nError in dashboard: {e}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Monitoring Dashboard")
    parser.add_argument('--mode', choices=['console', 'json'], default='console',
                       help='Display mode (default: console)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Refresh interval in seconds (default: 30)')
    parser.add_argument('--webhook', type=str, default='',
                       help='Alert webhook URL')
    
    args = parser.parse_args()
    
    config = DashboardConfig(
        display_mode=args.mode,
        refresh_interval=args.interval,
        alert_webhook=args.webhook
    )
    
    dashboard = MonitoringDashboard(config)
    
    try:
        asyncio.run(dashboard.run_dashboard())
    except KeyboardInterrupt:
        print("\nDashboard stopped by user.")
    except Exception as e:
        print(f"Dashboard error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()