#!/usr / bin / env python3
"""
Database Schema Fix Script
Adds missing columns to resolve dashboard errors:
- 'category' column to affiliate_programs table
- 'name' column to api_registry table (as alias for api_name)
"""

import os
import sqlite3
import sys
from pathlib import Path


def fix_database_schema():
    """Fix database schema by adding missing columns."""

    # Database paths
    main_db = "trae_ai.db"
    intelligence_db = "right_perspective.db"

    print("🔧 Starting database schema fixes...")

    # Fix main database (trae_ai.db)
    if os.path.exists(main_db):
        print(f"📊 Fixing schema in {main_db}...")
        try:
            conn = sqlite3.connect(main_db)
            cursor = conn.cursor()

            # Check if affiliate_programs table exists and add category column
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='affiliate_programs'"
            )
            if cursor.fetchone():
                # Check if category column already exists
                cursor.execute("PRAGMA table_info(affiliate_programs)")
                columns = [col[1] for col in cursor.fetchall()]

                if "category" not in columns:
                    print(
                        "  ➕ Adding 'category' column to affiliate_programs table..."
                    )
                    cursor.execute(
                        "ALTER TABLE affiliate_programs ADD COLUMN category TEXT DEFAULT 'General'"
                    )
                    print("  ✅ Category column added successfully")
                else:
                    print("  ℹ️  Category column already exists in affiliate_programs")

            # Check if api_registry table exists and add name column as alias
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='api_registry'"
            )
            if cursor.fetchone():
                # Check if name column already exists
                cursor.execute("PRAGMA table_info(api_registry)")
                columns = [col[1] for col in cursor.fetchall()]

                if "name" not in columns:
                    print("  ➕ Adding 'name' column to api_registry table...")
                    # Add name column and populate it with api_name values
                    cursor.execute("ALTER TABLE api_registry ADD COLUMN name TEXT")
                    cursor.execute(
                        "UPDATE api_registry SET name = api_name WHERE name IS NULL"
                    )
                    print("  ✅ Name column added and populated successfully")
                else:
                    print("  ℹ️  Name column already exists in api_registry")

            conn.commit()
            conn.close()
            print(f"✅ {main_db} schema fixes completed")

        except Exception as e:
            print(f"❌ Error fixing {main_db}: {e}")
            return False
    else:
        print(f"⚠️  {main_db} not found, skipping...")

    # Fix intelligence database (right_perspective.db)
    if os.path.exists(intelligence_db):
        print(f"📊 Fixing schema in {intelligence_db}...")
        try:
            conn = sqlite3.connect(intelligence_db)
            cursor = conn.cursor()

            # Check if affiliate_programs table exists and add category column
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='affiliate_programs'"
            )
            if cursor.fetchone():
                # Check if category column already exists
                cursor.execute("PRAGMA table_info(affiliate_programs)")
                columns = [col[1] for col in cursor.fetchall()]

                if "category" not in columns:
                    print(
                        "  ➕ Adding 'category' column to affiliate_programs table..."
                    )
                    cursor.execute(
                        "ALTER TABLE affiliate_programs ADD COLUMN category TEXT DEFAULT 'General'"
                    )
                    print("  ✅ Category column added successfully")
                else:
                    print("  ℹ️  Category column already exists in affiliate_programs")

            # Check if api_registry table exists and add name column
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='api_registry'"
            )
            if cursor.fetchone():
                # Check if name column already exists
                cursor.execute("PRAGMA table_info(api_registry)")
                columns = [col[1] for col in cursor.fetchall()]

                if "name" not in columns:
                    print("  ➕ Adding 'name' column to api_registry table...")
                    # Add name column and populate it with service_name or api_name values
                    cursor.execute("ALTER TABLE api_registry ADD COLUMN name TEXT")

                    # Try to populate from service_name first, then api_name
                    if "service_name" in columns:
                        cursor.execute(
                            "UPDATE api_registry SET name = service_name WHERE name IS NULL"
                        )
                    elif "api_name" in columns:
                        cursor.execute(
                            "UPDATE api_registry SET name = api_name WHERE name IS NULL"
                        )

                    print("  ✅ Name column added and populated successfully")
                else:
                    print("  ℹ️  Name column already exists in api_registry")

            conn.commit()
            conn.close()
            print(f"✅ {intelligence_db} schema fixes completed")

        except Exception as e:
            print(f"❌ Error fixing {intelligence_db}: {e}")
            return False
    else:
        print(f"⚠️  {intelligence_db} not found, skipping...")

    print("\n🎉 Database schema fixes completed successfully!")
    print("\n📋 Summary of changes:")
    print("  • Added 'category' column to affiliate_programs tables")
    print("  • Added 'name' column to api_registry tables")
    print("  • Populated new columns with appropriate default values")
    print("\n✅ Dashboard errors should now be resolved.")

    return True

if __name__ == "__main__":
    success = fix_database_schema()
    sys.exit(0 if success else 1)
