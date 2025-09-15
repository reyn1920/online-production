#!/usr/bin/env python3
""""""
API Configuration Manager
Centralized management of API keys, secrets, and configurations for 100+ APIs

Features:
- Secure environment variable management
- Configuration templates
- Deployment environment handling
- Secret rotation
- Configuration validation
- Backup and restore

Usage:
    python api_config_manager.py
""""""

import base64
import json
import logging
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class APIConfig:
    api_key: str
    api_name: str
    env_var: str
    current_value: Optional[str]
    is_configured: bool
    is_encrypted: bool
    last_updated: str
    expires_at: Optional[str]
    backup_count: int
    validation_status: str
    deployment_environments: List[str]
    cost_tier: str
    priority: str
    phase: int
    required_scopes: List[str]
    rate_limits: Dict[str, Any]
    documentation_url: str
    health_check_url: Optional[str]


@dataclass
class DeploymentEnvironment:
    name: str
    description: str
    base_url: str
    config_file: str
    is_production: bool
    requires_approval: bool
    auto_deploy: bool
    secret_prefix: str
    backup_retention_days: int


class APIConfigManager:
    def __init__(self):
        self.config_dir = Path("api_configs")
        self.backup_dir = Path("config_backups")
        self.templates_dir = Path("config_templates")

        # Create directories
        self.config_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

        self.encryption_key = self.get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        self.api_configs = {}
        self.environments = self.load_environments()

        # Load existing configurations
        self.load_all_configs()

        # Import API registry
        try:
            from api_registration_automation import API_REGISTRY

            self.api_registry = API_REGISTRY
            self.sync_with_registry()
        except ImportError:
            logger.warning("API registry not found, using empty registry")
            self.api_registry = {}

    def get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for sensitive data"""
        key_file = self.config_dir / "encryption.key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new key
            password = os.getenv("CONFIG_MASTER_PASSWORD")
            salt = os.urandom(16)

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
# BRACKET_SURGEON: disabled
#             )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

            with open(key_file, "wb") as f:
                f.write(key)

            logger.info("Created new encryption key")
            return key

    def load_environments(self) -> Dict[str, DeploymentEnvironment]:
        """Load deployment environment configurations"""
        environments = {
            "development": DeploymentEnvironment(
                name="development",
                description="Local development environment",
                base_url="http://localhost:8000",
                config_file=".env.development",
                is_production=False,
                requires_approval=False,
                auto_deploy=True,
                secret_prefix="DEV_",
                backup_retention_days=7,
# BRACKET_SURGEON: disabled
#             ),
            "staging": DeploymentEnvironment(
                name="staging",
                description="Staging environment for testing",
                base_url="https://staging.example.com",
                config_file=".env.staging",
                is_production=False,
                requires_approval=True,
                auto_deploy=False,
                secret_prefix="STAGING_",
                backup_retention_days=30,
# BRACKET_SURGEON: disabled
#             ),
            "production": DeploymentEnvironment(
                name="production",
                description="Live production environment",
                base_url="https://api.example.com",
                config_file=".env.production",
                is_production=True,
                requires_approval=True,
                auto_deploy=False,
                secret_prefix="PROD_",
                backup_retention_days=90,
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

        # Load custom environments if they exist
        env_config_file = self.config_dir / "environments.yaml"
        if env_config_file.exists():
            try:
                with open(env_config_file, "r") as f:
                    custom_envs = yaml.safe_load(f)
                    for name, config in custom_envs.items():
                        environments[name] = DeploymentEnvironment(**config)
            except Exception as e:
                logger.error(f"Failed to load custom environments: {e}")

        return environments

    def sync_with_registry(self):
        """Sync configurations with API registry"""
        logger.info("Syncing configurations with API registry...")

        for api_key, api_info in self.api_registry.items():
            if api_key not in self.api_configs:
                # Create new configuration
                config = APIConfig(
                    api_key=api_key,
                    api_name=api_info["name"],
                    env_var=api_info.get("env_var", f"{api_key.upper()}_API_KEY"),
                    current_value=os.getenv(api_info.get("env_var", f"{api_key.upper()}_API_KEY")),
                    is_configured=bool(
                        os.getenv(api_info.get("env_var", f"{api_key.upper()}_API_KEY"))
# BRACKET_SURGEON: disabled
#                     ),
                    is_encrypted=False,
                    last_updated=datetime.now().isoformat(),
                    expires_at=None,
                    backup_count=0,
                    validation_status="pending",
                    deployment_environments=["development"],
                    cost_tier=api_info.get("cost", "free"),
                    priority=api_info.get("priority", "medium"),
                    phase=api_info.get("phase", 1),
                    required_scopes=api_info.get("scopes", []),
                    rate_limits=api_info.get("rate_limits", {}),
                    documentation_url=api_info.get("docs_url", ""),
                    health_check_url=api_info.get("health_url"),
# BRACKET_SURGEON: disabled
#                 )
                self.api_configs[api_key] = config

        logger.info(f"Synced {len(self.api_configs)} API configurations")

    def load_all_configs(self):
        """Load all existing configurations from disk"""
        config_files = list(self.config_dir.glob("*.json"))

        for config_file in config_files:
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    config = APIConfig(**config_data)
                    self.api_configs[config.api_key] = config
            except Exception as e:
                logger.error(f"Failed to load config {config_file}: {e}")

        logger.info(f"Loaded {len(self.api_configs)} configurations from disk")

    def save_config(self, api_key: str):
        """Save configuration to disk"""
        if api_key not in self.api_configs:
            raise ValueError(f"Configuration for {api_key} not found")

        config = self.api_configs[api_key]
        config_file = self.config_dir / f"{api_key}.json"

        # Create backup before saving
        self.create_backup(api_key)

        try:
            with open(config_file, "w") as f:
                json.dump(asdict(config), f, indent=2)

            config.last_updated = datetime.now().isoformat()
            logger.info(f"Saved configuration for {api_key}")

        except Exception as e:
            logger.error(f"Failed to save config for {api_key}: {e}")
            raise

    def create_backup(self, api_key: str):
        """Create backup of configuration"""
        if api_key not in self.api_configs:
            return

        config = self.api_configs[api_key]
        timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
        backup_file = self.backup_dir / f"{api_key}_{timestamp}.json"

        try:
            with open(backup_file, "w") as f:
                json.dump(asdict(config), f, indent=2)

            config.backup_count += 1
            logger.debug(f"Created backup for {api_key}: {backup_file}")

        except Exception as e:
            logger.error(f"Failed to create backup for {api_key}: {e}")

    def encrypt_value(self, value: str) -> str:
        """Encrypt a sensitive value"""
        if not value:
            return value

        encrypted_bytes = self.cipher_suite.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()

    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a sensitive value"""
        if not encrypted_value:
            return encrypted_value

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt value: {e}")
            return encrypted_value

    def set_api_key(self, api_key: str, value: str, encrypt: bool = True):
        """Set API key value"""
        if api_key not in self.api_configs:
            raise ValueError(f"Configuration for {api_key} not found")

        config = self.api_configs[api_key]

        # Encrypt if requested
        if encrypt:
            config.current_value = self.encrypt_value(value)
            config.is_encrypted = True
        else:
            config.current_value = value
            config.is_encrypted = False

        config.is_configured = True
        config.last_updated = datetime.now().isoformat()

        # Save to disk
        self.save_config(api_key)

        logger.info(f"Updated API key for {api_key} (encrypted: {encrypt})")

    def get_api_key(self, api_key: str, decrypt: bool = True) -> Optional[str]:
        """Get API key value"""
        if api_key not in self.api_configs:
            return None

        config = self.api_configs[api_key]

        if not config.current_value:
            return None

        if config.is_encrypted and decrypt:
            return self.decrypt_value(config.current_value)
        else:
            return config.current_value

    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """Validate API key configuration"""
        if api_key not in self.api_configs:
            return {"valid": False, "error": "Configuration not found"}

        config = self.api_configs[api_key]
        validation_result = {"valid": True, "errors": [], "warnings": [], "info": []}

        # Check if configured
        if not config.is_configured:
            validation_result["errors"].append("API key not configured")
            validation_result["valid"] = False

        # Check if value exists
        if not config.current_value:
            validation_result["errors"].append("API key value is empty")
            validation_result["valid"] = False

        # Check expiration
        if config.expires_at:
            expires_dt = datetime.fromisoformat(config.expires_at)
            if expires_dt < datetime.now():
                validation_result["errors"].append("API key has expired")
                validation_result["valid"] = False
            elif expires_dt < datetime.now() + timedelta(days=7):
                validation_result["warnings"].append("API key expires within 7 days")

        # Check environment variable
        env_value = os.getenv(config.env_var)
        if not env_value:
            validation_result["warnings"].append(f"Environment variable {config.env_var} not set")
        elif env_value != self.get_api_key(api_key):
            validation_result["warnings"].append("Environment variable differs from stored value")

        # Update validation status
        if validation_result["valid"]:
            config.validation_status = "valid"
        else:
            config.validation_status = "invalid"

        return validation_result

    def generate_env_file(self, environment: str = "development") -> str:
        """Generate .env file for specific environment"""
        if environment not in self.environments:
            raise ValueError(f"Environment {environment} not found")

        env_config = self.environments[environment]
        env_lines = []

        # Add header
        env_lines.append(f"# API Configuration for {environment.upper()} environment")"
        env_lines.append(f"# Generated on {datetime.now().isoformat()}")"
        env_lines.append(f"# Environment: {env_config.description}")"
        env_lines.append("")

        # Add base configuration
        env_lines.append("# Base Configuration")"
        env_lines.append(f"NODE_ENV={environment}")
        env_lines.append(f"API_BASE_URL={env_config.base_url}")
        env_lines.append(f"ENVIRONMENT={environment}")
        env_lines.append("")

        # Group APIs by phase
        phases = {}
        for config in self.api_configs.values():
            if config.phase not in phases:
                phases[config.phase] = []
            phases[config.phase].append(config)

        # Add APIs by phase
        for phase in sorted(phases.keys()):
            env_lines.append(f"# Phase {phase} APIs")"

            for config in sorted(phases[phase], key=lambda x: x.api_name):
                if environment in config.deployment_environments:
                    api_key_value = self.get_api_key(config.api_key)

                    if api_key_value:
                        # Add prefix for non - development environments
                        var_name = config.env_var
                        if not env_config.is_production and env_config.secret_prefix:
                            var_name = f"{env_config.secret_prefix}{config.env_var}"

                        env_lines.append(f"{var_name}={api_key_value}")
                    else:
                        env_lines.append(f"# {config.env_var}=  # Not configured")"

                    # Add metadata as comments
                    env_lines.append(
                        f"# {config.api_name} - {config.cost_tier} tier, {config.priority} priority""
# BRACKET_SURGEON: disabled
#                     )
                    if config.documentation_url:
                        env_lines.append(f"# Docs: {config.documentation_url}")"

            env_lines.append("")

        return "\\n".join(env_lines)

    def deploy_to_environment(self, environment: str, dry_run: bool = False) -> Dict[str, Any]:
        """Deploy configuration to specific environment"""
        if environment not in self.environments:
            raise ValueError(f"Environment {environment} not found")

        env_config = self.environments[environment]
        result = {
            "environment": environment,
            "success": True,
            "deployed_apis": [],
            "skipped_apis": [],
            "errors": [],
# BRACKET_SURGEON: disabled
#         }

        # Check if approval required
        if env_config.requires_approval and not dry_run:
            approval = input(
                f"Deploy to {environment}? This is a {env_config.description}. (yes/no): "
# BRACKET_SURGEON: disabled
#             )
            if approval.lower() != "yes":
                result["success"] = False
                result["errors"].append("Deployment cancelled by user")
                return result

        # Generate environment file
        try:
            env_content = self.generate_env_file(environment)

            if dry_run:
                print(f"\\n--- DRY RUN: {env_config.config_file} ---")
                print(env_content)
                print("--- END DRY RUN ---\\n")
            else:
                # Write to file
                with open(env_config.config_file, "w") as f:
                    f.write(env_content)

                logger.info(f"Deployed configuration to {environment}: {env_config.config_file}")

            # Count deployed APIs
            for config in self.api_configs.values():
                if environment in config.deployment_environments:
                    if config.is_configured:
                        result["deployed_apis"].append(config.api_key)
                    else:
                        result["skipped_apis"].append(config.api_key)

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            logger.error(f"Failed to deploy to {environment}: {e}")

        return result

    def rotate_api_key(self, api_key: str, new_value: str):
        """Rotate API key with backup"""
        if api_key not in self.api_configs:
            raise ValueError(f"Configuration for {api_key} not found")

        self.api_configs[api_key]
        old_value = self.get_api_key(api_key)

        # Create backup with old value
        backup_data = {
            "api_key": api_key,
            "old_value": old_value,
            "new_value": new_value,
            "rotated_at": datetime.now().isoformat(),
            "rotated_by": os.getenv("USER", "unknown"),
# BRACKET_SURGEON: disabled
#         }

        rotation_file = (
            self.backup_dir
            / f"{api_key}_rotation_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
# BRACKET_SURGEON: disabled
#         )
        with open(rotation_file, "w") as f:
            json.dump(backup_data, f, indent=2)

        # Update with new value
        self.set_api_key(api_key, new_value)

        logger.info(f"Rotated API key for {api_key}")

    def cleanup_backups(self, retention_days: int = 30):
        """Clean up old backup files"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        cleaned_count = 0

        for backup_file in self.backup_dir.glob("*.json"):
            try:
                file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                if file_time < cutoff_date:
                    backup_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to clean backup {backup_file}: {e}")

        logger.info(f"Cleaned up {cleaned_count} old backup files")

    def export_configurations(self, include_secrets: bool = False) -> Dict[str, Any]:
        """Export all configurations"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "include_secrets": include_secrets,
            "environments": {k: asdict(v) for k, v in self.environments.items()},
            "configurations": {},
# BRACKET_SURGEON: disabled
#         }

        for api_key, config in self.api_configs.items():
            config_data = asdict(config)

            if not include_secrets:
                config_data["current_value"] = "***REDACTED***" if config.current_value else None

            export_data["configurations"][api_key] = config_data

        return export_data

    def import_configurations(self, import_data: Dict[str, Any], overwrite: bool = False):
        """Import configurations from export data"""
        imported_count = 0
        skipped_count = 0

        for api_key, config_data in import_data.get("configurations", {}).items():
            if api_key in self.api_configs and not overwrite:
                skipped_count += 1
                continue

            try:
                config = APIConfig(**config_data)
                self.api_configs[api_key] = config
                self.save_config(api_key)
                imported_count += 1
            except Exception as e:
                logger.error(f"Failed to import config for {api_key}: {e}")

        logger.info(f"Imported {imported_count} configurations, skipped {skipped_count}")

    def generate_status_report(self) -> Dict[str, Any]:
        """Generate comprehensive status report"""
        total_apis = len(self.api_configs)
        configured_apis = sum(1 for c in self.api_configs.values() if c.is_configured)
        encrypted_apis = sum(1 for c in self.api_configs.values() if c.is_encrypted)

        # Phase breakdown
        phase_stats = {}
        for phase in [1, 2, 3, 4]:
            phase_configs = [c for c in self.api_configs.values() if c.phase == phase]
            phase_stats[phase] = {
                "total": len(phase_configs),
                "configured": sum(1 for c in phase_configs if c.is_configured),
                "encrypted": sum(1 for c in phase_configs if c.is_encrypted),
# BRACKET_SURGEON: disabled
#             }

        # Environment deployment status
        env_stats = {}
        for env_name in self.environments.keys():
            deployed_apis = [
                c for c in self.api_configs.values() if env_name in c.deployment_environments
# BRACKET_SURGEON: disabled
#             ]
            env_stats[env_name] = {
                "total_apis": len(deployed_apis),
                "configured_apis": sum(1 for c in deployed_apis if c.is_configured),
# BRACKET_SURGEON: disabled
#             }

        return {
            "summary": {
                "total_apis": total_apis,
                "configured_apis": configured_apis,
                "encrypted_apis": encrypted_apis,
                "configuration_rate": (
                    (configured_apis / total_apis * 100) if total_apis > 0 else 0
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             },
            "phase_breakdown": phase_stats,
            "environment_deployment": env_stats,
            "generated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def interactive_menu(self):
        """Interactive configuration management menu"""
        while True:
            print("\\n🔧 API Configuration Manager")
            print("=" * 50)
            print("1. 📋 View all configurations")
            print("2. 🔑 Set API key")
            print("3. 👁️  View API key")
            print("4. ✅ Validate configuration")
            print("5. 📄 Generate .env file")
            print("6. 🚀 Deploy to environment")
            print("7. 🔄 Rotate API key")
            print("8. 📊 Status report")
            print("9. 💾 Export configurations")
            print("10. 📥 Import configurations")
            print("11. 🧹 Cleanup backups")
            print("12. ❌ Exit")

            choice = input("\\nSelect option (1 - 12): ").strip()

            if choice == "1":
                self.show_all_configurations()
            elif choice == "2":
                self.interactive_set_api_key()
            elif choice == "3":
                self.interactive_view_api_key()
            elif choice == "4":
                self.interactive_validate_config()
            elif choice == "5":
                self.interactive_generate_env_file()
            elif choice == "6":
                self.interactive_deploy_environment()
            elif choice == "7":
                self.interactive_rotate_key()
            elif choice == "8":
                self.show_status_report()
            elif choice == "9":
                self.interactive_export_configs()
            elif choice == "10":
                self.interactive_import_configs()
            elif choice == "11":
                self.interactive_cleanup_backups()
            elif choice == "12":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice")
                time.sleep(1)

    def show_all_configurations(self):
        """Show all API configurations"""
        print("\\n📋 API Configurations:")
        print("-" * 80)

        for api_key, config in sorted(self.api_configs.items()):
            status = "✅" if config.is_configured else "❌"
            encrypted = "🔒" if config.is_encrypted else "🔓"
            print(f"{status} {encrypted} {config.api_name} ({api_key})")
            print(f"    Env Var: {config.env_var}")
            print(f"    Phase: {config.phase}, Priority: {config.priority}")
            print(f"    Last Updated: {config.last_updated}")
            print()

        input("\\nPress Enter to continue...")

    def interactive_set_api_key(self):
        """Interactive API key setting"""
        api_key = input("Enter API key identifier: ").strip()

        if api_key not in self.api_configs:
            print(f"❌ API {api_key} not found")
            input("Press Enter to continue...")
            return

        value = input("Enter API key value: ").strip()
        encrypt = input("Encrypt value? (y/n): ").strip().lower() == "y"

        try:
            self.set_api_key(api_key, value, encrypt)
            print(f"✅ API key for {api_key} updated successfully")
        except Exception as e:
            print(f"❌ Failed to set API key: {e}")

        input("\\nPress Enter to continue...")

    def interactive_view_api_key(self):
        """Interactive API key viewing"""
        api_key = input("Enter API key identifier: ").strip()

        if api_key not in self.api_configs:
            print(f"❌ API {api_key} not found")
            input("Press Enter to continue...")
            return

        value = self.get_api_key(api_key)
        config = self.api_configs[api_key]

        print(f"\\n🔑 API Key: {api_key}")
        print(f"Name: {config.api_name}")
        print(f"Environment Variable: {config.env_var}")
        print(f"Configured: {'Yes' if config.is_configured else 'No'}")
        print(f"Encrypted: {'Yes' if config.is_encrypted else 'No'}")

        if value:
            show_value = input("Show value? (y/n): ").strip().lower() == "y"
            if show_value:
                print(f"Value: {value}")
        else:
            print("Value: Not set")

        input("\\nPress Enter to continue...")

    def interactive_validate_config(self):
        """Interactive configuration validation"""
        api_key = input("Enter API key identifier (or 'all' for all): ").strip()

        if api_key == "all":
            print("\\n🔍 Validating all configurations...")
            for key in self.api_configs.keys():
                result = self.validate_api_key(key)
                status = "✅" if result["valid"] else "❌"
                print(f"{status} {key}: {'Valid' if result['valid'] else 'Invalid'}")

                if result["errors"]:
                    for error in result["errors"]:
                        print(f"    ❌ {error}")

                if result["warnings"]:
                    for warning in result["warnings"]:
                        print(f"    ⚠️  {warning}")
        else:
            if api_key not in self.api_configs:
                print(f"❌ API {api_key} not found")
            else:
                result = self.validate_api_key(api_key)
                print(f"\\n🔍 Validation Result for {api_key}:")
                print(f"Valid: {'Yes' if result['valid'] else 'No'}")

                if result["errors"]:
                    print("\\nErrors:")
                    for error in result["errors"]:
                        print(f"  ❌ {error}")

                if result["warnings"]:
                    print("\\nWarnings:")
                    for warning in result["warnings"]:
                        print(f"  ⚠️  {warning}")

        input("\\nPress Enter to continue...")

    def interactive_generate_env_file(self):
        """Interactive .env file generation"""
        print("\\nAvailable environments:")
        for name, env in self.environments.items():
            print(f"  {name}: {env.description}")

        environment = input("\\nEnter environment name: ").strip()

        if environment not in self.environments:
            print(f"❌ Environment {environment} not found")
            input("Press Enter to continue...")
            return

        try:
            env_content = self.generate_env_file(environment)
            filename = f".env.{environment}"

            print(f"\\n📄 Generated .env file for {environment}:")
            print("-" * 50)
            print(env_content[:500] + "..." if len(env_content) > 500 else env_content)
            print("-" * 50)

            save = input(f"\\nSave to {filename}? (y/n): ").strip().lower() == "y"
            if save:
                with open(filename, "w") as f:
                    f.write(env_content)
                print(f"✅ Saved to {filename}")

        except Exception as e:
            print(f"❌ Failed to generate .env file: {e}")

        input("\\nPress Enter to continue...")

    def interactive_deploy_environment(self):
        """Interactive environment deployment"""
        print("\\nAvailable environments:")
        for name, env in self.environments.items():
            print(f"  {name}: {env.description}")

        environment = input("\\nEnter environment name: ").strip()

        if environment not in self.environments:
            print(f"❌ Environment {environment} not found")
            input("Press Enter to continue...")
            return

        dry_run = input("Dry run? (y/n): ").strip().lower() == "y"

        try:
            result = self.deploy_to_environment(environment, dry_run)

            if result["success"]:
                print(f"\\n✅ Deployment {'simulated' if dry_run else 'completed'} successfully")
                print(f"Deployed APIs: {len(result['deployed_apis'])}")
                print(f"Skipped APIs: {len(result['skipped_apis'])}")
            else:
                print("\\n❌ Deployment failed")
                for error in result["errors"]:
                    print(f"  {error}")

        except Exception as e:
            print(f"❌ Deployment error: {e}")

        input("\\nPress Enter to continue...")

    def interactive_rotate_key(self):
        """Interactive API key rotation"""
        api_key = input("Enter API key identifier: ").strip()

        if api_key not in self.api_configs:
            print(f"❌ API {api_key} not found")
            input("Press Enter to continue...")
            return

        current_value = self.get_api_key(api_key)
        if current_value:
            print(f"Current value: {current_value[:10]}...")

        new_value = input("Enter new API key value: ").strip()

        try:
            self.rotate_api_key(api_key, new_value)
            print(f"✅ API key for {api_key} rotated successfully")
        except Exception as e:
            print(f"❌ Failed to rotate API key: {e}")

        input("\\nPress Enter to continue...")

    def show_status_report(self):
        """Show status report"""
        report = self.generate_status_report()

        print("\\n📊 Configuration Status Report")
        print("=" * 50)

        summary = report["summary"]
        print(f"Total APIs: {summary['total_apis']}")
        print(f"Configured APIs: {summary['configured_apis']}")
        print(f"Encrypted APIs: {summary['encrypted_apis']}")
        print(f"Configuration Rate: {summary['configuration_rate']:.1f}%")

        print("\\nPhase Breakdown:")
        for phase, stats in report["phase_breakdown"].items():
            print(f"  Phase {phase}: {stats['configured']}/{stats['total']} configured")

        print("\\nEnvironment Deployment:")
        for env, stats in report["environment_deployment"].items():
            print(f"  {env}: {stats['configured_apis']}/{stats['total_apis']} configured")

        input("\\nPress Enter to continue...")

    def interactive_export_configs(self):
        """Interactive configuration export"""
        include_secrets = input("Include secrets in export? (y/n): ").strip().lower() == "y"

        if include_secrets:
            confirm = input("⚠️  This will export sensitive data. Are you sure? (yes/no): ")
            if confirm.lower() != "yes":
                print("Export cancelled")
                input("Press Enter to continue...")
                return

        try:
            export_data = self.export_configurations(include_secrets)
            filename = f"api_configs_export_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2)

            print(f"✅ Configurations exported to {filename}")

        except Exception as e:
            print(f"❌ Export failed: {e}")

        input("\\nPress Enter to continue...")

    def interactive_import_configs(self):
        """Interactive configuration import"""
        filename = input("Enter import file path: ").strip()

        if not os.path.exists(filename):
            print(f"❌ File {filename} not found")
            input("Press Enter to continue...")
            return

        overwrite = input("Overwrite existing configurations? (y/n): ").strip().lower() == "y"

        try:
            with open(filename, "r") as f:
                import_data = json.load(f)

            self.import_configurations(import_data, overwrite)
            print("✅ Configurations imported successfully")

        except Exception as e:
            print(f"❌ Import failed: {e}")

        input("\\nPress Enter to continue...")

    def interactive_cleanup_backups(self):
        """Interactive backup cleanup"""
        retention_days = input("Enter retention days (default 30): ").strip()

        try:
            retention_days = int(retention_days) if retention_days else 30
            self.cleanup_backups(retention_days)
            print(f"✅ Backup cleanup completed (retention: {retention_days} days)")
        except ValueError:
            print("❌ Invalid retention days")
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")

        input("\\nPress Enter to continue...")


def main():
    """Main entry point"""
    try:
        manager = APIConfigManager()
        manager.interactive_menu()
    except KeyboardInterrupt:
        print("\\n👋 Configuration manager stopped")
    except Exception as e:
        logger.error(f"Configuration manager error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()