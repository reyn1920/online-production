#!/usr/bin/env python3
"""
Health Monitor Module for API & Affiliate Command Center

This module provides health monitoring capabilities for external services,
including APIs and affiliate programs registered in the system.
"""

import sqlite3
import asyncio
import aiohttp
import json
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
import ssl
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNHEALTHY = "UNHEALTHY"
    INVALID_KEY = "INVALID_KEY"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"

class ServiceType(Enum):
    """Service type enumeration"""
    API = "api"
    AFFILIATE = "affiliate"

@dataclass
class HealthCheckResult:
    """Health check result data structure"""
    service_id: int
    service_name: str
    service_type: ServiceType
    status: HealthStatus
    response_time: float
    status_code: Optional[int]
    error_message: Optional[str]
    checked_at: datetime
    details: Dict[str, Any]

@dataclass
class ServiceConfig:
    """Service configuration for health checks"""
    id: int
    name: str
    service_type: ServiceType
    health_check_url: str
    api_key: Optional[str]
    headers: Dict[str, str]
    timeout: int
    expected_status_codes: List[int]
    is_active: bool

class HealthMonitor:
    """Health monitoring system for APIs and affiliate services"""
    
    def __init__(self, db_path: str = "right_perspective.db"):
        self.db_path = db_path
        self.session: Optional[aiohttp.ClientSession] = None
        self._init_database()
    
    def _init_database(self):
        """Initialize health monitoring database tables"""
        with sqlite3.connect(self.db_path) as conn:
            # Create health check logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS health_check_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_id INTEGER NOT NULL,
                    service_name TEXT NOT NULL,
                    service_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    response_time REAL,
                    status_code INTEGER,
                    error_message TEXT,
                    checked_at TEXT NOT NULL,
                    details TEXT
                )
            """)
            
            # Create index for efficient queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_health_logs_service_time 
                ON health_check_logs(service_id, checked_at)
            """)
            
            conn.commit()
    
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(
            ssl=ssl.create_default_context(),
            limit=100,
            limit_per_host=10
        )
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def get_active_services(self) -> List[ServiceConfig]:
        """Get all active services that need health monitoring"""
        services = []
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get active APIs
            api_cursor = conn.execute("""
                SELECT id, service_name, api_url, signup_url, is_active
                FROM api_registry 
                WHERE is_active = 1
            """)
            
            for row in api_cursor.fetchall():
                services.append(ServiceConfig(
                    id=row['id'],
                    name=row['service_name'],
                    service_type=ServiceType.API,
                    health_check_url=row['api_url'],
                    api_key=None,  # Will be loaded from secrets
                    headers={'User-Agent': 'TRAE-HealthMonitor/1.0'},
                    timeout=10,
                    expected_status_codes=[200, 201, 202],
                    is_active=bool(row['is_active'])
                ))
            
            # Get active affiliate programs
            affiliate_cursor = conn.execute("""
                SELECT id, program_name, program_url, signup_url, is_active
                FROM affiliate_programs 
                WHERE is_active = 1
            """)
            
            for row in affiliate_cursor.fetchall():
                services.append(ServiceConfig(
                    id=row['id'],
                    name=row['program_name'],
                    service_type=ServiceType.AFFILIATE,
                    health_check_url=row['signup_url'] or row['program_url'],
                    api_key=None,
                    headers={'User-Agent': 'TRAE-HealthMonitor/1.0'},
                    timeout=15,
                    expected_status_codes=[200, 301, 302],
                    is_active=bool(row['is_active'])
                ))
        
        return services
    
    async def check_service_health(self, service: ServiceConfig) -> HealthCheckResult:
        """Perform health check on a single service"""
        start_time = time.time()
        
        try:
            # Load API key from secrets if needed
            if service.service_type == ServiceType.API:
                service.api_key = self._load_api_key(service.name)
                if service.api_key:
                    service.headers['Authorization'] = f'Bearer {service.api_key}'
            
            # Perform HTTP request
            async with self.session.get(
                service.health_check_url,
                headers=service.headers,
                timeout=aiohttp.ClientTimeout(total=service.timeout)
            ) as response:
                response_time = time.time() - start_time
                
                # Determine health status
                if response.status in service.expected_status_codes:
                    status = HealthStatus.HEALTHY
                    error_message = None
                elif response.status == 401:
                    status = HealthStatus.INVALID_KEY
                    error_message = "Authentication failed - invalid API key"
                elif response.status >= 500:
                    status = HealthStatus.UNHEALTHY
                    error_message = f"Server error: {response.status}"
                else:
                    status = HealthStatus.DEGRADED
                    error_message = f"Unexpected status code: {response.status}"
                
                # Get response details
                try:
                    response_text = await response.text()
                    details = {
                        'response_size': len(response_text),
                        'content_type': response.headers.get('content-type', 'unknown')
                    }
                except:
                    details = {'response_size': 0, 'content_type': 'unknown'}
                
                return HealthCheckResult(
                    service_id=service.id,
                    service_name=service.name,
                    service_type=service.service_type,
                    status=status,
                    response_time=response_time,
                    status_code=response.status,
                    error_message=error_message,
                    checked_at=datetime.now(timezone.utc),
                    details=details
                )
        
        except asyncio.TimeoutError:
            return HealthCheckResult(
                service_id=service.id,
                service_name=service.name,
                service_type=service.service_type,
                status=HealthStatus.TIMEOUT,
                response_time=time.time() - start_time,
                status_code=None,
                error_message="Request timeout",
                checked_at=datetime.now(timezone.utc),
                details={'timeout': service.timeout}
            )
        
        except Exception as e:
            return HealthCheckResult(
                service_id=service.id,
                service_name=service.name,
                service_type=service.service_type,
                status=HealthStatus.UNHEALTHY,
                response_time=time.time() - start_time,
                status_code=None,
                error_message=str(e),
                checked_at=datetime.now(timezone.utc),
                details={'error_type': type(e).__name__}
            )
    
    def _load_api_key(self, service_name: str) -> Optional[str]:
        """Load API key from secure storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT encrypted_value FROM secrets WHERE service_name = ?",
                    (service_name,)
                )
                row = cursor.fetchone()
                if row:
                    # In a real implementation, this would decrypt the value
                    # For now, return the stored value (assuming it's already decrypted)
                    return row[0]
        except Exception as e:
            logger.warning(f"Failed to load API key for {service_name}: {e}")
        return None
    
    def save_health_result(self, result: HealthCheckResult):
        """Save health check result to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO health_check_logs (
                    service_id, service_name, service_type, status,
                    response_time, status_code, error_message, checked_at, details
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.service_id,
                result.service_name,
                result.service_type.value,
                result.status.value,
                result.response_time,
                result.status_code,
                result.error_message,
                result.checked_at.isoformat(),
                json.dumps(result.details)
            ))
            
            # Update the service's last health status
            if result.service_type == ServiceType.API:
                conn.execute("""
                    UPDATE api_registry 
                    SET last_health_status = ?
                    WHERE id = ?
                """, (result.status.value, result.service_id))
            else:
                conn.execute("""
                    UPDATE affiliate_programs 
                    SET last_health_status = ?
                    WHERE id = ?
                """, (result.status.value, result.service_id))
            
            conn.commit()
    
    async def run_health_checks(self) -> Dict[str, Any]:
        """Run health checks on all active services"""
        services = self.get_active_services()
        results = []
        
        logger.info(f"Starting health checks for {len(services)} services")
        
        # Run health checks concurrently
        tasks = [self.check_service_health(service) for service in services]
        health_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        healthy_count = 0
        unhealthy_count = 0
        
        for i, result in enumerate(health_results):
            if isinstance(result, Exception):
                logger.error(f"Health check failed for {services[i].name}: {result}")
                unhealthy_count += 1
                continue
            
            results.append(result)
            self.save_health_result(result)
            
            if result.status == HealthStatus.HEALTHY:
                healthy_count += 1
            else:
                unhealthy_count += 1
                logger.warning(
                    f"Service {result.service_name} is {result.status.value}: {result.error_message}"
                )
        
        summary = {
            'total_services': len(services),
            'healthy_services': healthy_count,
            'unhealthy_services': unhealthy_count,
            'check_completed_at': datetime.now(timezone.utc).isoformat(),
            'results': [{
                'service_name': r.service_name,
                'service_type': r.service_type.value,
                'status': r.status.value,
                'response_time': r.response_time,
                'error_message': r.error_message
            } for r in results if isinstance(r, HealthCheckResult)]
        }
        
        logger.info(
            f"Health check completed: {healthy_count} healthy, {unhealthy_count} unhealthy"
        )
        
        return summary
    
    def get_service_health_history(self, service_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get health check history for a specific service"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM health_check_logs 
                WHERE service_id = ?
                ORDER BY checked_at DESC 
                LIMIT ?
            """, (service_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_overall_health_summary(self) -> Dict[str, Any]:
        """Get overall health summary of all services"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            # Get latest status for each service
            cursor = conn.execute("""
                SELECT 
                    service_name,
                    service_type,
                    status,
                    response_time,
                    checked_at
                FROM health_check_logs h1
                WHERE checked_at = (
                    SELECT MAX(checked_at) 
                    FROM health_check_logs h2 
                    WHERE h2.service_id = h1.service_id
                )
                ORDER BY service_name
            """)
            
            services = [dict(row) for row in cursor.fetchall()]
            
            # Calculate summary statistics
            total_services = len(services)
            healthy_services = len([s for s in services if s['status'] == 'HEALTHY'])
            avg_response_time = sum(s['response_time'] or 0 for s in services) / max(total_services, 1)
            
            return {
                'total_services': total_services,
                'healthy_services': healthy_services,
                'unhealthy_services': total_services - healthy_services,
                'health_percentage': (healthy_services / max(total_services, 1)) * 100,
                'average_response_time': avg_response_time,
                'services': services,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }

# Example usage and testing
async def example_usage():
    """Example of how to use the Health Monitor"""
    async with HealthMonitor() as monitor:
        # Run health checks
        summary = await monitor.run_health_checks()
        
        print("Health Check Summary:")
        print(json.dumps(summary, indent=2, default=str))
        
        # Get overall health summary
        health_summary = monitor.get_overall_health_summary()
        print("\nOverall Health Summary:")
        print(json.dumps(health_summary, indent=2, default=str))

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())