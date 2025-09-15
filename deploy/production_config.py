#!/usr/bin/env python3
""""""
Production Deployment Configuration
Handles environment setup, security, and deployment validation
""""""

import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

@dataclass


class DeploymentConfig:
    """Configuration for production deployment"""

    environment: str
    debug: bool
    database_url: str
    secret_key: str
    allowed_hosts: List[str]
    cors_origins: List[str]

    # Payment provider configurations
    stripe_public_key: Optional[str] = None
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None

    paypal_client_id: Optional[str] = None
    paypal_client_secret: Optional[str] = None

    square_application_id: Optional[str] = None
    square_access_token: Optional[str] = None

    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None

    # Security settings
    jwt_secret_key: Optional[str] = None
    encryption_key: Optional[str] = None

    # Monitoring and logging
    log_level: str = "INFO"
    sentry_dsn: Optional[str] = None

    # Rate limiting
    redis_url: Optional[str] = None

    # Email configuration
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None


class ProductionValidator:
    """Validates production deployment requirements"""


    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.logger = logging.getLogger(__name__)


    def validate_environment_variables(self) -> bool:
        """Validate required environment variables are set"""
        required_vars = [
            "SECRET_KEY",
                "DATABASE_URL",
                "ALLOWED_HOSTS",
                "STRIPE_SECRET_KEY",
                "STRIPE_PUBLIC_KEY",
                "STRIPE_WEBHOOK_SECRET",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.errors.append(
                f"Missing required environment variables: {', '.join(missing_vars)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        return False

        return True


    def validate_security_settings(self) -> bool:
        """Validate security configuration"""
        valid = True

        # Check SECRET_KEY strength
        secret_key = os.getenv("SECRET_KEY", "")
        if len(secret_key) < 32:
            self.errors.append("SECRET_KEY must be at least 32 characters long")
            valid = False

        # Check DEBUG is disabled
        if os.getenv("DEBUG", "").lower() in ["true", "1", "yes"]:
            self.errors.append("DEBUG must be disabled in production")
            valid = False

        # Check HTTPS enforcement
        allowed_hosts = os.getenv("ALLOWED_HOSTS", "")
        if "localhost" in allowed_hosts or "127.0.0.1" in allowed_hosts:
            self.warnings.append(
                "localhost/127.0.0.1 should not be in ALLOWED_HOSTS for production"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        return valid


    def validate_payment_providers(self) -> bool:
        """Validate payment provider configurations"""
        valid = True

        # Stripe validation
        stripe_secret = os.getenv("STRIPE_SECRET_KEY", "")
        stripe_public = os.getenv("STRIPE_PUBLIC_KEY", "")

        if stripe_secret and not stripe_secret.startswith("sk_live_"):
            self.warnings.append("STRIPE_SECRET_KEY appears to be a test key, not live")

        if stripe_public and not stripe_public.startswith("pk_live_"):
            self.warnings.append("STRIPE_PUBLIC_KEY appears to be a test key, not live")

        if not stripe_secret or not stripe_public:
            self.errors.append("Stripe keys are required for payment processing")
            valid = False

        return valid


    def validate_database_connection(self) -> bool:
        """Validate database connection"""
        try:

            import sqlite3

            database_url = os.getenv("DATABASE_URL")

            if not database_url:
                self.errors.append("DATABASE_URL is required")
        except Exception as e:
            pass
        return False

            # For SQLite, check if file exists and is writable
            if database_url.startswith("sqlite:"):
                db_path = database_url.replace("sqlite:///", "").replace(
                    "sqlite://", ""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                db_dir = os.path.dirname(db_path)

                if not os.path.exists(db_dir):
                    self.errors.append(f"Database directory does not exist: {db_dir}")
        return False

                if not os.access(db_dir, os.W_OK):
                    self.errors.append(f"Database directory is not writable: {db_dir}")
        return False

        return True

        except Exception as e:
            self.errors.append(f"Database validation failed: {str(e)}")
        return False


    def validate_ssl_certificates(self) -> bool:
        """Validate SSL certificate configuration"""
        # This would typically check certificate files, expiration, etc.
        # For now, just check if HTTPS is enforced

        cors_origins = os.getenv("CORS_ORIGINS", "")
        if "http://" in cors_origins:
            self.warnings.append(
                "HTTP origins detected in CORS_ORIGINS, consider HTTPS only"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        return True


    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation checks"""
        self.logger.info("Starting production deployment validation...")

        validations = {
            "environment_variables": self.validate_environment_variables(),
            "security_settings": self.validate_security_settings(),
            "payment_providers": self.validate_payment_providers(),
            "database_connection": self.validate_database_connection(),
            "ssl_certificates": self.validate_ssl_certificates(),
# BRACKET_SURGEON: disabled
#         }

        all_passed = all(validations.values())

        return {
            "passed": all_passed,
            "validations": validations,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#         }


class DeploymentManager:
    """Manages production deployment process"""


    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validator = ProductionValidator()


    def load_config(self) -> DeploymentConfig:
        """Load deployment configuration from environment"""
        return DeploymentConfig(
            environment = os.getenv("ENVIRONMENT", "production"),
                debug = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"],
                database_url = os.getenv("DATABASE_URL", ""),
                secret_key = os.getenv("SECRET_KEY", ""),
                allowed_hosts = os.getenv("ALLOWED_HOSTS", "").split(","),
                cors_origins = os.getenv("CORS_ORIGINS", "").split(","),
                # Payment providers
            stripe_public_key = os.getenv("STRIPE_PUBLIC_KEY"),
                stripe_secret_key = os.getenv("STRIPE_SECRET_KEY"),
                stripe_webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET"),
                paypal_client_id = os.getenv("PAYPAL_CLIENT_ID"),
                paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET"),
                square_application_id = os.getenv("SQUARE_APPLICATION_ID"),
                square_access_token = os.getenv("SQUARE_ACCESS_TOKEN"),
                razorpay_key_id = os.getenv("RAZORPAY_KEY_ID"),
                razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET"),
                # Security
            jwt_secret_key = os.getenv("JWT_SECRET_KEY"),
                encryption_key = os.getenv("ENCRYPTION_KEY"),
                # Monitoring
            log_level = os.getenv("LOG_LEVEL", "INFO"),
                sentry_dsn = os.getenv("SENTRY_DSN"),
                # Infrastructure
            redis_url = os.getenv("REDIS_URL"),
                # Email
            smtp_host = os.getenv("SMTP_HOST"),
                smtp_port = int(os.getenv("SMTP_PORT", "587")),
                smtp_username = os.getenv("SMTP_USERNAME"),
                smtp_password = os.getenv("SMTP_PASSWORD"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )


    def setup_logging(self, config: DeploymentConfig):
        """Configure production logging"""
        logging.basicConfig(
            level = getattr(logging, config.log_level.upper()),
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                handlers=[
                logging.StreamHandler(sys.stdout),
                    (
                    logging.FileHandler("/var/log/revenue_systems.log")
                    if os.path.exists("/var/log")
                    else logging.StreamHandler()
# BRACKET_SURGEON: disabled
#                 ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     ],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        # Configure Sentry if available
        if config.sentry_dsn:
            try:

                import sentry_sdk
                from sentry_sdk.integrations.flask import FlaskIntegration

                sentry_sdk.init(
                    dsn = config.sentry_dsn,
                        integrations=[FlaskIntegration()],
                        traces_sample_rate = 0.1,
                        environment = config.environment,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                self.logger.info("Sentry monitoring initialized")
            except ImportError:
                self.logger.warning("Sentry SDK not available, monitoring disabled")


    def initialize_database(self, config: DeploymentConfig):
        """Initialize production database"""
        try:
            # Import and initialize all revenue system databases
            sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

            from api_monetization import APIMonetization
            from payment_processor import PaymentProcessor
                from revenue_streams_api import RevenueStreamsAPI

            # Initialize with production database
            db_path = config.database_url.replace("sqlite:///", "").replace(
                "sqlite://", ""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            revenue_api = RevenueStreamsAPI(db_path = db_path)
            api_mon = APIMonetization(db_path = db_path)
            payment_proc = PaymentProcessor(db_path = db_path)

            self.logger.info("Production databases initialized successfully")
        except Exception as e:
            pass
        return True

        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
        return False


    def run_health_checks(self) -> Dict[str, Any]:
        """Run comprehensive health checks"""
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "checks": {},
# BRACKET_SURGEON: disabled
#         }

        # Database connectivity
        try:

            import sqlite3

            database_url = os.getenv("DATABASE_URL", "")
            if database_url:
                db_path = database_url.replace("sqlite:///", "").replace(
                    "sqlite://", ""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                conn = sqlite3.connect(db_path)
                conn.execute("SELECT 1")
                conn.close()
                health_status["checks"]["database"] = "healthy"
            else:
                health_status["checks"]["database"] = "error: no database configured"
        except Exception as e:
            health_status["checks"]["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"

        # Payment provider connectivity
        stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if stripe_key:
            try:

                import stripe

                stripe.api_key = stripe_key
                # Test API call
                stripe.Account.retrieve()
                health_status["checks"]["stripe"] = "healthy"
            except Exception as e:
                health_status["checks"]["stripe"] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["stripe"] = "not configured"

        # File system permissions
        try:
            test_file = "/tmp/revenue_systems_test"
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            health_status["checks"]["filesystem"] = "healthy"
        except Exception as e:
            health_status["checks"]["filesystem"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"

        return health_status


    def deploy(self) -> bool:
        """Execute full production deployment"""
        self.logger.info("Starting production deployment...")

        # Load configuration
        config = self.load_config()

        # Setup logging
        self.setup_logging(config)

        # Run validation
        validation_result = self.validator.run_all_validations()

        if not validation_result["passed"]:
            self.logger.error("Deployment validation failed:")
            for error in validation_result["errors"]:
                self.logger.error(f"  - {error}")
        return False

        if validation_result["warnings"]:
            self.logger.warning("Deployment warnings:")
            for warning in validation_result["warnings"]:
                self.logger.warning(f"  - {warning}")

        # Initialize database
        if not self.initialize_database(config):
            self.logger.error("Database initialization failed")
        return False

        # Run health checks
        health = self.run_health_checks()
        if health["status"] == "unhealthy":
            self.logger.error("Health checks failed, aborting deployment")
        return False

        self.logger.info("Production deployment completed successfully")
        return True


def create_environment_template():
    """Create a template .env file for production"""
    template = """"""
# Production Environment Configuration
# Copy this file to .env and fill in the actual values

# Basic Configuration
ENVIRONMENT = production
DEBUG = false
SECRET_KEY = your - super - secret - key - at - least - 32 - characters - long
DATABASE_URL = sqlite:///production_revenue.db

# Security
ALLOWED_HOSTS = yourdomain.com,www.yourdomain.com
CORS_ORIGINS = https://yourdomain.com,https://www.yourdomain.com
JWT_SECRET_KEY = your - jwt - secret - key
ENCRYPTION_KEY = your - encryption - key

# Stripe Configuration (REQUIRED)
STRIPE_PUBLIC_KEY = pk_live_your_stripe_public_key
STRIPE_SECRET_KEY = sk_live_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET = whsec_your_webhook_secret

# PayPal Configuration (Optional)
PAYPAL_CLIENT_ID = your_paypal_client_id
PAYPAL_CLIENT_SECRET = your_paypal_client_secret

# Square Configuration (Optional)
SQUARE_APPLICATION_ID = your_square_app_id
SQUARE_ACCESS_TOKEN = your_square_access_token

# Razorpay Configuration (Optional)
RAZORPAY_KEY_ID = your_razorpay_key_id
RAZORPAY_KEY_SECRET = your_razorpay_key_secret

# Monitoring (Optional)
LOG_LEVEL = INFO
SENTRY_DSN = your_sentry_dsn_url

# Infrastructure (Optional)
REDIS_URL = redis://localhost:6379/0

# Email Configuration (Optional)
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USERNAME = your_email@gmail.com
SMTP_PASSWORD = your_app_password
""""""

    env_file = os.path.join(os.path.dirname(__file__), "..", ".env.production.template")
    with open(env_file, "w") as f:
        f.write(template.strip())

    print(f"Environment template created: {env_file}")
    print("Copy this file to .env and fill in your actual values")


def main():
    """Main deployment script"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Revenue Systems Production Deployment"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument(
        "--validate - only", action="store_true", help="Only run validation checks"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--health - check",
    action="store_true",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     help="Run health checks")
    parser.add_argument(
        "--create - template", action="store_true", help="Create environment template"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--deploy", action="store_true", help="Run full deployment")

    args = parser.parse_args()

    manager = DeploymentManager()

    if args.create_template:
        create_environment_template()
        return

    if args.validate_only:
        result = manager.validator.run_all_validations()
        print(json.dumps(result, indent = 2))
        sys.exit(0 if result["passed"] else 1)

    if args.health_check:
        health = manager.run_health_checks()
        print(json.dumps(health, indent = 2))
        sys.exit(0 if health["status"] in ["healthy", "degraded"] else 1)

    if args.deploy:
        success = manager.deploy()
        sys.exit(0 if success else 1)

    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()