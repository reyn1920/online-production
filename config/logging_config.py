#!/usr/bin/env python3
"""
Production Logging Configuration

This module provides comprehensive logging configuration for production deployment,
including structured logging, log rotation, and integration with monitoring systems.

Features:
- Structured JSON logging for production
- Log rotation and retention policies
- Performance monitoring integration
- Security event logging
- Error tracking and alerting

Usage:
    from config.logging_config import setup_production_logging
    setup_production_logging()

Author: TRAE AI Production Team
Version: 1.0.0
"""

import os
import sys
import json
import logging
import logging.config
import logging.handlers
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Create logs directory
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'process_id': os.getpid(),
            'thread_id': record.thread,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'lineno', 'funcName', 'created',
                'msecs', 'relativeCreated', 'thread', 'threadName',
                'processName', 'process', 'getMessage', 'exc_info',
                'exc_text', 'stack_info'
            }:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)

class SecurityFilter(logging.Filter):
    """Filter to identify and flag security-related log events"""
    
    SECURITY_KEYWORDS = {
        'authentication', 'authorization', 'login', 'logout', 'password',
        'token', 'api_key', 'secret', 'credential', 'unauthorized',
        'forbidden', 'access_denied', 'security', 'breach', 'attack',
        'injection', 'xss', 'csrf', 'malicious', 'suspicious'
    }
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add security flag to records containing security keywords"""
        message_lower = record.getMessage().lower()
        
        if any(keyword in message_lower for keyword in self.SECURITY_KEYWORDS):
            record.security_event = True
            record.alert_level = 'high' if record.levelno >= logging.ERROR else 'medium'
        
        return True

class PerformanceFilter(logging.Filter):
    """Filter to track performance metrics in logs"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance context to log records"""
        # Add request ID if available (from Flask/FastAPI context)
        try:
            from flask import g
            if hasattr(g, 'request_id'):
                record.request_id = g.request_id
        except ImportError:
            pass
        
        # Add performance metrics if available
        if hasattr(record, 'duration'):
            record.performance_metric = True
            duration = getattr(record, 'duration', 0)
            if isinstance(duration, (int, float)) and duration > 1.0:  # Slow operation (>1s)
                record.slow_operation = True
        
        return True

def get_log_level() -> int:
    """Get log level from environment variable"""
    level_name = os.getenv('LOG_LEVEL', 'INFO').upper()
    return getattr(logging, level_name, logging.INFO)

def get_logging_config() -> Dict[str, Any]:
    """Get comprehensive logging configuration"""
    
    environment = os.getenv('ENVIRONMENT', 'development')
    log_level = get_log_level()
    
    # Base configuration
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': JSONFormatter,
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            }
        },
        'filters': {
            'security': {
                '()': SecurityFilter,
            },
            'performance': {
                '()': PerformanceFilter,
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': log_level,
                'formatter': 'json' if environment == 'production' else 'detailed',
                'stream': sys.stdout,
                'filters': ['security', 'performance']
            },
            'file_app': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': log_level,
                'formatter': 'json',
                'filename': str(LOGS_DIR / 'application.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'filters': ['security', 'performance']
            },
            'file_error': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': str(LOGS_DIR / 'error.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 10,
                'filters': ['security', 'performance']
            },
            'file_security': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'WARNING',
                'formatter': 'json',
                'filename': str(LOGS_DIR / 'security.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 20,
                'filters': ['security']
            },
            'file_performance': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'INFO',
                'formatter': 'json',
                'filename': str(LOGS_DIR / 'performance.log'),
                'maxBytes': 10 * 1024 * 1024,  # 10MB
                'backupCount': 5,
                'filters': ['performance']
            }
        },
        'loggers': {
            # Application loggers
            'app': {
                'level': log_level,
                'handlers': ['console', 'file_app', 'file_error'],
                'propagate': False
            },
            'security': {
                'level': 'WARNING',
                'handlers': ['console', 'file_security', 'file_error'],
                'propagate': False
            },
            'performance': {
                'level': 'INFO',
                'handlers': ['file_performance'],
                'propagate': False
            },
            # Third-party loggers
            'werkzeug': {
                'level': 'WARNING',
                'handlers': ['file_app'],
                'propagate': False
            },
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['file_app'],
                'propagate': False
            },
            'requests': {
                'level': 'WARNING',
                'handlers': ['file_app'],
                'propagate': False
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file_app']
        }
    }
    
    # Add development-specific handlers
    if environment == 'development':
        try:
            config['handlers']['console']['formatter'] = 'detailed'
            config['loggers']['werkzeug']['level'] = 'INFO'
        except (KeyError, TypeError):
            pass  # Ignore if config structure is unexpected
    
    return config

