# src/services/data.py
from __future__ import annotations
from typing import Dict, Any, List, Optional
from src.core.config import Config
from src.services.base import BaseService
from src.services.registry import ServiceRegistry


class DataService(BaseService):
    """Manages data operations and database interactions."""

    def __init__(self, config: Config, registry: ServiceRegistry | None = None):
        super().__init__("data", config, registry)
        self.is_initialized = False
        self._data_store: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize the data service."""
        self.is_initialized = True

    async def shutdown(self):
        """Shutdown the data service."""
        self._data_store.clear()

    async def create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        if table not in self._data_store:
            self._data_store[table] = []

        record = {"id": f"{table}_{len(self._data_store[table])}", **data}
        self._data_store[table].append(record)
        return record

    async def read(self, table: str, record_id: str) -> Optional[Dict[str, Any]]:
        """Read a record by ID."""
        if table not in self._data_store:
            return None

        for record in self._data_store[table]:
            if record.get("id") == record_id:
                return record
        return None

    async def update(
        self, table: str, record_id: str, data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update a record."""
        if table not in self._data_store:
            return None

        for i, record in enumerate(self._data_store[table]):
            if record.get("id") == record_id:
                self._data_store[table][i] = {**record, **data}
                return self._data_store[table][i]
        return None

    async def delete(self, table: str, record_id: str) -> bool:
        """Delete a record."""
        if table not in self._data_store:
            return False

        for i, record in enumerate(self._data_store[table]):
            if record.get("id") == record_id:
                del self._data_store[table][i]
                return True
        return False

    async def list_all(self, table: str) -> List[Dict[str, Any]]:
        """List all records in a table."""
        return self._data_store.get(table, [])
