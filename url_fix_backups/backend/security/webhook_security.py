#!/usr / bin / env python3
""""""
Webhook Security System for ChatGPT Integration
Implements Rule 5: Webhook Security Requirements
""""""

import asyncio
import base64
import hashlib
import hmac
import ipaddress
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from audit_logger import AuditLevel, audit_logger
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from timeout_manager import TimeoutType, timeout_manager


class WebhookSecurityLevel(Enum):
    """Security levels for webhook validation"""

    BASIC = "basic"  # HTTPS + basic validation
    STANDARD = "standard"  # + signature verification
    ENHANCED = "enhanced"  # + IP allowlisting
    MAXIMUM = "maximum"  # + encryption + rate limiting


class WebhookEventType(Enum):
    """Types of webhook events"""

    CHATGPT_RESPONSE = "chatgpt_response"
    CONTENT_GENERATED = "content_generated"
    ERROR_NOTIFICATION = "error_notification"
    STATUS_UPDATE = "status_update"
    SECURITY_ALERT = "security_alert"


@dataclass
class WebhookConfig:
    """Webhook configuration settings"""

    webhook_id: str
    url: str
    secret_key: str
    security_level: WebhookSecurityLevel
    allowed_ips: List[str]
    max_payload_size: int
    timeout_seconds: int
    retry_attempts: int
    signature_algorithm: str
    encryption_enabled: bool
    rate_limit_per_minute: int
    active: bool


@dataclass
class WebhookEvent:
    """Webhook event data structure"""

    event_id: str
    event_type: WebhookEventType
    timestamp: str
    payload: Dict[str, Any]
    signature: Optional[str]
    source_ip: Optional[str]
    user_agent: Optional[str]
    webhook_id: str


@dataclass
class WebhookDeliveryResult:
    """Result of webhook delivery attempt"""

    event_id: str
    webhook_id: str
    success: bool
    status_code: Optional[int]
    response_time_ms: float
    attempt_number: int
    error_message: Optional[str]
    timestamp: str


