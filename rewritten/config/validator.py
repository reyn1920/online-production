#!/usr/bin/env python3
""""""
Configuration Validator

Validates environment configuration before application startup.
Follows go - live security practices:
- Validates required vs optional configurations
- Checks API key formats
- Ensures secure defaults
- Provides clear error messages
""""""

import logging
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels"""

    ERROR = "error"  # Will prevent startup
    WARNING = "warning"  # Will log but allow startup
    INFO = "info"  # Informational only


@dataclass
class ValidationResult:
    """Result of a configuration validation"""

    key: str
    level: ValidationLevel
    message: str
    value_present: bool
    value_valid: bool = True


class ConfigValidator:
    """Validates environment configuration for go - live readiness"""

    def __init__(self):
        self.results: List[ValidationResult] = []

        # Define validation rules
        self.validation_rules = {
            # Server Configuration
            "PORT": {
                "required": False,
                "default": "8000",
                "validator": self._validate_port,
                "description": "Server port number",
# BRACKET_SURGEON: disabled
#             },
            "HOST": {
                "required": False,
                "default": "0.0.0.0",
                "validator": self._validate_host,
                "description": "Server host address",
# BRACKET_SURGEON: disabled
#             },
            "ENVIRONMENT": {
                "required": False,
                "default": "development",
                "validator": self._validate_environment,
                "description": "Application environment",
# BRACKET_SURGEON: disabled
#             },
            # Database Configuration
            "DATABASE_URL": {
                "required": False,
                "validator": self._validate_database_url,
                "description": "Database connection string",
# BRACKET_SURGEON: disabled
#             },
            # Security Configuration
            "SECRET_KEY": {
                "required": True,
                "validator": self._validate_secret_key,
                "description": "Application secret key for security",
# BRACKET_SURGEON: disabled
#             },
            "JWT_SECRET": {
                "required": False,
                "validator": self._validate_jwt_secret,
                "description": "JWT token signing secret",
# BRACKET_SURGEON: disabled
#             },
            # Pet Care APIs (Optional)
            "EBIRD_API_TOKEN": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "eBird API token for bird observations",
# BRACKET_SURGEON: disabled
#             },
            "DOG_API_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Dog API key for breed information",
# BRACKET_SURGEON: disabled
#             },
            "CAT_API_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Cat API key for breed information",
# BRACKET_SURGEON: disabled
#             },
            "PETFINDER_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Petfinder API key",
# BRACKET_SURGEON: disabled
#             },
            "PETFINDER_SECRET": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Petfinder API secret",
# BRACKET_SURGEON: disabled
#             },
            # Veterinary Services (Optional)
            "VETSTER_API_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Vetster API key for online consultations",
# BRACKET_SURGEON: disabled
#             },
            "PAWP_API_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Pawp API key for emergency vet chat",
# BRACKET_SURGEON: disabled
#             },
            "AIRVET_API_KEY": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "AirVet API key for virtual care",
# BRACKET_SURGEON: disabled
#             },
            "CALENDLY_TOKEN": {
                "required": False,
                "validator": self._validate_api_key,
                "description": "Calendly token for appointment scheduling",
# BRACKET_SURGEON: disabled
#             },
            # Feature Flags
            "ENABLE_PET_CARE_APIS": {
                "required": False,
                "default": "false",
                "validator": self._validate_boolean,
                "description": "Enable pet care API endpoints",
# BRACKET_SURGEON: disabled
#             },
            "ENABLE_AFFILIATE_PROCESSING": {
                "required": False,
                "default": "true",
                "validator": self._validate_boolean,
                "description": "Enable affiliate data processing",
# BRACKET_SURGEON: disabled
#             },
            "ENABLE_DEBUG_MODE": {
                "required": False,
                "default": "false",
                "validator": self._validate_boolean,
                "description": "Enable debug mode (should be false in production)",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

    def _validate_port(self, value: str) -> Tuple[bool, str]:
        """Validate port number"""
        try:
            port = int(value)
            if 1 <= port <= 65535:
                return True, "Valid port number"
            else:
                return False, "Port must be between 1 and 65535"
        except ValueError:
            return False, "Port must be a valid integer"

    def _validate_host(self, value: str) -> Tuple[bool, str]:
        """Validate host address"""
        # Basic validation for common host patterns
        valid_hosts = ["0.0.0.0", "127.0.0.1", "localhost"]
        if value in valid_hosts or re.match(r"^\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}$", value):
            return True, "Valid host address"
        return False, "Invalid host address format"

    def _validate_environment(self, value: str) -> Tuple[bool, str]:
        """Validate environment setting"""
        valid_envs = ["development", "staging", "production", "test"]
        if value.lower() in valid_envs:
            if value.lower() == "production":
                return True, "Production environment detected"
            return True, f"Valid environment: {value}"
        return False, f"Environment must be one of: {', '.join(valid_envs)}"

    def _validate_database_url(self, value: str) -> Tuple[bool, str]:
        """Validate database URL format"""
        # Basic validation for common database URL patterns
        db_patterns = [
            r"^postgresql://.*",
            r"^mysql://.*",
            r"^sqlite:///.*",
            r"^mongodb://.*",
# BRACKET_SURGEON: disabled
#         ]

        for pattern in db_patterns:
            if re.match(pattern, value, re.IGNORECASE):
                return True, "Valid database URL format"

        return False, "Invalid database URL format"

    def _validate_secret_key(self, value: str) -> Tuple[bool, str]:
        """Validate secret key strength"""
        if len(value) < 32:
            return False, "Secret key must be at least 32 characters long"

        if value in ["your - secret - key", "change - me", "secret", "password"]:
            return False, "Secret key appears to be a default/weak value"

        # Check for reasonable entropy
        if len(set(value)) < 10:
            return False, "Secret key has insufficient character diversity"

        return True, "Secret key appears strong"

    def _validate_jwt_secret(self, value: str) -> Tuple[bool, str]:
        """Validate JWT secret"""
        return self._validate_secret_key(value)

    def _validate_api_key(self, value: str) -> Tuple[bool, str]:
        """Validate API key format"""
        if len(value) < 8:
            return False, "API key appears too short"

        # Check for obvious placeholder values
        placeholder_patterns = [
            "your - api - key",
            "api - key - here",
            "change - me",
            "placeholder",
            "example",
            "test - key",
# BRACKET_SURGEON: disabled
#         ]

        if value.lower() in placeholder_patterns:
            return False, "API key appears to be a placeholder value"

        return True, "API key format appears valid"

    def _validate_boolean(self, value: str) -> Tuple[bool, str]:
        """Validate boolean value"""
        valid_true = ["true", "1", "yes", "on", "enabled"]
        valid_false = ["false", "0", "no", "off", "disabled"]

        if value.lower() in valid_true + valid_false:
            return True, f"Valid boolean value: {value}"

        return (
            False,
            "Boolean value must be true/false, 1/0, yes/no, on/off, \"
#     or enabled/disabled",
# BRACKET_SURGEON: disabled
#         )

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all configuration settings"""
        self.results = []
        errors = []
        warnings = []
        info = []

        logger.info("Starting configuration validation...")

        for key, rules in self.validation_rules.items():
            value = os.getenv(key)

            # Check if value is present
            if value is None or value.strip() == "":
                if rules["required"]:
                    result = ValidationResult(
                        key=key,
                        level=ValidationLevel.ERROR,
                        message=f"Required configuration '{key}' is missing: {rules['description']}",
                        value_present=False,
# BRACKET_SURGEON: disabled
#                     )
                    errors.append(result.message)
                else:
                    # Use default if available
                    default_value = rules.get("default")
                    if default_value:
                        os.environ[key] = default_value
                        result = ValidationResult(
                            key=key,
                            level=ValidationLevel.INFO,
                            message=f"Using default value for '{key}': {default_value}",
                            value_present=False,
# BRACKET_SURGEON: disabled
#                         )
                        info.append(result.message)
                    else:
                        result = ValidationResult(
                            key=key,
                            level=ValidationLevel.WARNING,
                            message=f"Optional configuration '{key}' not set: {rules['description']}",
                            value_present=False,
# BRACKET_SURGEON: disabled
#                         )
                        warnings.append(result.message)
            else:
                # Validate the value
                validator = rules.get("validator")
                if validator:
                    is_valid, validation_message = validator(value)

                    if is_valid:
                        result = ValidationResult(
                            key=key,
                            level=ValidationLevel.INFO,
                            message=f"'{key}': {validation_message}",
                            value_present=True,
                            value_valid=True,
# BRACKET_SURGEON: disabled
#                         )
                        info.append(result.message)
                    else:
                        level = (
                            ValidationLevel.ERROR if rules["required"] else ValidationLevel.WARNING
# BRACKET_SURGEON: disabled
#                         )
                        result = ValidationResult(
                            key=key,
                            level=level,
                            message=f"'{key}' validation failed: {validation_message}",
                            value_present=True,
                            value_valid=False,
# BRACKET_SURGEON: disabled
#                         )

                        if level == ValidationLevel.ERROR:
                            errors.append(result.message)
                        else:
                            warnings.append(result.message)
                else:
                    result = ValidationResult(
                        key=key,
                        level=ValidationLevel.INFO,
                        message=f"'{key}' is set (no validation rule defined)",
                        value_present=True,
# BRACKET_SURGEON: disabled
#                     )
                    info.append(result.message)

            self.results.append(result)

        # Log results
        for error in errors:
            logger.error(error)

        for warning in warnings:
            logger.warning(warning)

        for info_msg in info:
            logger.info(info_msg)

        # Check for production - specific requirements
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            self._validate_production_requirements(errors, warnings)

        validation_summary = {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "info": info,
            "environment": env,
            "total_checks": len(self.results),
            "errors_count": len(errors),
            "warnings_count": len(warnings),
# BRACKET_SURGEON: disabled
#         }

        if validation_summary["valid"]:
            logger.info(f"✅ Configuration validation passed ({len(self.results)} checks)")
        else:
            logger.error(f"❌ Configuration validation failed with {len(errors)} errors")

        return validation_summary

    def _validate_production_requirements(self, errors: List[str], warnings: List[str]):
        """Additional validation for production environment"""
        logger.info("Performing additional production environment checks...")

        # Check debug mode is disabled
        debug_mode = os.getenv("ENABLE_DEBUG_MODE", "false").lower()
        if debug_mode in ["true", "1", "yes", "on", "enabled"]:
            errors.append("DEBUG_MODE must be disabled in production environment")

        # Check secret key is not default
        secret_key = os.getenv("SECRET_KEY")
        if secret_key and len(secret_key) < 64:
            warnings.append("Consider using a longer SECRET_KEY (64+ characters) for production")

        # Warn about missing optional but recommended configs
        recommended_for_prod = ["DATABASE_URL", "JWT_SECRET"]
        for key in recommended_for_prod:
            if not os.getenv(key):
                warnings.append(f"Consider setting '{key}' for production deployment")


def validate_startup_config() -> bool:
    """Validate configuration at startup and return success status"""
    validator = ConfigValidator()
    result = validator.validate_configuration()
    return result["valid"]


# Export functions
__all__ = [
    "ConfigValidator",
    "ValidationResult",
    "ValidationLevel",
    "validate_startup_config",
# BRACKET_SURGEON: disabled
# ]