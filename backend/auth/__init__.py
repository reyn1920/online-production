"""Fixed nested docstring"""

# Import core security components
# Import data models
from .models import AuditLogEntry  # Fixed incomplete statement
from .models import (ChangePasswordRequest, LoginRequest,  # Fixed incomplete statement
                     LoginResponse, RefreshTokenRequest, UserBase, UserCreate, UserInDB,
                     UserResponse, UserRole, UserStatus, UserUpdate)
# Import routes
from .routes import admin_router  # Fixed incomplete statement
from .routes import auth_router, users_router  # Fixed incomplete statement
from .security import rate_limiter  # Fixed incomplete statement
from .security import (JWTManager, PasswordManager,  # Fixed incomplete statement
                       RateLimiter, SecurityMiddleware, SecurityUtils, TokenData,
                       TokenResponse, jwt_manager, password_manager,
                       security_middleware, security_utils)
# Import service layer
from .service import auth_service  # Fixed incomplete statement
from .service import (AuthService, UserService,  # Fixed incomplete statement
                      user_service)

__version__ = "1.0.0"
__author__ = "TRAE.AI System"

# Export all public components
__all__ = [
    # Security components
    "JWTManager",
    "PasswordManager",
    "SecurityUtils",
    "SecurityMiddleware",
    "RateLimiter",
    "TokenData",
    "TokenResponse",
    "jwt_manager",
    "password_manager",
    "security_utils",
    "security_middleware",
    "rate_limiter",
    # Data models
    "UserRole",
    "UserStatus",
    "UserBase",
    "UserCreate",
    "UserInDB",
    "UserResponse",
    "UserUpdate",
    "LoginRequest",
    "LoginResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "AuditLogEntry",
    # Services
    "UserService",
    "AuthService",
    "user_service",
    "auth_service",
    # Routes
    "auth_router",
    "users_router",
    "admin_router",
]
