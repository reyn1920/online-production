#!/usr/bin/env python3
"""
Configuration Validator

Validates environment configuration before application startup.
Follows go-live security best practices and ensures all required
settings are properly configured.
"""

import os
import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a configuration validation check"""
    key: str
    is_valid: bool
    message: str
    severity: str = "info"  # info, warning, error
    value_preview: Optional[str] = None

class ConfigurationValidator:
    """Validates application configuration settings"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_required_env_var(self, key: str, description: str = "") -> ValidationResult:
        """Validate that a required environment variable is set"""
        value = os.getenv(key)
        
        if not value:
            result = ValidationResult(
                key=key,
                is_valid=False,
                message=f"Required environment variable '{key}' is not set. {description}",
                severity="error"
            )
        else:
            # Show preview of non-sensitive values
            preview = None
            if not any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                preview = value[:20] + "..." if len(value) > 20 else value
            else:
                preview = "[REDACTED]"
            
            result = ValidationResult(
                key=key,
                is_valid=True,
                message=f"Environment variable '{key}' is properly set",
                severity="info",
                value_preview=preview
            )
        
        self.results.append(result)
        return result
    
    def validate_optional_env_var(self, key: str, description: str = "") -> ValidationResult:
        """Validate an optional environment variable"""
        value = os.getenv(key)
        
        if not value:
            result = ValidationResult(
                key=key,
                is_valid=True,
                message=f"Optional environment variable '{key}' is not set. {description}",
                severity="info"
            )
        else:
            # Show preview of non-sensitive values
            preview = None
            if not any(sensitive in key.lower() for sensitive in ['key', 'secret', 'token', 'password']):
                preview = value[:20] + "..." if len(value) > 20 else value
            else:
                preview = "[REDACTED]"
            
            result = ValidationResult(
                key=key,
                is_valid=True,
                message=f"Optional environment variable '{key}' is set",
                severity="info",
                value_preview=preview
            )
        
        self.results.append(result)
        return result
    
    def validate_boolean_env_var(self, key: str, default: bool = False) -> ValidationResult:
        """Validate a boolean environment variable"""
        value = os.getenv(key, str(default)).lower()
        valid_true = ["true", "1", "yes", "on", "enabled"]
        valid_false = ["false", "0", "no", "off", "disabled"]
        
        if value in valid_true + valid_false:
            result = ValidationResult(
                key=key,
                is_valid=True,
                message=f"Boolean environment variable '{key}' has valid value: {value}",
                severity="info",
                value_preview=value
            )
        else:
            result = ValidationResult(
                key=key,
                is_valid=False,
                message=f"Boolean environment variable '{key}' has invalid value: {value}. Must be true/false, 1/0, yes/no, on/off, or enabled/disabled",
                severity="error",
                value_preview=value
            )
        
        self.results.append(result)
        return result
    
    def validate_integer_env_var(self, key: str, min_value: Optional[int] = None, max_value: Optional[int] = None) -> ValidationResult:
        """Validate an integer environment variable"""
        value = os.getenv(key)
        
        if not value:
            result = ValidationResult(
                key=key,
                is_valid=True,
                message=f"Integer environment variable '{key}' is not set (will use default)",
                severity="info"
            )
        else:
            try:
                int_value = int(value)
                
                # Check bounds
                if min_value is not None and int_value < min_value:
                    result = ValidationResult(
                        key=key,
                        is_valid=False,
                        message=f"Integer environment variable '{key}' value {int_value} is below minimum {min_value}",
                        severity="error",
                        value_preview=str(int_value)
                    )
                elif max_value is not None and int_value > max_value:
                    result = ValidationResult(
                        key=key,
                        is_valid=False,
                        message=f"Integer environment variable '{key}' value {int_value} is above maximum {max_value}",
                        severity="error",
                        value_preview=str(int_value)
                    )
                else:
                    result = ValidationResult(
                        key=key,
                        is_valid=True,
                        message=f"Integer environment variable '{key}' has valid value: {int_value}",
                        severity="info",
                        value_preview=str(int_value)
                    )
            except ValueError:
                result = ValidationResult(
                    key=key,
                    is_valid=False,
                    message=f"Integer environment variable '{key}' has invalid value: {value} (not a valid integer)",
                    severity="error",
                    value_preview=value
                )
        
        self.results.append(result)
        return result
    
    def validate_production_security(self) -> List[ValidationResult]:
        """Validate production security settings"""
        environment = os.getenv("ENVIRONMENT", "development")
        security_results = []
        
        if environment == "production":
            # Check for secure secret key
            secret_key = os.getenv("SECRET_KEY")
            if not secret_key or "your-secret-key-change-in-production" in secret_key:
                security_results.append(ValidationResult(
                    key="SECRET_KEY",
                    is_valid=False,
                    message="⚠️ CRITICAL: Default or missing SECRET_KEY in production environment!",
                    severity="error"
                ))
            else:
                security_results.append(ValidationResult(
                    key="SECRET_KEY",
                    is_valid=True,
                    message="Production SECRET_KEY is properly configured",
                    severity="info",
                    value_preview="[REDACTED]"
                ))
            
            # Check for secure JWT secret
            jwt_secret = os.getenv("JWT_SECRET")
            if not jwt_secret or "your-jwt-secret-change-in-production" in jwt_secret:
                security_results.append(ValidationResult(
                    key="JWT_SECRET",
                    is_valid=False,
                    message="⚠️ CRITICAL: Default or missing JWT_SECRET in production environment!",
                    severity="error"
                ))
            else:
                security_results.append(ValidationResult(
                    key="JWT_SECRET",
                    is_valid=True,
                    message="Production JWT_SECRET is properly configured",
                    severity="info",
                    value_preview="[REDACTED]"
                ))
            
            # Check debug mode
            debug = os.getenv("DEBUG", "false").lower()
            if debug in ["true", "1", "yes", "on"]:
                security_results.append(ValidationResult(
                    key="DEBUG",
                    is_valid=False,
                    message="⚠️ WARNING: DEBUG mode is enabled in production environment!",
                    severity="warning",
                    value_preview=debug
                ))
            else:
                security_results.append(ValidationResult(
                    key="DEBUG",
                    is_valid=True,
                    message="DEBUG mode is properly disabled in production",
                    severity="info",
                    value_preview=debug
                ))
        
        self.results.extend(security_results)
        return security_results
    
    def validate_database_config(self) -> List[ValidationResult]:
        """Validate database configuration"""
        db_results = []
        
        # Database URL
        db_url = os.getenv("DATABASE_URL")
        if db_url:
            if db_url.startswith("sqlite://"):
                db_results.append(ValidationResult(
                    key="DATABASE_URL",
                    is_valid=True,
                    message="SQLite database configured (suitable for development)",
                    severity="info",
                    value_preview="sqlite://..."
                ))
            elif any(db_url.startswith(prefix) for prefix in ["postgresql://", "mysql://", "mariadb://"]):
                db_results.append(ValidationResult(
                    key="DATABASE_URL",
                    is_valid=True,
                    message="Production database configured",
                    severity="info",
                    value_preview="[REDACTED]"
                ))
            else:
                db_results.append(ValidationResult(
                    key="DATABASE_URL",
                    is_valid=False,
                    message=f"Unsupported database URL format: {db_url[:20]}...",
                    severity="warning"
                ))
        else:
            db_results.append(ValidationResult(
                key="DATABASE_URL",
                is_valid=True,
                message="DATABASE_URL not set, will use default SQLite",
                severity="info"
            ))
        
        # Database pool settings
        self.validate_integer_env_var("DATABASE_POOL_SIZE", min_value=1, max_value=100)
        self.validate_integer_env_var("DATABASE_MAX_OVERFLOW", min_value=0, max_value=200)
        
        self.results.extend(db_results)
        return db_results
    
    def validate_startup_config(self) -> Dict[str, Any]:
        """Main validation function - validates all startup configuration"""
        logger.info("🔍 Starting configuration validation...")
        
        # Clear previous results
        self.results = []
        self.errors = []
        self.warnings = []
        
        # Validate core settings
        self.validate_optional_env_var("ENVIRONMENT", "Defaults to 'development'")
        self.validate_boolean_env_var("DEBUG")
        self.validate_optional_env_var("HOST", "Defaults to '0.0.0.0'")
        self.validate_integer_env_var("PORT", min_value=1, max_value=65535)
        
        # Validate security settings
        self.validate_production_security()
        
        # Validate database configuration
        self.validate_database_config()
        
        # Validate API keys (optional)
        api_keys = [
            "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY",
            "SENDOWL_API_KEY", "STRIPE_API_KEY"
        ]
        for key in api_keys:
            self.validate_optional_env_var(key, "Optional API integration")
        
        # Validate feature flags
        feature_flags = [
            "ENABLE_AI_FEATURES", "ENABLE_REAL_TIME", "ENABLE_ANALYTICS",
            "ENABLE_MONETIZATION", "ENABLE_AFFILIATE_TRACKING"
        ]
        for flag in feature_flags:
            self.validate_boolean_env_var(flag)
        
        # Collect errors and warnings
        for result in self.results:
            if result.severity == "error":
                self.errors.append(result.message)
            elif result.severity == "warning":
                self.warnings.append(result.message)
        
        # Log summary
        total_checks = len(self.results)
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        logger.info(f"✅ Configuration validation complete: {total_checks} checks performed")
        
        if error_count > 0:
            logger.error(f"❌ {error_count} configuration errors found:")
            for error in self.errors:
                logger.error(f"  • {error}")
        
        if warning_count > 0:
            logger.warning(f"⚠️ {warning_count} configuration warnings:")
            for warning in self.warnings:
                logger.warning(f"  • {warning}")
        
        if error_count == 0 and warning_count == 0:
            logger.info("🎉 All configuration checks passed!")
        
        return {
            "total_checks": total_checks,
            "errors": error_count,
            "warnings": warning_count,
            "results": [{
                "key": r.key,
                "is_valid": r.is_valid,
                "message": r.message,
                "severity": r.severity,
                "value_preview": r.value_preview
            } for r in self.results],
            "has_errors": error_count > 0,
            "is_production_ready": error_count == 0
        }

# Global validator instance
validator = ConfigurationValidator()

# Main validation function (for backward compatibility)
def validate_startup_config() -> Dict[str, Any]:
    """Validate startup configuration"""
    return validator.validate_startup_config()

# Export main components
__all__ = [
    "ConfigurationValidator", "ValidationResult", "validator", "validate_startup_config"
]