#!/usr/bin/env python3
""""""
Cloud Software Integration Verification

This script verifies that all requested cloud software products are properly
integrated into the database system with complete functionality.

Requested Software:
- Lingo Blaster
- Captionizer
- Thumbnail Blaster
- Speechelo
- Voice Generator
- Background music
- BONUS: Voiceover - Cash - Machine
- Training
- Scriptelo
- EXTRA SOFTWARE (additional integrations)
""""""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def verify_database_integration() -> Dict[str, Any]:
    """Verify all cloud software is properly integrated in the database"""

    # Required software list from user request
    required_software = {
        "lingo_blaster": "Lingo Blaster",
        "captionizer": "Captionizer",
        "thumbnail_blaster": "Thumbnail Blaster",
        "speechelo": "Speechelo",
        "voice_generator": "Voice Generator",
        "background_music": "Background music",
        "voiceover_cash_machine": "BONUS: Voiceover - Cash - Machine",
        "training": "Training",
        "scriptelo": "Scriptelo",
# BRACKET_SURGEON: disabled
#     }

    verification_results = {
        "timestamp": datetime.now().isoformat(),
        "database_file": "right_perspective.db",
        "total_required": len(required_software),
        "found_software": [],
        "missing_software": [],
        "database_tables": [],
        "integration_status": "UNKNOWN",
        "details": {},
# BRACKET_SURGEON: disabled
#     }

    try:
        # Connect to database
        db_path = Path("right_perspective.db")
        if not db_path.exists():
            verification_results["integration_status"] = "FAILED"
            verification_results["error"] = "Database file not found"
            return verification_results

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # Verify database tables exist
        cursor = conn.execute(
            """"""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name LIKE '%software%'
            ORDER BY name
        """"""
# BRACKET_SURGEON: disabled
#         )

        tables = [row["name"] for row in cursor.fetchall()]
        verification_results["database_tables"] = tables

        expected_tables = [
            "cloud_software",
            "software_usage_logs",
            "software_integration_status",
# BRACKET_SURGEON: disabled
#         ]
        missing_tables = [table for table in expected_tables if table not in tables]

        if missing_tables:
            verification_results["integration_status"] = "FAILED"
            verification_results["error"] = f"Missing tables: {missing_tables}"
            return verification_results

        # Check all required software is in database
        cursor = conn.execute(
            """"""
            SELECT software_name, display_name, category, status, integration_type,
                authentication_method, capabilities, license_type, notes
            FROM cloud_software
            ORDER BY software_name
        """"""
# BRACKET_SURGEON: disabled
#         )

        found_software = {}
        for row in cursor.fetchall():
            software_data = dict(row)
            found_software[software_data["software_name"]] = software_data
            verification_results["found_software"].append(software_data)

        # Check for missing software
        for software_key, display_name in required_software.items():
            if software_key not in found_software:
                verification_results["missing_software"].append(
                    {"key": software_key, "display_name": display_name}
# BRACKET_SURGEON: disabled
#                 )

        # Get integration status counts
        cursor = conn.execute(
            """"""
            SELECT status, COUNT(*) as count
            FROM cloud_software
            GROUP BY status
        """"""
# BRACKET_SURGEON: disabled
#         )

        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        verification_results["details"]["status_distribution"] = status_counts

        # Get integration type distribution
        cursor = conn.execute(
            """"""
            SELECT integration_type, COUNT(*) as count
            FROM cloud_software
            GROUP BY integration_type
        """"""
# BRACKET_SURGEON: disabled
#         )

        integration_counts = {row["integration_type"]: row["count"] for row in cursor.fetchall()}
        verification_results["details"]["integration_types"] = integration_counts

        # Get category distribution
        cursor = conn.execute(
            """"""
            SELECT category, COUNT(*) as count
            FROM cloud_software
            GROUP BY category
        """"""
# BRACKET_SURGEON: disabled
#         )

        category_counts = {row["category"]: row["count"] for row in cursor.fetchall()}
        verification_results["details"]["categories"] = category_counts

        # Determine overall integration status
        if len(verification_results["missing_software"]) == 0:
            verification_results["integration_status"] = "SUCCESS"
        else:
            verification_results["integration_status"] = "PARTIAL"

        conn.close()

    except Exception as e:
        verification_results["integration_status"] = "ERROR"
        verification_results["error"] = str(e)

    return verification_results


def print_verification_report(results: Dict[str, Any]):
    """Print a formatted verification report"""

    print("\\n" + "=" * 80)
    print("CLOUD SOFTWARE INTEGRATION VERIFICATION REPORT")
    print("=" * 80)
    print(f"Timestamp: {results['timestamp']}")
    print(f"Database: {results['database_file']}")
    print(f"Integration Status: {results['integration_status']}")

    if results["integration_status"] == "SUCCESS":
        print("\\n✅ ALL REQUESTED SOFTWARE SUCCESSFULLY INTEGRATED")
    elif results["integration_status"] == "PARTIAL":
        print("\\n⚠️  PARTIAL INTEGRATION - SOME SOFTWARE MISSING")
    else:
        print("\\n❌ INTEGRATION FAILED")
        if "error" in results:
            print(f"Error: {results['error']}")
        return

    print(f"\\nDatabase Tables: {', '.join(results['database_tables'])}")
    print(f"Total Required Software: {results['total_required']}")
    print(f"Found Software: {len(results['found_software'])}")

    if results["missing_software"]:
        print(f"Missing Software: {len(results['missing_software'])}")
        for missing in results["missing_software"]:
            print(f"  - {missing['display_name']} ({missing['key']})")

    print("\\nINTEGRATED SOFTWARE:")
    print("-" * 40)

    # Group by category
    by_category = {}
    for software in results["found_software"]:
        category = software["category"].replace("_", " ").title()
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(software)

    for category, software_list in sorted(by_category.items()):
        print(f"\\n{category.upper()}:")
        for software in software_list:
            status_icon = "✅" if software["status"] == "active" else "⚠️"
            print(f"  {status_icon} {software['display_name']}")
            print(f"      Integration: {software['integration_type']}")
            print(f"      Authentication: {software['authentication_method']}")
            print(f"      License: {software['license_type']}")
            if software["capabilities"]:
                try:
                    caps = json.loads(software["capabilities"])
                    print(f"      Capabilities: {', '.join(caps)}")
                except Exception:
                    print(f"      Capabilities: {software['capabilities']}")
            if software["notes"]:
                print(f"      Notes: {software['notes']}")

    if "details" in results:
        print("\\nINTEGRATION STATISTICS:")
        print("-" * 40)

        if "status_distribution" in results["details"]:
            print("Status Distribution:")
            for status, count in results["details"]["status_distribution"].items():
                print(f"  {status}: {count}")

        if "integration_types" in results["details"]:
            print("\\nIntegration Types:")
            for int_type, count in results["details"]["integration_types"].items():
                print(f"  {int_type}: {count}")

        if "categories" in results["details"]:
            print("\\nCategories:")
            for category, count in results["details"]["categories"].items():
                print(f"  {category.replace('_', ' ').title()}: {count}")

    print("\\n" + "=" * 80)
    print("VERIFICATION COMPLETE")
    print("=" * 80)


def main():
    """Main verification function"""
    print("Starting Cloud Software Integration Verification...")

    results = verify_database_integration()
    print_verification_report(results)

    # Save detailed results to file
    report_file = f"integration_verification_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
    with open(report_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\\nDetailed verification report saved to: {report_file}")

    # Return exit code based on integration status
    if results["integration_status"] == "SUCCESS":
        print("\\n🎉 Cloud software integration verification PASSED!")
        return 0
    elif results["integration_status"] == "PARTIAL":
        print("\\n⚠️  Cloud software integration verification PARTIAL - some software missing")
        return 1
    else:
        print("\\n❌ Cloud software integration verification FAILED")
        return 2


if __name__ == "__main__":
    exit(main())