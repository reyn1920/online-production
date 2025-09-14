#!/usr/bin/env python3
"""
Enterprise Security Framework
Implements JWT authentication, RBAC authorization, input validation, and secrets management
Designed for scalable channel system (100+ channels) with full functionality preservation
"""

import jwt
import bcrypt
import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum
import re
import os
from cryptography.fernet import Fernet
from pydantic import BaseModel, validator
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles for RBAC system"""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    CHANNEL_MANAGER = "channel_manager"
    CONTENT_CREATOR = "content_creator"
    MARKETING_SPECIALIST = "marketing_specialist"
    ANALYST = "analyst"
    VIEWER = "viewer"
    API_USER = "api_user"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions for fine-grained access control"""

    # Channel Management
    CREATE_CHANNEL = "create_channel"
    DELETE_CHANNEL = "delete_channel"
    MODIFY_CHANNEL = "modify_channel"
    VIEW_CHANNEL = "view_channel"

    # Content Operations
    CREATE_CONTENT = "create_content"
    EDIT_CONTENT = "edit_content"
    DELETE_CONTENT = "delete_content"
    PUBLISH_CONTENT = "publish_content"

    # Marketing & Analytics
    VIEW_ANALYTICS = "view_analytics"
    EXPORT_DATA = "export_data"
    MANAGE_CAMPAIGNS = "manage_campaigns"

    # System Administration
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"
    API_ACCESS = "api_access"

    # AI & Automation
    AI_GENERATION = "ai_generation"
    AUTOMATION_CONFIG = "automation_config"

    # Revenue & Monetization
    VIEW_REVENUE = "view_revenue"
    MANAGE_MONETIZATION = "manage_monetization"


@dataclass
class SecurityConfig:
    """Security configuration settings"""

    jwt_secret_key: str = field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    encryption_key: bytes = field(default_factory=lambda: Fernet.generate_key())
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 15


class TokenPayload(BaseModel):
    """JWT token payload structure"""

    user_id: str
    username: str
    roles: List[str]
    permissions: List[str]
    channel_access: List[str] = []
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


class UserCredentials(BaseModel):
    """User authentication credentials"""

    username: str
    password: str

    @validator("username")
    def validate_username(cls, v):
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", v):
            raise ValueError("Username must be 3-20 characters, alphanumeric and underscore only")
        return v

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


class InputValidator:
    """Comprehensive input validation system"""

    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS and injection attacks"""
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")

        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\'\/\\]', "", input_str)

        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_channel_name(name: str) -> bool:
        """Validate channel name format"""
        pattern = r"^[a-zA-Z0-9_\-\s]{3,50}$"
        return bool(re.match(pattern, name))

    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format"""
        pattern = r"^[a-zA-Z0-9]{32,128}$"
        return bool(re.match(pattern, api_key))


class SecretsManager:
    """Advanced secrets management system"""

    def __init__(self, config: SecurityConfig):
        self.config = config
        self.cipher_suite = Fernet(config.encryption_key)
        self.secrets_cache = {}

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        return self.cipher_suite.encrypt(secret.encode()).decode()

    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value"""
        return self.cipher_suite.decrypt(encrypted_secret.encode()).decode()

    def store_secret(self, key: str, value: str) -> None:
        """Store an encrypted secret"""
        encrypted_value = self.encrypt_secret(value)
        # In production, this would be stored in a secure database or vault
        self.secrets_cache[key] = encrypted_value
        logger.info(f"Secret stored for key: {key}")

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve and decrypt a secret"""
        encrypted_value = self.secrets_cache.get(key)
        if encrypted_value:
            return self.decrypt_secret(encrypted_value)

        # Fallback to environment variables
        env_value = os.getenv(key)
        if env_value:
            return env_value

        return None

    def rotate_encryption_key(self) -> bytes:
        """Rotate the encryption key for enhanced security"""
        new_key = Fernet.generate_key()
        # Re-encrypt all secrets with new key
        old_cipher = self.cipher_suite
        new_cipher = Fernet(new_key)

        for key, encrypted_value in self.secrets_cache.items():
            decrypted = old_cipher.decrypt(encrypted_value.encode()).decode()
            self.secrets_cache[key] = new_cipher.encrypt(decrypted.encode()).decode()

        self.cipher_suite = new_cipher
        logger.info("Encryption key rotated successfully")
        return new_key


