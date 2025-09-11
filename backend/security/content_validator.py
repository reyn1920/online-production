#!/usr/bin/env python3
"""
Production Content Validation System
Implements comprehensive input validation and sanitization for go-live security
"""

import hashlib
import html
import json
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

import bleach
import validators
from bleach.css_sanitizer import CSSSanitizer
from markupsafe import Markup
from pydantic import BaseModel, ValidationError, validator


class ContentValidationError(Exception):
    """Custom exception for content validation failures"""

    pass


class ValidationResult(BaseModel):
    """Result of content validation"""

    is_valid: bool
    sanitized_content: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []
    risk_score: int = 0  # 0-100, higher is more risky
    timestamp: datetime = datetime.utcnow()


class ProductionContentValidator:
    """Comprehensive content validation for production environment"""

    def __init__(self):
        # Allowed HTML tags and attributes for rich content
        self.allowed_tags = [
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
            "code",
            "pre",
            "a",
            "img",
        ]

        self.allowed_attributes = {
            "a": ["href", "title"],
            "img": ["src", "alt", "title", "width", "height"],
            "*": ["class"],
        }

        # CSS sanitizer for safe styling
        self.css_sanitizer = CSSSanitizer(
            allowed_css_properties=[
                "color",
                "background-color",
                "font-size",
                "font-weight",
                "text-align",
                "margin",
                "padding",
                "border",
            ]
        )

        # Dangerous patterns to detect
        self.dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # Script tags
            r"javascript:",  # JavaScript URLs
            r"on\w+\s*=",  # Event handlers
            r"data:text/html",  # Data URLs with HTML
            r"vbscript:",  # VBScript URLs
            r"<iframe[^>]*>.*?</iframe>",  # Iframe tags
            r"<object[^>]*>.*?</object>",  # Object tags
            r"<embed[^>]*>.*?</embed>",  # Embed tags
        ]

        # SQL injection patterns
        self.sql_patterns = [
            r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
            r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",
            r"(script|javascript|vbscript|onload|onerror|onclick)",
        ]

        # Maximum content lengths
        self.max_lengths = {
            "title": 200,
            "description": 1000,
            "content": 50000,
            "comment": 2000,
            "username": 50,
            "email": 254,
            "url": 2048,
        }

    def validate_text_input(
        self, content: str, content_type: str = "general"
    ) -> ValidationResult:
        """Validate and sanitize text input"""
        result = ValidationResult(is_valid=True)

        if not content or not isinstance(content, str):
            result.is_valid = False
            result.errors.append("Content is empty or not a string")
            return result

        # Check length limits
        max_length = self.max_lengths.get(content_type, 10000)
        if len(content) > max_length:
            result.is_valid = False
            result.errors.append(
                f"Content exceeds maximum length of {max_length} characters"
            )
            result.risk_score += 20

        # Check for dangerous patterns
        risk_score = 0
        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result.is_valid = False
                result.errors.append(f"Dangerous pattern detected: {pattern}")
                risk_score += 30

        # Check for SQL injection patterns
        for pattern in self.sql_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                result.warnings.append("Potential SQL injection pattern detected")
                risk_score += 25

        # HTML escape the content
        sanitized = html.escape(content)

        # Additional sanitization for specific content types
        if content_type == "email":
            if not validators.email(content):
                result.is_valid = False
                result.errors.append("Invalid email format")
            else:
                sanitized = content.lower().strip()

        elif content_type == "url":
            if not validators.url(content):
                result.is_valid = False
                result.errors.append("Invalid URL format")
            else:
                parsed = urlparse(content)
                if parsed.scheme not in ["http", "https"]:
                    result.is_valid = False
                    result.errors.append("Only HTTP and HTTPS URLs are allowed")

        result.sanitized_content = sanitized
        result.risk_score = min(risk_score, 100)

        return result

    def validate_html_content(self, content: str) -> ValidationResult:
        """Validate and sanitize HTML content"""
        result = ValidationResult(is_valid=True)

        if not content or not isinstance(content, str):
            result.is_valid = False
            result.errors.append("HTML content is empty or not a string")
            return result

        try:
            # Use bleach to sanitize HTML
            sanitized = bleach.clean(
                content,
                tags=self.allowed_tags,
                attributes=self.allowed_attributes,
                css_sanitizer=self.css_sanitizer,
                strip=True,
            )

            # Check if content was modified (indicates potentially dangerous content)
            if sanitized != content:
                result.warnings.append(
                    "HTML content was sanitized - some elements were removed"
                )
                result.risk_score += 15

            # Additional checks for dangerous patterns
            for pattern in self.dangerous_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result.errors.append(f"Dangerous HTML pattern detected: {pattern}")
                    result.risk_score += 40
                    result.is_valid = False

            result.sanitized_content = sanitized

        except Exception as e:
            result.is_valid = False
            result.errors.append(f"HTML sanitization failed: {str(e)}")
            result.risk_score = 100

        return result

    def validate_json_input(self, content: Union[str, dict]) -> ValidationResult:
        """Validate JSON input"""
        result = ValidationResult(is_valid=True)

        try:
            if isinstance(content, str):
                parsed_json = json.loads(content)
            else:
                parsed_json = content

            # Check for dangerous keys or values
            dangerous_keys = ["__proto__", "constructor", "prototype"]

            def check_dangerous_content(obj, path=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        current_path = f"{path}.{key}" if path else key

                        if key in dangerous_keys:
                            result.errors.append(
                                f"Dangerous key detected: {current_path}"
                            )
                            result.risk_score += 50
                            result.is_valid = False

                        if isinstance(value, str):
                            # Check string values for dangerous patterns
                            for pattern in self.dangerous_patterns:
                                if re.search(pattern, value, re.IGNORECASE):
                                    result.warnings.append(
                                        f"Suspicious pattern in {current_path}"
                                    )
                                    result.risk_score += 20

                        check_dangerous_content(value, current_path)

                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        check_dangerous_content(item, f"{path}[{i}]")

            check_dangerous_content(parsed_json)

            # Serialize back to ensure it's valid JSON
            result.sanitized_content = json.dumps(parsed_json, ensure_ascii=False)

        except json.JSONDecodeError as e:
            result.is_valid = False
            result.errors.append(f"Invalid JSON format: {str(e)}")
            result.risk_score = 80
        except Exception as e:
            result.is_valid = False
            result.errors.append(f"JSON validation failed: {str(e)}")
            result.risk_score = 90

        return result

    def validate_file_upload(
        self, filename: str, content_type: str, file_size: int
    ) -> ValidationResult:
        """Validate file upload parameters"""
        result = ValidationResult(is_valid=True)

        # Allowed file types
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "text/plain",
            "text/csv",
            "application/pdf",
            "application/json",
        }

        # Dangerous file extensions
        dangerous_extensions = {
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".pif",
            ".scr",
            ".js",
            ".jar",
            ".php",
            ".asp",
            ".aspx",
            ".jsp",
        }

        # Check file extension
        file_ext = "." + filename.split(".")[-1].lower() if "." in filename else ""
        if file_ext in dangerous_extensions:
            result.is_valid = False
            result.errors.append(f"Dangerous file extension: {file_ext}")
            result.risk_score += 80

        # Check content type
        if content_type not in allowed_types:
            result.is_valid = False
            result.errors.append(f"File type not allowed: {content_type}")
            result.risk_score += 60

        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if file_size > max_size:
            result.is_valid = False
            result.errors.append(f"File size exceeds limit: {file_size} bytes")
            result.risk_score += 40

        # Generate safe filename
        safe_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
        result.sanitized_content = safe_filename

        return result

    def create_content_hash(self, content: str) -> str:
        """Create a hash of content for integrity checking"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def validate_batch_content(
        self, content_items: List[Dict[str, Any]]
    ) -> Dict[str, ValidationResult]:
        """Validate multiple content items in batch"""
        results = {}

        for i, item in enumerate(content_items):
            item_id = item.get("id", f"item_{i}")
            content_type = item.get("type", "general")
            content = item.get("content", "")

            if content_type == "html":
                results[item_id] = self.validate_html_content(content)
            elif content_type == "json":
                results[item_id] = self.validate_json_input(content)
            else:
                results[item_id] = self.validate_text_input(content, content_type)

        return results


# Global validator instance
content_validator = ProductionContentValidator()


# Convenience functions for common validation tasks
def validate_user_input(
    content: str, content_type: str = "general"
) -> ValidationResult:
    """Quick validation for user input"""
    return content_validator.validate_text_input(content, content_type)


def validate_html(content: str) -> ValidationResult:
    """Quick HTML validation"""
    return content_validator.validate_html_content(content)


def validate_json(content: Union[str, dict]) -> ValidationResult:
    """Quick JSON validation"""
    return content_validator.validate_json_input(content)


def is_content_safe(content: str, content_type: str = "general") -> bool:
    """Quick safety check - returns True if content is safe"""
    result = validate_user_input(content, content_type)
    return result.is_valid and result.risk_score < 50
