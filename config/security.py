"""Production security configuration for FastAPI application."""

from __future__ import annotations

import os
from typing import List


class SecurityConfig:
    """Security configuration for production deployment."""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.is_production = self.environment == "production"
        
    @property
    def allowed_origins(self) -> List[str]:
        """Get allowed CORS origins based on environment."""
        if self.is_production:
            # Production: Only allow specific domains
            origins = os.getenv("ALLOWED_ORIGINS", "")
            if not origins:
                raise ValueError("ALLOWED_ORIGINS must be set in production")
            return [origin.strip() for origin in origins.split(",") if origin.strip()]
        else:
            # Development: Allow localhost variants
            return [
                "http://localhost:3000",
                "http://localhost:8000",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8000",
                "http://localhost:5173",  # Vite dev server
                "http://127.0.0.1:5173"
            ]
    
    @property
    def allow_credentials(self) -> bool:
        """Whether to allow credentials in CORS requests."""
        return True  # Required for authenticated requests
    
    @property
    def allowed_methods(self) -> List[str]:
        """Allowed HTTP methods."""
        return ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    
    @property
    def allowed_headers(self) -> List[str]:
        """Allowed request headers."""
        return [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-Request-ID",
            "Accept",
            "Origin",
            "User-Agent"
        ]
    
    @property
    def rate_limit_rpm(self) -> int:
        """Rate limit requests per minute."""
        return int(os.getenv("RATE_LIMIT_RPM", "120"))
    
    @property
    def trusted_hosts(self) -> List[str]:
        """Trusted host patterns."""
        if self.is_production:
            hosts = os.getenv("TRUSTED_HOSTS", "")
            if not hosts:
                raise ValueError("TRUSTED_HOSTS must be set in production")
            return [host.strip() for host in hosts.split(",") if host.strip()]
        else:
            return [
                "localhost",
                "127.0.0.1",
                "*.localhost",
                "*.netlify.app"  # For preview deployments
            ]
    
    @property
    def security_headers(self) -> dict[str, str]:
        """Security headers to add to all responses."""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), camera=(), microphone=(), payment=()",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains" if self.is_production else ""
        }
    
    def validate(self) -> bool:
        """Validate security configuration."""
        try:
            # Ensure critical settings are configured for production
            if self.is_production:
                if not os.getenv("ALLOWED_ORIGINS"):
                    raise ValueError("ALLOWED_ORIGINS must be set in production")
                if not os.getenv("TRUSTED_HOSTS"):
                    raise ValueError("TRUSTED_HOSTS must be set in production")
                
                # Ensure no wildcard origins in production
                if "*" in self.allowed_origins:
                    raise ValueError("Wildcard origins (*) not allowed in production")
            
            return True
        except Exception as e:
            print(f"Security configuration validation failed: {e}")
            return False


# Global security config instance
security_config = SecurityConfig()