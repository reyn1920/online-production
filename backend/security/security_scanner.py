#!/usr/bin/env python3
""""""



Security Scanner - Comprehensive security scanning and validation
Provides automated security checks, vulnerability scanning, and compliance validation

""""""


import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)

@dataclass


class SecurityFinding:
    
Represents a security finding
"""

    severity: str  # critical, high, medium, low, info
    category: str  # secrets, vulnerabilities, permissions, etc.
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    rule_id: str = ""
    remediation: str = ""
    confidence: str = "high"  # high, medium, low
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None

@dataclass


class ScanResult:
    """
Results of a security scan


    scan_id: str
    timestamp: str
    scan_type: str
    target_path: str
    findings: List[SecurityFinding]
    summary: Dict[str, int]
    duration_seconds: float
    status: str  # completed, failed, partial
   
""""""

    metadata: Dict[str, Any]
   

    
   
"""
class SecurityScanner:
    """Comprehensive security scanner for TRAE.AI projects"""


    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.scan_history: List[ScanResult] = []

        # Secret patterns (common secrets to detect)
        self.secret_patterns = {
            "api_key": {
                "pattern": r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?([a-zA-Z0-9_\-]{20,})["\']?',
                    "severity": "high",
                    "description": "Potential API key detected",
                     },
                "aws_access_key": {
                "pattern": r"AKIA[0-9A-Z]{16}",
                    "severity": "critical",
                    "description": "AWS Access Key ID detected",
                     },
                "aws_secret_key": {
                "pattern": r'(?i)aws[_-]?secret[_-]?access[_-]?key["\']?\s*[=:]\s*["\']?([a-zA-Z0-9/+=]{40})["\']?',"
                    "severity": "critical",
                    "description": "AWS Secret Access Key detected",
                     },
                "github_token": {
                "pattern": r"ghp_[a-zA-Z0-9]{36}",
                    "severity": "critical",
                    "description": "GitHub Personal Access Token detected",
                     },
                "private_key": {
                "pattern": r"-----BEGIN (RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----",
                    "severity": "critical",
                    "description": "Private key detected",
                     },
                "jwt_token": {
                "pattern": r"eyJ[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*\.[a-zA-Z0-9_\-]*",
                    "severity": "medium",
                    "description": "JWT token detected",
                     },
                "database_url": {
                "pattern": r'(?i)(database[_-]?url|db[_-]?url)\\s*[=:]\\s*["\\']?(postgresql|mysql|mongodb)://[^\\s"\\'>]+["\\']?',"
                    "severity": "high",
                    "description": "Database connection string detected",
                     },
                "password": {
                "pattern": r'(?i)(password|passwd|pwd)\\s*[=:]\\s*["\\']([^"\\'>\\s]{8,})["\\']',"
                    "severity": "medium",
                    "description": "Hardcoded password detected",
                     },
                 }

        # Vulnerability patterns
        self.vulnerability_patterns = {
            "sql_injection": {
                "pattern": r'(?i)(execute|query)\\s*\\(\\s*["\\'][^"\\'>]*\\+[^"\\'>]*["\\']',
                    "severity": "high",
                    "description": "Potential SQL injection vulnerability",
                    "cwe_id": "CWE - 89",
                     },
                "xss_vulnerability": {
                "pattern": r"(?i)innerHTML\\s*=\\s*[^;]*\\+",
                    "severity": "medium",
                    "description": "Potential XSS vulnerability",
                    "cwe_id": "CWE - 79",
                     },
                "path_traversal": {
                "pattern": r"(?i)(open|read|write)\\s*\\([^)]*\\.\\.[\\\\/]",
                    "severity": "high",
                    "description": "Potential path traversal vulnerability",
                    "cwe_id": "CWE - 22",
                     },
                "command_injection": {
                "pattern": r"(?i)(exec|system|popen|subprocess)\\s*\\([^)]*\\+[^)]*\\)",
                    "severity": "critical",
                    "description": "Potential command injection vulnerability",
                    "cwe_id": "CWE - 78",
                     },
                "insecure_random": {
                "pattern": r"(?i)math\\.random\\(\\)|random\\.random\\(\\)",
                    "severity": "low",
                    "description": "Insecure random number generation",
                    "cwe_id": "CWE - 338",
                     },
                 }

        # File extensions to scan
        self.scannable_extensions = {
            ".py",
                ".js",
                ".ts",
                ".jsx",
                ".tsx",
                ".java",
                ".php",
                ".rb",
                ".go",
                ".cs",
                ".cpp",
                ".c",
                ".h",
                ".hpp",
                ".sh",
                ".bash",
                ".zsh",
                ".ps1",
                ".sql",
                ".json",
                ".yaml",
                ".yml",
                ".xml",
                ".env",
                ".config",
                ".ini",
                 }

        # Files to exclude from scanning
        self.excluded_patterns = {
            r"node_modules/",
                r"\\.git/",
                r"__pycache__/",
                r"\\.pytest_cache/",
                r"venv/",
                r"env/",
                r"\\.venv/",
                r"dist/",
                r"build/",
                r"\\.next/",
                r"coverage/",
                r"\\.nyc_output/",
                r"logs/",
                r"\\.log$",
                r"\\.min\\.(js|css)$",
                r"\\.(jpg|jpeg|png|gif|bmp|ico|svg|pdf|zip|tar|gz|rar)$",
                 }

        logger.info(f"Security scanner initialized for {self.base_dir}")


    def scan_secrets(self, target_path: Optional[str] = None) -> ScanResult:
        """Scan for hardcoded secrets and credentials"""
        start_time = datetime.now()
        scan_id = f"secrets_{int(start_time.timestamp())}"

        target = Path(target_path) if target_path else self.base_dir
        findings = []

        logger.info(f"Starting secrets scan on {target}")

        try:
            for file_path in self._get_scannable_files(target):
                try:
                    with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                        content = f.read()

                    # Check each secret pattern
                    for rule_id, rule_config in self.secret_patterns.items():
                        matches = re.finditer(
                            rule_config["pattern"], content, re.MULTILINE
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                         )

                        for match in matches:
                            line_number = content[: match.start()].count("\\n") + 1

                            # Extract the matched secret (be careful not to log it)
                            matched_text = match.group(0)

                            # Additional validation for false positives
                            if self._is_likely_false_positive(matched_text, rule_id):
                                continue

                            finding = SecurityFinding(
                                severity = rule_config["severity"],
                                    category="secrets",
                                    title = f"Hardcoded Secret: {rule_id}",
                                    description = rule_config["description"],
                                    file_path = str(file_path.relative_to(self.base_dir)),
                                    line_number = line_number,
                                    rule_id = rule_id,
                                    remediation = self._get_secret_remediation(rule_id),
                                    confidence="high",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                                     )

                            findings.append(finding)

                except Exception as e:
                    logger.warning(f"Failed to scan file {file_path}: {e}")
                    continue

            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="secrets",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="completed",
                    metadata={
                    "files_scanned": len(list(self._get_scannable_files(target))),
                        "patterns_checked": len(self.secret_patterns),
                         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.info(
                f"Secrets scan completed: {len(findings)} findings in {duration:.2f}s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
             )

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="secrets",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="failed",
                    metadata={"error": str(e)},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.error(f"Secrets scan failed: {e}")

            return result


    def scan_vulnerabilities(self, target_path: Optional[str] = None) -> ScanResult:
        """Scan for common vulnerability patterns"""
        start_time = datetime.now()
        scan_id = f"vulnerabilities_{int(start_time.timestamp())}"

        target = Path(target_path) if target_path else self.base_dir
        findings = []

        logger.info(f"Starting vulnerability scan on {target}")

        try:
            for file_path in self._get_scannable_files(target):
                try:
                    with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                        content = f.read()

                    # Check each vulnerability pattern
                    for rule_id, rule_config in self.vulnerability_patterns.items():
                        matches = re.finditer(
                            rule_config["pattern"], content, re.MULTILINE
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                         )

                        for match in matches:
                            line_number = content[: match.start()].count("\\n") + 1

                            finding = SecurityFinding(
                                severity = rule_config["severity"],
                                    category="vulnerabilities",
                                    title = f"Vulnerability: {rule_id}",
                                    description = rule_config["description"],
                                    file_path = str(file_path.relative_to(self.base_dir)),
                                    line_number = line_number,
                                    rule_id = rule_id,
                                    remediation = self._get_vulnerability_remediation(
                                    rule_id
                                 ),
                                    confidence="medium",
                                    cwe_id = rule_config.get("cwe_id"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                                     )

                            findings.append(finding)

                except Exception as e:
                    logger.warning(f"Failed to scan file {file_path}: {e}")
                    continue

            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="vulnerabilities",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="completed",
                    metadata={
                    "files_scanned": len(list(self._get_scannable_files(target))),
                        "patterns_checked": len(self.vulnerability_patterns),
                         },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.info(
                f"Vulnerability scan completed: {len(findings)} findings in {duration:.2f}s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
             )

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="vulnerabilities",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="failed",
                    metadata={"error": str(e)},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.error(f"Vulnerability scan failed: {e}")

            return result


    def scan_permissions(self, target_path: Optional[str] = None) -> ScanResult:
        """Scan for insecure file permissions"""
        start_time = datetime.now()
        scan_id = f"permissions_{int(start_time.timestamp())}"

        target = Path(target_path) if target_path else self.base_dir
        findings = []

        logger.info(f"Starting permissions scan on {target}")

        try:
            for file_path in target.rglob("*"):
                if not file_path.is_file():
                    continue

                if self._should_exclude_file(file_path):
                    continue

                try:
                    stat_info = file_path.stat()
                    mode = stat_info.st_mode

                    # Check for world - writable files
                    if mode & 0o002:  # World writable
                        finding = SecurityFinding(
                            severity="medium",
                                category="permissions",
                                title="World - writable file",
                                description = f"File is writable by all users: {oct(mode)}",
                                file_path = str(file_path.relative_to(self.base_dir)),
                                rule_id="world_writable",
                                remediation="Remove world - write permissions: chmod o - w <file>",
                                confidence="high",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                                 )
                        findings.append(finding)

                    # Check for executable files that shouldn't be
                    if (mode & 0o111) and file_path.suffix in {
                        ".txt",
                            ".md",
                            ".json",
                            ".yaml",
                            ".yml",
#                             }:
                        finding = SecurityFinding(
                            severity="low",
                                category="permissions",
                                title="Unnecessary executable permission",
                                description = f"Non - executable file has execute permissions: {oct(mode)}",
                                file_path = str(file_path.relative_to(self.base_dir)),
                                rule_id="unnecessary_executable",
                                remediation="Remove execute permissions: chmod -x <file>",
                                confidence="medium",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                                 )
                        findings.append(finding)

                    # Check for overly permissive script files
                    if file_path.suffix in {".sh", ".py", ".pl", ".rb"} and (
                        mode & 0o022
#                     ):  # Group/other writable
                        finding = SecurityFinding(
                            severity="medium",
                                category="permissions",
                                title="Script file with excessive permissions",
                                description = f"Script file is writable by group/others: {oct(mode)}",
                                file_path = str(file_path.relative_to(self.base_dir)),
                                rule_id="script_excessive_perms",
                                remediation="Restrict permissions: chmod 755 <file>",
                                confidence="high",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                                 )
                        findings.append(finding)

                except Exception as e:
                    logger.warning(f"Failed to check permissions for {file_path}: {e}")
                    continue

            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="permissions",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="completed",
                    metadata={
                    "files_scanned": len([f for f in target.rglob("*") if f.is_file()])
                 },
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.info(
                f"Permissions scan completed: {len(findings)} findings in {duration:.2f}s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
             )

            return result

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            result = ScanResult(
                scan_id = scan_id,
                    timestamp = start_time.isoformat(),
                    scan_type="permissions",
                    target_path = str(target),
                    findings = findings,
                    summary = self._generate_summary(findings),
                    duration_seconds = duration,
                    status="failed",
                    metadata={"error": str(e)},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
                     )

            self.scan_history.append(result)
            logger.error(f"Permissions scan failed: {e}")

            return result


    def comprehensive_scan(
        self, target_path: Optional[str] = None
    ) -> Dict[str, ScanResult]:
        """Run all security scans"""
        logger.info("Starting comprehensive security scan")

        results = {
            "secrets": self.scan_secrets(target_path),
                "vulnerabilities": self.scan_vulnerabilities(target_path),
                "permissions": self.scan_permissions(target_path),
                 }

        # Generate overall summary
        total_findings = sum(len(result.findings) for result in results.values())
        critical_findings = sum(
            len([f for f in result.findings if f.severity == "critical"])
            for result in results.values()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
         )

        logger.info(
            f"Comprehensive scan completed: {total_findings} total findings, {critical_findings} critical"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
         )

        return results


    def _get_scannable_files(self, target_path: Path) -> List[Path]:
        """
