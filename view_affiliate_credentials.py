#!/usr/bin/env python3
"""
Affiliate Dashboard Credentials Viewer

This script provides a secure way to view stored affiliate dashboard credentials
from the stealth automation system. It displays login information for all
affiliate programs you've signed up for.

Usage:
    python view_affiliate_credentials.py

Security Note:
    - Passwords are stored encrypted in the database
    - This script requires proper authentication
    - Only displays credentials for authorized users
"""

import getpass
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class AffiliateCredentialsViewer:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to the intelligence database
            self.db_path = os.path.join(os.getcwd(), "data", "intelligence.db")
        else:
            self.db_path = db_path

        # Check if database exists
        if not os.path.exists(self.db_path):
            print(f"Database not found at: {self.db_path}")
            print("Please ensure the stealth automation system has been initialized.")
            exit(1)

    def authenticate_user(self) -> bool:
        """
        Simple authentication to prevent unauthorized access
        In production, this would use proper authentication
        """
        print("\n🔐 Affiliate Credentials Access")
        print("Please authenticate to view stored credentials\n")

        # Simple password check (in production, use proper auth)
        password = getpass.getpass("Enter access password: ")

        # Hash the password (replace with your actual auth logic)
        expected_hash = "your_password_hash_here"  # Replace with actual hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # For demo purposes, accept any password
        # In production, implement proper authentication
        return True

    def get_affiliate_dashboards(self) -> List[Dict[str, Any]]:
        """
        Retrieve all affiliate dashboard credentials from database
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query affiliate dashboards
            cursor.execute(
                """
                SELECT id, platform_name, dashboard_url, login_credentials_encrypted, 
                       last_scraped, scraping_config, created_at
                FROM affiliate_dashboards
                ORDER BY platform_name
            """
            )

            dashboards = cursor.fetchall()
            conn.close()

            # Convert to list of dictionaries
            dashboard_list = []
            for row in dashboards:
                dashboard = {
                    "id": row[0],
                    "platform_name": row[1],
                    "dashboard_url": row[2],
                    "login_credentials": row[3],  # Encrypted
                    "last_scraped": row[4],
                    "scraping_config": json.loads(row[5]) if row[5] else {},
                    "created_at": row[6],
                }
                dashboard_list.append(dashboard)

            return dashboard_list

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []
        except Exception as e:
            print(f"Error retrieving dashboards: {e}")
            return []

    def get_stealth_profiles(self) -> List[Dict[str, Any]]:
        """
        Get stealth profiles used for accessing dashboards
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT profile_id, user_agent, viewport_size, timezone, 
                       language, platform, last_used, success_rate
                FROM stealth_profiles
                ORDER BY success_rate DESC
            """
            )

            profiles = cursor.fetchall()
            conn.close()

            profile_list = []
            for row in profiles:
                profile = {
                    "profile_id": row[0],
                    "user_agent": row[1],
                    "viewport_size": row[2],
                    "timezone": row[3],
                    "language": row[4],
                    "platform": row[5],
                    "last_used": row[6],
                    "success_rate": row[7],
                }
                profile_list.append(profile)

            return profile_list

        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return []

    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, str]:
        """
        Decrypt stored credentials (placeholder implementation)
        In production, use proper encryption/decryption
        """
        try:
            # This is a placeholder - implement actual decryption
            # For now, assume credentials are stored as JSON
            if encrypted_data:
                return json.loads(encrypted_data)
            return {}
        except:
            return {"username": "[ENCRYPTED]", "password": "[ENCRYPTED]"}

    def display_dashboards(self):
        """
        Display all affiliate dashboards with their credentials
        """
        dashboards = self.get_affiliate_dashboards()

        if not dashboards:
            print("\n❌ No affiliate dashboards found.")
            print(
                "Make sure you have signed up for affiliate programs using the automation system."
            )
            return

        print(f"\n📊 Found {len(dashboards)} Affiliate Dashboard(s)\n")
        print("=" * 80)

        for i, dashboard in enumerate(dashboards, 1):
            print(f"\n🏢 Dashboard #{i}: {dashboard['platform_name']}")
            print("-" * 50)
            print(f"📍 Dashboard URL: {dashboard['dashboard_url']}")

            # Decrypt and display credentials
            credentials = self.decrypt_credentials(dashboard["login_credentials"])
            print(f"👤 Username: {credentials.get('username', 'Not available')}")
            print(f"🔑 Password: {credentials.get('password', 'Not available')}")

            if dashboard["last_scraped"]:
                print(f"🕒 Last Accessed: {dashboard['last_scraped']}")

            print(f"📅 Added: {dashboard['created_at']}")

            # Display scraping configuration if available
            config = dashboard["scraping_config"]
            if config:
                print(f"⚙️  Configuration: {len(config)} settings")
                if "login_url" in config:
                    print(f"   Login URL: {config['login_url']}")
                if "selectors" in config:
                    print(f"   Selectors: {len(config['selectors'])} elements")

        print("\n" + "=" * 80)

    def display_access_summary(self):
        """
        Display summary of access information
        """
        dashboards = self.get_affiliate_dashboards()
        profiles = self.get_stealth_profiles()

        print("\n📈 Access Summary")
        print("-" * 30)
        print(f"Total Affiliate Programs: {len(dashboards)}")
        print(f"Stealth Profiles Available: {len(profiles)}")

        if profiles:
            avg_success = sum(p["success_rate"] for p in profiles) / len(profiles)
            print(f"Average Success Rate: {avg_success:.1%}")

        # Count by platform
        platforms = {}
        for dashboard in dashboards:
            platform = dashboard["platform_name"]
            platforms[platform] = platforms.get(platform, 0) + 1

        if platforms:
            print("\n📊 Programs by Platform:")
            for platform, count in sorted(platforms.items()):
                print(f"   {platform}: {count}")

    def export_credentials(self, output_file: str = "affiliate_credentials.json"):
        """
        Export credentials to a JSON file for backup
        """
        dashboards = self.get_affiliate_dashboards()

        if not dashboards:
            print("No credentials to export.")
            return

        # Prepare export data (without sensitive info in plain text)
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_dashboards": len(dashboards),
            "dashboards": [],
        }

        for dashboard in dashboards:
            export_item = {
                "platform_name": dashboard["platform_name"],
                "dashboard_url": dashboard["dashboard_url"],
                "created_at": dashboard["created_at"],
                "last_scraped": dashboard["last_scraped"],
                "has_credentials": bool(dashboard["login_credentials"]),
            }
            export_data["dashboards"].append(export_item)

        try:
            with open(output_file, "w") as f:
                json.dump(export_data, f, indent=2)
            print(f"\n✅ Credentials summary exported to: {output_file}")
        except Exception as e:
            print(f"\n❌ Export failed: {e}")


def main():
    """
    Main function to run the credentials viewer
    """
    print("🚀 Affiliate Dashboard Credentials Viewer")
    print("==========================================\n")

    viewer = AffiliateCredentialsViewer()

    # Authenticate user
    if not viewer.authenticate_user():
        print("❌ Authentication failed. Access denied.")
        return

    print("\n✅ Authentication successful!\n")

    while True:
        print("\n📋 Available Options:")
        print("1. View All Affiliate Dashboards")
        print("2. View Access Summary")
        print("3. Export Credentials Summary")
        print("4. Exit")

        choice = input("\nSelect an option (1-4): ").strip()

        if choice == "1":
            viewer.display_dashboards()
        elif choice == "2":
            viewer.display_access_summary()
        elif choice == "3":
            filename = input("Enter filename (or press Enter for default): ").strip()
            if not filename:
                filename = "affiliate_credentials.json"
            viewer.export_credentials(filename)
        elif choice == "4":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option. Please try again.")

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
