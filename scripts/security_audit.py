#!/usr/bin/env python3
""""""
Base44 Pack Security Audit Script
Comprehensive security scanning for forbidden tokens, secrets, and risky code patterns.
""""""

import re
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Forbidden tokens that should never appear in code
FORBIDDEN_TOKENS = [
    # API Keys and Secrets
    r'sk-[a-zA-Z0-9]{48}',  # OpenAI API keys
    r'AIza[0-9A-Za-z\-_]{35}',  # Google API keys
    r'AKIA[0-9A-Z]{16}',  # AWS Access Key IDs
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',  # UUIDs that might be secrets
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub Personal Access Tokens
    r'gho_[a-zA-Z0-9]{36}',  # GitHub OAuth tokens
    r'ghu_[a-zA-Z0-9]{36}',  # GitHub User tokens
    r'ghs_[a-zA-Z0-9]{36}',  # GitHub Server tokens
    r'ghr_[a-zA-Z0-9]{36}',  # GitHub Refresh tokens

    # Database URLs and connection strings
    r'postgresql://[^\s]+',
    r'mysql://[^\s]+',
    r'mongodb://[^\s]+',
    r'redis://[^\s]+',

    # JWT tokens
    r'eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',

    # Private keys
    r'-----BEGIN PRIVATE KEY-----',
    r'-----BEGIN RSA PRIVATE KEY-----',
    r'-----BEGIN OPENSSH PRIVATE KEY-----',
# BRACKET_SURGEON: disabled
# ]

# Risky code patterns
RISKY_PATTERNS = [
    r'eval\s*\(',  # eval() calls
    r'exec\s*\(',  # exec() calls
    r'__import__\s*\(',  # dynamic imports
    r'subprocess\.call\s*\(',  # subprocess calls
    r'os\.system\s*\(',  # os.system calls
    r'shell=True',  # shell=True in subprocess
    r'pickle\.loads?\s*\(',  # pickle deserialization
    r'yaml\.load\s*\(',  # unsafe YAML loading
    r'input\s*\(',  # input() calls (potential injection)
    r'raw_input\s*\(',  # raw_input() calls
# BRACKET_SURGEON: disabled
# ]

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    r'\.git/',
    r'\.venv/',
    r'venv/',
    r'node_modules/',
    r'__pycache__/',
    r'\.pyc$',
    r'\.pyo$',
    r'\.egg-info/',
    r'\.tox/',
    r'\.coverage',
    r'\.pytest_cache/',
    r'dist/',
    r'build/',
    r'\.DS_Store',
    r'\.log$',
    r'\.sqlite$',
    r'\.db$',
    r'\.pid$',
    r'security_audit\.py$',  # Don't scan ourselves
# BRACKET_SURGEON: disabled
# ]

class SecurityAudit:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path).resolve()
        self.findings: List[Dict[str, Any]] = []
        self.scanned_files = 0
        self.excluded_files = 0

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from scanning."""
        relative_path = str(file_path.relative_to(self.root_path))

        for pattern in EXCLUDE_PATTERNS:
            if re.search(pattern, relative_path):
                return True

        return False

    def scan_file_for_secrets(self, file_path: Path) -> List[Dict[str, Any]]:
        """Scan a single file for forbidden tokens and secrets."""
        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')

            # Check for forbidden tokens
            for i, line in enumerate(lines, 1):
                for pattern in FORBIDDEN_TOKENS:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        findings.append({
                            'type': 'forbidden_token',
                            'file': str(file_path.relative_to(self.root_path)),
                            'line': i,
                            'column': match.start() + 1,
                            'pattern': pattern,
                            'match': match.group(),
                            'severity': 'critical',
                            'description': f'Potential secret or API key detected: {match.group()[:20]}...'
# BRACKET_SURGEON: disabled
#                         })

            # Check for risky code patterns
            for i, line in enumerate(lines, 1):
                for pattern in RISKY_PATTERNS:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        findings.append({
                            'type': 'risky_code',
                            'file': str(file_path.relative_to(self.root_path)),
                            'line': i,
                            'column': match.start() + 1,
                            'pattern': pattern,
                            'match': match.group(),
                            'severity': 'high',
                            'description': f'Risky code pattern detected: {match.group()}'
# BRACKET_SURGEON: disabled
#                         })

        except Exception as e:
            findings.append({
                'type': 'scan_error',
                'file': str(file_path.relative_to(self.root_path)),
                'error': str(e),
                'severity': 'medium',
                'description': f'Error scanning file: {e}'
# BRACKET_SURGEON: disabled
#             })

        return findings

    def scan_directory(self) -> Dict[str, Any]:
        """Scan entire directory tree for security issues."""
        print(f"Starting security audit of {self.root_path}")

        for file_path in self.root_path.rglob('*'):
            if file_path.is_file():
                if self.should_exclude_file(file_path):
                    self.excluded_files += 1
                    continue

                self.scanned_files += 1
                file_findings = self.scan_file_for_secrets(file_path)
                self.findings.extend(file_findings)

                if self.scanned_files % 100 == 0:
                    print(f"Scanned {self.scanned_files} files...")

        # Generate summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'root_path': str(self.root_path),
            'scanned_files': self.scanned_files,
            'excluded_files': self.excluded_files,
            'total_findings': len(self.findings),
            'critical_findings': len([f for f in self.findings if f.get('severity') == 'critical']),
            'high_findings': len([f for f in self.findings if f.get('severity') == 'high']),
            'medium_findings': len([f for f in self.findings if f.get('severity') == 'medium']),
            'findings': self.findings
# BRACKET_SURGEON: disabled
#         }

        return summary

    def generate_report(self, output_file: str = None) -> str:
        """Generate a comprehensive security audit report."""
        audit_results = self.scan_directory()

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(audit_results, f, indent=2)
            print(f"Security audit report saved to {output_file}")

        # Print summary to console
        print("\n" + "="*60)
        print("SECURITY AUDIT SUMMARY")
        print("="*60)
        print(f"Scanned files: {audit_results['scanned_files']}")
        print(f"Excluded files: {audit_results['excluded_files']}")
        print(f"Total findings: {audit_results['total_findings']}")
        print(f"Critical findings: {audit_results['critical_findings']}")
        print(f"High risk findings: {audit_results['high_findings']}")
        print(f"Medium risk findings: {audit_results['medium_findings']}")

        if audit_results['critical_findings'] > 0:
            print("\n⚠️  CRITICAL ISSUES FOUND:")
            for finding in audit_results['findings']:
                if finding.get('severity') == 'critical':
                    print(f"  {finding['file']}:{finding['line']} - {finding['description']}")

        if audit_results['high_findings'] > 0:
            print("\n🔍 HIGH RISK ISSUES:")
            for finding in audit_results['findings']:
                if finding.get('severity') == 'high':
                    print(f"  {finding['file']}:{finding['line']} - {finding['description']}")

        # Return status
        if audit_results['critical_findings'] > 0:
            return "CRITICAL_ISSUES_FOUND"
        elif audit_results['high_findings'] > 0:
            return "HIGH_RISK_ISSUES_FOUND"
        elif audit_results['medium_findings'] > 0:
            return "MEDIUM_RISK_ISSUES_FOUND"
        else:
            return "CLEAN"

def main():
    """Main entry point for security audit."""
    import argparse

    parser = argparse.ArgumentParser(description='Base44 Pack Security Audit')
    parser.add_argument('--path', '-p', default='.', help='Path to scan (default: current directory)')
    parser.add_argument('--output', '-o', help='Output file for detailed report')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')

    args = parser.parse_args()

    auditor = SecurityAudit(args.path)
    status = auditor.generate_report(args.output)

    if not args.quiet:
        print(f"\nAudit Status: {status}")

    # Exit with appropriate code
    if status == "CRITICAL_ISSUES_FOUND":
        sys.exit(2)
    elif status == "HIGH_RISK_ISSUES_FOUND":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()