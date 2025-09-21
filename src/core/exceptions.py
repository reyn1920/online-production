"""
Core exceptions for the application.
"""


class ApplicationError(Exception):
    """Base exception for application errors."""
    
    def __init__(self, message: str, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class AuthenticationError(ApplicationError):
    """Exception raised for authentication failures."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, "AUTH_ERROR")


class AuthorizationError(ApplicationError):
    """Exception raised for authorization failures."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, "AUTHZ_ERROR")


class ValidationError(ApplicationError):
    """Exception raised for data validation failures."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, "VALIDATION_ERROR")


class DatabaseError(ApplicationError):
    """Exception raised for database operation failures."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DB_ERROR")


class ConfigurationError(ApplicationError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str = "Configuration error"):
        super().__init__(message, "CONFIG_ERROR")


class ServiceError(ApplicationError):
    """Exception raised for service operation failures."""
    
    def __init__(self, message: str = "Service error"):
        super().__init__(message, "SERVICE_ERROR")


# Alias for backward compatibility
BaseApplicationError = ApplicationError