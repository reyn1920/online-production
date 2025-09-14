#!/usr/bin/env python3
"""
Ensures minimal tables exist in your main DB used by the dashboard checks.
Add - only; if a table exists this is a no - op.
"""

import sqlite3
from pathlib import Path

# pick the DB you are using in the checks; you showed right_perspective.db
DB = Path("right_perspective.db")

DDL = {
    "reports": """
      CREATE TABLE IF NOT EXISTS reports (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_type TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
      );
    """,
    "content_performance": """
      CREATE TABLE IF NOT EXISTS content_performance (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT,
            views INTEGER DEFAULT 0,
            engagement_rate REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    """,
    # Harmless extras that some suites expect. Safe if already present.
    "generated_reports": """
      CREATE TABLE IF NOT EXISTS generated_reports (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    """,
    "platform_monitoring_log": """
      CREATE TABLE IF NOT EXISTS platform_monitoring_log (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT, message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      );
    """,
}


def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    cur = con.cursor()
    for name, ddl in DDL.items():
        cur.execute(ddl)
    con.commit()
    con.close()
    print(f"OK: ensured tables exist in {DB}")


if __name__ == "__main__":
    main()
