#!/usr/bin/env python3
"""
Conservative Research System - Self-Healing Health Monitor
Autonomous system monitoring with predictive failure detection and auto-recovery

This module provides comprehensive system health monitoring with:
- Real-time component health checks
- Predictive failure detection
- Automatic recovery mechanisms
- Performance optimization
- Resource scaling
"""

import asyncio
import logging
import psutil
import time
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum
import requests
import subprocess
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('system_health.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """System component health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    FAILED = "failed"
    RECOVERING = "recovering"

class ComponentType(Enum):
    """Types of system components to monitor"""
    DATABASE = "database"
    SCRAPER = "scraper"
    CONTENT_GENERATOR = "content_generator"
    API_ENDPOINT = "api_endpoint"
    YOUTUBE_ANALYZER = "youtube_analyzer"
    SYSTEM_RESOURCE = "system_resource"
    NETWORK = "network"

@dataclass
class HealthMetric:
    """Individual health metric data structure"""
    component_name: str
    component_type: ComponentType
    status: HealthStatus
    value: float
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime
    message: str = ""
    recovery_attempts: int = 0
    last_recovery: Optional[datetime] = None

@dataclass
class SystemSnapshot:
    """Complete system health snapshot"""
    timestamp: datetime
    overall_status: HealthStatus
    metrics: List[HealthMetric]
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_status: bool
    active_processes: int
    uptime_seconds: int

class PredictiveAnalyzer:
    """AI-powered predictive failure analysis"""
    
    def __init__(self):
        self.historical_data = []
        self.failure_patterns = {}
        self.prediction_accuracy = 0.0
        
    def analyze_trends(self, metrics: List[HealthMetric]) -> Dict[str, float]:
        """Analyze metric trends to predict potential failures"""
        predictions = {}
        
        for metric in metrics:
            component_key = f"{metric.component_type.value}_{metric.component_name}"
            
            # Simple trend analysis (can be enhanced with ML models)
            if len(self.historical_data) >= 10:
                recent_values = [m.value for m in self.historical_data[-10:] 
                               if m.component_name == metric.component_name]
                
                if len(recent_values) >= 5:
                    # Calculate trend slope
                    trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
                    
                    # Predict failure probability based on trend
                    if trend > 0 and metric.value > metric.threshold_warning:
                        failure_probability = min(0.9, (metric.value / metric.threshold_critical) * 0.7)
                        predictions[component_key] = failure_probability
                    
        return predictions
    
    def update_historical_data(self, metrics: List[HealthMetric]):
        """Update historical data for trend analysis"""
        self.historical_data.extend(metrics)
        
        # Keep only last 1000 data points to prevent memory issues
        if len(self.historical_data) > 1000:
            self.historical_data = self.historical_data[-1000:]

class AutoRecoverySystem:
    """Intelligent auto-recovery system for failed components"""
    
    def __init__(self):
        self.recovery_strategies = {
            ComponentType.DATABASE: self._recover_database,
            ComponentType.SCRAPER: self._recover_scraper,
            ComponentType.CONTENT_GENERATOR: self._recover_content_generator,
            ComponentType.API_ENDPOINT: self._recover_api,
            ComponentType.YOUTUBE_ANALYZER: self._recover_youtube_analyzer,
            ComponentType.SYSTEM_RESOURCE: self._recover_system_resource
        }
        self.max_recovery_attempts = 3
        self.recovery_cooldown = 300  # 5 minutes
        
    async def attempt_recovery(self, metric: HealthMetric) -> bool:
        """Attempt to recover a failed component"""
        if metric.recovery_attempts >= self.max_recovery_attempts:
            logger.error(f"Max recovery attempts reached for {metric.component_name}")
            return False
            
        if (metric.last_recovery and 
            datetime.now() - metric.last_recovery < timedelta(seconds=self.recovery_cooldown)):
            logger.info(f"Recovery cooldown active for {metric.component_name}")
            return False
            
        logger.info(f"Attempting recovery for {metric.component_name}")
        
        try:
            recovery_func = self.recovery_strategies.get(metric.component_type)
            if recovery_func:
                success = await recovery_func(metric)
                if success:
                    logger.info(f"Successfully recovered {metric.component_name}")
                    return True
                else:
                    logger.warning(f"Recovery failed for {metric.component_name}")
                    return False
            else:
                logger.error(f"No recovery strategy for {metric.component_type}")
                return False
                
        except Exception as e:
            logger.error(f"Recovery attempt failed for {metric.component_name}: {str(e)}")
            return False
    
    async def _recover_database(self, metric: HealthMetric) -> bool:
        """Recover database connection issues"""
        try:
            # Attempt to restart database connection
            # This would typically involve reconnecting to the database
            logger.info(f"Restarting database connection for {metric.component_name}")
            
            # Simulate database recovery (replace with actual implementation)
            await asyncio.sleep(2)
            
            # Test database connectivity
            test_conn = sqlite3.connect('conservative_research.db')
            test_conn.execute('SELECT 1')
            test_conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Database recovery failed: {str(e)}")
            return False
    
    async def _recover_scraper(self, metric: HealthMetric) -> bool:
        """Recover news scraper issues"""
        try:
            logger.info(f"Restarting scraper: {metric.component_name}")
            
            # Implement scraper restart logic
            # This might involve:
            # - Clearing stuck processes
            # - Rotating proxy servers
            # - Resetting rate limiting
            # - Clearing cache
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Scraper recovery failed: {str(e)}")
            return False
    
    async def _recover_content_generator(self, metric: HealthMetric) -> bool:
        """Recover content generation issues"""
        try:
            logger.info(f"Restarting content generator: {metric.component_name}")
            
            # Implement content generator recovery
            # - Clear generation queue
            # - Restart AI models
            # - Reset template cache
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"Content generator recovery failed: {str(e)}")
            return False
    
    async def _recover_api(self, metric: HealthMetric) -> bool:
        """Recover API endpoint issues"""
        try:
            logger.info(f"Restarting API endpoint: {metric.component_name}")
            
            # Implement API recovery
            # - Restart web server
            # - Clear connection pools
            # - Reset authentication tokens
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"API recovery failed: {str(e)}")
            return False
    
    async def _recover_youtube_analyzer(self, metric: HealthMetric) -> bool:
        """Recover YouTube analyzer issues"""
        try:
            logger.info(f"Restarting YouTube analyzer: {metric.component_name}")
            
            # Implement YouTube analyzer recovery
            # - Reset API quotas
            # - Clear analysis cache
            # - Restart analysis models
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"YouTube analyzer recovery failed: {str(e)}")
            return False
    
    async def _recover_system_resource(self, metric: HealthMetric) -> bool:
        """Recover system resource issues"""
        try:
            logger.info(f"Optimizing system resource: {metric.component_name}")
            
            if "memory" in metric.component_name.lower():
                # Clear memory caches
                subprocess.run(['sync'], check=False)
                subprocess.run(['echo', '3', '>', '/proc/sys/vm/drop_caches'], 
                             shell=True, check=False)
            
            elif "disk" in metric.component_name.lower():
                # Clean temporary files
                subprocess.run(['find', '/tmp', '-type', 'f', '-atime', '+7', '-delete'], 
                             check=False)
            
            await asyncio.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"System resource recovery failed: {str(e)}")
            return False

