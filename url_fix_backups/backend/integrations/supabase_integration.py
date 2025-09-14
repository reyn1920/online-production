#!/usr / bin / env python3
"""
TRAE.AI Supabase Integration

Provides comprehensive Supabase database integration for cloud - based
credential management, state persistence, and real - time data synchronization.

Features:
- Secure credential and secrets management
- Real - time data synchronization
- User authentication and authorization
- Workflow state persistence
- Analytics and metrics storage
- File storage and CDN integration
- Row - level security (RLS) policies

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore

try:

    from postgrest import APIError
        from storage3 import StorageException
    from supabase import Client, create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    # Fallback for when Supabase is not installed
    SUPABASE_AVAILABLE = False


    class Client:


        def __init__(self, *args, **kwargs):
            pass


    class APIError(Exception):
        pass


    class StorageException(Exception):
        pass


class TableName(Enum):
    """Supabase table names."""

    USERS = "users"
    CREDENTIALS = "credentials"
    WORKFLOWS = "workflows"
    EXECUTIONS = "executions"
    AGENTS = "agents"
    TASKS = "tasks"
    ANALYTICS = "analytics"
    FILES = "files"
    SETTINGS = "settings"
    AUDIT_LOG = "audit_log"


class CredentialType(Enum):
    """Types of credentials stored."""

    API_KEY = "api_key"
    OAUTH_TOKEN = "oauth_token"
    DATABASE_URL = "database_url"
    WEBHOOK_URL = "webhook_url"
    SSH_KEY = "ssh_key"
    CERTIFICATE = "certificate"
    PASSWORD = "password"
    SECRET = "secret"


class ExecutionStatus(Enum):
    """Execution status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass


class SupabaseConfig:
    """Supabase configuration."""

    url: str
    key: str
    service_role_key: Optional[str] = None
    jwt_secret: Optional[str] = None
    db_password: Optional[str] = None
    storage_bucket: str = "trae - ai - storage"

@dataclass


class UserProfile:
    """User profile data structure."""

    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    subscription_tier: str = "free"
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass


class SecureCredential:
    """Secure credential data structure."""

    id: str
    user_id: str
    name: str
    credential_type: CredentialType
    encrypted_value: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass


class WorkflowState:
    """Workflow state data structure."""

    id: str
    user_id: str
    name: str
    status: str
    config: Dict[str, Any]
    state_data: Dict[str, Any]
    created_at: datetime = None
    updated_at: datetime = None
    version: int = 1

@dataclass


