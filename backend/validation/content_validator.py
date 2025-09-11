#!/usr/bin/env python3
"""
Content Validation and Quality Assurance System
Implements automated content validation for go-live compliance
"""

import asyncio
import base64
import hashlib
import html
import io
import json
import logging
import mimetypes
import os
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

import aiohttp
import bleach
from audit_logger import AuditLevel, audit_logger
from PIL import Image
from timeout_manager import TimeoutType, timeout_manager


class ValidationLevel(Enum):
    """Content validation levels"""

    BASIC = "basic"  # Basic format and size checks
    STANDARD = "standard"  # + content filtering and sanitization
    STRICT = "strict"  # + advanced security checks
    PARANOID = "paranoid"  # + AI-powered content analysis


class ContentType(Enum):
    """Types of content to validate"""

    TEXT = "text"
    HTML = "html"
    JSON = "json"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    FILE = "file"
    URL = "url"
    EMAIL = "email"
    PHONE = "phone"
    API_RESPONSE = "api_response"
    USER_INPUT = "user_input"


class ValidationResult(Enum):
    """Validation result status"""

    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    BLOCKED = "blocked"


class ThreatLevel(Enum):
    """Security threat levels"""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ValidationRule:
    """Content validation rule"""

    rule_id: str
    name: str
    description: str
    content_types: List[ContentType]
    validation_level: ValidationLevel
    enabled: bool
    priority: int
    action: str  # "allow", "sanitize", "block", "flag"


@dataclass
class ContentValidationResult:
    """Result of content validation"""

    content_id: str
    content_type: ContentType
    validation_level: ValidationLevel
    result: ValidationResult
    threat_level: ThreatLevel
    score: float  # 0-100, higher is safer
    issues: List[str]
    sanitized_content: Optional[str]
    metadata: Dict[str, Any]
    processing_time_ms: float
    timestamp: str
    rules_applied: List[str]


@dataclass
class SecurityScanResult:
    """Result of security scanning"""

    scan_id: str
    content_hash: str
    threats_detected: List[str]
    malware_score: float
    phishing_score: float
    spam_score: float
    adult_content_score: float
    violence_score: float
    hate_speech_score: float
    timestamp: str


