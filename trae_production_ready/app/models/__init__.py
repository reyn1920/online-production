"""Central model registry for Base metadata.
Import all models here so they are registered.
Do not delete or rename without approval.
"""

from .base import BaseModel
from .user import User

# Import Base for metadata access
from app.core.database import Base

__all__ = [
    "BaseModel",
    "User",
    "Base",
]