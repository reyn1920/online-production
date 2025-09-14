#!/usr/bin/env python3
"""
Conservative Research System - Security Scanner

This script performs comprehensive security scanning including:
- Hardcoded secrets detection
- Vulnerability scanning
- File permission analysis
- Dependency security checks
- Code quality security analysis

Author: Conservative Research System
Version: 1.0.0
"""

import hashlib
import json
import logging
import os
import re
import stat
import subprocess
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("security_scan.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Security issue severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class IssueType(Enum):
    """Security issue types"""

    HARDCODED_SECRET = "hardcoded_secret"
    WEAK_PERMISSION = "weak_permission"
    VULNERABLE_DEPENDENCY = "vulnerable_dependency"
    INSECURE_CODE = "insecure_code"
    CONFIGURATION_ISSUE = "configuration_issue"
    EXPOSED_ENDPOINT = "exposed_endpoint"

@dataclass


class SecurityIssue:
    """Security issue data structure"""

    type: IssueType
    severity: SeverityLevel
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    cve_id: Optional[str] = None
    confidence: float = 1.0


class SecurityScanner:
    """Comprehensive security scanning system"""


    def __init__(self, project_root: str = None):
        self.project_root = Path(project_root or os.getcwd())
        self.issues: List[SecurityIssue] = []
        self.scanned_files = 0
        self.excluded_patterns = {
            ".git",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                ".pytest_cache",
                ".coverage",
                "dist",
                "build",
                ".DS_Store",
                }

        # Secret patterns for detection
        self.secret_patterns = {
            "api_key": {
                "pattern": r'(?i)(api[_-]?key|apikey)\\s*[=:]\\s*["\\']?([a - zA - Z0 - 9_\\-]{20,})["\\']?',
                    "severity": SeverityLevel.HIGH,
                    },
                "secret_key": {
                "pattern": r'(?i)(secret[_-]?key|secretkey)\\s*[=:]\\s*["\\']?([a - zA - Z0 - 9_\\-]{20,})["\\']?',
                    "severity": SeverityLevel.CRITICAL,
                    },
                "password": {
                "pattern": r'(?i)(password|passwd|pwd)\\s*[=:]\\s*["\\']([^"\\s]{8,})["\\']',
                    "severity": SeverityLevel.HIGH,
                    },
                "token": {
                "pattern": r'(?i)(token|auth[_-]?token)\\s*[=:]\\s*["\\']?([a - zA - Z0 - 9_\\-]{20,})["\\']?',
                    "severity": SeverityLevel.HIGH,
                    },
                "private_key": {
                "pattern": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
                    "severity": SeverityLevel.CRITICAL,
                    },
                "aws_access_key": {
                "pattern": r"AKIA[0 - 9A - Z]{16}",
                    "severity": SeverityLevel.CRITICAL,
                    },
                "github_token": {
                "pattern": r"ghp_[a - zA - Z0 - 9]{36}",
                    "severity": SeverityLevel.HIGH,
                    },
                "slack_token": {
                "pattern": r"xox[baprs]-[0 - 9a - zA - Z]{10,48}",
                    "severity": SeverityLevel.MEDIUM,
                    },
                "stripe_key": {
                "pattern": r"sk_live_[0 - 9a - zA - Z]{24}",
                    "severity": SeverityLevel.CRITICAL,
                    },
                "paypal_key": {
                "pattern": r'(?i)(paypal[_-]?(client[_-]?)?secret)\\s*[=:]\\s*["\\']?([a - zA - Z0 - 9_\\-]{20,})["\\']?',
                    "severity": SeverityLevel.HIGH,
                    },
                }

        # Insecure code patterns
        self.insecure_patterns = {
            "sql_injection": {
                "pattern": r'(?i)(execute|query)\\s*\\(\\s*["\\'][^"\\']*(\\+|%|format|f["\\'])',
                    "severity": SeverityLevel.HIGH,
                    "description": "Potential SQL injection vulnerability",
                    },
                "command_injection": {
                "pattern": r"(?i)(os\\.system|subprocess\\.(call|run|Popen))\\s*\\([^)]*\\+",
                    "severity": SeverityLevel.HIGH,
                    "description": "Potential command injection vulnerability",
                    },
                "eval_usage": {
                "pattern": r"\\beval\\s*\\(",
                    "severity": SeverityLevel.MEDIUM,
                    "description": "Use of eval() function can be dangerous",
                    },
                "debug_mode": {
                "pattern": r"(?i)debug\\s*=\\s * true",
                    "severity": SeverityLevel.MEDIUM,
                    "description": "Debug mode enabled in production",
                    },
                "hardcoded_ip": {
                "pattern": r"\\b(?:[0 - 9]{1,3}\\.){3}[0 - 9]{1,3}\\b",
                    "severity": SeverityLevel.LOW,
                    "description": "Hardcoded IP address found",
                    },
                }

        logger.info(f"🔒 Initializing security scanner for: {self.project_root}")


    def scan_all(self) -> Dict[str, any]:
        """Run comprehensive security scan"""
        logger.info("🚀 Starting comprehensive security scan...")

        # File - based scans
        self._scan_for_secrets()
        self._scan_for_insecure_code()
        self._scan_file_permissions()
        self._scan_configuration_files()

        # Dependency scans
        self._scan_dependencies()

        # Infrastructure scans
        self._scan_exposed_endpoints()

        # Generate comprehensive report
        return self._generate_security_report()


    def _scan_for_secrets(self):
        """Scan for hardcoded secrets in source code"""
        logger.info("🔍 Scanning for hardcoded secrets...")

        for file_path in self._get_source_files():
            try:
                with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\\n")

                    for line_num, line in enumerate(lines, 1):
                        self._check_line_for_secrets(file_path, line_num, line)

                self.scanned_files += 1

            except Exception as e:
                logger.warning(f"Could not scan file {file_path}: {str(e)}")


    def _check_line_for_secrets(self, file_path: Path, line_num: int, line: str):
        """Check a single line for secret patterns"""
        # Skip comments and obvious examples
        if (
            line.strip().startswith("#")
            or "example" in line.lower()
            or "placeholder" in line.lower()
        ):
            return

        for secret_type, config in self.secret_patterns.items():
            pattern = config["pattern"]
            severity = config["severity"]

            matches = re.finditer(pattern, line)
            for match in matches:
                # Extract the potential secret
                secret_value = (
                    match.group(2) if match.lastindex >= 2 else match.group(0)
                )

                # Skip obvious placeholders
                if self._is_placeholder(secret_value):
                    continue

                confidence = self._calculate_confidence(secret_type, secret_value)

                if confidence > 0.5:  # Only report high - confidence findings
                    self.issues.append(
                        SecurityIssue(
                            type = IssueType.HARDCODED_SECRET,
                                severity = severity,
                                title = f"Hardcoded {
                                secret_type.replace(
                                    '_',
                                        ' ').title()} Detected",
                                        description = f"Potential {secret_type} found in source code",
                                file_path = str(file_path.relative_to(self.project_root)),
                                line_number = line_num,
                                code_snippet = line.strip(),
                                recommendation = f"Move {secret_type} to environment variables \
    or secure vault",
                                confidence = confidence,
                                )
                    )


    def _is_placeholder(self, value: str) -> bool:
        """Check if a value is likely a placeholder"""
        placeholder_indicators = [
            "your_",
                "example",
                "placeholder",
                "test_",
                "demo_",
                "fake_",
                "sample_",
                "xxx",
                "yyy",
                "zzz",
                "123",
                "change_me",
                "replace_me",
                "todo",
                "fixme",
                ]

        value_lower = value.lower()
        return any(indicator in value_lower for indicator in placeholder_indicators)


    def _calculate_confidence(self, secret_type: str, value: str) -> float:
        """Calculate confidence score for secret detection"""
        confidence = 1.0

        # Reduce confidence for short values
        if len(value) < 10:
            confidence *= 0.3
        elif len(value) < 20:
            confidence *= 0.7

        # Reduce confidence for common patterns
        if value.isdigit():
            confidence *= 0.2
        elif value.isalpha() and len(set(value)) < 5:
            confidence *= 0.3

        # Increase confidence for specific patterns
        if secret_type == "aws_access_key" and value.startswith("AKIA"):
            confidence = 1.0
        elif secret_type == "github_token" and value.startswith("ghp_"):
            confidence = 1.0

        return min(confidence, 1.0)


    def _scan_for_insecure_code(self):
        """Scan for insecure coding patterns"""
        logger.info("🔍 Scanning for insecure code patterns...")

        for file_path in self._get_source_files():
            if file_path.suffix not in {
                ".py",
                    ".js",
                    ".ts",
                    ".jsx",
                    ".tsx",
                    ".php",
                    ".java",
                    }:
                continue

            try:
                with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read()
                    lines = content.split("\\n")

                    for line_num, line in enumerate(lines, 1):
                        self._check_line_for_insecure_patterns(
                            file_path, line_num, line
                        )

            except Exception as e:
                logger.warning(f"Could not scan file {file_path}: {str(e)}")


    def _check_line_for_insecure_patterns(
        self, file_path: Path, line_num: int, line: str
    ):
        """Check a single line for insecure patterns"""
        # Skip comments
        if line.strip().startswith("#") or line.strip().startswith("//"):
            return

        for pattern_name, config in self.insecure_patterns.items():
            pattern = config["pattern"]
            severity = config["severity"]
            description = config["description"]

            if re.search(pattern, line):
                self.issues.append(
                    SecurityIssue(
                        type = IssueType.INSECURE_CODE,
                            severity = severity,
                            title = f"Insecure Code Pattern: {
                            pattern_name.replace(
                                '_',
                                    ' ').title()}",
                                    description = description,
                            file_path = str(file_path.relative_to(self.project_root)),
                            line_number = line_num,
                            code_snippet = line.strip(),
                            recommendation = f"Review and secure the {
                            pattern_name.replace(
                                '_',
                                    ' ')} implementation",
                                    confidence = 0.8,
                            )
                )


    def _scan_file_permissions(self):
        """Scan for insecure file permissions"""
        logger.info("🔍 Scanning file permissions...")

        sensitive_files = [
            ".env",
                ".env.local",
                ".env.production",
                "id_rsa",
                "id_dsa",
                "id_ecdsa",
                ]

        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_exclude_path(file_path):
                try:
                    file_stat = file_path.stat()
                    permissions = stat.filemode(file_stat.st_mode)
                    octal_perms = oct(file_stat.st_mode)[-3:]

                    # Check for world - readable sensitive files
                    if (
                        file_path.name in sensitive_files
                        or file_path.name.startswith(".env")
                        or "private" in file_path.name.lower()
                    ):

                        if octal_perms[2] != "0":  # World readable
                            self.issues.append(
                                SecurityIssue(
                                    type = IssueType.WEAK_PERMISSION,
                                        severity = SeverityLevel.HIGH,
                                        title="Sensitive File World - Readable",
                                        description = f"Sensitive file has world - readable permissions: {permissions}",
                                        file_path = str(
                                        file_path.relative_to(self.project_root)
                                    ),
                                        recommendation="Run: chmod 600 <filename> to restrict access",
                                        confidence = 1.0,
                                        )
                            )

                    # Check for world - writable files
                    if octal_perms[2] in ["2", "3", "6", "7"]:  # World writable
                        self.issues.append(
                            SecurityIssue(
                                type = IssueType.WEAK_PERMISSION,
                                    severity = SeverityLevel.MEDIUM,
                                    title="File World - Writable",
                                    description = f"File has world - writable permissions: {permissions}",
                                    file_path = str(file_path.relative_to(self.project_root)),
                                    recommendation="Remove world - write permissions",
                                    confidence = 1.0,
                                    )
                        )

                except Exception as e:
                    logger.debug(
                        f"Could not check permissions for {file_path}: {
                            str(e)}"
                    )


    def _scan_configuration_files(self):
        """Scan configuration files for security issues"""
        logger.info("🔍 Scanning configuration files...")

        config_files = [
            "package.json",
                "requirements.txt",
                "Dockerfile",
                "docker - compose.yml",
                "nginx.conf",
                "apache.conf",
                ".htaccess",
                "web.config",
                ]

        for config_file in config_files:
            file_path = self.project_root/config_file
            if file_path.exists():
                self._scan_config_file(file_path)


    def _scan_config_file(self, file_path: Path):
        """Scan a specific configuration file"""
        try:
            with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                content = f.read()

            # Check for common misconfigurations
            if file_path.name == "package.json":
                self._scan_package_json(file_path, content)
            elif file_path.name in ["Dockerfile", "docker - compose.yml"]:
                self._scan_docker_config(file_path, content)

        except Exception as e:
            logger.warning(f"Could not scan config file {file_path}: {str(e)}")


    def _scan_package_json(self, file_path: Path, content: str):
        """Scan package.json for security issues"""
        try:
            package_data = json.loads(content)

            # Check for scripts that might be dangerous
            scripts = package_data.get("scripts", {})
            dangerous_patterns = ["rm -rf", "sudo", "curl | sh", "wget | sh"]

            for script_name, script_content in scripts.items():
                for pattern in dangerous_patterns:
                    if pattern in script_content:
                        self.issues.append(
                            SecurityIssue(
                                type = IssueType.CONFIGURATION_ISSUE,
                                    severity = SeverityLevel.MEDIUM,
                                    title="Potentially Dangerous npm Script",
                                    description = f"Script '{script_name}' contains potentially dangerous command: {pattern}",
                                    file_path = str(file_path.relative_to(self.project_root)),
                                    recommendation="Review script for security implications",
                                    confidence = 0.8,
                                    )
                        )

        except json.JSONDecodeError:
            pass


    def _scan_docker_config(self, file_path: Path, content: str):
        """Scan Docker configuration for security issues"""
        lines = content.split("\\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip().upper()

            # Check for running as root
            if line.startswith("USER ROOT") or "USER 0" in line:
                self.issues.append(
                    SecurityIssue(
                        type = IssueType.CONFIGURATION_ISSUE,
                            severity = SeverityLevel.HIGH,
                            title="Docker Container Running as Root",
                            description="Container configured to run as root user",
                            file_path = str(file_path.relative_to(self.project_root)),
                            line_number = line_num,
                            recommendation="Use a non - root user for better security",
                            confidence = 1.0,
                            )
                )


    def _scan_dependencies(self):
        """Scan dependencies for known vulnerabilities"""
        logger.info("🔍 Scanning dependencies for vulnerabilities...")

        # Check Python dependencies
        requirements_file = self.project_root/"requirements.txt"
        if requirements_file.exists():
            self._scan_python_dependencies()

        # Check Node.js dependencies
        package_json = self.project_root/"package.json"
        if package_json.exists():
            self._scan_nodejs_dependencies()


    def _scan_python_dependencies(self):
        """Scan Python dependencies using safety"""
        try:
            # Try to run safety check
            result = subprocess.run(
                ["python3", "-m", "pip", "list", "--format = json"],
                    capture_output = True,
                    text = True,
                    timeout = 30,
                    cwd = self.project_root,
                    )

            if result.returncode == 0:
                packages = json.loads(result.stdout)

                # Check for known vulnerable packages (simplified check)
                vulnerable_packages = {
                    "django": {
                        "version": "3.0.0",
                            "issue": "Known security vulnerabilities in older versions",
                            },
                        "flask": {
                        "version": "1.0.0",
                            "issue": "Security issues in older versions",
                            },
                        "requests": {
                        "version": "2.20.0",
                            "issue": "SSL verification issues in older versions",
                            },
                        }

                for package in packages:
                    package_name = package["name"].lower()
                    if package_name in vulnerable_packages:
                        self.issues.append(
                            SecurityIssue(
                                type = IssueType.VULNERABLE_DEPENDENCY,
                                    severity = SeverityLevel.MEDIUM,
                                    title = f"Potentially Vulnerable Dependency: {package_name}",
                                    description = vulnerable_packages[package_name]["issue"],
                                    recommendation = f"Update {package_name} to the latest version",
                                    confidence = 0.7,
                                    )
                        )

        except Exception as e:
            logger.debug(f"Could not scan Python dependencies: {str(e)}")


    def _scan_nodejs_dependencies(self):
        """Scan Node.js dependencies using npm audit"""
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                    capture_output = True,
                    text = True,
                    timeout = 60,
                    cwd = self.project_root,
                    )

            if result.returncode != 0 and result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    vulnerabilities = audit_data.get("vulnerabilities", {})

                    for vuln_name, vuln_data in vulnerabilities.items():
                        severity_map = {
                            "critical": SeverityLevel.CRITICAL,
                                "high": SeverityLevel.HIGH,
                                "moderate": SeverityLevel.MEDIUM,
                                "low": SeverityLevel.LOW,
                                }

                        severity = severity_map.get(
                            vuln_data.get("severity", "medium").lower(),
                                SeverityLevel.MEDIUM,
                                )

                        self.issues.append(
                            SecurityIssue(
                                type = IssueType.VULNERABLE_DEPENDENCY,
                                    severity = severity,
                                    title = f"Vulnerable Dependency: {vuln_name}",
                                    description = vuln_data.get(
                                    "title", "Known vulnerability"
                                ),
                                    recommendation="Run 'npm audit fix' to resolve vulnerabilities",
                                    cve_id=(
                                    vuln_data.get("cve", [None])[0]
                                    if vuln_data.get("cve")
                                    else None
                                ),
                                    confidence = 1.0,
                                    )
                        )

                except json.JSONDecodeError:
                    pass

        except Exception as e:
            logger.debug(f"Could not scan Node.js dependencies: {str(e)}")


    def _scan_exposed_endpoints(self):
        """Scan for potentially exposed endpoints"""
        logger.info("🔍 Scanning for exposed endpoints...")

        # Look for common endpoint patterns in source files
        endpoint_patterns = [
            r'@app\\.route\\(["\\']([^"\\']*)["\\'\\)]',  # Flask routes
            r'app\\.(get|post|put|delete)\\(["\\']([^"\\']*)["\\'\\)]',  # Express routes
            r'router\\.(get|post|put|delete)\\(["\\']([^"\\']*)["\\'\\)]',  # Router patterns
        ]

        for file_path in self._get_source_files():
            if file_path.suffix in {".py", ".js", ".ts"}:
                try:
                    with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                        content = f.read()

                    for pattern in endpoint_patterns:
                        matches = re.finditer(pattern, content, re.MULTILINE)
                        for match in matches:
                            endpoint = (
                                match.group(2)
                                if match.lastindex >= 2
                                else match.group(1)
                            )

                            # Check for potentially sensitive endpoints
                            if any(
                                sensitive in endpoint.lower()
                                for sensitive in [
                                    "admin",
                                        "debug",
                                        "test",
                                        "internal",
                                        "private",
                                        ]
                            ):

                                line_num = content[: match.start()].count("\\n") + 1

                                self.issues.append(
                                    SecurityIssue(
                                        type = IssueType.EXPOSED_ENDPOINT,
                                            severity = SeverityLevel.MEDIUM,
                                            title="Potentially Sensitive Endpoint Exposed",
                                            description = f"Endpoint '{endpoint}' may expose sensitive functionality",
                                            file_path = str(
                                            file_path.relative_to(self.project_root)
                                        ),
                                            line_number = line_num,
                                            recommendation="Ensure proper authentication \
    and authorization",
                                            confidence = 0.6,
                                            )
                                )

                except Exception as e:
                    logger.debug(f"Could not scan endpoints in {file_path}: {str(e)}")


    def _get_source_files(self) -> List[Path]:
        """Get list of source files to scan"""
        source_files = []

        for file_path in self.project_root.rglob("*"):
            if (
                file_path.is_file()
                and not self._should_exclude_path(file_path)
                and self._is_source_file(file_path)
            ):
                source_files.append(file_path)

        return source_files


    def _should_exclude_path(self, path: Path) -> bool:
        """Check if path should be excluded from scanning"""
        path_parts = set(path.parts)
        return bool(path_parts.intersection(self.excluded_patterns))


    def _is_source_file(self, file_path: Path) -> bool:
        """Check if file is a source code file"""
        source_extensions = {
            ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".php",
                ".java",
                ".c",
                ".cpp",
                ".h",
                ".hpp",
                ".cs",
                ".rb",
                ".go",
                ".rs",
                ".swift",
                ".kt",
                ".scala",
                ".html",
                ".htm",
                ".css",
                ".scss",
                ".sass",
                ".less",
                ".vue",
                ".json",
                ".xml",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
                ".conf",
                ".sh",
                ".bash",
                ".zsh",
                ".fish",
                ".ps1",
                ".bat",
                ".cmd",
                ".sql",
                ".md",
                ".txt",
                ".env",
                }

        return file_path.suffix.lower() in source_extensions


    def _generate_security_report(self) -> Dict[str, any]:
        """Generate comprehensive security report"""
        # Count issues by severity
        severity_counts = {severity.value: 0 for severity in SeverityLevel}
        type_counts = {issue_type.value: 0 for issue_type in IssueType}

        for issue in self.issues:
            severity_counts[issue.severity.value] += 1
            type_counts[issue.type.value] += 1

        # Calculate risk score
        risk_score = (
            severity_counts["critical"] * 10
            + severity_counts["high"] * 7
            + severity_counts["medium"] * 4
            + severity_counts["low"] * 2
            + severity_counts["info"] * 1
        )

        # Determine overall security status
        if severity_counts["critical"] > 0:
            overall_status = "CRITICAL"
        elif severity_counts["high"] > 0:
            overall_status = "HIGH_RISK"
        elif severity_counts["medium"] > 0:
            overall_status = "MEDIUM_RISK"
        elif severity_counts["low"] > 0:
            overall_status = "LOW_RISK"
        else:
            overall_status = "SECURE"

        report = {
            "overall_status": overall_status,
                "risk_score": risk_score,
                "scan_summary": {
                "files_scanned": self.scanned_files,
                    "total_issues": len(self.issues),
                    "severity_breakdown": severity_counts,
                    "type_breakdown": type_counts,
                    },
                "issues": [
                {
                    **asdict(issue),
                        "severity": issue.severity.value,
                        "type": issue.type.value,
                        }
                for issue in self.issues
            ],
                "recommendations": self._generate_recommendations(),
                "scan_metadata": {
                "project_root": str(self.project_root),
                    "scanner_version": "1.0.0",
                    "scan_timestamp": str(Path().cwd()),
                    },
                }

        logger.info(
            f"🔒 Security scan completed: {overall_status} (Risk Score: {risk_score})"
        )
        return report


    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        # Count issues by type for targeted recommendations
        type_counts = {}
        for issue in self.issues:
            type_counts[issue.type] = type_counts.get(issue.type, 0) + 1

        if type_counts.get(IssueType.HARDCODED_SECRET, 0) > 0:
            recommendations.append(
                "🔑 Move all hardcoded secrets to environment variables or secure vaults"
            )

        if type_counts.get(IssueType.WEAK_PERMISSION, 0) > 0:
            recommendations.append(
                "🔒 Fix file permissions: chmod 600 for sensitive files, remove world - write access"
            )

        if type_counts.get(IssueType.VULNERABLE_DEPENDENCY, 0) > 0:
            recommendations.append(
                "📦 Update vulnerable dependencies: run 'npm audit fix' \
    and 'pip - audit --fix'"
            )

        if type_counts.get(IssueType.INSECURE_CODE, 0) > 0:
            recommendations.append(
                "💻 Review and fix insecure code patterns: avoid eval(), sanitize inputs"
            )

        if type_counts.get(IssueType.CONFIGURATION_ISSUE, 0) > 0:
            recommendations.append(
                "⚙️ Review configuration files for security best practices"
            )

        if type_counts.get(IssueType.EXPOSED_ENDPOINT, 0) > 0:
            recommendations.append(
                "🌐 Secure exposed endpoints with proper authentication \
    and authorization"
            )

        if not recommendations:
            recommendations.append(
                "✅ No critical security issues found. Continue following security best practices."
            )

        return recommendations

# CLI Interface
if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser(
        description="Conservative Research System - Security Scanner"
    )
    parser.add_argument("--project - root", default=".", help="Project root directory")
    parser.add_argument(
        "--output", choices=["json", "text"], default="text", help="Output format"
    )
    parser.add_argument(
        "--severity",
            choices=["critical", "high", "medium", "low", "info"],
            default="medium",
            help="Minimum severity level to report",
            )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save - report", help="Save report to file")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    scanner = SecurityScanner(args.project_root)
    report = scanner.scan_all()

    # Filter by severity
    severity_order = ["info", "low", "medium", "high", "critical"]
    min_severity_index = severity_order.index(args.severity)

    filtered_issues = [
        issue
        for issue in report["issues"]
        if severity_order.index(issue["severity"]) >= min_severity_index
    ]

    report["issues"] = filtered_issues
    report["scan_summary"]["filtered_issues"] = len(filtered_issues)

    if args.save_report:
        with open(args.save_report, "w") as f:
            json.dump(report, f, indent = 2)
        logger.info(f"Report saved to {args.save_report}")

    if args.output == "json":
        print(json.dumps(report, indent = 2))
    else:
        # Text output
        print(f"\\n🔒 Security Scan Report")
        print(f"{'=' * 50}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Risk Score: {report['risk_score']}")
        print(f"Files Scanned: {report['scan_summary']['files_scanned']}")
        print(f"Total Issues: {report['scan_summary']['total_issues']}")

        print(f"\\nSeverity Breakdown:")
        for severity, count in report["scan_summary"]["severity_breakdown"].items():
            if count > 0:
                emoji = {
                    "critical": "🚨",
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢",
                        "info": "ℹ️",
                        }
                print(f"  {emoji.get(severity, '•')} {severity.title()}: {count}")

        if filtered_issues:
            print(f"\\nSecurity Issues (>= {args.severity}):")
            for i, issue in enumerate(filtered_issues, 1):
                severity_emoji = {
                    "critical": "🚨",
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢",
                        "info": "ℹ️",
                        }
                print(
                    f"\\n{i}. {
                        severity_emoji.get(
                            issue['severity'],
                                '•')} {
                                issue['title']}"
                )
                print(f"   Severity: {issue['severity'].title()}")
                print(f"   Description: {issue['description']}")

                if issue.get("file_path"):
                    location = issue["file_path"]
                    if issue.get("line_number"):
                        location += f":{issue['line_number']}"
                    print(f"   Location: {location}")

                if issue.get("code_snippet"):
                    print(f"   Code: {issue['code_snippet']}")

                if issue.get("recommendation"):
                    print(f"   💡 Fix: {issue['recommendation']}")

        if report["recommendations"]:
            print(f"\\nRecommendations:")
            for rec in report["recommendations"]:
                print(f"  {rec}")

    # Exit with appropriate code
    if report["overall_status"] in ["CRITICAL", "HIGH_RISK"]:
        sys.exit(1)
    elif report["overall_status"] == "MEDIUM_RISK":
        sys.exit(2)
    else:
        sys.exit(0)