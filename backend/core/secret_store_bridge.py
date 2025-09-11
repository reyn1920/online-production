#!/usr / bin / env python3
"""
SecretStore Bridge - Enhanced version with CLI integration and env fallback
Provides secure credential management for TRAE.AI system
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class SecretStoreBridge:
    """Bridge to SecretStore CLI with environment variable fallback"""


    def __init__(self, cli_path: Optional[str] = None):
        self.cli_path = cli_path or self._find_cli()
        self.available = self._check_availability()


    def _find_cli(self) -> Optional[str]:
        """Find SecretStore CLI in common locations"""
        possible_paths = [
            "./scripts / secrets_cli.py",
                "/usr / local / bin / secrets_cli",
                "~/.local / bin / secrets_cli",
                "secrets_cli",
                ]

        for path in possible_paths:
            expanded_path = Path(path).expanduser()
            if expanded_path.exists() and expanded_path.is_file():
                return str(expanded_path)

        # Check if it's in PATH
        try:
            result = subprocess.run(
                ["which", "secrets_cli"], capture_output = True, text = True, timeout = 5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return None


    def _check_availability(self) -> bool:
        """Check if SecretStore CLI is available and working"""
        if not self.cli_path:
            logger.warning("SecretStore CLI not found, using env fallback only")
            return False

        try:
            result = subprocess.run(
                ["python3", self.cli_path, "--version"],
                    capture_output = True,
                    text = True,
                    timeout = 10,
                    )
            if result.returncode == 0:
                logger.info(f"SecretStore CLI available at {self.cli_path}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"SecretStore CLI check failed: {e}")

        return False


    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get secret from SecretStore CLI or environment variable"""
        # First try SecretStore CLI if available
        if self.available:
            try:
                result = subprocess.run(
                    ["python3", self.cli_path, "get", key],
                        capture_output = True,
                        text = True,
                        timeout = 30,
                        )
                if result.returncode == 0:
                    secret = result.stdout.strip()
                    if secret:
                        logger.debug(f"Retrieved secret '{key}' from SecretStore")
                        return secret
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.warning(f"SecretStore CLI failed for '{key}': {e}")

        # Fallback to environment variable
        env_value = os.getenv(key, default)
        if env_value:
            logger.debug(f"Retrieved secret '{key}' from environment")
            return env_value

        logger.warning(f"Secret '{key}' not found in SecretStore or environment")
        return default


    def set_secret(self, key: str, value: str) -> bool:
        """Set secret in SecretStore CLI"""
        if not self.available:
            logger.error("Cannot set secret: SecretStore CLI not available")
            return False

        try:
            result = subprocess.run(
                ["python3", self.cli_path, "set", key, value],
                    capture_output = True,
                    text = True,
                    timeout = 30,
                    )
            if result.returncode == 0:
                logger.info(f"Secret '{key}' set successfully")
                return True
            else:
                logger.error(f"Failed to set secret '{key}': {result.stderr}")
        except (subprocess.TimeoutExpired, OSError) as e:
            logger.error(f"SecretStore CLI failed to set '{key}': {e}")

        return False


    def list_secrets(self) -> Dict[str, Any]:
        """List available secrets (keys only for security)"""
        secrets_info = {
            "cli_available": self.available,
                "cli_path": self.cli_path,
                "keys": [],
                }

        if self.available:
            try:
                result = subprocess.run(
                    ["python3", self.cli_path, "list"],
                        capture_output = True,
                        text = True,
                        timeout = 30,
                        )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if output:
                        secrets_info["keys"] = output.split("\n")
            except (subprocess.TimeoutExpired, OSError) as e:
                logger.warning(f"Failed to list secrets: {e}")

        # Add environment variables that look like secrets
        env_secrets = [
            key
            for key in os.environ.keys()
            if any(
                pattern in key.upper()
                for pattern in ["API_KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL"]
            )
        ]
        secrets_info["env_keys"] = env_secrets

        return secrets_info


    def get_database_url(self) -> str:
        """Get database URL with fallback to SQLite"""
        db_url = self.get_secret("DATABASE_URL")
        if db_url:
            return db_url

        # Default to SQLite in data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok = True)
        return f"sqlite:///{data_dir}/trae_ai.db"


    def get_api_credentials(self) -> Dict[str, Optional[str]]:
        """Get common API credentials"""
        credentials = {
            "openai_api_key": self.get_secret("OPENAI_API_KEY"),
                "anthropic_api_key": self.get_secret("ANTHROPIC_API_KEY"),
                "youtube_api_key": self.get_secret("YOUTUBE_API_KEY"),
                "speechelo_email": self.get_secret("SPEECHELO_EMAIL", "test@example.com"),
                "speechelo_password": self.get_secret("SPEECHELO_PASSWORD"),
                "davinci_resolve_path": self.get_secret("DAVINCI_RESOLVE_PATH"),
                "blender_path": self.get_secret(
                "BLENDER_PATH", "/Applications / Blender.app / Contents / MacOS / Blender"
            ),
                }

        return credentials


    def validate_required_secrets(self) -> Dict[str, bool]:
        """Validate that required secrets are available"""
        required_secrets = ["OPENAI_API_KEY", "SPEECHELO_EMAIL", "YOUTUBE_API_KEY"]

        validation = {}
        for secret in required_secrets:
            value = self.get_secret(secret)
            validation[secret] = bool(value and len(value) > 0)

        return validation

# Global instance
_secret_store = None


def get_secret_store() -> SecretStoreBridge:
    """Get global SecretStore instance"""
    global _secret_store
    if _secret_store is None:
        _secret_store = SecretStoreBridge()
    return _secret_store


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """Convenience function to get a secret"""
    return get_secret_store().get_secret(key, default)


def get_database_url() -> str:
    """Convenience function to get database URL"""
    return get_secret_store().get_database_url()


def get_api_credentials() -> Dict[str, Optional[str]]:
    """Convenience function to get API credentials"""
    return get_secret_store().get_api_credentials()

if __name__ == "__main__":
    # Test the bridge
    bridge = SecretStoreBridge()
    print(f"CLI Available: {bridge.available}")
    print(f"CLI Path: {bridge.cli_path}")

    secrets_info = bridge.list_secrets()
    print(f"Available secrets: {json.dumps(secrets_info, indent = 2)}")

    validation = bridge.validate_required_secrets()
    print(f"Required secrets validation: {json.dumps(validation, indent = 2)}")