class RBACManager:
    """Role-Based Access Control Manager"""

    def __init__(self):
        self.role_permissions = self._initialize_role_permissions()
        self.user_roles = {}
        self.channel_permissions = {}

    def _initialize_role_permissions(self) -> Dict[UserRole, List[Permission]]:
        """Initialize default role-permission mappings"""
        return {
            UserRole.SUPER_ADMIN: list(Permission),  # All permissions
            UserRole.ADMIN: [
                Permission.CREATE_CHANNEL,
                Permission.MODIFY_CHANNEL,
                Permission.VIEW_CHANNEL,
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.PUBLISH_CONTENT,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.MANAGE_CAMPAIGNS,
                Permission.MANAGE_USERS,
                Permission.AI_GENERATION,
                Permission.VIEW_REVENUE,
            ],
            UserRole.CHANNEL_MANAGER: [
                Permission.CREATE_CHANNEL,
                Permission.MODIFY_CHANNEL,
                Permission.VIEW_CHANNEL,
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.PUBLISH_CONTENT,
                Permission.VIEW_ANALYTICS,
                Permission.AI_GENERATION,
            ],
            UserRole.CONTENT_CREATOR: [
                Permission.VIEW_CHANNEL,
                Permission.CREATE_CONTENT,
                Permission.EDIT_CONTENT,
                Permission.AI_GENERATION,
            ],
            UserRole.MARKETING_SPECIALIST: [
                Permission.VIEW_CHANNEL,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
                Permission.MANAGE_CAMPAIGNS,
            ],
            UserRole.ANALYST: [
                Permission.VIEW_CHANNEL,
                Permission.VIEW_ANALYTICS,
                Permission.EXPORT_DATA,
            ],
            UserRole.API_USER: [
                Permission.API_ACCESS,
                Permission.VIEW_CHANNEL,
                Permission.CREATE_CONTENT,
            ],
            UserRole.VIEWER: [Permission.VIEW_CHANNEL],
            UserRole.GUEST: [],
        }

    def assign_role(self, user_id: str, role: UserRole) -> None:
        """Assign a role to a user"""
        if user_id not in self.user_roles:
            self.user_roles[user_id] = []
        if role not in self.user_roles[user_id]:
            self.user_roles[user_id].append(role)
        logger.info(f"Role {role.value} assigned to user {user_id}")

    def revoke_role(self, user_id: str, role: UserRole) -> None:
        """Revoke a role from a user"""
        if user_id in self.user_roles and role in self.user_roles[user_id]:
            self.user_roles[user_id].remove(role)
            logger.info(f"Role {role.value} revoked from user {user_id}")

    def grant_channel_access(
        self, user_id: str, channel_id: str, permissions: List[Permission]
    ) -> None:
        """Grant specific permissions to a user for a channel"""
        if user_id not in self.channel_permissions:
            self.channel_permissions[user_id] = {}
        self.channel_permissions[user_id][channel_id] = permissions
        logger.info(f"Channel access granted to user {user_id} for channel {channel_id}")

    def check_permission(
        self, user_id: str, permission: Permission, channel_id: str = None
    ) -> bool:
        """Check if user has specific permission"""
        # Check role-based permissions
        user_roles = self.user_roles.get(user_id, [])
        for role in user_roles:
            if permission in self.role_permissions.get(role, []):
                return True

        # Check channel-specific permissions
        if channel_id and user_id in self.channel_permissions:
            channel_perms = self.channel_permissions[user_id].get(channel_id, [])
            if permission in channel_perms:
                return True

        return False

    def get_user_permissions(self, user_id: str) -> List[Permission]:
        """Get all permissions for a user"""
        permissions = set()

        # Add role-based permissions
        user_roles = self.user_roles.get(user_id, [])
        for role in user_roles:
            permissions.update(self.role_permissions.get(role, []))

        # Add channel-specific permissions
        if user_id in self.channel_permissions:
            for channel_perms in self.channel_permissions[user_id].values():
                permissions.update(channel_perms)

        return list(permissions)


