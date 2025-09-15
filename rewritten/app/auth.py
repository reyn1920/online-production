# auth.py - AI-Enhanced User Authentication and Authorization Module

import hashlib
import os
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

# AI Integration for enhanced security
try:
    from core_ai_integration import core_ai, AIPlatform, AIRequest

    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False
    core_ai = None

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
        Permission.VIEW_LOGS,
# BRACKET_SURGEON: disabled
#     ],
    UserRole.MANAGER: [
        Permission.READ_DASHBOARD,
        Permission.WRITE_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_DATA,
        Permission.VIEW_LOGS,
# BRACKET_SURGEON: disabled
#     ],
    UserRole.ANALYST: [
        Permission.READ_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.EXPORT_DATA,
# BRACKET_SURGEON: disabled
#     ],
    UserRole.VIEWER: [Permission.READ_DASHBOARD],
# BRACKET_SURGEON: disabled
# }


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
        """Get all permissions for user's role"""'
        return ROLE_PERMISSIONS.get(self.role, [])

    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary (excluding password hash)"""
        data = asdict(self)
        data.pop("password_hash", None)
        data["created_at"] = self.created_at.isoformat() if self.created_at else None
        data["last_login"] = self.last_login.isoformat() if self.last_login else None
        data["permissions"] = [p.value for p in self.get_permissions()]
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
    """AI-Enhanced authentication manager with intelligent security features"""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.sessions: Dict[str, Dict] = {}
        self.ai_security_logs: List[Dict[str, Any]] = []
        self.suspicious_activities: Dict[str, List[Dict[str, Any]]] = {}

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
                "password": "admin123",  # In production, use secure password
# BRACKET_SURGEON: disabled
#             },
            {
                "id": "manager_001",
                "username": "manager",
                "email": "manager@dashboard.com",
                "full_name": "Dashboard Manager",
                "role": UserRole.MANAGER,
                "password": "manager123",
# BRACKET_SURGEON: disabled
#             },
            {
                "id": "analyst_001",
                "username": "analyst",
                "email": "analyst@dashboard.com",
                "full_name": "Data Analyst",
                "role": UserRole.ANALYST,
                "password": "analyst123",
# BRACKET_SURGEON: disabled
#             },
            {
                "id": "viewer_001",
                "username": "viewer",
                "email": "viewer@dashboard.com",
                "full_name": "Dashboard Viewer",
                "role": UserRole.VIEWER,
                "password": "viewer123",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         ]

        for user_data in default_users:
            password = user_data.pop("password")
            user = User(**user_data)
            user.password_hash = self.hash_password(password)
            self.users[user.username] = user

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(
        self, username: str, password: str, request_info: Dict[str, Any] = None
    ) -> Optional[User]:
        """Authenticate user with AI-enhanced security analysis"""
        user = self.get_user_by_username(username)
        if not user:
            self._log_security_event(username, "failed_login", {"reason": "user_not_found"})
            return None

        if not user.is_active:
            self._log_security_event(username, "failed_login", {"reason": "account_disabled"})
            return None

        if not self.verify_password(password, user.password_hash):
            self._log_security_event(username, "failed_login", {"reason": "invalid_password"})
            return None

        # AI-enhanced security analysis
        if request_info and AI_INTEGRATION_AVAILABLE:
            self._analyze_login_attempt(username, request_info)
            self._analyze_user_behavior(user, request_info)

        # Update last login
        user.last_login = datetime.now()
        self._log_security_event(username, "successful_login", {})
        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.users.get(username)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None

    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "permissions": [p.value for p in user.get_permissions()],
            "exp": expire,
            "iat": datetime.utcnow(),
# BRACKET_SURGEON: disabled
#         }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
# BRACKET_SURGEON: disabled
#         }
        return jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)

    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                return None

            # Check if token is refresh token
            if payload.get("type") == "refresh":
                return None

            token_data = TokenData(
                user_id=user_id,
                username=payload.get("username"),
                role=UserRole(payload.get("role")),
                permissions=payload.get("permissions", []),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
# BRACKET_SURGEON: disabled
#             )
            return token_data
        except JWTError:
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Create new access token from refresh token"""
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            token_type: str = payload.get("type")

            if user_id is None or token_type != "refresh":
                return None

            user = self.get_user_by_id(user_id)
            if not user or not user.is_active:
                return None

            return self.create_access_token(user)
        except JWTError:
            return None

    def create_user(
        self, username: str, email: str, full_name: str, password: str, role: UserRole
# BRACKET_SURGEON: disabled
#     ) -> User:
        """Create new user"""
        if username in self.users:
            raise ValueError("Username already exists")

        user_id = f"{role.value}_{secrets.token_hex(8)}"
        user = User(
            id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            password_hash=self.hash_password(password),
# BRACKET_SURGEON: disabled
#         )
        self.users[username] = user
        self._log_security_event(username, "user_created", {"role": role.value})
        return user

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key) and key != "id":
                if key == "password":
                    user.password_hash = self.hash_password(value)
                else:
                    setattr(user, key, value)

        self._log_security_event(
            user.username, "user_updated", {"updated_fields": list(kwargs.keys())}
# BRACKET_SURGEON: disabled
#         )
        return user

    def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        del self.users[user.username]
        self._log_security_event(user.username, "user_deleted", {})
        return True

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users"""
        return [user.to_dict() for user in self.users.values()]

    def get_user_stats(self) -> Dict[str, Any]:
        """Get user statistics"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)
        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = sum(1 for user in self.users.values() if user.role == role)

        recent_logins = sum(
            1
            for user in self.users.values()
            if user.last_login and user.last_login > datetime.now() - timedelta(days=7)
# BRACKET_SURGEON: disabled
#         )

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts,
            "recent_logins_7d": recent_logins,
# BRACKET_SURGEON: disabled
#         }

    def _analyze_login_attempt(self, username: str, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """AI-enhanced login attempt analysis"""
        if not AI_INTEGRATION_AVAILABLE:
            return {"threat_level": "unknown", "analysis": "AI not available"}

        try:
            # Prepare data for AI analysis
            analysis_data = {
                "username": username,
                "ip_address": request_info.get("ip_address"),
                "user_agent": request_info.get("user_agent"),
                "timestamp": datetime.now().isoformat(),
                "geolocation": request_info.get("geolocation"),
                "device_fingerprint": request_info.get("device_fingerprint"),
# BRACKET_SURGEON: disabled
#             }

            # Get AI analysis from multiple platforms
            chatgpt_request = AIRequest(
                platform=AIPlatform.CHATGPT,
                prompt=f"Analyze this login attempt for security threats: {analysis_data}",
                context="security_analysis",
# BRACKET_SURGEON: disabled
#             )

            gemini_request = AIRequest(
                platform=AIPlatform.GEMINI,
                prompt=f"Security assessment of login attempt: {analysis_data}",
                context="threat_detection",
# BRACKET_SURGEON: disabled
#             )

            chatgpt_response = core_ai.process_request(chatgpt_request)
            gemini_response = core_ai.process_request(gemini_request)

            # Combine AI insights
            threat_level = self._determine_threat_level(chatgpt_response, gemini_response)

            analysis_result = {
                "threat_level": threat_level,
                "chatgpt_analysis": chatgpt_response.get("content", ""),
                "gemini_analysis": gemini_response.get("content", ""),
                "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

            self.ai_security_logs.append(analysis_result)
            return analysis_result

        except Exception as e:
            return {
                "threat_level": "error",
                "analysis": f"Analysis failed: {str(e)}",
# BRACKET_SURGEON: disabled
#             }

    def _analyze_user_behavior(self, user: User, request_info: Dict[str, Any]) -> None:
        """Analyze user behavior patterns with AI"""
        if not AI_INTEGRATION_AVAILABLE:
            return

        try:
            # Track user behavior patterns
            behavior_data = {
                "user_id": user.id,
                "username": user.username,
                "login_time": datetime.now().isoformat(),
                "ip_address": request_info.get("ip_address"),
                "user_agent": request_info.get("user_agent"),
                "previous_login": (user.last_login.isoformat() if user.last_login else None),
# BRACKET_SURGEON: disabled
#             }

            # Check for suspicious patterns
            if user.username not in self.suspicious_activities:
                self.suspicious_activities[user.username] = []

            # Add current activity
            self.suspicious_activities[user.username].append(behavior_data)

            # Keep only recent activities (last 30 days)
            cutoff_date = datetime.now() - timedelta(days=30)
            self.suspicious_activities[user.username] = [
                activity
                for activity in self.suspicious_activities[user.username]
                if datetime.fromisoformat(activity["login_time"]) > cutoff_date
# BRACKET_SURGEON: disabled
#             ]

        except Exception as e:
            self._log_security_event(user.username, "behavior_analysis_error", {"error": str(e)})

    def _determine_threat_level(self, chatgpt_response: Dict, gemini_response: Dict) -> str:
        """Determine threat level from AI responses"""
        try:
            # Simple threat level determination logic
            chatgpt_content = chatgpt_response.get("content", "").lower()
            gemini_content = gemini_response.get("content", "").lower()

            high_risk_keywords = ["suspicious", "threat", "malicious", "attack"]
            medium_risk_keywords = ["unusual", "anomaly", "caution"]

            high_risk_score = sum(
                1 for keyword in high_risk_keywords if keyword in chatgpt_content
            ) + sum(1 for keyword in high_risk_keywords if keyword in gemini_content)

            medium_risk_score = sum(
                1 for keyword in medium_risk_keywords if keyword in chatgpt_content
            ) + sum(1 for keyword in medium_risk_keywords if keyword in gemini_content)

            if high_risk_score >= 2:
                return "high"
            elif high_risk_score >= 1 or medium_risk_score >= 2:
                return "medium"
            else:
                return "low"

        except Exception:
            return "unknown"

    def _log_security_event(self, username: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log security event"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "event_type": event_type,
            "details": details,
# BRACKET_SURGEON: disabled
#         }
        self.ai_security_logs.append(event)

        # Keep only recent logs (last 1000 events)
        if len(self.ai_security_logs) > 1000:
            self.ai_security_logs = self.ai_security_logs[-1000:]

    def _get_ai_security_insights(self) -> Dict[str, Any]:
        """Get AI-powered security insights"""
        if not AI_INTEGRATION_AVAILABLE:
            return {"status": "AI not available"}

        try:
            recent_logs = self.ai_security_logs[-100:]  # Last 100 events

            # Analyze patterns
            failed_logins = sum(1 for log in recent_logs if log.get("event_type") == "failed_login")
            successful_logins = sum(
                1 for log in recent_logs if log.get("event_type") == "successful_login"
# BRACKET_SURGEON: disabled
#             )

            # Calculate security metrics
            total_attempts = failed_logins + successful_logins
            failure_rate = (failed_logins / max(total_attempts, 1)) * 100

            return {
                "total_security_events": len(recent_logs),
                "failed_login_attempts": failed_logins,
                "successful_logins": successful_logins,
                "login_failure_rate": round(failure_rate, 2),
                "security_status": "high_alert" if failure_rate > 50 else "normal",
                "ai_recommendations": [
                    "Monitor failed login patterns",
                    "Implement rate limiting",
                    "Enable multi-factor authentication",
# BRACKET_SURGEON: disabled
#                 ],
# BRACKET_SURGEON: disabled
#             }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive security dashboard data"""
        return {
            "user_stats": self.get_user_stats(),
            "ai_insights": self._get_ai_security_insights(),
            "recent_events": self.ai_security_logs[-20:],  # Last 20 events
# BRACKET_SURGEON: disabled
#         }


# Global auth manager instance
auth_manager = AuthManager()


# FastAPI dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
# BRACKET_SURGEON: disabled
# ) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
# BRACKET_SURGEON: disabled
#     )

    token_data = auth_manager.verify_token(credentials.credentials)
    if token_data is None:
        raise credentials_exception

    user = auth_manager.get_user_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception

    return user


def require_permission(permission: Permission):
    """Decorator to require specific permission"""

    def permission_checker(current_user: User = Depends(get_current_user)):
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}",
# BRACKET_SURGEON: disabled
#             )
        return current_user

    return permission_checker


def require_role(role: UserRole):
    """Decorator to require specific role"""

    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}",
# BRACKET_SURGEON: disabled
#             )
        return current_user

    return role_checker


# Utility functions
def generate_api_key(user_id: str) -> str:
    """Generate API key for user"""
    timestamp = str(int(datetime.now().timestamp()))
    data = f"{user_id}:{timestamp}:{secrets.token_hex(16)}"
    return hashlib.sha256(data.encode()).hexdigest()


def validate_password_strength(password: str) -> Dict[str, Any]:
    """Validate password strength"""
    issues = []
    score = 0

    if len(password) < PASSWORD_MIN_LENGTH:
        issues.append(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
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

    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):"
        issues.append("Password must contain at least one special character")
    else:
        score += 1

    strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
    strength = strength_levels[min(score, 4)]

    return {
        "is_valid": len(issues) == 0,
        "strength": strength,
        "score": score,
        "issues": issues,
# BRACKET_SURGEON: disabled
#     }