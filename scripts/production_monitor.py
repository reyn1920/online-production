#!/usr/bin/env python3
"""
Production Monitoring and Health Check Script

This script provides comprehensive monitoring capabilities for the production
application, including health checks, performance monitoring, and alerting.

Usage:
    python scripts/production_monitor.py --check-all
    python scripts/production_monitor.py --health-check
    python scripts/production_monitor.py --performance-test
    python scripts/production_monitor.py --alert-test

Author: TRAE AI Production Team
Version: 1.0.0
"""

import os
import sys
import time
import json
import argparse
import requests
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    service: str
    status: str  # 'healthy', 'degraded', 'unhealthy'
    response_time: float
    message: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    response_time: float
    error_rate: float
    active_connections: int
    timestamp: datetime

class ProductionMonitor:
    """Production monitoring and health check system"""
    
    def __init__(self):
        self.base_url = os.getenv('PRODUCTION_URL', 'https://your-app.netlify.app')
        self.api_key = os.getenv('MONITOR_API_KEY', '')
        self.alert_webhook = os.getenv('ALERT_WEBHOOK_URL', '')
        self.timeout = 30
        self.max_retries = 3
        
        # Performance thresholds
        self.thresholds = {
            'response_time': 3.0,  # seconds
            'cpu_usage': 80.0,     # percentage
            'memory_usage': 85.0,  # percentage
            'disk_usage': 90.0,    # percentage
            'error_rate': 1.0,     # percentage
        }
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
    
    def health_check_endpoint(self, endpoint: str) -> HealthCheckResult:
        """Check health of a specific endpoint"""
        start_time = time.time()
        url = urljoin(self.base_url, endpoint)
        
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = requests.get(
                url, 
                headers=headers, 
                timeout=self.timeout
            )
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        status = 'healthy'
                        message = 'Service is healthy'
                    else:
                        status = 'degraded'
                        message = f"Service reports: {data.get('message', 'Unknown status')}"
                except json.JSONDecodeError:
                    status = 'healthy' if response_time < self.thresholds['response_time'] else 'degraded'
                    message = f'Endpoint responding (non-JSON response)'
            else:
                status = 'unhealthy'
                message = f'HTTP {response.status_code}: {response.reason}'
            
            return HealthCheckResult(
                service=endpoint,
                status=status,
                response_time=response_time,
                message=message,
                timestamp=datetime.now(),
                details={
                    'status_code': response.status_code,
                    'headers': dict(response.headers),
                    'url': url
                }
            )
            
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service=endpoint,
                status='unhealthy',
                response_time=self.timeout,
                message='Request timeout',
                timestamp=datetime.now()
            )
        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                service=endpoint,
                status='unhealthy',
                response_time=0,
                message='Connection error',
                timestamp=datetime.now()
            )
        except Exception as e:
            return HealthCheckResult(
                service=endpoint,
                status='unhealthy',
                response_time=0,
                message=f'Unexpected error: {str(e)}',
                timestamp=datetime.now()
            )
    
    def comprehensive_health_check(self) -> List[HealthCheckResult]:
        """Run comprehensive health checks on all critical endpoints"""
        endpoints = [
            '/',                    # Main application
            '/health',             # Health check endpoint
            '/api/health',         # API health check
            '/api/status',         # API status
        ]
        
        results = []
        logger.info("Starting comprehensive health check...")
        
        for endpoint in endpoints:
            logger.info(f"Checking endpoint: {endpoint}")
            result = self.health_check_endpoint(endpoint)
            results.append(result)
            
            # Log result
            if result.status == 'healthy':
                logger.info(f"✅ {endpoint}: {result.message} ({result.response_time:.2f}s)")
            elif result.status == 'degraded':
                logger.warning(f"⚠️ {endpoint}: {result.message} ({result.response_time:.2f}s)")
            else:
                logger.error(f"❌ {endpoint}: {result.message}")
        
        return results
    
    def get_system_metrics(self) -> PerformanceMetrics:
        """Get current system performance metrics"""
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Test response time with a simple request
            start_time = time.time()
            try:
                requests.get(self.base_url, timeout=10)
                response_time = time.time() - start_time
            except:
                response_time = float('inf')
            
            return PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory.percent,
                disk_usage=disk.percent,
                response_time=response_time,
                error_rate=0.0,  # Would need log analysis for accurate error rate
                active_connections=len(psutil.net_connections()),
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return PerformanceMetrics(
                cpu_usage=0,
                memory_usage=0,
                disk_usage=0,
                response_time=float('inf'),
                error_rate=100.0,
                active_connections=0,
                timestamp=datetime.now()
            )
    
    def performance_test(self) -> Dict[str, Any]:
        """Run performance tests and return results"""
        logger.info("Starting performance test...")
        
        metrics = self.get_system_metrics()
        
        # Performance analysis
        issues = []
        if metrics.cpu_usage > self.thresholds['cpu_usage']:
            issues.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.thresholds['memory_usage']:
            issues.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.disk_usage > self.thresholds['disk_usage']:
            issues.append(f"High disk usage: {metrics.disk_usage:.1f}%")
        
        if metrics.response_time > self.thresholds['response_time']:
            issues.append(f"Slow response time: {metrics.response_time:.2f}s")
        
        status = 'healthy' if not issues else 'degraded' if len(issues) < 3 else 'critical'
        
        result = {
            'status': status,
            'metrics': {
                'cpu_usage': f"{metrics.cpu_usage:.1f}%",
                'memory_usage': f"{metrics.memory_usage:.1f}%",
                'disk_usage': f"{metrics.disk_usage:.1f}%",
                'response_time': f"{metrics.response_time:.2f}s",
                'active_connections': metrics.active_connections
            },
            'issues': issues,
            'timestamp': metrics.timestamp.isoformat()
        }
        
        logger.info(f"Performance test completed: {status}")
        if issues:
            for issue in issues:
                logger.warning(f"⚠️ {issue}")
        else:
            logger.info("✅ All performance metrics within acceptable ranges")
        
        return result
    
    def send_alert(self, message: str, severity: str = 'warning') -> bool:
        """Send alert notification"""
        if not self.alert_webhook:
            logger.warning("No alert webhook configured")
            return False
        
        try:
            payload = {
                'text': f"🚨 Production Alert [{severity.upper()}]\n{message}",
                'timestamp': datetime.now().isoformat(),
                'severity': severity,
                'source': 'production_monitor'
            }
            
            response = requests.post(
                self.alert_webhook,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Alert sent successfully: {message}")
                return True
            else:
                logger.error(f"Failed to send alert: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
            return False
    
    def analyze_health_results(self, results: List[HealthCheckResult]) -> Dict[str, Any]:
        """Analyze health check results and determine overall status"""
        healthy_count = sum(1 for r in results if r.status == 'healthy')
        degraded_count = sum(1 for r in results if r.status == 'degraded')
        unhealthy_count = sum(1 for r in results if r.status == 'unhealthy')
        
        total_count = len(results)
        avg_response_time = sum(r.response_time for r in results) / total_count if results else 0
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = 'critical'
        elif degraded_count > total_count // 2:
            overall_status = 'degraded'
        elif degraded_count > 0:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        return {
            'overall_status': overall_status,
            'summary': {
                'total_services': total_count,
                'healthy': healthy_count,
                'degraded': degraded_count,
                'unhealthy': unhealthy_count,
                'avg_response_time': f"{avg_response_time:.2f}s"
            },
            'details': [
                {
                    'service': r.service,
                    'status': r.status,
                    'response_time': f"{r.response_time:.2f}s",
                    'message': r.message
                }
                for r in results
            ]
        }
    
    def generate_report(self, health_results: List[HealthCheckResult], 
                       performance_results: Dict[str, Any]) -> str:
        """Generate comprehensive monitoring report"""
        health_analysis = self.analyze_health_results(health_results)
        
        report = f"""
# Production Monitoring Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Application**: {self.base_url}

## Overall Status: {health_analysis['overall_status'].upper()}

### Health Check Summary
- Total Services: {health_analysis['summary']['total_services']}
- Healthy: {health_analysis['summary']['healthy']} ✅
- Degraded: {health_analysis['summary']['degraded']} ⚠️
- Unhealthy: {health_analysis['summary']['unhealthy']} ❌
- Average Response Time: {health_analysis['summary']['avg_response_time']}

### Service Details
"""
        
        for detail in health_analysis['details']:
            status_emoji = {'healthy': '✅', 'degraded': '⚠️', 'unhealthy': '❌'}
            report += f"- **{detail['service']}**: {status_emoji.get(detail['status'], '❓')} {detail['status']} ({detail['response_time']}) - {detail['message']}\n"
        
        report += f"""

### Performance Metrics
- Status: {performance_results['status'].upper()}
- CPU Usage: {performance_results['metrics']['cpu_usage']}
- Memory Usage: {performance_results['metrics']['memory_usage']}
- Disk Usage: {performance_results['metrics']['disk_usage']}
- Response Time: {performance_results['metrics']['response_time']}
- Active Connections: {performance_results['metrics']['active_connections']}
"""
        
        if performance_results['issues']:
            report += "\n### Performance Issues\n"
            for issue in performance_results['issues']:
                report += f"- ⚠️ {issue}\n"
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Production Monitoring Tool')
    parser.add_argument('--health-check', action='store_true', 
                       help='Run health checks only')
    parser.add_argument('--performance-test', action='store_true', 
                       help='Run performance tests only')
    parser.add_argument('--check-all', action='store_true', 
                       help='Run all checks and generate report')
    parser.add_argument('--alert-test', action='store_true', 
                       help='Test alert system')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument('--json', action='store_true', 
                       help='Output results in JSON format')
    
    args = parser.parse_args()
    
    if not any([args.health_check, args.performance_test, args.check_all, args.alert_test]):
        parser.print_help()
        return
    
    monitor = ProductionMonitor()
    
    try:
        if args.alert_test:
            logger.info("Testing alert system...")
            success = monitor.send_alert("Test alert from production monitor", "info")
            if success:
                print("✅ Alert test successful")
            else:
                print("❌ Alert test failed")
            return
        
        health_results = []
        performance_results = {}
        
        if args.health_check or args.check_all:
            health_results = monitor.comprehensive_health_check()
        
        if args.performance_test or args.check_all:
            performance_results = monitor.performance_test()
        
        if args.check_all:
            # Generate comprehensive report
            report = monitor.generate_report(health_results, performance_results)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(report)
                logger.info(f"Report saved to {args.output}")
            else:
                print(report)
            
            # Send alerts if there are issues
            health_analysis = monitor.analyze_health_results(health_results)
            if health_analysis['overall_status'] in ['critical', 'degraded']:
                alert_message = f"Production health check failed: {health_analysis['overall_status']}\n"
                alert_message += f"Unhealthy services: {health_analysis['summary']['unhealthy']}\n"
                alert_message += f"Degraded services: {health_analysis['summary']['degraded']}"
                monitor.send_alert(alert_message, 'critical' if health_analysis['overall_status'] == 'critical' else 'warning')
            
            if performance_results.get('status') == 'critical':
                alert_message = f"Performance issues detected:\n" + "\n".join(performance_results.get('issues', []))
                monitor.send_alert(alert_message, 'warning')
        
        elif args.json:
            # Output JSON results
            results = {
                'timestamp': datetime.now().isoformat(),
                'health_results': [{
                    'service': r.service,
                    'status': r.status,
                    'response_time': r.response_time,
                    'message': r.message,
                    'timestamp': r.timestamp.isoformat()
                } for r in health_results] if health_results else [],
                'performance_results': performance_results
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(results, f, indent=2)
            else:
                print(json.dumps(results, indent=2))
        
        # Exit with appropriate code
        if health_results:
            unhealthy_count = sum(1 for r in health_results if r.status == 'unhealthy')
            if unhealthy_count > 0:
                sys.exit(1)
        
        if performance_results and performance_results.get('status') == 'critical':
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Monitoring interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Monitoring failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()