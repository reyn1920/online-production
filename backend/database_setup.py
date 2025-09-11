#!/usr/bin/env python3
"""
Database Setup and Migration Module

This module handles database schema migrations and ensures the database
is in the correct state for the application to function properly.
"""

import logging
import os
import sqlite3
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)


def get_database_path() -> str:
    """Get the database path from environment or use default"""
    return os.getenv("DATABASE_PATH", "backend/database/intelligence.db")


def ensure_database_directory():
    """Ensure the database directory exists"""
    db_path = get_database_path()
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        logger.info(f"Created database directory: {db_dir}")


def run_database_migration() -> bool:
    """
    Run database migration to ensure all required tables exist with correct schema.

    Returns:
        bool: True if migration was successful, False otherwise
    """
    try:
        ensure_database_directory()
        db_path = get_database_path()

        logger.info(f"Starting database migration for: {db_path}")

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Create news_intelligence table (the correct table name expected by the code)
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS news_intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    url TEXT,
                    source TEXT,
                    published_date TEXT,
                    category TEXT,
                    sentiment REAL,
                    relevance_score REAL,
                    keywords TEXT,
                    summary TEXT,
                    task_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Check if news_articles table exists and migrate data if needed
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='news_articles'
            """
            )

            if cursor.fetchone():
                logger.info("Found existing news_articles table, migrating data...")

                # Get the schema of news_articles table
                cursor.execute("PRAGMA table_info(news_articles)")
                columns = [row[1] for row in cursor.fetchall()]

                # Migrate data from news_articles to news_intelligence
                # Only migrate columns that exist in both tables
                common_columns = []
                target_columns = [
                    "title",
                    "content",
                    "url",
                    "source",
                    "published_date",
                    "category",
                    "sentiment",
                    "relevance_score",
                    "keywords",
                    "summary",
                    "task_name",
                    "created_at",
                    "updated_at",
                ]

                for col in target_columns:
                    if col in columns:
                        common_columns.append(col)

                if common_columns:
                    columns_str = ", ".join(common_columns)
                    cursor.execute(
                        f"""
                        INSERT OR IGNORE INTO news_intelligence ({columns_str})
                        SELECT {columns_str} FROM news_articles
                    """
                    )

                    migrated_count = cursor.rowcount
                    logger.info(
                        f"Migrated {migrated_count} records from news_articles to news_intelligence"
                    )

                # Rename the old table as backup
                cursor.execute(
                    """
                    ALTER TABLE news_articles RENAME TO news_articles_backup
                """
                )
                logger.info("Renamed news_articles table to news_articles_backup")

            # Ensure task_name column exists (add if missing)
            cursor.execute("PRAGMA table_info(news_intelligence)")
            columns = [row[1] for row in cursor.fetchall()]

            if "task_name" not in columns:
                cursor.execute(
                    """
                    ALTER TABLE news_intelligence ADD COLUMN task_name TEXT
                """
                )
                logger.info("Added task_name column to news_intelligence table")

            # Create indexes for better performance
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_intelligence_task_name 
                ON news_intelligence(task_name)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_intelligence_created_at 
                ON news_intelligence(created_at)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_news_intelligence_category 
                ON news_intelligence(category)
            """
            )

            # Create other required tables
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    task_data TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL,
                    metric_unit TEXT,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # Create system_health table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS system_health (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    cpu_usage REAL NOT NULL,
                    memory_usage REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    agent_status TEXT NOT NULL,
                    service_status TEXT NOT NULL,
                    error_count INTEGER NOT NULL,
                    uptime_seconds INTEGER NOT NULL,
                    health_score REAL NOT NULL
                )
            """
            )

            # Add status column to system_health table if missing
            cursor.execute("PRAGMA table_info(system_health)")
            columns = [col[1] for col in cursor.fetchall()]
            if "status" not in columns:
                logger.info("Migrating system_health: adding 'status' column...")
                cursor.execute("ALTER TABLE system_health ADD COLUMN status TEXT;")

            conn.commit()
            logger.info("Database migration completed successfully")
            return True

    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        return False


def verify_database_schema() -> bool:
    """
    Verify that the database schema is correct.

    Returns:
        bool: True if schema is correct, False otherwise
    """
    try:
        db_path = get_database_path()

        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            # Check if news_intelligence table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='news_intelligence'
            """
            )

            if not cursor.fetchone():
                logger.error("news_intelligence table does not exist")
                return False

            # Check if task_name column exists
            cursor.execute("PRAGMA table_info(news_intelligence)")
            columns = [row[1] for row in cursor.fetchall()]

            if "task_name" not in columns:
                logger.error("task_name column missing from news_intelligence table")
                return False

            logger.info("Database schema verification passed")
            return True

    except Exception as e:
        logger.error(f"Database schema verification failed: {e}")
        return False


if __name__ == "__main__":
    # Configure logging for standalone execution
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    print("Running database migration...")
    success = run_database_migration()

    if success:
        print("Database migration completed successfully")

        print("Verifying database schema...")
        if verify_database_schema():
            print("Database schema verification passed")
        else:
            print("Database schema verification failed")
    else:
        print("Database migration failed")
