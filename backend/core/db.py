from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Optional, Tuple

# Support multiple database files


def get_db_path(db_name: str) -> Path:
    """Get path for a specific database file"""
    if not db_name.endswith(".db"):
        db_name += ".db"
    path = Path("data") / db_name
    path.parent.mkdir(parents = True, exist_ok = True)
    return path

@contextmanager


def get_conn(db_name: str = "trae_ai.db"):
    """Get database connection with context manager"""
    db_path = get_db_path(db_name)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def connect(db_name: str = "trae_ai.db") -> sqlite3.Connection:
    """Direct connection (legacy compatibility)"""
    db_path = get_db_path(db_name)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def count_table(db_name: str, table_name: str) -> int:
    """Count rows in a table"""
    with get_conn(db_name) as conn:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]


def ensure_schema() -> None:
    """Ensure basic schema exists"""
    with get_conn("trae_ai.db") as cx:
        cx.execute(
            """
        CREATE TABLE IF NOT EXISTS affiliates(
            name TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                tag TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                mtime REAL NOT NULL
        )
        """
        )
        cx.commit()
