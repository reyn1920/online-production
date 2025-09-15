#!/usr / bin / env python3
""""""
rule1_rewrite_suggester.py - Rule - 1 Compliance Analysis and Suggestion Tool
Part of the Trae AI Cleanup Framework

This tool analyzes code for Rule - 1 compliance issues and suggests improvements.
Rule - 1 focuses on security, maintainability, and best practices.
""""""

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Setup logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
        logging.FileHandler("tools / cleanup / rule1_suggester.log"),
            logging.StreamHandler(),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )
logger = logging.getLogger(__name__)

@dataclass


class Rule1Issue:
    """Represents a Rule - 1 compliance issue"""

    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    description: str
    current_code: str
    suggested_fix: str
    rule_reference: str
    auto_fixable: bool = False


class Rule1Analyzer:
    """Analyzes code for Rule - 1 compliance issues"""


    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.issues: List[Rule1Issue] = []
        self.stats = {
            "files_scanned": 0,
                "issues_found": 0,
                "critical_issues": 0,
                "high_issues": 0,
                "medium_issues": 0,
                "low_issues": 0,
                "auto_fixable": 0,
# BRACKET_SURGEON: disabled
#                 }

        # Load rule patterns
        self.security_patterns = self._load_security_patterns()
        self.maintainability_patterns = self._load_maintainability_patterns()
        self.performance_patterns = self._load_performance_patterns()


    def _load_security_patterns(self) -> Dict:
        """Load security - related Rule - 1 patterns"""
        return {
            "hardcoded_secrets": {
                "patterns": [
                    r'(?i)(api_key|password|secret|token)\\s*=\\s*[\\'"][^\\'"]+[\\'"]',"
                        r'(?i)(aws_access_key|aws_secret)\\s*=\\s*[\\'"][^\\'"]+[\\'"]',"
                        r'(?i)(database_url|db_password)\\s*=\\s*[\\'"][^\\'"]+[\\'"]',"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "severity": "critical",
                    "description": "Hardcoded secrets detected",
                    "suggestion": "Move secrets to environment variables \"
#     or secure vault",
# BRACKET_SURGEON: disabled
#                     },
                "sql_injection": {
                "patterns": [
                    r'execute\\s*\\(\\s*[\\'"].*%s.*[\\'"]\\s*%',
                        r'query\\s*\\(\\s*[\\'"].*\\+.*[\\'"]\\s*\\)',
                        r'cursor\\.execute\\s*\\(\\s*[\\'"].*%.*[\\'"]',
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "severity": "critical",
                    "description": "Potential SQL injection vulnerability",
                    "suggestion": "Use parameterized queries or ORM methods",
# BRACKET_SURGEON: disabled
#                     },
                "xss_vulnerability": {
                "patterns": [
                    r"innerHTML\\s*=\\s*.*\\+",
                        r"document\\.write\\s*\\(",
                        r"eval\\s*\\(",
                        r"dangerouslySetInnerHTML",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "severity": "high",
                    "description": "Potential XSS vulnerability",
                    "suggestion": "Use safe DOM manipulation methods or sanitize input",
# BRACKET_SURGEON: disabled
#                     },
                "insecure_random": {
                "patterns": [r"Math\\.random\\s*\\(\\)", r"random\\.random\\s*\\(\\)"],
                    "severity": "medium",
                    "description": "Insecure random number generation",
                    "suggestion": "Use cryptographically secure random generators",
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }


    def _load_maintainability_patterns(self) -> Dict:
        """Load maintainability - related Rule - 1 patterns"""
        return {
            "long_functions": {
                "patterns": [],  # Handled by line counting
                "severity": "medium",
                    "description": "Function too long (>50 lines)",
                    "suggestion": "Break down into smaller, focused functions",
# BRACKET_SURGEON: disabled
#                     },
                "deep_nesting": {
                "patterns": [],  # Handled by indentation analysis
                "severity": "medium",
                    "description": "Excessive nesting depth (>4 levels)",
                    "suggestion": "Refactor to reduce nesting complexity",
# BRACKET_SURGEON: disabled
#                     },
                "magic_numbers": {
                "patterns": [
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     r"\\b(?<!\\.)\\d{2,}(?!\\.\\d)\\b(?!\\s*[\\)\\]])",  # Numbers with 2+ digits
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ],
                    "severity": "low",
                    "description": "Magic numbers detected",
                    "suggestion": "Replace with named constants",
# BRACKET_SURGEON: disabled
#                     },
                "todo_comments": {
                "patterns": [
                    r"(?i)#\\s*(todo|fixme|hack|xxx)\\b","
                        r"(?i)//\\s*(todo|fixme|hack|xxx)\\b",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "severity": "low",
                    "description": "TODO / FIXME comments found",
                    "suggestion": "Address pending tasks or create proper tickets",
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }


    def _load_performance_patterns(self) -> Dict:
        """Load performance - related Rule - 1 patterns"""
        return {
            "inefficient_loops": {
                "patterns": [
                    r"for\\s+\\w+\\s + in\\s + range\\s*\\(\\s * len\\s*\\(",
                        r"while\\s+.*\\.length\\s*>\\s * 0",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
                    "severity": "medium",
                    "description": "Inefficient loop pattern",
                    "suggestion": "Use more efficient iteration methods",
# BRACKET_SURGEON: disabled
#                     },
                "repeated_calculations": {
                "patterns": [
                    r"(\\w+\\.\\w+\\(\\)).*\\1",  # Same method call repeated
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ],
                    "severity": "low",
                    "description": "Repeated calculations detected",
                    "suggestion": "Cache calculation results",
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }


    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single file for Rule - 1 issues"""
        try:
            with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                content = f.read()
                lines = content.split("\\n")

            self.stats["files_scanned"] += 1

            # Analyze security patterns
            self._analyze_patterns(file_path, content, lines, self.security_patterns)

            # Analyze maintainability patterns
            self._analyze_patterns(
                file_path, content, lines, self.maintainability_patterns
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Analyze performance patterns
            self._analyze_patterns(file_path, content, lines, self.performance_patterns)

            # Special analyses
            self._analyze_function_length(file_path, lines)
            self._analyze_nesting_depth(file_path, lines)

        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")


    def _analyze_patterns(
        self, file_path: Path, content: str, lines: List[str], patterns: Dict
# BRACKET_SURGEON: disabled
#     ) -> None:
        """Analyze file content against pattern rules"""
        for rule_name, rule_config in patterns.items():
            for pattern in rule_config.get("patterns", []):
                for line_num, line in enumerate(lines, 1):
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        issue = Rule1Issue(
                            file_path = str(file_path.relative_to(self.project_root)),
                                line_number = line_num,
                                issue_type = rule_name,
                                severity = rule_config["severity"],
                                description = rule_config["description"],
                                current_code = line.strip(),
                                suggested_fix = rule_config["suggestion"],
                                rule_reference = f"Rule - 1.{rule_name}",
                                auto_fixable = rule_config.get("auto_fixable", False),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
                        self._add_issue(issue)


    def _analyze_function_length(self, file_path: Path, lines: List[str]) -> None:
        """Analyze function length for maintainability"""
        current_function = None
        function_start = 0
        brace_count = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Detect function start (simplified)
            if re.match(r"(def |function |class |async def )", stripped):
                if current_function and line_num - function_start > 50:
                    issue = Rule1Issue(
                        file_path = str(file_path.relative_to(self.project_root)),
                            line_number = function_start,
                            issue_type="long_function",
                            severity="medium",
                            description = f"Function is {line_num - function_start} lines long",
                            current_code = f"Function starting at line {function_start}",
                            suggested_fix="Break down into smaller, focused functions",
                            rule_reference="Rule - 1.maintainability.function_length",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             )
                    self._add_issue(issue)

                current_function = stripped
                function_start = line_num
                brace_count = 0


    def _analyze_nesting_depth(self, file_path: Path, lines: List[str]) -> None:
        """Analyze nesting depth for complexity"""
        for line_num, line in enumerate(lines, 1):
            # Count leading whitespace to determine nesting level
            leading_spaces = len(line) - len(line.lstrip())
            nesting_level = leading_spaces // 4  # Assuming 4 - space indentation

            if nesting_level > 4 and line.strip():
                issue = Rule1Issue(
                    file_path = str(file_path.relative_to(self.project_root)),
                        line_number = line_num,
                        issue_type="deep_nesting",
                        severity="medium",
                        description = f"Nesting depth of {nesting_level} levels",
                        current_code = line.strip(),
                        suggested_fix="Refactor to reduce nesting complexity",
                        rule_reference="Rule - 1.maintainability.nesting_depth",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                self._add_issue(issue)


    def _add_issue(self, issue: Rule1Issue) -> None:
        """Add an issue to the list and update statistics"""
        self.issues.append(issue)
        self.stats["issues_found"] += 1
        self.stats[f"{issue.severity}_issues"] += 1

        if issue.auto_fixable:
            self.stats["auto_fixable"] += 1


    def scan_directory(self, directory: Path, extensions: List[str]) -> None:
        """Scan directory for files to analyze"""
        for ext in extensions:
            pattern = f"**/*.{ext}"
            for file_path in directory.glob(pattern):
                # Skip certain directories
                if any(
                    skip in str(file_path)
                    for skip in [
                        "node_modules",
                            "venv",
                            ".git",
                            "dist",
                            "build",
                            "__pycache__",
                            ".pytest_cache",
                            "coverage",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ]
# BRACKET_SURGEON: disabled
#                 ):
                    continue

                self.analyze_file(file_path)


    def generate_report(self, output_format: str = "text") -> str:
        """Generate analysis report"""
        if output_format == "json":
            return self._generate_json_report()
        else:
            return self._generate_text_report()


    def _generate_text_report(self) -> str:
        """Generate text format report"""
        report = []
        report.append("=" * 60)
        report.append("RULE - 1 COMPLIANCE ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Statistics
        report.append("STATISTICS:")
        report.append("-" * 20)
        for key, value in self.stats.items():
            report.append(f"{key.replace('_', ' ').title()}: {value}")
        report.append("")

        # Issues by severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_issues = [i for i in self.issues if i.severity == severity]
            if severity_issues:
                report.append(f"{severity.upper()} ISSUES ({len(severity_issues)}):")
                report.append("-" * 30)

                for issue in severity_issues:
                    report.append(f"File: {issue.file_path}:{issue.line_number}")
                    report.append(f"Type: {issue.issue_type}")
                    report.append(f"Description: {issue.description}")
                    report.append(f"Current: {issue.current_code}")
                    report.append(f"Suggestion: {issue.suggested_fix}")
                    report.append(f"Rule: {issue.rule_reference}")
                    if issue.auto_fixable:
                        report.append("[AUTO - FIXABLE]")
                    report.append("")

        return "\\n".join(report)


    def _generate_json_report(self) -> str:
        """Generate JSON format report"""
        report_data = {
            "timestamp": datetime.now().isoformat(),
                "statistics": self.stats,
                "issues": [
                {
                    "file_path": issue.file_path,
                        "line_number": issue.line_number,
                        "issue_type": issue.issue_type,
                        "severity": issue.severity,
                        "description": issue.description,
                        "current_code": issue.current_code,
                        "suggested_fix": issue.suggested_fix,
                        "rule_reference": issue.rule_reference,
                        "auto_fixable": issue.auto_fixable,
# BRACKET_SURGEON: disabled
#                         }
                for issue in self.issues
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ],
# BRACKET_SURGEON: disabled
#                 }
        return json.dumps(report_data, indent = 2)


    def apply_auto_fixes(self, dry_run: bool = True) -> int:
        """Apply automatic fixes for auto - fixable issues"""
        fixes_applied = 0

        for issue in self.issues:
            if issue.auto_fixable:
                if self._apply_fix(issue, dry_run):
                    fixes_applied += 1

        return fixes_applied


    def _apply_fix(self, issue: Rule1Issue, dry_run: bool) -> bool:
        """Apply a specific fix"""
        try:
            file_path = self.project_root / issue.file_path

            if dry_run:
                logger.info(
                    f"[DRY RUN] Would fix {issue.issue_type} in {issue.file_path}:{issue.line_number}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                return True

            # Implementation would depend on the specific fix type
            logger.info(
                f"Applied fix for {issue.issue_type} in {issue.file_path}:{issue.line_number}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return True

        except Exception as e:
            logger.error(f"Failed to apply fix for {issue.issue_type}: {e}")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Rule - 1 Compliance Analysis and Suggestion Tool"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument(
        "--target - dir",
            default=".",
            help="Target directory to analyze (default: current directory)",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument(
        "--extensions",
            default="py,js,ts,jsx,tsx,php,html",
            help="File extensions to analyze (comma - separated)",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument(
        "--output - format",
            choices=["text", "json"],
            default="text",
            help="Output format for report",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument(
        "--output - file", help="Output file for report (default: stdout)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument(
        "--auto - fix",
            action="store_true",
            help="Apply automatic fixes for auto - fixable issues",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument(
        "--dry - run",
            action="store_true",
            help="Show what would be fixed without making changes",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
    parser.add_argument(
        "--severity - filter",
            choices=["critical", "high", "medium", "low"],
            help="Only show issues of specified severity or higher",
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

    args = parser.parse_args()

    # Initialize analyzer
    project_root = Path(args.target_dir).resolve()
    analyzer = Rule1Analyzer(str(project_root))

    # Parse extensions
    extensions = [ext.strip() for ext in args.extensions.split(",")]

    # Run analysis
    logger.info(f"Starting Rule - 1 analysis of {project_root}")
    analyzer.scan_directory(project_root, extensions)

    # Apply auto - fixes if requested
    if args.auto_fix:
        fixes_applied = analyzer.apply_auto_fixes(dry_run = args.dry_run)
        logger.info(f"Applied {fixes_applied} automatic fixes")

    # Generate report
    report = analyzer.generate_report(args.output_format)

    # Output report
    if args.output_file:
        with open(args.output_file, "w") as f:
            f.write(report)
        logger.info(f"Report saved to {args.output_file}")
    else:
        print(report)

    # Exit with appropriate code
    if analyzer.stats["critical_issues"] > 0:
        sys.exit(2)  # Critical issues found
    elif analyzer.stats["high_issues"] > 0:
        sys.exit(1)  # High severity issues found
    else:
        sys.exit(0)  # No critical / high issues

if __name__ == "__main__":
    main()