Get list of files that should be scanned

       
""""""

        scannable_files = []
       

        
       
"""
        for file_path in target_path.rglob("*"):
       """

        
       

        scannable_files = []
       
""""""
            if not file_path.is_file():
                continue

            if self._should_exclude_file(file_path):
                continue

            # Check if file extension is scannable
            if file_path.suffix.lower() in self.scannable_extensions:
                scannable_files.append(file_path)
            elif file_path.name.startswith(".env"):
                scannable_files.append(file_path)
            elif not file_path.suffix and self._is_text_file(file_path):
                scannable_files.append(file_path)

        return scannable_files


    def _should_exclude_file(self, file_path: Path) -> bool:
        """
Check if file should be excluded from scanning

       
""""""

        file_str = str(file_path)
       

        
       
"""
        for pattern in self.excluded_patterns:
       """

        
       

        file_str = str(file_path)
       
""""""

            if re.search(pattern, file_str):
                return True

        return False


    def _is_text_file(self, file_path: Path) -> bool:
        
Check if file is likely a text file
"""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)

            # Check for null bytes (binary indicator)
            if b"\\x00" in chunk:
                return False

            # Try to decode as UTF - 8
            try:
                chunk.decode("utf - 8")
                return True
            except UnicodeDecodeError:
                return False

        except Exception:
            return False


    def _is_likely_false_positive(self, matched_text: str, rule_id: str) -> bool:
        """
Check if a match is likely a false positive

       
""""""

        # Common false positive patterns
       

        
       
"""
        false_positive_indicators = {
            "example",
                "test",
                "dummy",
                "placeholder",
                "sample",
                "your_key_here",
                "insert_key",
                "replace_with",
                "xxxxxxxx",
                "12345678",
                "abcdefgh",
                 }
       """

        
       

        # Common false positive patterns
       
""""""
        matched_lower = matched_text.lower()

        for indicator in false_positive_indicators:
            if indicator in matched_lower:
                return True

        # Rule - specific false positive checks
        if rule_id == "jwt_token":
            # Very short JWT tokens are likely false positives
            if len(matched_text) < 50:
                return True

        if rule_id == "api_key":
            # Very short or common patterns
            if len(matched_text) < 10 or matched_text.lower() in {"api_key", "apikey"}:
                return True

        return False


    def _get_secret_remediation(self, rule_id: str) -> str:
        """Get remediation advice for secret findings"""
        remediations = {
            "api_key": "Move API key to environment variable or secure secret store",
                "aws_access_key": "Rotate AWS credentials immediately \"
#     and use IAM roles or environment variables",
                "aws_secret_key": "Rotate AWS credentials immediately \"
#     and use IAM roles or environment variables",
                "github_token": "Revoke GitHub token \"
#     and use GitHub Actions secrets or environment variables",
                "private_key": "Remove private key from code \"
#     and use secure key management",
                "jwt_token": "Remove JWT token from code \"
#     and generate tokens dynamically",
                "database_url": "Move database URL to environment variable \"
#     or configuration file",
                "password": "Remove hardcoded password \"
#     and use secure authentication methods",
                 }

        return remediations.get(
            rule_id, "Remove sensitive data from code and use secure storage"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
         )


    def _get_vulnerability_remediation(self, rule_id: str) -> str:
        """Get remediation advice for vulnerability findings"""
        remediations = {
            "sql_injection": "Use parameterized queries or prepared statements",
                "xss_vulnerability": "Sanitize user input \"
#     and use safe DOM manipulation methods",
                "path_traversal": "Validate and sanitize file paths, use allowlists",
                "command_injection": "Avoid dynamic command construction, use safe APIs",
                "insecure_random": "Use cryptographically secure random number generators",
                 }

        return remediations.get(rule_id, "Review code for security best practices")


    def _generate_summary(self, findings: List[SecurityFinding]) -> Dict[str, int]:
        """Generate summary statistics for findings"""
        summary = {
            "total": len(findings),
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                 }

        for finding in findings:
            if finding.severity in summary:
                summary[finding.severity] += 1

        return summary


    def export_results(self, results: Dict[str, ScanResult], output_path: str) -> bool:
        """
