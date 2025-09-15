# auth.py - AI - Enhanced User Authentication and Authorization Module

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
    """User roles for role - based access control"""

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


# Role - Permission mapping
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
    """AI - Enhanced authentication manager with intelligent security features"""

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
            self.users[user.id] = user

    def hash_password(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    def authenticate_user(
        self, username: str, password: str, request_info: Dict[str, Any] = None
    ) -> Optional[User]:
        """AI - Enhanced authentication with intelligent security analysis"""
        user = self.get_user_by_username(username)
        if not user or not user.is_active:
            return None

        # AI - powered security analysis
        if AI_INTEGRATION_AVAILABLE and request_info:
            security_analysis = self._analyze_login_attempt(username, request_info)
            if security_analysis.get("threat_level", "low") == "high":
                self._log_security_event(username, "high_threat_login_blocked", security_analysis)
                return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Update last login
        user.last_login = datetime.now()

        # AI - powered behavioral analysis
        if AI_INTEGRATION_AVAILABLE:
            self._analyze_user_behavior(user, request_info)

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
            "iat": datetime.utcnow(),
# BRACKET_SURGEON: disabled
#         }

        return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)

    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

        payload = {
            "sub": user.id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.utcnow(),
# BRACKET_SURGEON: disabled
#         }

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

            if payload.get("type") != "refresh":
                return None

            user_id = payload.get("sub")
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
            password_hash=self.hash_password(password),
# BRACKET_SURGEON: disabled
#         )

        self.users[user_id] = user
        return user

    def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information"""
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ["email", "full_name", "role", "is_active"]
        for field, value in kwargs.items():
            if field in allowed_fields:
                setattr(user, field, value)

        # Handle password update
        if "password" in kwargs:
            user.password_hash = self.hash_password(kwargs["password"])

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
        """Get AI - enhanced user statistics with security insights"""
        total_users = len(self.users)
        active_users = sum(1 for user in self.users.values() if user.is_active)

        role_counts = {}
        for role in UserRole:
            role_counts[role.value] = sum(1 for user in self.users.values() if user.role == role)

        # AI - powered security insights
        security_insights = {}
        if AI_INTEGRATION_AVAILABLE:
            security_insights = self._get_ai_security_insights()

        return {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "role_distribution": role_counts,
            "security_insights": security_insights,
            "suspicious_activities_count": len(self.suspicious_activities),
            "ai_security_logs_count": len(self.ai_security_logs),
            "last_updated": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

    def _analyze_login_attempt(self, username: str, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """AI - powered analysis of login attempts for threat detection"""
        if not AI_INTEGRATION_AVAILABLE:
            return {"threat_level": "low"}

        try:
            # Prepare analysis prompt
            analysis_prompt = f""""""
            Analyze this login attempt for security threats:
            Username: {username}
            IP Address: {request_info.get('ip_address', 'unknown')}
            User Agent: {request_info.get('user_agent', 'unknown')}
            Timestamp: {datetime.now().isoformat()}

            Assess threat level (low / medium / high) and provide reasoning.
            Consider: unusual IP, suspicious user agent, timing patterns, geographic anomalies.
            """"""

            # Get AI analysis from multiple platforms for cross - validation
            ai_request = AIRequest(
                prompt=analysis_prompt,
                platform=AIPlatform.CHATGPT,
                context={"type": "security_analysis", "username": username},
# BRACKET_SURGEON: disabled
#             )

            chatgpt_response = core_ai.process_request(ai_request)

            # Cross - validate with Gemini
            ai_request.platform = AIPlatform.GEMINI
            gemini_response = core_ai.process_request(ai_request)

            # Parse responses and determine threat level
            threat_analysis = {
                "chatgpt_assessment": chatgpt_response.get("content", ""),
                "gemini_assessment": gemini_response.get("content", ""),
                "threat_level": self._determine_threat_level(chatgpt_response, gemini_response),
                "timestamp": datetime.now().isoformat(),
                "request_info": request_info,
# BRACKET_SURGEON: disabled
#             }

            return threat_analysis

        except Exception as e:
            self._log_security_event(username, "ai_analysis_error", {"error": str(e)})
            return {"threat_level": "low", "error": str(e)}

    def _analyze_user_behavior(self, user: User, request_info: Dict[str, Any]) -> None:
        """AI - powered behavioral analysis for anomaly detection"""
        if not AI_INTEGRATION_AVAILABLE:
            return

        try:
            behavior_prompt = f""""""
            Analyze user behavior for anomalies:
            User: {user.username} (Role: {user.role.value})
            Login time: {datetime.now().isoformat()}
            Last login: {user.last_login.isoformat() if user.last_login else 'Never'}
            IP Address: {request_info.get('ip_address', 'unknown')}

            Identify any unusual patterns or potential security concerns.
            """"""

            ai_request = AIRequest(
                prompt=behavior_prompt,
                platform=AIPlatform.ABACUS_AI,
                context={"type": "behavior_analysis", "user_id": user.id},
# BRACKET_SURGEON: disabled
#             )

            response = core_ai.process_request(ai_request)

            # Log behavioral insights
            behavior_log = {
                "user_id": user.id,
                "username": user.username,
                "analysis": response.get("content", ""),
                "timestamp": datetime.now().isoformat(),
                "request_info": request_info,
# BRACKET_SURGEON: disabled
#             }

            self.ai_security_logs.append(behavior_log)

            # Check for suspicious activity indicators
            if "suspicious" in response.get("content", "").lower():
                if user.username not in self.suspicious_activities:
                    self.suspicious_activities[user.username] = []
                self.suspicious_activities[user.username].append(behavior_log)

        except Exception as e:
            self._log_security_event(user.username, "behavior_analysis_error", {"error": str(e)})

    def _determine_threat_level(self, chatgpt_response: Dict, gemini_response: Dict) -> str:
        """Determine threat level from AI responses"""
        chatgpt_content = chatgpt_response.get("content", "").lower()
        gemini_content = gemini_response.get("content", "").lower()

        high_indicators = ["high", "dangerous", "suspicious", "threat", "malicious"]
        medium_indicators = ["medium", "caution", "unusual", "anomaly"]

        # Check for high threat indicators
        if any(
            indicator in chatgpt_content or indicator in gemini_content
            for indicator in high_indicators
# BRACKET_SURGEON: disabled
#         ):
            return "high"

        # Check for medium threat indicators
        if any(
            indicator in chatgpt_content or indicator in gemini_content
            for indicator in medium_indicators
# BRACKET_SURGEON: disabled
#         ):
            return "medium"

        return "low"

    def _log_security_event(self, username: str, event_type: str, details: Dict[str, Any]) -> None:
        """Log security events for monitoring and analysis"""
        security_event = {
            "username": username,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#         }

        self.ai_security_logs.append(security_event)

        # Keep only last 1000 logs to prevent memory issues
        if len(self.ai_security_logs) > 1000:
            self.ai_security_logs = self.ai_security_logs[-1000:]

    def _get_ai_security_insights(self) -> Dict[str, Any]:
        """Generate AI - powered security insights from logged events"""
        if not AI_INTEGRATION_AVAILABLE or not self.ai_security_logs:
            return {}

        try:
            recent_logs = self.ai_security_logs[-50:]  # Analyze last 50 events

            insights_prompt = f""""""
            Analyze these security events and provide insights:
            {recent_logs}

            Provide:
            1. Overall security status
            2. Key threats identified
            3. Recommendations for improvement
            4. Risk assessment
            """"""

            ai_request = AIRequest(
                prompt=insights_prompt,
                platform=AIPlatform.CHATGPT,
                context={"type": "security_insights"},
# BRACKET_SURGEON: disabled
#             )

            response = core_ai.process_request(ai_request)

            return {
                "analysis": response.get("content", ""),
                "generated_at": datetime.now().isoformat(),
                "events_analyzed": len(recent_logs),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            return {"error": str(e), "generated_at": datetime.now().isoformat()}

    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive security data for dashboard display"""
        return {
            "total_security_events": len(self.ai_security_logs),
            "suspicious_users": len(self.suspicious_activities),
            "recent_threats": [
                log for log in self.ai_security_logs[-10:] if "threat" in log.get("event_type", "")
# BRACKET_SURGEON: disabled
#             ],
            "ai_integration_status": AI_INTEGRATION_AVAILABLE,
            "security_insights": self._get_ai_security_insights()
            if AI_INTEGRATION_AVAILABLE
            else None,
# BRACKET_SURGEON: disabled
#         }


# Global auth manager instance
auth_manager = AuthManager()

# Dependency functions for FastAPI


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
# BRACKET_SURGEON: disabled
# ) -> User:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW - Authenticate": "Bearer"},
# BRACKET_SURGEON: disabled
#     )

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
                detail=f"Permission required: {permission.value}",
# BRACKET_SURGEON: disabled
#             )
        return current_user

    return permission_checker


def require_role(role: UserRole):
    """Decorator to require specific role"""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
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