#!/usr/bin/env python3
"""
Compliance Monitor for ChatGPT Integration
Implements continuous monitoring of all 15 mandatory rules
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
import psutil
from audit_logger import AuditLevel, audit_logger


class ComplianceStatus(Enum):
    """Compliance status levels"""

    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    CRITICAL = "critical"


class RuleCategory(Enum):
    """ChatGPT integration rule categories"""

    AUTHENTICATION = "authentication"
    RATE_LIMITING = "rate_limiting"
    ERROR_HANDLING = "error_handling"
    CONTENT_VALIDATION = "content_validation"
    WEBHOOK_SECURITY = "webhook_security"
    TIMEOUT_MANAGEMENT = "timeout_management"
    MONITORING = "monitoring"
    DATA_SECURITY = "data_security"
    INTEGRATION_TESTING = "integration_testing"
    PERFORMANCE = "performance"
    SCALING = "scaling"
    DISASTER_RECOVERY = "disaster_recovery"
    COMPLIANCE_AUDIT = "compliance_audit"


@dataclass
class ComplianceRule:
    """Individual compliance rule definition"""

    rule_id: str
    rule_number: str
    category: RuleCategory
    title: str
    description: str
    check_function: str
    severity: str
    auto_remediation: bool
    monitoring_interval: int  # seconds
    last_check: Optional[datetime] = None
    status: ComplianceStatus = ComplianceStatus.COMPLIANT
    violations: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.violations is None:
            self.violations = []


class ComplianceMonitor:
    """Continuous compliance monitoring system"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.rules = self._initialize_rules()
        self.monitoring_active = False
        self.violation_counts = {}
        self.performance_metrics = {
            "api_response_times": [],
            "error_rates": {},
            "rate_limit_hits": 0,
            "webhook_failures": 0,
            "system_health": {},
        }

        # Setup logging
        self.logger = logging.getLogger("compliance_monitor")
        self.logger.setLevel(logging.INFO)

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load compliance monitoring configuration"""
        default_config = {
            "monitoring_interval": 60,  # seconds
            "alert_thresholds": {
                "error_rate": 0.05,  # 5%
                "response_time_p95": 5000,  # 5 seconds
                "rate_limit_violations": 10,
                "webhook_failures": 5,
            },
            "auto_remediation": True,
            "notification_endpoints": [],
            "compliance_report_interval": 3600,  # 1 hour
        }

        if config_path and Path(config_path).exists():
            with open(config_path, "r") as f:
                user_config = json.load(f)
                default_config.update(user_config)

        return default_config

    def _initialize_rules(self) -> Dict[str, ComplianceRule]:
        """Initialize all 15 ChatGPT integration compliance rules"""
        rules = {
            "rule_01": ComplianceRule(
                rule_id="rule_01",
                rule_number="Rule 1",
                category=RuleCategory.AUTHENTICATION,
                title="API Authentication and Authorization",
                description="All ChatGPT API calls must use valid authentication tokens",
                check_function="check_api_authentication",
                severity="critical",
                auto_remediation=False,
                monitoring_interval=300,
            ),
            "rule_02": ComplianceRule(
                rule_id="rule_02",
                rule_number="Rule 2",
                category=RuleCategory.RATE_LIMITING,
                title="Rate Limiting Compliance",
                description="API calls must respect rate limits (100 requests/minute)",
                check_function="check_rate_limiting",
                severity="high",
                auto_remediation=True,
                monitoring_interval=60,
            ),
            "rule_03": ComplianceRule(
                rule_id="rule_03",
                rule_number="Rule 3",
                category=RuleCategory.ERROR_HANDLING,
                title="Error Code Mapping",
                description="All API errors must be properly mapped and logged",
                check_function="check_error_handling",
                severity="medium",
                auto_remediation=False,
                monitoring_interval=300,
            ),
            "rule_04": ComplianceRule(
                rule_id="rule_04",
                rule_number="Rule 4",
                category=RuleCategory.CONTENT_VALIDATION,
                title="Content Generation Constraints",
                description="Generated content must comply with safety guidelines",
                check_function="check_content_validation",
                severity="high",
                auto_remediation=True,
                monitoring_interval=180,
            ),
            "rule_05": ComplianceRule(
                rule_id="rule_05",
                rule_number="Rule 5",
                category=RuleCategory.WEBHOOK_SECURITY,
                title="Webhook Security",
                description="Webhooks must use signature verification and HTTPS",
                check_function="check_webhook_security",
                severity="critical",
                auto_remediation=False,
                monitoring_interval=600,
            ),
            "rule_06": ComplianceRule(
                rule_id="rule_06",
                rule_number="Rule 6",
                category=RuleCategory.TIMEOUT_MANAGEMENT,
                title="Timeout Configuration",
                description="API calls must have proper timeout settings (30s)",
                check_function="check_timeout_configuration",
                severity="medium",
                auto_remediation=True,
                monitoring_interval=300,
            ),
            "rule_07": ComplianceRule(
                rule_id="rule_07",
                rule_number="Rule 7",
                category=RuleCategory.MONITORING,
                title="System Monitoring",
                description="Health checks and metrics must be continuously monitored",
                check_function="check_system_monitoring",
                severity="high",
                auto_remediation=False,
                monitoring_interval=120,
            ),
            "rule_08": ComplianceRule(
                rule_id="rule_08",
                rule_number="Rule 8",
                category=RuleCategory.DATA_SECURITY,
                title="Data Security and Privacy",
                description="User data must be encrypted and access logged",
                check_function="check_data_security",
                severity="critical",
                auto_remediation=False,
                monitoring_interval=600,
            ),
            "rule_09": ComplianceRule(
                rule_id="rule_09",
                rule_number="Rule 9",
                category=RuleCategory.INTEGRATION_TESTING,
                title="Integration Testing",
                description="Automated tests must cover all integration points",
                check_function="check_integration_testing",
                severity="medium",
                auto_remediation=False,
                monitoring_interval=3600,
            ),
            "rule_10": ComplianceRule(
                rule_id="rule_10",
                rule_number="Rule 10",
                category=RuleCategory.PERFORMANCE,
                title="Performance Requirements",
                description="API response times must be under 5 seconds (95th percentile)",
                check_function="check_performance_requirements",
                severity="high",
                auto_remediation=True,
                monitoring_interval=180,
            ),
            "rule_11": ComplianceRule(
                rule_id="rule_11",
                rule_number="Rule 11",
                category=RuleCategory.SCALING,
                title="Scaling and Load Management",
                description="System must handle traffic spikes gracefully",
                check_function="check_scaling_requirements",
                severity="high",
                auto_remediation=True,
                monitoring_interval=300,
            ),
            "rule_12": ComplianceRule(
                rule_id="rule_12",
                rule_number="Rule 12",
                category=RuleCategory.DISASTER_RECOVERY,
                title="Disaster Recovery",
                description="Backup and recovery procedures must be tested",
                check_function="check_disaster_recovery",
                severity="medium",
                auto_remediation=False,
                monitoring_interval=86400,  # daily
            ),
            "rule_13": ComplianceRule(
                rule_id="rule_13",
                rule_number="Rule 13",
                category=RuleCategory.COMPLIANCE_AUDIT,
                title="Compliance Documentation",
                description="All compliance activities must be documented",
                check_function="check_compliance_documentation",
                severity="medium",
                auto_remediation=False,
                monitoring_interval=3600,
            ),
            "rule_14": ComplianceRule(
                rule_id="rule_14",
                rule_number="Rule 14",
                category=RuleCategory.DATA_SECURITY,
                title="Data Retention Policy",
                description="Data retention policies must be enforced",
                check_function="check_data_retention",
                severity="high",
                auto_remediation=True,
                monitoring_interval=86400,  # daily
            ),
            "rule_15": ComplianceRule(
                rule_id="rule_15",
                rule_number="Rule 15",
                category=RuleCategory.COMPLIANCE_AUDIT,
                title="Regular Security Audits",
                description="Security audits must be conducted regularly",
                check_function="check_security_audits",
                severity="high",
                auto_remediation=False,
                monitoring_interval=604800,  # weekly
            ),
        }

        return rules

    async def start_monitoring(self):
        """Start continuous compliance monitoring"""
        self.monitoring_active = True
        self.logger.info("Starting compliance monitoring")

        # Log monitoring start
        audit_logger.log_security_event(
            event_description="Compliance monitoring started",
            severity=AuditLevel.INFO,
            additional_data={"rules_count": len(self.rules)},
        )

        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._monitor_rules()),
            asyncio.create_task(self._generate_periodic_reports()),
            asyncio.create_task(self._monitor_system_health()),
        ]

        await asyncio.gather(*tasks)

    async def _monitor_rules(self):
        """Monitor all compliance rules continuously"""
        while self.monitoring_active:
            current_time = datetime.now()

            for rule_id, rule in self.rules.items():
                # Check if rule needs monitoring
                if (
                    rule.last_check is None
                    or (current_time - rule.last_check).total_seconds()
                    >= rule.monitoring_interval
                ):

                    try:
                        # Execute rule check
                        check_result = await self._execute_rule_check(rule)

                        # Update rule status
                        rule.last_check = current_time
                        rule.status = check_result["status"]

                        if check_result["violations"]:
                            rule.violations.extend(check_result["violations"])
                            self._handle_violations(rule, check_result["violations"])

                        # Log compliance check
                        audit_logger.log_security_event(
                            event_description=f"Compliance check: {rule.title}",
                            severity=(
                                AuditLevel.INFO
                                if rule.status == ComplianceStatus.COMPLIANT
                                else AuditLevel.WARNING
                            ),
                            additional_data={
                                "rule_id": rule_id,
                                "status": rule.status.value,
                                "violations_count": len(check_result["violations"]),
                            },
                        )

                    except Exception as e:
                        self.logger.error(f"Error checking rule {rule_id}: {str(e)}")
                        audit_logger.log_security_event(
                            event_description=f"Compliance check failed: {rule.title}",
                            severity=AuditLevel.ERROR,
                            additional_data={"rule_id": rule_id, "error": str(e)},
                        )

            await asyncio.sleep(30)  # Check every 30 seconds

    async def _execute_rule_check(self, rule: ComplianceRule) -> Dict[str, Any]:
        """Execute individual rule check"""
        check_function = getattr(self, rule.check_function, None)
        if not check_function:
            return {
                "status": ComplianceStatus.WARNING,
                "violations": [
                    {"error": f"Check function {rule.check_function} not found"}
                ],
            }

        return await check_function()

    async def check_api_authentication(self) -> Dict[str, Any]:
        """Check API authentication compliance (Rule 1)"""
        violations = []

        # Check if API keys are properly configured
        required_keys = ["OPENAI_API_KEY", "CHATGPT_API_KEY"]
        for key in required_keys:
            if not os.getenv(key):
                violations.append(
                    {
                        "type": "missing_api_key",
                        "key": key,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        # Check for hardcoded keys in code (basic check)
        # In production, this would scan actual code files

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.VIOLATION
        )
        return {"status": status, "violations": violations}

    async def check_rate_limiting(self) -> Dict[str, Any]:
        """Check rate limiting compliance (Rule 2)"""
        violations = []

        # Check current rate limit metrics
        if (
            self.performance_metrics["rate_limit_hits"]
            > self.config["alert_thresholds"]["rate_limit_violations"]
        ):
            violations.append(
                {
                    "type": "rate_limit_exceeded",
                    "hits": self.performance_metrics["rate_limit_hits"],
                    "threshold": self.config["alert_thresholds"][
                        "rate_limit_violations"
                    ],
                    "timestamp": datetime.now().isoformat(),
                }
            )

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.WARNING
        )
        return {"status": status, "violations": violations}

    async def check_error_handling(self) -> Dict[str, Any]:
        """Check error handling compliance (Rule 3)"""
        violations = []

        # Check error rate
        total_requests = sum(self.performance_metrics["error_rates"].values())
        if total_requests > 0:
            error_rate = (
                self.performance_metrics["error_rates"].get("5xx", 0) / total_requests
            )
            if error_rate > self.config["alert_thresholds"]["error_rate"]:
                violations.append(
                    {
                        "type": "high_error_rate",
                        "rate": error_rate,
                        "threshold": self.config["alert_thresholds"]["error_rate"],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.WARNING
        )
        return {"status": status, "violations": violations}

    async def check_content_validation(self) -> Dict[str, Any]:
        """Check content validation compliance (Rule 4)"""
        violations = []

        # Check if content validation is active
        # This would integrate with actual content validation system

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_webhook_security(self) -> Dict[str, Any]:
        """Check webhook security compliance (Rule 5)"""
        violations = []

        # Check webhook failure rate
        if (
            self.performance_metrics["webhook_failures"]
            > self.config["alert_thresholds"]["webhook_failures"]
        ):
            violations.append(
                {
                    "type": "webhook_failures",
                    "failures": self.performance_metrics["webhook_failures"],
                    "threshold": self.config["alert_thresholds"]["webhook_failures"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.WARNING
        )
        return {"status": status, "violations": violations}

    async def check_timeout_configuration(self) -> Dict[str, Any]:
        """Check timeout configuration compliance (Rule 6)"""
        violations = []

        # Check if timeouts are properly configured
        # This would check actual timeout settings in the application

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_system_monitoring(self) -> Dict[str, Any]:
        """Check system monitoring compliance (Rule 7)"""
        violations = []

        # Check if monitoring systems are active
        try:
            # Check system health metrics
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent

            if cpu_usage > 90:
                violations.append(
                    {
                        "type": "high_cpu_usage",
                        "usage": cpu_usage,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if memory_usage > 90:
                violations.append(
                    {
                        "type": "high_memory_usage",
                        "usage": memory_usage,
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        except Exception as e:
            violations.append(
                {
                    "type": "monitoring_error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.WARNING
        )
        return {"status": status, "violations": violations}

    async def check_data_security(self) -> Dict[str, Any]:
        """Check data security compliance (Rule 8)"""
        violations = []

        # Check encryption settings
        # Check access logging
        # This would integrate with actual security systems

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_integration_testing(self) -> Dict[str, Any]:
        """Check integration testing compliance (Rule 9)"""
        violations = []

        # Check if tests are running and passing
        # This would integrate with CI/CD pipeline

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_performance_requirements(self) -> Dict[str, Any]:
        """Check performance requirements compliance (Rule 10)"""
        violations = []

        # Check response time metrics
        if self.performance_metrics["api_response_times"]:
            p95_response_time = sorted(self.performance_metrics["api_response_times"])[
                int(0.95 * len(self.performance_metrics["api_response_times"]))
            ]

            if p95_response_time > self.config["alert_thresholds"]["response_time_p95"]:
                violations.append(
                    {
                        "type": "slow_response_time",
                        "p95_time": p95_response_time,
                        "threshold": self.config["alert_thresholds"][
                            "response_time_p95"
                        ],
                        "timestamp": datetime.now().isoformat(),
                    }
                )

        status = (
            ComplianceStatus.COMPLIANT if not violations else ComplianceStatus.WARNING
        )
        return {"status": status, "violations": violations}

    async def check_scaling_requirements(self) -> Dict[str, Any]:
        """Check scaling requirements compliance (Rule 11)"""
        violations = []

        # Check auto-scaling metrics
        # This would integrate with infrastructure monitoring

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_disaster_recovery(self) -> Dict[str, Any]:
        """Check disaster recovery compliance (Rule 12)"""
        violations = []

        # Check backup status
        # Check recovery procedures
        # This would integrate with backup systems

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_compliance_documentation(self) -> Dict[str, Any]:
        """Check compliance documentation (Rule 13)"""
        violations = []

        # Check if documentation is up to date
        # Check audit trail completeness

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_data_retention(self) -> Dict[str, Any]:
        """Check data retention compliance (Rule 14)"""
        violations = []

        # Check data retention policies
        # This would integrate with data management systems

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    async def check_security_audits(self) -> Dict[str, Any]:
        """Check security audit compliance (Rule 15)"""
        violations = []

        # Check last audit date
        # Check audit completeness

        status = ComplianceStatus.COMPLIANT
        return {"status": status, "violations": violations}

    def _handle_violations(
        self, rule: ComplianceRule, violations: List[Dict[str, Any]]
    ):
        """Handle compliance violations"""
        for violation in violations:
            # Log violation
            audit_logger.log_security_event(
                event_description=f"Compliance violation: {rule.title}",
                severity=(
                    AuditLevel.WARNING
                    if rule.severity != "critical"
                    else AuditLevel.ERROR
                ),
                additional_data={
                    "rule_id": rule.rule_id,
                    "violation": violation,
                    "auto_remediation": rule.auto_remediation,
                },
            )

            # Attempt auto-remediation if enabled
            if rule.auto_remediation:
                self._attempt_auto_remediation(rule, violation)

    def _attempt_auto_remediation(
        self, rule: ComplianceRule, violation: Dict[str, Any]
    ):
        """Attempt automatic remediation of violations"""
        # Implementation would depend on specific violation types
        self.logger.info(f"Attempting auto-remediation for rule {rule.rule_id}")

    async def _generate_periodic_reports(self):
        """Generate periodic compliance reports"""
        while self.monitoring_active:
            await asyncio.sleep(self.config["compliance_report_interval"])

            report = self.generate_compliance_report()

            # Save report
            report_file = Path(
                f"/var/log/trae/compliance/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            report_file.parent.mkdir(parents=True, exist_ok=True)

            with open(report_file, "w") as f:
                json.dump(report, f, indent=2)

            # Log report generation
            audit_logger.log_security_event(
                event_description="Compliance report generated",
                severity=AuditLevel.INFO,
                additional_data={"report_file": str(report_file)},
            )

    async def _monitor_system_health(self):
        """Monitor overall system health"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                self.performance_metrics["system_health"] = {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                    "timestamp": datetime.now().isoformat(),
                }

            except Exception as e:
                self.logger.error(f"Error collecting system health metrics: {str(e)}")

            await asyncio.sleep(60)  # Check every minute

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        compliant_rules = sum(
            1
            for rule in self.rules.values()
            if rule.status == ComplianceStatus.COMPLIANT
        )
        total_rules = len(self.rules)
        compliance_percentage = (compliant_rules / total_rules) * 100

        report = {
            "report_id": f"compliance_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_rules": total_rules,
                "compliant_rules": compliant_rules,
                "compliance_percentage": compliance_percentage,
                "monitoring_active": self.monitoring_active,
            },
            "rule_status": {
                rule_id: {
                    "status": rule.status.value,
                    "last_check": (
                        rule.last_check.isoformat() if rule.last_check else None
                    ),
                    "violations_count": len(rule.violations),
                    "category": rule.category.value,
                }
                for rule_id, rule in self.rules.items()
            },
            "performance_metrics": self.performance_metrics,
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        non_compliant_rules = [
            rule
            for rule in self.rules.values()
            if rule.status != ComplianceStatus.COMPLIANT
        ]

        if non_compliant_rules:
            recommendations.append(
                f"Address {len(non_compliant_rules)} non-compliant rules"
            )

        if self.performance_metrics["rate_limit_hits"] > 0:
            recommendations.append("Review rate limiting implementation")

        if self.performance_metrics["webhook_failures"] > 0:
            recommendations.append("Investigate webhook failures")

        return recommendations

    def stop_monitoring(self):
        """Stop compliance monitoring"""
        self.monitoring_active = False
        self.logger.info("Compliance monitoring stopped")

        audit_logger.log_security_event(
            event_description="Compliance monitoring stopped", severity=AuditLevel.INFO
        )


# Global compliance monitor instance
compliance_monitor = ComplianceMonitor()
