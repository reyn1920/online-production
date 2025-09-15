#!/usr/bin/env python3
"""
TRAE.AI Secure Secret Store

Fully encrypted secret management system for sensitive information
"""""""""

System Constitution Adherence:
- 100% Live Code: All encryption and storage implementations are functional
- Zero - Cost Stack: Uses built - in Python cryptography libraries
- Additive Evolution: Enhances security without breaking existing functionality
- Secure Design: Military - grade encryption with multiple security layers



"""

import base64
import hashlib
import json
import logging
import os
import secrets
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Cryptography imports
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

    CRYPTO_AVAILABLE = True
except ImportError:
    # Set to False if imports fail
    CRYPTO_AVAILABLE = False
    print("Warning: cryptography library not available. Install with: pip install cryptography")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecretType(Enum):
    """Types of secrets that can be stored"""

    API_KEY = "api_key"
    DATABASE_URL = "database_url"
    OAUTH_TOKEN = "oauth_token"
    WEBHOOK_SECRET = "webhook_secret"
    ENCRYPTION_KEY = "encryption_key"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "private_key"
    PASSWORD = "password"
    SESSION_SECRET = "session_secret"
    JWT_SECRET = "jwt_secret"
    CUSTOM = "custom"


class AccessLevel(Enum):
    """Access levels for secrets"""

    PUBLIC = "public"  # Can be read by any component
    INTERNAL = "internal"  # Can be read by authenticated components
    RESTRICTED = "restricted"  # Requires special permissions
    CONFIDENTIAL = "confidential"  # Highest security level


class EncryptionMethod(Enum):
    """Encryption methods available"""

    FERNET = "fernet"  # Symmetric encryption (recommended)
    AES_GCM = "aes_gcm"  # AES with Galois/Counter Mode
    CHACHA20 = "chacha20"  # ChaCha20 - Poly1305


@dataclass
class SecretMetadata:
    """
Metadata for stored secrets


    secret_id: str
    name: str
    secret_type: SecretType
    access_level: AccessLevel
    encryption_method: EncryptionMethod
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]
    access_count: int
    last_accessed: Optional[datetime]
    tags: List[str]
    description: str
    rotation_interval: Optional[int]  # Days
   
""""""

    is_active: bool
   

    
   
"""
@dataclass
class SecretEntry:
    """
Complete secret entry with metadata and encrypted data


    metadata: SecretMetadata
    encrypted_value: bytes
    salt: bytes
    nonce: Optional[bytes] = None
   
""""""

    checksum: Optional[str] = None
   

    
   
"""
class SecretStore:
    """Secure secret storage with military - grade encryption"""

    def __init__(
        self,
        store_path: str = "data/secrets.db",
        master_key: Optional[str] = None,
        auto_backup: bool = True,
        backup_interval: int = 3600
    ):
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library required for SecretStore")

        self.store_path = store_path
        self.auto_backup = auto_backup
        self.backup_interval = backup_interval
        self._lock = threading.RLock()
        self._access_log: List[Dict[str, Any]] = []

        # Initialize storage directory
        Path(store_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize or load master key
        self.master_key = self._init_master_key(master_key)

        # Initialize database
        self._init_database()

        # Start background tasks
        if auto_backup:
            self._start_backup_thread()

        logger.info("SecretStore initialized with encrypted storage")

    def _init_master_key(self, provided_key: Optional[str] = None) -> bytes:
        """Initialize or load master encryption key"""
        key_file = Path(self.store_path).parent / ".master_key"

        if provided_key:
            # Use provided key
            key_bytes = provided_key.encode("utf - 8")
        elif key_file.exists():
            # Load existing key
            try:
                with open(key_file, "rb") as f:
                    key_bytes = base64.b64decode(f.read())
            except Exception as e:
                logger.error(f"Failed to load master key: {e}")
                raise
        else:
            # Generate new key
            key_bytes = secrets.token_bytes(32)  # 256 - bit key

            # Save key securely
            try:
                with open(key_file, "wb") as f:
                    f.write(base64.b64encode(key_bytes))
                os.chmod(key_file, 0o600)  # Read/write for owner only
                logger.info("Generated new master key")
            except Exception as e:
                logger.error(f"Failed to save master key: {e}")
                raise

        return key_bytes

    def _init_database(self):
        """
