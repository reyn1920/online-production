#!/usr/bin/env python3
"""
Database Singleton Manager

This module provides singleton instances of database managers to prevent
redundant initialization across multiple modules.

Features:
- Singleton pattern for HypocrisyDatabaseManager
- Thread-safe initialization
- Lazy loading
- Error handling and fallback

Author: TRAE.AI System
Version: 1.0.0
"""

import logging
import threading
from typing import Optional

try:
    from backend.database.hypocrisy_db_manager import HypocrisyDatabaseManager
except ImportError:
    HypocrisyDatabaseManager = None


class DatabaseSingleton:
    """Singleton manager for database instances"""

    _instance = None
    _lock = threading.Lock()
    _hypocrisy_db_manager = None
    _hypocrisy_db_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseSingleton, cls).__new__(cls)
                    cls._instance.logger = logging.getLogger(__name__)
        return cls._instance

    def get_hypocrisy_db_manager(self) -> Optional[HypocrisyDatabaseManager]:
        """Get singleton instance of HypocrisyDatabaseManager"""
        if self._hypocrisy_db_manager is None:
            with self._hypocrisy_db_lock:
                if self._hypocrisy_db_manager is None:
                    if HypocrisyDatabaseManager:
                        try:
                            self._hypocrisy_db_manager = HypocrisyDatabaseManager()
                            self.logger.info(
                                "Hypocrisy database manager initialized successfully (singleton)"
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Failed to initialize hypocrisy database manager: {e}"
                            )
                            return None
                    else:
                        self.logger.warning("HypocrisyDatabaseManager not available")
                        return None

        return self._hypocrisy_db_manager

    def reset_hypocrisy_db_manager(self):
        """Reset the hypocrisy database manager (for testing)"""
        with self._hypocrisy_db_lock:
            self._hypocrisy_db_manager = None


# Global singleton instance
_db_singleton = DatabaseSingleton()


def get_hypocrisy_db_manager() -> Optional[HypocrisyDatabaseManager]:
    """Get the singleton HypocrisyDatabaseManager instance"""
    return _db_singleton.get_hypocrisy_db_manager()


def reset_db_singletons():
    """Reset all database singletons (for testing)"""
    _db_singleton.reset_hypocrisy_db_manager()
