# src/services/base.py
from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from typing import Any, Optional
from src.core.logging import get_logger

class BaseService(ABC):
    """Base class for all services in the application."""
    
    def __init__(self, name: str, config: Any = None, registry: Any = None):
        self.name = name
        self.config = config
        self.registry = registry
        self.logger = get_logger(f"service.{name}")
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service. Must be implemented by subclasses."""
        pass
    
    async def shutdown(self) -> None:
        """Shutdown the service. Can be overridden by subclasses."""
        self._initialized = False
        self.logger.info(f"Service {self.name} shutdown")
    
    @property
    def is_initialized(self) -> bool:
        """Check if the service is initialized."""
        return self._initialized
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
    
    def __repr__(self) -> str:
        return self.__str__()