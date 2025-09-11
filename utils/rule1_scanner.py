#!/usr/bin/env python3
"""
Rule-1 Content Scanner and Enforcer

This module provides comprehensive content scanning and enforcement capabilities
for the TRAE.AI system. It implements Rule-1 compliance by detecting and
replacing forbidden terms, ensuring content meets platform guidelines.

Features:
- Deep directory scanning for forbidden content
- Configurable forbidden terms database
- Automatic content replacement and enforcement
- Backup and rollback capabilities
- Detailed reporting and logging
- Multi-format file support (text, markdown, code, etc.)

Author: TRAE.AI System
Version: 1.0.0
"""

import hashlib
import json
import mimetypes
import os
import re
import shutil
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from utils.logger import get_logger


@dataclass
class ScanResult:
    """Result of a content scan operation."""

    file_path: str
    violations: List[Dict[str, Any]]
    total_violations: int
    file_size: int
    scan_timestamp: str
    file_hash: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class EnforcementResult:
    """Result of a content enforcement operation."""

    file_path: str
    replacements_made: int
    backup_created: bool
    backup_path: Optional[str]
    original_hash: str
    new_hash: str
    enforcement_timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class Rule1DeepScanner:
    """
    Deep content scanner for Rule-1 compliance.

    Scans directories and files for forbidden terms and content patterns
    that violate platform guidelines or content policies.
    """

    def __init__(
        self,
        forbidden_terms_db: str = "data/forbidden_terms.json",
        scan_results_db: str = "data/scan_results.sqlite",
        backup_dir: str = "data/backups",
    ):
        """
        Initialize the Rule-1 Deep Scanner.

        Args:
            forbidden_terms_db: Path to forbidden terms database
            scan_results_db: Path to scan results SQLite database
            backup_dir: Directory for file backups
        """
        self.logger = get_logger(__name__)
        self.forbidden_terms_db = Path(forbidden_terms_db)
        self.scan_results_db = Path(scan_results_db)
        self.backup_dir = Path(backup_dir)

        # Ensure directories exist
        self.forbidden_terms_db.parent.mkdir(parents=True, exist_ok=True)
        self.scan_results_db.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Load forbidden terms
        self.forbidden_terms = self._load_forbidden_terms()

        # Initialize database
        self._init_database()

        # Supported file extensions
        self.supported_extensions = {
            ".txt",
            ".md",
            ".py",
            ".js",
            ".html",
            ".css",
            ".json",
            ".xml",
            ".yml",
            ".yaml",
            ".ini",
            ".cfg",
            ".conf",
            ".log",
            ".rst",
            ".tex",
            ".csv",
            ".sql",
            ".sh",
            ".bat",
        }

        self.logger.info(
            f"Rule1DeepScanner initialized with {len(self.forbidden_terms)} forbidden terms"
        )

    def _load_forbidden_terms(self) -> Dict[str, Dict[str, Any]]:
        """Load forbidden terms from database file."""
        if not self.forbidden_terms_db.exists():
            # Create default forbidden terms database
            default_terms = {
                "hate_speech": {
                    "category": "hate_speech",
                    "severity": "high",
                    "patterns": [
                        r"\b(hate|hatred)\s+(speech|content)\b",
                        r"\b(racist|racism)\b",
                        r"\b(sexist|sexism)\b",
                        r"\b(homophobic|homophobia)\b",
                    ],
                    "replacement": "[CONTENT_REMOVED]",
                    "description": "Hate speech and discriminatory content",
                },
                "violence": {
                    "category": "violence",
                    "severity": "high",
                    "patterns": [
                        r"\b(kill|murder|assassinate)\s+(someone|people|person)\b",
                        r"\b(bomb|explosion|terrorist)\s+(attack|threat)\b",
                        r"\b(violence|violent)\s+(content|imagery)\b",
                    ],
                    "replacement": "[VIOLENT_CONTENT_REMOVED]",
                    "description": "Violent content and threats",
                },
                "misinformation": {
                    "category": "misinformation",
                    "severity": "medium",
                    "patterns": [
                        r"\b(fake|false)\s+(news|information)\b",
                        r"\b(conspiracy|hoax)\s+(theory|theories)\b",
                        r"\b(misinformation|disinformation)\b",
                    ],
                    "replacement": "[UNVERIFIED_CLAIM]",
                    "description": "Misinformation and false claims",
                },
                "spam": {
                    "category": "spam",
                    "severity": "low",
                    "patterns": [
                        r"\b(click\s+here|buy\s+now)\b",
                        r"\b(limited\s+time|act\s+now)\b",
                        r"\b(free\s+money|get\s+rich)\b",
                    ],
                    "replacement": "[PROMOTIONAL_CONTENT]",
                    "description": "Spam and promotional content",
                },
                "personal_info": {
                    "category": "privacy",
                    "severity": "high",
                    "patterns": [
                        r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern
                        r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",  # Credit card pattern
                        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email pattern
                    ],
                    "replacement": "[PERSONAL_INFO_REDACTED]",
                    "description": "Personal information and sensitive data",
                },
            }

            with open(self.forbidden_terms_db, "w") as f:
                json.dump(default_terms, f, indent=2)

            self.logger.info(
                f"Created default forbidden terms database: {self.forbidden_terms_db}"
            )
            return default_terms

        try:
            with open(self.forbidden_terms_db, "r") as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading forbidden terms: {e}")
            return {}

    def _init_database(self):
        """Initialize the scan results database."""
        with sqlite3.connect(self.scan_results_db) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scan_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_violations INTEGER DEFAULT 0,
                    file_size INTEGER DEFAULT 0,
                    file_hash TEXT,
                    violations_json TEXT,
                    scan_duration_ms INTEGER DEFAULT 0
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enforcement_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    enforcement_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    replacements_made INTEGER DEFAULT 0,
                    backup_path TEXT,
                    original_hash TEXT,
                    new_hash TEXT,
                    enforcer_version TEXT
                )
            """
            )

            # Create indexes for better performance
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scan_file_path ON scan_results(file_path)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_enforcement_file_path ON enforcement_history(file_path)"
            )
            conn.commit()

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            self.logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if file is a text file that can be scanned."""
        # Check extension
        if file_path.suffix.lower() in self.supported_extensions:
            return True

        # Check MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type and mime_type.startswith("text/"):
            return True

        # Try to read first few bytes to detect text
        try:
            with open(file_path, "rb") as f:
                sample = f.read(1024)
                # Check if it's mostly printable ASCII
                printable_ratio = sum(
                    1 for b in sample if 32 <= b <= 126 or b in [9, 10, 13]
                ) / len(sample)
                return printable_ratio > 0.7
        except Exception:
            return False

    def scan_file(self, file_path: Path) -> ScanResult:
        """Scan a single file for forbidden content."""
        start_time = datetime.now()
        violations = []

        try:
            if not file_path.exists() or not file_path.is_file():
                self.logger.warning(f"File not found or not a file: {file_path}")
                return ScanResult(
                    file_path=str(file_path),
                    violations=[],
                    total_violations=0,
                    file_size=0,
                    scan_timestamp=start_time.isoformat(),
                    file_hash="",
                )

            if not self._is_text_file(file_path):
                self.logger.debug(f"Skipping non-text file: {file_path}")
                return ScanResult(
                    file_path=str(file_path),
                    violations=[],
                    total_violations=0,
                    file_size=file_path.stat().st_size,
                    scan_timestamp=start_time.isoformat(),
                    file_hash=self._calculate_file_hash(file_path),
                )

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Scan for forbidden terms
            for term_id, term_data in self.forbidden_terms.items():
                patterns = term_data.get("patterns", [])
                category = term_data.get("category", "unknown")
                severity = term_data.get("severity", "medium")

                for pattern in patterns:
                    try:
                        matches = list(
                            re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
                        )
                        for match in matches:
                            line_num = content[: match.start()].count("\n") + 1
                            violations.append(
                                {
                                    "term_id": term_id,
                                    "category": category,
                                    "severity": severity,
                                    "pattern": pattern,
                                    "match": match.group(),
                                    "line_number": line_num,
                                    "start_pos": match.start(),
                                    "end_pos": match.end(),
                                    "context": self._get_context(
                                        content, match.start(), match.end()
                                    ),
                                }
                            )
                    except re.error as e:
                        self.logger.error(f"Invalid regex pattern '{pattern}': {e}")

            # Create scan result
            result = ScanResult(
                file_path=str(file_path),
                violations=violations,
                total_violations=len(violations),
                file_size=file_path.stat().st_size,
                scan_timestamp=start_time.isoformat(),
                file_hash=self._calculate_file_hash(file_path),
            )

            # Store result in database
            self._store_scan_result(
                result, (datetime.now() - start_time).total_seconds() * 1000
            )

            if violations:
                self.logger.warning(
                    f"Found {len(violations)} violations in {file_path}"
                )
            else:
                self.logger.debug(f"No violations found in {file_path}")

            return result

        except Exception as e:
            self.logger.error(f"Error scanning file {file_path}: {e}")
            return ScanResult(
                file_path=str(file_path),
                violations=[],
                total_violations=0,
                file_size=0,
                scan_timestamp=start_time.isoformat(),
                file_hash="",
            )

    def _get_context(
        self, content: str, start: int, end: int, context_size: int = 50
    ) -> str:
        """Get context around a match for better understanding."""
        context_start = max(0, start - context_size)
        context_end = min(len(content), end + context_size)
        context = content[context_start:context_end]

        # Replace newlines with spaces for cleaner output
        context = re.sub(r"\s+", " ", context).strip()

        return context

    def _store_scan_result(self, result: ScanResult, duration_ms: float):
        """Store scan result in database."""
        try:
            with sqlite3.connect(self.scan_results_db) as conn:
                conn.execute(
                    """
                    INSERT INTO scan_results 
                    (file_path, total_violations, file_size, file_hash, violations_json, scan_duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.file_path,
                        result.total_violations,
                        result.file_size,
                        result.file_hash,
                        json.dumps(result.violations),
                        int(duration_ms),
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing scan result: {e}")

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
    ) -> List[ScanResult]:
        """Scan a directory for forbidden content."""
        results = []

        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Directory not found: {directory}")
            return results

        self.logger.info(
            f"Starting directory scan: {directory} (recursive={recursive})"
        )

        try:
            if recursive:
                files = directory.rglob("*")
            else:
                files = directory.glob("*")

            for file_path in files:
                if file_path.is_file():
                    # Apply file pattern filters if specified
                    if file_patterns:
                        if not any(
                            file_path.match(pattern) for pattern in file_patterns
                        ):
                            continue

                    result = self.scan_file(file_path)
                    results.append(result)

        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")

        total_violations = sum(r.total_violations for r in results)
        self.logger.info(
            f"Directory scan completed: {len(results)} files, {total_violations} violations"
        )

        return results

    def get_scan_history(
        self, file_path: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get scan history from database."""
        try:
            with sqlite3.connect(self.scan_results_db) as conn:
                conn.row_factory = sqlite3.Row

                if file_path:
                    cursor = conn.execute(
                        """
                        SELECT * FROM scan_results 
                        WHERE file_path = ? 
                        ORDER BY scan_timestamp DESC 
                        LIMIT ?
                    """,
                        (file_path, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM scan_results 
                        ORDER BY scan_timestamp DESC 
                        LIMIT ?
                    """,
                        (limit,),
                    )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error retrieving scan history: {e}")
            return []

    def add_forbidden_term(
        self,
        term_id: str,
        category: str,
        patterns: List[str],
        severity: str = "medium",
        replacement: str = "[CONTENT_REMOVED]",
        description: str = "",
    ) -> bool:
        """Add a new forbidden term to the database."""
        try:
            self.forbidden_terms[term_id] = {
                "category": category,
                "severity": severity,
                "patterns": patterns,
                "replacement": replacement,
                "description": description,
            }

            # Save to file
            with open(self.forbidden_terms_db, "w") as f:
                json.dump(self.forbidden_terms, f, indent=2)

            self.logger.info(f"Added forbidden term: {term_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error adding forbidden term: {e}")
            return False

    def remove_forbidden_term(self, term_id: str) -> bool:
        """Remove a forbidden term from the database."""
        try:
            if term_id in self.forbidden_terms:
                del self.forbidden_terms[term_id]

                # Save to file
                with open(self.forbidden_terms_db, "w") as f:
                    json.dump(self.forbidden_terms, f, indent=2)

                self.logger.info(f"Removed forbidden term: {term_id}")
                return True
            else:
                self.logger.warning(f"Forbidden term not found: {term_id}")
                return False

        except Exception as e:
            self.logger.error(f"Error removing forbidden term: {e}")
            return False


class Rule1Enforcer:
    """
    Content enforcer for Rule-1 compliance.

    Automatically replaces forbidden content with approved alternatives,
    maintaining content integrity while ensuring compliance.
    """

    def __init__(self, scanner: Rule1DeepScanner):
        """
        Initialize the Rule-1 Enforcer.

        Args:
            scanner: Rule1DeepScanner instance for content analysis
        """
        self.scanner = scanner
        self.logger = get_logger(__name__)

        self.logger.info("Rule1Enforcer initialized")

    def create_backup(self, file_path: Path) -> Optional[Path]:
        """Create a backup of the original file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}.backup"
            backup_path = self.scanner.backup_dir / backup_name

            shutil.copy2(file_path, backup_path)
            self.logger.info(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            self.logger.error(f"Error creating backup for {file_path}: {e}")
            return None

    def enforce_file(
        self, file_path: Path, create_backup: bool = True
    ) -> EnforcementResult:
        """Enforce Rule-1 compliance on a single file."""
        start_time = datetime.now()

        # Get original file hash
        original_hash = self.scanner._calculate_file_hash(file_path)

        # Create backup if requested
        backup_path = None
        backup_created = False
        if create_backup:
            backup_path = self.create_backup(file_path)
            backup_created = backup_path is not None

        try:
            # Scan file for violations
            scan_result = self.scanner.scan_file(file_path)

            if scan_result.total_violations == 0:
                self.logger.debug(f"No violations found in {file_path}")
                return EnforcementResult(
                    file_path=str(file_path),
                    replacements_made=0,
                    backup_created=backup_created,
                    backup_path=str(backup_path) if backup_path else None,
                    original_hash=original_hash,
                    new_hash=original_hash,
                    enforcement_timestamp=start_time.isoformat(),
                )

            # Read file content
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            original_content = content
            replacements_made = 0

            # Apply replacements for each violation
            for violation in scan_result.violations:
                term_id = violation["term_id"]
                pattern = violation["pattern"]

                if term_id in self.scanner.forbidden_terms:
                    replacement = self.scanner.forbidden_terms[term_id].get(
                        "replacement", "[CONTENT_REMOVED]"
                    )

                    # Apply replacement
                    new_content, count = re.subn(
                        pattern,
                        replacement,
                        content,
                        flags=re.IGNORECASE | re.MULTILINE,
                    )
                    if count > 0:
                        content = new_content
                        replacements_made += count
                        self.logger.debug(
                            f"Replaced {count} instances of pattern '{pattern}' in {file_path}"
                        )

            # Write modified content back to file
            if replacements_made > 0:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.logger.info(
                    f"Enforced {replacements_made} replacements in {file_path}"
                )

            # Calculate new hash
            new_hash = self.scanner._calculate_file_hash(file_path)

            # Create enforcement result
            result = EnforcementResult(
                file_path=str(file_path),
                replacements_made=replacements_made,
                backup_created=backup_created,
                backup_path=str(backup_path) if backup_path else None,
                original_hash=original_hash,
                new_hash=new_hash,
                enforcement_timestamp=start_time.isoformat(),
            )

            # Store enforcement history
            self._store_enforcement_result(result)

            return result

        except Exception as e:
            self.logger.error(f"Error enforcing file {file_path}: {e}")

            # Restore from backup if enforcement failed
            if backup_path and backup_path.exists():
                try:
                    shutil.copy2(backup_path, file_path)
                    self.logger.info(
                        f"Restored {file_path} from backup due to enforcement error"
                    )
                except Exception as restore_error:
                    self.logger.error(f"Error restoring from backup: {restore_error}")

            return EnforcementResult(
                file_path=str(file_path),
                replacements_made=0,
                backup_created=backup_created,
                backup_path=str(backup_path) if backup_path else None,
                original_hash=original_hash,
                new_hash=original_hash,
                enforcement_timestamp=start_time.isoformat(),
            )

    def _store_enforcement_result(self, result: EnforcementResult):
        """Store enforcement result in database."""
        try:
            with sqlite3.connect(self.scanner.scan_results_db) as conn:
                conn.execute(
                    """
                    INSERT INTO enforcement_history 
                    (file_path, replacements_made, backup_path, original_hash, new_hash, enforcer_version)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        result.file_path,
                        result.replacements_made,
                        result.backup_path,
                        result.original_hash,
                        result.new_hash,
                        "1.0.0",
                    ),
                )
                conn.commit()
        except Exception as e:
            self.logger.error(f"Error storing enforcement result: {e}")

    def enforce_directory(
        self,
        directory: Path,
        recursive: bool = True,
        file_patterns: Optional[List[str]] = None,
        create_backups: bool = True,
    ) -> List[EnforcementResult]:
        """Enforce Rule-1 compliance on a directory."""
        results = []

        if not directory.exists() or not directory.is_dir():
            self.logger.error(f"Directory not found: {directory}")
            return results

        self.logger.info(
            f"Starting directory enforcement: {directory} (recursive={recursive})"
        )

        try:
            if recursive:
                files = directory.rglob("*")
            else:
                files = directory.glob("*")

            for file_path in files:
                if file_path.is_file():
                    # Apply file pattern filters if specified
                    if file_patterns:
                        if not any(
                            file_path.match(pattern) for pattern in file_patterns
                        ):
                            continue

                    result = self.enforce_file(file_path, create_backup=create_backups)
                    results.append(result)

        except Exception as e:
            self.logger.error(f"Error enforcing directory {directory}: {e}")

        total_replacements = sum(r.replacements_made for r in results)
        self.logger.info(
            f"Directory enforcement completed: {len(results)} files, {total_replacements} replacements"
        )

        return results

    def rollback_file(
        self, file_path: Path, backup_path: Optional[Path] = None
    ) -> bool:
        """Rollback a file to its backup version."""
        try:
            if backup_path is None:
                # Find the most recent backup
                backups = list(
                    self.scanner.backup_dir.glob(
                        f"{file_path.stem}_*{file_path.suffix}.backup"
                    )
                )
                if not backups:
                    self.logger.error(f"No backup found for {file_path}")
                    return False

                # Sort by modification time and get the most recent
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)

            if not backup_path.exists():
                self.logger.error(f"Backup file not found: {backup_path}")
                return False

            # Restore from backup
            shutil.copy2(backup_path, file_path)
            self.logger.info(f"Rolled back {file_path} from {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error rolling back {file_path}: {e}")
            return False

    def get_enforcement_history(
        self, file_path: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get enforcement history from database."""
        try:
            with sqlite3.connect(self.scanner.scan_results_db) as conn:
                conn.row_factory = sqlite3.Row

                if file_path:
                    cursor = conn.execute(
                        """
                        SELECT * FROM enforcement_history 
                        WHERE file_path = ? 
                        ORDER BY enforcement_timestamp DESC 
                        LIMIT ?
                    """,
                        (file_path, limit),
                    )
                else:
                    cursor = conn.execute(
                        """
                        SELECT * FROM enforcement_history 
                        ORDER BY enforcement_timestamp DESC 
                        LIMIT ?
                    """,
                        (limit,),
                    )

                return [dict(row) for row in cursor.fetchall()]

        except Exception as e:
            self.logger.error(f"Error retrieving enforcement history: {e}")
            return []


if __name__ == "__main__":
    # Test the Rule-1 scanner and enforcer
    import tempfile

    # Create test content with violations
    test_content = """
    This is a test file with some problematic content.
    
    Here's some hate speech that should be detected.
    This contains fake news and misinformation.
    
    Contact us at test@example.com or call 123-45-6789.
    Credit card: 1234 5678 9012 3456
    
    Click here to buy now! Limited time offer!
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_file = temp_path / "test.txt"

        # Write test content
        with open(test_file, "w") as f:
            f.write(test_content)

        # Initialize scanner and enforcer
        scanner = Rule1DeepScanner(
            forbidden_terms_db=str(temp_path / "forbidden_terms.json"),
            scan_results_db=str(temp_path / "scan_results.sqlite"),
            backup_dir=str(temp_path / "backups"),
        )

        enforcer = Rule1Enforcer(scanner)

        # Scan the test file
        print("\n=== SCANNING TEST FILE ===")
        scan_result = scanner.scan_file(test_file)
        print(f"Found {scan_result.total_violations} violations:")
        for violation in scan_result.violations:
            print(
                f"  - {violation['category']}: {violation['match']} (line {violation['line_number']})"
            )

        # Enforce compliance
        print("\n=== ENFORCING COMPLIANCE ===")
        enforcement_result = enforcer.enforce_file(test_file)
        print(f"Made {enforcement_result.replacements_made} replacements")
        print(f"Backup created: {enforcement_result.backup_created}")

        # Show modified content
        print("\n=== MODIFIED CONTENT ===")
        with open(test_file, "r") as f:
            modified_content = f.read()
        print(modified_content)

        # Test rollback
        print("\n=== TESTING ROLLBACK ===")
        rollback_success = enforcer.rollback_file(test_file)
        print(f"Rollback successful: {rollback_success}")

        if rollback_success:
            with open(test_file, "r") as f:
                restored_content = f.read()
            print("Content restored to original")

    print("\nRule-1 scanner and enforcer test completed.")
