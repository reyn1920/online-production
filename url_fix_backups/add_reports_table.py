#!/usr / bin / env python3
""""""
Database Migration Script: Add generated_reports table
This script adds the new generated_reports table to the existing right_perspective.db database.
""""""

import os
import sqlite3
from datetime import datetime


def add_reports_table():
    """Add the generated_reports table to the database."""
    db_path = "right_perspective.db"

    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database...")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create the generated_reports table
        cursor.execute(
            """"""
            CREATE TABLE IF NOT EXISTS generated_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    key_headline TEXT,
                    date_range_start DATE,
                    date_range_end DATE,
                    generated_by TEXT,
                    generation_parameters TEXT,
                    file_size_bytes INTEGER,
                    status TEXT DEFAULT 'active',
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# BRACKET_SURGEON: disabled
#             )
        """"""
# BRACKET_SURGEON: disabled
#         )

        # Check if table was created successfully
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='generated_reports'"
# BRACKET_SURGEON: disabled
#         )
        if cursor.fetchone():
            print("✅ generated_reports table created successfully")
        else:
            print("❌ Failed to create generated_reports table")
            return False

        # Add some sample data for testing
        sample_reports = [
            {
                "report_type": "daily_performance",
                "title": "Daily Performance Report - Sample",
                "content": "# Daily Performance Report\\n\\n## Key Metrics\\n- Total Views: 1,250\\n- Engagement Rate: 4.2%\\n- Revenue: $45.30\\n\\n## Top Performing Content\\n1. Tech Review Video - 450 views\\n2. Tutorial Series - 320 views\\n3. News Commentary - 280 views","
                "key_headline": "Daily performance shows 15% growth in viewership with tech content leading",
                "date_range_start": "2024 - 01 - 20",
                "date_range_end": "2024 - 01 - 20",
                "generated_by": "Performance Agent",
                "generation_parameters": '{"metrics": ["views", "engagement", "revenue"], "channels": ["all"]}',
                "file_size_bytes": 245,
                "tags": "daily,performance,metrics",
# BRACKET_SURGEON: disabled
#             },
            {
                "report_type": "weekly_growth",
                "title": "Weekly Growth Analysis - Sample",
                "content": "# Weekly Growth Analysis\\n\\n## Growth Summary\\n- Subscriber Growth: +127 new subscribers\\n- View Growth: +23% compared to last week\\n- Revenue Growth: +18%\\n\\n## Channel Performance\\n- Tech Channel: Leading with 40% of total views\\n- News Channel: Steady growth at 25%\\n- Tutorial Channel: 35% of views","
                "key_headline": "Weekly growth accelerating with 23% increase in views, tech channel dominating",
                "date_range_start": "2024 - 01 - 14",
                "date_range_end": "2024 - 01 - 20",
                "generated_by": "Growth Agent",
                "generation_parameters": '{"period": "weekly", "comparison": "previous_week"}',
                "file_size_bytes": 312,
                "tags": "weekly,growth,analysis",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         ]

        for report in sample_reports:
            cursor.execute(
                """"""
                INSERT INTO generated_reports
                (report_type,
    title,
    content,
    key_headline,
    date_range_start,
    date_range_end,
# BRACKET_SURGEON: disabled
#                     generated_by, generation_parameters, file_size_bytes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                (
                    report["report_type"],
                    report["title"],
                    report["content"],
                    report["key_headline"],
                    report["date_range_start"],
                    report["date_range_end"],
                    report["generated_by"],
                    report["generation_parameters"],
                    report["file_size_bytes"],
                    report["tags"],
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

        conn.commit()
        print(f"✅ Added {len(sample_reports)} sample reports for testing")

        # Verify the data
        cursor.execute("SELECT COUNT(*) FROM generated_reports")
        count = cursor.fetchone()[0]
        print(f"✅ Database now contains {count} reports")

        conn.close()
        return True

    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("Adding generated_reports table to database...")
    success = add_reports_table()
    if success:
        print("\\n🎉 Migration completed successfully!")
    else:
        print("\\n💥 Migration failed!")