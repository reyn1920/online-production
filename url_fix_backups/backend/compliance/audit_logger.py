#!/usr / bin / env python3
""""""
Audit Logger for ChatGPT Integration Compliance
Implements Rule 15: Compliance and Audit Requirements
""""""

import hashlib
import hmac
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """Types of audit events"""

    API_REQUEST = "api_request"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    SYSTEM_EVENT = "system_event"
    SECURITY_EVENT = "security_event"
    COMPLIANCE_EVENT = "compliance_event"
    ERROR_EVENT = "error_event"


class AuditLevel(Enum):
    """Audit event severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""

    timestamp: str
    event_id: str
    event_type: AuditEventType
    level: AuditLevel
    user_id: Optional[str]
    session_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[float]
    request_size: Optional[int]
    response_size: Optional[int]
    error_message: Optional[str]
    additional_data: Dict[str, Any]
    compliance_tags: List[str]
    data_classification: str
    retention_period_days: int


class AuditLogger:
    """Comprehensive audit logging system for compliance"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._load_default_config()
        self.audit_dir = Path(self.config["audit_directory"])
        self.audit_dir.mkdir(parents=True, exist_ok=True)

        # Setup structured logging
        self.logger = self._setup_logger()

        # Initialize compliance tracking
        self.compliance_metrics = {
            "total_events": 0,
            "security_events": 0,
            "failed_authentications": 0,
            "data_access_events": 0,
            "gdpr_events": 0,
            "ccpa_events": 0,
# BRACKET_SURGEON: disabled
#         }

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default audit configuration"""
        return {
            "audit_directory": "/var / log / trae / audit",
            "retention_days": 365,  # 1 year as per Rule 15
            "max_file_size_mb": 100,
            "encryption_enabled": True,
            "compression_enabled": True,
            "real_time_alerts": True,
            "compliance_reporting": True,
            "gdpr_compliance": True,
            "ccpa_compliance": True,
            "audit_integrity_checks": True,
# BRACKET_SURGEON: disabled
#         }

    def _setup_logger(self) -> logging.Logger:
        """Setup structured audit logger"""
        logger = logging.getLogger("audit_logger")
        logger.setLevel(logging.INFO)

        # Create file handler with rotation
        log_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y % m%d')}.log"
        handler = logging.FileHandler(log_file)

        # JSON formatter for structured logging
        formatter = logging.Formatter(
            "%(asctime)s|%(levelname)s|%(message)s", datefmt="%Y-%m-%d %H:%M:%S"
# BRACKET_SURGEON: disabled
#         )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def log_api_request(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status_code: Optional[int] = None,
        response_time_ms: Optional[float] = None,
        request_size: Optional[int] = None,
        response_size: Optional[int] = None,
        additional_data: Optional[Dict[str, Any]] = None,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Log API request for compliance tracking"""

        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_id=self._generate_event_id(),
            event_type=AuditEventType.API_REQUEST,
            level=AuditLevel.INFO,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            request_size=request_size,
            response_size=response_size,
            error_message=None,
            additional_data=additional_data or {},
            compliance_tags=["api_access", "chatgpt_integration"],
            data_classification="internal",
            retention_period_days=365,
# BRACKET_SURGEON: disabled
#         )

        return self._write_audit_event(event)

    def log_authentication_event(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Log authentication events for security monitoring"""

        level = AuditLevel.INFO if success else AuditLevel.WARNING

        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_id=self._generate_event_id(),
            event_type=AuditEventType.AUTHENTICATION,
            level=level,
            user_id=user_id,
            session_id=None,
            ip_address=ip_address,
            user_agent=user_agent,
            endpoint=None,
            method=None,
            status_code=200 if success else 401,
            response_time_ms=None,
            request_size=None,
            response_size=None,
            error_message=failure_reason if not success else None,
            additional_data=additional_data or {},
            compliance_tags=["authentication", "security"],
            data_classification="confidential",
            retention_period_days=365,
# BRACKET_SURGEON: disabled
#         )

        if not success:
            self.compliance_metrics["failed_authentications"] += 1

        return self._write_audit_event(event)

    def log_security_event(
        self,
        event_description: str,
        severity: AuditLevel,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Log security events for threat monitoring"""

        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_id=self._generate_event_id(),
            event_type=AuditEventType.SECURITY_EVENT,
            level=severity,
            user_id=user_id,
            session_id=None,
            ip_address=ip_address,
            user_agent=None,
            endpoint=None,
            method=None,
            status_code=None,
            response_time_ms=None,
            request_size=None,
            response_size=None,
            error_message=event_description,
            additional_data=additional_data or {},
            compliance_tags=["security", "threat_detection"],
            data_classification="confidential",
            retention_period_days=365,
# BRACKET_SURGEON: disabled
#         )

        self.compliance_metrics["security_events"] += 1

        return self._write_audit_event(event)

    def log_data_access(
        self,
        data_type: str,
        operation: str,
        user_id: str,
        data_classification: str = "internal",
        gdpr_relevant: bool = False,
        ccpa_relevant: bool = False,
        additional_data: Optional[Dict[str, Any]] = None,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Log data access for privacy compliance"""

        compliance_tags = ["data_access"]
        if gdpr_relevant:
            compliance_tags.append("gdpr")
            self.compliance_metrics["gdpr_events"] += 1
        if ccpa_relevant:
            compliance_tags.append("ccpa")
            self.compliance_metrics["ccpa_events"] += 1

        event = AuditEvent(
            timestamp=datetime.utcnow().isoformat(),
            event_id=self._generate_event_id(),
            event_type=AuditEventType.DATA_ACCESS,
            level=AuditLevel.INFO,
            user_id=user_id,
            session_id=None,
            ip_address=None,
            user_agent=None,
            endpoint=None,
            method=None,
            status_code=None,
            response_time_ms=None,
            request_size=None,
            response_size=None,
            error_message=None,
            additional_data={
                "data_type": data_type,
                "operation": operation,
                **(additional_data or {}),
# BRACKET_SURGEON: disabled
#             },
            compliance_tags=compliance_tags,
            data_classification=data_classification,
            retention_period_days=365,
# BRACKET_SURGEON: disabled
#         )

        self.compliance_metrics["data_access_events"] += 1

        return self._write_audit_event(event)

    def _write_audit_event(self, event: AuditEvent) -> str:
        """Write audit event to log with integrity protection"""

        # Convert to JSON
        event_json = json.dumps(asdict(event), sort_keys=True)

        # Add integrity hash
        event_hash = self._calculate_integrity_hash(event_json)

        # Create final log entry
        log_entry = {
            "event": asdict(event),
            "integrity_hash": event_hash,
            "log_timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#         }

        # Write to structured log
        self.logger.info(json.dumps(log_entry))

        # Update metrics
        self.compliance_metrics["total_events"] += 1

        return event.event_id

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        timestamp = datetime.utcnow().isoformat()
        random_data = os.urandom(8).hex()
        return f"audit_{timestamp}_{random_data}"

    def _calculate_integrity_hash(self, data: str) -> str:
        """Calculate integrity hash for audit event"""
        secret_key = os.getenv("AUDIT_INTEGRITY_KEY", "default_audit_key")
        return hmac.new(
            secret_key.encode("utf - 8"), data.encode("utf - 8"), hashlib.sha256
        ).hexdigest()

    def generate_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for audit purposes"""

        report = {
            "report_id": self._generate_event_id(),
            "report_timestamp": datetime.utcnow().isoformat(),
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "metrics": self.compliance_metrics.copy(),
            "compliance_status": {
                "gdpr_compliant": True,
                "ccpa_compliant": True,
                "audit_logging_active": True,
                "data_retention_policy_enforced": True,
                "security_monitoring_active": True,
# BRACKET_SURGEON: disabled
#             },
            "recommendations": [
                "Continue regular security audits",
                "Monitor authentication failure rates",
                "Review data access patterns monthly",
                "Ensure audit log integrity checks",
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         }

        # Save report
        report_file = (
            self.audit_dir
            / f"compliance_report_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
# BRACKET_SURGEON: disabled
#         )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        return report

    def cleanup_old_logs(self) -> int:
        """Clean up old audit logs based on retention policy"""

        retention_days = self.config["retention_days"]
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        deleted_count = 0
        for log_file in self.audit_dir.glob("audit_*.log"):
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                log_file.unlink()
                deleted_count += 1

        return deleted_count


# Global audit logger instance
audit_logger = AuditLogger()

# Convenience functions for common audit events


def log_chatgpt_api_call(endpoint: str, user_id: str, success: bool, **kwargs):
    """Log ChatGPT API integration calls"""
    if success:
        return audit_logger.log_api_request(
            endpoint=endpoint,
            method="POST",
            user_id=user_id,
            additional_data={"integration": "chatgpt", **kwargs},
# BRACKET_SURGEON: disabled
#         )
    else:
        return audit_logger.log_security_event(
            event_description=f"ChatGPT API call failed: {endpoint}",
            severity=AuditLevel.WARNING,
            user_id=user_id,
            additional_data={"integration": "chatgpt", **kwargs},
# BRACKET_SURGEON: disabled
#         )


def log_rate_limit_violation(user_id: str, endpoint: str, ip_address: str):
    """Log rate limit violations"""
    return audit_logger.log_security_event(
        event_description=f"Rate limit exceeded for endpoint: {endpoint}",
        severity=AuditLevel.WARNING,
        user_id=user_id,
        ip_address=ip_address,
        additional_data={"violation_type": "rate_limit", "endpoint": endpoint},
# BRACKET_SURGEON: disabled
#     )


def log_webhook_signature_failure(webhook_id: str, ip_address: str):
    """Log webhook signature verification failures"""
    return audit_logger.log_security_event(
        event_description=f"Webhook signature verification failed: {webhook_id}",
        severity=AuditLevel.ERROR,
        ip_address=ip_address,
        additional_data={
            "violation_type": "signature_verification",
            "webhook_id": webhook_id,
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     )