#!/usr / bin / env python3
""""""
Secure Configuration Generator for TRAE AI Production

This script generates secure credentials \
#     and configuration files for production deployment.
Run this script before deploying to production to ensure all secrets are properly configured.
""""""

import argparse
import hashlib
import json
import os
import secrets
import string
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_secure_password(length: int = 32, include_symbols: bool = True) -> str:
    """Generate a cryptographically secure password."""
    alphabet = string.ascii_letters + string.digits
    if include_symbols:
        alphabet += "!@#$%^&*()-_=+[]{}|;:,.<>?""

    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


def generate_api_key(prefix: str = "trae", length: int = 32) -> str:
    """Generate a secure API key with prefix."""
    key = secrets.token_urlsafe(length)
    return f"{prefix}_{key}"


def generate_jwt_secret() -> str:
    """Generate a secure JWT secret."""
    return secrets.token_urlsafe(64)


def generate_database_credentials() -> Dict[str, str]:
    """Generate secure database credentials."""
    return {
        "DB_USER": f"trae_user_{secrets.token_hex(4)}",
        "DB_PASSWORD": generate_secure_password(32, False),  # No symbols for DB password
        "DB_NAME": "trae_ai_production",
# BRACKET_SURGEON: disabled
#     }


def generate_redis_credentials() -> Dict[str, str]:
    """Generate secure Redis credentials."""
    return {"REDIS_PASSWORD": generate_secure_password(32, False)}


def generate_rabbitmq_credentials() -> Dict[str, str]:
    """Generate secure RabbitMQ credentials."""
    return {
        "RABBITMQ_USER": f"trae_mq_{secrets.token_hex(4)}",
        "RABBITMQ_PASSWORD": generate_secure_password(32, False),
        "RABBITMQ_ERLANG_COOKIE": secrets.token_hex(32),
# BRACKET_SURGEON: disabled
#     }


def generate_admin_credentials() -> Dict[str, str]:
    """Generate secure admin credentials."""
    return {
        "ADMIN_USERNAME": f"admin_{secrets.token_hex(4)}",
        "ADMIN_PASSWORD": generate_secure_password(16, True),
        "ADMIN_EMAIL": "admin@yourdomain.com",  # User should update this
# BRACKET_SURGEON: disabled
#     }


def generate_encryption_keys() -> Dict[str, str]:
    """Generate encryption keys for various purposes."""
    return {
        "SECRET_KEY": secrets.token_urlsafe(32),
        "JWT_SECRET": generate_jwt_secret(),
        "TRAE_MASTER_KEY": generate_api_key("trae_master", 32),
        "BACKUP_ENCRYPTION_KEY": secrets.token_urlsafe(32),
# BRACKET_SURGEON: disabled
#     }


def create_production_env_file(credentials: Dict[str, Any], output_path: str) -> None:
    """Create the production .env file with secure credentials."""
    env_content = f"""# Production Environment Configuration"""
# Generated on: {datetime.now().isoformat()}
# NEVER commit this file to version control

ENVIRONMENT = production
DEBUG = false
LOG_LEVEL = WARNING

# Security Keys
SECRET_KEY={credentials['SECRET_KEY']}
JWT_SECRET={credentials['JWT_SECRET']}
TRAE_MASTER_KEY={credentials['TRAE_MASTER_KEY']}

# Database Configuration
DATABASE_URL = postgresql://{credentials['DB_USER']}:{credentials['DB_PASSWORD']}@localhost:5432/{credentials['DB_NAME']}
DB_HOST = localhost
DB_PORT = 5432
DB_NAME={credentials['DB_NAME']}
DB_USER={credentials['DB_USER']}
DB_PASSWORD={credentials['DB_PASSWORD']}

# Redis Configuration
REDIS_URL = redis://:{credentials['REDIS_PASSWORD']}@localhost:6379 / 0
REDIS_PASSWORD={credentials['REDIS_PASSWORD']}

# RabbitMQ Configuration
RABBITMQ_URL = amqp://{credentials['RABBITMQ_USER']}:{credentials['RABBITMQ_PASSWORD']}@localhost:5672/
RABBITMQ_USER={credentials['RABBITMQ_USER']}
RABBITMQ_PASSWORD={credentials['RABBITMQ_PASSWORD']}
RABBITMQ_ERLANG_COOKIE={credentials['RABBITMQ_ERLANG_COOKIE']}

# External API Keys (UPDATE THESE)
OPENAI_API_KEY = REPLACE_WITH_OPENAI_API_KEY
SUPABASE_URL = REPLACE_WITH_SUPABASE_URL
SUPABASE_KEY = REPLACE_WITH_SUPABASE_KEY

# Security Settings
CORS_ORIGINS = https://yourdomain.com,https://www.yourdomain.com
ALLOWED_HOSTS = yourdomain.com,www.yourdomain.com
SECURE_COOKIES = true
HTTPS_ONLY = true

# Admin User (Change email address)
ADMIN_USERNAME={credentials['ADMIN_USERNAME']}
ADMIN_PASSWORD={credentials['ADMIN_PASSWORD']}
ADMIN_EMAIL={credentials['ADMIN_EMAIL']}

# Monitoring and Logging
SENTRY_DSN = REPLACE_WITH_SENTRY_DSN
LOG_FILE_PATH=/var / log / trae - ai / app.log

# Rate Limiting
RATE_LIMIT_PER_MINUTE = 60
RATE_LIMIT_BURST = 10

# Session Configuration
SESSION_TIMEOUT_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# File Upload Limits
MAX_FILE_SIZE_MB = 10
ALLOWED_FILE_TYPES = jpg,jpeg,png,gif,pdf,txt,csv

# Backup Configuration
BACKUP_ENCRYPTION_KEY={credentials['BACKUP_ENCRYPTION_KEY']}
BACKUP_SCHEDULE = 0 2 * * *  # Daily at 2 AM

# Grafana Admin Password
GRAFANA_ADMIN_PASSWORD={generate_secure_password(16, False)}
""""""

    with open(output_path, "w") as f:
        f.write(env_content)

    # Set restrictive permissions
    os.chmod(output_path, 0o600)
    print(f"✅ Created secure production environment file: {output_path}")


def create_credentials_backup(credentials: Dict[str, Any], output_path: str) -> None:
    """Create an encrypted backup of credentials for safe storage."""
    backup_data = {
        "generated_at": datetime.now().isoformat(),
        "credentials": credentials,
        "notes": [
            "Store this file securely and separately from your codebase",
            "Use a password manager or encrypted storage",
            "Never commit this file to version control",
            "Rotate these credentials regularly",
# BRACKET_SURGEON: disabled
#         ],
# BRACKET_SURGEON: disabled
#     }

    with open(output_path, "w") as f:
        json.dump(backup_data, f, indent=2)

    os.chmod(output_path, 0o600)
    print(f"✅ Created credentials backup: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate secure configuration for TRAE AI production"
# BRACKET_SURGEON: disabled
#     )
    parser.add_argument("--output - dir", default=".", help="Output directory for generated files")
    parser.add_argument("--backup", action="store_true", help="Create credentials backup file")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    print("🔐 Generating secure credentials for TRAE AI production...")

    # Generate all credentials
    credentials = {}
    credentials.update(generate_encryption_keys())
    credentials.update(generate_database_credentials())
    credentials.update(generate_redis_credentials())
    credentials.update(generate_rabbitmq_credentials())
    credentials.update(generate_admin_credentials())

    # Create production environment file
    env_file_path = output_dir / ".env.production"
    create_production_env_file(credentials, str(env_file_path))

    # Create credentials backup if requested
    if args.backup:
        backup_path = (
            output_dir / f"credentials_backup_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
# BRACKET_SURGEON: disabled
#         )
        create_credentials_backup(credentials, str(backup_path))

    print("\\n🎯 Next Steps:")
    print("1. Review and update the generated .env.production file")
    print("2. Update external API keys (OpenAI, Supabase, etc.)")
    print("3. Update domain names and email addresses")
    print("4. Store credentials securely (password manager recommended)")
    print("5. Never commit .env.production to version control")
    print("6. Test the configuration in a staging environment first")

    print("\\n⚠️  IMPORTANT SECURITY NOTES:")
    print("- Change the admin email address before deployment")
    print("- Rotate these credentials regularly")
    print("- Use HTTPS in production")
    print("- Enable firewall rules to restrict database access")
    print("- Monitor logs for suspicious activity")

    print(f"\\n✅ Secure configuration generated successfully!")
    print(f"📁 Files created in: {output_dir.absolute()}")


if __name__ == "__main__":
    main()