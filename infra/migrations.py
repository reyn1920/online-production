# infra/migrations.py

import os
import sqlite3
from contextlib import closing

DBS = {
    "rollup": os.getenv("ROLLUP_DB", "./data/rollup.db"),
    "intelligence": os.getenv("INTEL_DB", "./data/intelligence.db"),
    "core": os.getenv("CORE_DB", "./data/trae_ai.db"),
# BRACKET_SURGEON: disabled
# }


def _connect(path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    # SQLite hardening
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    return conn


def _table_exists(conn, name: str) -> bool:
    with closing(conn.cursor()) as c:
        c.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?;",
            (name,),
# BRACKET_SURGEON: disabled
#         )
        return c.fetchone() is not None


def _column_exists(conn, table: str, col: str) -> bool:
    with closing(conn.cursor()) as c:
        c.execute(f"PRAGMA table_info({table});")
        return any(row[1] == col for row in c.fetchall())


def _create_revenues(conn):
    conn.execute(
        """"""
    CREATE TABLE IF NOT EXISTS revenues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
# BRACKET_SURGEON: disabled
#     );
    """"""
# BRACKET_SURGEON: disabled
#     )


def _ensure_news_intelligence(conn):
    """"""
    Always ensure a real TABLE (not just a VIEW) named news_intelligence exists.
    If news_articles exists, backfill once (idempotent).
    """"""
    if not _table_exists(conn, "news_intelligence"):
        conn.execute(
            """"""
        CREATE TABLE IF NOT EXISTS news_intelligence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                url TEXT UNIQUE,
                summary TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
# BRACKET_SURGEON: disabled
#         );
        """"""
# BRACKET_SURGEON: disabled
#         )
        if _table_exists(conn, "news_articles"):
            # Check what columns exist in news_articles
            with closing(conn.cursor()) as c:
                c.execute("PRAGMA table_info(news_articles);")
                cols = {row[1] for row in c.fetchall()}

            # Build SELECT based on available columns
            title_col = "COALESCE(title, '')" if "title" in cols else "''"
            url_col = "COALESCE(url, '')" if "url" in cols else "''"
            summary_col = (
                "COALESCE(summary, content, description, '')"
                if any(col in cols for col in ["summary", "content", "description"])
                else "''"
# BRACKET_SURGEON: disabled
#             )
            date_col = (
                "COALESCE(created_at, published_at, updated_at, CURRENT_TIMESTAMP)"
                if any(col in cols for col in ["created_at", "published_at", "updated_at"])
                else "CURRENT_TIMESTAMP"
# BRACKET_SURGEON: disabled
#             )

            # Backfill without duping by URL
            conn.execute(
                f""""""
            INSERT OR IGNORE INTO news_intelligence (title, url, summary, created_at)
            SELECT
              {title_col},
                  {url_col},
                  {summary_col},
                  {date_col}
            FROM news_articles;
            """"""
# BRACKET_SURGEON: disabled
#             )
    # Helpful indexes
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_news_intelligence_created_at ON news_intelligence(created_at DESC);"
# BRACKET_SURGEON: disabled
#     )
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ux_news_intelligence_url ON news_intelligence(url);"
# BRACKET_SURGEON: disabled
#     )


def _ensure_discovery_tasks(conn):
    if not _table_exists(conn, "discovery_tasks"):
        conn.execute(
            """"""
        CREATE TABLE discovery_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT,
                payload TEXT,
                status TEXT DEFAULT 'queued',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME
# BRACKET_SURGEON: disabled
#         );
        """"""
# BRACKET_SURGEON: disabled
#         )
        return
    if not _column_exists(conn, "discovery_tasks", "task_name"):
        conn.execute("ALTER TABLE discovery_tasks ADD COLUMN task_name TEXT;")
        if _column_exists(conn, "discovery_tasks", "task_type"):
            conn.execute(
                "UPDATE discovery_tasks SET task_name = task_type WHERE task_name IS NULL;"
# BRACKET_SURGEON: disabled
#             )


def migrate():
    print("[Migrations] DB paths ->", DBS)
    for label, path in DBS.items():
        conn = _connect(path)
        try:
            if label == "rollup":
                _create_revenues(conn)
            if label == "intelligence":
                _ensure_news_intelligence(conn)
            if label == "core":
                _ensure_discovery_tasks(conn)
            conn.commit()
            print(f"[Migrations] {label}: OK @ {path}")
        finally:
            conn.close()