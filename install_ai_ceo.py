#!/usr/bin/env python3
""""""
AI CEO Automation System - Automated Installation Script

This script automatically sets up the complete AI CEO system:
1. Checks system requirements
2. Installs Python dependencies
3. Creates configuration files
4. Sets up database
5. Validates installation
6. Provides setup instructions

Usage:
    python install_ai_ceo.py
    python install_ai_ceo.py --quick
    python install_ai_ceo.py --dev

Author: TRAE.AI System
Version: 2.0.0
""""""

import argparse
import json
import logging
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Dict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("ai_ceo_installation.log"), logging.StreamHandler()],
# BRACKET_SURGEON: disabled
# )

logger = logging.getLogger(__name__)


class AICEOInstaller:
    """Automated installer for the AI CEO Automation System."""

    def __init__(self, quick_install: bool = False, dev_mode: bool = False):
        self.quick_install = quick_install
        self.dev_mode = dev_mode
        self.system_info = self._get_system_info()
        self.installation_path = Path.cwd()
        self.errors = []
        self.warnings = []

        logger.info("🚀 AI CEO Automation System Installer")
        logger.info("=" * 60)

    def _get_system_info(self) -> Dict[str, str]:
        """Get system information."""
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "python_version": platform.python_version(),
            "python_executable": sys.executable,
