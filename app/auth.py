# auth.py - User Authentication and Authorization Module
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import secrets
import hashlib
import os
from enum import Enum

# Configuration - Use environment variables for security
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
JWT_SECRET = os.getenv("JWT_SECRET", secrets.token_urlsafe(64))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Security settings
PASSWORD_MIN_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class UserRole(str, Enum):
    """User roles for role-based access control"""
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions"""
    READ_DASHBOARD = "read:dashboard"
    WRITE_DASHBOARD = "write:dashboard"
    READ_ANALYTICS = "read:analytics"
    EXPORT_DATA = "export:data"
    MANAGE_USERS = "manage:users"
    SYSTEM_ADMIN = "system:admin"
    RESTART_SERVICES = "restart:services"
    VIEW_LOGS = "view:logs"


# Role-Permission mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_DASHBOARD,
        Permission.WRITE_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.MANAGE_USERS,
        Permission.SYSTEM_ADMIN,
        Permission.RESTART_SERVICES,
        Permission.VIEW_LOGS
    ],
    UserRole.MANAGER: [
        Permission.READ_DASHBOARD,
        Permission.WRITE_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.VIEW_LOGS
    ],
    UserRole.ANALYST: [
        Permission.READ_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_DATA
    ],
    UserRole.VIEWER: [
        Permission.READ_DASHBOARD
    ]
}


@dataclass
class User:
    """User model"""
    id: str
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool = True
    created_at: datetime = None
    last_login: datetime = None
    password_hash: str = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def get_permissions(self) -> List[Permission]:
        """Get all permissions for user's role"""
        return ROLE_PERMISSIONS.get(self.role, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password hash)"""
        data = asdict(self)
        data.pop('password_hash', None)
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['last_login'] = self.last_login.isoformat() if self.last_login else None
        data['permissions'] = [p.value for p in self.get_permissions()]
        return data


@dataclass
class TokenData:
    """Token payload data"""
    user_id: str
    username: str
    role: UserRole
    permissions: List[str]
    exp: datetime
    iat: datetime


class AuthManager:
    """Authentication and authorization manager"""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}

        # Create default admin user
        self._create_default_users()

    def _create_default_users(self):
        """Create default users for demonstration"""
        default_users = [
            {
                "id": "admin_001",
                "username": "admin",
                "email": "admin@dashboard.com",
                "full_name": "System Administrator",
                "role": UserRole.ADMIN,
                "password": "admin123"  # In production, use secure password
            },
            {
                "id": "manager_001",
                "username": "manager",
                "email": "manager@dashboard.com",
                "full_name": "Dashboard Manager",
                "role": UserRole.MANAGER,
                "password": "manager123"
            },
            {
                "id": "analyst_001",
                "username": "analyst",
                "email": "analyst@dashboard.com",
                "full_name": "Data Analyst",
                "role": UserRole.ANALYST,
                "password": "analyst123"
            },
            {
                "id": "viewer_001",
                "username": "viewer",
                "email": "viewer@dashboard.com",
                "full_name": "Dashboard Viewer",
                "role": UserRole.VIEWER,
                "password": "viewer123"
            }
        ]

        for user_data in default_users:
            password = user_data.pop('password')
            user = User(**user_data)
            user.password_hash = self.hash_password(password)
            self.users[user.id] = user

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        if not user or not user.is_active:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now()
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        for user in self.users.values():
            if user.username == username:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(user_id)

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        payload = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.get_permissions()],
            "exp": expire,
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow()
        }

        return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])

            user_id = payload.get("sub")
            if user_id is None:
                return None

            # Check if it's a refresh token
            if payload.get("type") == "refresh":
                return None

            token_data = TokenData(
                user_id=user_id,
                username=payload.get("username"),
                role=UserRole(payload.get("role")),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat"))
            )

            return token_data

        except JWTError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[ALGORITHM])

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
            user = self.get_user_by_id(user_id)

            if not user or not user.is_active:
                return None

            return self.create_access_token(user)

        except JWTError:
            return None

    def create_user(self, username: str, email: str, full_name: str,
                    password: str, role: UserRole) -> User:
        """Create a new user"""
        # Check if username already exists
        if self.get_user_by_username(username):
            raise ValueError("Username already exists")

        # Generate user ID
        user_id = f"{role.value}_{len(self.users) + 1:03d}"

        user = User(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            password_hash=self.hash_password(password)
        )

        self.users[user_id] = user
        return user

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ['email', 'full_name', 'role', 'is_active']
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)

        # Handle password update
        if 'password' in kwargs:
            user.password_hash = self.hash_password(kwargs['password'])

        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if user_id in self.users:
            del self.users[user_id]
            return True
        return False

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (without sensitive data)"""
        return [user.to_dict() for user in self.users.values()]

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)

        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = sum(
                1 for user in self.users.values() if user.role == role)

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts
        }


# Global auth manager instance
auth_manager = AuthManager()

# Dependency functions for FastAPI


async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token_data = auth_manager.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception

        user = auth_manager.get_user_by_id(token_data.user_id)
        if user is None or not user.is_active:
            raise credentials_exception

        return user

    except Exception:
        raise credentials_exception


def require_permission(permission: Permission):
    """Decorator to require specific permission"""
    def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return current_user

    return permission_checker


def require_role(role: UserRole):
    """Decorator to require specific role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )
        return current_user

    return role_checker

# Utility functions


def generate_api_key(user_id: str) -> str:
    """Generate API key for user"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{user_id}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    issues = []
    score = 0

    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    else:
        score += 1

    if not any(c.isupper() for c in password):
        issues.append("Password must contain at least one uppercase letter")
    else:
        score += 1

    if not any(c.islower() for c in password):
        issues.append("Password must contain at least one lowercase letter")
    else:
        score += 1

    if not any(c.isdigit() for c in password):
        issues.append("Password must contain at least one number")
    else:
        score += 1

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        issues.append("Password must contain at least one special character")
    else:
        score += 1

    strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    strength = strength_levels[min(score, 4)]

    return {
        "is_valid": len(issues) == 0,
        "strength": strength,
        "score": score,
        "issues": issues
    }
