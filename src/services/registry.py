# src/services/registry.py
from __future__ import annotations
import asyncio
from typing import Dict, Type, TypeVar, Any
from src.core.logging import get_logger
from src.core.config import Config
from src.services.base import BaseService

T = TypeVar("T", bound=BaseService)
logger = get_logger(__name__)

class ServiceRegistry:
    """A central registry for managing application services."""

    def __init__(self, config: Config | None = None):
        self.config = config or Config()
        self._services: Dict[str, BaseService] = {}
        self._singletons: Dict[Type[BaseService], BaseService] = {}
        self._initialized = False

    def register(self, service_name: str, service_instance: BaseService):
        """Registers a named service instance."""
        if service_name in self._services:
            logger.warning(f"Service '{service_name}' is already registered. Overwriting.")
        self._services[service_name] = service_instance
        logger.debug(f"Registered service: {service_name}")

    def register_singleton(self, service_class: Type[T]) -> T:
        """Registers and instantiates a singleton service."""
        if service_class in self._singletons:
            return self._singletons[service_class]
        
        instance = service_class(config=self.config, registry=self)
        self._singletons[service_class] = instance
        logger.debug(f"Registered singleton: {service_class.__name__}")
        return instance

    def get(self, service_name: str) -> BaseService | None:
        """Gets a named service instance."""
        return self._services.get(service_name)

    def get_service(self, service_class: Type[T]) -> T:
        """Gets a singleton service instance by its class."""
        if service_class not in self._singletons:
            return self.register_singleton(service_class)
        return self._singletons[service_class]

    async def initialize_all(self):
        """Initializes all registered services."""
        if self._initialized:
            return
        logger.info("Initializing all services...")
        
        all_services = list(self._services.values()) + list(self._singletons.values())
        init_tasks = [
            service.initialize()
            for service in all_services
            if hasattr(service, "initialize") and callable(service.initialize)
        ]
        await asyncio.gather(*init_tasks)
        self._initialized = True
        logger.info("All services initialized.")

    async def shutdown_all(self):
        """Shuts down all registered services."""
        logger.info("Shutting down all services...")
        all_services = list(self._services.values()) + list(self._singletons.values())
        shutdown_tasks = [
            service.shutdown()
            for service in all_services
            if hasattr(service, "shutdown") and callable(service.shutdown)
        ]
        await asyncio.gather(*shutdown_tasks)
        self._initialized = False
        logger.info("All services shut down.")
