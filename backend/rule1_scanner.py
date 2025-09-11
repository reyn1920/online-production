#!/usr/bin/env python3
"""
TRAE.AI Rule-1 Content Scanner and Enforcer

Production-ready content scanning system that identifies and replaces
forbidden terms, patterns, and content violations. Designed for high-performance
content moderation with configurable rules and comprehensive reporting.

Rule-1 Definition:
- No forbidden terms or patterns in content
- Automatic detection and replacement
- Comprehensive audit trail
- Performance-optimized scanning
- Configurable rule sets

Author: TRAE.AI System
Version: 1.0.0
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import our logger
try:
    from utils.logger import get_logger
except ImportError:
    # Fallback if logger not available
    import logging

    def get_logger(name=None):
        return logging.getLogger(name or __name__)


@dataclass
class ScanResult:
    """
    Result of a content scan operation.

    Attributes:
        file_path (str): Path to the scanned file
        violations_found (int): Number of violations detected
        violations (List[Dict]): Detailed violation information
        scan_duration (float): Time taken for scan in seconds
        file_size (int): Size of scanned file in bytes
        scan_timestamp (str): ISO timestamp of scan
        rule_set_version (str): Version of rules used for scanning
    """

    file_path: str
    violations_found: int
    violations: List[Dict[str, Any]]
    scan_duration: float
    file_size: int
    scan_timestamp: str
    rule_set_version: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class EnforcementResult:
    """
    Result of content enforcement operation.

    Attributes:
        file_path (str): Path to the enforced file
        replacements_made (int): Number of replacements performed
        replacements (List[Dict]): Detailed replacement information
        enforcement_duration (float): Time taken for enforcement in seconds
        backup_created (bool): Whether backup was created
        enforcement_timestamp (str): ISO timestamp of enforcement
    """

    file_path: str
    replacements_made: int
    replacements: List[Dict[str, Any]]
    enforcement_duration: float
    backup_created: bool
    enforcement_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


class Rule1DeepScanner:
    """
    Deep content scanner for Rule-1 violations.

    Performs comprehensive scanning of files and directories to identify
    forbidden terms, patterns, and content violations with high performance
    and detailed reporting.
    """

    def __init__(
        self,
        rules_file: str = "data/rule1_patterns.json",
        db_path: str = "data/rule1_scans.sqlite",
        max_workers: int = 4,
        max_file_size: int = 100 * 1024 * 1024,
    ):  # 100MB
        """
        Initialize the Rule-1 Deep Scanner.

        Args:
            rules_file (str): Path to JSON file containing scan rules
            db_path (str): Path to SQLite database for scan results
            max_workers (int): Maximum number of worker threads
            max_file_size (int): Maximum file size to scan (bytes)
        """
        self.rules_file = Path(rules_file)
        self.db_path = Path(db_path)
        self.max_workers = max_workers
        self.max_file_size = max_file_size

        # Thread safety
        self._lock = threading.Lock()

        # Initialize logger
        self.logger = get_logger("rule1_scanner")

        # Initialize components
        self._init_database()
        self._load_rules()

        # Performance tracking
        self.stats = {"files_scanned": 0, "violations_found": 0, "total_scan_time": 0.0}

    def _init_database(self) -> None:
        """
        Initialize SQLite database for storing scan results.
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    file_hash TEXT NOT NULL,
                    violations_found INTEGER NOT NULL,
                    violations_json TEXT NOT NULL,
                    scan_duration REAL NOT NULL,
                    file_size INTEGER NOT NULL,
                    scan_timestamp TEXT NOT NULL,
                    rule_set_version TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_file_path ON scan_results(file_path)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scan_timestamp ON scan_results(scan_timestamp)
            """
            )

            conn.commit()

    def _load_rules(self) -> None:
        """
        Load scanning rules from configuration file.
        """
        if self.rules_file.exists():
            try:
                with open(self.rules_file, "r", encoding="utf-8") as f:
                    rules_data = json.load(f)

                self.forbidden_terms = set(rules_data.get("forbidden_terms", []))
                self.forbidden_patterns = rules_data.get("forbidden_patterns", [])
                self.file_extensions = set(
                    rules_data.get(
                        "file_extensions",
                        [".py", ".js", ".html", ".css", ".txt", ".md"],
                    )
                )
                self.exclude_dirs = set(
                    rules_data.get(
                        "exclude_dirs", [".git", "__pycache__", "node_modules", ".venv"]
                    )
                )
                self.rule_set_version = rules_data.get("version", "1.0.0")

                # Compile regex patterns for performance
                self.compiled_patterns = []
                for pattern in self.forbidden_patterns:
                    try:
                        compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                        self.compiled_patterns.append((pattern, compiled))
                    except re.error as e:
                        self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")

                self.logger.info(
                    f"Loaded {len(self.forbidden_terms)} forbidden terms and {len(self.compiled_patterns)} patterns"
                )

            except Exception as e:
                self.logger.error(f"Failed to load rules from {self.rules_file}: {e}")
                self._create_default_rules()
        else:
            self._create_default_rules()

    def _create_default_rules(self) -> None:
        """
        Create default scanning rules.
        """
        default_rules = {
            "version": "1.0.0",
            "forbidden_terms": [
                "TODO",
                "FIXME",
                "HACK",
                "XXX",
                "BUG",
                "password123",
                "admin",
                "root",
                "secret",
                "api_key",
                "private_key",
                "access_token",
            ],
            "forbidden_patterns": [
                r"\b(password|pwd)\s*=\s*['\"][^'\"]{1,}['\"]"  # Password assignments
                r"\b(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{10,}['\"]"  # API keys
                r"\b(secret|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]"  # Secrets/tokens
                r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"  # Credit card numbers
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"  # Email addresses (if sensitive)
            ],
            "file_extensions": [
                ".py",
                ".js",
                ".ts",
                ".html",
                ".css",
                ".json",
                ".txt",
                ".md",
                ".yml",
                ".yaml",
                ".xml",
                ".sql",
            ],
            "exclude_dirs": [
                ".git",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build",
            ],
        }

        # Create rules file
        self.rules_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.rules_file, "w", encoding="utf-8") as f:
            json.dump(default_rules, f, indent=2)

        # Load the default rules
        self.forbidden_terms = set(default_rules["forbidden_terms"])
        self.forbidden_patterns = default_rules["forbidden_patterns"]
        self.file_extensions = set(default_rules["file_extensions"])
        self.exclude_dirs = set(default_rules["exclude_dirs"])
        self.rule_set_version = default_rules["version"]

        # Compile patterns
        self.compiled_patterns = []
        for pattern in self.forbidden_patterns:
            try:
                compiled = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                self.compiled_patterns.append((pattern, compiled))
            except re.error as e:
                self.logger.warning(f"Invalid regex pattern '{pattern}': {e}")

        self.logger.info(
            f"Created default rules with {len(self.forbidden_terms)} terms and {len(self.compiled_patterns)} patterns"
        )

    def _calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate SHA-256 hash of file content.

        Args:
            file_path (Path): Path to file

        Returns:
            str: Hexadecimal hash string
        """
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def _should_scan_file(self, file_path: Path) -> bool:
        """
        Determine if a file should be scanned.

        Args:
            file_path (Path): Path to file

        Returns:
            bool: True if file should be scanned
        """
        # Check file extension
        if file_path.suffix.lower() not in self.file_extensions:
            return False

        # Check file size
        try:
            if file_path.stat().st_size > self.max_file_size:
                self.logger.warning(
                    f"Skipping large file: {file_path} ({file_path.stat().st_size} bytes)"
                )
                return False
        except OSError:
            return False

        # Check if file is in excluded directory
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in file_path.parts:
                return False

        return True

    def scan_file(self, file_path: Union[str, Path]) -> ScanResult:
        """
        Scan a single file for Rule-1 violations.

        Args:
            file_path (Union[str, Path]): Path to file to scan

        Returns:
            ScanResult: Detailed scan results
        """
        import time

        start_time = time.time()
        file_path = Path(file_path)
        violations = []

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            file_size = len(content.encode("utf-8"))

            # Scan for forbidden terms
            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                line_lower = line.lower()

                # Check forbidden terms
                for term in self.forbidden_terms:
                    if term.lower() in line_lower:
                        violations.append(
                            {
                                "type": "forbidden_term",
                                "term": term,
                                "line_number": line_num,
                                "line_content": line.strip(),
                                "severity": "high",
                            }
                        )

                # Check regex patterns
                for pattern_name, compiled_pattern in self.compiled_patterns:
                    matches = compiled_pattern.finditer(line)
                    for match in matches:
                        violations.append(
                            {
                                "type": "forbidden_pattern",
                                "pattern": pattern_name,
                                "match": match.group(),
                                "line_number": line_num,
                                "line_content": line.strip(),
                                "start_pos": match.start(),
                                "end_pos": match.end(),
                                "severity": "critical",
                            }
                        )

            scan_duration = time.time() - start_time

            # Create scan result
            result = ScanResult(
                file_path=str(file_path),
                violations_found=len(violations),
                violations=violations,
                scan_duration=scan_duration,
                file_size=file_size,
                scan_timestamp=datetime.now().isoformat(),
                rule_set_version=self.rule_set_version,
            )

            # Store result in database
            self._store_scan_result(result)

            # Update statistics
            with self._lock:
                self.stats["files_scanned"] += 1
                self.stats["violations_found"] += len(violations)
                self.stats["total_scan_time"] += scan_duration

            if violations:
                self.logger.warning(
                    f"Found {len(violations)} violations in {file_path}"
                )
            else:
                self.logger.debug(f"No violations found in {file_path}")

            return result

        except Exception as e:
            self.logger.error(f"Failed to scan file {file_path}: {e}")
            return ScanResult(
                file_path=str(file_path),
                violations_found=0,
                violations=[],
                scan_duration=time.time() - start_time,
                file_size=0,
                scan_timestamp=datetime.now().isoformat(),
                rule_set_version=self.rule_set_version,
            )

    def scan_directory(
        self, directory_path: Union[str, Path], recursive: bool = True
    ) -> List[ScanResult]:
        """
        Scan a directory for Rule-1 violations.

        Args:
            directory_path (Union[str, Path]): Path to directory to scan
            recursive (bool): Whether to scan subdirectories

        Returns:
            List[ScanResult]: List of scan results for all files
        """
        directory_path = Path(directory_path)

        if not directory_path.exists() or not directory_path.is_dir():
            self.logger.error(f"Directory does not exist: {directory_path}")
            return []

        # Collect files to scan
        files_to_scan = []

        if recursive:
            for file_path in directory_path.rglob("*"):
                if file_path.is_file() and self._should_scan_file(file_path):
                    files_to_scan.append(file_path)
        else:
            for file_path in directory_path.iterdir():
                if file_path.is_file() and self._should_scan_file(file_path):
                    files_to_scan.append(file_path)

        self.logger.info(f"Scanning {len(files_to_scan)} files in {directory_path}")

        # Scan files using thread pool
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.scan_file, file_path): file_path
                for file_path in files_to_scan
            }

            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    self.logger.error(f"Failed to scan {file_path}: {e}")

        # Sort results by violations (most violations first)
        results.sort(key=lambda x: x.violations_found, reverse=True)

        total_violations = sum(r.violations_found for r in results)
        self.logger.info(
            f"Scan complete: {len(results)} files, {total_violations} total violations"
        )

        return results

    def _store_scan_result(self, result: ScanResult) -> None:
        """
        Store scan result in database.

        Args:
            result (ScanResult): Scan result to store
        """
        try:
            file_hash = self._calculate_file_hash(Path(result.file_path))

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO scan_results 
                    (file_path, file_hash, violations_found, violations_json, 
                     scan_duration, file_size, scan_timestamp, rule_set_version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.file_path,
                        file_hash,
                        result.violations_found,
                        json.dumps(result.violations),
                        result.scan_duration,
                        result.file_size,
                        result.scan_timestamp,
                        result.rule_set_version,
                    ),
                )
                conn.commit()

        except Exception as e:
            self.logger.error(f"Failed to store scan result: {e}")

    def get_scan_history(
        self, file_path: str = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get scan history from database.

        Args:
            file_path (str, optional): Filter by specific file path
            limit (int): Maximum number of results

        Returns:
            List[Dict]: Scan history records
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row

                if file_path:
                    cursor = conn.execute(
                        """
                        SELECT * FROM scan_results 
                        WHERE file_path = ? 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (file_path, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM scan_results 
                        ORDER BY created_at DESC 
                        LIMIT ?
                    """,
                        (limit,),
                    )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Failed to get scan history: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get scanning statistics.

        Returns:
            Dict: Statistics including performance metrics
        """
        stats = self.stats.copy()

        # Add database statistics
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM scan_results")
                stats["total_scans_in_db"] = cursor.fetchone()[0]

                cursor = conn.execute("SELECT SUM(violations_found) FROM scan_results")
                result = cursor.fetchone()[0]
                stats["total_violations_in_db"] = result if result else 0

        except Exception as e:
            self.logger.error(f"Failed to get database statistics: {e}")

        return stats


class Rule1Enforcer:
    """
    Content enforcer for Rule-1 violations.

    Automatically replaces forbidden terms and patterns with approved
    alternatives, maintaining content integrity while ensuring compliance.
    """

    def __init__(
        self,
        scanner: Rule1DeepScanner,
        replacements_file: str = "data/rule1_replacements.json",
        create_backups: bool = True,
        backup_dir: str = "data/backups",
    ):
        """
        Initialize the Rule-1 Enforcer.

        Args:
            scanner (Rule1DeepScanner): Scanner instance for violation detection
            replacements_file (str): Path to JSON file containing replacement rules
            create_backups (bool): Whether to create backups before enforcement
            backup_dir (str): Directory for backup files
        """
        self.scanner = scanner
        self.replacements_file = Path(replacements_file)
        self.create_backups = create_backups
        self.backup_dir = Path(backup_dir)

        if self.create_backups:
            self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize logger
        self.logger = get_logger("rule1_enforcer")

        # Load replacement rules
        self._load_replacements()

    def _load_replacements(self) -> None:
        """
        Load replacement rules from configuration file.
        """
        if self.replacements_file.exists():
            try:
                with open(self.replacements_file, "r", encoding="utf-8") as f:
                    replacements_data = json.load(f)

                self.term_replacements = replacements_data.get("term_replacements", {})
                self.pattern_replacements = replacements_data.get(
                    "pattern_replacements", {}
                )

                self.logger.info(
                    f"Loaded {len(self.term_replacements)} term replacements and {len(self.pattern_replacements)} pattern replacements"
                )

            except Exception as e:
                self.logger.error(
                    f"Failed to load replacements from {self.replacements_file}: {e}"
                )
                self._create_default_replacements()
        else:
            self._create_default_replacements()

    def _create_default_replacements(self) -> None:
        """
        Create default replacement rules.
        """
        default_replacements = {
            "term_replacements": {
                "TODO": "# Task: ",
                "FIXME": "# Fix: ",
                "HACK": "# Workaround: ",
                "XXX": "# Note: ",
                "BUG": "# Issue: ",
                "password123": "[REDACTED_PASSWORD]",
                "admin": "[REDACTED_USERNAME]",
                "root": "[REDACTED_USERNAME]",
                "secret": "[REDACTED_SECRET]",
            },
            "pattern_replacements": {
                r"\b(password|pwd)\s*=\s*['\"][^'\"]{1,}['\"]" "$1='[REDACTED]'",
                r"\b(api[_-]?key|apikey)\s*[=:]\s*['\"][^'\"]{10,}['\"]"
                "$1='[REDACTED]'",
                r"\b(secret|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]" "$1='[REDACTED]'",
            },
        }

        # Create replacements file
        self.replacements_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.replacements_file, "w", encoding="utf-8") as f:
            json.dump(default_replacements, f, indent=2)

        self.term_replacements = default_replacements["term_replacements"]
        self.pattern_replacements = default_replacements["pattern_replacements"]

        self.logger.info("Created default replacement rules")

    def _create_backup(self, file_path: Path) -> bool:
        """
        Create a backup of the file before enforcement.

        Args:
            file_path (Path): Path to file to backup

        Returns:
            bool: True if backup was created successfully
        """
        if not self.create_backups:
            return False

        try:
            import shutil

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.name}.{timestamp}.backup"
            backup_path = self.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create backup for {file_path}: {e}")
            return False

    def enforce_file(self, file_path: Union[str, Path]) -> EnforcementResult:
        """
        Enforce Rule-1 compliance on a single file.

        Args:
            file_path (Union[str, Path]): Path to file to enforce

        Returns:
            EnforcementResult: Detailed enforcement results
        """
        import time

        start_time = time.time()
        file_path = Path(file_path)
        replacements = []

        try:
            # First, scan the file to identify violations
            scan_result = self.scanner.scan_file(file_path)

            if scan_result.violations_found == 0:
                return EnforcementResult(
                    file_path=str(file_path),
                    replacements_made=0,
                    replacements=[],
                    enforcement_duration=time.time() - start_time,
                    backup_created=False,
                    enforcement_timestamp=datetime.now().isoformat(),
                )

            # Create backup if enabled
            backup_created = self._create_backup(file_path)

            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Apply term replacements
            for violation in scan_result.violations:
                if violation["type"] == "forbidden_term":
                    term = violation["term"]
                    if term in self.term_replacements:
                        replacement = self.term_replacements[term]
                        old_content = content
                        content = content.replace(term, replacement)

                        if content != old_content:
                            replacements.append(
                                {
                                    "type": "term_replacement",
                                    "original": term,
                                    "replacement": replacement,
                                    "line_number": violation["line_number"],
                                }
                            )

            # Apply pattern replacements
            for pattern, replacement in self.pattern_replacements.items():
                try:
                    compiled_pattern = re.compile(pattern, re.IGNORECASE | re.MULTILINE)
                    matches = list(compiled_pattern.finditer(content))

                    if matches:
                        for match in reversed(
                            matches
                        ):  # Replace from end to preserve positions
                            original_text = match.group()
                            new_text = compiled_pattern.sub(replacement, original_text)

                            content = (
                                content[: match.start()]
                                + new_text
                                + content[match.end() :]
                            )

                            replacements.append(
                                {
                                    "type": "pattern_replacement",
                                    "original": original_text,
                                    "replacement": new_text,
                                    "pattern": pattern,
                                    "position": match.start(),
                                }
                            )

                except re.error as e:
                    self.logger.error(f"Invalid replacement pattern '{pattern}': {e}")

            # Write the modified content back to file
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.logger.info(
                    f"Applied {len(replacements)} replacements to {file_path}"
                )

            enforcement_duration = time.time() - start_time

            return EnforcementResult(
                file_path=str(file_path),
                replacements_made=len(replacements),
                replacements=replacements,
                enforcement_duration=enforcement_duration,
                backup_created=backup_created,
                enforcement_timestamp=datetime.now().isoformat(),
            )

        except Exception as e:
            self.logger.error(f"Failed to enforce file {file_path}: {e}")
            return EnforcementResult(
                file_path=str(file_path),
                replacements_made=0,
                replacements=[],
                enforcement_duration=time.time() - start_time,
                backup_created=False,
                enforcement_timestamp=datetime.now().isoformat(),
            )

    def enforce_directory(
        self, directory_path: Union[str, Path], recursive: bool = True
    ) -> List[EnforcementResult]:
        """
        Enforce Rule-1 compliance on a directory.

        Args:
            directory_path (Union[str, Path]): Path to directory to enforce
            recursive (bool): Whether to enforce subdirectories

        Returns:
            List[EnforcementResult]: List of enforcement results for all files
        """
        directory_path = Path(directory_path)

        # First scan the directory to identify files with violations
        scan_results = self.scanner.scan_directory(directory_path, recursive)

        # Filter to only files with violations
        files_with_violations = [
            result for result in scan_results if result.violations_found > 0
        ]

        self.logger.info(
            f"Enforcing {len(files_with_violations)} files with violations"
        )

        # Enforce each file
        enforcement_results = []
        for scan_result in files_with_violations:
            enforcement_result = self.enforce_file(scan_result.file_path)
            enforcement_results.append(enforcement_result)

        total_replacements = sum(r.replacements_made for r in enforcement_results)
        self.logger.info(
            f"Enforcement complete: {total_replacements} total replacements made"
        )

        return enforcement_results


if __name__ == "__main__":
    # Example usage and testing
    import os
    import tempfile

    # Create test environment
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create test files with violations
        test_file1 = temp_path / "test1.py"
        test_file1.write_text(
            """
# This is a test file with violations
password = "secret123"  # TODO: Remove this
api_key = "sk-1234567890abcdef"  # FIXME: Use environment variable

def main():
    # XXX: This is a hack
    print("Hello World")
        """
        )

        test_file2 = temp_path / "test2.js"
        test_file2.write_text(
            """
// JavaScript test file
const password = 'admin123';  // BUG: Hardcoded password
const token = 'secret_token_here';  // TODO: Load from config
        """
        )

        # Initialize scanner and enforcer
        scanner = Rule1DeepScanner(
            rules_file=str(temp_path / "rules.json"),
            db_path=str(temp_path / "scans.sqlite"),
        )

        enforcer = Rule1Enforcer(
            scanner=scanner,
            replacements_file=str(temp_path / "replacements.json"),
            backup_dir=str(temp_path / "backups"),
        )

        # Test scanning
        print("\n=== Scanning Test Files ===")
        scan_results = scanner.scan_directory(temp_path)

        for result in scan_results:
            print(f"\nFile: {result.file_path}")
            print(f"Violations: {result.violations_found}")
            for violation in result.violations:
                print(
                    f"  - {violation['type']}: {violation.get('term', violation.get('pattern', 'N/A'))} at line {violation['line_number']}"
                )

        # Test enforcement
        print("\n=== Enforcing Rule-1 Compliance ===")
        enforcement_results = enforcer.enforce_directory(temp_path)

        for result in enforcement_results:
            print(f"\nFile: {result.file_path}")
            print(f"Replacements: {result.replacements_made}")
            print(f"Backup created: {result.backup_created}")
            for replacement in result.replacements:
                print(
                    f"  - Replaced '{replacement['original']}' with '{replacement['replacement']}'"
                )

        # Show statistics
        print("\n=== Statistics ===")
        stats = scanner.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")

        print("\n=== Test completed successfully ===")
