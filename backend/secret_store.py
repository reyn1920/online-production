#!/usr/bin/env python3
"""
Secure Secret Store for TRAE.AI System

This module provides a production-ready secret storage system using AES encryption
with Fernet (symmetric encryption) from the cryptography library. Secrets are
stored in an encrypted SQLite database.

Security Features:
- AES encryption using Fernet (cryptographically secure)
- Key derivation using PBKDF2 with salt
- Secure random salt generation
- SQLite database with encrypted values
- Input validation and sanitization

Author: TRAE.AI System
Version: 1.0.0
"""

import base64
import hashlib
import logging
import os
import secrets
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SecretStoreError(Exception):
    """Custom exception for SecretStore operations"""

    pass


class SecretStore:
    """
    Production-ready secure secret storage system.

    This class provides encrypted storage of sensitive data using industry-standard
    cryptographic practices. All secrets are encrypted before storage and decrypted
    only when retrieved.

    Attributes:
        db_path (Path): Path to the SQLite database file
        master_key (bytes): Master encryption key derived from password
        fernet (Fernet): Encryption/decryption handler
    """

    def __init__(
        self,
        db_path: str = "data/secrets.sqlite",
        master_password: Optional[str] = None,
    ):
        """
        Initialize the SecretStore.

        Args:
            db_path (str): Path to the SQLite database file
            master_password (str, optional): Master password for encryption.
                                           If None, will use environment variable TRAE_MASTER_KEY

        Note:
            If no master password is provided, the SecretStore will operate in disabled mode
            where all operations return None/False gracefully instead of raising errors.
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Setup logging first
        self.logger = logging.getLogger(__name__)

        # Get master password from parameter or environment
        if master_password is None:
            master_password = os.getenv("TRAE_MASTER_KEY")

        if not master_password:
            # Degrade gracefully - enter disabled mode
            self.logger.warning(
                "No master password provided. SecretStore operating in disabled mode. "
                "Set TRAE_MASTER_KEY environment variable to enable secret storage."
            )
            self._disabled = True
            self.fernet = None
            return

        # Initialize encryption
        self._disabled = False
        self._setup_encryption(master_password)

        # Initialize database
        self._init_database()

    def _setup_encryption(self, master_password: str) -> None:
        """
        Setup encryption using PBKDF2 key derivation and Fernet encryption.

        Args:
            master_password (str): Master password for key derivation
        """
        # Get or create salt
        salt = self._get_or_create_salt()

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,  # OWASP recommended minimum
        )

        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self.fernet = Fernet(key)

    def _get_or_create_salt(self) -> bytes:
        """
        Get existing salt from database or create a new one.

        Returns:
            bytes: Cryptographic salt for key derivation
        """
        salt_file = self.db_path.parent / ".salt"

        if salt_file.exists():
            with open(salt_file, "rb") as f:
                return f.read()
        else:
            # Generate cryptographically secure random salt
            salt = secrets.token_bytes(32)
            with open(salt_file, "wb") as f:
                f.write(salt)
            # Set restrictive permissions (owner read/write only)
            os.chmod(salt_file, 0o600)
            return salt

    def _init_database(self) -> None:
        """
        Initialize the SQLite database with the secrets table.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS secrets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_name TEXT UNIQUE NOT NULL,
                    encrypted_value BLOB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create index for faster lookups
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_key_name ON secrets(key_name)
            """
            )

            conn.commit()

    def store_secret(self, key_name: str, secret_value: str) -> bool:
        """
        Store a secret with encryption.

        Args:
            key_name (str): Unique identifier for the secret
            secret_value (str): The secret value to encrypt and store

        Returns:
            bool: True if successful, False if disabled or failed

        Raises:
            SecretStoreError: If storage operation fails (only when not disabled)
        """
        # Return False gracefully if in disabled mode
        if getattr(self, "_disabled", False):
            self.logger.debug(f"SecretStore disabled - cannot store secret: {key_name}")
            return False

        try:
            # Validate inputs
            if not key_name or not isinstance(key_name, str):
                raise SecretStoreError("Key name must be a non-empty string")

            if not secret_value or not isinstance(secret_value, str):
                raise SecretStoreError("Secret value must be a non-empty string")

            # Encrypt the secret
            encrypted_value = self.fernet.encrypt(secret_value.encode())

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO secrets (key_name, encrypted_value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                    (key_name, encrypted_value),
                )
                conn.commit()

            self.logger.info(f"Secret stored successfully: {key_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to store secret {key_name}: {str(e)}")
            raise SecretStoreError(f"Failed to store secret: {str(e)}")

    def get_secret(self, key_name: str) -> Optional[str]:
        """
        Retrieve and decrypt a secret.

        Args:
            key_name (str): Unique identifier for the secret

        Returns:
            str: Decrypted secret value, or None if not found or in disabled mode

        Raises:
            SecretStoreError: If retrieval or decryption fails (only when not disabled)
        """
        # Return None gracefully if in disabled mode
        if getattr(self, "_disabled", False):
            self.logger.debug(
                f"SecretStore disabled - returning None for key: {key_name}"
            )
            return None

        try:
            if not key_name or not isinstance(key_name, str):
                raise SecretStoreError("Key name must be a non-empty string")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT encrypted_value FROM secrets WHERE key_name = ?",
                    (key_name,),
                )
                row = cursor.fetchone()

            if row is None:
                return None

            # Decrypt the secret
            encrypted_value = row[0]
            decrypted_value = self.fernet.decrypt(encrypted_value).decode()

            self.logger.info(f"Secret retrieved successfully: {key_name}")
            return decrypted_value

        except Exception as e:
            self.logger.error(f"Failed to retrieve secret {key_name}: {str(e)}")
            raise SecretStoreError(f"Failed to retrieve secret: {str(e)}")

    def delete_secret(self, key_name: str) -> bool:
        """
        Delete a secret from the store.

        Args:
            key_name (str): Unique identifier for the secret

        Returns:
            bool: True if deleted, False if not found or disabled

        Raises:
            SecretStoreError: If deletion fails (only when not disabled)
        """
        # Return False gracefully if in disabled mode
        if getattr(self, "_disabled", False):
            self.logger.debug(
                f"SecretStore disabled - cannot delete secret: {key_name}"
            )
            return False

        try:
            if not key_name or not isinstance(key_name, str):
                raise SecretStoreError("Key name must be a non-empty string")

            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM secrets WHERE key_name = ?", (key_name,)
                )
                conn.commit()

                deleted = cursor.rowcount > 0

            if deleted:
                self.logger.info(f"Secret deleted successfully: {key_name}")
            else:
                self.logger.warning(f"Secret not found for deletion: {key_name}")

            return deleted

        except Exception as e:
            self.logger.error(f"Failed to delete secret {key_name}: {str(e)}")
            raise SecretStoreError(f"Failed to delete secret: {str(e)}")

    def list_secrets(self) -> List[Dict[str, str]]:
        """
        List all stored secrets (metadata only, not values).

        Returns:
            List[Dict]: List of secret metadata (key_name, created_at, updated_at), empty list if disabled
        """
        # Return empty list gracefully if in disabled mode
        if getattr(self, "_disabled", False):
            self.logger.debug("SecretStore disabled - returning empty secrets list")
            return []

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    """
                    SELECT key_name, created_at, updated_at 
                    FROM secrets 
                    ORDER BY key_name
                """
                )

                secrets = [dict(row) for row in cursor.fetchall()]

            self.logger.info(f"Listed {len(secrets)} secrets")
            return secrets

        except Exception as e:
            self.logger.error(f"Failed to list secrets: {str(e)}")
            raise SecretStoreError(f"Failed to list secrets: {str(e)}")

    def secret_exists(self, key_name: str) -> bool:
        """
        Check if a secret exists in the store.

        Args:
            key_name (str): Unique identifier for the secret

        Returns:
            bool: True if secret exists, False otherwise or if disabled
        """
        # Return False gracefully if in disabled mode
        if getattr(self, "_disabled", False):
            self.logger.debug(
                f"SecretStore disabled - returning False for secret existence: {key_name}"
            )
            return False

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT 1 FROM secrets WHERE key_name = ? LIMIT 1", (key_name,)
                )
                return cursor.fetchone() is not None

        except Exception as e:
            self.logger.error(f"Failed to check secret existence {key_name}: {str(e)}")
            return False

    def backup_secrets(self, backup_path: str) -> bool:
        """
        Create a backup of the secrets database.

        Args:
            backup_path (str): Path for the backup file

        Returns:
            bool: True if backup successful, False otherwise
        """
        try:
            import shutil

            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Copy salt file
            salt_file = self.db_path.parent / ".salt"
            if salt_file.exists():
                backup_salt = backup_path.parent / ".salt"
                shutil.copy2(salt_file, backup_salt)

            self.logger.info(f"Secrets backed up to: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to backup secrets: {str(e)}")
            return False

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        # Cleanup if needed
        pass


if __name__ == "__main__":
    # Example usage and testing
    import os
    import tempfile

    # Set up test environment
    os.environ["TRAE_MASTER_KEY"] = "test_master_password_123"

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_secrets.sqlite")

        # Test the SecretStore
        with SecretStore(db_path) as store:
            # Store some test secrets
            store.store_secret("api_key", "sk-1234567890abcdef")
            store.store_secret("database_url", "postgresql://user:pass@localhost/db")

            # Retrieve secrets
            api_key = store.get_secret("api_key")
            print(f"Retrieved API key: {api_key}")

            # List all secrets
            secrets = store.list_secrets()
            print(f"All secrets: {secrets}")

            # Check existence
            exists = store.secret_exists("api_key")
            print(f"API key exists: {exists}")

            # Delete a secret
            deleted = store.delete_secret("api_key")
            print(f"API key deleted: {deleted}")
