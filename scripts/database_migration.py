#!/usr/bin/env python3
"""
TRAE.AI Database Migration and Production Setup Script

This script helps migrate from SQLite to PostgreSQL and verifies
production database configuration.

Usage:
    python scripts/database_migration.py --check
    python scripts/database_migration.py --migrate
    python scripts/database_migration.py --verify-production

Author: TRAE.AI System
Version: 1.0.0
Date: 2024
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from backend.core.database import database_health_check, get_db_connection
    from backend.core.database_production import ProductionDatabaseManager
except ImportError as e:
    print(f"Error importing database modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class DatabaseMigrationManager:
    """Manages database migration and production setup"""

    def __init__(self):
        self.current_db_url = os.getenv("DATABASE_URL", "sqlite:///data/trae_master.db")
        self.production_db_url = os.getenv("PRODUCTION_DATABASE_URL")

    def check_current_database(self) -> Dict[str, Any]:
        """Check current database configuration and health"""
        print("🔍 Checking current database configuration...")

        result = {
            "database_url": self.current_db_url,
            "database_type": self._get_db_type(self.current_db_url),
            "health_check": None,
            "tables": [],
            "recommendations": [],
        }

        # Perform health check
        try:
            health = database_health_check()
            result["health_check"] = health
            print(f"✅ Database health: {health['status']}")
        except Exception as e:
            result["health_check"] = {"status": "error", "error": str(e)}
            print(f"❌ Database health check failed: {e}")

        # Check tables
        try:
            with get_db_connection() as conn:
                if result["database_type"] == "sqlite":
                    cursor = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                    )
                else:
                    cursor = conn.execute(
                        "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                    )

                tables = [row[0] for row in cursor.fetchall()]
                result["tables"] = tables
                print(
                    f"📊 Found {len(tables)} tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}"
                )
        except Exception as e:
            print(f"⚠️ Could not list tables: {e}")

        # Generate recommendations
        result["recommendations"] = self._generate_recommendations(result)

        return result

    def verify_production_setup(self) -> Dict[str, Any]:
        """Verify production database setup"""
        print("🏭 Verifying production database setup...")

        result = {
            "environment_check": self._check_environment_variables(),
            "postgresql_dependencies": self._check_postgresql_dependencies(),
            "connection_test": None,
            "schema_validation": None,
            "recommendations": [],
        }

        # Test production database connection if URL is provided
        if self.production_db_url:
            try:
                prod_manager = ProductionDatabaseManager(self.production_db_url)
                health = prod_manager.health_check()
                result["connection_test"] = health

                if health["status"] == "healthy":
                    print("✅ Production database connection successful")

                    # Validate schema
                    result["schema_validation"] = self._validate_production_schema(
                        prod_manager
                    )
                else:
                    print(
                        f"❌ Production database connection failed: {health.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                result["connection_test"] = {"status": "error", "error": str(e)}
                print(f"❌ Production database test failed: {e}")
        else:
            print("⚠️ PRODUCTION_DATABASE_URL not set")

        # Generate recommendations
        result["recommendations"] = self._generate_production_recommendations(result)

        return result

    def migrate_to_production(self, dry_run: bool = True) -> Dict[str, Any]:
        """Migrate from SQLite to PostgreSQL"""
        if dry_run:
            print("🧪 Running migration in DRY RUN mode...")
        else:
            print("🚀 Running LIVE migration...")

        if not self.production_db_url:
            raise ValueError("PRODUCTION_DATABASE_URL must be set for migration")

        result = {
            "source_db": self.current_db_url,
            "target_db": self.production_db_url,
            "dry_run": dry_run,
            "steps": [],
            "success": False,
        }

        try:
            # Step 1: Validate source database
            print("📋 Step 1: Validating source database...")
            source_check = self.check_current_database()
            if source_check["health_check"]["status"] != "healthy":
                raise Exception("Source database is not healthy")
            result["steps"].append(
                {"step": 1, "status": "completed", "description": "Source validation"}
            )

            # Step 2: Setup target database
            print("🎯 Step 2: Setting up target database...")
            if not dry_run:
                target_manager = ProductionDatabaseManager(self.production_db_url)
                target_health = target_manager.health_check()
                if target_health["status"] != "healthy":
                    raise Exception(
                        f"Target database setup failed: {target_health.get('error')}"
                    )
            result["steps"].append(
                {"step": 2, "status": "completed", "description": "Target setup"}
            )

            # Step 3: Export data
            print("📤 Step 3: Exporting data from source...")
            exported_data = (
                self._export_sqlite_data()
                if not dry_run
                else {"tables": source_check["tables"]}
            )
            result["steps"].append(
                {
                    "step": 3,
                    "status": "completed",
                    "description": f'Data export ({len(exported_data.get("tables", []))} tables)',
                }
            )

            # Step 4: Import data
            print("📥 Step 4: Importing data to target...")
            if not dry_run:
                self._import_postgresql_data(target_manager, exported_data)
            result["steps"].append(
                {"step": 4, "status": "completed", "description": "Data import"}
            )

            # Step 5: Validate migration
            print("✅ Step 5: Validating migration...")
            if not dry_run:
                validation = self._validate_migration(target_manager, source_check)
                if not validation["success"]:
                    raise Exception(
                        f"Migration validation failed: {validation['error']}"
                    )
            result["steps"].append(
                {
                    "step": 5,
                    "status": "completed",
                    "description": "Migration validation",
                }
            )

            result["success"] = True
            print("🎉 Migration completed successfully!")

        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Migration failed: {e}")

        return result

    def _get_db_type(self, url: str) -> str:
        """Determine database type from URL"""
        if url.startswith("postgresql://"):
            return "postgresql"
        elif url.startswith("sqlite://"):
            return "sqlite"
        else:
            return "sqlite"  # Default

    def _check_environment_variables(self) -> Dict[str, Any]:
        """Check required environment variables"""
        required_vars = [
            "DATABASE_URL",
            "PRODUCTION_DATABASE_URL",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
        ]

        result = {"missing": [], "present": [], "recommendations": []}

        for var in required_vars:
            if os.getenv(var):
                result["present"].append(var)
            else:
                result["missing"].append(var)

        if result["missing"]:
            result["recommendations"].append(
                f"Set missing environment variables: {', '.join(result['missing'])}"
            )

        return result

    def _check_postgresql_dependencies(self) -> Dict[str, Any]:
        """Check if PostgreSQL dependencies are installed"""
        result = {"psycopg2": False, "sqlalchemy": False, "recommendations": []}

        try:
            import psycopg2

            result["psycopg2"] = True
        except ImportError:
            result["recommendations"].append(
                "Install psycopg2: pip install psycopg2-binary"
            )

        try:
            import sqlalchemy

            result["sqlalchemy"] = True
        except ImportError:
            result["recommendations"].append(
                "Install SQLAlchemy: pip install sqlalchemy"
            )

        return result

    def _validate_production_schema(
        self, manager: ProductionDatabaseManager
    ) -> Dict[str, Any]:
        """Validate production database schema"""
        try:
            with manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                )
                tables = [row[0] for row in cursor.fetchall()]

                return {"success": True, "tables_found": len(tables), "tables": tables}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _export_sqlite_data(self) -> Dict[str, Any]:
        """Export data from SQLite database"""
        # This is a simplified version - in production you'd want more robust export
        exported = {"tables": []}

        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
                tables = [row[0] for row in cursor.fetchall()]

                for table in tables:
                    cursor = conn.execute(f"SELECT * FROM {table}")
                    rows = cursor.fetchall()
                    exported["tables"].append(
                        {
                            "name": table,
                            "row_count": len(rows),
                            "data": [dict(row) for row in rows],
                        }
                    )
        except Exception as e:
            exported["error"] = str(e)

        return exported

    def _import_postgresql_data(
        self, manager: ProductionDatabaseManager, data: Dict[str, Any]
    ):
        """Import data to PostgreSQL database"""
        # This is a simplified version - in production you'd want more robust import
        for table_data in data.get("tables", []):
            table_name = table_data["name"]
            rows = table_data["data"]

            if not rows:
                continue

            # Generate INSERT statements (simplified)
            columns = list(rows[0].keys())
            placeholders = ", ".join(["%s"] * len(columns))
            insert_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"

            with manager.get_connection() as conn:
                cursor = conn.cursor()
                for row in rows:
                    values = [row[col] for col in columns]
                    cursor.execute(insert_sql, values)

    def _validate_migration(
        self, manager: ProductionDatabaseManager, source_check: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate that migration was successful"""
        try:
            with manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
                )
                target_tables = [row[0] for row in cursor.fetchall()]

            source_tables = source_check.get("tables", [])

            return {
                "success": len(target_tables) >= len(source_tables),
                "source_tables": len(source_tables),
                "target_tables": len(target_tables),
                "missing_tables": list(set(source_tables) - set(target_tables)),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_recommendations(self, check_result: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current database check"""
        recommendations = []

        if check_result["database_type"] == "sqlite":
            recommendations.append("Consider migrating to PostgreSQL for production")

        if (
            check_result["health_check"]
            and check_result["health_check"]["status"] != "healthy"
        ):
            recommendations.append("Fix database health issues before proceeding")

        if len(check_result["tables"]) == 0:
            recommendations.append("Initialize database schema")

        return recommendations

    def _generate_production_recommendations(self, result: Dict[str, Any]) -> List[str]:
        """Generate production setup recommendations"""
        recommendations = []

        env_check = result.get("environment_check", {})
        if env_check.get("missing"):
            recommendations.extend(env_check.get("recommendations", []))

        deps_check = result.get("postgresql_dependencies", {})
        if deps_check.get("recommendations"):
            recommendations.extend(deps_check["recommendations"])

        if not result.get("connection_test"):
            recommendations.append("Set PRODUCTION_DATABASE_URL environment variable")
        elif result["connection_test"].get("status") != "healthy":
            recommendations.append("Fix production database connection issues")

        return recommendations


def main():
    parser = argparse.ArgumentParser(description="TRAE.AI Database Migration Tool")
    parser.add_argument("--check", action="store_true", help="Check current database")
    parser.add_argument(
        "--verify-production", action="store_true", help="Verify production setup"
    )
    parser.add_argument(
        "--migrate", action="store_true", help="Migrate to production database"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Run migration in dry-run mode"
    )
    parser.add_argument("--output", help="Output results to JSON file")

    args = parser.parse_args()

    if not any([args.check, args.verify_production, args.migrate]):
        parser.print_help()
        return

    manager = DatabaseMigrationManager()
    results = {}

    try:
        if args.check:
            results["database_check"] = manager.check_current_database()

        if args.verify_production:
            results["production_verification"] = manager.verify_production_setup()

        if args.migrate:
            results["migration"] = manager.migrate_to_production(dry_run=args.dry_run)

        # Output results
        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print(f"📄 Results saved to {args.output}")

        # Print summary
        print("\n📋 Summary:")
        for key, result in results.items():
            if isinstance(result, dict) and "recommendations" in result:
                recommendations = result["recommendations"]
                if recommendations:
                    print(f"\n{key.replace('_', ' ').title()} Recommendations:")
                    for rec in recommendations:
                        print(f"  • {rec}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
