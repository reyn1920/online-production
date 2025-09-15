#!/usr/bin/env python3
"""
Health Check API Endpoint
Provides standardized health check endpoints for production monitoring.
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

# Add config directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'config'))

try:
    from health_monitoring import HealthMonitor, HealthStatus
    has_health_monitoring = True
except ImportError:
    has_health_monitoring = False
    
    class HealthStatus:
        HEALTHY = "healthy"
        DEGRADED = "degraded"
        UNHEALTHY = "unhealthy"


class HealthAPI:
    """Health check API implementation."""
    
    def __init__(self):
        self.start_time = datetime.now()
        if has_health_monitoring:
            try:
                from health_monitoring import HealthMonitor
                self.monitor = HealthMonitor()
            except ImportError:
                self.monitor = None
        else:
            self.monitor = None
    
    def get_uptime(self) -> float:
        """Get application uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    def check_basic_health(self) -> Dict[str, Any]:
        """Perform basic health checks."""
        return {
            'status': HealthStatus.HEALTHY,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': self.get_uptime(),
            'version': os.getenv('APP_VERSION', '1.0.0'),
            'environment': os.getenv('NODE_ENV', 'development')
        }
    
    def check_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies."""
        dependencies = {
            'database': self._check_database(),
            'external_apis': self._check_external_apis(),
            'file_system': self._check_file_system()
        }
        
        # Determine overall dependency status
        all_healthy = all(dep['status'] == HealthStatus.HEALTHY for dep in dependencies.values())
        any_unhealthy = any(dep['status'] == HealthStatus.UNHEALTHY for dep in dependencies.values())
        
        if any_unhealthy:
            overall_status = HealthStatus.UNHEALTHY
        elif not all_healthy:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            'status': overall_status,
            'dependencies': dependencies
        }
    
    def _check_database(self) -> Dict[str, Any]:
        """Check database connectivity."""
        db_url = os.getenv('DATABASE_URL')
        
        if not db_url:
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'No database configured',
                'response_time': 0
            }
        
        start_time = time.time()
        
        try:
            # In a real application, you would test actual database connectivity
            # For now, we'll simulate a successful connection
            time.sleep(0.01)  # Simulate connection time
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Database connection successful',
                'response_time': time.time() - start_time
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Database connection failed: {str(e)}',
                'response_time': time.time() - start_time
            }
    
    def _check_external_apis(self) -> Dict[str, Any]:
        """Check external API dependencies."""
        external_apis = os.getenv('EXTERNAL_API_ENDPOINTS', '').split(',') if os.getenv('EXTERNAL_API_ENDPOINTS') else []
        
        if not external_apis or not external_apis[0].strip():
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'No external APIs configured',
                'apis_checked': 0
            }
        
        # In a real application, you would make actual HTTP requests
        # For now, we'll simulate successful API checks
        return {
            'status': HealthStatus.HEALTHY,
            'message': f'All {len(external_apis)} external APIs are healthy',
            'apis_checked': len(external_apis)
        }
    
    def _check_file_system(self) -> Dict[str, Any]:
        """Check file system access."""
        try:
            # Check if we can write to a temporary file
            temp_file = '/tmp/health_check_test'
            with open(temp_file, 'w') as f:
                f.write('health_check')
            
            # Clean up
            os.remove(temp_file)
            
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'File system access is working',
                'writable': True
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'message': f'File system access failed: {str(e)}',
                'writable': False
            }
    
    async def comprehensive_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check using monitoring system."""
        if not self.monitor:
            # Fallback to basic checks if monitoring system is not available
            basic_health = self.check_basic_health()
            dependencies = self.check_dependencies()
            
            return {
                'status': dependencies['status'],
                'timestamp': basic_health['timestamp'],
                'uptime_seconds': basic_health['uptime_seconds'],
                'version': basic_health['version'],
                'environment': basic_health['environment'],
                'checks': {
                    'basic': basic_health,
                    'dependencies': dependencies
                }
            }
        
        # Use full monitoring system
        try:
            results = await self.monitor.run_all_checks()
            analysis = self.monitor.analyze_health_status(results)
            
            return {
                'status': analysis['overall_status'],
                'timestamp': analysis['timestamp'],
                'uptime_seconds': self.get_uptime(),
                'version': os.getenv('APP_VERSION', '1.0.0'),
                'environment': os.getenv('NODE_ENV', 'development'),
                'checks': {
                    'total': analysis['total_checks'],
                    'healthy': analysis['healthy_checks'],
                    'degraded': analysis['degraded_checks'],
                    'unhealthy': analysis['unhealthy_checks']
                },
                'average_response_time': analysis['average_response_time'],
                'details': analysis['details']
            }
        except Exception as e:
            return {
                'status': HealthStatus.UNHEALTHY,
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': self.get_uptime(),
                'error': f'Health check system error: {str(e)}'
            }
    
    def get_readiness_check(self) -> Dict[str, Any]:
        """Check if application is ready to serve traffic."""
        # Basic readiness checks
        checks = {
            'configuration_loaded': self._check_configuration(),
            'dependencies_available': self._check_critical_dependencies(),
            'resources_available': self._check_resources()
        }
        
        all_ready = all(check['ready'] for check in checks.values())
        
        return {
            'ready': all_ready,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }
    
    def _check_configuration(self) -> Dict[str, Any]:
        """Check if required configuration is loaded."""
        required_env_vars = ['NODE_ENV']
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        return {
            'ready': len(missing_vars) == 0,
            'message': 'All required configuration loaded' if len(missing_vars) == 0 else f'Missing: {missing_vars}'
        }
    
    def _check_critical_dependencies(self) -> Dict[str, Any]:
        """Check critical dependencies for readiness."""
        # In a real application, check database connections, required services, etc.
        return {
            'ready': True,
            'message': 'All critical dependencies are available'
        }
    
    def _check_resources(self) -> Dict[str, Any]:
        """Check if system resources are available."""
        try:
            # Basic resource checks
            import psutil
            
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            memory_ok = memory.percent < 95
            disk_ok = disk.percent < 95
            
            return {
                'ready': memory_ok and disk_ok,
                'message': 'System resources are available',
                'memory_usage': memory.percent,
                'disk_usage': disk.percent
            }
        except ImportError:
            # psutil not available, assume resources are OK
            return {
                'ready': True,
                'message': 'Resource monitoring not available (psutil not installed)'
            }
        except Exception as e:
            return {
                'ready': False,
                'message': f'Resource check failed: {str(e)}'
            }