def setup_production_logging(config_override: Optional[Dict[str, Any]] = None) -> None:
    """Setup production logging configuration"""
    
    # Get base configuration
    config = get_logging_config()
    
    # Apply any overrides
    if config_override:
        config.update(config_override)
    
    # Configure logging
    logging.config.dictConfig(config)
    
    # Log startup message
    logger = logging.getLogger('app')
    environment = os.getenv('ENVIRONMENT', 'development')
    log_level = logging.getLevelName(get_log_level())
    
    logger.info(
        "Logging system initialized",
        extra={
            'environment': environment,
            'log_level': log_level,
            'logs_directory': str(LOGS_DIR),
            'startup_event': True
        }
    )

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance"""
    return logging.getLogger(name)

def log_performance(logger: logging.Logger, operation: str, duration: float, 
                   **kwargs) -> None:
    """Log performance metrics"""
    logger.info(
        f"Performance: {operation} completed",
        extra={
            'operation': operation,
            'duration': duration,
            'performance_metric': True,
            **kwargs
        }
    )

def log_security_event(logger: logging.Logger, event_type: str, 
                      severity: str = 'medium', **kwargs) -> None:
    """Log security events"""
    level = logging.ERROR if severity == 'high' else logging.WARNING
    
    logger.log(
        level,
        f"Security Event: {event_type}",
        extra={
            'security_event': True,
            'event_type': event_type,
            'severity': severity,
            'alert_level': severity,
            **kwargs
        }
    )

def log_api_request(logger: logging.Logger, method: str, path: str, 
                   status_code: int, duration: float, **kwargs) -> None:
    """Log API request details"""
    logger.info(
        f"API Request: {method} {path} - {status_code}",
        extra={
            'api_request': True,
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration': duration,
            'performance_metric': True,
            **kwargs
        }
    )

def log_database_operation(logger: logging.Logger, operation: str, 
                          table: str, duration: float, **kwargs) -> None:
    """Log database operations"""
    logger.info(
        f"Database: {operation} on {table}",
        extra={
            'database_operation': True,
            'operation': operation,
            'table': table,
            'duration': duration,
            'performance_metric': True,
            **kwargs
        }
    )

def log_external_api_call(logger: logging.Logger, service: str, endpoint: str,
                         status_code: int, duration: float, **kwargs) -> None:
    """Log external API calls"""
    logger.info(
        f"External API: {service} {endpoint} - {status_code}",
        extra={
            'external_api_call': True,
            'service': service,
            'endpoint': endpoint,
            'status_code': status_code,
            'duration': duration,
            'performance_metric': True,
            **kwargs
        }
    )

# Context managers for performance logging
class LogPerformance:
    """Context manager for automatic performance logging"""
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            
            if exc_type:
                self.logger.error(
                    f"Performance: {self.operation} failed",
                    extra={
                        'operation': self.operation,
                        'duration': duration,
                        'performance_metric': True,
                        'error': str(exc_val),
                        **self.kwargs
                    }
                )
            else:
                log_performance(self.logger, self.operation, duration, **self.kwargs)

# Example usage functions
def example_usage():
    """Example of how to use the logging system"""
    
    # Setup logging
    setup_production_logging()
    
    # Get loggers
    app_logger = get_logger('app')
    security_logger = get_logger('security')
    performance_logger = get_logger('performance')
    
    # Basic logging
    app_logger.info("Application started successfully")
    app_logger.warning("This is a warning message")
    app_logger.error("This is an error message")
    
    # Security logging
    log_security_event(
        security_logger,
        'failed_login_attempt',
        severity='high',
        user_id='user123',
        ip_address='192.168.1.100'
    )
    
    # Performance logging
    log_performance(
        performance_logger,
        'database_query',
        0.25,
        query_type='SELECT',
        table='users'
    )
    
    # API request logging
    log_api_request(
        app_logger,
        'GET',
        '/api/users',
        200,
        0.15,
        user_id='user123'
    )
    
    # Using context manager
    with LogPerformance(performance_logger, 'complex_calculation'):
        # Simulate some work
        import time
        time.sleep(0.1)

if __name__ == '__main__':
    example_usage()