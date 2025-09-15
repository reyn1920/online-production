#!/usr/bin/env python3
""""""
Cloud Software Integration Manager

This module manages the integration and monitoring of cloud software products
including Lingo Blaster, Captionizer, Thumbnail Blaster, Speechelo, Voice Generator,
Background Music, Voiceover Cash Machine, Training, and Scriptelo.

Features:
- Database integration management
- Software status monitoring
- Usage tracking and analytics
- Health checks and diagnostics
- Integration testing
""""""

import json
import logging
import sqlite3
import psutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SoftwareStatus:
    """Data class for software status information"""

    software_name: str
    display_name: str
    category: str
    status: str
    integration_type: str
    health_status: str
    last_health_check: Optional[datetime]
    installation_status: str
    license_type: str
    subscription_status: Optional[str]
    capabilities: List[str]
    notes: str


class CloudSoftwareManager:
    """Manages cloud software integration and monitoring"""

    def __init__(self, db_path: str = "right_perspective.db"):
        self.db_path = db_path
        self.ensure_database_exists()

    def ensure_database_exists(self):
        """Ensure the database and cloud software tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if cloud_software table exists
                cursor.execute(
                    """"""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='cloud_software'
                """"""
# BRACKET_SURGEON: disabled
#                 )

                if not cursor.fetchone():
                    logger.info("Cloud software table not found. Creating from schema...")
                    self.create_cloud_software_tables(conn)
                else:
                    logger.info("Cloud software tables already exist")

        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise

    def create_cloud_software_tables(self, conn: sqlite3.Connection):
        """Create cloud software tables directly"""
        try:
            # Create cloud_software table
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS cloud_software (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        software_name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        category TEXT NOT NULL CHECK (category IN ('voice_generation', 'video_editing', 'thumbnail_creation', 'script_writing', 'background_music', 'training', 'automation', 'bonus_tools')),
                        provider TEXT,
                        version TEXT,
                        status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'deprecated')),
                        integration_type TEXT CHECK (integration_type IN ('api', 'rpa', 'manual', 'webhook', 'cli')),
                        api_endpoint TEXT,
                        authentication_method TEXT CHECK (authentication_method IN ('api_key', 'oauth2', 'username_password', 'token', 'none')),
                        credentials_stored BOOLEAN DEFAULT FALSE,
                        rate_limit_per_hour INTEGER,
                        rate_limit_per_day INTEGER,
                        current_usage_hour INTEGER DEFAULT 0,
                        current_usage_day INTEGER DEFAULT 0,
                        last_usage_reset TIMESTAMP,
                        configuration JSON,
                        capabilities JSON,
                        dependencies JSON,
                        installation_status TEXT DEFAULT 'not_installed' CHECK (installation_status IN ('not_installed', 'installing', 'installed', 'failed', 'updating')),
                        installation_path TEXT,
                        license_type TEXT CHECK (license_type IN ('free', 'paid', 'subscription', 'one_time', 'trial')),
                        license_expires_at TIMESTAMP,
                        subscription_status TEXT CHECK (subscription_status IN ('active', 'expired', 'cancelled', 'trial', 'none')),
                        monthly_cost DECIMAL(10,2),
                        annual_cost DECIMAL(10,2),
                        usage_metrics JSON,
                        performance_metrics JSON,
                        last_health_check TIMESTAMP,
                        health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
                        documentation_url TEXT,
                        support_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_by TEXT,
                        notes TEXT,
                        metadata JSON
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            # Create software_usage_logs table
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS software_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        software_id INTEGER NOT NULL,
                        usage_type TEXT NOT NULL,
                        operation TEXT,
                        input_data JSON,
                        output_data JSON,
                        execution_time_ms INTEGER,
                        status TEXT CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
                        error_message TEXT,
                        cost DECIMAL(10,4),
                        user_id TEXT,
                        session_id TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSON,
                        FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            # Create software_integration_status table
            conn.execute(
                """"""
                CREATE TABLE IF NOT EXISTS software_integration_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        software_id INTEGER NOT NULL,
                        check_type TEXT NOT NULL,
                        status TEXT CHECK (status IN ('pass', 'fail', 'warning', 'skip')),
                        message TEXT,
                        response_time_ms INTEGER,
                        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        checked_by TEXT,
                        details JSON,
                        FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
# BRACKET_SURGEON: disabled
#                 )
            """"""
# BRACKET_SURGEON: disabled
#             )

            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_name ON cloud_software(software_name)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_category ON cloud_software(category)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_status ON cloud_software(status)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_integration_type ON cloud_software(integration_type)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_installation ON cloud_software(installation_status)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_health ON cloud_software(health_status)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_software_id ON software_usage_logs(software_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_type ON software_usage_logs(usage_type)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_timestamp ON software_usage_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_status ON software_usage_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_user ON software_usage_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_software_id ON software_integration_status(software_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_type ON software_integration_status(check_type)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_status ON software_integration_status(status)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_checked ON software_integration_status(checked_at)",
# BRACKET_SURGEON: disabled
#             ]

            for index_sql in indexes:
                conn.execute(index_sql)

            # Insert the cloud software products
            software_products = [
                (
                    "lingo_blaster",
                    "Lingo Blaster",
                    "automation",
                    "Lingo Blaster Inc",
                    "active",
                    "rpa",
                    "username_password",
                    '["language_processing", "content_translation", "multilingual_support"]',
                    "subscription",
                    "system",
                    "Language processing and translation tool",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "captionizer",
                    "Captionizer",
                    "video_editing",
                    "Captionizer Pro",
                    "active",
                    "api",
                    "api_key",
                    '["subtitle_generation", "caption_creation", "video_processing"]',
                    "subscription",
                    "system",
                    "Automated caption and subtitle generation",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "thumbnail_blaster",
                    "Thumbnail Blaster",
                    "thumbnail_creation",
                    "Thumbnail Blaster",
                    "active",
                    "rpa",
                    "username_password",
                    '["thumbnail_creation", "image_editing", "template_processing"]',
                    "subscription",
                    "system",
                    "Automated thumbnail creation and editing",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "speechelo",
                    "Speechelo",
                    "voice_generation",
                    "Speechelo",
                    "active",
                    "rpa",
                    "username_password",
                    '["text_to_speech", "voice_synthesis", "audio_generation"]',
                    "one_time",
                    "system",
                    "Text - to - speech voice generation software",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "voice_generator",
                    "Voice Generator",
                    "voice_generation",
                    "Voice Generator Pro",
                    "active",
                    "api",
                    "api_key",
                    '["voice_synthesis", "custom_voices", "audio_processing"]',
                    "subscription",
                    "system",
                    "Advanced voice generation and synthesis",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "background_music",
                    "Background Music",
                    "background_music",
                    "Music Library Pro",
                    "active",
                    "api",
                    "api_key",
                    '["music_library", "royalty_free_music", "audio_mixing"]',
                    "subscription",
                    "system",
                    "Royalty - free background music library",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "voiceover_cash_machine",
                    "Voiceover Cash Machine",
                    "bonus_tools",
                    "Voiceover Cash Machine",
                    "active",
                    "manual",
                    "none",
                    '["voiceover_training", "business_strategies", "monetization"]',
                    "one_time",
                    "system",
                    "BONUS: Voiceover business training and strategies",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "training",
                    "Training",
                    "training",
                    "Training Academy",
                    "active",
                    "manual",
                    "none",
                    '["video_training", "tutorials", "skill_development"]',
                    "subscription",
                    "system",
                    "Comprehensive training modules and tutorials",
# BRACKET_SURGEON: disabled
#                 ),
                (
                    "scriptelo",
                    "Scriptelo",
                    "script_writing",
                    "Scriptelo",
                    "active",
                    "rpa",
                    "username_password",
                    '["script_generation", "content_writing", "template_processing"]',
                    "subscription",
                    "system",
                    "Automated script writing and content generation",
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             ]

            conn.executemany(
                """"""
                INSERT OR REPLACE INTO cloud_software (
                    software_name, display_name, category, provider, status, integration_type,
                        authentication_method, capabilities, license_type, created_by, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ""","""
                software_products,
# BRACKET_SURGEON: disabled
#             )

            conn.commit()
            logger.info("Cloud software tables created successfully")

        except Exception as e:
            logger.error(f"Error creating cloud software tables: {e}")
            raise

    def get_all_software(self) -> List[SoftwareStatus]:
        """Get all cloud software with their current status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """"""
                    SELECT software_name, display_name, category, status,
                        integration_type, health_status, last_health_check,
                               installation_status, license_type, subscription_status,
                               capabilities, notes
                    FROM cloud_software
                    ORDER BY category, display_name
                """"""
