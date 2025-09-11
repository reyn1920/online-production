#!/usr/bin/env python3
"""
Prometheus Integration Module

Integrates Prometheus metrics collection with the existing performance monitoring system
to enable real-time performance tracking and automatic scaling based on metrics.

Features:
- Prometheus metrics export endpoint
- Custom application metrics
- Integration with existing performance monitor
- Real-time metrics collection
- Auto-scaling metrics support
- Health check metrics
- Resource utilization metrics
"""

import time
import logging
import threading
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from prometheus_client import (
    Counter, Gauge, Histogram, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    multiprocess, values
)
from flask import Flask, Response
import psutil
import asyncio
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import existing performance monitor
try:
    from backend.services.performance_monitor import performance_monitor
    from monitoring.performance_monitor import PerformanceMonitor as TraePerformanceMonitor
except ImportError:
    performance_monitor = None
    TraePerformanceMonitor = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PrometheusConfig:
    """Prometheus configuration"""
    metrics_port: int = 9090
    metrics_path: str = '/metrics'
    collection_interval: float = 15.0
    enable_multiprocess: bool = True
    registry_name: str = 'trae_ai'

class PrometheusMetrics:
    """Prometheus metrics definitions"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._init_metrics()
    
    def _init_metrics(self):
        """Initialize all Prometheus metrics"""
        
        # System metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )
        
        self.memory_usage = Gauge(
            'system_memory_usage_percent',
            'Memory usage percentage',
            registry=self.registry
        )
        
        self.disk_usage = Gauge(
            'system_disk_usage_percent',
            'Disk usage percentage',
            ['mount_point'],
            registry=self.registry
        )
        
        # Application metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'active_connections_total',
            'Number of active connections',
            registry=self.registry
        )
        
        # Model generation metrics
        self.model_generation_requests = Counter(
            'model_generation_requests_total',
            'Total model generation requests',
            ['status', 'model_type'],
            registry=self.registry
        )
        
        self.model_generation_duration = Histogram(
            'model_generation_duration_seconds',
            'Model generation duration in seconds',
            ['model_type'],
            registry=self.registry
        )
        
        self.model_generation_queue_size = Gauge(
            'model_generation_queue_size',
            'Number of pending model generation requests',
            registry=self.registry
        )
        
        # Database metrics
        self.database_connections = Gauge(
            'database_connections_active',
            'Number of active database connections',
            registry=self.registry
        )
        
        self.database_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['query_type'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Service health metrics
        self.service_health = Gauge(
            'service_health_status',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service_name'],
            registry=self.registry
        )
        
        # Auto-scaling metrics
        self.scaling_events = Counter(
            'scaling_events_total',
            'Total scaling events',
            ['action', 'resource_type'],
            registry=self.registry
        )
        
        self.resource_utilization = Gauge(
            'resource_utilization_percent',
            'Resource utilization percentage for scaling decisions',
            ['resource_type', 'service'],
            registry=self.registry
        )
        
        # Application info
        self.app_info = Info(
            'application_info',
            'Application information',
            registry=self.registry
        )
        
        # Set application info
        self.app_info.info({
            'version': '1.0.0',
            'environment': 'production',
            'build_time': datetime.now().isoformat()
        })

class PrometheusIntegration:
    """Main Prometheus integration class"""
    
    def __init__(self, config: PrometheusConfig = None):
        self.config = config or PrometheusConfig()
        self.registry = CollectorRegistry()
        self.metrics = PrometheusMetrics(self.registry)
        self.flask_app = None
        self.collection_thread = None
        self.running = False
        
        # Integration with existing monitors
        self.performance_monitor = performance_monitor
        self.trae_monitor = None
        if TraePerformanceMonitor:
            try:
                self.trae_monitor = TraePerformanceMonitor()
            except Exception as e:
                logger.warning(f"Could not initialize TRAE performance monitor: {e}")
    
    def start(self):
        """Start Prometheus integration"""
        if self.running:
            return
        
        self.running = True
        
        # Start metrics collection
        self._start_metrics_collection()
        
        # Start Flask app for metrics endpoint
        self._start_metrics_server()
        
        logger.info(f"Prometheus integration started on port {self.config.metrics_port}")
    
    def stop(self):
        """Stop Prometheus integration"""
        self.running = False
        
        if self.collection_thread:
            self.collection_thread.join(timeout=5)
        
        logger.info("Prometheus integration stopped")
    
    def _start_metrics_collection(self):
        """Start metrics collection thread"""
        self.collection_thread = threading.Thread(
            target=self._metrics_collection_loop,
            daemon=True
        )
        self.collection_thread.start()
    
    def _start_metrics_server(self):
        """Start Flask server for metrics endpoint"""
        self.flask_app = Flask(__name__)
        
        @self.flask_app.route(self.config.metrics_path)
        def metrics():
            """Metrics endpoint"""
            return Response(
                generate_latest(self.registry),
                mimetype=CONTENT_TYPE_LATEST
            )
        
        @self.flask_app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
        
        # Start Flask app in a separate thread
        server_thread = threading.Thread(
            target=lambda: self.flask_app.run(
                host='0.0.0.0',
                port=self.config.metrics_port,
                debug=False
            ),
            daemon=True
        )
        server_thread.start()
    
    def _metrics_collection_loop(self):
        """Main metrics collection loop"""
        while self.running:
            try:
                self._collect_system_metrics()
                self._collect_application_metrics()
                self._collect_service_health_metrics()
                time.sleep(self.config.collection_interval)
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                time.sleep(self.config.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.cpu_usage.set(cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.memory_usage.set(memory.percent)
            
            # Disk usage
            for partition in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    self.metrics.disk_usage.labels(
                        mount_point=partition.mountpoint
                    ).set(usage.percent)
                except (PermissionError, FileNotFoundError):
                    continue
            
            # Update resource utilization for scaling
            self.metrics.resource_utilization.labels(
                resource_type='cpu', service='system'
            ).set(cpu_percent)
            
            self.metrics.resource_utilization.labels(
                resource_type='memory', service='system'
            ).set(memory.percent)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_application_metrics(self):
        """Collect application-specific metrics"""
        try:
            # Integrate with existing performance monitor
            if self.performance_monitor:
                # Get metrics from existing performance monitor
                stats = self.performance_monitor.metrics_collector.get_all_metrics()
                
                for metric in stats:
                    if metric.name == 'model.generation.latency_ms':
                        # Convert to seconds for Prometheus
                        self.metrics.model_generation_duration.labels(
                            model_type='default'
                        ).observe(metric.value / 1000.0)
                    
                    elif metric.name == 'system.cpu.usage_percent':
                        self.metrics.resource_utilization.labels(
                            resource_type='cpu', service='application'
                        ).set(metric.value)
                    
                    elif metric.name == 'system.memory.usage_percent':
                        self.metrics.resource_utilization.labels(
                            resource_type='memory', service='application'
                        ).set(metric.value)
            
            # Integrate with TRAE performance monitor
            if self.trae_monitor:
                try:
                    app_metrics = self.trae_monitor.collect_application_metrics()
                    
                    # Update database connections
                    self.metrics.database_connections.set(app_metrics.database_connections)
                    
                    # Update resource utilization
                    self.metrics.resource_utilization.labels(
                        resource_type='cpu', service='trae_app'
                    ).set(app_metrics.cpu_usage_percent)
                    
                    self.metrics.resource_utilization.labels(
                        resource_type='memory', service='trae_app'
                    ).set(app_metrics.memory_usage_mb / 1024)  # Convert to percentage
                    
                except Exception as e:
                    logger.debug(f"Could not collect TRAE metrics: {e}")
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
    
    def _collect_service_health_metrics(self):
        """Collect service health metrics"""
        try:
            # Check various services
            services = {
                'main_app': 'http://localhost:8080/health',
                'content_agent': 'http://localhost:8001/health',
                'marketing_agent': 'http://localhost:8002/health',
                'monetization_bundle': 'http://localhost:8003/health',
                'analytics_dashboard': 'http://localhost:8004/health'
            }
            
            import requests
            
            for service_name, health_url in services.items():
                try:
                    response = requests.get(health_url, timeout=5)
                    health_status = 1 if response.status_code == 200 else 0
                except Exception:
                    health_status = 0
                
                self.metrics.service_health.labels(
                    service_name=service_name
                ).set(health_status)
            
        except Exception as e:
            logger.error(f"Error collecting service health metrics: {e}")
    
    def record_http_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics"""
        self.metrics.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status_code)
        ).inc()
        
        self.metrics.http_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
    
    def record_model_generation(self, model_type: str, status: str, duration: float):
        """Record model generation metrics"""
        self.metrics.model_generation_requests.labels(
            status=status,
            model_type=model_type
        ).inc()
        
        if status == 'success':
            self.metrics.model_generation_duration.labels(
                model_type=model_type
            ).observe(duration)
    
    def record_scaling_event(self, action: str, resource_type: str):
        """Record scaling event"""
        self.metrics.scaling_events.labels(
            action=action,
            resource_type=resource_type
        ).inc()
    
    def update_queue_size(self, queue_size: int):
        """Update model generation queue size"""
        self.metrics.model_generation_queue_size.set(queue_size)
    
    def record_cache_hit(self, cache_type: str):
        """Record cache hit"""
        self.metrics.cache_hits.labels(cache_type=cache_type).inc()
    
    def record_cache_miss(self, cache_type: str):
        """Record cache miss"""
        self.metrics.cache_misses.labels(cache_type=cache_type).inc()
    
    def record_database_query(self, query_type: str, duration: float):
        """Record database query metrics"""
        self.metrics.database_query_duration.labels(
            query_type=query_type
        ).observe(duration)

