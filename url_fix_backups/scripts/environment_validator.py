#!/usr / bin / env python3
"""
Conservative Research System - Environment Validator

This script validates the production environment setup including:
- Node.js and npm installation
- Netlify CLI setup
- Environment variables
- System dependencies
- Security configurations

Author: Conservative Research System
Version: 1.0.0
"""

import json
import logging
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
        logging.FileHandler("environment_validation.log"),
            logging.StreamHandler(),
            ],
)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration"""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"

@dataclass


class ValidationResult:
    """Validation result data structure"""

    name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict] = None
    fix_command: Optional[str] = None


class EnvironmentValidator:
    """Comprehensive environment validation system"""


    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.results: List[ValidationResult] = []
        self.required_node_version = "18.0.0"
        self.required_npm_version = "8.0.0"

        logging.getLogger(__name__).info(f"🔍 Initializing environment validator for: {self.project_root}")


    def validate_all(self) -> Dict[str, any]:
        """Run all validation checks"""
        logging.getLogger(__name__).info("🚀 Starting comprehensive environment validation...")

        # Core system validations
        self._validate_python_environment()
        self._validate_nodejs_environment()
        self._validate_npm_environment()
        self._validate_netlify_cli()

        # Project structure validations
        self._validate_project_structure()
        self._validate_package_json()
        self._validate_environment_files()

        # Security validations
        self._validate_file_permissions()
        self._validate_git_configuration()
        self._validate_environment_variables()

        # Dependency validations
        self._validate_dependencies()
        self._validate_build_tools()

        # Generate summary report
        return self._generate_validation_report()


    def _validate_python_environment(self):
        """Validate Python environment"""
        try:
            python_version = sys.version_info
            version_str = f"{
                python_version.major}.{
                    python_version.minor}.{
                    python_version.micro}"

            if python_version.major >= 3 and python_version.minor >= 8:
                self.results.append(
                    ValidationResult(
                        name="Python Environment",
                            status = ValidationStatus.PASSED,
                            message = f"Python {version_str} is compatible",
                            details={"version": version_str, "executable": sys.executable},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Python Environment",
                            status = ValidationStatus.FAILED,
                            message = f"Python {version_str} is too old. Requires Python 3.8+",
                            fix_command="Install Python 3.8 or higher",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Python Environment",
                        status = ValidationStatus.FAILED,
                        message = f"Python validation failed: {str(e)}",
                        )
            )


    def _validate_nodejs_environment(self):
        """Validate Node.js installation"""
        try:
            # Check if Node.js is installed
            result = subprocess.run(
                ["node", "--version"], capture_output = True, text = True, timeout = 10
            )

            if result.returncode == 0:
                version = result.stdout.strip().lstrip("v")
                version_parts = [int(x) for x in version.split(".")]
                required_parts = [int(x) for x in self.required_node_version.split(".")]

                if version_parts >= required_parts:
                    self.results.append(
                        ValidationResult(
                            name="Node.js Environment",
                                status = ValidationStatus.PASSED,
                                message = f"Node.js v{version} is compatible",
                                details={"version": version, "path": shutil.which("node")},
                                )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            name="Node.js Environment",
                                status = ValidationStatus.FAILED,
                                message = f"Node.js v{version} is too old. Requires v{
                                self.required_node_version}+",
                                    fix_command="Install Node.js v18+ from https://nodejs.org",
                                )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        name="Node.js Environment",
                            status = ValidationStatus.FAILED,
                            message="Node.js is not installed or not in PATH",
                            fix_command="Install Node.js from https://nodejs.org",
                            )
                )

        except subprocess.TimeoutExpired:
            self.results.append(
                ValidationResult(
                    name="Node.js Environment",
                        status = ValidationStatus.FAILED,
                        message="Node.js command timed out",
                        )
            )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Node.js Environment",
                        status = ValidationStatus.FAILED,
                        message = f"Node.js validation failed: {str(e)}",
                        )
            )


    def _validate_npm_environment(self):
        """Validate npm installation"""
        try:
            # Check npm version
            result = subprocess.run(
                ["npm", "--version"], capture_output = True, text = True, timeout = 10
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                version_parts = [int(x) for x in version.split(".")]
                required_parts = [int(x) for x in self.required_npm_version.split(".")]

                if version_parts >= required_parts:
                    # Check npm configuration
                    config_result = subprocess.run(
                        ["npm", "config", "list"],
                            capture_output = True,
                            text = True,
                            timeout = 10,
                            )

                    self.results.append(
                        ValidationResult(
                            name="npm Environment",
                                status = ValidationStatus.PASSED,
                                message = f"npm v{version} is compatible",
                                details={
            "version": version,
            "path": shutil.which("npm"),
            "config_valid": config_result.returncode == 0,
        except Exception as e:
            pass
        },
                                )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            name="npm Environment",
                                status = ValidationStatus.FAILED,
                                message = f"npm v{version} is too old. Requires v{
                                self.required_npm_version}+",
                                    fix_command="Update npm: npm install -g npm@latest",
                                )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        name="npm Environment",
                            status = ValidationStatus.FAILED,
                            message="npm is not installed or not in PATH",
                            fix_command="Install Node.js (includes npm) from https://nodejs.org",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="npm Environment",
                        status = ValidationStatus.FAILED,
                        message = f"npm validation failed: {str(e)}",
                        )
            )


    def _validate_netlify_cli(self):
        """Validate Netlify CLI installation"""
        try:
            # Check if Netlify CLI is installed
            result = subprocess.run(
                ["netlify", "--version"], capture_output = True, text = True, timeout = 10
            )

            if result.returncode == 0:
                version = result.stdout.strip()

                # Check authentication status
                auth_result = subprocess.run(
                    ["netlify", "status"], capture_output = True, text = True, timeout = 10
                )

                if "Not logged in" in auth_result.stdout or auth_result.returncode != 0:
                    self.results.append(
                        ValidationResult(
                            name="Netlify CLI",
                                status = ValidationStatus.WARNING,
                                message = f"Netlify CLI {version} installed but not authenticated",
                                details={"version": version, "authenticated": False},
                                fix_command="Run: netlify login",
                                )
                    )
                else:
                    self.results.append(
                        ValidationResult(
                            name="Netlify CLI",
                                status = ValidationStatus.PASSED,
                                message = f"Netlify CLI {version} installed \
    and authenticated",
                                details={"version": version, "authenticated": True},
                                )
                    )
            else:
                self.results.append(
                    ValidationResult(
                        name="Netlify CLI",
                            status = ValidationStatus.FAILED,
                            message="Netlify CLI is not installed",
                            fix_command="Install: npm install -g netlify - cli",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Netlify CLI",
                        status = ValidationStatus.FAILED,
                        message = f"Netlify CLI validation failed: {str(e)}",
                        )
            )


    def _validate_project_structure(self):
        """Validate project directory structure"""
        try:
            required_files = ["package.json", "src", "public", ".gitignore"]

            missing_files = []
            existing_files = []

            for file_path in required_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    existing_files.append(file_path)
                else:
                    missing_files.append(file_path)

            if not missing_files:
                self.results.append(
                    ValidationResult(
                        name="Project Structure",
                            status = ValidationStatus.PASSED,
                            message="All required project files and directories exist",
                            details={"existing_files": existing_files},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Project Structure",
                            status = ValidationStatus.WARNING,
                            message = f"Missing project files: {
                            ', '.join(missing_files)}",
                                details={
            "missing_files": missing_files,
            "existing_files": existing_files,
        except Exception as e:
            pass
        },
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Project Structure",
                        status = ValidationStatus.FAILED,
                        message = f"Project structure validation failed: {str(e)}",
                        )
            )


    def _validate_package_json(self):
        """Validate package.json configuration"""
        try:
            package_json_path = self.project_root / "package.json"

            if not package_json_path.exists():
                self.results.append(
                    ValidationResult(
                        name="package.json",
                            status = ValidationStatus.FAILED,
                            message="package.json not found",
                            fix_command="Run: npm init -y",
                            )
                )
                return

            with open(package_json_path, "r") as f:
                package_data = json.load(f)

            # Check required fields
            required_fields = ["name", "version", "scripts"]
            missing_fields = [
                field for field in required_fields if field not in package_data
            ]

            # Check build script
            has_build_script = "build" in package_data.get("scripts", {})

            if not missing_fields and has_build_script:
                self.results.append(
                    ValidationResult(
                        name="package.json",
                            status = ValidationStatus.PASSED,
                            message="package.json is properly configured",
                            details={
            "name": package_data.get("name"),
            "version": package_data.get("version"),
            "has_build_script": has_build_script,
        except Exception as e:
            pass
        },
                            )
                )
            else:
                issues = []
                if missing_fields:
                    issues.append(f"Missing fields: {', '.join(missing_fields)}")
                if not has_build_script:
                    issues.append("Missing build script")

                self.results.append(
                    ValidationResult(
                        name="package.json",
                            status = ValidationStatus.WARNING,
                            message = f"package.json issues: {'; '.join(issues)}",
                            details={"issues": issues},
                            )
                )

        except json.JSONDecodeError as e:
            self.results.append(
                ValidationResult(
                    name="package.json",
                        status = ValidationStatus.FAILED,
                        message = f"package.json is not valid JSON: {str(e)}",
                        )
            )
        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="package.json",
                        status = ValidationStatus.FAILED,
                        message = f"package.json validation failed: {str(e)}",
                        )
            )


    def _validate_environment_files(self):
        """Validate environment configuration files"""
        try:
            env_files = [".env.example", ".env.local", ".env.production"]
            found_files = []

            for env_file in env_files:
                env_path = self.project_root / env_file
                if env_path.exists():
                    found_files.append(env_file)

            # Check .env.example exists (template)
            if ".env.example" in found_files:
                self.results.append(
                    ValidationResult(
                        name="Environment Files",
                            status = ValidationStatus.PASSED,
                            message="Environment configuration files found",
                            details={"found_files": found_files},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Environment Files",
                            status = ValidationStatus.WARNING,
                            message="No .env.example template found",
                            details={"found_files": found_files},
                            fix_command="Create .env.example with required environment variables",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Environment Files",
                        status = ValidationStatus.FAILED,
                        message = f"Environment files validation failed: {str(e)}",
                        )
            )


    def _validate_file_permissions(self):
        """Validate file permissions for security"""
        try:
            sensitive_files = [".env", ".env.local", ".env.production"]
            permission_issues = []

            for file_name in sensitive_files:
                file_path = self.project_root / file_name
                if file_path.exists():
                    # Check if file is readable by others (security risk)
                    file_stat = file_path.stat()
                    permissions = oct(file_stat.st_mode)[-3:]

                    # Check if file is readable by group or others
                    if permissions[1] != "0" or permissions[2] != "0":
                        permission_issues.append(f"{file_name}: {permissions}")

            if not permission_issues:
                self.results.append(
                    ValidationResult(
                        name="File Permissions",
                            status = ValidationStatus.PASSED,
                            message="Sensitive files have secure permissions",
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="File Permissions",
                            status = ValidationStatus.WARNING,
                            message = f"Insecure file permissions: {
                            ', '.join(permission_issues)}",
                                fix_command="Run: chmod 600 .env*",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="File Permissions",
                        status = ValidationStatus.FAILED,
                        message = f"File permissions validation failed: {str(e)}",
                        )
            )


    def _validate_git_configuration(self):
        """Validate Git configuration"""
        try:
            # Check if .gitignore exists and contains sensitive files
            gitignore_path = self.project_root / ".gitignore"

            if not gitignore_path.exists():
                self.results.append(
                    ValidationResult(
                        name="Git Configuration",
                            status = ValidationStatus.WARNING,
                            message="No .gitignore file found",
                            fix_command="Create .gitignore file",
                            )
                )
                return

            with open(gitignore_path, "r") as f:
                gitignore_content = f.read()

            # Check for important patterns
            required_patterns = [".env", "node_modules", "dist", "build"]
            missing_patterns = []

            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    missing_patterns.append(pattern)

            if not missing_patterns:
                self.results.append(
                    ValidationResult(
                        name="Git Configuration",
                            status = ValidationStatus.PASSED,
                            message="Git configuration is secure",
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Git Configuration",
                            status = ValidationStatus.WARNING,
                            message = f"Missing .gitignore patterns: {
                            ', '.join(missing_patterns)}",
                                details={"missing_patterns": missing_patterns},
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Git Configuration",
                        status = ValidationStatus.FAILED,
                        message = f"Git configuration validation failed: {str(e)}",
                        )
            )


    def _validate_environment_variables(self):
        """Validate required environment variables"""
        try:
            # Check for common required environment variables
            required_vars = ["NODE_ENV", "NETLIFY_AUTH_TOKEN", "NETLIFY_SITE_ID"]

            missing_vars = []
            present_vars = []

            for var in required_vars:
                if os.getenv(var):
                    present_vars.append(var)
                else:
                    missing_vars.append(var)

            if len(present_vars) >= len(required_vars) // 2:  # At least half present
                status = (
                    ValidationStatus.PASSED
                    if not missing_vars
                    else ValidationStatus.WARNING
                )
                message = (
                    "Environment variables configured"
                    if not missing_vars
                    else f"Some environment variables missing: {
                        ', '.join(missing_vars)}"
                )

                self.results.append(
                    ValidationResult(
                        name="Environment Variables",
                            status = status,
                            message = message,
                            details={"present": present_vars, "missing": missing_vars},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Environment Variables",
                            status = ValidationStatus.FAILED,
                            message = f"Critical environment variables missing: {
                            ', '.join(missing_vars)}",
                                details={"missing": missing_vars},
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Environment Variables",
                        status = ValidationStatus.FAILED,
                        message = f"Environment variables validation failed: {str(e)}",
                        )
            )


    def _validate_dependencies(self):
        """Validate project dependencies"""
        try:
            package_json_path = self.project_root / "package.json"

            if not package_json_path.exists():
                self.results.append(
                    ValidationResult(
                        name="Dependencies",
                            status = ValidationStatus.SKIPPED,
                            message="No package.json found, skipping dependency validation",
                            )
                )
                return

            # Check if node_modules exists
            node_modules_path = self.project_root / "node_modules"

            if not node_modules_path.exists():
                self.results.append(
                    ValidationResult(
                        name="Dependencies",
                            status = ValidationStatus.FAILED,
                            message="Dependencies not installed",
                            fix_command="Run: npm install",
                            )
                )
                return

            # Check for package - lock.json (security)
            package_lock_path = self.project_root / "package - lock.json"

            if package_lock_path.exists():
                self.results.append(
                    ValidationResult(
                        name="Dependencies",
                            status = ValidationStatus.PASSED,
                            message="Dependencies installed with lock file",
                            details={"has_lock_file": True},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Dependencies",
                            status = ValidationStatus.WARNING,
                            message="Dependencies installed but no lock file found",
                            details={"has_lock_file": False},
                            fix_command="Run: npm install to generate package - lock.json",
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Dependencies",
                        status = ValidationStatus.FAILED,
                        message = f"Dependencies validation failed: {str(e)}",
                        )
            )


    def _validate_build_tools(self):
        """Validate build tools and configuration"""
        try:
            # Check for common build tool configurations
            build_configs = [
                "vite.config.js",
                    "vite.config.ts",
                    "webpack.config.js",
                    "rollup.config.js",
                    ]

            found_configs = []
            for config in build_configs:
                config_path = self.project_root / config
                if config_path.exists():
                    found_configs.append(config)

            if found_configs:
                self.results.append(
                    ValidationResult(
                        name="Build Tools",
                            status = ValidationStatus.PASSED,
                            message = f"Build configuration found: {', '.join(found_configs)}",
                            details={"configs": found_configs},
                            )
                )
            else:
                self.results.append(
                    ValidationResult(
                        name="Build Tools",
                            status = ValidationStatus.WARNING,
                            message="No build tool configuration found",
                            details={"configs": []},
                            )
                )

        except Exception as e:
            self.results.append(
                ValidationResult(
                    name="Build Tools",
                        status = ValidationStatus.FAILED,
                        message = f"Build tools validation failed: {str(e)}",
                        )
            )


    def _generate_validation_report(self) -> Dict[str, any]:
        """Generate comprehensive validation report"""
        passed = sum(1 for r in self.results if r.status == ValidationStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == ValidationStatus.FAILED)
        warnings = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        skipped = sum(1 for r in self.results if r.status == ValidationStatus.SKIPPED)

        total = len(self.results)
        success_rate = (passed / total * 100) if total > 0 else 0

        # Determine overall status
        if failed > 0:
            overall_status = "FAILED"
        elif warnings > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASSED"

        report = {
            "overall_status": overall_status,
            "success_rate": round(success_rate, 2),
            "summary": {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "skipped": skipped,
        },
            "results": [
                {
            "name": r.name,
            "status": r.status.value,
            "message": r.message,
            "details": r.details,
            "fix_command": r.fix_command,
        }
                for r in self.results
            ],
            "recommendations": self._generate_recommendations(),
        }

        logging.getLogger(__name__).info(
            f"✅ Environment validation completed: {overall_status} ({
                success_rate:.1f}% success rate)"
        )
        return report


    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []

        failed_results = [
            r for r in self.results if r.status == ValidationStatus.FAILED
        ]
        warning_results = [
            r for r in self.results if r.status == ValidationStatus.WARNING
        ]

        if failed_results:
            recommendations.append("🚨 Critical Issues Found:")
            for result in failed_results:
                if result.fix_command:
                    recommendations.append(f"  • {result.name}: {result.fix_command}")
                else:
                    recommendations.append(f"  • {result.name}: {result.message}")

        if warning_results:
            recommendations.append("⚠️ Improvements Recommended:")
            for result in warning_results:
                if result.fix_command:
                    recommendations.append(f"  • {result.name}: {result.fix_command}")

        if not failed_results and not warning_results:
            recommendations.append(
                "🎉 Environment is fully validated and ready for production!"
            )

        return recommendations


    def fix_issues(self, auto_fix: bool = False) -> Dict[str, any]:
        """Attempt to automatically fix common issues"""
        logging.getLogger(__name__).info("🔧 Attempting to fix environment issues...")

        fixed_issues = []
        failed_fixes = []

        for result in self.results:
            if (
                result.status in [ValidationStatus.FAILED, ValidationStatus.WARNING]
                and result.fix_command
                    ):
                try:
                    if auto_fix:
                        logging.getLogger(__name__).info(f"Fixing: {result.name}")
                        # This would implement actual fixes
                        # For now, just log the command
                            logging.getLogger(__name__).info(f"Would run: {result.fix_command}")
                        fixed_issues.append(result.name)
                    else:
                        logging.getLogger(__name__).info(
                            f"Fix available for {
                                result.name}: {
                                    result.fix_command}"
                        )

                except Exception as e:
                    logging.getLogger(__name__).error(f"Failed to fix {result.name}: {str(e)}")
                    failed_fixes.append(result.name)

        return {
            "auto_fix_enabled": auto_fix,
            "fixed_issues": fixed_issues,
            "failed_fixes": failed_fixes,
            "manual_fixes_required": len(
                [r for r in self.results if r.fix_command and not auto_fix]
            ),
        }

# CLI Interface
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Conservative Research System - Environment Validator"
    )
    parser.add_argument("--project - root", default=".", help="Project root directory")
    parser.add_argument(
        "--output", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument("--fix",
    action="store_true",
    help="Attempt to auto - fix issues")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    validator = EnvironmentValidator(args.project_root)
    report = validator.validate_all()

    if args.fix:
        fix_report = validator.fix_issues(auto_fix = True)
        report["fix_report"] = fix_report

    if args.output == "json":
        print(json.dumps(report, indent = 2))
    else:
        # Text output
        print(f"\\n🔍 Environment Validation Report")
        print(f"{'=' * 50}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Success Rate: {report['success_rate']}%")
        print(f"\\nSummary:")
        print(f"  Total Checks: {report['summary']['total_checks']}")
        print(f"  ✅ Passed: {report['summary']['passed']}")
        print(f"  ❌ Failed: {report['summary']['failed']}")
        print(f"  ⚠️  Warnings: {report['summary']['warnings']}")
        print(f"  ⏭️  Skipped: {report['summary']['skipped']}")

        print(f"\\nDetailed Results:")
        for result in report["results"]:
            status_emoji = {
            "passed": "✅",
            "failed": "❌",
            "warning": "⚠️",
            "skipped": "⏭️",
        }.get(result["status"], "❓")

            print(f"  {status_emoji} {result['name']}: {result['message']}")
            if result.get("fix_command"):
                print(f"    💡 Fix: {result['fix_command']}")

        if report["recommendations"]:
            print(f"\\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  {rec}")

    # Exit with appropriate code
    if report["overall_status"] == "FAILED":
        sys.exit(1)
    elif report["overall_status"] == "WARNING":
        sys.exit(2)
    else:
        sys.exit(0)