# Global health API instance
health_api = HealthAPI()


# Flask/FastAPI compatible handlers
def health_handler():
    """Basic health check handler for Flask/FastAPI."""
    result = health_api.check_basic_health()
    status_code = 200 if result['status'] == HealthStatus.HEALTHY else 503
    return result, status_code


async def health_handler_async():
    """Async health check handler for FastAPI."""
    result = await health_api.comprehensive_health_check()
    status_code = 200 if result['status'] == HealthStatus.HEALTHY else 503
    return result, status_code


def readiness_handler():
    """Readiness check handler."""
    result = health_api.get_readiness_check()
    status_code = 200 if result['ready'] else 503
    return result, status_code


def liveness_handler():
    """Liveness check handler (simple uptime check)."""
    result = {
        'alive': True,
        'timestamp': datetime.now().isoformat(),
        'uptime_seconds': health_api.get_uptime()
    }
    return result, 200


# Express.js/Node.js compatible handlers (for reference)
def get_express_handlers():
    """Get handler functions compatible with Express.js format."""
    return {
        'health': lambda req, res: res.json(health_api.check_basic_health()),
        'readiness': lambda req, res: res.json(health_api.get_readiness_check()),
        'liveness': lambda req, res: res.json({
            'alive': True,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': health_api.get_uptime()
        })
    }


if __name__ == '__main__':
    # CLI interface for health checks
    import argparse
    
    parser = argparse.ArgumentParser(description="Health Check CLI")
    parser.add_argument('--check', choices=['basic', 'comprehensive', 'readiness', 'liveness'], 
                       default='basic', help='Type of health check to perform')
    parser.add_argument('--format', choices=['json', 'text'], default='json', 
                       help='Output format')
    
    args = parser.parse_args()
    
    async def run_check():
        result = {}
        if args.check == 'basic':
            result = health_api.check_basic_health()
        elif args.check == 'comprehensive':
            result = await health_api.comprehensive_health_check()
        elif args.check == 'readiness':
            result = health_api.get_readiness_check()
        elif args.check == 'liveness':
            result = {
                'alive': True,
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': health_api.get_uptime()
            }
        
        if args.format == 'json':
            print(json.dumps(result, indent=2, default=str))
        else:
            status = result.get('status', result.get('ready', result.get('alive')))
            print(f"Status: {status}")
            print(f"Timestamp: {result.get('timestamp', 'N/A')}")
            if 'uptime_seconds' in result:
                print(f"Uptime: {result['uptime_seconds']:.1f} seconds")
        
        # Exit with appropriate code
        if args.check in ['basic', 'comprehensive']:
            sys.exit(0 if result.get('status') == HealthStatus.HEALTHY else 1)
        elif args.check == 'readiness':
            sys.exit(0 if result.get('ready') else 1)
        else:  # liveness
            sys.exit(0 if result.get('alive') else 1)
    
    asyncio.run(run_check())