class ExecutionRecord:
    """Execution record data structure."""

    id: str
    user_id: str
    workflow_id: str
    status: ExecutionStatus
    started_at: datetime
    finished_at: Optional[datetime] = None
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class SupabaseIntegration:
    """
    Comprehensive Supabase integration for TRAE.AI with secure
    credential management, real - time sync, and cloud persistence.
    """


    def __init__(self, secrets_db_path: str = "data / secrets.sqlite"):
        self.logger = setup_logger("supabase_integration")
        self.secret_store = SecretStore(secrets_db_path)

        # Check Supabase availability
        if not SUPABASE_AVAILABLE:
            self.logger.warning(
                "Supabase not installed. Install with: pip install supabase"
            )
            self.client = None
            return

        # Load configuration
        self.config = self._load_config()

        # Initialize Supabase client
        self.client = self._init_client()

        # Initialize encryption for credentials
        self.encryption_key = self._get_encryption_key()

        # Cache for frequently accessed data
        self.cache = {"users": {}, "credentials": {}, "workflows": {}, "executions": {}}

        # Real - time subscriptions
        self.subscriptions = {}

        self.logger.info("Supabase integration initialized successfully")


    def _load_config(self) -> SupabaseConfig:
        """Load Supabase configuration from secure storage."""
        try:
            with self.secret_store as store:
                config = SupabaseConfig(
                    url = store.get_secret("SUPABASE_URL") or os.getenv("SUPABASE_URL"),
                        key = store.get_secret("SUPABASE_ANON_KEY")
                    or os.getenv("SUPABASE_ANON_KEY"),
                        service_role_key = store.get_secret("SUPABASE_SERVICE_ROLE_KEY")
                    or os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
                        jwt_secret = store.get_secret("SUPABASE_JWT_SECRET")
                    or os.getenv("SUPABASE_JWT_SECRET"),
                        db_password = store.get_secret("SUPABASE_DB_PASSWORD")
                    or os.getenv("SUPABASE_DB_PASSWORD"),
                        storage_bucket = store.get_secret("SUPABASE_STORAGE_BUCKET")
                    or "trae - ai - storage",
                        )

                if not config.url or not config.key:
                    self.logger.error("Missing required Supabase configuration")
                    raise ValueError("Supabase URL and key are required")

                return config

        except Exception as e:
            self.logger.error(f"Failed to load Supabase configuration: {e}")
            raise


    def _init_client(self) -> Optional[Client]:
        """Initialize Supabase client."""
        try:
            if not SUPABASE_AVAILABLE:
                return None

            client = create_client(self.config.url, self.config.key)

            # Test connection
            response = client.table("users").select("id").limit(1).execute()

            self.logger.info("Supabase client initialized and connected")
            return client

        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase client: {e}")
            return None


    def _get_encryption_key(self) -> bytes:
        """Get or generate encryption key for credentials."""
        try:
            with self.secret_store as store:
                key = store.get_secret("CREDENTIAL_ENCRYPTION_KEY")
                if not key:
                    # Generate new key
                    key = base64.b64encode(os.urandom(32)).decode("utf - 8")
                    store.set_secret("CREDENTIAL_ENCRYPTION_KEY", key)

                return base64.b64decode(key.encode("utf - 8"))

        except Exception as e:
            self.logger.error(f"Failed to get encryption key: {e}")
            # Fallback to a default key (not recommended for production)
            return hashlib.sha256(b"trae - ai - default - key").digest()


    def _encrypt_credential(self, value: str) -> str:
        """Encrypt credential value."""
        try:

            from cryptography.fernet import Fernet

            # Use first 32 bytes for Fernet key
            fernet_key = base64.urlsafe_b64encode(self.encryption_key)
            cipher = Fernet(fernet_key)

            encrypted = cipher.encrypt(value.encode("utf - 8"))
            return base64.b64encode(encrypted).decode("utf - 8")

        except ImportError:
            self.logger.warning("cryptography not installed, using base64 encoding")
            return base64.b64encode(value.encode("utf - 8")).decode("utf - 8")
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            return base64.b64encode(value.encode("utf - 8")).decode("utf - 8")


    def _decrypt_credential(self, encrypted_value: str) -> str:
        """Decrypt credential value."""
        try:

            from cryptography.fernet import Fernet

            fernet_key = base64.urlsafe_b64encode(self.encryption_key)
            cipher = Fernet(fernet_key)

            encrypted_bytes = base64.b64decode(encrypted_value.encode("utf - 8"))
            decrypted = cipher.decrypt(encrypted_bytes)
            return decrypted.decode("utf - 8")

        except ImportError:
            self.logger.warning("cryptography not installed, using base64 decoding")
            return base64.b64decode(encrypted_value.encode("utf - 8")).decode("utf - 8")
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            return base64.b64decode(encrypted_value.encode("utf - 8")).decode("utf - 8")


    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase connection health."""
        if not self.client:
            return {
                "status": "unavailable",
                    "error": "Supabase client not initialized",
                    "timestamp": datetime.now().isoformat(),
                    }

        try:
            start_time = time.time()

            # Test database connection
            response = self.client.table("users").select("id").limit(1).execute()

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                    "url": self.config.url,
                    "response_time": response_time,
                    "timestamp": datetime.now().isoformat(),
                    "tables_accessible": True,
                    }

        except Exception as e:
            return {
                "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    }


    async def create_user_profile(
        self, user_data: Dict[str, Any]
    ) -> Optional[UserProfile]:
        """Create a new user profile."""
        if not self.client:
            self.logger.error("Supabase client not available")
            return None

        try:
            profile_data = {
                "id": user_data.get("id", str(uuid.uuid4())),
                    "email": user_data["email"],
                    "full_name": user_data.get("full_name"),
                    "avatar_url": user_data.get("avatar_url"),
                    "subscription_tier": user_data.get("subscription_tier", "free"),
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "metadata": user_data.get("metadata", {}),
                    }

            response = (
                self.client.table(TableName.USERS.value).insert(profile_data).execute()
            )

            if response.data:
                profile = UserProfile(**response.data[0])
                self.cache["users"][profile.id] = profile

                self.logger.info(f"Created user profile: {profile.email}")
                return profile

            return None

        except Exception as e:
            self.logger.error(f"Error creating user profile: {e}")
            return None


    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID."""
        if not self.client:
            return None

        # Check cache first
        if user_id in self.cache["users"]:
            return self.cache["users"][user_id]

        try:
            response = (
                self.client.table(TableName.USERS.value)
                .select("*")
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                profile = UserProfile(**response.data[0])
                self.cache["users"][user_id] = profile
                return profile

            return None

        except Exception as e:
            self.logger.error(f"Error getting user profile {user_id}: {e}")
            return None


    async def store_credential(
        self,
            user_id: str,
            name: str,
            value: str,
            credential_type: CredentialType,
            description: Optional[str] = None,
            expires_at: Optional[datetime] = None,
            ) -> Optional[SecureCredential]:
        """Store encrypted credential."""
        if not self.client:
            return None

        try:
            encrypted_value = self._encrypt_credential(value)

            credential_data = {
                "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "name": name,
                    "credential_type": credential_type.value,
                    "encrypted_value": encrypted_value,
                    "description": description,
                    "expires_at": expires_at.isoformat() if expires_at else None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    }

            response = (
                self.client.table(TableName.CREDENTIALS.value)
                .insert(credential_data)
                .execute()
            )

            if response.data:
                credential = SecureCredential(**response.data[0])

                # Cache without the encrypted value for security
                cache_credential = SecureCredential(**response.data[0])
                cache_credential.encrypted_value = "[ENCRYPTED]"
                self.cache["credentials"][credential.id] = cache_credential

                self.logger.info(f"Stored credential: {name} for user {user_id}")
                return credential

            return None

        except Exception as e:
            self.logger.error(f"Error storing credential: {e}")
            return None


    async def get_credential(self, user_id: str, credential_id: str) -> Optional[str]:
        """Get decrypted credential value."""
        if not self.client:
            return None

        try:
            response = (
                self.client.table(TableName.CREDENTIALS.value)
                .select("*")
                .eq("id", credential_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                credential_data = response.data[0]

                # Check if expired
                if credential_data.get("expires_at"):
                    expires_at = datetime.fromisoformat(credential_data["expires_at"])
                    if expires_at < datetime.now():
                        self.logger.warning(f"Credential {credential_id} has expired")
                        return None

                decrypted_value = self._decrypt_credential(
                    credential_data["encrypted_value"]
                )
                return decrypted_value

            return None

        except Exception as e:
            self.logger.error(f"Error getting credential {credential_id}: {e}")
            return None


    async def list_user_credentials(self, user_id: str) -> List[SecureCredential]:
        """List all credentials for a user (without values)."""
        if not self.client:
            return []

        try:
            response = (
                self.client.table(TableName.CREDENTIALS.value)
                .select(
                    "id, user_id, name, credential_type, description, expires_at, created_at, updated_at"
                )
                .eq("user_id", user_id)
                .execute()
            )

            credentials = []
            for cred_data in response.data:
                credential = SecureCredential(
                    **cred_data, encrypted_value="[ENCRYPTED]"
                )
                credentials.append(credential)

            return credentials

        except Exception as e:
            self.logger.error(f"Error listing credentials for user {user_id}: {e}")
            return []


    async def store_workflow_state(self, workflow_state: WorkflowState) -> bool:
        """Store workflow state."""
        if not self.client:
            return False

        try:
            state_data = {
                "id": workflow_state.id,
                    "user_id": workflow_state.user_id,
                    "name": workflow_state.name,
                    "status": workflow_state.status,
                    "config": workflow_state.config,
                    "state_data": workflow_state.state_data,
                    "created_at": (
                    workflow_state.created_at.isoformat()
                    if workflow_state.created_at
                    else datetime.now().isoformat()
                ),
                    "updated_at": datetime.now().isoformat(),
                    "version": workflow_state.version,
                    }

            response = (
                self.client.table(TableName.WORKFLOWS.value)
                .upsert(state_data)
                .execute()
            )

            if response.data:
                self.cache["workflows"][workflow_state.id] = workflow_state
                self.logger.info(f"Stored workflow state: {workflow_state.name}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error storing workflow state: {e}")
            return False


    async def get_workflow_state(
        self, user_id: str, workflow_id: str
    ) -> Optional[WorkflowState]:
        """Get workflow state."""
        if not self.client:
            return None

        # Check cache first
        if workflow_id in self.cache["workflows"]:
            return self.cache["workflows"][workflow_id]

        try:
            response = (
                self.client.table(TableName.WORKFLOWS.value)
                .select("*")
                .eq("id", workflow_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                workflow_data = response.data[0]
                workflow_state = WorkflowState(
                    id = workflow_data["id"],
                        user_id = workflow_data["user_id"],
                        name = workflow_data["name"],
                        status = workflow_data["status"],
                        config = workflow_data["config"],
                        state_data = workflow_data["state_data"],
                        created_at = datetime.fromisoformat(workflow_data["created_at"]),
                        updated_at = datetime.fromisoformat(workflow_data["updated_at"]),
                        version = workflow_data["version"],
                        )

                self.cache["workflows"][workflow_id] = workflow_state
                return workflow_state

            return None

        except Exception as e:
            self.logger.error(f"Error getting workflow state {workflow_id}: {e}")
            return None


    async def store_execution_record(self, execution: ExecutionRecord) -> bool:
        """Store execution record."""
        if not self.client:
            return False

        try:
            execution_data = {
                "id": execution.id,
                    "user_id": execution.user_id,
                    "workflow_id": execution.workflow_id,
                    "status": execution.status.value,
                    "started_at": execution.started_at.isoformat(),
                    "finished_at": (
                    execution.finished_at.isoformat() if execution.finished_at else None
                ),
                    "results": execution.results,
                    "error_message": execution.error_message,
                    "metrics": execution.metrics,
                    }

            response = (
                self.client.table(TableName.EXECUTIONS.value)
                .upsert(execution_data)
                .execute()
            )

            if response.data:
                self.cache["executions"][execution.id] = execution
                self.logger.info(f"Stored execution record: {execution.id}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error storing execution record: {e}")
            return False


    async def get_execution_record(
        self, user_id: str, execution_id: str
    ) -> Optional[ExecutionRecord]:
        """Get execution record."""
        if not self.client:
            return None

        # Check cache first
        if execution_id in self.cache["executions"]:
            return self.cache["executions"][execution_id]

        try:
            response = (
                self.client.table(TableName.EXECUTIONS.value)
                .select("*")
                .eq("id", execution_id)
                .eq("user_id", user_id)
                .execute()
            )

            if response.data:
                exec_data = response.data[0]
                execution = ExecutionRecord(
                    id = exec_data["id"],
                        user_id = exec_data["user_id"],
                        workflow_id = exec_data["workflow_id"],
                        status = ExecutionStatus(exec_data["status"]),
                        started_at = datetime.fromisoformat(exec_data["started_at"]),
                        finished_at=(
                        datetime.fromisoformat(exec_data["finished_at"])
                        if exec_data["finished_at"]
                        else None
                    ),
                        results = exec_data["results"],
                        error_message = exec_data["error_message"],
                        metrics = exec_data["metrics"],
                        )

                self.cache["executions"][execution_id] = execution
                return execution

            return None

        except Exception as e:
            self.logger.error(f"Error getting execution record {execution_id}: {e}")
            return None


    async def upload_file(
        self,
            user_id: str,
            file_path: str,
            file_data: bytes,
            content_type: str = "application / octet - stream",
            ) -> Optional[str]:
        """Upload file to Supabase storage."""
        if not self.client:
            return None

        try:
            # Create user - specific path
            storage_path = f"{user_id}/{file_path}"

            # Upload file
            response = self.client.storage.from_(self.config.storage_bucket).upload(
                path = storage_path,
                    file = file_data,
                    file_options={"content - type": content_type},
                    )

            if response:
                # Get public URL
                public_url = self.client.storage.from_(
                    self.config.storage_bucket
                ).get_public_url(storage_path)

                self.logger.info(f"Uploaded file: {storage_path}")
                return public_url

            return None

        except Exception as e:
            self.logger.error(f"Error uploading file {file_path}: {e}")
            return None


    async def delete_file(self, user_id: str, file_path: str) -> bool:
        """Delete file from Supabase storage."""
        if not self.client:
            return False

        try:
            storage_path = f"{user_id}/{file_path}"

            response = self.client.storage.from_(self.config.storage_bucket).remove(
                [storage_path]
            )

            if response:
                self.logger.info(f"Deleted file: {storage_path}")
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error deleting file {file_path}: {e}")
            return False


    async def subscribe_to_changes(
        self, table: str, callback: callable, filter_conditions: Optional[Dict] = None
    ):
        """Subscribe to real - time changes in a table."""
        if not self.client:
            return None

        try:
            subscription = self.client.table(table).on("*", callback)

            if filter_conditions:
                for key, value in filter_conditions.items():
                    subscription = subscription.eq(key, value)

            subscription.subscribe()

            subscription_id = f"{table}_{uuid.uuid4()}"
            self.subscriptions[subscription_id] = subscription

            self.logger.info(f"Subscribed to changes in table: {table}")
            return subscription_id

        except Exception as e:
            self.logger.error(f"Error subscribing to table {table}: {e}")
            return None


    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from real - time changes."""
        if subscription_id in self.subscriptions:
            try:
                self.subscriptions[subscription_id].unsubscribe()
                del self.subscriptions[subscription_id]
                self.logger.info(f"Unsubscribed: {subscription_id}")
            except Exception as e:
                self.logger.error(f"Error unsubscribing {subscription_id}: {e}")


    async def cleanup(self):
        """Cleanup resources and close connections."""
        # Unsubscribe from all real - time subscriptions
        for subscription_id in list(self.subscriptions.keys()):
            await self.unsubscribe(subscription_id)

        # Clear caches
        self.cache.clear()

        self.logger.info("Supabase integration cleaned up")

# Example usage and testing
if __name__ == "__main__":


    async def test_supabase_integration():
        supabase = SupabaseIntegration()

        # Health check
        health = await supabase.health_check()
        print(f"Supabase Health: {health}")

        if health["status"] == "healthy":
            # Test user profile creation
            user_data = {
                "email": "test@example.com",
                    "full_name": "Test User",
                    "subscription_tier": "pro",
                    }

            profile = await supabase.create_user_profile(user_data)
            if profile:
                print(f"Created user profile: {profile.email}")

                # Test credential storage
                credential = await supabase.store_credential(
                    user_id = profile.id,
                        name="OpenAI API Key",
                        value="sk - test - key - 12345",
                        credential_type = CredentialType.API_KEY,
                        description="OpenAI API key for GPT - 4",
                        )

                if credential:
                    print(f"Stored credential: {credential.name}")

                    # Test credential retrieval
                    decrypted_value = await supabase.get_credential(
                        profile.id, credential.id
                    )
                    print(f"Retrieved credential value: {decrypted_value}")

    # Run test
    asyncio.run(test_supabase_integration())