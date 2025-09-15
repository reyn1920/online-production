from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from typing import Final
from collections.abc import Iterator, Mapping  # removed unused Iterable

from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse

# Strict, no-Any config typing
conf: dict[str, str] = {
    "DB_PATH": os.getenv("BASE44_DB_PATH", "data/base44.db"),
}

@dataclass(frozen=True)
class AppConfig:
    db_path: str

    @classmethod
    def from_mapping(cls, d: Mapping[str, str | None]) -> "AppConfig":
        return cls(db_path=(d.get("DB_PATH") or "data/base44.db"))

CFG: Final[AppConfig] = AppConfig.from_mapping(conf)

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(CFG.db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with get_conn() as conn:
        cur: sqlite3.Cursor = conn.cursor()
        _ = cur.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        _ = cur.execute("CREATE INDEX IF NOT EXISTS idx_items_key ON items(key)")
        conn.commit()

def set_item(key: str, value: str) -> None:
    with get_conn() as conn:
        cur: sqlite3.Cursor = conn.cursor()
        sql = "INSERT INTO items(key, value) VALUES(?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value"
        _ = cur.execute(sql, (key, value))
        conn.commit()

def get_all() -> Iterator[sqlite3.Row]:
    with get_conn() as conn:
        cur: sqlite3.Cursor = conn.cursor()
        _ = cur.execute("SELECT id, key, value, created_at FROM items ORDER BY id DESC")
        rows: list[sqlite3.Row] = cur.fetchall()
        for row in rows:
            yield row

# Initialize once on import for long-lived processes
init_db()

# Create FastAPI app
app = FastAPI(title="TRAE.AI Base44 Runtime API")

# Health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "trae-ai-base44"}

# Policy router
policy_router = APIRouter()

# Mock policy data for the endpoint
DO_NOT_DELETE = {
    "core_files": [
        "backend/app.py",
        "main.py",
        "backend/routers/health.py"
    ],
    "protection_level": "high",
    "created_at": "2025-01-09T19:24:00Z"
}

REVENUE_SOURCES = [
    "subscription_fees",
    "api_usage",
    "premium_features"
]

def decoded_paths():
    return ["backend/app.py", "main.py", "backend/routers/health.py"]

@policy_router.get("/api/policy/do-not-delete")
async def get_do_not_delete():
    reg = {**DO_NOT_DELETE, "paths": decoded_paths()}
    return {"ok": True, "registry": reg}

@policy_router.get("/api/policy/revenue-sources")
async def get_revenue_sources():
    return {"ok": True, "sources": REVENUE_SOURCES}

# Include the policy router
app.include_router(policy_router, tags=["policy"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "TRAE.AI Base44 Runtime API", "status": "running"}