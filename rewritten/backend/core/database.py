#!/usr/bin/env python3
"""
TRAE.AI Database Connection Manager

This module provides database connection management \
    and utilities for the TRAE.AI system.
It handles both SQLite (development) and PostgreSQL (production) database connections,
connection pooling, and database initialization.

Author: TRAE.AI System
Version: 2.0.0
Date: 2024
"""

import os
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List

# Import utilities

from utils.logger import get_logger

# Import production database manager
try:
    from .database_production import ProductionDatabaseManager

    PRODUCTION_DB_AVAILABLE = True
except ImportError:
    PRODUCTION_DB_AVAILABLE = False

logger = get_logger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations"""

    pass


class DatabaseManager:
    """
    Database connection manager for TRAE.AI system.

    Provides thread - safe database connections and utilities for SQLite operations.
    Handles connection pooling and automatic database initialization.
    """

    def __init__(self, db_path: str = "data/trae_master.db"):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._ensure_db_directory()
        self._initialize_database()

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_database(self):
        """Initialize database with schema if needed"""
        try:
            with self.get_connection() as conn:
                # Enable foreign keys
                conn.execute("PRAGMA foreign_keys = ON")

                # Check if database is initialized
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='task_queue'"
                )
                if not cursor.fetchone():
                    logger.info("Initializing database schema")
                    self._create_schema(conn)

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}")

    def _create_schema(self, conn: sqlite3.Connection):
        """Create database schema from schema.sql"""
        schema_path = Path("schema.sql")
        if schema_path.exists():
            with open(schema_path, "r") as f:
                schema_sql = f.read()
            conn.executescript(schema_sql)
        else:
            # Fallback basic schema
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS task_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT UNIQUE NOT NULL,
                        task_type TEXT NOT NULL DEFAULT 'system',
                        priority TEXT NOT NULL DEFAULT 'medium',
                        status TEXT NOT NULL DEFAULT 'pending',
                        agent_id TEXT,
                        payload TEXT,
                        result TEXT,
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        started_at TIMESTAMP,
                        completed_at TIMESTAMP,
                        retry_count INTEGER DEFAULT 0,
                        max_retries INTEGER DEFAULT 3
                );

                CREATE INDEX IF NOT EXISTS idx_task_status ON task_queue(status);
                CREATE INDEX IF NOT EXISTS idx_task_type ON task_queue(task_type);
                CREATE INDEX IF NOT EXISTS idx_agent_id ON task_queue(agent_id);
            """
            )

    @contextmanager
    def get_connection(self):
        """Get a database connection with automatic cleanup"""
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def execute_script(self, script: str) -> None:
        """Execute a SQL script"""
        with self.get_connection() as conn:
            conn.executescript(script)
            conn.commit()


# Initialize appropriate database manager based on environment


def _get_database_manager():
    """Get the appropriate database manager based on DATABASE_URL"""
    database_url = os.getenv("DATABASE_URL", "data/trae_master.db")

    # Use production manager for PostgreSQL URLs or when explicitly requested
    if PRODUCTION_DB_AVAILABLE and (
        database_url.startswith("postgresql://")
        or os.getenv("USE_PRODUCTION_DB", "").lower() == "true"
    ):
        logger.info("Using ProductionDatabaseManager for PostgreSQL")
        return ProductionDatabaseManager(database_url)
    else:
        logger.info("Using legacy DatabaseManager for SQLite")
        return DatabaseManager(
            database_url if not database_url.startswith("postgresql://") else "data/trae_master.db"
        )


# Global database manager instance
db_manager = _get_database_manager()

# Convenience functions


def get_db_connection():
    """Get database connection context manager"""
    return db_manager.get_connection()


def get_db_session():
    """Get SQLAlchemy session context manager (production only)"""
    if hasattr(db_manager, "get_session"):
        return db_manager.get_session()
    else:
        raise NotImplementedError(
            "SQLAlchemy sessions only available with ProductionDatabaseManager"
        )


def execute_query(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Execute a SELECT query"""
    return db_manager.execute_query(query, params)


def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an INSERT/UPDATE/DELETE query"""
    return db_manager.execute_update(query, params)


def database_health_check() -> Dict[str, Any]:
    """Perform database health check"""
    if hasattr(db_manager, "health_check"):
        return db_manager.health_check()
    else:
        # Fallback health check for legacy manager
        try:
            with get_db_connection() as conn:
                conn.execute("SELECT 1")
            return {"status": "healthy", "database_type": "sqlite"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "database_type": "sqlite"}
