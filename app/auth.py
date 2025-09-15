#!/usr/bin/env python3
"""
Authentication and Authorization Module
Provides user authentication, role-based access control, and security features.
"""

import hashlib
import logging
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any

from fastapi import HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()

# Permission system
class Permission(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"
    MANAGE_CONTENT = "manage_content"
    FINANCIAL_ACCESS = "financial_access"

class Role(str, Enum):
    GUEST = "guest"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

# Role-based permissions mapping
ROLE_PERMISSIONS = {
    Role.GUEST: [Permission.READ],
    Role.USER: [Permission.READ, Permission.WRITE],
    Role.MODERATOR: [
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.MANAGE_CONTENT, Permission.VIEW_ANALYTICS
    ],
    Role.ADMIN: [
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.MANAGE_USERS, Permission.VIEW_ANALYTICS,
        Permission.MANAGE_CONTENT, Permission.FINANCIAL_ACCESS
    ],
    Role.SUPER_ADMIN: list(Permission)
}

# Pydantic models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: Role = Role.USER

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: Role
    is_active: bool
    created_at: str
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: UserResponse

@dataclass
class User:
    id: str
    username: str
    email: str
    password_hash: str
    role: Role
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash"""
        return self.password_hash == self._hash_password(password)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def get_permissions(self) -> List[Permission]:
        """Get all permissions for user's role"""
        return ROLE_PERMISSIONS.get(self.role, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password hash)"""
        data = asdict(self)
        data.pop("password_hash", None)
        # Convert datetime objects to ISO strings
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("last_login"), datetime):
            data["last_login"] = data["last_login"].isoformat()
        return data

# In-memory user storage (replace with database in production)
users_db: Dict[str, User] = {}
tokens_db: Dict[str, Dict[str, Any]] = {}

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.secret_key = secrets.token_urlsafe(32)
        self.token_expiry_hours = 24
        
        # Create default admin user
        self._create_default_admin()
    
    def _create_default_admin(self):
        """Create default admin user if none exists"""
        admin_exists = any(user.role == Role.ADMIN for user in users_db.values())
        if not admin_exists:
            admin_user = self.create_user(
                username="admin",
                email="admin@example.com",
                password="admin123",
                role=Role.ADMIN
            )
            logger.info(f"Created default admin user: {admin_user.username}")
    
    def create_user(self, username: str, email: str, password: str, role: Role = Role.USER) -> User:
        """Create a new user"""
        # Check if user already exists
        if any(u.username == username or u.email == email for u in users_db.values()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists"
            )
        
        # Generate user ID
        user_id = secrets.token_urlsafe(16)
        
        # Create user
        user = User(
            id=user_id,
            username=username,
            email=email,
            password_hash=User._hash_password(password),
            role=role
        )
        
        # Store user
        users_db[user_id] = user
        logger.info(f"Created user: {username} with role: {role}")
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = next((u for u in users_db.values() if u.username == username), None)
        
        if user and user.is_active and user.verify_password(password):
            user.last_login = datetime.now()
            logger.info(f"User authenticated: {username}")
            return user
        
        logger.warning(f"Authentication failed for user: {username}")
        return None
    
    def create_access_token(self, user: User) -> str:
        """Create access token for user"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=self.token_expiry_hours)
        
        tokens_db[token] = {
            "user_id": user.id,
            "expires_at": expires_at,
            "created_at": datetime.now()
        }
        
        logger.info(f"Created access token for user: {user.username}")
        return token
    
    def verify_token(self, token: str) -> Optional[User]:
        """Verify access token and return user"""
        token_data = tokens_db.get(token)
        
        if not token_data:
            return None
        
        # Check if token is expired
        if datetime.now() > token_data["expires_at"]:
            del tokens_db[token]
            return None
        
        # Get user
        user = users_db.get(token_data["user_id"])
        if user and user.is_active:
            return user
        
        return None
    
    def revoke_token(self, token: str) -> bool:
        """Revoke access token"""
        if token in tokens_db:
            del tokens_db[token]
            logger.info("Access token revoked")
            return True
        return False
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return users_db.get(user_id)
    
    def get_all_users(self) -> List[User]:
        """Get all users (admin only)"""
        return list(users_db.values())
    
    def update_user_role(self, user_id: str, new_role: Role) -> bool:
        """Update user role (admin only)"""
        user = users_db.get(user_id)
        if user:
            user.role = new_role
            logger.info(f"Updated user {user.username} role to {new_role}")
            return True
        return False
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user (admin only)"""
        user = users_db.get(user_id)
        if user:
            user.is_active = False
            logger.info(f"Deactivated user: {user.username}")
            return True
        return False
    
    def cleanup_expired_tokens(self):
        """Remove expired tokens from storage"""
        current_time = datetime.now()
        expired_tokens = [
            token for token, data in tokens_db.items()
            if current_time > data["expires_at"]
        ]
        
        for token in expired_tokens:
            del tokens_db[token]
        
        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")

# Global auth manager instance
auth_manager = AuthManager()

# Dependency functions for FastAPI
def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = None) -> User:
    """Get current authenticated user"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = auth_manager.verify_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user

def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(user: Optional[User] = None):
        if not user or not user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return user
    return decorator

def require_role(required_role: Role):
    """Decorator to require specific role"""
    def decorator(user: Optional[User] = None):
        if not user or user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {required_role}"
            )
        return user
    return decorator

# Utility functions
def hash_password(password: str) -> str:
    """Hash password utility function"""
    return User._hash_password(password)

def generate_secure_token() -> str:
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def validate_password_strength(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    return has_upper and has_lower and has_digit

# Export main components
__all__ = [
    "User", "Role", "Permission", "AuthManager",
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "auth_manager", "get_current_user", "require_permission", "require_role",
    "hash_password", "generate_secure_token", "validate_password_strength"
]