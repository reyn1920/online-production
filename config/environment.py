#!/usr/bin/env python3
"""
Environment Configuration Manager

This module handles secure loading and validation of environment variables
following go-live security best practices:
- Never hardcode secrets
- Use environment variable hierarchy
- Validate required configurations
- Provide secure defaults
"""

import os
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///./app.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "your-secret-key-change-in-production"
    jwt_secret: str = "your-jwt-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://localhost:8000"]

@dataclass
class APIConfig:
    """API configuration"""
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    sendowl_api_key: Optional[str] = None
    stripe_api_key: Optional[str] = None
    
@dataclass
class FeatureFlags:
    """Feature flags configuration"""
    enable_ai_features: bool = True
    enable_real_time: bool = True
    enable_analytics: bool = True
    enable_monetization: bool = False
    enable_affiliate_tracking: bool = False
    debug_mode: bool = False

class EnvironmentConfig:
    """Main configuration manager"""
    
    def __init__(self):
        self.environment = self._get_env("ENVIRONMENT", "development")
        self.debug = self._get_bool_env("DEBUG", True)
        self.host = self._get_env("HOST", "0.0.0.0")
        self.port = self._get_int_env("PORT", 8000)
        
        # Load configuration sections
        self.database = self._load_database_config()
        self.security = self._load_security_config()
        self.apis = self._load_api_config()
        self.features = self._load_feature_flags()
        
        # Validate configuration
        self._validate_config()
        
        logger.info(f"Configuration loaded for environment: {self.environment}")
    
    def _get_env(self, key: str, default: str = "") -> str:
        """Get environment variable with default"""
        return os.getenv(key, default)
    
    def _get_bool_env(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")
    
    def _get_int_env(self, key: str, default: int = 0) -> int:
        """Get integer environment variable"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            logger.warning(f"Invalid integer value for {key}, using default: {default}")
            return default
    
    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            url=self._get_env("DATABASE_URL", "sqlite:///./app.db"),
            echo=self._get_bool_env("DATABASE_ECHO", False),
            pool_size=self._get_int_env("DATABASE_POOL_SIZE", 5),
            max_overflow=self._get_int_env("DATABASE_MAX_OVERFLOW", 10)
        )
    
    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        cors_origins_str = self._get_env("CORS_ORIGINS", "")
        cors_origins = cors_origins_str.split(",") if cors_origins_str else None
        
        return SecurityConfig(
            secret_key=self._get_env("SECRET_KEY", "your-secret-key-change-in-production"),
            jwt_secret=self._get_env("JWT_SECRET", "your-jwt-secret-change-in-production"),
            algorithm=self._get_env("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=self._get_int_env("ACCESS_TOKEN_EXPIRE_MINUTES", 30),
            cors_origins=cors_origins
        )
    
    def _load_api_config(self) -> APIConfig:
        """Load API configuration"""
        return APIConfig(
            openai_api_key=self._get_env("OPENAI_API_KEY"),
            anthropic_api_key=self._get_env("ANTHROPIC_API_KEY"),
            google_api_key=self._get_env("GOOGLE_API_KEY"),
            sendowl_api_key=self._get_env("SENDOWL_API_KEY"),
            stripe_api_key=self._get_env("STRIPE_API_KEY")
        )
    
    def _load_feature_flags(self) -> FeatureFlags:
        """Load feature flags"""
        return FeatureFlags(
            enable_ai_features=self._get_bool_env("ENABLE_AI_FEATURES", True),
            enable_real_time=self._get_bool_env("ENABLE_REAL_TIME", True),
            enable_analytics=self._get_bool_env("ENABLE_ANALYTICS", True),
            enable_monetization=self._get_bool_env("ENABLE_MONETIZATION", False),
            enable_affiliate_tracking=self._get_bool_env("ENABLE_AFFILIATE_TRACKING", False),
            debug_mode=self._get_bool_env("DEBUG_MODE", self.debug)
        )
    
    def _validate_config(self) -> None:
        """Validate configuration"""
        # Check for production security
        if self.environment == "production":
            if self.security.secret_key == "your-secret-key-change-in-production":
                logger.error("⚠️ SECURITY WARNING: Default secret key detected in production!")
            
            if self.security.jwt_secret == "your-jwt-secret-change-in-production":
                logger.error("⚠️ SECURITY WARNING: Default JWT secret detected in production!")
            
            if self.debug:
                logger.warning("⚠️ DEBUG mode is enabled in production environment")
        
        # Log configuration status
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Debug mode: {self.debug}")
        logger.info(f"Host: {self.host}:{self.port}")
        logger.info(f"Database: {self.database.url}")
        
        # Log feature flags
        enabled_features = []
        if self.features.enable_ai_features:
            enabled_features.append("AI")
        if self.features.enable_real_time:
            enabled_features.append("Real-time")
        if self.features.enable_analytics:
            enabled_features.append("Analytics")
        if self.features.enable_monetization:
            enabled_features.append("Monetization")
        if self.features.enable_affiliate_tracking:
            enabled_features.append("Affiliate")
        
        logger.info(f"Enabled features: {', '.join(enabled_features) if enabled_features else 'None'}")
    
    def get_database_url(self) -> str:
        """Get database URL"""
        return self.database.url
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins"""
        return self.security.cors_origins or []
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "development"
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "production"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary (excluding secrets)"""
        return {
            "environment": self.environment,
            "debug": self.debug,
            "host": self.host,
            "port": self.port,
            "database": {
                "url": "[REDACTED]" if "://" in self.database.url else self.database.url,
                "echo": self.database.echo,
                "pool_size": self.database.pool_size,
                "max_overflow": self.database.max_overflow
            },
            "security": {
                "algorithm": self.security.algorithm,
                "access_token_expire_minutes": self.security.access_token_expire_minutes,
                "cors_origins": self.security.cors_origins
            },
            "features": {
                "enable_ai_features": self.features.enable_ai_features,
                "enable_real_time": self.features.enable_real_time,
                "enable_analytics": self.features.enable_analytics,
                "enable_monetization": self.features.enable_monetization,
                "enable_affiliate_tracking": self.features.enable_affiliate_tracking,
                "debug_mode": self.features.debug_mode
            }
        }

# Global configuration instance
config = EnvironmentConfig()

# Utility functions
def get_config() -> EnvironmentConfig:
    """Get global configuration instance"""
    return config

def reload_config() -> EnvironmentConfig:
    """Reload configuration from environment"""
    global config
    config = EnvironmentConfig()
    return config

# Export main components
__all__ = [
    "EnvironmentConfig", "DatabaseConfig", "SecurityConfig", 
    "APIConfig", "FeatureFlags", "config", "get_config", "reload_config"
]