Export scan results to file

        
"""
        try:
        """
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                    "scan_results": {},
                     }
        """

        try:
        

       
""""""
            for scan_type, result in results.items():
                export_data["scan_results"][scan_type] = {
                    "scan_id": result.scan_id,
                        "timestamp": result.timestamp,
                        "scan_type": result.scan_type,
                        "target_path": result.target_path,
                        "findings": [asdict(finding) for finding in result.findings],
                        "summary": result.summary,
                        "duration_seconds": result.duration_seconds,
                        "status": result.status,
                        "metadata": result.metadata,
                         }

            output_file = Path(output_path)
            with open(output_file, "w", encoding="utf - 8") as f:
                json.dump(export_data, f, indent = 2, ensure_ascii = False)

            logger.info(f"Results exported to {output_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to export results: {e}")
            return False


    def get_scan_history(self) -> List[ScanResult]:
        """
Get scan history

        
"""
        return self.scan_history.copy()
        """"""
        """


        return self.scan_history.copy()

        

       
""""""

    def clear_scan_history(self) -> None:
        """
        Clear scan history
        """
        self.scan_history.clear()
        logger.info("Scan history cleared")


def main():
    """Command - line interface for security scanner"""

    import argparse

    parser = argparse.ArgumentParser(
        description="Security Scanner - Comprehensive security analysis"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
     )
    parser.add_argument(
        "--base - dir", default=".", help="Base directory to scan (default: current)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
     )
    parser.add_argument(
        "--scan - type",
            choices=["secrets", "vulnerabilities", "permissions", "all"],
            default="all",
            help="Type of scan to perform",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
             )
    parser.add_argument("--target", help="Specific target path to scan")
    parser.add_argument("--output", help="Output file for results (JSON format)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    scanner = SecurityScanner(args.base_dir)

    if args.scan_type == "all":
        results = scanner.comprehensive_scan(args.target)
    elif args.scan_type == "secrets":
        results = {"secrets": scanner.scan_secrets(args.target)}
    elif args.scan_type == "vulnerabilities":
        results = {"vulnerabilities": scanner.scan_vulnerabilities(args.target)}
    elif args.scan_type == "permissions":
        results = {"permissions": scanner.scan_permissions(args.target)}

    # Print summary
    print("\\n=== Security Scan Results ===")
    for scan_type, result in results.items():
        print(f"\\n{scan_type.upper()} Scan:")
        print(f"  Status: {result.status}")
        print(f"  Duration: {result.duration_seconds:.2f}s")
        print(f"  Findings: {result.summary['total']}")

        if result.summary["total"] > 0:
            print(f"    Critical: {result.summary['critical']}")
            print(f"    High: {result.summary['high']}")
            print(f"    Medium: {result.summary['medium']}")
            print(f"    Low: {result.summary['low']}")

            # Show first few findings
            for i, finding in enumerate(result.findings[:3]):
                print(f"\\n  Finding {i + 1}:")
                print(f"    Severity: {finding.severity}")
                print(f"    Title: {finding.title}")
                print(f"    File: {finding.file_path}:{finding.line_number or 'N/A'}")
                print(f"    Description: {finding.description}")

            if len(result.findings) > 3:
                print(f"\\n  ... and {len(result.findings) - 3} more findings")

    # Export results if requested
    if args.output:
        if scanner.export_results(results, args.output):
            print(f"\\nResults exported to {args.output}")
        else:
            print(f"\\nFailed to export results to {args.output}")

    # Exit with appropriate code
    total_critical = sum(result.summary["critical"] for result in results.values())
    total_high = sum(result.summary["high"] for result in results.values())

    if total_critical > 0:
        exit(2)  # Critical findings
    elif total_high > 0:
        exit(1)  # High severity findings
    else:
        exit(0)  # No critical/high findings

if __name__ == "__main__":
    main()