# BRACKET_SURGEON: disabled
#                 )

                software_list = []
                for row in cursor.fetchall():
                    capabilities = json.loads(row[10]) if row[10] else []
                    last_check = datetime.fromisoformat(row[6]) if row[6] else None

                    software_list.append(
                        SoftwareStatus(
                            software_name=row[0],
                            display_name=row[1],
                            category=row[2],
                            status=row[3],
                            integration_type=row[4],
                            health_status=row[5],
                            last_health_check=last_check,
                            installation_status=row[7],
                            license_type=row[8],
                            subscription_status=row[9],
                            capabilities=capabilities,
                            notes=row[11],
# BRACKET_SURGEON: disabled
#                         )
# BRACKET_SURGEON: disabled
#                     )

                return software_list

        except Exception as e:
            logger.error(f"Error retrieving software list: {e}")
            return []

    def update_software_status(
        self,
        software_name: str,
        status: str,
        health_status: str = None,
        notes: str = None,
# BRACKET_SURGEON: disabled
#     ):
        """Update software status and health information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]

                if health_status:
                    update_fields.append("health_status = ?")
                    update_fields.append("last_health_check = CURRENT_TIMESTAMP")
                    params.append(health_status)

                if notes:
                    update_fields.append("notes = ?")
                    params.append(notes)

                params.append(software_name)

                cursor.execute(
                    f""""""
                    UPDATE cloud_software
                    SET {', '.join(update_fields)}
                    WHERE software_name = ?
                ""","""
                    params,
# BRACKET_SURGEON: disabled
#                 )

                conn.commit()
                logger.info(f"Updated status for {software_name}: {status}")

        except Exception as e:
            logger.error(f"Error updating software status: {e}")

    def log_software_usage(
        self,
        software_name: str,
        usage_type: str,
        operation: str,
        status: str = "success",
        execution_time_ms: int = None,
        error_message: str = None,
# BRACKET_SURGEON: disabled
#     ):
        """Log software usage for tracking and analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Get software ID
                cursor.execute(
                    "SELECT id FROM cloud_software WHERE software_name = ?",
                    (software_name,),
# BRACKET_SURGEON: disabled
#                 )
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Software {software_name} not found")
                    return

                software_id = result[0]

                cursor.execute(
                    """"""
                    INSERT INTO software_usage_logs
                    (software_id,
    usage_type,
    operation,
    status,
    execution_time_ms,
# BRACKET_SURGEON: disabled
#     error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                ""","""
                    (
                        software_id,
                        usage_type,
                        operation,
                        status,
                        execution_time_ms,
                        error_message,
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )

                conn.commit()
                logger.info(f"Logged usage for {software_name}: {operation}")

        except Exception as e:
            logger.error(f"Error logging software usage: {e}")

    def perform_health_checks(self) -> Dict[str, str]:
        """Perform health checks on all active software"""
        results = {}
        software_list = self.get_all_software()

        for software in software_list:
            if software.status == "active":
                health_status = self._check_software_health(software)
                results[software.software_name] = health_status
                self.update_software_status(software.software_name, software.status, health_status)

        return results

    def _check_software_health(self, software: SoftwareStatus) -> str:
        """Check health of individual software"""
        try:
            # Update last health check timestamp
            self._update_last_health_check(software.software_name)

            if software.integration_type == "api":
                return self._check_api_health(software)
            elif software.integration_type == "rpa":
                return self._check_rpa_health(software)
            elif software.integration_type == "manual":
                return self._check_manual_health(software)
            else:
                return "unknown"

        except Exception as e:
            logger.error(f"Health check failed for {software.software_name}: {e}")
            return "unhealthy"

    def _check_api_health(self, software: SoftwareStatus) -> str:
        """Check health of API-based software integrations"""
        try:
            # Get API endpoint from metadata or construct from software name
            metadata = self._get_software_metadata(software.software_name)
            api_endpoint = metadata.get("api_endpoint") or metadata.get("health_endpoint")

            if not api_endpoint:
                # Try to construct common health endpoints
                base_urls = {
                    "slack": "https://slack.com/api/api.test",
                    "discord": "https://discord.com/api/v10/gateway",
                    "github": "https://api.github.com/zen",
                    "google": "https://www.googleapis.com/oauth2/v1/tokeninfo",
                    "microsoft": "https://graph.microsoft.com/v1.0/me",
                    "zoom": "https://api.zoom.us/v2/users/me",
                    "dropbox": "https://api.dropboxapi.com/2/users/get_current_account",
                    "salesforce": "https://login.salesforce.com/services/oauth2/token",
# BRACKET_SURGEON: disabled
#                 }

                software_lower = software.software_name.lower()
                for service, url in base_urls.items():
                    if service in software_lower:
                        api_endpoint = url
                        break

            if api_endpoint:
                return self._perform_api_health_check(api_endpoint, software)
            else:
                # Fallback: check if software process is running
                return self._check_process_health(software)

        except Exception as e:
            logger.error(f"API health check failed for {software.software_name}: {e}")
            return "unhealthy"

    def _perform_api_health_check(self, endpoint: str, software: SoftwareStatus) -> str:
        """Perform actual HTTP health check"""
        try:
            import requests

            # Get API credentials from metadata if available
            metadata = self._get_software_metadata(software.software_name)
            headers = metadata.get("headers", {})
            auth_token = metadata.get("auth_token")

            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            # Perform health check with timeout
            response = requests.get(endpoint, headers=headers, timeout=10, verify=True)

            if response.status_code == 200:
                return "healthy"
            elif response.status_code in [401, 403]:
                return "degraded"  # Authentication issues
            elif response.status_code >= 500:
                return "unhealthy"  # Server errors
            else:
                return "degraded"  # Other client errors

        except requests.exceptions.Timeout:
            return "degraded"
        except requests.exceptions.ConnectionError:
            return "unhealthy"
        except Exception as e:
            logger.error(f"API request failed for {software.software_name}: {e}")
            return "unhealthy"

    def _check_rpa_health(self, software: SoftwareStatus) -> str:
        """Check health of RPA (Robotic Process Automation) integrations"""
        try:
            # Check for common RPA tools and their processes
            rpa_processes = {
                "uipath": [
                    "UiPath.Executor.exe",
                    "UiPath.Agent.exe",
                    "UiPath.Service.exe",
# BRACKET_SURGEON: disabled
#                 ],
                "automation_anywhere": [
                    "AAApplicationManager.exe",
                    "AATaskManager.exe",
# BRACKET_SURGEON: disabled
#                 ],
                "blue_prism": ["Automate.exe", "BluePrism.exe"],
                "power_automate": ["PAD.Console.Host.exe", "PAD.Robot.exe"],
                "selenium": ["chromedriver.exe", "geckodriver.exe", "msedgedriver.exe"],
                "playwright": ["playwright"],
                "puppeteer": ["node"],
# BRACKET_SURGEON: disabled
#             }

            software_lower = software.software_name.lower()

            # Check if RPA processes are running
            running_processes = [p.name() for p in psutil.process_iter(["name"])]

            for rpa_tool, processes in rpa_processes.items():
                if rpa_tool in software_lower:
                    for process in processes:
                        if any(process.lower() in rp.lower() for rp in running_processes):
                            return "healthy"
                    return "unhealthy"  # Expected processes not found

            # Check for automation scripts or configuration files
            automation_paths = [
                Path.home() / ".uipath",
                Path.home() / "Documents" / "UiPath",
                Path.home() / "AppData" / "Local" / "UiPath",
                Path("/opt/uipath"),
                Path("/usr/local/bin/chromedriver"),
                Path("/usr/local/bin/geckodriver"),
# BRACKET_SURGEON: disabled
#             ]

            for path in automation_paths:
                if path.exists():
                    return "healthy"

            # Check if automation capabilities are available via command line
            automation_commands = [
                "chromedriver",
                "geckodriver",
                "playwright",
                "selenium-server",
# BRACKET_SURGEON: disabled
#             ]

            for cmd in automation_commands:
                try:
                    result = subprocess.run(
                        [cmd, "--version"], capture_output=True, timeout=5, text=True
# BRACKET_SURGEON: disabled
#                     )
                    if result.returncode == 0:
                        return "healthy"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            return "degraded"  # RPA tools may be installed but not actively running

        except Exception as e:
            logger.error(f"RPA health check failed for {software.software_name}: {e}")
            return "unhealthy"

    def _check_manual_health(self, software: SoftwareStatus) -> str:
        """Check health of manual integrations"""
        try:
            # For manual integrations, check various indicators of health

            # Check if software is installed (for desktop applications)
            if software.installation_status == "installed":
                installation_path = self._get_installation_path(software.software_name)
                if installation_path and Path(installation_path).exists():
                    return "healthy"

            # Check subscription status
            if software.subscription_status in ["active", "trial"]:
                # Check if subscription is not expired
                metadata = self._get_software_metadata(software.software_name)
                expires_at = metadata.get("license_expires_at")

                if expires_at:
                    try:
                        expiry_date = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                        if datetime.now() < expiry_date:
                            return "healthy"
                        else:
                            return "degraded"  # Expired subscription
                    except ValueError:
                        pass
                else:
                    return "healthy"  # Active subscription without expiry

            # Check if software process is running (for desktop apps)
            process_health = self._check_process_health(software)
            if process_health == "healthy":
                return "healthy"

            # Check recent usage indicators
            if self._check_recent_usage(software):
                return "healthy"

            # Default to healthy for manual integrations if no issues detected
            return "healthy"

        except Exception as e:
            logger.error(f"Manual health check failed for {software.software_name}: {e}")
            return "unhealthy"

    def _check_process_health(self, software: SoftwareStatus) -> str:
        """Check if software process is running"""
        try:
            # Common process names for popular software
            process_mappings = {
                "slack": ["slack.exe", "Slack"],
                "discord": ["discord.exe", "Discord"],
                "zoom": ["zoom.exe", "zoom", "Zoom"],
                "teams": ["teams.exe", "Microsoft Teams"],
                "chrome": ["chrome.exe", "Google Chrome"],
                "firefox": ["firefox.exe", "Firefox"],
                "vscode": ["code.exe", "Visual Studio Code"],
                "photoshop": ["photoshop.exe", "Adobe Photoshop"],
                "excel": ["excel.exe", "Microsoft Excel"],
                "word": ["winword.exe", "Microsoft Word"],
# BRACKET_SURGEON: disabled
#             }

            software_lower = software.software_name.lower()
            running_processes = [p.name() for p in psutil.process_iter(["name"])]

            for software_key, process_names in process_mappings.items():
                if software_key in software_lower:
                    for process_name in process_names:
                        if any(process_name.lower() in rp.lower() for rp in running_processes):
                            return "healthy"
                    return "degraded"  # Software not currently running

            return "unknown"  # No process mapping found

        except Exception as e:
            logger.error(f"Process health check failed for {software.software_name}: {e}")
            return "unhealthy"

    def _check_recent_usage(self, software: SoftwareStatus) -> bool:
        """Check for recent usage indicators"""
        try:
            # Check for recent log files, cache files, or configuration updates
            common_paths = [
                Path.home() / "AppData" / "Local" / software.software_name,
                Path.home() / "AppData" / "Roaming" / software.software_name,
                Path.home() / ".config" / software.software_name.lower(),
                Path.home() / "Library" / "Application Support" / software.software_name,
                Path.home() / f".{software.software_name.lower()}",
# BRACKET_SURGEON: disabled
#             ]

            recent_threshold = datetime.now() - timedelta(days=7)

            for path in common_paths:
                if path.exists():
                    # Check modification time of directory or files within
                    try:
                        if path.is_file():
                            mod_time = datetime.fromtimestamp(path.stat().st_mtime)
                            if mod_time > recent_threshold:
                                return True
                        elif path.is_dir():
                            for file_path in path.rglob("*"):
                                if file_path.is_file():
                                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                                    if mod_time > recent_threshold:
                                        return True
                    except (OSError, PermissionError):
                        continue

            return False

        except Exception as e:
            logger.error(f"Recent usage check failed for {software.software_name}: {e}")
            return False

    def _get_software_metadata(self, software_name: str) -> Dict[str, Any]:
        """Get software metadata from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT metadata FROM cloud_software WHERE software_name = ?",
                (software_name,),
# BRACKET_SURGEON: disabled
#             )

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                return json.loads(result[0])
            return {}

        except Exception as e:
            logger.error(f"Failed to get metadata for {software_name}: {e}")
            return {}

    def _get_installation_path(self, software_name: str) -> Optional[str]:
        """Get installation path for software"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT installation_path FROM cloud_software WHERE software_name = ?",
                (software_name,),
# BRACKET_SURGEON: disabled
#             )

            result = cursor.fetchone()
            conn.close()

            return result[0] if result else None

        except Exception as e:
            logger.error(f"Failed to get installation path for {software_name}: {e}")
            return None

    def _update_last_health_check(self, software_name: str):
        """Update the last health check timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE cloud_software SET last_health_check = ? WHERE software_name = ?",
                (datetime.now().isoformat(), software_name),
# BRACKET_SURGEON: disabled
#             )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Failed to update health check timestamp for {software_name}: {e}")

    def get_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration status report"""
        software_list = self.get_all_software()

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_software": len(software_list),
            "by_category": {},
            "by_status": {},
            "by_integration_type": {},
            "health_summary": {},
            "software_details": [],
# BRACKET_SURGEON: disabled
#         }

        for software in software_list:
            # Count by category
            if software.category not in report["by_category"]:
                report["by_category"][software.category] = 0
            report["by_category"][software.category] += 1

            # Count by status
            if software.status not in report["by_status"]:
                report["by_status"][software.status] = 0
            report["by_status"][software.status] += 1

            # Count by integration type
            if software.integration_type not in report["by_integration_type"]:
                report["by_integration_type"][software.integration_type] = 0
            report["by_integration_type"][software.integration_type] += 1

            # Count by health status
            if software.health_status not in report["health_summary"]:
                report["health_summary"][software.health_status] = 0
            report["health_summary"][software.health_status] += 1

            # Add software details
            report["software_details"].append(
                {
                    "name": software.display_name,
                    "category": software.category,
                    "status": software.status,
                    "integration_type": software.integration_type,
                    "health_status": software.health_status,
                    "capabilities": software.capabilities,
                    "license_type": software.license_type,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

        return report

    def print_integration_status(self):
        """Print formatted integration status to console"""
        software_list = self.get_all_software()

        print("\\n" + "=" * 80)
        print("CLOUD SOFTWARE INTEGRATION STATUS")
        print("=" * 80)

        if not software_list:
            print("No cloud software found in database.")
            return

        # Group by category
        by_category = {}
        for software in software_list:
            if software.category not in by_category:
                by_category[software.category] = []
            by_category[software.category].append(software)

        for category, software_items in by_category.items():
            print(f"\\n{category.upper().replace('_', ' ')}:")
            print("-" * 40)

            for software in software_items:
                status_icon = "✅" if software.status == "active" else "❌"
                health_icon = {
                    "healthy": "🟢",
                    "degraded": "🟡",
                    "unhealthy": "🔴",
                    "unknown": "⚪",
                }.get(software.health_status, "⚪")

                print(f"  {status_icon} {health_icon} {software.display_name}")
                print(f"      Integration: {software.integration_type}")
                print(f"      License: {software.license_type}")
                print(f"      Capabilities: {', '.join(software.capabilities)}")
                if software.notes:
                    print(f"      Notes: {software.notes}")
                print()

        # Summary
        active_count = sum(1 for s in software_list if s.status == "active")
        healthy_count = sum(1 for s in software_list if s.health_status == "healthy")

        print("\\nSUMMARY:")
        print(f"  Total Software: {len(software_list)}")
        print(f"  Active: {active_count}")
        print(f"  Healthy: {healthy_count}")
        print("=" * 80)


def main():
    """Main function to demonstrate cloud software management"""
    manager = CloudSoftwareManager()

    print("Cloud Software Integration Manager")
    print("Initializing database and checking integration status...")

    # Print current status
    manager.print_integration_status()

    # Perform health checks
    print("\\nPerforming health checks...")
    health_results = manager.perform_health_checks()

    for software_name, health_status in health_results.items():
        print(f"  {software_name}: {health_status}")

    # Generate report
    report = manager.get_integration_report()
    print(f"\\nIntegration report generated at {report['timestamp']}")
    print(f"Total software products: {report['total_software']}")

    # Save report to file
    report_path = f"cloud_software_report_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()