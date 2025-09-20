# src/services/registry.py
from __future__ import annotations
import asyncio
from typing import Dict, Type, TypeVar, Optional, List
from src.core.config import Config
from src.core.logging import get_logger
from src.services.base import BaseService

T = TypeVar("T", bound=BaseService)
logger = get_logger(__name__)


class ServiceRegistry:
    def __init__(self, config: Optional[Config] = None) -> None:
        self.config = config or Config()
        self._services: Dict[str, BaseService] = {}
        self._singletons: Dict[Type[BaseService], BaseService] = {}
        self._initialized = False

    def register(self, service_name: str, service_instance: BaseService) -> None:
        self._services[service_name] = service_instance

    def get(self, service_name: str) -> Optional[BaseService]:
        return self._services.get(service_name)

    def get_service(self, service_class: Type[T]) -> T:
        if service_class not in self._singletons:
            instance = service_class(config=self.config, registry=self)
            self._singletons[service_class] = instance
        return self._singletons[service_class]

    async def initialize_all(self) -> None:
        if self._initialized:
            return
        all_services: List[BaseService] = list(self._services.values()) + list(self._singletons.values())
        init_tasks = [s.initialize() for s in all_services if hasattr(s, "initialize")]
        await asyncio.gather(*init_tasks)
        self._initialized = True

    async def shutdown_all(self) -> None:
        all_services: List[BaseService] = list(self._services.values()) + list(self._singletons.values())
        shutdown_tasks = [s.shutdown() for s in all_services if hasattr(s, "shutdown")]
        await asyncio.gather(*shutdown_tasks)
        self._initialized = False


_DEFAULT_REGISTRY: ServiceRegistry | None = None


def get_service_registry() -> ServiceRegistry:
    """Returns the singleton service registry instance."""
    global _DEFAULT_REGISTRY
    if _DEFAULT_REGISTRY is None:
        _DEFAULT_REGISTRY = ServiceRegistry()
    return _DEFAULT_REGISTRY