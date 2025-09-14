#!/usr/bin/env python3
"""
TRAE.AI Database Schema Validator
Validates the master database schema and generates comprehensive reports
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any


class DatabaseValidator:
    def __init__(self, db_path: str = "databases/master.db"):
        self.db_path = db_path
        self.connection = None
        self.validation_results = {
            "timestamp": datetime.now().isoformat(),
            "database_path": db_path,
            "validation_status": "pending",
            "total_tables": 0,
            "total_indexes": 0,
            "total_triggers": 0,
            "tables_by_category": {},
            "schema_integrity": {},
            "foreign_key_constraints": [],
            "missing_indexes": [],
            "recommendations": [],
        }

    def connect(self) -> bool:
        """Connect to the database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False

    def get_table_info(self) -> List[Dict[str, Any]]:
        """Get information about all tables"""
        cursor = self.connection.cursor()

        # Get all tables
        cursor.execute(
            """
            SELECT name, type, sql
            FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """
        )

        tables = []
        for row in cursor.fetchall():
            table_name = row["name"]

            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            # Get foreign keys
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()

            # Get indexes
            cursor.execute(f"PRAGMA index_list({table_name})")
            indexes = cursor.fetchall()

            tables.append(
                {
                    "name": table_name,
                    "sql": row["sql"],
                    "columns": [dict(col) for col in columns],
                    "foreign_keys": [dict(fk) for fk in foreign_keys],
                    "indexes": [dict(idx) for idx in indexes],
                }
            )

        return tables

    def categorize_tables(self, tables: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Categorize tables by their purpose"""
        categories = {
            "Core System": [],
            "Content Management": [],
            "Analytics & Performance": [],
            "Monetization": [],
            "User Management": [],
            "API Integration": [],
            "Research & Evidence": [],
            "Automation": [],
            "Financial Management": [],
            "Social Media": [],
            "System Monitoring": [],
            "Compliance & Security": [],
            "Other": [],
        }

        # Define categorization rules
        category_keywords = {
            "Core System": [
                "task_queue",
                "system_config",
                "audit_log",
                "component_health",
                "repair_log",
            ],
            "Content Management": [
                "author_personas",
                "hypocrisy_tracker",
                "content_",
                "format_",
                "evolution_",
            ],
            "Analytics & Performance": [
                "channels",
                "video_performance",
                "performance_",
                "metrics",
                "analytics",
            ],
            "Monetization": [
                "affiliate_",
                "financial_",
                "budget_",
                "payout_",
                "revenue",
            ],
            "User Management": [
                "contacts",
                "audience_",
                "segment_",
                "workflow_executions",
            ],
            "API Integration": ["api_", "cloud_software", "software_", "integration"],
            "Research & Evidence": ["evidence", "intelligence_", "news_", "research"],
            "Automation": ["automation_", "stealth_", "workflow", "campaign"],
            "Financial Management": [
                "allocation_",
                "financial_",
                "budget_",
                "resource_",
            ],
            "Social Media": [
                "comments",
                "engagement_",
                "topic_",
                "user_interactions",
                "promotion_",
            ],
            "System Monitoring": [
                "system_metrics",
                "application_metrics",
                "error_",
                "alert_",
                "monitoring",
            ],
            "Compliance & Security": [
                "compliance_",
                "scan_",
                "enforcement_",
                "violations",
                "detection_",
            ],
        }

        for table in tables:
            table_name = table["name"]
            categorized = False

            for category, keywords in category_keywords.items():
                if any(keyword in table_name for keyword in keywords):
                    categories[category].append(table_name)
                    categorized = True
                    break

            if not categorized:
                categories["Other"].append(table_name)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def validate_foreign_keys(
        self, tables: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate foreign key constraints"""
        table_names = {table["name"] for table in tables}
        fk_issues = []

        for table in tables:
            for fk in table["foreign_keys"]:
                referenced_table = fk["table"]
                if referenced_table not in table_names:
                    fk_issues.append(
                        {
                            "table": table["name"],
                            "column": fk["from"],
                            "references": f"{referenced_table}({fk['to']})",
                            "issue": "Referenced table does not exist",
                        }
                    )

        return fk_issues

    def check_recommended_indexes(
        self, tables: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Check for recommended indexes that might be missing"""
        missing_indexes = []

        # Common patterns that should have indexes
        index_patterns = [
            ("status", "Status columns should be indexed"),
            ("created_at", "Timestamp columns should be indexed"),
            ("updated_at", "Update timestamp columns should be indexed"),
            ("_id", "ID columns should be indexed"),
            ("email", "Email columns should be indexed"),
            ("type", "Type columns should be indexed"),
        ]

        for table in tables:
            table_name = table["name"]
            existing_indexes = {idx["name"] for idx in table["indexes"]}

            for column in table["columns"]:
                column_name = column["name"]

                for pattern, reason in index_patterns:
                    if pattern in column_name.lower():
                        expected_index = f"idx_{table_name}_{column_name}"
                        if expected_index not in existing_indexes:
                            # Check if any index exists on this column
                            has_index = any(
                                column_name in str(idx) for idx in existing_indexes
                            )
                            if not has_index:
                                missing_indexes.append(
                                    {
                                        "table": table_name,
                                        "column": column_name,
                                        "reason": reason,
                                        "suggested_index": expected_index,
                                    }
                                )

        return missing_indexes

    def generate_recommendations(
        self,
        tables: List[Dict[str, Any]],
        fk_issues: List[Dict[str, Any]],
        missing_indexes: List[Dict[str, str]],
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        # Table count recommendation
        if len(tables) > 100:
            recommendations.append(
                f"Consider database partitioning - {len(tables)} tables detected"
            )

        # Foreign key recommendations
        if fk_issues:
            recommendations.append(
                f"Fix {len(fk_issues)} foreign key constraint issues"
            )

        # Index recommendations
        if missing_indexes:
            recommendations.append(
                f"Consider adding {len(missing_indexes)} recommended indexes for better performance"
            )

        # Large table recommendations
        for table in tables:
            if len(table["columns"]) > 20:
                recommendations.append(
                    f"Table '{table['name']}' has {len(table['columns'])} columns - consider normalization"
                )

        # JSON column recommendations
        json_tables = []
        for table in tables:
            json_columns = [
                col["name"] for col in table["columns"] if "JSON" in col["type"]
            ]
            if json_columns:
                json_tables.append(f"{table['name']} ({', '.join(json_columns)})")

        if json_tables:
            recommendations.append(
                f"Monitor JSON column performance in: {', '.join(json_tables[:3])}{'...' if len(json_tables) > 3 else ''}"
            )

        return recommendations

    def validate_schema(self) -> Dict[str, Any]:
        """Perform comprehensive schema validation"""
        if not self.connect():
            self.validation_results["validation_status"] = "failed"
            return self.validation_results

        try:
            # Get table information
            tables = self.get_table_info()
            self.validation_results["total_tables"] = len(tables)

            # Get index count
            cursor = self.connection.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            self.validation_results["total_indexes"] = cursor.fetchone()[0]

            # Get trigger count
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
            self.validation_results["total_triggers"] = cursor.fetchone()[0]

            # Categorize tables
            self.validation_results["tables_by_category"] = self.categorize_tables(
                tables
            )

            # Validate foreign keys
            fk_issues = self.validate_foreign_keys(tables)
            self.validation_results["foreign_key_constraints"] = fk_issues

            # Check for missing indexes
            missing_indexes = self.check_recommended_indexes(tables)
            self.validation_results["missing_indexes"] = missing_indexes

            # Generate recommendations
            recommendations = self.generate_recommendations(
                tables, fk_issues, missing_indexes
            )
            self.validation_results["recommendations"] = recommendations

            # Schema integrity summary
            self.validation_results["schema_integrity"] = {
                "foreign_key_issues": len(fk_issues),
                "missing_recommended_indexes": len(missing_indexes),
                "tables_with_json_columns": len(
                    [
                        t
                        for t in tables
                        if any("JSON" in col["type"] for col in t["columns"])
                    ]
                ),
                "tables_with_foreign_keys": len(
                    [t for t in tables if t["foreign_keys"]]
                ),
                "average_columns_per_table": (
                    sum(len(t["columns"]) for t in tables) / len(tables)
                    if tables
                    else 0
                ),
            }

            self.validation_results["validation_status"] = "completed"

        except Exception as e:
            self.validation_results["validation_status"] = "error"
            self.validation_results["error"] = str(e)

        finally:
            if self.connection:
                self.connection.close()

        return self.validation_results

    def generate_report(self) -> str:
        """Generate a comprehensive validation report"""
        results = self.validate_schema()

        report = []
        report.append("\\n" + "=" * 80)
        report.append("TRAE.AI DATABASE SCHEMA VALIDATION REPORT")
        report.append("=" * 80)
        report.append(f"Timestamp: {results['timestamp']}")
        report.append(f"Database: {results['database_path']}")
        report.append(f"Status: {results['validation_status'].upper()}")
        report.append("")

        # Summary statistics
        report.append("📊 SCHEMA SUMMARY")
        report.append("-" * 40)
        report.append(f"Total Tables: {results['total_tables']}")
        report.append(f"Total Indexes: {results['total_indexes']}")
        report.append(f"Total Triggers: {results['total_triggers']}")
        report.append("")

        # Tables by category
        report.append("📁 TABLES BY CATEGORY")
        report.append("-" * 40)
        for category, tables in results["tables_by_category"].items():
            report.append(f"{category}: {len(tables)} tables")
            for table in sorted(tables)[:5]:  # Show first 5 tables
                report.append(f"  • {table}")
            if len(tables) > 5:
                report.append(f"  ... and {len(tables) - 5} more")
            report.append("")

        # Schema integrity
        integrity = results["schema_integrity"]
        report.append("🔍 SCHEMA INTEGRITY")
        report.append("-" * 40)
        report.append(f"Foreign Key Issues: {integrity.get('foreign_key_issues', 0)}")
        report.append(
            f"Missing Recommended Indexes: {integrity.get('missing_recommended_indexes',
    0)}"
        )
        report.append(
            f"Tables with JSON Columns: {integrity.get('tables_with_json_columns',
    0)}"
        )
        report.append(
            f"Tables with Foreign Keys: {integrity.get('tables_with_foreign_keys',
    0)}"
        )
        report.append(
            f"Average Columns per Table: {integrity.get('average_columns_per_table',
    0):.1f}"
        )
        report.append("")

        # Recommendations
        if results["recommendations"]:
            report.append("💡 RECOMMENDATIONS")
            report.append("-" * 40)
            for i, rec in enumerate(results["recommendations"], 1):
                report.append(f"{i}. {rec}")
            report.append("")

        # Status
        if results["validation_status"] == "completed":
            report.append("✅ DATABASE SCHEMA VALIDATION COMPLETED SUCCESSFULLY")
        else:
            report.append("❌ DATABASE SCHEMA VALIDATION FAILED")
            if "error" in results:
                report.append(f"Error: {results['error']}")

        report.append("=" * 80)

        return "\\n".join(report)

    def save_report(self, filename: str = None) -> str:
        """Save validation report to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
            filename = f"database_validation_report_{timestamp}.txt"

        report = self.generate_report()

        with open(filename, "w") as f:
            f.write(report)

        return filename

    def save_json_report(self, filename: str = None) -> str:
        """Save detailed validation results as JSON"""
        if not filename:
            timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
            filename = f"database_validation_data_{timestamp}.json"

        results = self.validate_schema()

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        return filename


def main():
    """Main execution function"""
    print("🔍 Starting TRAE.AI Database Schema Validation...")

    validator = DatabaseValidator()

    # Generate and display report
    report = validator.generate_report()
    print(report)

    # Save reports
    txt_file = validator.save_report()
    json_file = validator.save_json_report()

    print("\\n📄 Reports saved:")
    print(f"  • Text Report: {txt_file}")
    print(f"  • JSON Data: {json_file}")


if __name__ == "__main__":
    main()