class JWTManager:
    """JWT token management system"""

    def __init__(self, config: SecurityConfig, rbac_manager: RBACManager):
        self.config = config
        self.rbac_manager = rbac_manager
        self.revoked_tokens = set()  # In production, use Redis or database

    def create_access_token(
        self, user_id: str, username: str, channel_access: List[str] = None
    ) -> str:
        """Create JWT access token"""
        user_roles = self.rbac_manager.user_roles.get(user_id, [])
        user_permissions = self.rbac_manager.get_user_permissions(user_id)

        payload = {
            "user_id": user_id,
            "username": username,
            "roles": [role.value for role in user_roles],
            "permissions": [perm.value for perm in user_permissions],
            "channel_access": channel_access or [],
            "exp": datetime.utcnow() + timedelta(minutes=self.config.access_token_expire_minutes),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
        logger.info(f"Access token created for user {username}")
        return token

    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        payload = {
            "user_id": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=self.config.refresh_token_expire_days),
            "iat": datetime.utcnow(),
            "jti": secrets.token_urlsafe(16),
        }

        token = jwt.encode(payload, self.config.jwt_secret_key, algorithm=self.config.jwt_algorithm)
        return token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )

            # Check if token is revoked
            if payload.get("jti") in self.revoked_tokens:
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def revoke_token(self, token: str) -> None:
        """Revoke a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm],
            )
            jti = payload.get("jti")
            if jti:
                self.revoked_tokens.add(jti)
                logger.info(f"Token revoked: {jti}")
        except jwt.InvalidTokenError:
            logger.warning("Cannot revoke invalid token")


class AuthenticationManager:
    """Main authentication and authorization manager"""

    def __init__(self, config: SecurityConfig = None):
        self.config = config or SecurityConfig()
        self.rbac_manager = RBACManager()
        self.jwt_manager = JWTManager(self.config, self.rbac_manager)
        self.secrets_manager = SecretsManager(self.config)
        self.validator = InputValidator()
        self.login_attempts = {}  # In production, use Redis
        self.security = HTTPBearer()

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))

    def authenticate_user(self, credentials: UserCredentials) -> Optional[Dict[str, Any]]:
        """Authenticate user credentials"""
        username = self.validator.sanitize_string(credentials.username)

        # Check login attempts
        if self._is_account_locked(username):
            raise HTTPException(
                status_code=423,
                detail="Account temporarily locked due to too many failed attempts",
            )

        # In production, retrieve user from database
        # For demo, using mock user data
        mock_users = {
            "admin": {
                "user_id": "1",
                "username": "admin",
                "password_hash": self.hash_password("Admin123!"),
                "roles": [UserRole.SUPER_ADMIN],
            }
        }

        user = mock_users.get(username)
        if not user or not self.verify_password(credentials.password, user["password_hash"]):
            self._record_failed_attempt(username)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Reset login attempts on successful authentication
        self._reset_login_attempts(username)

        # Assign roles
        for role in user["roles"]:
            self.rbac_manager.assign_role(user["user_id"], role)

        return user

    def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts"""
        attempts_data = self.login_attempts.get(username, {})
        attempts = attempts_data.get("count", 0)
        last_attempt = attempts_data.get("last_attempt")

        if attempts >= self.config.max_login_attempts and last_attempt:
            lockout_end = last_attempt + timedelta(minutes=self.config.lockout_duration_minutes)
            return datetime.utcnow() < lockout_end

        return False

    def _record_failed_attempt(self, username: str) -> None:
        """Record failed login attempt"""
        if username not in self.login_attempts:
            self.login_attempts[username] = {"count": 0, "last_attempt": None}

        self.login_attempts[username]["count"] += 1
        self.login_attempts[username]["last_attempt"] = datetime.utcnow()

    def _reset_login_attempts(self, username: str) -> None:
        """Reset login attempts after successful authentication"""
        if username in self.login_attempts:
            del self.login_attempts[username]

    async def get_current_user(
        self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
    ) -> Dict[str, Any]:
        """FastAPI dependency to get current authenticated user"""
        token = credentials.credentials
        payload = self.jwt_manager.verify_token(token)

        if not payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        return payload

    def require_permission(self, permission: Permission, channel_id: str = None):
        """Decorator to require specific permission"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract user from request context
                request = kwargs.get("request") or (
                    args[0] if args and hasattr(args[0], "state") else None
                )
                if not request or not hasattr(request.state, "user"):
                    raise HTTPException(status_code=401, detail="Authentication required")

                user = request.state.user
                user_id = user.get("user_id")

                if not self.rbac_manager.check_permission(user_id, permission, channel_id):
                    raise HTTPException(status_code=403, detail="Insufficient permissions")

                return await func(*args, **kwargs)

            return wrapper

        return decorator


# Global authentication manager instance
auth_manager = AuthenticationManager()


# FastAPI middleware for authentication
async def auth_middleware(request: Request, call_next):
    """Authentication middleware for FastAPI"""
    # Skip authentication for public endpoints
    public_paths = [
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/login",
        "/register",
    ]
    if request.url.path in public_paths:
        response = await call_next(request)
        return response

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = auth_header.split(" ")[1]
    user = auth_manager.jwt_manager.verify_token(token)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Add user to request state
    request.state.user = user

    response = await call_next(request)
    return response


# Example usage and testing functions
def setup_demo_data():
    """Setup demo data for testing"""
    # Create demo users with different roles
    demo_users = [
        ("admin", UserRole.SUPER_ADMIN),
        ("channel_mgr", UserRole.CHANNEL_MANAGER),
        ("creator", UserRole.CONTENT_CREATOR),
        ("marketer", UserRole.MARKETING_SPECIALIST),
        ("analyst", UserRole.ANALYST),
    ]

    for username, role in demo_users:
        user_id = f"user_{username}"
        auth_manager.rbac_manager.assign_role(user_id, role)

    # Setup channel permissions for scalable system (100 channels)
    for i in range(1, 101):
        channel_id = f"channel_{i:03d}"
        # Grant channel manager access to specific channels
        if i <= 20:  # First 20 channels for demo
            auth_manager.rbac_manager.grant_channel_access(
                "user_channel_mgr",
                channel_id,
                [
                    Permission.CREATE_CONTENT,
                    Permission.EDIT_CONTENT,
                    Permission.PUBLISH_CONTENT,
                ],
            )

    logger.info("Demo data setup completed")


if __name__ == "__main__":
    # Initialize and test the security framework
    setup_demo_data()

    # Test authentication
    credentials = UserCredentials(username="admin", password="Admin123!")
    try:
        user = auth_manager.authenticate_user(credentials)
        token = auth_manager.jwt_manager.create_access_token(
            user["user_id"],
            user["username"],
            [f"channel_{i:03d}" for i in range(1, 5)],  # Access to first 4 channels
        )
        print(f"Authentication successful. Token: {token[:50]}...")

        # Test permission checking
        has_permission = auth_manager.rbac_manager.check_permission(
            user["user_id"], Permission.CREATE_CHANNEL
        )
        print(f"User has CREATE_CHANNEL permission: {has_permission}")

    except Exception as e:
        print(f"Authentication failed: {e}")
