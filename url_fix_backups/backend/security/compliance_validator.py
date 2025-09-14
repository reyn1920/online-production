#!/usr / bin / env python3
"""
Compliance Validator - Ensures TRAE.AI system meets security and operational standards
Validates configuration, dependencies, and deployment readiness
"""

import hashlib
import json
import logging
import os
import re
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class ComplianceCheck:
    """Represents a compliance check result"""

    check_id: str
    category: str
    title: str
    description: str
    status: str  # passed, failed, warning, skipped
    severity: str  # critical, high, medium, low
    details: str = ""
    remediation: str = ""
    evidence: List[str] = None


    def __post_init__(self):
        if self.evidence is None:
            self.evidence = []

@dataclass


class ComplianceReport:
    """Complete compliance validation report"""

    report_id: str
    timestamp: str
    target_path: str
    checks: List[ComplianceCheck]
    summary: Dict[str, int]
    overall_status: str  # compliant, non_compliant, partial
    compliance_score: float  # 0 - 100
    duration_seconds: float
    metadata: Dict[str, Any]


class ComplianceValidator:
    """Validates TRAE.AI system compliance with security and operational standards"""


    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)

        # Required files and directories
        self.required_structure = {
            "files": [
                "README.md",
                    "requirements.txt",
                    ".gitignore",
                    "app / dashboard.py",
                    "backend / core / secret_store_bridge.py",
                    "scripts / phoenix_protocol.sh",
                    ],
                "directories": [
                "app",
                    "backend / core",
                    "backend / runner",
                    "backend / security",
                    "scripts",
                    "assets / incoming",
                    "assets / releases",
                    "assets / temp",
                    "assets / archive",
                    "tests",
                    ],
                }


    def validate_project_structure(self, project_path: str) -> Dict[str, Any]:
        """
        Validate overall project structure and organization

        Args:
            project_path: Path to project root

        Returns:
            Dict with validation results
        """
        checks = []

        # Check for essential directories
        essential_dirs = ["backend", "app", "scripts", "tests"]
        for dir_name in essential_dirs:
            dir_path = Path(project_path) / dir_name
            checks.append(
                {
                    "check": f"Directory {dir_name} exists",
                        "status": "pass" if dir_path.exists() else "fail",
                        "path": str(dir_path),
                        }
            )

        # Check for configuration files
        config_files = ["requirements.txt", "package.json", ".env.example"]
        for file_name in config_files:
            file_path = Path(project_path) / file_name
            checks.append(
                {
                    "check": f"Config file {file_name}",
                        "status": "pass" if file_path.exists() else "info",
                        "path": str(file_path),
                        }
            )

        passed = sum(1 for check in checks if check["status"] == "pass")
        total = len([c for c in checks if c["status"] in ["pass", "fail"]])

        return {
            "status": "ok",
                "checks": checks,
                "summary": f"{passed}/{total} essential checks passed",
                }

        # Security configuration requirements
        self.security_requirements = {
            "env_files": [".env.example", ".env.local"],
                "secret_patterns": [
                r'(?i)(password|secret|key|token)\\s*=\\s*["\\'][^"\\'>\\s]+["\\']',
                    r'(?i)api[_-]?key\\s*=\\s*["\\'][^"\\'>\\s]+["\\']',
                    ],
                "required_gitignore_entries": [
                ".env",
                    ".env.local",
                    "__pycache__",
                    "node_modules",
                    "*.log",
                    ".DS_Store",
                    ],
                }

        # Dependency security requirements
        self.dependency_requirements = {
            "python": {
                "file": "requirements.txt",
                    "vulnerable_packages": [
                    "django < 3.2",
                        "flask < 2.0",
                        "requests < 2.20",
                        "urllib3 < 1.24",
                        ],
                    },
                "javascript": {
                "file": "package.json",
                    "vulnerable_packages": [
                    "lodash < 4.17.21",
                        "axios < 0.21.1",
                        "express < 4.17.1",
                        ],
                    },
                }

        logger.info(f"Compliance validator initialized for {self.base_dir}")


    def validate_compliance(self) -> ComplianceReport:
        """Run complete compliance validation"""
        start_time = datetime.now()
        report_id = f"compliance_{int(start_time.timestamp())}"

        logger.info("Starting compliance validation")

        checks = []

        # Run all compliance checks
        checks.extend(self._check_project_structure())
        checks.extend(self._check_security_configuration())
        checks.extend(self._check_dependency_security())
        checks.extend(self._check_file_permissions())
        checks.extend(self._check_git_configuration())
        checks.extend(self._check_deployment_readiness())
        checks.extend(self._check_documentation())
        checks.extend(self._check_testing_framework())

        # Calculate summary and scores
        summary = self._calculate_summary(checks)
        overall_status, compliance_score = self._calculate_compliance_score(checks)

        duration = (datetime.now() - start_time).total_seconds()

        report = ComplianceReport(
            report_id = report_id,
                timestamp = start_time.isoformat(),
                target_path = str(self.base_dir),
                checks = checks,
                summary = summary,
                overall_status = overall_status,
                compliance_score = compliance_score,
                duration_seconds = duration,
                metadata={"total_checks": len(checks), "validator_version": "1.0.0"},
                )

        logger.info(
            f"Compliance validation completed: {overall_status} ({compliance_score:.1f}%)"
        )

        return report


    def _check_project_structure(self) -> List[ComplianceCheck]:
        """Validate required project structure"""
        checks = []

        # Check required files
        for required_file in self.required_structure["files"]:
            file_path = self.base_dir / required_file

            if file_path.exists():
                checks.append(
                    ComplianceCheck(
                        check_id = f"structure_file_{required_file.replace('/', '_').replace('.', '_')}",
                            category="structure",
                            title = f"Required file: {required_file}",
                            description = f"File {required_file} exists",
                            status="passed",
                            severity="medium",
                            evidence=[str(file_path)],
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id = f"structure_file_{required_file.replace('/', '_').replace('.', '_')}",
                            category="structure",
                            title = f"Missing required file: {required_file}",
                            description = f"Required file {required_file} is missing",
                            status="failed",
                            severity="high",
                            remediation = f"Create the required file: {required_file}",
                            )
                )

        # Check required directories
        for required_dir in self.required_structure["directories"]:
            dir_path = self.base_dir / required_dir

            if dir_path.exists() and dir_path.is_dir():
                checks.append(
                    ComplianceCheck(
                        check_id = f"structure_dir_{required_dir.replace('/', '_')}",
                            category="structure",
                            title = f"Required directory: {required_dir}",
                            description = f"Directory {required_dir} exists",
                            status="passed",
                            severity="medium",
                            evidence=[str(dir_path)],
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id = f"structure_dir_{required_dir.replace('/', '_')}",
                            category="structure",
                            title = f"Missing required directory: {required_dir}",
                            description = f"Required directory {required_dir} is missing",
                            status="failed",
                            severity="high",
                            remediation = f"Create the required directory: mkdir -p {required_dir}",
                            )
                )

        return checks


    def _check_security_configuration(self) -> List[ComplianceCheck]:
        """Validate security configuration"""
        checks = []

        # Check for .env.example file
        env_example = self.base_dir/".env.example"
        if env_example.exists():
            checks.append(
                ComplianceCheck(
                    check_id="security_env_example",
                        category="security",
                        title="Environment template exists",
                        description=".env.example file provides template for environment variables",
                        status="passed",
                        severity="medium",
                        evidence=[str(env_example)],
                        )
            )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="security_env_example",
                        category="security",
                        title="Missing environment template",
                        description="No .env.example file found",
                        status="failed",
                        severity="medium",
                        remediation="Create .env.example with required environment variables",
                        )
            )

        # Check .gitignore for sensitive files
        gitignore_path = self.base_dir/".gitignore"
        if gitignore_path.exists():
            try:
                with open(gitignore_path, "r", encoding="utf - 8") as f:
                    gitignore_content = f.read()

                missing_entries = []
                for required_entry in self.security_requirements[
                    "required_gitignore_entries"
                ]:
                    if required_entry not in gitignore_content:
                        missing_entries.append(required_entry)

                if not missing_entries:
                    checks.append(
                        ComplianceCheck(
                            check_id="security_gitignore",
                                category="security",
                                title="Gitignore properly configured",
                                description="All required entries present in .gitignore",
                                status="passed",
                                severity="high",
                                evidence=[str(gitignore_path)],
                                )
                    )
                else:
                    checks.append(
                        ComplianceCheck(
                            check_id="security_gitignore",
                                category="security",
                                title="Incomplete gitignore configuration",
                                description = f"Missing entries in .gitignore: {', '.join(missing_entries)}",
                                status="failed",
                                severity="high",
                                remediation = f"Add missing entries to .gitignore: {', '.join(missing_entries)}",
                                )
                    )

            except Exception as e:
                checks.append(
                    ComplianceCheck(
                        check_id="security_gitignore",
                            category="security",
                            title="Gitignore read error",
                            description = f"Failed to read .gitignore: {e}",
                            status="failed",
                            severity="medium",
                            )
                )

        # Check for hardcoded secrets in main files
        secret_violations = []
        main_files = ["app / dashboard.py", "backend / core / secret_store_bridge.py"]

        for file_path in main_files:
            full_path = self.base_dir / file_path
            if full_path.exists():
                try:
                    with open(full_path, "r", encoding="utf - 8", errors="ignore") as f:
                        content = f.read()

                    for pattern in self.security_requirements["secret_patterns"]:
                        matches = re.findall(pattern, content)
                        if matches:
                            secret_violations.append(
                                f"{file_path}: {len(matches)} potential secrets"
                            )

                except Exception as e:
                    logger.warning(f"Failed to scan {file_path}: {e}")

        if not secret_violations:
            checks.append(
                ComplianceCheck(
                    check_id="security_no_hardcoded_secrets",
                        category="security",
                        title="No hardcoded secrets detected",
                        description="Main application files do not contain hardcoded secrets",
                        status="passed",
                        severity="critical",
                        )
            )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="security_no_hardcoded_secrets",
                        category="security",
                        title="Potential hardcoded secrets detected",
                        description = f"Found potential secrets: {'; '.join(secret_violations)}",
                        status="failed",
                        severity="critical",
                        remediation="Remove hardcoded secrets \
    and use environment variables or secret store",
                        )
            )

        return checks


    def _check_dependency_security(self) -> List[ComplianceCheck]:
        """Validate dependency security"""
        checks = []

        # Check Python dependencies
        requirements_file = self.base_dir/"requirements.txt"
        if requirements_file.exists():
            try:
                with open(requirements_file, "r", encoding="utf - 8") as f:
                    requirements_content = f.read()

                vulnerable_found = []
                for vulnerable_pkg in self.dependency_requirements["python"][
                    "vulnerable_packages"
                ]:
                    if vulnerable_pkg.split("<")[0] in requirements_content:
                        # Simple check - in production, use proper version parsing
                        vulnerable_found.append(vulnerable_pkg)

                if not vulnerable_found:
                    checks.append(
                        ComplianceCheck(
                            check_id="security_python_dependencies",
                                category="security",
                                title="Python dependencies secure",
                                description="No known vulnerable Python packages detected",
                                status="passed",
                                severity="high",
                                evidence=[str(requirements_file)],
                                )
                    )
                else:
                    checks.append(
                        ComplianceCheck(
                            check_id="security_python_dependencies",
                                category="security",
                                title="Vulnerable Python dependencies",
                                description = f"Potentially vulnerable packages: {', '.join(vulnerable_found)}",
                                status="failed",
                                severity="high",
                                remediation="Update vulnerable packages to secure versions",
                                )
                    )

            except Exception as e:
                checks.append(
                    ComplianceCheck(
                        check_id="security_python_dependencies",
                            category="security",
                            title="Failed to check Python dependencies",
                            description = f"Error reading requirements.txt: {e}",
                            status="failed",
                            severity="medium",
                            )
                )

        # Check for package - lock.json or yarn.lock for JavaScript projects
        package_json = self.base_dir/"package.json"
        if package_json.exists():
            lock_files = [
                self.base_dir/"package - lock.json",
                    self.base_dir/"yarn.lock",
                    ]

            has_lock_file = any(lock_file.exists() for lock_file in lock_files)

            if has_lock_file:
                checks.append(
                    ComplianceCheck(
                        check_id="security_js_lock_file",
                            category="security",
                            title="JavaScript dependencies locked",
                            description="Lock file ensures reproducible builds",
                            status="passed",
                            severity="medium",
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id="security_js_lock_file",
                            category="security",
                            title="Missing JavaScript lock file",
                            description="No package - lock.json or yarn.lock found",
                            status="warning",
                            severity="medium",
                            remediation="Run 'npm install' \
    or 'yarn install' to generate lock file",
                            )
                )

        return checks


    def _check_file_permissions(self) -> List[ComplianceCheck]:
        """Validate file permissions"""
        checks = []

        # Check script file permissions
        script_files = list(self.base_dir.glob("scripts/*.sh"))

        executable_scripts = 0
        non_executable_scripts = []

        for script_file in script_files:
            if os.access(script_file, os.X_OK):
                executable_scripts += 1
            else:
                non_executable_scripts.append(str(script_file.name))

        if script_files:
            if not non_executable_scripts:
                checks.append(
                    ComplianceCheck(
                        check_id="permissions_scripts_executable",
                            category="permissions",
                            title="Script files properly executable",
                            description = f"All {len(script_files)} script files have execute permissions",
                            status="passed",
                            severity="medium",
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id="permissions_scripts_executable",
                            category="permissions",
                            title="Non - executable script files",
                            description = f"Scripts without execute permissions: {', '.join(non_executable_scripts)}",
                            status="failed",
                            severity="medium",
                            remediation="Make scripts executable: chmod +x scripts/*.sh",
                            )
                )

        # Check for world - writable files
        world_writable_files = []

        for file_path in self.base_dir.rglob("*"):
            if file_path.is_file():
                try:
                    stat_info = file_path.stat()
                    if stat_info.st_mode & 0o002:  # World writable
                        world_writable_files.append(
                            str(file_path.relative_to(self.base_dir))
                        )
                except Exception:
                    continue

        if not world_writable_files:
            checks.append(
                ComplianceCheck(
                    check_id="permissions_no_world_writable",
                        category="permissions",
                        title="No world - writable files",
                        description="No files are writable by all users",
                        status="passed",
                        severity="high",
                        )
            )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="permissions_no_world_writable",
                        category="permissions",
                        title="World - writable files detected",
                        description = f"Files writable by all users: {', '.join(world_writable_files[:5])}",
                        status="failed",
                        severity="high",
                        remediation="Remove world - write permissions: chmod o - w <files>",
                        )
            )

        return checks


    def _check_git_configuration(self) -> List[ComplianceCheck]:
        """Validate Git configuration"""
        checks = []

        # Check if .git directory exists
        git_dir = self.base_dir/".git"
        if git_dir.exists():
            checks.append(
                ComplianceCheck(
                    check_id="git_repository_initialized",
                        category="git",
                        title="Git repository initialized",
                        description="Project is under version control",
                        status="passed",
                        severity="medium",
                        )
            )

            # Check for .gitignore
            gitignore = self.base_dir/".gitignore"
            if gitignore.exists():
                checks.append(
                    ComplianceCheck(
                        check_id="git_gitignore_exists",
                            category="git",
                            title="Gitignore file exists",
                            description="Repository has .gitignore file",
                            status="passed",
                            severity="medium",
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id="git_gitignore_exists",
                            category="git",
                            title="Missing gitignore file",
                            description="No .gitignore file found",
                            status="failed",
                            severity="medium",
                            remediation="Create .gitignore file to exclude sensitive files",
                            )
                )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="git_repository_initialized",
                        category="git",
                        title="Git repository not initialized",
                        description="Project is not under version control",
                        status="warning",
                        severity="low",
                        remediation="Initialize Git repository: git init",
                        )
            )

        return checks


    def _check_deployment_readiness(self) -> List[ComplianceCheck]:
        """Validate deployment readiness"""
        checks = []

        # Check for deployment scripts
        deployment_files = [
            "scripts / phoenix_protocol.sh",
                "Dockerfile",
                "docker - compose.yml",
                ".github / workflows / deploy.yml",
                ]

        deployment_methods = 0
        for deploy_file in deployment_files:
            if (self.base_dir / deploy_file).exists():
                deployment_methods += 1

        if deployment_methods > 0:
            checks.append(
                ComplianceCheck(
                    check_id="deployment_method_available",
                        category="deployment",
                        title="Deployment method configured",
                        description = f"Found {deployment_methods} deployment configuration(s)",
                        status="passed",
                        severity="medium",
                        )
            )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="deployment_method_available",
                        category="deployment",
                        title="No deployment method configured",
                        description="No deployment scripts or configurations found",
                        status="warning",
                        severity="medium",
                        remediation="Create deployment scripts or Docker configuration",
                        )
            )

        # Check for environment configuration
        env_files = [".env.example", ".env.template"]
        has_env_template = any(
            (self.base_dir / env_file).exists() for env_file in env_files
        )

        if has_env_template:
            checks.append(
                ComplianceCheck(
                    check_id="deployment_env_template",
                        category="deployment",
                        title="Environment template available",
                        description="Environment variable template exists for deployment",
                        status="passed",
                        severity="medium",
                        )
            )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="deployment_env_template",
                        category="deployment",
                        title="Missing environment template",
                        description="No environment variable template for deployment",
                        status="failed",
                        severity="medium",
                        remediation="Create .env.example with required environment variables",
                        )
            )

        return checks


    def _check_documentation(self) -> List[ComplianceCheck]:
        """Validate documentation"""
        checks = []

        # Check README.md
        readme_path = self.base_dir/"README.md"
        if readme_path.exists():
            try:
                with open(readme_path, "r", encoding="utf - 8") as f:
                    readme_content = f.read()

                required_sections = ["installation", "usage", "configuration"]
                missing_sections = []

                for section in required_sections:
                    if section.lower() not in readme_content.lower():
                        missing_sections.append(section)

                if not missing_sections:
                    checks.append(
                        ComplianceCheck(
                            check_id="documentation_readme_complete",
                                category="documentation",
                                title="README documentation complete",
                                description="README contains all required sections",
                                status="passed",
                                severity="low",
                                )
                    )
                else:
                    checks.append(
                        ComplianceCheck(
                            check_id="documentation_readme_complete",
                                category="documentation",
                                title="Incomplete README documentation",
                                description = f"Missing sections: {', '.join(missing_sections)}",
                                status="warning",
                                severity="low",
                                remediation = f"Add missing sections to README: {', '.join(missing_sections)}",
                                )
                    )

            except Exception as e:
                checks.append(
                    ComplianceCheck(
                        check_id="documentation_readme_complete",
                            category="documentation",
                            title="README read error",
                            description = f"Failed to read README: {e}",
                            status="failed",
                            severity="low",
                            )
                )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="documentation_readme_exists",
                        category="documentation",
                        title="Missing README file",
                        description="No README.md file found",
                        status="failed",
                        severity="medium",
                        remediation="Create README.md with project documentation",
                        )
            )

        return checks


    def _check_testing_framework(self) -> List[ComplianceCheck]:
        """Validate testing framework"""
        checks = []

        # Check for test directory
        test_dirs = ["tests", "test"]
        has_test_dir = any(
            (self.base_dir / test_dir).exists() for test_dir in test_dirs
        )

        if has_test_dir:
            checks.append(
                ComplianceCheck(
                    check_id="testing_directory_exists",
                        category="testing",
                        title="Test directory exists",
                        description="Project has dedicated test directory",
                        status="passed",
                        severity="medium",
                        )
            )

            # Check for test files
            test_files = []
            for test_dir in test_dirs:
                test_path = self.base_dir / test_dir
                if test_path.exists():
                    test_files.extend(list(test_path.glob("test_*.py")))
                    test_files.extend(list(test_path.glob("*_test.py")))

            if test_files:
                checks.append(
                    ComplianceCheck(
                        check_id="testing_files_exist",
                            category="testing",
                            title="Test files exist",
                            description = f"Found {len(test_files)} test files",
                            status="passed",
                            severity="medium",
                            )
                )
            else:
                checks.append(
                    ComplianceCheck(
                        check_id="testing_files_exist",
                            category="testing",
                            title="No test files found",
                            description="Test directory exists but no test files found",
                            status="warning",
                            severity="medium",
                            remediation="Create test files in the test directory",
                            )
                )
        else:
            checks.append(
                ComplianceCheck(
                    check_id="testing_directory_exists",
                        category="testing",
                        title="No test directory",
                        description="No test directory found",
                        status="failed",
                        severity="medium",
                        remediation="Create tests directory and add test files",
                        )
            )

        return checks


    def _calculate_summary(self, checks: List[ComplianceCheck]) -> Dict[str, int]:
        """Calculate summary statistics"""
        summary = {
            "total": len(checks),
                "passed": 0,
                "failed": 0,
                "warning": 0,
                "skipped": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                }

        for check in checks:
            summary[check.status] += 1
            summary[check.severity] += 1

        return summary


    def _calculate_compliance_score(
        self, checks: List[ComplianceCheck]
    ) -> Tuple[str, float]:
        """Calculate overall compliance score and status"""
        if not checks:
            return "unknown", 0.0

        # Weight checks by severity
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}

        total_weight = 0
        passed_weight = 0

        for check in checks:
            weight = severity_weights.get(check.severity, 1)
            total_weight += weight

            if check.status == "passed":
                passed_weight += weight
            elif check.status == "warning":
                passed_weight += weight * 0.5  # Partial credit for warnings

        if total_weight == 0:
            return "unknown", 0.0

        score = (passed_weight / total_weight) * 100

        # Determine overall status
        critical_failures = sum(
            1
            for check in checks
            if check.status == "failed" and check.severity == "critical"
        )
        high_failures = sum(
            1
            for check in checks
            if check.status == "failed" and check.severity == "high"
        )

        if critical_failures > 0:
            status = "non_compliant"
        elif high_failures > 2 or score < 70:
            status = "partial"
        elif score >= 90:
            status = "compliant"
        else:
            status = "partial"

        return status, score


    def export_report(self, report: ComplianceReport, output_path: str) -> bool:
        """Export compliance report to file"""
        try:
            export_data = {
                "report_id": report.report_id,
                    "timestamp": report.timestamp,
                    "target_path": report.target_path,
                    "summary": report.summary,
                    "overall_status": report.overall_status,
                    "compliance_score": report.compliance_score,
                    "duration_seconds": report.duration_seconds,
                    "metadata": report.metadata,
                    "checks": [asdict(check) for check in report.checks],
                    }

            output_file = Path(output_path)
            with open(output_file, "w", encoding="utf - 8") as f:
                json.dump(export_data, f, indent = 2, ensure_ascii = False)

            logger.info(f"Compliance report exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return False


def main():
    """Command - line interface for compliance validator"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Compliance Validator - TRAE.AI system compliance validation"
    )
    parser.add_argument(
        "--base - dir",
    default=".",
    help="Base directory to validate (default: current)"
    )
    parser.add_argument("--output", help="Output file for report (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--fail - on - non - compliant",
            action="store_true",
            help="Exit with error code if not compliant",
            )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    validator = ComplianceValidator(args.base_dir)
    report = validator.validate_compliance()

    # Print summary
    print("\\n=== Compliance Validation Report ===")
    print(f"Overall Status: {report.overall_status.upper()}")
    print(f"Compliance Score: {report.compliance_score:.1f}%")
    print(f"Duration: {report.duration_seconds:.2f}s")

    print(f"\\nSummary:")
    print(f"  Total Checks: {report.summary['total']}")
    print(f"  Passed: {report.summary['passed']}")
    print(f"  Failed: {report.summary['failed']}")
    print(f"  Warnings: {report.summary['warning']}")

    print(f"\\nBy Severity:")
    print(f"  Critical: {report.summary['critical']}")
    print(f"  High: {report.summary['high']}")
    print(f"  Medium: {report.summary['medium']}")
    print(f"  Low: {report.summary['low']}")

    # Show failed checks
    failed_checks = [check for check in report.checks if check.status == "failed"]
    if failed_checks:
        print(f"\\nFailed Checks ({len(failed_checks)}):")
        for check in failed_checks[:10]:  # Show first 10
            print(f"  [{check.severity.upper()}] {check.title}")
            if check.remediation:
                print(f"    Remediation: {check.remediation}")

        if len(failed_checks) > 10:
            print(f"  ... and {len(failed_checks) - 10} more failed checks")

    # Export report if requested
    if args.output:
        if validator.export_report(report, args.output):
            print(f"\\nReport exported to {args.output}")
        else:
            print(f"\\nFailed to export report to {args.output}")

    # Exit with appropriate code
    if args.fail_on_non_compliant and report.overall_status == "non_compliant":
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    main()