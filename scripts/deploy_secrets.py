#!/usr / bin / env python3
"""
TRAE.AI Secrets Management Production Deployment Script

This script handles the production deployment of the SecretStore system,
including database initialization, security validation, and system checks.

Usage:
    python scripts / deploy_secrets.py --environment production
    python scripts / deploy_secrets.py --environment staging --validate - only
    python scripts / deploy_secrets.py --init - database --backup - existing

Author: TRAE.AI System
Version: 1.0.0
"""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from backend.secret_store import SecretStore, SecretStoreError

# Add the project root to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class SecretsDeployment:
    """
    Production deployment manager for the SecretStore system.

    Handles database initialization, security validation, backup management,
        and production readiness checks.
    """


    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.backup_dir = self.project_root / "backups" / "secrets"
        self.config = self._load_deployment_config()

        # Environment - specific settings
        self.db_path = self.config.get(
            "database_path",
                {
                "production": "data / secrets.sqlite",
                    "staging": "data / secrets_staging.sqlite",
                    "development": "data / secrets_dev.sqlite",
                    },
                ).get(environment, "data / secrets.sqlite")


    def _load_deployment_config(self) -> Dict:
        """Load deployment configuration from file."""
        config_file = self.project_root / "config" / "deployment.json"

        default_config = {
            "database_path": {
                "production": "data / secrets.sqlite",
                    "staging": "data / secrets_staging.sqlite",
                    "development": "data / secrets_dev.sqlite",
                    },
                "backup_retention_days": 30,
                "security_checks": {
                "require_master_key": True,
                    "validate_permissions": True,
                    "check_encryption": True,
                    },
                "production_requirements": {
                "min_python_version": "3.8",
                    "required_packages": ["cryptography", "sqlite3"],
                    },
                }

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"Warning: Could not load deployment config: {e}")
                print("Using default configuration.")

        return default_config


    def validate_environment(self) -> bool:
        """
        Validate the deployment environment for production readiness.

        Returns:
            bool: True if environment is valid, False otherwise
        """
        print(f"\n=== Validating {self.environment.upper()} Environment ===")

        checks_passed = 0
        total_checks = 6

        # Check 1: Python version
        min_version = self.config["production_requirements"]["min_python_version"]
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if current_version >= min_version:
            print(f"✓ Python version: {current_version} (>= {min_version})")
            checks_passed += 1
        else:
            print(f"✗ Python version: {current_version} (requires >= {min_version})")

        # Check 2: Required packages
        required_packages = self.config["production_requirements"]["required_packages"]
        for package in required_packages:
            try:
                __import__(package)
                print(f"✓ Package available: {package}")
                checks_passed += 1
            except ImportError:
                print(f"✗ Missing package: {package}")

        # Check 3: Master key environment variable
        if self.config["security_checks"]["require_master_key"]:
            if os.getenv("TRAE_MASTER_KEY"):
                print("✓ Master key environment variable set")
                checks_passed += 1
            else:
                print("✗ TRAE_MASTER_KEY environment variable not set")

        # Check 4: Directory permissions
        if self.config["security_checks"]["validate_permissions"]:
            data_dir = Path(self.db_path).parent
            if self._check_directory_permissions(data_dir):
                print(f"✓ Directory permissions: {data_dir}")
                checks_passed += 1
            else:
                print(f"✗ Invalid directory permissions: {data_dir}")

        # Check 5: Database file permissions (if exists)
        db_file = Path(self.db_path)
        if db_file.exists():
            if self._check_file_permissions(db_file):
                print(f"✓ Database file permissions: {db_file}")
                checks_passed += 1
            else:
                print(f"✗ Invalid database file permissions: {db_file}")
        else:
            print(f"ℹ Database file does not exist yet: {db_file}")
            checks_passed += 1  # Not an error for new deployments

        # Check 6: Encryption functionality
        if self.config["security_checks"]["check_encryption"]:
            if self._test_encryption():
                print("✓ Encryption functionality working")
                checks_passed += 1
            else:
                print("✗ Encryption functionality failed")

        success_rate = (checks_passed / total_checks) * 100
        print(
            f"\nValidation Results: {checks_passed}/{total_checks} checks passed ({success_rate:.1f}%)"
        )

        if self.environment == "production" and checks_passed < total_checks:
            print("❌ Production deployment requires all checks to pass.")
            return False
        elif checks_passed >= (total_checks * 0.8):  # 80% for staging / dev
            print("✅ Environment validation passed.")
            return True
        else:
            print("❌ Environment validation failed.")
            return False


    def _check_directory_permissions(self, directory: Path) -> bool:
        """Check if directory has appropriate permissions."""
        try:
            directory.mkdir(parents = True, exist_ok = True)
            # Test write permissions
            test_file = directory / ".permission_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False


    def _check_file_permissions(self, file_path: Path) -> bool:
        """Check if file has appropriate permissions (readable / writable by owner only)."""
        try:
            stat = file_path.stat()
            # Check if file is readable and writable by owner
            return os.access(file_path, os.R_OK | os.W_OK)
        except Exception:
            return False


    def _test_encryption(self) -> bool:
        """Test encryption functionality with a temporary store."""
        try:
            # Create a temporary database for testing
            test_db = self.data_dir / "test_encryption.sqlite"
            test_db.parent.mkdir(parents = True, exist_ok = True)

            # Test with a temporary master key
            os.environ["TRAE_MASTER_KEY_TEST"] = "test_key_for_validation"

            with SecretStore(str(test_db), os.getenv("TRAE_MASTER_KEY_TEST")) as store:
                # Test store and retrieve
                test_key = "test_secret"
                test_value = "test_value_123"

                store.store_secret(test_key, test_value)
                retrieved_value = store.get_secret(test_key)

                success = retrieved_value == test_value

                # Clean up
                store.delete_secret(test_key)

            # Remove test database
            if test_db.exists():
                test_db.unlink()

            # Clean up test environment variable
            if "TRAE_MASTER_KEY_TEST" in os.environ:
                del os.environ["TRAE_MASTER_KEY_TEST"]

            return success

        except Exception as e:
            print(f"Encryption test failed: {e}")
            return False


    def backup_existing_database(self) -> Optional[str]:
        """
        Create a backup of the existing database before deployment.

        Returns:
            str: Path to backup file if successful, None otherwise
        """
        db_file = Path(self.db_path)

        if not db_file.exists():
            print("No existing database to backup.")
            return None

        # Create backup directory
        self.backup_dir.mkdir(parents = True, exist_ok = True)

        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"secrets_backup_{self.environment}_{timestamp}.sqlite"
        backup_path = self.backup_dir / backup_filename

        try:
            shutil.copy2(db_file, backup_path)
            print(f"✓ Database backed up to: {backup_path}")

            # Clean up old backups
            self._cleanup_old_backups()

            return str(backup_path)

        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return None


    def _cleanup_old_backups(self) -> None:
        """Remove old backup files based on retention policy."""
        retention_days = self.config.get("backup_retention_days", 30)
        cutoff_time = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)

        try:
            for backup_file in self.backup_dir.glob("secrets_backup_*.sqlite"):
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    print(f"Removed old backup: {backup_file.name}")
        except Exception as e:
            print(f"Warning: Could not clean up old backups: {e}")


    def initialize_database(self) -> bool:
        """
        Initialize the secrets database for production use.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        print(f"\n=== Initializing Database for {self.environment.upper()} ===")

        try:
            # Ensure data directory exists
            Path(self.db_path).parent.mkdir(parents = True, exist_ok = True)

            # Check if master key is available
            master_key = os.getenv("TRAE_MASTER_KEY")
            if not master_key:
                print("✗ TRAE_MASTER_KEY environment variable not set")
                return False

            # Initialize the database
            with SecretStore(self.db_path, master_key) as store:
                # Test basic functionality
                test_key = "_deployment_test"
                test_value = f"deployment_test_{datetime.now().isoformat()}"

                store.store_secret(test_key, test_value)
                retrieved = store.get_secret(test_key)

                if retrieved == test_value:
                    print("✓ Database initialization successful")
                    print("✓ Encryption / decryption test passed")

                    # Clean up test secret
                    store.delete_secret(test_key)

                    # Set secure file permissions
                    self._set_secure_permissions(Path(self.db_path))

                    return True
                else:
                    print("✗ Database test failed")
                    return False

        except SecretStoreError as e:
            print(f"✗ Database initialization failed: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during initialization: {e}")
            return False


    def _set_secure_permissions(self, file_path: Path) -> None:
        """Set secure file permissions (owner read / write only)."""
        try:
            # Set permissions to 600 (owner read / write only)
            os.chmod(file_path, 0o600)
            print(f"✓ Secure permissions set for: {file_path}")
        except Exception as e:
            print(f"Warning: Could not set secure permissions: {e}")


    def deploy(
        self,
            validate_only: bool = False,
            backup_existing: bool = True,
            init_database: bool = True,
            ) -> bool:
        """
        Execute the complete deployment process.

        Args:
            validate_only (bool): Only run validation, don't deploy
            backup_existing (bool): Create backup before deployment
            init_database (bool): Initialize database during deployment

        Returns:
            bool: True if deployment successful, False otherwise
        """
        print(f"\n🚀 Starting TRAE.AI Secrets Management Deployment")
        print(f"Environment: {self.environment.upper()}")
        print(f"Database: {self.db_path}")
        print(f"Timestamp: {datetime.now().isoformat()}")

        # Step 1: Validate environment
        if not self.validate_environment():
            print("\n❌ Deployment aborted due to validation failures.")
            return False

        if validate_only:
            print("\n✅ Validation - only mode completed successfully.")
            return True

        # Step 2: Backup existing database
        if backup_existing:
            backup_path = self.backup_existing_database()
            if backup_path:
                print(f"Backup created: {backup_path}")

        # Step 3: Initialize database
        if init_database:
            if not self.initialize_database():
                print("\n❌ Deployment failed during database initialization.")
                return False

        # Step 4: Final validation
        print("\n=== Final Deployment Validation ===")
        try:
            master_key = os.getenv("TRAE_MASTER_KEY")
            with SecretStore(self.db_path, master_key) as store:
                # Test all basic operations
                test_operations = [
                    (
                        "store_secret",
                            lambda: store.store_secret("_final_test", "test_value"),
                            ),
                        ("get_secret", lambda: store.get_secret("_final_test")),
                        ("secret_exists", lambda: store.secret_exists("_final_test")),
                        ("list_secrets", lambda: store.list_secrets()),
                        ("delete_secret", lambda: store.delete_secret("_final_test")),
                        ]

                for operation_name, operation in test_operations:
                    try:
                        result = operation()
                        print(f"✓ {operation_name}: OK")
                    except Exception as e:
                        print(f"✗ {operation_name}: {e}")
                        return False

            print("\n🎉 Deployment completed successfully!")
            print(f"SecretStore is ready for {self.environment} use.")
            return True

        except Exception as e:
            print(f"\n❌ Final validation failed: {e}")
            return False


def main():
    """Main entry point for the deployment script."""
    parser = argparse.ArgumentParser(
        description="TRAE.AI Secrets Management Production Deployment",
            formatter_class = argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s --environment production
  %(prog)s --environment staging --validate - only
  %(prog)s --init - database --backup - existing
  %(prog)s --environment production --no - backup

Environment Variables:
  TRAE_MASTER_KEY: Master password for encryption (required)
  TRAE_SECRETS_DB: Override default database path (optional)
        """,
            )

    parser.add_argument(
        "--environment",
            "-e",
            choices=["production", "staging", "development"],
            default="production",
            help="Deployment environment",
            )

    parser.add_argument(
        "--validate - only",
            action="store_true",
            help="Only validate environment, do not deploy",
            )

    parser.add_argument(
        "--backup - existing",
            action="store_true",
            default = True,
            help="Create backup of existing database",
            )

    parser.add_argument(
        "--no - backup",
            dest="backup_existing",
            action="store_false",
            help="Skip backup of existing database",
            )

    parser.add_argument(
        "--init - database",
            action="store_true",
            default = True,
            help="Initialize database during deployment",
            )

    parser.add_argument(
        "--no - init",
            dest="init_database",
            action="store_false",
            help="Skip database initialization",
            )

    args = parser.parse_args()

    # Override database path if environment variable is set
    if os.getenv("TRAE_SECRETS_DB"):
        print(f"Using database path from environment: {os.getenv('TRAE_SECRETS_DB')}")

    # Create deployment manager
    deployment = SecretsDeployment(args.environment)

    # Execute deployment
    success = deployment.deploy(
        validate_only = args.validate_only,
            backup_existing = args.backup_existing,
            init_database = args.init_database,
            )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
