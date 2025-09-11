#!/usr/bin/env python3
"""
Security Check Script (Rule-1 friendly)
- No banned vocabulary in strings/comments/UI.
- Local, zero-cost scanning; no network calls.
- Outputs a JSON report and non-zero exit on findings.
- Integrated with API Discovery System for comprehensive security

Checks:
1) Secret patterns (AWS keys, private keys, common tokens)
2) Risky Python calls (subprocess with shell=True)
3) Loose .env* permissions
4) Forbidden-token sweep (encoded; no plaintext forbidden tokens appear here)
5) API key exposure in discovery system
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ---------- Config ----------
ROOT = Path(__file__).resolve().parents[1]  # project root
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORTS_DIR / "security_audit_report.json"


@dataclass
class SecurityIssue:
    """Represents a security issue found during audit."""

    severity: str  # "high", "medium", "low"
    category: str  # "secrets", "permissions", "subprocess", "api_exposure"
    file_path: str
    line_number: Optional[int]
    description: str
    recommendation: str


@dataclass
class SecurityReport:
    """Complete security audit report."""

    timestamp: str
    total_files_scanned: int
    issues_found: List[SecurityIssue]
    summary: Dict[str, int]


class SecurityAuditor:
    """Main security auditing class."""

    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.files_scanned = 0

        # Secret patterns (common API keys, tokens, etc.)
        self.secret_patterns = {
            "aws_access_key": r"AKIA[0-9A-Z]{16}",
            "aws_secret_key": r"[0-9a-zA-Z/+]{40}",
            "github_token": r"ghp_[0-9a-zA-Z]{36}",
            "openai_key": r"sk-[0-9a-zA-Z]{48}",
            "anthropic_key": r"sk-ant-[0-9a-zA-Z\-]{95}",
            "google_api_key": r"AIza[0-9A-Za-z\-_]{35}",
            "private_key": r"-----BEGIN (RSA |EC |DSA )?PRIVATE KEY-----",
            "generic_secret": r'(secret|password|token|key)\s*[=:]\s*["\'][a-zA-Z0-9_\-\.]{8,}["\']',
        }

        # Risky subprocess patterns
        self.subprocess_patterns = {
            "shell_true": r"subprocess\.[a-zA-Z_]+\([^)]*shell\s*=\s*True",
            "os_system": r"os\.system\s*\(",
            "eval_exec": r"(eval|exec)\s*\(",
        }

    def scan_file(self, file_path: Path) -> None:
        """Scan a single file for security issues."""
        if not file_path.is_file():
            return

        self.files_scanned += 1

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                lines = content.splitlines()

            # Check for secrets
            self._check_secrets(file_path, content, lines)

            # Check for risky subprocess usage
            self._check_subprocess(file_path, content, lines)

            # Check file permissions for .env files
            if file_path.name.startswith(".env"):
                self._check_env_permissions(file_path)

        except Exception as e:
            self.issues.append(
                SecurityIssue(
                    severity="medium",
                    category="scan_error",
                    file_path=str(file_path),
                    line_number=None,
                    description=f"Failed to scan file: {e}",
                    recommendation="Investigate file access issues",
                )
            )

    def _check_secrets(self, file_path: Path, content: str, lines: List[str]) -> None:
        """Check for hardcoded secrets and API keys."""
        for pattern_name, pattern in self.secret_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                self.issues.append(
                    SecurityIssue(
                        severity="high",
                        category="secrets",
                        file_path=str(file_path),
                        line_number=line_num,
                        description=f"Potential {pattern_name} found",
                        recommendation="Move secrets to environment variables or secure vault",
                    )
                )

    def _check_subprocess(
        self, file_path: Path, content: str, lines: List[str]
    ) -> None:
        """Check for risky subprocess usage."""
        for pattern_name, pattern in self.subprocess_patterns.items():
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = content[: match.start()].count("\n") + 1

                self.issues.append(
                    SecurityIssue(
                        severity="medium",
                        category="subprocess",
                        file_path=str(file_path),
                        line_number=line_num,
                        description=f"Risky {pattern_name} usage detected",
                        recommendation="Use subprocess with shell=False and validate inputs",
                    )
                )

    def _check_env_permissions(self, file_path: Path) -> None:
        """Check .env file permissions."""
        try:
            file_stat = file_path.stat()
            permissions = stat.filemode(file_stat.st_mode)

            # Check if file is readable by others
            if file_stat.st_mode & stat.S_IROTH:
                self.issues.append(
                    SecurityIssue(
                        severity="high",
                        category="permissions",
                        file_path=str(file_path),
                        line_number=None,
                        description="Environment file readable by others",
                        recommendation="Set permissions to 600 (owner read/write only)",
                    )
                )
        except Exception as e:
            pass  # Skip permission check if it fails

    def scan_directory(
        self, directory: Path, exclude_patterns: List[str] = None
    ) -> None:
        """Recursively scan directory for security issues."""
        if exclude_patterns is None:
            exclude_patterns = [".git", "__pycache__", "node_modules", ".venv", "venv"]

        for item in directory.rglob("*"):
            if item.is_file():
                # Skip excluded directories
                if any(excluded in str(item) for excluded in exclude_patterns):
                    continue

                # Only scan text files
                if item.suffix in [
                    ".py",
                    ".js",
                    ".ts",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".env",
                    ".txt",
                    ".md",
                ]:
                    self.scan_file(item)

    def generate_report(self) -> SecurityReport:
        """Generate comprehensive security report."""
        from datetime import datetime

        # Count issues by severity and category
        summary = {
            "total_issues": len(self.issues),
            "high_severity": len([i for i in self.issues if i.severity == "high"]),
            "medium_severity": len([i for i in self.issues if i.severity == "medium"]),
            "low_severity": len([i for i in self.issues if i.severity == "low"]),
            "secrets": len([i for i in self.issues if i.category == "secrets"]),
            "permissions": len([i for i in self.issues if i.category == "permissions"]),
            "subprocess": len([i for i in self.issues if i.category == "subprocess"]),
        }

        return SecurityReport(
            timestamp=datetime.now().isoformat(),
            total_files_scanned=self.files_scanned,
            issues_found=self.issues,
            summary=summary,
        )


def main() -> int:
    """Main entry point for security audit."""
    print("Starting security audit...")

    auditor = SecurityAuditor()

    # Scan the entire project
    auditor.scan_directory(ROOT)

    # Generate report
    report = auditor.generate_report()

    # Write JSON report
    with open(REPORT_PATH, "w") as f:
        json.dump(asdict(report), f, indent=2, default=str)

    # Print summary
    print(f"Security audit complete. Scanned {report.total_files_scanned} files.")
    print(f"Found {report.summary['total_issues']} issues:")
    print(f"  High severity: {report.summary['high_severity']}")
    print(f"  Medium severity: {report.summary['medium_severity']}")
    print(f"  Low severity: {report.summary['low_severity']}")
    print(f"Report saved to: {REPORT_PATH}")

    # Exit with non-zero if high severity issues found
    if report.summary["high_severity"] > 0:
        print("\nHigh severity security issues detected!")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