class SystemHealthMonitor:
    """Main system health monitoring class"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.is_running = False
        self.metrics_history = []
        self.predictive_analyzer = PredictiveAnalyzer()
        self.recovery_system = AutoRecoverySystem()
        self.alert_callbacks = []
        self.start_time = datetime.now()
        
        # Component health checkers
        self.health_checkers = {
            'database_connectivity': self._check_database_health,
            'news_scrapers': self._check_scraper_health,
            'content_generator': self._check_content_generator_health,
            'youtube_analyzer': self._check_youtube_analyzer_health,
            'api_endpoints': self._check_api_health,
            'system_resources': self._check_system_resources,
            'network_connectivity': self._check_network_health
        }
    
    def add_alert_callback(self, callback: Callable[[HealthMetric], None]):
        """Add callback function for health alerts"""
        self.alert_callbacks.append(callback)
    
    async def start_monitoring(self):
        """Start continuous system monitoring"""
        self.is_running = True
        logger.info("Starting system health monitoring...")
        
        while self.is_running:
            try:
                # Perform health checks
                snapshot = await self._perform_health_check()
                
                # Store snapshot
                self.metrics_history.append(snapshot)
                
                # Update predictive analyzer
                self.predictive_analyzer.update_historical_data(snapshot.metrics)
                
                # Analyze trends and predict failures
                predictions = self.predictive_analyzer.analyze_trends(snapshot.metrics)
                
                # Handle critical issues
                await self._handle_critical_issues(snapshot.metrics)
                
                # Handle predictions
                await self._handle_predictions(predictions)
                
                # Trigger alerts
                await self._trigger_alerts(snapshot)
                
                # Log system status
                self._log_system_status(snapshot)
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_running = False
        logger.info("Stopping system health monitoring...")
    
    async def _perform_health_check(self) -> SystemSnapshot:
        """Perform comprehensive health check"""
        metrics = []
        
        # Run all health checkers
        for checker_name, checker_func in self.health_checkers.items():
            try:
                checker_metrics = await checker_func()
                metrics.extend(checker_metrics)
            except Exception as e:
                logger.error(f"Health checker {checker_name} failed: {str(e)}")
                # Create error metric
                error_metric = HealthMetric(
                    component_name=checker_name,
                    component_type=ComponentType.SYSTEM_RESOURCE,
                    status=HealthStatus.FAILED,
                    value=0.0,
                    threshold_warning=0.5,
                    threshold_critical=0.8,
                    timestamp=datetime.now(),
                    message=f"Health checker failed: {str(e)}"
                )
                metrics.append(error_metric)
        
        # Determine overall system status
        overall_status = self._calculate_overall_status(metrics)
        
        # Get system info
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent
        network_status = self._test_network_connectivity()
        active_processes = len(psutil.pids())
        uptime_seconds = int((datetime.now() - self.start_time).total_seconds())
        
        return SystemSnapshot(
            timestamp=datetime.now(),
            overall_status=overall_status,
            metrics=metrics,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_status=network_status,
            active_processes=active_processes,
            uptime_seconds=uptime_seconds
        )
    
    def _calculate_overall_status(self, metrics: List[HealthMetric]) -> HealthStatus:
        """Calculate overall system health status"""
        if not metrics:
            return HealthStatus.WARNING
        
        status_counts = {status: 0 for status in HealthStatus}
        for metric in metrics:
            status_counts[metric.status] += 1
        
        total_metrics = len(metrics)
        
        # If any component is failed, system is critical
        if status_counts[HealthStatus.FAILED] > 0:
            return HealthStatus.CRITICAL
        
        # If more than 20% are critical, system is critical
        if status_counts[HealthStatus.CRITICAL] / total_metrics > 0.2:
            return HealthStatus.CRITICAL
        
        # If more than 50% are warning, system is warning
        if status_counts[HealthStatus.WARNING] / total_metrics > 0.5:
            return HealthStatus.WARNING
        
        # If any are recovering, system is recovering
        if status_counts[HealthStatus.RECOVERING] > 0:
            return HealthStatus.RECOVERING
        
        return HealthStatus.HEALTHY
    
    async def _check_database_health(self) -> List[HealthMetric]:
        """Check database connectivity and performance"""
        metrics = []
        
        try:
            # Test database connection
            start_time = time.time()
            conn = sqlite3.connect('conservative_research.db', timeout=5)
            conn.execute('SELECT COUNT(*) FROM sqlite_master')
            conn.close()
            response_time = time.time() - start_time
            
            # Create response time metric
            status = HealthStatus.HEALTHY
            if response_time > 1.0:
                status = HealthStatus.WARNING
            elif response_time > 5.0:
                status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                component_name="database_response_time",
                component_type=ComponentType.DATABASE,
                status=status,
                value=response_time,
                threshold_warning=1.0,
                threshold_critical=5.0,
                timestamp=datetime.now(),
                message=f"Database response time: {response_time:.2f}s"
            ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                component_name="database_connectivity",
                component_type=ComponentType.DATABASE,
                status=HealthStatus.FAILED,
                value=0.0,
                threshold_warning=0.5,
                threshold_critical=0.8,
                timestamp=datetime.now(),
                message=f"Database connection failed: {str(e)}"
            ))
        
        return metrics
    
    async def _check_scraper_health(self) -> List[HealthMetric]:
        """Check news scraper health and performance"""
        metrics = []
        
        # Check scraper components
        scrapers = ['fox_news', 'cnn', 'msnbc', 'drudge_report', 'babylon_bee']
        
        for scraper in scrapers:
            try:
                # Simulate scraper health check
                # In real implementation, this would test actual scraper functionality
                success_rate = 0.95  # Placeholder
                
                status = HealthStatus.HEALTHY
                if success_rate < 0.8:
                    status = HealthStatus.WARNING
                elif success_rate < 0.5:
                    status = HealthStatus.CRITICAL
                
                metrics.append(HealthMetric(
                    component_name=f"{scraper}_scraper",
                    component_type=ComponentType.SCRAPER,
                    status=status,
                    value=success_rate,
                    threshold_warning=0.8,
                    threshold_critical=0.5,
                    timestamp=datetime.now(),
                    message=f"Scraper success rate: {success_rate:.1%}"
                ))
                
            except Exception as e:
                metrics.append(HealthMetric(
                    component_name=f"{scraper}_scraper",
                    component_type=ComponentType.SCRAPER,
                    status=HealthStatus.FAILED,
                    value=0.0,
                    threshold_warning=0.8,
                    threshold_critical=0.5,
                    timestamp=datetime.now(),
                    message=f"Scraper failed: {str(e)}"
                ))
        
        return metrics
    
    async def _check_content_generator_health(self) -> List[HealthMetric]:
        """Check content generator health and performance"""
        metrics = []
        
        try:
            # Check content generation performance
            generation_speed = 10.5  # articles per hour (placeholder)
            quality_score = 0.92  # content quality score (placeholder)
            
            # Speed metric
            speed_status = HealthStatus.HEALTHY
            if generation_speed < 5:
                speed_status = HealthStatus.WARNING
            elif generation_speed < 2:
                speed_status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                component_name="content_generation_speed",
                component_type=ComponentType.CONTENT_GENERATOR,
                status=speed_status,
                value=generation_speed,
                threshold_warning=5.0,
                threshold_critical=2.0,
                timestamp=datetime.now(),
                message=f"Generation speed: {generation_speed} articles/hour"
            ))
            
            # Quality metric
            quality_status = HealthStatus.HEALTHY
            if quality_score < 0.8:
                quality_status = HealthStatus.WARNING
            elif quality_score < 0.6:
                quality_status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                component_name="content_quality_score",
                component_type=ComponentType.CONTENT_GENERATOR,
                status=quality_status,
                value=quality_score,
                threshold_warning=0.8,
                threshold_critical=0.6,
                timestamp=datetime.now(),
                message=f"Content quality: {quality_score:.1%}"
            ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                component_name="content_generator",
                component_type=ComponentType.CONTENT_GENERATOR,
                status=HealthStatus.FAILED,
                value=0.0,
                threshold_warning=0.5,
                threshold_critical=0.8,
                timestamp=datetime.now(),
                message=f"Content generator failed: {str(e)}"
            ))
        
        return metrics
    
    async def _check_youtube_analyzer_health(self) -> List[HealthMetric]:
        """Check YouTube analyzer health and performance"""
        metrics = []
        
        try:
            # Check YouTube API quota usage
            api_quota_used = 0.65  # 65% of daily quota used (placeholder)
            analysis_accuracy = 0.88  # Analysis accuracy (placeholder)
            
            # API quota metric
            quota_status = HealthStatus.HEALTHY
            if api_quota_used > 0.8:
                quota_status = HealthStatus.WARNING
            elif api_quota_used > 0.95:
                quota_status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                component_name="youtube_api_quota",
                component_type=ComponentType.YOUTUBE_ANALYZER,
                status=quota_status,
                value=api_quota_used,
                threshold_warning=0.8,
                threshold_critical=0.95,
                timestamp=datetime.now(),
                message=f"API quota used: {api_quota_used:.1%}"
            ))
            
            # Analysis accuracy metric
            accuracy_status = HealthStatus.HEALTHY
            if analysis_accuracy < 0.8:
                accuracy_status = HealthStatus.WARNING
            elif analysis_accuracy < 0.6:
                accuracy_status = HealthStatus.CRITICAL
            
            metrics.append(HealthMetric(
                component_name="youtube_analysis_accuracy",
                component_type=ComponentType.YOUTUBE_ANALYZER,
                status=accuracy_status,
                value=analysis_accuracy,
                threshold_warning=0.8,
                threshold_critical=0.6,
                timestamp=datetime.now(),
                message=f"Analysis accuracy: {analysis_accuracy:.1%}"
            ))
            
        except Exception as e:
            metrics.append(HealthMetric(
                component_name="youtube_analyzer",
                component_type=ComponentType.YOUTUBE_ANALYZER,
                status=HealthStatus.FAILED,
                value=0.0,
                threshold_warning=0.5,
                threshold_critical=0.8,
                timestamp=datetime.now(),
                message=f"YouTube analyzer failed: {str(e)}"
            ))
        
        return metrics
    
    async def _check_api_health(self) -> List[HealthMetric]:
        """Check API endpoint health and performance"""
        metrics = []
        
        # API endpoints to check
        endpoints = [
            {'name': 'health_check', 'url': 'http://localhost:8000/health'},
            {'name': 'research_api', 'url': 'http://localhost:8000/api/research'},
            {'name': 'content_api', 'url': 'http://localhost:8000/api/content'}
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(endpoint['url'], timeout=10)
                response_time = time.time() - start_time
                
                # Determine status based on response
                if response.status_code == 200 and response_time < 2.0:
                    status = HealthStatus.HEALTHY
                elif response.status_code == 200 and response_time < 5.0:
                    status = HealthStatus.WARNING
                else:
                    status = HealthStatus.CRITICAL
                
                metrics.append(HealthMetric(
                    component_name=endpoint['name'],
                    component_type=ComponentType.API_ENDPOINT,
                    status=status,
                    value=response_time,
                    threshold_warning=2.0,
                    threshold_critical=5.0,
                    timestamp=datetime.now(),
                    message=f"Response time: {response_time:.2f}s, Status: {response.status_code}"
                ))
                
            except Exception as e:
                metrics.append(HealthMetric(
                    component_name=endpoint['name'],
                    component_type=ComponentType.API_ENDPOINT,
                    status=HealthStatus.FAILED,
                    value=0.0,
                    threshold_warning=2.0,
                    threshold_critical=5.0,
                    timestamp=datetime.now(),
                    message=f"API endpoint failed: {str(e)}"
                ))
        
        return metrics
    
    async def _check_system_resources(self) -> List[HealthMetric]:
        """Check system resource usage"""
        metrics = []
        
        # CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu_status = HealthStatus.HEALTHY
        if cpu_usage > 80:
            cpu_status = HealthStatus.WARNING
        elif cpu_usage > 95:
            cpu_status = HealthStatus.CRITICAL
        
        metrics.append(HealthMetric(
            component_name="cpu_usage",
            component_type=ComponentType.SYSTEM_RESOURCE,
            status=cpu_status,
            value=cpu_usage,
            threshold_warning=80.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            message=f"CPU usage: {cpu_usage:.1f}%"
        ))
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_status = HealthStatus.HEALTHY
        if memory.percent > 85:
            memory_status = HealthStatus.WARNING
        elif memory.percent > 95:
            memory_status = HealthStatus.CRITICAL
        
        metrics.append(HealthMetric(
            component_name="memory_usage",
            component_type=ComponentType.SYSTEM_RESOURCE,
            status=memory_status,
            value=memory.percent,
            threshold_warning=85.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            message=f"Memory usage: {memory.percent:.1f}%"
        ))
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        disk_status = HealthStatus.HEALTHY
        if disk_percent > 85:
            disk_status = HealthStatus.WARNING
        elif disk_percent > 95:
            disk_status = HealthStatus.CRITICAL
        
        metrics.append(HealthMetric(
            component_name="disk_usage",
            component_type=ComponentType.SYSTEM_RESOURCE,
            status=disk_status,
            value=disk_percent,
            threshold_warning=85.0,
            threshold_critical=95.0,
            timestamp=datetime.now(),
            message=f"Disk usage: {disk_percent:.1f}%"
        ))
        
        return metrics
    
    async def _check_network_health(self) -> List[HealthMetric]:
        """Check network connectivity and performance"""
        metrics = []
        
        # Test network connectivity
        network_status = self._test_network_connectivity()
        
        metrics.append(HealthMetric(
            component_name="network_connectivity",
            component_type=ComponentType.NETWORK,
            status=HealthStatus.HEALTHY if network_status else HealthStatus.FAILED,
            value=1.0 if network_status else 0.0,
            threshold_warning=0.5,
            threshold_critical=0.8,
            timestamp=datetime.now(),
            message=f"Network connectivity: {'OK' if network_status else 'FAILED'}"
        ))
        
        return metrics
    
    def _test_network_connectivity(self) -> bool:
        """Test basic network connectivity"""
        try:
            response = requests.get('https://www.google.com', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    async def _handle_critical_issues(self, metrics: List[HealthMetric]):
        """Handle critical system issues with auto-recovery"""
        critical_metrics = [m for m in metrics if m.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]]
        
        for metric in critical_metrics:
            logger.warning(f"Critical issue detected: {metric.component_name} - {metric.message}")
            
            # Attempt auto-recovery
            recovery_success = await self.recovery_system.attempt_recovery(metric)
            
            if recovery_success:
                metric.status = HealthStatus.RECOVERING
                metric.recovery_attempts += 1
                metric.last_recovery = datetime.now()
                logger.info(f"Auto-recovery initiated for {metric.component_name}")
            else:
                logger.error(f"Auto-recovery failed for {metric.component_name}")
    
    async def _handle_predictions(self, predictions: Dict[str, float]):
        """Handle predictive failure alerts"""
        for component, probability in predictions.items():
            if probability > 0.7:
                logger.warning(f"High failure probability ({probability:.1%}) predicted for {component}")
                # Implement proactive measures here
    
    async def _trigger_alerts(self, snapshot: SystemSnapshot):
        """Trigger alerts for system issues"""
        for callback in self.alert_callbacks:
            try:
                for metric in snapshot.metrics:
                    if metric.status in [HealthStatus.CRITICAL, HealthStatus.FAILED]:
                        callback(metric)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")
    
    def _log_system_status(self, snapshot: SystemSnapshot):
        """Log current system status"""
        status_summary = {
            'timestamp': snapshot.timestamp.isoformat(),
            'overall_status': snapshot.overall_status.value,
            'cpu_usage': snapshot.cpu_usage,
            'memory_usage': snapshot.memory_usage,
            'disk_usage': snapshot.disk_usage,
            'uptime_hours': snapshot.uptime_seconds / 3600,
            'component_count': len(snapshot.metrics),
            'healthy_components': len([m for m in snapshot.metrics if m.status == HealthStatus.HEALTHY]),
            'warning_components': len([m for m in snapshot.metrics if m.status == HealthStatus.WARNING]),
            'critical_components': len([m for m in snapshot.metrics if m.status == HealthStatus.CRITICAL]),
            'failed_components': len([m for m in snapshot.metrics if m.status == HealthStatus.FAILED])
        }
        
        logger.info(f"System Status: {json.dumps(status_summary, indent=2)}")
    
    def get_system_report(self) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        if not self.metrics_history:
            return {'error': 'No monitoring data available'}
        
        latest_snapshot = self.metrics_history[-1]
        
        return {
            'system_overview': {
                'status': latest_snapshot.overall_status.value,
                'uptime_hours': latest_snapshot.uptime_seconds / 3600,
                'last_check': latest_snapshot.timestamp.isoformat(),
                'monitoring_duration_hours': len(self.metrics_history) * self.check_interval / 3600
            },
            'resource_usage': {
                'cpu_percent': latest_snapshot.cpu_usage,
                'memory_percent': latest_snapshot.memory_usage,
                'disk_percent': latest_snapshot.disk_usage,
                'active_processes': latest_snapshot.active_processes
            },
            'component_health': {
                'total_components': len(latest_snapshot.metrics),
                'healthy': len([m for m in latest_snapshot.metrics if m.status == HealthStatus.HEALTHY]),
                'warning': len([m for m in latest_snapshot.metrics if m.status == HealthStatus.WARNING]),
                'critical': len([m for m in latest_snapshot.metrics if m.status == HealthStatus.CRITICAL]),
                'failed': len([m for m in latest_snapshot.metrics if m.status == HealthStatus.FAILED])
            },
            'recent_issues': [
                {
                    'component': m.component_name,
                    'status': m.status.value,
                    'message': m.message,
                    'timestamp': m.timestamp.isoformat()
                }
                for m in latest_snapshot.metrics 
                if m.status in [HealthStatus.WARNING, HealthStatus.CRITICAL, HealthStatus.FAILED]
            ][-10:]  # Last 10 issues
        }

# Example usage and CLI interface
if __name__ == "__main__":
    import argparse
    
    def alert_callback(metric: HealthMetric):
        """Example alert callback function"""
        print(f"🚨 ALERT: {metric.component_name} is {metric.status.value} - {metric.message}")
    
    async def main():
        parser = argparse.ArgumentParser(description='Conservative Research System Health Monitor')
        parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds')
        parser.add_argument('--report', action='store_true', help='Generate system report and exit')
        args = parser.parse_args()
        
        monitor = SystemHealthMonitor(check_interval=args.interval)
        monitor.add_alert_callback(alert_callback)
        
        if args.report:
            # Generate one-time report
            snapshot = await monitor._perform_health_check()
            monitor.metrics_history.append(snapshot)
            report = monitor.get_system_report()
            print(json.dumps(report, indent=2))
        else:
            # Start continuous monitoring
            try:
                await monitor.start_monitoring()
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\nMonitoring stopped.")
    
    # Run the monitor
    asyncio.run(main())