Initialize encrypted database

        with sqlite3.connect(self.store_path) as conn:
            conn.executescript(
               
""""""

                CREATE TABLE IF NOT EXISTS secrets (
                    secret_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL UNIQUE,
                        secret_type TEXT NOT NULL,
                        access_level TEXT NOT NULL,
                        encryption_method TEXT NOT NULL,
                        encrypted_value BLOB NOT NULL,
                        salt BLOB NOT NULL,
                        nonce BLOB,
                        checksum TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        access_count INTEGER DEFAULT 0,
                        last_accessed TIMESTAMP,
                        tags TEXT,
                        description TEXT,
                        rotation_interval INTEGER,
                        is_active BOOLEAN DEFAULT 1
               

                
               
"""
                );
               """"""
                
               """

                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        secret_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        client_info TEXT,
                        success BOOLEAN DEFAULT 1,
                        error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS key_rotation_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        secret_id TEXT NOT NULL,
                        old_checksum TEXT,
                        new_checksum TEXT,
                        rotation_reason TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_secrets_name ON secrets(name);
                CREATE INDEX IF NOT EXISTS idx_secrets_type ON secrets(secret_type);
                CREATE INDEX IF NOT EXISTS idx_secrets_access_level ON secrets(access_level);
                CREATE INDEX IF NOT EXISTS idx_access_log_secret_id ON access_log(secret_id);
                CREATE INDEX IF NOT EXISTS idx_access_log_timestamp ON access_log(timestamp);
           

            
           
""""""

            
           

            )
           
""""""

           

            
           
"""
    def _derive_key(self, salt: bytes, method: EncryptionMethod = EncryptionMethod.FERNET) -> bytes:
        """Derive encryption key from master key and salt"""
        if not CRYPTO_AVAILABLE:
            raise ImportError("Cryptography library required")
            
        if method == EncryptionMethod.FERNET:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
        else:
            # Use Scrypt for other methods (more secure but slower)
            kdf = Scrypt(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                n=2**14,
                r=8,
                p=1,
                backend=default_backend()
            )

        return kdf.derive(self.master_key)

    def _encrypt_value(
        self, value: str, method: EncryptionMethod = EncryptionMethod.FERNET
    ) -> Tuple[bytes, bytes, Optional[bytes]]:
        """
Encrypt a secret value

        salt = secrets.token_bytes(16)
       
""""""

        key = self._derive_key(salt, method)
       

        
       
""""""


        

       

        key = self._derive_key(salt, method)
       
""""""
        if method == EncryptionMethod.FERNET:
            fernet = Fernet(base64.urlsafe_b64encode(key))
            encrypted_value = fernet.encrypt(value.encode("utf - 8"))
            return encrypted_value, salt, None

        elif method == EncryptionMethod.AES_GCM:
            nonce = secrets.token_bytes(12)
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_value = encryptor.update(value.encode("utf - 8")) + encryptor.finalize()
            # Append authentication tag
            encrypted_value += encryptor.tag
            return encrypted_value, salt, nonce

        elif method == EncryptionMethod.CHACHA20:
            nonce = secrets.token_bytes(12)
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
            encryptor = cipher.encryptor()
            encrypted_value = encryptor.update(value.encode("utf - 8")) + encryptor.finalize()
            return encrypted_value, salt, nonce

        else:
            raise ValueError(f"Unsupported encryption method: {method}")

    def _decrypt_value(
        self,
        encrypted_value: bytes,
        salt: bytes,
        nonce: Optional[bytes],
        method: EncryptionMethod,
#     ) -> str:
        """
Decrypt a secret value

       
""""""

        key = self._derive_key(salt, method)
       

        
       
""""""


        

       

        key = self._derive_key(salt, method)
       
""""""
        if method == EncryptionMethod.FERNET:
            fernet = Fernet(base64.urlsafe_b64encode(key))
            decrypted_value = fernet.decrypt(encrypted_value)
            return decrypted_value.decode("utf - 8")

        elif method == EncryptionMethod.AES_GCM:
            if not nonce:
                raise ValueError("Nonce required for AES - GCM decryption")

            # Split encrypted data and authentication tag
            encrypted_data = encrypted_value[:-16]
            tag = encrypted_value[-16:]

            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_value = decryptor.update(encrypted_data) + decryptor.finalize()
            return decrypted_value.decode("utf - 8")

        elif method == EncryptionMethod.CHACHA20:
            if not nonce:
                raise ValueError("Nonce required for ChaCha20 decryption")

            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
            decryptor = cipher.decryptor()
            decrypted_value = decryptor.update(encrypted_value) + decryptor.finalize()
            return decrypted_value.decode("utf - 8")

        else:
            raise ValueError(f"Unsupported encryption method: {method}")

    def _calculate_checksum(self, value: str) -> str:
        """Calculate SHA - 256 checksum of value"""
        return hashlib.sha256(value.encode("utf - 8")).hexdigest()

    def _log_access(
        self,
        secret_id: str,
        action: str,
        success: bool = True,
        error_message: Optional[str] = None,
#     ):
        """Log secret access for audit trail"""
        try:
            with sqlite3.connect(self.store_path) as conn:
                conn.execute(
                    "INSERT INTO access_log (secret_id, action, timestamp, success, error_message) VALUES (?, ?, ?, ?, ?)",
                    (secret_id, action, datetime.now(), success, error_message),
                 )
        except Exception as e:
            logger.error(f"Failed to log access: {e}")

    @contextmanager
    def _database_transaction(self):
        """
Context manager for database transactions

        conn = sqlite3.connect(self.store_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
           
""""""

            conn.close()
           

            
           
""""""


            

           

            conn.close()
           
""""""
    def store_secret(
        self,
        name: str,
        value: str,
        secret_type: SecretType = SecretType.CUSTOM,
        access_level: AccessLevel = AccessLevel.INTERNAL,
        encryption_method: EncryptionMethod = EncryptionMethod.FERNET,
        expires_at: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        description: str = "",
        rotation_interval: Optional[int] = None,
#     ) -> str:
        """
Store a secret securely


        
"""

        with self._lock:

        """"""
            secret_id = secrets.token_urlsafe(16)
           """"""
        with self._lock:
        """"""
            try:
                # Encrypt the value
                encrypted_value, salt, nonce = self._encrypt_value(value, encryption_method)

                # Calculate checksum
                checksum = self._calculate_checksum(value)

                # Create metadata
                metadata = SecretMetadata(
                    secret_id=secret_id,
                    name=name,
                    secret_type=secret_type,
                    access_level=access_level,
                    encryption_method=encryption_method,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    expires_at=expires_at,
                    access_count=0,
                    last_accessed=None,
                    tags=tags or [],
                    description=description,
                    rotation_interval=rotation_interval,
                    is_active=True,
                 )

                # Store in database
                with self._database_transaction() as conn:
                    conn.execute(
                       """

                        
                       

                        INSERT INTO secrets (
                            secret_id, name, secret_type, access_level, encryption_method,
                                encrypted_value, salt, nonce, checksum, created_at, updated_at,
                                expires_at, tags, description, rotation_interval, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    
""","""

                        (
                            secret_id,
                            name,
                            secret_type.value,
                            access_level.value,
                            encryption_method.value,
                            encrypted_value,
                            salt,
                            nonce,
                            checksum,
                            metadata.created_at,
                            metadata.updated_at,
                            expires_at,
                            json.dumps(tags or []),
                            description,
                            rotation_interval,
                            True,
                         ),
                    

                     
                    
"""
                     )
                    """"""
                self._log_access(secret_id, "STORE", True)
                logger.info(f"Secret '{name}' stored successfully with ID: {secret_id}")
                    """

                     
                    

                     )
                    
""""""
                return secret_id

            except Exception as e:
                self._log_access(secret_id, "STORE", False, str(e))
                logger.error(f"Failed to store secret '{name}': {e}")
                raise

    def get_secret(
        self, name: str, access_level_required: AccessLevel = AccessLevel.INTERNAL
    ) -> Optional[str]:
        """
Retrieve a secret by name


        with self._lock:
            try:
                
"""
                with self._database_transaction() as conn:
                """
                    row = conn.execute(
                        "SELECT * FROM secrets WHERE name = ? AND is_active = 1",
                        (name,),
                    ).fetchone()
                """

                with self._database_transaction() as conn:
                

               
""""""
                    if not row:
                        self._log_access("unknown", "GET", False, f"Secret '{name}' not found")
                        return None

                    # Check access level
                    secret_access_level = AccessLevel(row["access_level"])
                    if secret_access_level.value > access_level_required.value:
                        self._log_access(
                            row["secret_id"], "GET", False, "Insufficient access level"
                         )
                        logger.warning(
                            f"Access denied for secret '{name}': insufficient access level"
                         )
                        return None

                    # Check expiration
                    if row["expires_at"]:
                        expires_at = datetime.fromisoformat(row["expires_at"])
                        if datetime.now() > expires_at:
                            self._log_access(row["secret_id"], "GET", False, "Secret expired")
                            logger.warning(f"Secret '{name}' has expired")
                            return None

                    # Decrypt value
                    encryption_method = EncryptionMethod(row["encryption_method"])
                    decrypted_value = self._decrypt_value(
                        row["encrypted_value"],
                        row["salt"],
                        row["nonce"],
                        encryption_method,
                     )

                    # Update access statistics
                    conn.execute(
                        "UPDATE secrets SET access_count = access_count + 1, last_accessed = ? WHERE secret_id = ?",
                        (datetime.now(), row["secret_id"]),
                     )

                    self._log_access(row["secret_id"], "GET", True)
                    return decrypted_value

            except Exception as e:
                self._log_access("unknown", "GET", False, str(e))
                logger.error(f"Failed to retrieve secret '{name}': {e}")
                return None

    def update_secret(self, name: str, new_value: str) -> bool:
        """
Update an existing secret


        with self._lock:
            try:
                with self._database_transaction() as conn:
                   
""""""

                    # Get existing secret
                   

                    
                   
"""
                    row = conn.execute(
                        "SELECT * FROM secrets WHERE name = ? AND is_active = 1",
                        (name,),
                    ).fetchone()
                   """

                    
                   

                    # Get existing secret
                   
""""""
                    if not row:
                        self._log_access("unknown", "UPDATE", False, f"Secret '{name}' not found")
                        return False

                    # Encrypt new value
                    encryption_method = EncryptionMethod(row["encryption_method"])
                    encrypted_value, salt, nonce = self._encrypt_value(new_value, encryption_method)

                    # Calculate new checksum
                    old_checksum = row["checksum"]
                    new_checksum = self._calculate_checksum(new_value)

                    # Update secret
                    conn.execute(
                        """"""

                        UPDATE secrets
                        SET encrypted_value = ?, salt = ?, nonce = ?, checksum = ?, updated_at = ?
                        WHERE secret_id = ?
                    
,
"""
                        (
                            encrypted_value,
                            salt,
                            nonce,
                            new_checksum,
                            datetime.now(),
                            row["secret_id"],
                         ),
                     )

                    # Log rotation
                    conn.execute(
                        "INSERT INTO key_rotation_log (secret_id, old_checksum, new_checksum, rotation_reason, timestamp) VALUES (?, ?, ?, ?, ?)",
                        (
                            row["secret_id"],
                            old_checksum,
                            new_checksum,
                            "Manual update",
                            datetime.now(),
                         ),
                     )

                    self._log_access(row["secret_id"], "UPDATE", True)
                    logger.info(f"Secret '{name}' updated successfully")

                    return True

            except Exception as e:
                self._log_access("unknown", "UPDATE", False, str(e))
                logger.error(f"Failed to update secret '{name}': {e}")
                return False

    def delete_secret(self, name: str) -> bool:
        """
Delete a secret (soft delete)


        with self._lock:
            try:
                
"""
                with self._database_transaction() as conn:
                """
                    result = conn.execute(
                        "UPDATE secrets SET is_active = 0, updated_at = ? WHERE name = ? AND is_active = 1",
                        (datetime.now(), name),
                     )
                """

                with self._database_transaction() as conn:
                

               
""""""
                    if result.rowcount == 0:
                        self._log_access("unknown", "DELETE", False, f"Secret '{name}' not found")
                        return False

                    self._log_access("unknown", "DELETE", True)
                    logger.info(f"Secret '{name}' deleted successfully")

                    return True

            except Exception as e:
                self._log_access("unknown", "DELETE", False, str(e))
                logger.error(f"Failed to delete secret '{name}': {e}")
                return False

    def list_secrets(
        self,
        secret_type: Optional[SecretType] = None,
        access_level: Optional[AccessLevel] = None,
    ) -> List[Dict[str, Any]]:
        """
List all secrets (metadata only)


        try:
            
"""
            with self._database_transaction() as conn:
            """
                query = "SELECT secret_id, name, secret_type, access_level, created_at, updated_at, expires_at, access_count, last_accessed, tags, description FROM secrets WHERE is_active = 1"
            """
            with self._database_transaction() as conn:
            """
                params = []

                if secret_type:
                    query += " AND secret_type = ?"
                    params.append(secret_type.value)

                if access_level:
                    query += " AND access_level = ?"
                    params.append(access_level.value)

                query += " ORDER BY name"

                rows = conn.execute(query, params).fetchall()

                secrets = []
                for row in rows:
                    secret_info = {
                        "secret_id": row["secret_id"],
                        "name": row["name"],
                        "secret_type": row["secret_type"],
                        "access_level": row["access_level"],
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                        "expires_at": row["expires_at"],
                        "access_count": row["access_count"],
                        "last_accessed": row["last_accessed"],
                        "tags": json.loads(row["tags"] or "[]"),
                        "description": row["description"],
                     }
                    secrets.append(secret_info)

                return secrets

        except Exception as e:
            logger.error(f"Failed to list secrets: {e}")
            return []

    def rotate_secret(self, name: str, new_value: Optional[str] = None) -> bool:
        """
Rotate a secret (generate new value if not provided)


        if not new_value:
            # Generate new secure value
            new_value = secrets.token_urlsafe(32)

        return self.update_secret(name, new_value)

    def get_access_log(
        self, secret_name: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        
"""Get access log entries"""


        try:
            

            with self._database_transaction() as conn:
            
""""""

            
           

                if secret_name:
                    # Get secret_id first
            
"""
            with self._database_transaction() as conn:
            """
                    row = conn.execute(
                        "SELECT secret_id FROM secrets WHERE name = ?", (secret_name,)
                    ).fetchone()

                    if not row:
                        return []

                    rows = conn.execute(
                        "SELECT * FROM access_log WHERE secret_id = ? ORDER BY timestamp DESC LIMIT ?",
                        (row["secret_id"], limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        "SELECT * FROM access_log ORDER BY timestamp DESC LIMIT ?",
                        (limit,),
                    ).fetchall()

                log_entries = []
                for row in rows:
                    log_entry = {
                        "id": row["id"],
                        "secret_id": row["secret_id"],
                        "action": row["action"],
                        "timestamp": row["timestamp"],
                        "success": bool(row["success"]),
                        "error_message": row["error_message"],
                     }
                    log_entries.append(log_entry)

                return log_entries

        except Exception as e:
            logger.error(f"Failed to get access log: {e}")
            return []

    def backup_secrets(self, backup_path: Optional[str] = None) -> bool:
        """Create encrypted backup of all secrets"""

        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backups/secrets_backup_{timestamp}.db"

        try:
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)

            # Copy database file

            import shutil

            shutil.copy2(self.store_path, backup_path)

            logger.info(f"Secrets backup created: {backup_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def _start_backup_thread(self):
        """Start automatic backup thread"""

        def backup_worker():
            while True:
                try:
                    time.sleep(self.backup_interval)
                    self.backup_secrets()
                except Exception as e:
                    logger.error(f"Backup thread error: {e}")

        backup_thread = threading.Thread(target=backup_worker, daemon=True)
        backup_thread.start()
        logger.info(f"Automatic backup started (interval: {self.backup_interval}s)")

    def get_statistics(self) -> Dict[str, Any]:
        """
Get secret store statistics


        try:
            with self._database_transaction() as conn:
               
""""""

                # Count secrets by type
               

                
               
"""
                type_counts = {}
               """

                
               

                # Count secrets by type
               
""""""
                rows = conn.execute(
                    "SELECT secret_type, COUNT(*) as count FROM secrets WHERE is_active = 1 GROUP BY secret_type"
                ).fetchall()

                for row in rows:
                    type_counts[row["secret_type"]] = row["count"]

                # Count secrets by access level
                access_counts = {}
                rows = conn.execute(
                    "SELECT access_level, COUNT(*) as count FROM secrets WHERE is_active = 1 GROUP BY access_level"
                ).fetchall()

                for row in rows:
                    access_counts[row["access_level"]] = row["count"]

                # Get total counts
                total_secrets = conn.execute(
                    "SELECT COUNT(*) as count FROM secrets WHERE is_active = 1"
                ).fetchone()["count"]

                total_access_events = conn.execute(
                    "SELECT COUNT(*) as count FROM access_log"
                ).fetchone()["count"]

                # Get recent activity
                recent_activity = conn.execute(
                    "SELECT COUNT(*) as count FROM access_log WHERE timestamp > datetime('now', '-24 hours')"
                ).fetchone()["count"]

                return {
                    "total_secrets": total_secrets,
                    "secrets_by_type": type_counts,
                    "secrets_by_access_level": access_counts,
                    "total_access_events": total_access_events,
                    "recent_activity_24h": recent_activity,
                    "store_path": self.store_path,
                    "auto_backup_enabled": self.auto_backup,
                    "backup_interval": self.backup_interval,
                 }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Convenience functions for common operations


def get_secret_store(store_path: str = "data/secrets.db") -> SecretStore:
    """
Get or create a secret store instance

    
"""
    return SecretStore(store_path)
    """"""
    """


    return SecretStore(store_path)

    

   
""""""
def store_api_key(name: str, api_key: str, description: str = "") -> str:
    """
Store an API key

    store = get_secret_store()
    return store.store_secret(
        name=name,
        value=api_key,
        secret_type=SecretType.API_KEY,
        access_level=AccessLevel.RESTRICTED,
        description=description,
    
""""""

     )
    

     
    
""""""


     

    

     )
    
""""""

def get_api_key(name: str) -> Optional[str]:
    
Get an API key
"""
    store = get_secret_store()
    """

    return store.get_secret(name, AccessLevel.RESTRICTED)
    

   
""""""

    


    return store.get_secret(name, AccessLevel.RESTRICTED)

    
""""""
    
   """
def store_database_url(name: str, url: str, description: str = "") -> str:
    """
Store a database URL

    store = get_secret_store()
    return store.store_secret(
        name=name,
        value=url,
        secret_type=SecretType.DATABASE_URL,
        access_level=AccessLevel.CONFIDENTIAL,
        description=description,
    
""""""

     )
    

     
    
""""""


     

    

     )
    
""""""

def get_database_url(name: str) -> Optional[str]:
    
Get a database URL
"""
    store = get_secret_store()
    """

    return store.get_secret(name, AccessLevel.CONFIDENTIAL)
    

   
""""""

    


    return store.get_secret(name, AccessLevel.CONFIDENTIAL)

    
""""""
    
   """
# Example usage and testing
if __name__ == "__main__":
    # Initialize secret store
    store = SecretStore("data/test_secrets.db")

    # Store some test secrets
    print("Storing test secrets...")

    # API keys
    openai_id = store.store_secret(
        name="openai_api_key",
        value="sk - test - key - 12345",
        secret_type=SecretType.API_KEY,
        access_level=AccessLevel.RESTRICTED,
        description="OpenAI API key for content generation",
     )

    youtube_id = store.store_secret(
        name="youtube_api_key",
        value="AIza - test - key - 67890",
        secret_type=SecretType.API_KEY,
        access_level=AccessLevel.RESTRICTED,
        description="YouTube API key for video uploads",
     )

    # Database URL
    db_id = store.store_secret(
        name="database_url",
        value="postgresql://user:pass@localhost:5432/trae_ai",
        secret_type=SecretType.DATABASE_URL,
        access_level=AccessLevel.CONFIDENTIAL,
        description="Main database connection string",
     )

    # JWT secret
    jwt_id = store.store_secret(
        name="jwt_secret",
        value=secrets.token_urlsafe(32),
        secret_type=SecretType.JWT_SECRET,
        access_level=AccessLevel.CONFIDENTIAL,
        description="JWT signing secret",
     )

    print(f"Stored secrets with IDs: {openai_id}, {youtube_id}, {db_id}, {jwt_id}")

    # Retrieve secrets
    print("\\nRetrieving secrets...")
    openai_key = store.get_secret("openai_api_key", AccessLevel.RESTRICTED)
    youtube_key = store.get_secret("youtube_api_key", AccessLevel.RESTRICTED)
    db_url = store.get_secret("database_url", AccessLevel.CONFIDENTIAL)

    print(f"OpenAI key: {openai_key[:10]}...")
    print(f"YouTube key: {youtube_key[:10]}...")
    print(f"Database URL: {db_url[:20]}...")

    # List all secrets
    print("\\nAll secrets:")
    secrets_list = store.list_secrets()
    for secret in secrets_list:
        print(f"- {secret['name']} ({secret['secret_type']}) - {secret['access_level']}")

    # Get statistics
    print("\\nSecret store statistics:")
    stats = store.get_statistics()
    for key, value in stats.items():
        print(f"- {key}: {value}")

    # Get access log
    print("\\nRecent access log:")
    log_entries = store.get_access_log(limit=10)
    for entry in log_entries:
        print(
            f"- {entry['timestamp']}: {entry['action']} - {'SUCCESS' if entry['success'] else 'FAILED'}"
         )

    print("\\nSecure secret store test completed successfully!")