# BRACKET_SURGEON: disabled
#         }

    def install(self) -> bool:
        """Run the complete installation process."""
        logger.info("🔍 Starting AI CEO system installation...")

        installation_steps = [
            ("System Requirements Check", self._check_system_requirements),
            ("Python Environment Setup", self._setup_python_environment),
            ("Dependency Installation", self._install_dependencies),
            ("Configuration Setup", self._setup_configuration),
            ("Database Initialization", self._initialize_database),
            ("File Permissions", self._set_file_permissions),
            ("Installation Validation", self._validate_installation),
            ("Post - Installation Setup", self._post_installation_setup),
# BRACKET_SURGEON: disabled
#         ]

        success = True

        for step_name, step_function in installation_steps:
            logger.info(f"\\n📋 {step_name}...")
            try:
                if not step_function():
                    logger.error(f"❌ {step_name} failed")
                    success = False
                    if not self.quick_install:
                        user_input = input("Continue with installation? (y/n): ").lower()
                        if user_input != "y":
                            break
                else:
                    logger.info(f"✅ {step_name} completed")
            except Exception as e:
                logger.error(f"❌ {step_name} failed with error: {e}")
                self.errors.append(f"{step_name}: {e}")
                success = False

        # Installation summary
        self._print_installation_summary(success)

        return success and len(self.errors) == 0

    def _check_system_requirements(self) -> bool:
        """Check system requirements."""
        logger.info("🔍 Checking system requirements...")

        checks = [
            self._check_python_version,
            self._check_available_memory,
            self._check_disk_space,
            self._check_network_connectivity,
            self._check_required_commands,
# BRACKET_SURGEON: disabled
#         ]

        all_passed = True
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                logger.error(f"❌ System check failed: {e}")
                all_passed = False

        if all_passed:
            logger.info("✅ All system requirements met")
        else:
            logger.warning("⚠️ Some system requirements not met")

        return all_passed or self.quick_install

    def _check_python_version(self) -> bool:
        """Check Python version."""
        version = sys.version_info
        if version < (3, 8):
            logger.error(
                f"❌ Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}"
# BRACKET_SURGEON: disabled
#             )
            return False

        logger.info(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True

    def _check_available_memory(self) -> bool:
        """Check available system memory."""
        try:
            import psutil

            available_gb = psutil.virtual_memory().available / (1024**3)

            if available_gb < 1.0:
                logger.error(
                    f"❌ Insufficient memory: {available_gb:.1f}GB available (1GB required)"
# BRACKET_SURGEON: disabled
#                 )
                return False

            logger.info(f"✅ Available memory: {available_gb:.1f}GB")
            return True

        except ImportError:
            logger.warning("⚠️ psutil not available, skipping memory check")
            return True

    def _check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil

            total, used, free = shutil.disk_usage(self.installation_path)
            free_gb = free / (1024**3)

            if free_gb < 1.0:
                logger.error(f"❌ Insufficient disk space: {free_gb:.1f}GB available (1GB required)")
                return False

            logger.info(f"✅ Available disk space: {free_gb:.1f}GB")
            return True

        except Exception as e:
            logger.warning(f"⚠️ Could not check disk space: {e}")
            return True

    def _check_network_connectivity(self) -> bool:
        """Check network connectivity."""
        try:
            urllib.request.urlopen("https://pypi.org", timeout=10)
            logger.info("✅ Network connectivity available")
            return True
        except Exception:
            logger.warning("⚠️ Limited network connectivity (offline installation)")
            return True  # Allow offline installation

    def _check_required_commands(self) -> bool:
        """Check for required system commands."""
        required_commands = ["pip"]

        if self.system_info["platform"] == "Windows":
            required_commands.extend(["where"])
        else:
            required_commands.extend(["which"])

        all_found = True
        for cmd in required_commands:
            if not shutil.which(cmd):
                logger.error(f"❌ Required command not found: {cmd}")
                all_found = False
            else:
                logger.info(f"✅ Found command: {cmd}")

        return all_found

    def _setup_python_environment(self) -> bool:
        """Setup Python environment."""
        logger.info("🐍 Setting up Python environment...")

        try:
            # Check if we're in a virtual environment
            in_venv = hasattr(sys, "real_prefix") or (
                hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
# BRACKET_SURGEON: disabled
#             )

            if not in_venv and not self.quick_install:
                logger.warning("⚠️ Not running in a virtual environment")
                logger.info("💡 Recommendation: Create a virtual environment:")
                logger.info("   python -m venv ai_ceo_env")
                logger.info(
                    "   source ai_ceo_env/bin/activate  # On Windows: ai_ceo_env\\\\Scripts\\\\activate""
# BRACKET_SURGEON: disabled
#                 )

                if not self.quick_install:
                    user_input = input("Continue without virtual environment? (y/n): ").lower()
                    if user_input != "y":
                        return False

            # Upgrade pip
            logger.info("📦 Upgrading pip...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                capture_output=True,
                text=True,
# BRACKET_SURGEON: disabled
#             )

            if result.returncode != 0:
                logger.warning(f"⚠️ Pip upgrade failed: {result.stderr}")
            else:
                logger.info("✅ Pip upgraded successfully")

            return True

        except Exception as e:
            logger.error(f"❌ Python environment setup failed: {e}")
            return False

    def _install_dependencies(self) -> bool:
        """Install Python dependencies."""
        logger.info("📦 Installing dependencies...")

        requirements_file = self.installation_path / "requirements.txt"

        if not requirements_file.exists():
            logger.error(f"❌ Requirements file not found: {requirements_file}")
            return False

        try:
            # Install requirements
            logger.info("📥 Installing packages from requirements.txt...")

            install_cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                "-r",
                str(requirements_file),
# BRACKET_SURGEON: disabled
#             ]

            if self.quick_install:
                install_cmd.extend(["--quiet", "--no - warn - script - location"])

            result = subprocess.run(
                install_cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
# BRACKET_SURGEON: disabled
#             )

            if result.returncode != 0:
                logger.error(f"❌ Dependency installation failed: {result.stderr}")
                return False

            logger.info("✅ Dependencies installed successfully")

            # Install additional development dependencies if in dev mode
            if self.dev_mode:
                logger.info("🔧 Installing development dependencies...")
                dev_packages = [
                    "pytest >= 7.4.0",
                    "black >= 23.7.0",
                    "flake8 >= 6.0.0",
                    "mypy >= 1.5.0",
# BRACKET_SURGEON: disabled
#                 ]

                for package in dev_packages:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        capture_output=True,
# BRACKET_SURGEON: disabled
#                     )

            return True

        except subprocess.TimeoutExpired:
            logger.error("❌ Dependency installation timed out")
            return False
        except Exception as e:
            logger.error(f"❌ Dependency installation failed: {e}")
            return False

    def _setup_configuration(self) -> bool:
        """Setup configuration files."""
        logger.info("⚙️ Setting up configuration...")

        try:
            # Create .env file if it doesn't exist
            env_file = self.installation_path / ".env"
            env_example = self.installation_path / ".env.example"

            if not env_file.exists():
                if env_example.exists():
                    shutil.copy2(env_example, env_file)
                    logger.info("✅ Created .env from .env.example")
                else:
                    # Create basic .env file
                    env_content = self._generate_default_env_content()
                    with open(env_file, "w") as f:
                        f.write(env_content)
                    logger.info("✅ Created default .env file")
            else:
                logger.info("✅ .env file already exists")

            # Create AI CEO configuration file
            config_file = self.installation_path / "ai_ceo_config.json"
            if not config_file.exists():
                config_content = self._generate_default_config()
                with open(config_file, "w") as f:
                    json.dump(config_content, f, indent=2)
                logger.info("✅ Created ai_ceo_config.json")
            else:
                logger.info("✅ ai_ceo_config.json already exists")

            # Create logs directory
            logs_dir = self.installation_path / "logs"
            logs_dir.mkdir(exist_ok=True)
            logger.info("✅ Created logs directory")

            # Create data directory
            data_dir = self.installation_path / "data"
            data_dir.mkdir(exist_ok=True)
            logger.info("✅ Created data directory")

            return True

        except Exception as e:
            logger.error(f"❌ Configuration setup failed: {e}")
            return False

    def _generate_default_env_content(self) -> str:
        """Generate default .env file content."""
        return """# AI CEO Automation System Configuration"""
# Copy this file to .env and fill in your actual values

# API Keys (Required)
OPENAI_API_KEY = your_openai_api_key_here
YOUTUBE_API_KEY = your_youtube_api_key_here
GMAIL_API_CREDENTIALS = path/to/gmail_credentials.json
STRIPE_API_KEY = your_stripe_api_key_here
TWITTER_API_KEY = your_twitter_api_key_here
TWITTER_API_SECRET = your_twitter_api_secret_here
TWITTER_ACCESS_TOKEN = your_twitter_access_token_here
TWITTER_ACCESS_TOKEN_SECRET = your_twitter_access_token_secret_here

# Database Configuration
DATABASE_URL = sqlite:///ai_ceo_system.db

# System Configuration
SYSTEM_MODE = production
LOG_LEVEL = INFO
AUTO_RESTART = true
HEALTH_CHECK_INTERVAL = 30
MAX_RESTART_ATTEMPTS = 3

# Business Configuration
COMPANY_NAME = Your Company Name
BUSINESS_OBJECTIVES = revenue_growth,market_expansion,cost_optimization
TARGET_REVENUE = 10000
CONTENT_SCHEDULE = daily
MONETIZATION_FOCUS = high

# Dashboard Configuration
DASHBOARD_PORT = 5000
DASHBOARD_HOST = 0.0.0.0
DASHBOARD_DEBUG = false

# Security Configuration
SECRET_KEY = your_secret_key_here_change_this_in_production
ENCRYPTION_KEY = your_encryption_key_here

# Optional API Keys
INSTAGRAM_API_KEY = your_instagram_api_key_here
LINKEDIN_API_KEY = your_linkedin_api_key_here
PAYPAL_CLIENT_ID = your_paypal_client_id_here
PAYPAL_CLIENT_SECRET = your_paypal_client_secret_here

# Performance Configuration
MAX_WORKERS = 4
CACHE_TIMEOUT = 3600
API_RATE_LIMIT = 100
BATCH_SIZE = 50
""""""

    def _generate_default_config(self) -> Dict:
        """Generate default AI CEO configuration."""
        return {
            "system": {
                "startup_timeout": 300,
                "health_check_interval": 30,
                "auto_restart": True,
                "max_restart_attempts": 3,
                "log_level": "INFO",
                "performance_monitoring": True,
# BRACKET_SURGEON: disabled
#             },
            "components": {
                "decision_engine": {
                    "enabled": True,
                    "startup_delay": 0,
                    "analysis_interval": 300,
                    "decision_threshold": 0.7,
# BRACKET_SURGEON: disabled
#                 },
                "pipeline": {
                    "enabled": True,
                    "startup_delay": 5,
                    "batch_size": 50,
                    "processing_interval": 60,
# BRACKET_SURGEON: disabled
#                 },
                "healing_protocols": {
                    "enabled": True,
                    "startup_delay": 10,
                    "check_interval": 30,
                    "auto_recovery": True,
# BRACKET_SURGEON: disabled
#                 },
                "master_controller": {
                    "enabled": True,
                    "startup_delay": 15,
                    "coordination_interval": 120,
                    "strategy_update_interval": 3600,
# BRACKET_SURGEON: disabled
#                 },
                "monitoring_dashboard": {
                    "enabled": True,
                    "startup_delay": 20,
                    "port": 5000,
                    "host": "0.0.0.0",
                    "refresh_rate": 5,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             },
            "agents": {
                "marketing_agent": {
                    "enabled": True,
                    "priority": "high",
                    "execution_interval": 1800,
# BRACKET_SURGEON: disabled
#                 },
                "financial_agent": {
                    "enabled": True,
                    "priority": "high",
                    "execution_interval": 3600,
# BRACKET_SURGEON: disabled
#                 },
                "monetization_agent": {
                    "enabled": True,
                    "priority": "high",
                    "execution_interval": 900,
# BRACKET_SURGEON: disabled
#                 },
                "content_generation_agent": {
                    "enabled": True,
                    "priority": "medium",
                    "execution_interval": 7200,
# BRACKET_SURGEON: disabled
#                 },
                "stealth_automation_agent": {
                    "enabled": True,
                    "priority": "low",
                    "execution_interval": 300,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             },
            "apis": {
                "youtube_api": {"enabled": True, "rate_limit": 100, "timeout": 30},
                "gmail_api": {"enabled": True, "rate_limit": 50, "timeout": 30},
                "social_media_apis": {
                    "enabled": True,
                    "rate_limit": 200,
                    "timeout": 30,
# BRACKET_SURGEON: disabled
#                 },
                "payment_apis": {"enabled": True, "rate_limit": 10, "timeout": 60},
# BRACKET_SURGEON: disabled
#             },
            "business": {
                "revenue_targets": {
                    "daily": 100,
                    "weekly": 700,
                    "monthly": 3000,
                    "yearly": 36000,
# BRACKET_SURGEON: disabled
#                 },
                "optimization_focus": [
                    "revenue_growth",
                    "cost_reduction",
                    "market_expansion",
                    "customer_retention",
# BRACKET_SURGEON: disabled
#                 ],
                "content_strategy": {
                    "posting_frequency": "daily",
                    "content_types": ["blog", "social", "email", "video"],
                    "seo_optimization": True,
                    "engagement_tracking": True,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             },
            "monitoring": {
                "enable_real_time_alerts": True,
                "enable_performance_tracking": True,
                "enable_business_metrics": True,
                "dashboard_refresh_rate": 5,
                "alert_thresholds": {
                    "error_rate": 0.05,
                    "response_time": 5.0,
                    "memory_usage": 0.8,
                    "disk_usage": 0.9,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

    def _initialize_database(self) -> bool:
        """Initialize the database."""
        logger.info("🗄️ Initializing database...")

        try:
            import sqlite3

            db_path = self.installation_path / "ai_ceo_system.db"

            # Create database connection
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Create basic tables
            tables = [
                """"""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        component TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
# BRACKET_SURGEON: disabled
#                 )
                ""","""
                """"""
                CREATE TABLE IF NOT EXISTS business_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_name TEXT NOT NULL,
                        metric_value REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        category TEXT
# BRACKET_SURGEON: disabled
#                 )
                ""","""
                """"""
                CREATE TABLE IF NOT EXISTS agent_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        agent_name TEXT NOT NULL,
                        activity TEXT NOT NULL,
                        status TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        result TEXT
# BRACKET_SURGEON: disabled
#                 )
                ""","""
                """"""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        decision_type TEXT NOT NULL,
                        decision_data TEXT NOT NULL,
                        confidence REAL NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        outcome TEXT
# BRACKET_SURGEON: disabled
#                 )
                ""","""
# BRACKET_SURGEON: disabled
#             ]

            for table_sql in tables:
                cursor.execute(table_sql)

            conn.commit()
            conn.close()

            logger.info("✅ Database initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False

    def _set_file_permissions(self) -> bool:
        """Set appropriate file permissions."""
        logger.info("🔒 Setting file permissions...")

        try:
            # Make startup script executable
            startup_script = self.installation_path / "start_ai_ceo.py"
            if startup_script.exists():
                startup_script.chmod(0o755)
                logger.info("✅ Made start_ai_ceo.py executable")

            # Secure .env file
            env_file = self.installation_path / ".env"
            if env_file.exists():
                env_file.chmod(0o600)
                logger.info("✅ Secured .env file permissions")

            # Create logs directory with proper permissions
            logs_dir = self.installation_path / "logs"
            if logs_dir.exists():
                logs_dir.chmod(0o755)
                logger.info("✅ Set logs directory permissions")

            return True

        except Exception as e:
            logger.warning(f"⚠️ Could not set file permissions: {e}")
            return True  # Non - critical error

    def _validate_installation(self) -> bool:
        """Validate the installation."""
        logger.info("🔍 Validating installation...")

        try:
            # Check required files
            required_files = [
                "start_ai_ceo.py",
                "ai_ceo_master_controller.py",
                "full_automation_pipeline.py",
                "autonomous_decision_engine.py",
                "self_healing_protocols.py",
                "monitoring_dashboard.py",
                "requirements.txt",
                ".env",
                "ai_ceo_config.json",
# BRACKET_SURGEON: disabled
#             ]

            missing_files = []
            for file_name in required_files:
                file_path = self.installation_path / file_name
                if not file_path.exists():
                    missing_files.append(file_name)

            if missing_files:
                logger.error(f"❌ Missing required files: {missing_files}")
                return False

            logger.info("✅ All required files present")

            # Test import of main modules
            logger.info("🧪 Testing module imports...")

            test_imports = ["sqlite3", "json", "logging", "threading", "asyncio"]

            for module_name in test_imports:
                try:
                    __import__(module_name)
                    logger.info(f"✅ {module_name} import successful")
                except ImportError as e:
                    logger.error(f"❌ {module_name} import failed: {e}")
                    return False

            # Test database connection
            logger.info("🗄️ Testing database connection...")

            import sqlite3

            db_path = self.installation_path / "ai_ceo_system.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            conn.close()

            if len(tables) >= 4:  # We created 4 tables
                logger.info("✅ Database connection and tables verified")
            else:
                logger.warning(f"⚠️ Expected 4 tables, found {len(tables)}")

            return True

        except Exception as e:
            logger.error(f"❌ Installation validation failed: {e}")
            return False

    def _post_installation_setup(self) -> bool:
        """Post - installation setup and instructions."""
        logger.info("📋 Post - installation setup...")

        try:
            # Create quick start script
            self._create_quick_start_script()

            # Generate installation report
            self._generate_installation_report()

            return True

        except Exception as e:
            logger.error(f"❌ Post - installation setup failed: {e}")
            return False

    def _create_quick_start_script(self):
        """Create a quick start script."""
        if self.system_info["platform"] == "Windows":
            script_name = "quick_start.bat"
            script_content = """@echo off"""
echo Starting AI CEO Automation System...
python start_ai_ceo.py
pause
""""""
        else:
            script_name = "quick_start.sh"
            script_content = """#!/bin/bash"""
echo "Starting AI CEO Automation System..."
python start_ai_ceo.py
""""""

        script_path = self.installation_path / script_name
        with open(script_path, "w") as f:
            f.write(script_content)

        if self.system_info["platform"] != "Windows":
            script_path.chmod(0o755)

        logger.info(f"✅ Created quick start script: {script_name}")

    def _generate_installation_report(self):
        """Generate installation report."""
        report_content = f""""""
# AI CEO Automation System - Installation Report

Installation completed on: {self._get_timestamp()}
System: {self.system_info['platform']} {self.system_info['platform_version']}
Python: {self.system_info['python_version']}
Installation Path: {self.installation_path}

## Installation Status
- System Requirements: {'✅ Passed' if len(self.errors) == 0 else '❌ Issues Found'}
- Dependencies: {'✅ Installed' if len(self.errors) == 0 else '❌ Issues Found'}
- Configuration: {'✅ Created' if len(self.errors) == 0 else '❌ Issues Found'}
- Database: {'✅ Initialized' if len(self.errors) == 0 else '❌ Issues Found'}

## Next Steps

1. **Configure API Keys:**
    Edit the `.env` file and add your API keys:
   ```
   OPENAI_API_KEY = your_key_here
   YOUTUBE_API_KEY = your_key_here
   # ... other keys
   ```

2. **Start the System:**
    ```bash
   python start_ai_ceo.py
   ```

   Or use the quick start script:
   ```bash
   ./quick_start.sh  # Linux/Mac
   quick_start.bat   # Windows
   ```

3. **Access Dashboard:**
    Open your browser to: http://localhost:5000

4. **Read Documentation:**
    See README_AI_CEO.md for detailed instructions

## Support

If you encounter issues:
1. Check the installation log: ai_ceo_installation.log
2. Review system requirements in README_AI_CEO.md
3. Verify API keys in .env file
4. Check system status: python start_ai_ceo.py --status

## Errors and Warnings

{'Errors: ' + str(len(self.errors)) if self.errors else 'No errors detected'}
{'Warnings: ' + str(len(self.warnings)) if self.warnings else 'No warnings'}

{chr(10).join(f'- {error}' for error in self.errors) if self.errors else ''}
{chr(10).join(f'- {warning}' for warning in self.warnings) if self.warnings else ''}
""""""

        report_path = self.installation_path / "INSTALLATION_REPORT.md"
        with open(report_path, "w") as f:
            f.write(report_content)

        logger.info(f"✅ Installation report saved: {report_path}")

    def _get_timestamp(self) -> str:
        """Get current timestamp."""

        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _print_installation_summary(self, success: bool):
        """Print installation summary."""
        logger.info("\\n" + "=" * 60)

        if success and len(self.errors) == 0:
            logger.info("🎉 AI CEO INSTALLATION COMPLETED SUCCESSFULLY!")
            logger.info("\\n🚀 Your AI CEO Automation System is ready!")
            logger.info("\\n📋 Next Steps:")
            logger.info("1. Edit .env file with your API keys")
            logger.info("2. Run: python start_ai_ceo.py")
            logger.info("3. Open: http://localhost:5000")
            logger.info("4. Read: README_AI_CEO.md")
        else:
            logger.error("❌ INSTALLATION COMPLETED WITH ISSUES")
            logger.error(
                f"\\n📋 Found {len(self.errors)} errors \"
#     and {len(self.warnings)} warnings"
# BRACKET_SURGEON: disabled
#             )
            logger.error("\\n🔧 Please review the installation log and fix issues before starting")

            if self.errors:
                logger.error("\\n❌ Errors:")
                for error in self.errors:
                    logger.error(f"  - {error}")

        logger.info("\\n📄 Full installation report: INSTALLATION_REPORT.md")
        logger.info("📄 Installation log: ai_ceo_installation.log")
        logger.info("=" * 60)


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="AI CEO Automation System Installer")
    parser.add_argument("--quick", action="store_true", help="Quick installation (skip prompts)")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--check - only", action="store_true", help="Only check requirements")

    args = parser.parse_args()

    try:
        installer = AICEOInstaller(quick_install=args.quick, dev_mode=args.dev)

        if args.check_only:
            # Only run system checks
            success = installer._check_system_requirements()
            sys.exit(0 if success else 1)

        # Run full installation
        success = installer.install()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("\\n🛑 Installation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\\n❌ Installation failed with critical error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()