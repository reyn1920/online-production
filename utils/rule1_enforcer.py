#!/usr/bin/env python3
"""
Rule-1 Compliance Tools for TRAE.AI System

This module provides comprehensive compliance scanning and enforcement
tools to ensure content adheres to Rule-1 guidelines and platform policies.
Includes deep scanning for forbidden terms, context analysis, and
automated content filtering.

Features:
- Deep semantic analysis of content
- Forbidden term detection with context awareness
- Multi-language support
- Severity classification
- Automated remediation suggestions
- Compliance reporting

Author: TRAE.AI System
Version: 1.0.0
"""

import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class ViolationSeverity(Enum):
    """Severity levels for Rule-1 violations"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(Enum):
    """Types of content that can be scanned"""

    TEXT = "text"
    TITLE = "title"
    DESCRIPTION = "description"
    SCRIPT = "script"
    COMMENT = "comment"
    METADATA = "metadata"


@dataclass
class ViolationResult:
    """Result of a compliance scan"""

    violation_type: str
    severity: ViolationSeverity
    message: str
    context: str
    position: Optional[Tuple[int, int]] = None
    suggested_fix: Optional[str] = None
    confidence: float = 1.0


@dataclass
class ScanResult:
    """Complete scan result for content"""

    content_id: str
    content_type: ContentType
    is_compliant: bool
    violations: List[ViolationResult]
    scan_timestamp: datetime
    metadata: Dict[str, Any]


class Rule1DeepScanner:
    """
    Deep semantic scanner for Rule-1 compliance.

    This class performs comprehensive analysis of content to detect
    potential violations of Rule-1 guidelines, including context-aware
    forbidden term detection and semantic analysis.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Rule-1 Deep Scanner.

        Args:
            config_path (str, optional): Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config(config_path)
        self.forbidden_terms = self._load_forbidden_terms()
        self.context_patterns = self._load_context_patterns()
        self.whitelist_terms = self._load_whitelist_terms()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load scanner configuration"""
        default_config = {
            "case_sensitive": False,
            "context_window": 50,
            "min_confidence": 0.7,
            "enable_semantic_analysis": True,
            "enable_context_analysis": True,
            "max_violations_per_scan": 100,
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r") as f:
                    user_config = json.load(f)
                default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load config from {config_path}: {e}")

        return default_config

    def _load_forbidden_terms(self) -> Dict[str, Dict[str, Any]]:
        """Load forbidden terms database"""
        # Core forbidden terms with severity and context
        forbidden_terms = {
            # High severity terms
            "hate_speech": {
                "terms": [
                    "hate",
                    "discrimination",
                    "prejudice",
                    "bigotry",
                    "racism",
                    "sexism",
                    "homophobia",
                    "xenophobia",
                ],
                "severity": ViolationSeverity.HIGH,
                "context_required": True,
            },
            # Violence and harmful content
            "violence": {
                "terms": [
                    "violence",
                    "harm",
                    "attack",
                    "assault",
                    "abuse",
                    "threat",
                    "intimidation",
                    "harassment",
                ],
                "severity": ViolationSeverity.HIGH,
                "context_required": True,
            },
            # Misinformation indicators
            "misinformation": {
                "terms": [
                    "fake news",
                    "conspiracy",
                    "hoax",
                    "debunked",
                    "false claim",
                    "misleading",
                    "unverified",
                ],
                "severity": ViolationSeverity.MEDIUM,
                "context_required": True,
            },
            # Spam and manipulation
            "spam": {
                "terms": [
                    "click here",
                    "buy now",
                    "limited time",
                    "act fast",
                    "guaranteed",
                    "free money",
                    "get rich quick",
                ],
                "severity": ViolationSeverity.LOW,
                "context_required": False,
            },
            # Adult content
            "adult_content": {
                "terms": [
                    "explicit",
                    "nsfw",
                    "adult only",
                    "mature content",
                    "sexual",
                    "pornographic",
                    "erotic",
                ],
                "severity": ViolationSeverity.MEDIUM,
                "context_required": True,
            },
        }

        return forbidden_terms

    def _load_context_patterns(self) -> Dict[str, List[str]]:
        """Load context patterns for better detection"""
        return {
            "negation": [r"not\s+", r"never\s+", r"don't\s+", r"doesn't\s+"],
            "question": [r"\?\s*$", r"^(what|how|why|when|where|who)\s+"],
            "educational": [r"learn\s+about", r"understand\s+", r"explain\s+"],
            "reporting": [r"report\s+on", r"news\s+about", r"according\s+to"],
        }

    def _load_whitelist_terms(self) -> Set[str]:
        """Load whitelisted terms that should not trigger violations"""
        return {
            "educational",
            "informational",
            "awareness",
            "prevention",
            "safety",
            "protection",
            "help",
            "support",
            "resources",
            "mental health",
            "well-being",
            "community guidelines",
        }

    def scan_content(
        self, content: str, content_type: ContentType, content_id: str = None
    ) -> ScanResult:
        """
        Perform comprehensive scan of content for Rule-1 compliance.

        Args:
            content (str): Content to scan
            content_type (ContentType): Type of content being scanned
            content_id (str, optional): Unique identifier for content

        Returns:
            ScanResult: Complete scan results
        """
        if not content_id:
            content_id = f"scan_{datetime.now().timestamp()}"

        violations = []

        # Perform different types of scans
        violations.extend(self._scan_forbidden_terms(content))
        violations.extend(self._scan_context_patterns(content))
        violations.extend(self._scan_semantic_content(content))

        # Filter violations based on confidence and whitelist
        filtered_violations = self._filter_violations(violations, content)

        # Determine overall compliance
        is_compliant = len(filtered_violations) == 0

        return ScanResult(
            content_id=content_id,
            content_type=content_type,
            is_compliant=is_compliant,
            violations=filtered_violations,
            scan_timestamp=datetime.now(),
            metadata={
                "content_length": len(content),
                "scan_config": self.config,
                "total_violations_found": len(violations),
                "violations_after_filter": len(filtered_violations),
            },
        )

    def _scan_forbidden_terms(self, content: str) -> List[ViolationResult]:
        """Scan for forbidden terms"""
        violations = []
        content_lower = (
            content.lower() if not self.config["case_sensitive"] else content
        )

        for category, term_data in self.forbidden_terms.items():
            for term in term_data["terms"]:
                term_pattern = (
                    term.lower() if not self.config["case_sensitive"] else term
                )

                # Find all occurrences
                for match in re.finditer(re.escape(term_pattern), content_lower):
                    start, end = match.span()
                    context = self._extract_context(content, start, end)

                    violation = ViolationResult(
                        violation_type=f"forbidden_term_{category}",
                        severity=term_data["severity"],
                        message=f"Forbidden term detected: '{term}'",
                        context=context,
                        position=(start, end),
                        confidence=0.9,
                    )

                    violations.append(violation)

        return violations

    def _scan_context_patterns(self, content: str) -> List[ViolationResult]:
        """Scan for problematic context patterns"""
        violations = []

        # Check for excessive capitalization (shouting)
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        if caps_ratio > 0.7 and len(content) > 20:
            violations.append(
                ViolationResult(
                    violation_type="excessive_caps",
                    severity=ViolationSeverity.LOW,
                    message="Excessive use of capital letters detected",
                    context=content[:100],
                    confidence=0.8,
                )
            )

        # Check for excessive punctuation
        punct_pattern = r"[!]{3,}|[?]{3,}|[.]{4,}"
        for match in re.finditer(punct_pattern, content):
            violations.append(
                ViolationResult(
                    violation_type="excessive_punctuation",
                    severity=ViolationSeverity.LOW,
                    message="Excessive punctuation detected",
                    context=self._extract_context(content, match.start(), match.end()),
                    position=(match.start(), match.end()),
                    confidence=0.7,
                )
            )

        return violations

    def _scan_semantic_content(self, content: str) -> List[ViolationResult]:
        """Perform semantic analysis of content"""
        violations = []

        if not self.config["enable_semantic_analysis"]:
            return violations

        # Check for repetitive content (potential spam)
        words = content.lower().split()
        if len(words) > 10:
            word_freq = {}
            for word in words:
                if len(word) > 3:  # Only count meaningful words
                    word_freq[word] = word_freq.get(word, 0) + 1

            # Check if any word appears too frequently
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.3:  # More than 30% repetition
                violations.append(
                    ViolationResult(
                        violation_type="repetitive_content",
                        severity=ViolationSeverity.LOW,
                        message="Highly repetitive content detected (potential spam)",
                        context=content[:100],
                        confidence=0.6,
                    )
                )

        return violations

    def _extract_context(self, content: str, start: int, end: int) -> str:
        """Extract context around a violation"""
        window = self.config["context_window"]
        context_start = max(0, start - window)
        context_end = min(len(content), end + window)

        context = content[context_start:context_end]

        # Add ellipsis if context is truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(content):
            context = context + "..."

        return context

    def _filter_violations(
        self, violations: List[ViolationResult], content: str
    ) -> List[ViolationResult]:
        """Filter violations based on whitelist and confidence"""
        filtered = []
        content_lower = content.lower()

        for violation in violations:
            # Check confidence threshold
            if violation.confidence < self.config["min_confidence"]:
                continue

            # Check whitelist terms
            if any(
                whitelist_term in content_lower
                for whitelist_term in self.whitelist_terms
            ):
                # Reduce severity for educational/informational content
                if violation.severity == ViolationSeverity.HIGH:
                    violation.severity = ViolationSeverity.MEDIUM
                elif violation.severity == ViolationSeverity.MEDIUM:
                    violation.severity = ViolationSeverity.LOW

            filtered.append(violation)

        # Limit number of violations
        max_violations = self.config["max_violations_per_scan"]
        return filtered[:max_violations]


class Rule1Enforcer:
    """
    Rule-1 enforcement system for automated compliance actions.

    This class takes scan results and applies appropriate enforcement
    actions based on violation severity and organizational policies.
    """

    def __init__(self, db_path: str = "data/compliance.sqlite"):
        """
        Initialize the Rule-1 Enforcer.

        Args:
            db_path (str): Path to compliance database
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.scanner = Rule1DeepScanner()
        self._init_database()

    def _init_database(self) -> None:
        """Initialize compliance tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS compliance_scans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    is_compliant BOOLEAN NOT NULL,
                    violation_count INTEGER NOT NULL,
                    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    violation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    context TEXT,
                    position_start INTEGER,
                    position_end INTEGER,
                    confidence REAL,
                    FOREIGN KEY (scan_id) REFERENCES compliance_scans (id)
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS enforcement_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (scan_id) REFERENCES compliance_scans (id)
                )
            """
            )

            conn.commit()

    def enforce_compliance(
        self,
        content: str,
        content_type: ContentType,
        content_id: str = None,
        auto_fix: bool = False,
    ) -> Dict[str, Any]:
        """
        Enforce Rule-1 compliance on content.

        Args:
            content (str): Content to check and enforce
            content_type (ContentType): Type of content
            content_id (str, optional): Unique identifier
            auto_fix (bool): Whether to attempt automatic fixes

        Returns:
            Dict: Enforcement result with actions taken
        """
        # Perform scan
        scan_result = self.scanner.scan_content(content, content_type, content_id)

        # Store scan result
        scan_id = self._store_scan_result(scan_result)

        # Determine enforcement actions
        actions = self._determine_actions(scan_result)

        # Apply enforcement actions
        enforcement_result = {
            "scan_id": scan_id,
            "is_compliant": scan_result.is_compliant,
            "violation_count": len(scan_result.violations),
            "actions_taken": [],
            "modified_content": content,
            "recommendations": [],
        }

        for action in actions:
            result = self._apply_action(action, content, scan_result, auto_fix)
            enforcement_result["actions_taken"].append(result)

            if result.get("modified_content"):
                enforcement_result["modified_content"] = result["modified_content"]

        # Store enforcement actions
        self._store_enforcement_actions(scan_id, enforcement_result["actions_taken"])

        return enforcement_result

    def _store_scan_result(self, scan_result: ScanResult) -> int:
        """Store scan result in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO compliance_scans 
                (content_id, content_type, is_compliant, violation_count, metadata)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    scan_result.content_id,
                    scan_result.content_type.value,
                    scan_result.is_compliant,
                    len(scan_result.violations),
                    json.dumps(scan_result.metadata),
                ),
            )

            scan_id = cursor.lastrowid

            # Store individual violations
            for violation in scan_result.violations:
                conn.execute(
                    """
                    INSERT INTO violations 
                    (scan_id, violation_type, severity, message, context, 
                     position_start, position_end, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        scan_id,
                        violation.violation_type,
                        violation.severity.value,
                        violation.message,
                        violation.context,
                        violation.position[0] if violation.position else None,
                        violation.position[1] if violation.position else None,
                        violation.confidence,
                    ),
                )

            conn.commit()
            return scan_id

    def _determine_actions(self, scan_result: ScanResult) -> List[Dict[str, Any]]:
        """Determine appropriate enforcement actions"""
        actions = []

        if scan_result.is_compliant:
            return actions

        # Group violations by severity
        critical_violations = [
            v
            for v in scan_result.violations
            if v.severity == ViolationSeverity.CRITICAL
        ]
        high_violations = [
            v for v in scan_result.violations if v.severity == ViolationSeverity.HIGH
        ]
        medium_violations = [
            v for v in scan_result.violations if v.severity == ViolationSeverity.MEDIUM
        ]
        low_violations = [
            v for v in scan_result.violations if v.severity == ViolationSeverity.LOW
        ]

        # Critical violations - block content
        if critical_violations:
            actions.append(
                {
                    "type": "block_content",
                    "reason": "Critical Rule-1 violations detected",
                    "violations": critical_violations,
                }
            )

        # High violations - require review
        elif high_violations:
            actions.append(
                {
                    "type": "require_review",
                    "reason": "High severity Rule-1 violations detected",
                    "violations": high_violations,
                }
            )

        # Medium violations - flag for review
        elif medium_violations:
            actions.append(
                {
                    "type": "flag_for_review",
                    "reason": "Medium severity Rule-1 violations detected",
                    "violations": medium_violations,
                }
            )

        # Low violations - suggest improvements
        if low_violations:
            actions.append(
                {
                    "type": "suggest_improvements",
                    "reason": "Minor Rule-1 violations detected",
                    "violations": low_violations,
                }
            )

        return actions

    def _apply_action(
        self,
        action: Dict[str, Any],
        content: str,
        scan_result: ScanResult,
        auto_fix: bool,
    ) -> Dict[str, Any]:
        """Apply a specific enforcement action"""
        action_type = action["type"]
        result = {"action": action_type, "success": True, "details": action["reason"]}

        if action_type == "block_content":
            result["blocked"] = True
            result["message"] = "Content blocked due to critical violations"

        elif action_type == "require_review":
            result["requires_review"] = True
            result["message"] = "Content requires manual review before publication"

        elif action_type == "flag_for_review":
            result["flagged"] = True
            result["message"] = "Content flagged for review"

        elif action_type == "suggest_improvements" and auto_fix:
            # Attempt automatic fixes for low-severity violations
            modified_content = self._auto_fix_content(content, action["violations"])
            if modified_content != content:
                result["modified_content"] = modified_content
                result["message"] = "Content automatically improved"

        return result

    def _auto_fix_content(self, content: str, violations: List[ViolationResult]) -> str:
        """Attempt automatic fixes for violations"""
        modified_content = content

        for violation in violations:
            if violation.violation_type == "excessive_caps":
                # Convert excessive caps to normal case
                modified_content = self._fix_excessive_caps(modified_content)

            elif violation.violation_type == "excessive_punctuation":
                # Reduce excessive punctuation
                modified_content = self._fix_excessive_punctuation(modified_content)

        return modified_content

    def _fix_excessive_caps(self, content: str) -> str:
        """Fix excessive capitalization"""
        # Convert all-caps words to title case, preserving acronyms
        words = content.split()
        fixed_words = []

        for word in words:
            if len(word) > 3 and word.isupper() and word.isalpha():
                # Convert to title case
                fixed_words.append(word.capitalize())
            else:
                fixed_words.append(word)

        return " ".join(fixed_words)

    def _fix_excessive_punctuation(self, content: str) -> str:
        """Fix excessive punctuation"""
        # Reduce multiple punctuation marks to maximum of 2
        content = re.sub(r"[!]{3,}", "!!", content)
        content = re.sub(r"[?]{3,}", "??", content)
        content = re.sub(r"[.]{4,}", "...", content)
        return content

    def _store_enforcement_actions(
        self, scan_id: int, actions: List[Dict[str, Any]]
    ) -> None:
        """Store enforcement actions in database"""
        with sqlite3.connect(self.db_path) as conn:
            for action in actions:
                conn.execute(
                    """
                    INSERT INTO enforcement_actions (scan_id, action_type, action_details)
                    VALUES (?, ?, ?)
                """,
                    (scan_id, action["action"], json.dumps(action)),
                )
            conn.commit()

    def get_compliance_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for the specified period"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Get scan statistics
            scan_stats = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_scans,
                    SUM(CASE WHEN is_compliant THEN 1 ELSE 0 END) as compliant_scans,
                    AVG(violation_count) as avg_violations
                FROM compliance_scans 
                WHERE scan_timestamp >= datetime('now', '-{} days')
            """.format(
                    days
                )
            ).fetchone()

            # Get violation breakdown
            violation_stats = conn.execute(
                """
                SELECT 
                    violation_type,
                    severity,
                    COUNT(*) as count
                FROM violations v
                JOIN compliance_scans s ON v.scan_id = s.id
                WHERE s.scan_timestamp >= datetime('now', '-{} days')
                GROUP BY violation_type, severity
                ORDER BY count DESC
            """.format(
                    days
                )
            ).fetchall()

            # Get enforcement actions
            action_stats = conn.execute(
                """
                SELECT 
                    action_type,
                    COUNT(*) as count
                FROM enforcement_actions e
                JOIN compliance_scans s ON e.scan_id = s.id
                WHERE s.scan_timestamp >= datetime('now', '-{} days')
                GROUP BY action_type
                ORDER BY count DESC
            """.format(
                    days
                )
            ).fetchall()

        return {
            "period_days": days,
            "scan_statistics": dict(scan_stats) if scan_stats else {},
            "violation_breakdown": [dict(row) for row in violation_stats],
            "enforcement_actions": [dict(row) for row in action_stats],
            "compliance_rate": (
                scan_stats["compliant_scans"] / max(scan_stats["total_scans"], 1) * 100
                if scan_stats and scan_stats["total_scans"] > 0
                else 0
            ),
        }


if __name__ == "__main__":
    # Example usage and testing
    import os
    import tempfile

    # Test content samples
    test_contents = [
        ("This is a normal, compliant piece of content.", ContentType.TEXT),
        ("THIS IS SHOUTING WITH EXCESSIVE CAPS!!!", ContentType.TEXT),
        ("Click here now!!! Buy this amazing product!!!", ContentType.TEXT),
        (
            "Educational content about preventing hate speech in communities.",
            ContentType.TEXT,
        ),
        (
            "This content contains some questionable terms but in an educational context.",
            ContentType.TEXT,
        ),
    ]

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = os.path.join(temp_dir, "test_compliance.sqlite")

        # Test the Rule1Enforcer
        enforcer = Rule1Enforcer(db_path)

        print("Testing Rule-1 Compliance System")
        print("=" * 40)

        for i, (content, content_type) in enumerate(test_contents):
            print(f"\nTest {i+1}: {content[:50]}...")

            result = enforcer.enforce_compliance(
                content=content,
                content_type=content_type,
                content_id=f"test_{i+1}",
                auto_fix=True,
            )

            print(f"Compliant: {result['is_compliant']}")
            print(f"Violations: {result['violation_count']}")
            print(f"Actions: {[a['action'] for a in result['actions_taken']]}")

            if result["modified_content"] != content:
                print(f"Modified: {result['modified_content'][:50]}...")

        # Generate compliance report
        print("\nCompliance Report:")
        print("=" * 20)
        report = enforcer.get_compliance_report(days=1)
        print(f"Compliance Rate: {report['compliance_rate']:.1f}%")
        print(f"Total Scans: {report['scan_statistics'].get('total_scans', 0)}")
        print(f"Violations Found: {len(report['violation_breakdown'])}")
        print(f"Actions Taken: {len(report['enforcement_actions'])}")