class WebhookSecurityManager:
    """Comprehensive webhook security management system"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = self._load_default_config()
        if config:
            self.config.update(config)

        self.webhooks = {}
        self.delivery_history = []
        self.rate_limit_tracker = {}
        self.blocked_ips = set()

        # Initialize encryption
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # Setup logging
        self.logger = logging.getLogger("webhook_security")
        self.logger.setLevel(logging.INFO)

        # Load webhook configurations
        self._load_webhook_configs()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default webhook security configuration"""
        return {
            "default_security_level": WebhookSecurityLevel.STANDARD,
            "signature_algorithm": "sha256",
            "max_payload_size": 1024 * 1024,  # 1MB
            "default_timeout": 10,  # seconds
            "default_retry_attempts": 3,
            "rate_limit_window": 60,  # seconds
            "default_rate_limit": 100,  # requests per minute
            "ip_allowlist_enabled": True,
            "encryption_enabled": True,
            "signature_verification_required": True,
            "https_required": True,
            "webhook_config_file": "/etc / trae / webhooks.json",
            "blocked_ip_threshold": 10,  # failed attempts before blocking
            "block_duration": 3600,  # 1 hour
# BRACKET_SURGEON: disabled
#         }

    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for webhook payloads"""
        key_env = os.getenv("WEBHOOK_ENCRYPTION_KEY")
        if key_env:
            return base64.urlsafe_b64decode(key_env.encode())

        # Generate new key
        password = os.getenv("WEBHOOK_MASTER_PASSWORD", "default_webhook_password").encode()
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
# BRACKET_SURGEON: disabled
#         )
        key = base64.urlsafe_b64encode(kdf.derive(password))

        # In production, this should be stored securely
        self.logger.warning("Generated new webhook encryption key. Store securely!")

        return key

    def _load_webhook_configs(self):
        """Load webhook configurations from file or environment"""
        # Default ChatGPT integration webhook
        default_webhook = WebhookConfig(
            webhook_id="chatgpt_integration",
            url=os.getenv("CHATGPT_WEBHOOK_URL", "https://api.example.com / webhooks / chatgpt"),
            secret_key=os.getenv("CHATGPT_WEBHOOK_SECRET", "default_secret"),
            security_level=WebhookSecurityLevel.STANDARD,
            allowed_ips=["0.0.0.0 / 0"],  # Allow all by default, restrict in production
            max_payload_size=self.config["max_payload_size"],
            timeout_seconds=self.config["default_timeout"],
            retry_attempts=self.config["default_retry_attempts"],
            signature_algorithm=self.config["signature_algorithm"],
            encryption_enabled=self.config["encryption_enabled"],
            rate_limit_per_minute=self.config["default_rate_limit"],
            active=True,
# BRACKET_SURGEON: disabled
#         )

        self.webhooks[default_webhook.webhook_id] = default_webhook

    def register_webhook(self, webhook_config: WebhookConfig) -> bool:
        """Register a new webhook with security validation"""
        try:
            # Validate webhook configuration
            validation_result = self._validate_webhook_config(webhook_config)
            if not validation_result["valid"]:
                self.logger.error(f"Invalid webhook config: {validation_result['errors']}")
                return False

            # Store webhook configuration
            self.webhooks[webhook_config.webhook_id] = webhook_config

            # Log registration
            audit_logger.log_security_event(
                event_description=f"Webhook registered: {webhook_config.webhook_id}",
                severity=AuditLevel.INFO,
                additional_data={
                    "webhook_id": webhook_config.webhook_id,
                    "url": webhook_config.url,
                    "security_level": webhook_config.security_level.value,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             )

            return True

        except Exception as e:
            self.logger.error(f"Error registering webhook: {str(e)}")
            return False

    def _validate_webhook_config(self, config: WebhookConfig) -> Dict[str, Any]:
        """Validate webhook configuration for security compliance"""
        errors = []

        # Validate URL
        try:
            parsed_url = urlparse(config.url)
            if self.config["https_required"] and parsed_url.scheme != "https":
                errors.append("HTTPS is required for webhook URLs")
            if not parsed_url.netloc:
                errors.append("Invalid webhook URL")
        except Exception:
            errors.append("Invalid webhook URL format")

        # Validate secret key
        if len(config.secret_key) < 32:
            errors.append("Webhook secret key must be at least 32 characters")

        # Validate IP allowlist
        for ip_range in config.allowed_ips:
            try:
                ipaddress.ip_network(ip_range, strict=False)
            except ValueError:
                errors.append(f"Invalid IP range: {ip_range}")

        # Validate payload size
        if config.max_payload_size > 10 * 1024 * 1024:  # 10MB max
            errors.append("Maximum payload size too large (max 10MB)")

        return {"valid": len(errors) == 0, "errors": errors}

    def generate_signature(self, payload: str, secret_key: str, algorithm: str = "sha256") -> str:
        """Generate HMAC signature for webhook payload"""
        if algorithm == "sha256":
            hash_func = hashlib.sha256
        elif algorithm == "sha1":
            hash_func = hashlib.sha1
        else:
            raise ValueError(f"Unsupported signature algorithm: {algorithm}")

        signature = hmac.new(
            secret_key.encode("utf - 8"), payload.encode("utf - 8"), hash_func
        ).hexdigest()

        return f"{algorithm}={signature}"

    def verify_signature(self, payload: str, signature: str, secret_key: str) -> bool:
        """Verify webhook signature"""
        try:
            # Parse signature
            if "=" not in signature:
                return False

            algorithm, provided_signature = signature.split("=", 1)

            # Generate expected signature
            expected_signature = self.generate_signature(payload, secret_key, algorithm)
            expected_hash = expected_signature.split("=", 1)[1]

            # Constant - time comparison to prevent timing attacks
            return hmac.compare_digest(provided_signature, expected_hash)

        except Exception as e:
            self.logger.error(f"Signature verification error: {str(e)}")
            return False

    def validate_ip_address(self, ip_address: str, allowed_ranges: List[str]) -> bool:
        """Validate if IP address is in allowed ranges"""
        try:
            client_ip = ipaddress.ip_address(ip_address)

            for ip_range in allowed_ranges:
                network = ipaddress.ip_network(ip_range, strict=False)
                if client_ip in network:
                    return True

            return False

        except ValueError:
            return False

    def check_rate_limit(self, webhook_id: str, source_ip: str) -> bool:
        """Check if request is within rate limits"""
        current_time = time.time()
        window_start = current_time - self.config["rate_limit_window"]

        # Clean old entries
        key = f"{webhook_id}:{source_ip}"
        if key not in self.rate_limit_tracker:
            self.rate_limit_tracker[key] = []

        # Remove old timestamps
        self.rate_limit_tracker[key] = [
            timestamp for timestamp in self.rate_limit_tracker[key] if timestamp > window_start
# BRACKET_SURGEON: disabled
#         ]

        # Check limit
        webhook_config = self.webhooks.get(webhook_id)
        if not webhook_config:
            return False

        if len(self.rate_limit_tracker[key]) >= webhook_config.rate_limit_per_minute:
            return False

        # Add current request
        self.rate_limit_tracker[key].append(current_time)
        return True

    def encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt webhook payload"""
        try:
            payload_json = json.dumps(payload, sort_keys=True)
            encrypted_data = self.cipher_suite.encrypt(payload_json.encode("utf - 8"))
            return base64.urlsafe_b64encode(encrypted_data).decode("utf - 8")
        except Exception as e:
            self.logger.error(f"Payload encryption error: {str(e)}")
            raise

    def decrypt_payload(self, encrypted_payload: str) -> Dict[str, Any]:
        """Decrypt webhook payload"""
        try:
            encrypted_data = base64.urlsafe_b64decode(encrypted_payload.encode("utf - 8"))
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode("utf - 8"))
        except Exception as e:
            self.logger.error(f"Payload decryption error: {str(e)}")
            raise

    async def validate_incoming_webhook(
        self,
        webhook_id: str,
        payload: str,
        signature: Optional[str],
        source_ip: str,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate incoming webhook request"""

        validation_result = {
            "valid": False,
            "errors": [],
            "security_checks": {
                "signature_valid": False,
                "ip_allowed": False,
                "rate_limit_ok": False,
                "payload_size_ok": False,
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        try:
            # Get webhook configuration
            webhook_config = self.webhooks.get(webhook_id)
            if not webhook_config:
                validation_result["errors"].append("Unknown webhook ID")
                return validation_result

            if not webhook_config.active:
                validation_result["errors"].append("Webhook is disabled")
                return validation_result

            # Check if IP is blocked
            if source_ip in self.blocked_ips:
                validation_result["errors"].append("IP address is blocked")
                audit_logger.log_security_event(
                    event_description=f"Blocked IP attempted webhook access: {source_ip}",
                    severity=AuditLevel.WARNING,
                    ip_address=source_ip,
                    additional_data={"webhook_id": webhook_id},
# BRACKET_SURGEON: disabled
#                 )
                return validation_result

            # Check payload size
            if len(payload.encode("utf - 8")) > webhook_config.max_payload_size:
                validation_result["errors"].append("Payload too large")
            else:
                validation_result["security_checks"]["payload_size_ok"] = True

            # Check rate limiting
            if not self.check_rate_limit(webhook_id, source_ip):
                validation_result["errors"].append("Rate limit exceeded")
                audit_logger.log_security_event(
                    event_description=f"Rate limit exceeded for webhook: {webhook_id}",
                    severity=AuditLevel.WARNING,
                    ip_address=source_ip,
                    additional_data={"webhook_id": webhook_id},
# BRACKET_SURGEON: disabled
#                 )
            else:
                validation_result["security_checks"]["rate_limit_ok"] = True

            # Check IP allowlist
            if webhook_config.security_level in [
                WebhookSecurityLevel.ENHANCED,
                WebhookSecurityLevel.MAXIMUM,
# BRACKET_SURGEON: disabled
#             ]:
                if not self.validate_ip_address(source_ip, webhook_config.allowed_ips):
                    validation_result["errors"].append("IP address not allowed")
                    audit_logger.log_security_event(
                        event_description=f"Unauthorized IP attempted webhook access: {source_ip}",
                        severity=AuditLevel.WARNING,
                        ip_address=source_ip,
                        additional_data={"webhook_id": webhook_id},
# BRACKET_SURGEON: disabled
#                     )
                else:
                    validation_result["security_checks"]["ip_allowed"] = True
            else:
                validation_result["security_checks"]["ip_allowed"] = True

            # Check signature
            if webhook_config.security_level in [
                WebhookSecurityLevel.STANDARD,
                WebhookSecurityLevel.ENHANCED,
                WebhookSecurityLevel.MAXIMUM,
# BRACKET_SURGEON: disabled
#             ]:
                if not signature:
                    validation_result["errors"].append("Missing signature")
                elif not self.verify_signature(payload, signature, webhook_config.secret_key):
                    validation_result["errors"].append("Invalid signature")
                    audit_logger.log_security_event(
                        event_description=f"Invalid webhook signature: {webhook_id}",
                        severity=AuditLevel.ERROR,
                        ip_address=source_ip,
                        additional_data={
                            "webhook_id": webhook_id,
                            "signature": signature,
# BRACKET_SURGEON: disabled
#                         },
# BRACKET_SURGEON: disabled
#                     )
                else:
                    validation_result["security_checks"]["signature_valid"] = True
            else:
                validation_result["security_checks"]["signature_valid"] = True

            # Overall validation result
            validation_result["valid"] = len(validation_result["errors"]) == 0

            # Log validation result
            audit_logger.log_security_event(
                event_description=f"Webhook validation: {webhook_id}",
                severity=(AuditLevel.INFO if validation_result["valid"] else AuditLevel.WARNING),
                ip_address=source_ip,
                additional_data={
                    "webhook_id": webhook_id,
                    "valid": validation_result["valid"],
                    "errors": validation_result["errors"],
                    "user_agent": user_agent,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             )

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            self.logger.error(f"Webhook validation error: {str(e)}")

        return validation_result

    async def send_webhook(
        self,
        webhook_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        custom_headers: Optional[Dict[str, str]] = None,
# BRACKET_SURGEON: disabled
#     ) -> WebhookDeliveryResult:
        """Send webhook with security measures"""

        webhook_config = self.webhooks.get(webhook_id)
        if not webhook_config:
            raise ValueError(f"Unknown webhook ID: {webhook_id}")

        event_id = f"webhook_{int(time.time() * 1000)}"
        start_time = time.time()

        # Prepare payload
        webhook_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            payload=payload,
            signature=None,
            source_ip=None,
            user_agent="Trae - Webhook - Client / 1.0",
            webhook_id=webhook_id,
# BRACKET_SURGEON: disabled
#         )

        # Encrypt payload if required
        if webhook_config.encryption_enabled:
            encrypted_payload = self.encrypt_payload(asdict(webhook_event))
            payload_to_send = {"encrypted_data": encrypted_payload}
        else:
            payload_to_send = asdict(webhook_event)

        payload_json = json.dumps(payload_to_send, sort_keys=True)

        # Generate signature
        signature = self.generate_signature(
            payload_json, webhook_config.secret_key, webhook_config.signature_algorithm
# BRACKET_SURGEON: disabled
#         )

        # Prepare headers
        headers = {
            "Content - Type": "application / json",
            "X - Webhook - Signature": signature,
            "X - Webhook - Event - Type": event_type.value,
            "X - Webhook - Event - ID": event_id,
            "X - Webhook - Timestamp": webhook_event.timestamp,
            "User - Agent": webhook_event.user_agent,
# BRACKET_SURGEON: disabled
#         }

        if custom_headers:
            headers.update(custom_headers)

        # Send webhook with timeout
        last_exception = None

        for attempt in range(webhook_config.retry_attempts + 1):
            try:
                async with timeout_manager.timeout_context(
                    operation_type=TimeoutType.WEBHOOK,
                    custom_timeout=webhook_config.timeout_seconds,
# BRACKET_SURGEON: disabled
#                 ):
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            url=webhook_config.url, data=payload_json, headers=headers
# BRACKET_SURGEON: disabled
#                         ) as response:
                            end_time = time.time()
                            response_time_ms = (end_time - start_time) * 1000

                            success = response.status < 400

                            result = WebhookDeliveryResult(
                                event_id=event_id,
                                webhook_id=webhook_id,
                                success=success,
                                status_code=response.status,
                                response_time_ms=response_time_ms,
                                attempt_number=attempt + 1,
                                error_message=(None if success else f"HTTP {response.status}"),
                                timestamp=datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#                             )

                            # Log delivery result
                            audit_logger.log_api_request(
                                endpoint=webhook_config.url,
                                method="POST",
                                status_code=response.status,
                                response_time_ms=response_time_ms,
                                additional_data={
                                    "webhook_id": webhook_id,
                                    "event_type": event_type.value,
                                    "attempt": attempt + 1,
                                    "success": success,
# BRACKET_SURGEON: disabled
#                                 },
# BRACKET_SURGEON: disabled
#                             )

                            self.delivery_history.append(result)

                            if success:
                                return result

                            last_exception = Exception(f"HTTP {response.status}")

            except Exception as e:
                last_exception = e

                if attempt < webhook_config.retry_attempts:
                    await asyncio.sleep(2**attempt)  # Exponential backoff

        # Final failure
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        result = WebhookDeliveryResult(
            event_id=event_id,
            webhook_id=webhook_id,
            success=False,
            status_code=None,
            response_time_ms=response_time_ms,
            attempt_number=webhook_config.retry_attempts + 1,
            error_message=str(last_exception),
            timestamp=datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#         )

        self.delivery_history.append(result)

        audit_logger.log_security_event(
            event_description=f"Webhook delivery failed: {webhook_id}",
            severity=AuditLevel.ERROR,
            additional_data={
                "webhook_id": webhook_id,
                "event_type": event_type.value,
                "error": str(last_exception),
                "attempts": webhook_config.retry_attempts + 1,
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         )

        return result

    def get_webhook_security_report(self) -> Dict[str, Any]:
        """Generate webhook security compliance report"""

        total_webhooks = len(self.webhooks)
        active_webhooks = sum(1 for wh in self.webhooks.values() if wh.active)
        https_compliant = sum(
            1 for wh in self.webhooks.values() if urlparse(wh.url).scheme == "https"
# BRACKET_SURGEON: disabled
#         )

        recent_deliveries = [
            delivery
            for delivery in self.delivery_history
            if datetime.fromisoformat(delivery.timestamp) > datetime.utcnow() - timedelta(hours=24)
# BRACKET_SURGEON: disabled
#         ]

        success_rate = (
            sum(1 for d in recent_deliveries if d.success) / len(recent_deliveries)
            if recent_deliveries
            else 0
# BRACKET_SURGEON: disabled
#         ) * 100

        report = {
            "report_id": f"webhook_security_{datetime.now().strftime('%Y % m%d_ % H%M % S')}",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_webhooks": total_webhooks,
                "active_webhooks": active_webhooks,
                "https_compliance": f"{https_compliant}/{total_webhooks}",
                "success_rate_24h": f"{success_rate:.1f}%",
                "blocked_ips": len(self.blocked_ips),
# BRACKET_SURGEON: disabled
#             },
            "security_compliance": {
                "rule_5_https_required": https_compliant == total_webhooks,
                "signature_verification_enabled": all(
                    wh.security_level != WebhookSecurityLevel.BASIC for wh in self.webhooks.values()
# BRACKET_SURGEON: disabled
#                 ),
                "rate_limiting_active": True,
                "ip_allowlisting_available": True,
                "encryption_available": True,
# BRACKET_SURGEON: disabled
#             },
            "webhook_details": {
                wh_id: {
                    "url": wh.url,
                    "security_level": wh.security_level.value,
                    "https_enabled": urlparse(wh.url).scheme == "https",
                    "active": wh.active,
                    "rate_limit": wh.rate_limit_per_minute,
# BRACKET_SURGEON: disabled
#                 }
                for wh_id, wh in self.webhooks.items()
# BRACKET_SURGEON: disabled
#             },
            "recent_activity": {
                "deliveries_24h": len(recent_deliveries),
                "success_count": sum(1 for d in recent_deliveries if d.success),
                "failure_count": sum(1 for d in recent_deliveries if not d.success),
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        return report


# Global webhook security manager instance
webhook_security = WebhookSecurityManager()

# Convenience functions


async def send_chatgpt_webhook(event_type: WebhookEventType, payload: Dict[str, Any]):
    """Send ChatGPT integration webhook"""
    return await webhook_security.send_webhook(
        webhook_id="chatgpt_integration", event_type=event_type, payload=payload
# BRACKET_SURGEON: disabled
#     )


async def validate_chatgpt_webhook(payload: str, signature: str, source_ip: str):
    """Validate incoming ChatGPT webhook"""
    return await webhook_security.validate_incoming_webhook(
        webhook_id="chatgpt_integration",
        payload=payload,
        signature=signature,
        source_ip=source_ip,
# BRACKET_SURGEON: disabled
#     )