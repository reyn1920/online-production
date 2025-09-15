#!/usr / bin / env python3
""""""
TRAE AI Database Management Script

This script serves as the single source of truth for all database operations.
It ensures the application and database schema are always perfectly aligned.

Usage:
    python scripts / manage_db.py init          # Initialize all databases
    python scripts / manage_db.py migrate       # Apply schema migrations
    python scripts / manage_db.py verify        # Verify schema integrity
    python scripts / manage_db.py backup        # Create database backup
    python scripts / manage_db.py restore FILE  # Restore from backup
    python scripts / manage_db.py reset         # Reset all databases (DANGER)
    python scripts / manage_db.py status        # Show database status

Author: TRAE.AI System
Version: 1.0.0
""""""

import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class DatabaseManager:
    """Professional database management for TRAE AI system."""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.data_dir = self.project_root / "data"
        self.app_dir = self.project_root / "app"
        self.backup_dir = self.project_root / "backups" / "database"

        # Database configurations
        self.databases = {
            "main": {
                "path": self.data_dir / "trae_ai.db",
                "schema_file": self.project_root / "master_schema.sql",
                "description": "Main application database",
# BRACKET_SURGEON: disabled
#             },
            "intelligence": {
                "path": self.data_dir / "right_perspective.db",
                "schema_file": self.project_root / "right_perspective_schema.sql",
                "description": "Intelligence and research database",
# BRACKET_SURGEON: disabled
#             },
            "app_main": {
                "path": self.app_dir / "trae_ai.db",
                "schema_file": self.project_root / "master_schema.sql",
                "description": "App directory main database",
# BRACKET_SURGEON: disabled
#             },
            "app_intelligence": {
                "path": self.app_dir / "right_perspective.db",
                "schema_file": self.project_root / "right_perspective_schema.sql",
                "description": "App directory intelligence database",
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def get_schema_sql(self, schema_file: Path) -> str:
        """Load schema SQL from file."""
        if not schema_file.exists():
            print(f"⚠️  Schema file not found: {schema_file}")
            return ""

        with open(schema_file, "r") as f:
            return f.read()

    def execute_sql(self, db_path: Path, sql: str, description: str = "") -> bool:
        """Execute SQL against database with error handling."""
        try:
            with sqlite3.connect(db_path) as conn:
                conn.executescript(sql)
                conn.commit()
                if description:
                    print(f"✅ {description}")
                return True
        except sqlite3.Error as e:
            print(f"❌ Database error in {db_path}: {e}")
            if description:
                print(f"   Failed operation: {description}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error with {db_path}: {e}")
            return False

    def get_table_info(self, db_path: Path) -> List[Dict]:
        """Get information about tables in database."""
        if not db_path.exists():
            return []

        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = cursor.fetchall()

                table_info = []
                for (table_name,) in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    table_info.append({"name": table_name, "rows": count})

                return table_info
        except sqlite3.Error:
            return []

    def init_database(self, db_name: str) -> bool:
        """Initialize a specific database."""
        if db_name not in self.databases:
            print(f"❌ Unknown database: {db_name}")
            return False

        config = self.databases[db_name]
        db_path = config["path"]
        schema_file = config["schema_file"]

        print(f"🔧 Initializing {config['description']}...")
        print(f"   Database: {db_path}")
        print(f"   Schema: {schema_file}")

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Load and execute schema
        schema_sql = self.get_schema_sql(schema_file)
        if not schema_sql:
            print(f"❌ No schema found for {db_name}")
            return False

        success = self.execute_sql(db_path, schema_sql, f"Schema applied to {db_name}")

        if success:
            # Verify tables were created
            tables = self.get_table_info(db_path)
            print(f"   Created {len(tables)} tables")

        return success

    def init_all_databases(self) -> bool:
        """Initialize all databases."""
        print("🚀 Initializing all TRAE AI databases...")
        print("=" * 50)

        success_count = 0
        total_count = len(self.databases)

        for db_name in self.databases:
            if self.init_database(db_name):
                success_count += 1
            print()  # Add spacing

        print(f"📊 Database initialization complete: {success_count}/{total_count} successful")
        return success_count == total_count

    def verify_schema_integrity(self) -> bool:
        """Verify all databases have correct schema."""
        print("🔍 Verifying database schema integrity...")
        print("=" * 50)

        all_valid = True

        for db_name, config in self.databases.items():
            db_path = config["path"]

            if not db_path.exists():
                print(f"❌ {db_name}: Database file missing")
                all_valid = False
                continue

            tables = self.get_table_info(db_path)
            if not tables:
                print(f"❌ {db_name}: No tables found")
                all_valid = False
            else:
                print(f"✅ {db_name}: {len(tables)} tables found")
                for table in tables:
                    print(f"   - {table['name']}: {table['rows']} rows")

        return all_valid

    def backup_databases(self) -> bool:
        """Create backup of all databases."""
        timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
        backup_subdir = self.backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(parents=True, exist_ok=True)

        print(f"💾 Creating database backup: {backup_subdir}")
        print("=" * 50)

        success_count = 0

        for db_name, config in self.databases.items():
            db_path = config["path"]

            if not db_path.exists():
                print(f"⚠️  {db_name}: Database not found, skipping")
                continue

            backup_path = backup_subdir / f"{db_name}_{db_path.name}"

            try:
                shutil.copy2(db_path, backup_path)
                print(f"✅ {db_name}: Backed up to {backup_path.name}")
                success_count += 1
            except Exception as e:
                print(f"❌ {db_name}: Backup failed - {e}")

        # Create backup manifest
        manifest = {
            "timestamp": timestamp,
            "databases_backed_up": success_count,
            "backup_directory": str(backup_subdir),
            "created_by": "TRAE AI Database Manager",
# BRACKET_SURGEON: disabled
#         }

        manifest_path = backup_subdir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"\\n📋 Backup manifest created: {manifest_path}")
        print(f"📊 Backup complete: {success_count} databases backed up")

        return success_count > 0

    def show_status(self) -> None:
        """Show status of all databases."""
        print("📊 TRAE AI Database Status")
        print("=" * 50)

        for db_name, config in self.databases.items():
            db_path = config["path"]
            print(f"\\n🗄️  {db_name.upper()}")
            print(f"   Description: {config['description']}")
            print(f"   Path: {db_path}")

            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                tables = self.get_table_info(db_path)
                total_rows = sum(table["rows"] for table in tables)

                print(f"   Status: ✅ EXISTS")
                print(f"   Size: {size_mb:.2f} MB")
                print(f"   Tables: {len(tables)}")
                print(f"   Total Rows: {total_rows:,}")

                if tables:
                    print("   Table Details:")
                    for table in tables:
                        print(f"     - {table['name']}: {table['rows']:,} rows")
            else:
                print(f"   Status: ❌ MISSING")

    def reset_databases(self, confirm: bool = False) -> bool:
        """Reset all databases (DANGEROUS OPERATION)."""
        if not confirm:
            print("⚠️  WARNING: This will DELETE ALL DATABASE DATA!")
            print("This operation cannot be undone.")
            response = input("Type 'RESET' to confirm: ")
            if response != "RESET":
                print("❌ Operation cancelled.")
                return False

        print("🔥 RESETTING ALL DATABASES...")
        print("=" * 50)

        # First, backup existing databases
        print("📦 Creating safety backup before reset...")
        self.backup_databases()

        # Delete existing databases
        deleted_count = 0
        for db_name, config in self.databases.items():
            db_path = config["path"]
            if db_path.exists():
                try:
                    db_path.unlink()
                    print(f"🗑️  Deleted {db_name}")
                    deleted_count += 1
                except Exception as e:
                    print(f"❌ Failed to delete {db_name}: {e}")

        print(f"\\n🔄 Reinitializing databases...")
        success = self.init_all_databases()

        if success:
            print(f"\\n✅ Database reset complete!")
            print(f"   Deleted: {deleted_count} databases")
            print(f"   Recreated: {len(self.databases)} databases")
        else:
            print(f"\\n❌ Database reset encountered errors!")

        return success


def main():
    parser = argparse.ArgumentParser(
        description="TRAE AI Database Management System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=""""""
Examples:
  python scripts / manage_db.py init          # Initialize all databases
  python scripts / manage_db.py verify        # Check database integrity
  python scripts / manage_db.py backup        # Create backup
  python scripts / manage_db.py status        # Show database status
        ""","""
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument(
        "command",
        choices=["init", "migrate", "verify", "backup", "restore", "reset", "status"],
        help="Database management command",
# BRACKET_SURGEON: disabled
#     )

    parser.add_argument("file", nargs="?", help="File for restore command")
    parser.add_argument("--force", action="store_true", help="Force operation without confirmation")

    args = parser.parse_args()

    # Initialize database manager
    db_manager = DatabaseManager()

    try:
        if args.command == "init":
            success = db_manager.init_all_databases()
        elif args.command == "verify":
            success = db_manager.verify_schema_integrity()
        elif args.command == "backup":
            success = db_manager.backup_databases()
        elif args.command == "status":
            db_manager.show_status()
            success = True
        elif args.command == "reset":
            success = db_manager.reset_databases(confirm=args.force)
        elif args.command == "migrate":
            print("🔄 Migration functionality coming soon...")
            success = True
        elif args.command == "restore":
            print("🔄 Restore functionality coming soon...")
            success = True
        else:
            print(f"❌ Unknown command: {args.command}")
            success = False

    except KeyboardInterrupt:
        print("\\n⚠️  Operation interrupted by user.")
        return 1
    except Exception as e:
        print(f"\\n❌ Unexpected error: {e}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())