# Global Prometheus integration instance
prometheus_integration = None

def initialize_prometheus_integration(config: PrometheusConfig = None) -> PrometheusIntegration:
    """Initialize Prometheus integration"""
    global prometheus_integration
    
    if prometheus_integration is None:
        prometheus_integration = PrometheusIntegration(config)
    
    return prometheus_integration

def start_prometheus_monitoring(config: PrometheusConfig = None):
    """Start Prometheus monitoring"""
    integration = initialize_prometheus_integration(config)
    integration.start()
    return integration

def stop_prometheus_monitoring():
    """Stop Prometheus monitoring"""
    global prometheus_integration
    
    if prometheus_integration:
        prometheus_integration.stop()

# Convenience functions for metrics recording
def record_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Record HTTP request metrics"""
    if prometheus_integration:
        prometheus_integration.record_http_request(method, endpoint, status_code, duration)

def record_model_generation(model_type: str, status: str, duration: float):
    """Record model generation metrics"""
    if prometheus_integration:
        prometheus_integration.record_model_generation(model_type, status, duration)

def record_scaling_event(action: str, resource_type: str):
    """Record scaling event"""
    if prometheus_integration:
        prometheus_integration.record_scaling_event(action, resource_type)

if __name__ == "__main__":
    # Example usage
    config = PrometheusConfig(metrics_port=9090)
    integration = start_prometheus_monitoring(config)
    
    try:
        logger.info("Prometheus integration running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Stopping Prometheus integration...")
        stop_prometheus_monitoring()