class ContentValidator:
    """Comprehensive content validation and quality assurance system"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)

        self.validation_rules = {}
        self.validation_history = []
        self.blocked_patterns = set()
        self.allowed_domains = set()
        self.content_cache = {}

        # Setup logging
        self.logger = logging.getLogger("content_validator")
        self.logger.setLevel(logging.INFO)

        # Initialize validation rules
        self._initialize_validation_rules()

        # Load security patterns
        self._load_security_patterns()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default validation configuration"""
        return {
            "default_validation_level": ValidationLevel.STANDARD,
            "max_content_size": 10 * 1024 * 1024,  # 10MB
            "max_text_length": 100000,  # 100k characters
            "max_url_length": 2048,
            "allowed_image_formats": ["JPEG", "PNG", "GIF", "WebP"],
            "max_image_size": 5 * 1024 * 1024,  # 5MB
            "max_image_dimensions": (4096, 4096),
            "allowed_video_formats": ["mp4", "webm", "avi", "mov"],
            "max_video_size": 100 * 1024 * 1024,  # 100MB
            "allowed_audio_formats": ["mp3", "wav", "ogg", "aac"],
            "max_audio_size": 50 * 1024 * 1024,  # 50MB
            "html_allowed_tags": [
                "p",
                "br",
                "strong",
                "em",
                "u",
                "ol",
                "ul",
                "li",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "blockquote",
                "a",
                "img",
                "code",
                "pre",
            ],
            "html_allowed_attributes": {
                "a": ["href", "title"],
                "img": ["src", "alt", "width", "height"],
                "*": ["class", "id"],
            },
            "blocked_file_extensions": [
                "exe",
                "bat",
                "cmd",
                "com",
                "pif",
                "scr",
                "vbs",
                "js",
                "jar",
                "app",
                "deb",
                "pkg",
                "dmg",
            ],
            "suspicious_patterns": [
                r"<script[^>]*>.*?</script>",
                r"javascript:",
                r"vbscript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"onclick\s*=",
                r"eval\s*\(",
                r"document\.cookie",
                r"window\.location",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
            ],
            "profanity_filter_enabled": True,
            "spam_detection_enabled": True,
            "malware_scanning_enabled": True,
            "ai_content_analysis_enabled": False,  # Requires external AI service
            "cache_validation_results": True,
            "cache_ttl_seconds": 3600,  # 1 hour
            "rate_limit_per_minute": 1000,
            "quarantine_suspicious_content": True,
            "auto_sanitize_html": True,
            "strict_url_validation": True,
            "check_url_reputation": True,
            "validate_ssl_certificates": True,
        }

    def _initialize_validation_rules(self):
        """Initialize default validation rules"""

        # Text content rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="text_length_check",
                name="Text Length Validation",
                description="Validate text content length limits",
                content_types=[ContentType.TEXT, ContentType.USER_INPUT],
                validation_level=ValidationLevel.BASIC,
                enabled=True,
                priority=1,
                action="block",
            )
        )

        # HTML sanitization rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="html_sanitization",
                name="HTML Content Sanitization",
                description="Sanitize HTML content and remove dangerous elements",
                content_types=[ContentType.HTML],
                validation_level=ValidationLevel.STANDARD,
                enabled=True,
                priority=2,
                action="sanitize",
            )
        )

        # XSS protection rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="xss_protection",
                name="Cross-Site Scripting Protection",
                description="Detect and block XSS attempts",
                content_types=[
                    ContentType.HTML,
                    ContentType.TEXT,
                    ContentType.USER_INPUT,
                ],
                validation_level=ValidationLevel.STANDARD,
                enabled=True,
                priority=3,
                action="block",
            )
        )

        # File type validation
        self.register_validation_rule(
            ValidationRule(
                rule_id="file_type_validation",
                name="File Type Validation",
                description="Validate file types and extensions",
                content_types=[
                    ContentType.FILE,
                    ContentType.IMAGE,
                    ContentType.VIDEO,
                    ContentType.AUDIO,
                ],
                validation_level=ValidationLevel.BASIC,
                enabled=True,
                priority=1,
                action="block",
            )
        )

        # URL validation rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="url_validation",
                name="URL Validation and Safety Check",
                description="Validate URLs and check for malicious domains",
                content_types=[ContentType.URL],
                validation_level=ValidationLevel.STANDARD,
                enabled=True,
                priority=2,
                action="block",
            )
        )

        # JSON validation rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="json_validation",
                name="JSON Structure Validation",
                description="Validate JSON structure and content",
                content_types=[ContentType.JSON, ContentType.API_RESPONSE],
                validation_level=ValidationLevel.BASIC,
                enabled=True,
                priority=1,
                action="block",
            )
        )

        # Content filtering rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="content_filtering",
                name="Content Filtering",
                description="Filter inappropriate content including profanity and spam",
                content_types=[
                    ContentType.TEXT,
                    ContentType.HTML,
                    ContentType.USER_INPUT,
                ],
                validation_level=ValidationLevel.STANDARD,
                enabled=True,
                priority=2,
                action="sanitize",
            )
        )

        # Malware detection rules
        self.register_validation_rule(
            ValidationRule(
                rule_id="malware_detection",
                name="Malware Detection",
                description="Scan content for malware and suspicious patterns",
                content_types=[
                    ContentType.FILE,
                    ContentType.IMAGE,
                    ContentType.VIDEO,
                    ContentType.AUDIO,
                ],
                validation_level=ValidationLevel.STRICT,
                enabled=True,
                priority=3,
                action="block",
            )
        )

    def _load_security_patterns(self):
        """Load security patterns and blocked content"""

        # Common XSS patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"on\w+\s*=",
            r"eval\s*\(",
            r"expression\s*\(",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
            r"<link[^>]*>",
            r"<meta[^>]*>",
            r"<style[^>]*>.*?</style>",
        ]

        # SQL injection patterns
        self.sql_injection_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bSELECT\b.*\bFROM\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\'\s*(OR|AND)\s*\')",
            r"(\-\-)",
            r"(/\*.*\*/)",
            r"(\bEXEC\b)",
            r"(\bSP_\w+)",
        ]

        # Command injection patterns
        self.command_injection_patterns = [
            r"(\||&|;|`|\$\(|\${)",
            r"(\bcat\b|\bls\b|\bpwd\b|\bwhoami\b)",
            r"(\brm\b|\bmv\b|\bcp\b|\bchmod\b)",
            r"(\bwget\b|\bcurl\b|\bnc\b|\btelnet\b)",
            r"(\becho\b.*\>)",
            r"(\beval\b|\bexec\b|\bsystem\b)",
        ]

        # Malicious file signatures (simplified)
        self.malicious_signatures = {
            "PE_HEADER": b"\x4d\x5a",  # Windows PE header
            "ELF_HEADER": b"\x7f\x45\x4c\x46",  # Linux ELF header
            "MACH_O_HEADER": b"\xfe\xed\xfa\xce",  # macOS Mach-O header
            "ZIP_BOMB": b"\x50\x4b\x03\x04",  # ZIP header (needs additional checks)
        }

        # Common profanity words (simplified list)
        self.profanity_words = {
            "damn",
            "hell",
            "crap",
            "shit",
            "fuck",
            "bitch",
            "ass",
            "bastard",
            "piss",
            "whore",
            "slut",
            "nigger",
            "faggot",
        }

        # Spam indicators
        self.spam_patterns = [
            r"\b(viagra|cialis|pharmacy)\b",
            r"\b(casino|poker|gambling)\b",
            r"\b(lottery|winner|prize)\b",
            r"\b(click here|act now|limited time)\b",
            r"\$\d+.*\b(million|thousand)\b",
            r"\b(free money|easy money)\b",
            r"\b(work from home|make money)\b",
        ]

    def register_validation_rule(self, rule: ValidationRule):
        """Register a validation rule"""
        self.validation_rules[rule.rule_id] = rule
        self.logger.info(f"Registered validation rule: {rule.rule_id}")

    def _generate_content_id(self, content: Union[str, bytes]) -> str:
        """Generate unique content ID based on hash"""
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        return hashlib.sha256(content_bytes).hexdigest()[:16]

    async def validate_content(
        self,
        content: Union[str, bytes],
        content_type: ContentType,
        validation_level: Optional[ValidationLevel] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ContentValidationResult:
        """Validate content according to rules and security policies"""

        start_time = time.time()
        content_id = self._generate_content_id(content)
        validation_level = validation_level or self.config["default_validation_level"]
        metadata = metadata or {}

        # Check cache first
        if self.config["cache_validation_results"]:
            cached_result = self._get_cached_result(content_id, validation_level)
            if cached_result:
                return cached_result

        result = ContentValidationResult(
            content_id=content_id,
            content_type=content_type,
            validation_level=validation_level,
            result=ValidationResult.VALID,
            threat_level=ThreatLevel.NONE,
            score=100.0,
            issues=[],
            sanitized_content=None,
            metadata=metadata,
            processing_time_ms=0,
            timestamp=datetime.utcnow().isoformat(),
            rules_applied=[],
        )

        try:
            # Apply validation rules
            applicable_rules = [
                rule
                for rule in self.validation_rules.values()
                if (
                    rule.enabled
                    and content_type in rule.content_types
                    and rule.validation_level.value <= validation_level.value
                )
            ]

            # Sort rules by priority
            applicable_rules.sort(key=lambda r: r.priority)

            for rule in applicable_rules:
                rule_result = await self._apply_validation_rule(
                    rule, content, content_type, metadata
                )
                result.rules_applied.append(rule.rule_id)

                if rule_result["issues"]:
                    result.issues.extend(rule_result["issues"])
                    result.score = min(result.score, rule_result["score"])

                    if rule_result["threat_level"].value > result.threat_level.value:
                        result.threat_level = rule_result["threat_level"]

                if rule_result["sanitized_content"] is not None:
                    result.sanitized_content = rule_result["sanitized_content"]
                    content = rule_result[
                        "sanitized_content"
                    ]  # Use sanitized content for next rules

                # If rule blocks content, stop processing
                if rule.action == "block" and rule_result["issues"]:
                    result.result = ValidationResult.BLOCKED
                    break

            # Determine final result
            if result.result != ValidationResult.BLOCKED:
                if result.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
                    result.result = ValidationResult.INVALID
                elif result.threat_level == ThreatLevel.MEDIUM or result.score < 70:
                    result.result = ValidationResult.WARNING
                else:
                    result.result = ValidationResult.VALID

            # Calculate processing time
            result.processing_time_ms = (time.time() - start_time) * 1000

            # Cache result
            if self.config["cache_validation_results"]:
                self._cache_result(result)

            # Log validation
            audit_logger.log_data_access(
                data_type=content_type.value,
                operation="validate",
                additional_data={
                    "content_id": content_id,
                    "validation_level": validation_level.value,
                    "result": result.result.value,
                    "threat_level": result.threat_level.value,
                    "score": result.score,
                    "issues_count": len(result.issues),
                    "processing_time_ms": result.processing_time_ms,
                },
            )

            # Store in history
            self.validation_history.append(result)

            # Cleanup old history
            if len(self.validation_history) > 10000:
                self.validation_history = self.validation_history[-5000:]

            return result

        except Exception as e:
            self.logger.error(f"Error validating content: {str(e)}")

            result.result = ValidationResult.INVALID
            result.threat_level = ThreatLevel.UNKNOWN
            result.score = 0.0
            result.issues = [f"Validation error: {str(e)}"]
            result.processing_time_ms = (time.time() - start_time) * 1000

            return result

    async def _apply_validation_rule(
        self,
        rule: ValidationRule,
        content: Union[str, bytes],
        content_type: ContentType,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply a specific validation rule"""

        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        try:
            if rule.rule_id == "text_length_check":
                result = await self._validate_text_length(content, metadata)

            elif rule.rule_id == "html_sanitization":
                result = await self._sanitize_html_content(content)

            elif rule.rule_id == "xss_protection":
                result = await self._check_xss_patterns(content)

            elif rule.rule_id == "file_type_validation":
                result = await self._validate_file_type(content, metadata)

            elif rule.rule_id == "url_validation":
                result = await self._validate_url(content)

            elif rule.rule_id == "json_validation":
                result = await self._validate_json(content)

            elif rule.rule_id == "content_filtering":
                result = await self._filter_content(content)

            elif rule.rule_id == "malware_detection":
                result = await self._scan_for_malware(content, metadata)

        except Exception as e:
            result["issues"].append(f"Rule {rule.rule_id} failed: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.UNKNOWN

        return result

    async def _validate_text_length(
        self, content: Union[str, bytes], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate text content length"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = content

        if len(content_str) > self.config["max_text_length"]:
            result["issues"].append(
                f"Text too long: {len(content_str)} > {self.config['max_text_length']}"
            )
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.LOW

        return result

    async def _sanitize_html_content(
        self, content: Union[str, bytes]
    ) -> Dict[str, Any]:
        """Sanitize HTML content"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = content

        try:
            # Use bleach to sanitize HTML
            sanitized = bleach.clean(
                content_str,
                tags=self.config["html_allowed_tags"],
                attributes=self.config["html_allowed_attributes"],
                strip=True,
            )

            if sanitized != content_str:
                result["sanitized_content"] = sanitized
                result["issues"].append("HTML content was sanitized")
                result["score"] = 80.0
                result["threat_level"] = ThreatLevel.LOW

        except Exception as e:
            result["issues"].append(f"HTML sanitization failed: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.MEDIUM

        return result

    async def _check_xss_patterns(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Check for XSS attack patterns"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = content

        content_lower = content_str.lower()

        for pattern in self.xss_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE | re.DOTALL):
                result["issues"].append(f"XSS pattern detected: {pattern}")
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.HIGH

        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                result["issues"].append(f"SQL injection pattern detected: {pattern}")
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.HIGH

        # Check for command injection patterns
        for pattern in self.command_injection_patterns:
            if re.search(pattern, content_str, re.IGNORECASE):
                result["issues"].append(
                    f"Command injection pattern detected: {pattern}"
                )
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.HIGH

        return result

    async def _validate_file_type(
        self, content: Union[str, bytes], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate file type and content"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        filename = metadata.get("filename", "")
        if not filename:
            result["issues"].append("No filename provided")
            result["score"] = 50.0
            result["threat_level"] = ThreatLevel.LOW
            return result

        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip(".")
        if file_ext in self.config["blocked_file_extensions"]:
            result["issues"].append(f"Blocked file extension: {file_ext}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.HIGH
            return result

        # Check file size
        if isinstance(content, str):
            content_size = len(content.encode("utf-8"))
        else:
            content_size = len(content)

        if content_size > self.config["max_content_size"]:
            result["issues"].append(
                f"File too large: {content_size} > {self.config['max_content_size']}"
            )
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.MEDIUM

        # Validate MIME type
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            metadata["mime_type"] = mime_type

            # Additional validation for images
            if mime_type.startswith("image/"):
                image_result = await self._validate_image_content(content, metadata)
                result["issues"].extend(image_result["issues"])
                result["score"] = min(result["score"], image_result["score"])
                if image_result["threat_level"].value > result["threat_level"].value:
                    result["threat_level"] = image_result["threat_level"]

        return result

    async def _validate_image_content(
        self, content: Union[str, bytes], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate image content"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        try:
            if isinstance(content, str):
                # Assume base64 encoded
                image_data = base64.b64decode(content)
            else:
                image_data = content

            # Check image size
            if len(image_data) > self.config["max_image_size"]:
                result["issues"].append(
                    f"Image too large: {len(image_data)} > {self.config['max_image_size']}"
                )
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.MEDIUM
                return result

            # Validate image format
            try:
                with Image.open(io.BytesIO(image_data)) as img:
                    if img.format not in self.config["allowed_image_formats"]:
                        result["issues"].append(
                            f"Unsupported image format: {img.format}"
                        )
                        result["score"] = 0.0
                        result["threat_level"] = ThreatLevel.MEDIUM

                    # Check image dimensions
                    width, height = img.size
                    max_width, max_height = self.config["max_image_dimensions"]

                    if width > max_width or height > max_height:
                        result["issues"].append(
                            f"Image dimensions too large: {width}x{height} > {max_width}x{max_height}"
                        )
                        result["score"] = 50.0
                        result["threat_level"] = ThreatLevel.LOW

                    # Store image metadata
                    metadata.update(
                        {
                            "image_format": img.format,
                            "image_size": (width, height),
                            "image_mode": img.mode,
                        }
                    )

            except Exception as e:
                result["issues"].append(f"Invalid image data: {str(e)}")
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.MEDIUM

        except Exception as e:
            result["issues"].append(f"Image validation failed: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.UNKNOWN

        return result

    async def _validate_url(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Validate URL content"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            url = content.decode("utf-8", errors="ignore")
        else:
            url = content

        # Basic URL format validation
        try:
            parsed = urlparse(url)

            if not parsed.scheme or not parsed.netloc:
                result["issues"].append("Invalid URL format")
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.LOW
                return result

            # Check URL length
            if len(url) > self.config["max_url_length"]:
                result["issues"].append(
                    f"URL too long: {len(url)} > {self.config['max_url_length']}"
                )
                result["score"] = 0.0
                result["threat_level"] = ThreatLevel.LOW

            # Check for suspicious schemes
            if parsed.scheme not in ["http", "https", "ftp", "ftps"]:
                result["issues"].append(f"Suspicious URL scheme: {parsed.scheme}")
                result["score"] = 30.0
                result["threat_level"] = ThreatLevel.MEDIUM

            # Check for suspicious patterns in URL
            suspicious_patterns = [
                r"\b(phishing|malware|virus)\b",
                r"\b(bit\.ly|tinyurl|t\.co)\b",  # URL shorteners (can be suspicious)
                r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}",  # IP addresses
                r"[a-zA-Z0-9]+-[a-zA-Z0-9]+-[a-zA-Z0-9]+\.",  # Suspicious domain patterns
            ]

            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    result["issues"].append(f"Suspicious URL pattern: {pattern}")
                    result["score"] = min(result["score"], 40.0)
                    result["threat_level"] = ThreatLevel.MEDIUM

            # Additional checks for HTTPS requirement
            if self.config["strict_url_validation"] and parsed.scheme != "https":
                result["issues"].append("Non-HTTPS URL detected")
                result["score"] = min(result["score"], 70.0)
                result["threat_level"] = ThreatLevel.LOW

        except Exception as e:
            result["issues"].append(f"URL validation failed: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.UNKNOWN

        return result

    async def _validate_json(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Validate JSON content"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            json_str = content.decode("utf-8", errors="ignore")
        else:
            json_str = content

        try:
            # Parse JSON
            parsed_json = json.loads(json_str)

            # Check for suspicious keys or values
            suspicious_keys = [
                "__proto__",
                "constructor",
                "prototype",
                "eval",
                "function",
            ]

            def check_json_recursive(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if key in suspicious_keys:
                            result["issues"].append(
                                f"Suspicious JSON key: {path}.{key}"
                            )
                            result["score"] = min(result["score"], 30.0)
                            result["threat_level"] = ThreatLevel.MEDIUM

                        check_json_recursive(value, f"{path}.{key}")

                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_json_recursive(item, f"{path}[{i}]")

                elif isinstance(obj, str):
                    # Check for suspicious string content
                    if any(
                        pattern in obj.lower()
                        for pattern in ["<script", "javascript:", "eval("]
                    ):
                        result["issues"].append(
                            f"Suspicious content in JSON string: {path}"
                        )
                        result["score"] = min(result["score"], 40.0)
                        result["threat_level"] = ThreatLevel.MEDIUM

            check_json_recursive(parsed_json)

        except json.JSONDecodeError as e:
            result["issues"].append(f"Invalid JSON format: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.LOW

        except Exception as e:
            result["issues"].append(f"JSON validation failed: {str(e)}")
            result["score"] = 0.0
            result["threat_level"] = ThreatLevel.UNKNOWN

        return result

    async def _filter_content(self, content: Union[str, bytes]) -> Dict[str, Any]:
        """Filter content for profanity, spam, and inappropriate material"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if isinstance(content, bytes):
            content_str = content.decode("utf-8", errors="ignore")
        else:
            content_str = content

        content_lower = content_str.lower()
        sanitized_content = content_str

        # Profanity filtering
        if self.config["profanity_filter_enabled"]:
            profanity_count = 0
            for word in self.profanity_words:
                if word in content_lower:
                    profanity_count += 1
                    sanitized_content = re.sub(
                        r"\b" + re.escape(word) + r"\b",
                        "*" * len(word),
                        sanitized_content,
                        flags=re.IGNORECASE,
                    )

            if profanity_count > 0:
                result["issues"].append(
                    f"Profanity detected: {profanity_count} instances"
                )
                result["sanitized_content"] = sanitized_content
                result["score"] = max(20.0, 100.0 - (profanity_count * 20))
                result["threat_level"] = ThreatLevel.LOW

        # Spam detection
        if self.config["spam_detection_enabled"]:
            spam_score = 0
            for pattern in self.spam_patterns:
                matches = len(re.findall(pattern, content_lower, re.IGNORECASE))
                spam_score += matches * 10

            if spam_score > 30:
                result["issues"].append(f"Spam content detected (score: {spam_score})")
                result["score"] = min(result["score"], max(10.0, 100.0 - spam_score))
                result["threat_level"] = ThreatLevel.MEDIUM

        return result

    async def _scan_for_malware(
        self, content: Union[str, bytes], metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Scan content for malware signatures"""
        result = {
            "issues": [],
            "score": 100.0,
            "threat_level": ThreatLevel.NONE,
            "sanitized_content": None,
        }

        if not self.config["malware_scanning_enabled"]:
            return result

        try:
            if isinstance(content, str):
                content_bytes = content.encode("utf-8")
            else:
                content_bytes = content

            # Check for known malicious signatures
            for sig_name, signature in self.malicious_signatures.items():
                if signature in content_bytes:
                    result["issues"].append(f"Malicious signature detected: {sig_name}")
                    result["score"] = 0.0
                    result["threat_level"] = ThreatLevel.CRITICAL

            # Check for suspicious file headers
            if len(content_bytes) >= 4:
                header = content_bytes[:4]

                # Check for executable headers
                if header in [b"\x4d\x5a", b"\x7f\x45\x4c\x46", b"\xfe\xed\xfa\xce"]:
                    result["issues"].append("Executable file header detected")
                    result["score"] = 0.0
                    result["threat_level"] = ThreatLevel.HIGH

        except Exception as e:
            result["issues"].append(f"Malware scanning failed: {str(e)}")
            result["score"] = 50.0
            result["threat_level"] = ThreatLevel.UNKNOWN

        return result

    def _get_cached_result(
        self, content_id: str, validation_level: ValidationLevel
    ) -> Optional[ContentValidationResult]:
        """Get cached validation result"""
        cache_key = f"{content_id}_{validation_level.value}"

        if cache_key in self.content_cache:
            cached_entry = self.content_cache[cache_key]

            # Check if cache entry is still valid
            cache_time = datetime.fromisoformat(cached_entry["timestamp"])
            if datetime.utcnow() - cache_time < timedelta(
                seconds=self.config["cache_ttl_seconds"]
            ):
                return cached_entry["result"]
            else:
                # Remove expired entry
                del self.content_cache[cache_key]

        return None

    def _cache_result(self, result: ContentValidationResult):
        """Cache validation result"""
        cache_key = f"{result.content_id}_{result.validation_level.value}"

        self.content_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Cleanup old cache entries
        if len(self.content_cache) > 1000:
            # Remove oldest 200 entries
            sorted_entries = sorted(
                self.content_cache.items(), key=lambda x: x[1]["timestamp"]
            )

            for key, _ in sorted_entries[:200]:
                del self.content_cache[key]

    async def validate_api_response(
        self, response_data: Dict[str, Any], endpoint: str
    ) -> ContentValidationResult:
        """Validate API response data"""
        response_json = json.dumps(response_data, sort_keys=True)

        return await self.validate_content(
            content=response_json,
            content_type=ContentType.API_RESPONSE,
            validation_level=ValidationLevel.STANDARD,
            metadata={"endpoint": endpoint, "response_size": len(response_json)},
        )

    async def validate_user_input(
        self, user_input: str, input_type: str = "text"
    ) -> ContentValidationResult:
        """Validate user input"""
        content_type = ContentType.USER_INPUT

        if input_type == "html":
            content_type = ContentType.HTML
        elif input_type == "url":
            content_type = ContentType.URL
        elif input_type == "email":
            content_type = ContentType.EMAIL

        return await self.validate_content(
            content=user_input,
            content_type=content_type,
            validation_level=ValidationLevel.STRICT,
            metadata={"input_type": input_type, "input_length": len(user_input)},
        )

    def get_validation_report(self) -> Dict[str, Any]:
        """Generate validation system report"""

        recent_validations = [
            result
            for result in self.validation_history
            if datetime.fromisoformat(result.timestamp)
            > datetime.utcnow() - timedelta(hours=24)
        ]

        total_validations = len(recent_validations)
        valid_count = sum(
            1 for r in recent_validations if r.result == ValidationResult.VALID
        )
        warning_count = sum(
            1 for r in recent_validations if r.result == ValidationResult.WARNING
        )
        invalid_count = sum(
            1 for r in recent_validations if r.result == ValidationResult.INVALID
        )
        blocked_count = sum(
            1 for r in recent_validations if r.result == ValidationResult.BLOCKED
        )

        avg_processing_time = (
            sum(r.processing_time_ms for r in recent_validations) / total_validations
            if total_validations > 0
            else 0
        )

        threat_distribution = {}
        for threat_level in ThreatLevel:
            threat_distribution[threat_level.value] = sum(
                1 for r in recent_validations if r.threat_level == threat_level
            )

        return {
            "report_id": f"validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_validations_24h": total_validations,
                "valid_count": valid_count,
                "warning_count": warning_count,
                "invalid_count": invalid_count,
                "blocked_count": blocked_count,
                "success_rate": (
                    (valid_count / total_validations * 100)
                    if total_validations > 0
                    else 0
                ),
                "avg_processing_time_ms": avg_processing_time,
            },
            "threat_distribution": threat_distribution,
            "validation_rules": {
                "total_rules": len(self.validation_rules),
                "enabled_rules": sum(
                    1 for r in self.validation_rules.values() if r.enabled
                ),
                "rule_details": {
                    rule_id: {
                        "name": rule.name,
                        "enabled": rule.enabled,
                        "priority": rule.priority,
                        "action": rule.action,
                    }
                    for rule_id, rule in self.validation_rules.items()
                },
            },
            "cache_stats": {
                "cached_results": len(self.content_cache),
                "cache_hit_rate": "N/A",  # Would need to track hits/misses
            },
            "compliance_status": {
                "content_validation_active": True,
                "security_scanning_enabled": self.config["malware_scanning_enabled"],
                "profanity_filtering_enabled": self.config["profanity_filter_enabled"],
                "spam_detection_enabled": self.config["spam_detection_enabled"],
                "html_sanitization_enabled": self.config["auto_sanitize_html"],
            },
        }


# Global content validator instance
content_validator = ContentValidator()


# Convenience functions
async def validate_text_content(
    text: str, strict: bool = False
) -> ContentValidationResult:
    """Validate text content"""
    validation_level = ValidationLevel.STRICT if strict else ValidationLevel.STANDARD
    return await content_validator.validate_content(
        text, ContentType.TEXT, validation_level
    )


async def validate_html_content(html: str) -> ContentValidationResult:
    """Validate and sanitize HTML content"""
    return await content_validator.validate_content(
        html, ContentType.HTML, ValidationLevel.STANDARD
    )


async def validate_user_upload(
    file_content: bytes, filename: str
) -> ContentValidationResult:
    """Validate user file upload"""
    return await content_validator.validate_content(
        file_content, ContentType.FILE, ValidationLevel.STRICT, {"filename": filename}
    )


async def validate_api_data(
    data: Dict[str, Any], endpoint: str
) -> ContentValidationResult:
    """Validate API response data"""
    return await content_validator.validate_api_response(data, endpoint)
