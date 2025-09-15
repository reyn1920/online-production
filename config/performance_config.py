#!/usr/bin/env python3
"""
Production Performance Configuration
Optimizes application performance for production deployment.
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    redis_url: Optional[str] = None
    default_timeout: int = 300  # 5 minutes
    max_entries: int = 1000
    

@dataclass
class DatabaseConfig:
    """Database optimization settings."""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600  # 1 hour
    echo: bool = False
    

@dataclass
class CompressionConfig:
    """Response compression settings."""
    enabled: bool = True
    min_size: int = 1024  # 1KB
    compression_level: int = 6
    

@dataclass
class StaticFilesConfig:
    """Static files optimization."""
    max_age: int = 31536000  # 1 year
    gzip_enabled: bool = True
    etag_enabled: bool = True
    

@dataclass
class PerformanceConfig:
    """Main performance configuration."""
    cache: CacheConfig
    database: DatabaseConfig
    compression: CompressionConfig
    static_files: StaticFilesConfig
    request_timeout: int = 30
    max_request_size: int = 16 * 1024 * 1024  # 16MB
    worker_processes: int = 4
    worker_connections: int = 1000
    

def get_performance_config(environment: str = 'production') -> PerformanceConfig:
    """Get performance configuration for the specified environment."""
    
    # Base configuration
    cache_config = CacheConfig(
        redis_url=os.getenv('REDIS_URL'),
        default_timeout=int(os.getenv('CACHE_TIMEOUT', '300')),
        max_entries=int(os.getenv('CACHE_MAX_ENTRIES', '1000'))
    )
    
    database_config = DatabaseConfig(
        pool_size=int(os.getenv('DB_POOL_SIZE', '10')),
        max_overflow=int(os.getenv('DB_MAX_OVERFLOW', '20')),
        pool_timeout=int(os.getenv('DB_POOL_TIMEOUT', '30')),
        pool_recycle=int(os.getenv('DB_POOL_RECYCLE', '3600')),
        echo=os.getenv('DB_ECHO', 'false').lower() == 'true'
    )
    
    compression_config = CompressionConfig(
        enabled=os.getenv('COMPRESSION_ENABLED', 'true').lower() == 'true',
        min_size=int(os.getenv('COMPRESSION_MIN_SIZE', '1024')),
        compression_level=int(os.getenv('COMPRESSION_LEVEL', '6'))
    )
    
    static_files_config = StaticFilesConfig(
        max_age=int(os.getenv('STATIC_MAX_AGE', '31536000')),
        gzip_enabled=os.getenv('STATIC_GZIP', 'true').lower() == 'true',
        etag_enabled=os.getenv('STATIC_ETAG', 'true').lower() == 'true'
    )
    
    config = PerformanceConfig(
        cache=cache_config,
        database=database_config,
        compression=compression_config,
        static_files=static_files_config,
        request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
        max_request_size=int(os.getenv('MAX_REQUEST_SIZE', str(16 * 1024 * 1024))),
        worker_processes=int(os.getenv('WORKER_PROCESSES', '4')),
        worker_connections=int(os.getenv('WORKER_CONNECTIONS', '1000'))
    )
    
    # Environment-specific adjustments
    if environment == 'development':
        config.database.echo = True
        config.cache.default_timeout = 60  # Shorter cache for development
        config.worker_processes = 1
        
    elif environment == 'staging':
        config.worker_processes = 2
        config.cache.default_timeout = 180  # 3 minutes
        
    return config


def get_middleware_config(performance_config: PerformanceConfig) -> Dict[str, Any]:
    """Get middleware configuration based on performance settings."""
    
    middleware_config = {
        'compression': {
            'enabled': performance_config.compression.enabled,
            'minimum_size': performance_config.compression.min_size,
            'compression_level': performance_config.compression.compression_level
        },
        'cors': {
            'allow_origins': os.getenv('CORS_ORIGINS', '*').split(','),
            'allow_methods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['*'],
            'max_age': 86400  # 24 hours
        },
        'rate_limiting': {
            'requests_per_minute': int(os.getenv('RATE_LIMIT_RPM', '100')),
            'burst_size': int(os.getenv('RATE_LIMIT_BURST', '20')),
            'storage_url': performance_config.cache.redis_url
        },
        'security_headers': {
            'x_frame_options': 'DENY',
            'x_content_type_options': 'nosniff',
            'x_xss_protection': '1; mode=block',
            'strict_transport_security': 'max-age=31536000; includeSubDomains',
            'content_security_policy': os.getenv('CSP_POLICY', "default-src 'self'")
        }
    }
    
    return middleware_config


def get_caching_strategy() -> Dict[str, Any]:
    """Get caching strategy configuration."""
    
    return {
        'api_responses': {
            'ttl': int(os.getenv('API_CACHE_TTL', '300')),  # 5 minutes
            'vary_headers': ['Authorization', 'Accept-Language']
        },
        'static_assets': {
            'ttl': int(os.getenv('STATIC_CACHE_TTL', '31536000')),  # 1 year
            'immutable': True
        },
        'database_queries': {
            'ttl': int(os.getenv('DB_CACHE_TTL', '600')),  # 10 minutes
            'invalidation_tags': True
        },
        'user_sessions': {
            'ttl': int(os.getenv('SESSION_TTL', '3600')),  # 1 hour
            'sliding_expiration': True
        }
    }


def optimize_for_production() -> Dict[str, Any]:
    """Get production optimization settings."""
    
    return {
        'minify_responses': True,
        'remove_debug_headers': True,
        'enable_http2': True,
        'preload_critical_resources': True,
        'lazy_load_images': True,
        'bundle_splitting': {
            'vendor_chunk': True,
            'common_chunk': True,
            'async_chunks': True
        },
        'asset_optimization': {
            'image_compression': True,
            'css_minification': True,
            'js_minification': True,
            'tree_shaking': True
        },
        'cdn_config': {
            'enabled': os.getenv('CDN_ENABLED', 'false').lower() == 'true',
            'base_url': os.getenv('CDN_BASE_URL', ''),
            'cache_control': 'public, max-age=31536000, immutable'
        }
    }


if __name__ == '__main__':
    # Example usage
    config = get_performance_config('production')
    middleware = get_middleware_config(config)
    caching = get_caching_strategy()
    optimization = optimize_for_production()
    
    print("Performance Configuration:")
    print(f"Worker Processes: {config.worker_processes}")
    print(f"Cache Timeout: {config.cache.default_timeout}s")
    print(f"Database Pool Size: {config.database.pool_size}")
    print(f"Compression Enabled: {config.compression.enabled}")
    print(f"Rate Limiting: {middleware['rate_limiting']['requests_per_minute']} RPM")