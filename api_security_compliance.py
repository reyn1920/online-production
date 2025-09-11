#!/usr/bin/env python3
"""
API Security and Compliance Validator
Comprehensive security validation and compliance checking for 100+ APIs

Features:
- Security vulnerability scanning
- Compliance validation (GDPR, CCPA, SOC2, etc.)
- API authentication testing
- Rate limiting validation
- SSL/TLS certificate checking
- Data privacy assessment
- Penetration testing
- Compliance reporting

Usage:
    python api_security_compliance.py
"""

import asyncio
import base64
import concurrent.futures
import hashlib
import hmac
import json
import logging
import os
import re
import socket
import ssl
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
import yaml
from cryptography import x509
from cryptography.hazmat.backends import default_backend

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SecurityVulnerability:
    severity: str  # critical, high, medium, low
    category: str
    description: str
    recommendation: str
    cve_id: Optional[str]
    affected_endpoints: List[str]
    remediation_effort: str  # low, medium, high
    compliance_impact: List[str]


@dataclass
class ComplianceRequirement:
    regulation: str  # GDPR, CCPA, SOC2, HIPAA, etc.
    requirement_id: str
    description: str
    status: str  # compliant, non_compliant, partial, unknown
    evidence: List[str]
    remediation_steps: List[str]
    deadline: Optional[str]
    risk_level: str


@dataclass
class SecurityTestResult:
    api_name: str
    api_key: str
    test_timestamp: str
    overall_score: float  # 0-100
    security_grade: str  # A+, A, B, C, D, F
    vulnerabilities: List[SecurityVulnerability]
    compliance_status: List[ComplianceRequirement]
    ssl_certificate: Dict[str, Any]
    authentication_security: Dict[str, Any]
    rate_limiting: Dict[str, Any]
    data_privacy: Dict[str, Any]
    penetration_test: Dict[str, Any]
    recommendations: List[str]
    next_scan_date: str


class APISecurityCompliance:
    def __init__(self):
        self.results_dir = Path("security_results")
        self.reports_dir = Path("compliance_reports")
        self.templates_dir = Path("compliance_templates")

        # Create directories
        self.results_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

        self.security_results = {}
        self.compliance_frameworks = self.load_compliance_frameworks()

        # Load API configurations
        try:
            from api_config_manager import APIConfigManager

            self.config_manager = APIConfigManager()
        except ImportError:
            logger.warning("API config manager not found")
            self.config_manager = None

        # Security testing configuration
        self.security_config = {
            "timeout": 30,
            "max_retries": 3,
            "user_agent": "SecurityScanner/1.0",
            "rate_limit_test_requests": 100,
            "penetration_test_payloads": self.load_penetration_payloads(),
        }

    def load_compliance_frameworks(self) -> Dict[str, Any]:
        """Load compliance framework definitions"""
        frameworks = {
            "GDPR": {
                "name": "General Data Protection Regulation",
                "region": "EU",
                "requirements": {
                    "data_minimization": "Collect only necessary personal data",
                    "consent_management": "Obtain explicit consent for data processing",
                    "right_to_erasure": "Implement data deletion capabilities",
                    "data_portability": "Enable data export functionality",
                    "breach_notification": "Report breaches within 72 hours",
                    "privacy_by_design": "Implement privacy controls by default",
                    "dpo_appointment": "Appoint Data Protection Officer if required",
                    "impact_assessment": "Conduct privacy impact assessments",
                },
            },
            "CCPA": {
                "name": "California Consumer Privacy Act",
                "region": "California, US",
                "requirements": {
                    "disclosure_notice": "Provide clear privacy notices",
                    "opt_out_rights": "Enable opt-out of data sales",
                    "access_rights": "Provide data access to consumers",
                    "deletion_rights": "Enable data deletion requests",
                    "non_discrimination": "No discrimination for privacy choices",
                    "third_party_disclosure": "Disclose third-party data sharing",
                },
            },
            "SOC2": {
                "name": "Service Organization Control 2",
                "region": "US",
                "requirements": {
                    "security_controls": "Implement comprehensive security controls",
                    "availability_monitoring": "Monitor system availability",
                    "processing_integrity": "Ensure data processing accuracy",
                    "confidentiality_protection": "Protect confidential information",
                    "privacy_safeguards": "Implement privacy protection measures",
                },
            },
            "HIPAA": {
                "name": "Health Insurance Portability and Accountability Act",
                "region": "US",
                "requirements": {
                    "administrative_safeguards": "Implement administrative controls",
                    "physical_safeguards": "Secure physical access to systems",
                    "technical_safeguards": "Implement technical security measures",
                    "breach_notification": "Report breaches to authorities",
                    "business_associate": "Manage business associate agreements",
                    "minimum_necessary": "Limit data access to minimum necessary",
                },
            },
            "PCI_DSS": {
                "name": "Payment Card Industry Data Security Standard",
                "region": "Global",
                "requirements": {
                    "firewall_configuration": "Maintain secure firewall configuration",
                    "default_passwords": "Change default passwords and security parameters",
                    "cardholder_data": "Protect stored cardholder data",
                    "data_transmission": "Encrypt cardholder data transmission",
                    "antivirus_software": "Use and maintain antivirus software",
                    "secure_systems": "Develop and maintain secure systems",
                    "access_control": "Restrict access to cardholder data",
                    "unique_ids": "Assign unique ID to each person with access",
                    "physical_access": "Restrict physical access to cardholder data",
                    "network_monitoring": "Track and monitor access to network resources",
                    "security_testing": "Regularly test security systems and processes",
                    "information_security": "Maintain information security policy",
                },
            },
        }

        return frameworks

    def load_penetration_payloads(self) -> Dict[str, List[str]]:
        """Load penetration testing payloads"""
        return {
            "sql_injection": [
                "' OR '1'='1",
                "'; DROP TABLE users; --",
                "' UNION SELECT * FROM users --",
                "admin'--",
                "' OR 1=1#",
            ],
            "xss": [
                "<script>alert('XSS')</script>",
                "javascript:alert('XSS')",
                "<img src=x onerror=alert('XSS')>",
                "<svg onload=alert('XSS')>",
                "'><script>alert('XSS')</script>",
            ],
            "command_injection": [
                "; ls -la",
                "| whoami",
                "&& cat /etc/passwd",
                "`id`",
                "$(whoami)",
            ],
            "path_traversal": [
                "../../../etc/passwd",
                "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
                "....//....//....//etc/passwd",
                "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            ],
            "ldap_injection": [
                "*)(uid=*))(|(uid=*",
                "*)(|(password=*))",
                "admin)(&(password=*))",
                "*))%00",
            ],
        }

    async def scan_api_security(
        self, api_key: str, api_config: Dict[str, Any]
    ) -> SecurityTestResult:
        """Comprehensive security scan for a single API"""
        logger.info(f"Starting security scan for {api_key}")

        start_time = datetime.now()
        vulnerabilities = []
        compliance_status = []

        # Initialize result structure
        result = SecurityTestResult(
            api_name=api_config.get("name", api_key),
            api_key=api_key,
            test_timestamp=start_time.isoformat(),
            overall_score=0.0,
            security_grade="F",
            vulnerabilities=[],
            compliance_status=[],
            ssl_certificate={},
            authentication_security={},
            rate_limiting={},
            data_privacy={},
            penetration_test={},
            recommendations=[],
            next_scan_date=(start_time + timedelta(days=30)).isoformat(),
        )

        try:
            # 1. SSL/TLS Certificate Analysis
            result.ssl_certificate = await self.analyze_ssl_certificate(api_config)

            # 2. Authentication Security Testing
            result.authentication_security = await self.test_authentication_security(
                api_config
            )

            # 3. Rate Limiting Validation
            result.rate_limiting = await self.test_rate_limiting(api_config)

            # 4. Data Privacy Assessment
            result.data_privacy = await self.assess_data_privacy(api_config)

            # 5. Penetration Testing
            result.penetration_test = await self.conduct_penetration_test(api_config)

            # 6. Compliance Validation
            result.compliance_status = await self.validate_compliance(api_config)

            # 7. Vulnerability Assessment
            result.vulnerabilities = await self.assess_vulnerabilities(api_config)

            # 8. Calculate overall score and grade
            result.overall_score = self.calculate_security_score(result)
            result.security_grade = self.calculate_security_grade(result.overall_score)

            # 9. Generate recommendations
            result.recommendations = self.generate_security_recommendations(result)

            # Save result
            self.security_results[api_key] = result
            await self.save_security_result(result)

            logger.info(
                f"Security scan completed for {api_key}: Grade {result.security_grade} ({result.overall_score:.1f}/100)"
            )

        except Exception as e:
            logger.error(f"Security scan failed for {api_key}: {e}")
            result.vulnerabilities.append(
                SecurityVulnerability(
                    severity="high",
                    category="scan_error",
                    description=f"Security scan failed: {str(e)}",
                    recommendation="Investigate scan failure and retry",
                    cve_id=None,
                    affected_endpoints=["all"],
                    remediation_effort="medium",
                    compliance_impact=["all"],
                )
            )

        return result

    async def analyze_ssl_certificate(
        self, api_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze SSL/TLS certificate security"""
        base_url = api_config.get("base_url", "")
        if not base_url:
            return {"status": "no_url", "score": 0}

        try:
            parsed_url = urlparse(base_url)
            hostname = parsed_url.hostname
            port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)

            if parsed_url.scheme != "https":
                return {
                    "status": "no_ssl",
                    "score": 0,
                    "issues": ["API does not use HTTPS"],
                    "recommendations": ["Enable HTTPS/SSL encryption"],
                }

            # Get certificate
            context = ssl.create_default_context()
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert_der = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()

            # Parse certificate
            cert = x509.load_der_x509_certificate(cert_der, default_backend())

            # Analyze certificate
            analysis = {
                "status": "valid",
                "score": 100,
                "issuer": cert_info.get("issuer", []),
                "subject": cert_info.get("subject", []),
                "serial_number": str(cert.serial_number),
                "not_before": cert.not_valid_before.isoformat(),
                "not_after": cert.not_valid_after.isoformat(),
                "signature_algorithm": cert.signature_algorithm_oid._name,
                "public_key_size": cert.public_key().key_size,
                "san_domains": [],
                "issues": [],
                "recommendations": [],
            }

            # Check expiration
            days_until_expiry = (cert.not_valid_after - datetime.now()).days
            if days_until_expiry < 0:
                analysis["issues"].append("Certificate has expired")
                analysis["score"] -= 50
            elif days_until_expiry < 30:
                analysis["issues"].append(
                    f"Certificate expires in {days_until_expiry} days"
                )
                analysis["score"] -= 20
                analysis["recommendations"].append("Renew SSL certificate soon")

            # Check key size
            if analysis["public_key_size"] < 2048:
                analysis["issues"].append(
                    f'Weak key size: {analysis["public_key_size"]} bits'
                )
                analysis["score"] -= 30
                analysis["recommendations"].append("Use at least 2048-bit RSA keys")

            # Check signature algorithm
            weak_algorithms = ["sha1", "md5"]
            if any(
                alg in analysis["signature_algorithm"].lower()
                for alg in weak_algorithms
            ):
                analysis["issues"].append(
                    f'Weak signature algorithm: {analysis["signature_algorithm"]}'
                )
                analysis["score"] -= 25
                analysis["recommendations"].append(
                    "Use SHA-256 or stronger signature algorithm"
                )

            # Extract SAN domains
            try:
                san_extension = cert.extensions.get_extension_for_oid(
                    x509.oid.ExtensionOID.SUBJECT_ALTERNATIVE_NAME
                )
                analysis["san_domains"] = [name.value for name in san_extension.value]
            except x509.ExtensionNotFound:
                pass

            return analysis

        except Exception as e:
            return {
                "status": "error",
                "score": 0,
                "error": str(e),
                "issues": [f"SSL analysis failed: {str(e)}"],
                "recommendations": ["Investigate SSL configuration"],
            }

    async def test_authentication_security(
        self, api_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Test API authentication security"""
        auth_methods = api_config.get("auth_methods", ["api_key"])
        base_url = api_config.get("base_url", "")

        analysis = {
            "methods": auth_methods,
            "score": 0,
            "issues": [],
            "recommendations": [],
            "tests": {},
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                # Test 1: No authentication
                analysis["tests"]["no_auth"] = await self.test_no_auth_access(
                    session, base_url
                )

                # Test 2: Invalid credentials
                analysis["tests"]["invalid_creds"] = (
                    await self.test_invalid_credentials(session, base_url, auth_methods)
                )

                # Test 3: Brute force protection
                analysis["tests"]["brute_force"] = (
                    await self.test_brute_force_protection(
                        session, base_url, auth_methods
                    )
                )

                # Test 4: Token security
                if "bearer" in auth_methods or "jwt" in auth_methods:
                    analysis["tests"]["token_security"] = (
                        await self.test_token_security(session, base_url)
                    )

                # Calculate score based on test results
                total_tests = len(analysis["tests"])
                passed_tests = sum(
                    1
                    for test in analysis["tests"].values()
                    if test.get("passed", False)
                )
                analysis["score"] = (
                    (passed_tests / total_tests * 100) if total_tests > 0 else 0
                )

                # Generate recommendations
                if analysis["tests"]["no_auth"].get("vulnerable", False):
                    analysis["issues"].append("API allows unauthenticated access")
                    analysis["recommendations"].append(
                        "Implement proper authentication"
                    )

                if analysis["tests"]["brute_force"].get("vulnerable", False):
                    analysis["issues"].append("No brute force protection detected")
                    analysis["recommendations"].append(
                        "Implement rate limiting and account lockout"
                    )

        except Exception as e:
            analysis["error"] = str(e)
            analysis["issues"].append(f"Authentication testing failed: {str(e)}")

        return analysis

    async def test_no_auth_access(
        self, session: aiohttp.ClientSession, base_url: str
    ) -> Dict[str, Any]:
        """Test if API allows access without authentication"""
        test_endpoints = ["/api/users", "/api/data", "/api/admin", "/health", "/status"]

        results = {
            "passed": True,
            "vulnerable": False,
            "accessible_endpoints": [],
            "protected_endpoints": [],
        }

        for endpoint in test_endpoints:
            try:
                url = urljoin(base_url, endpoint)
                async with session.get(url) as response:
                    if response.status == 200:
                        results["accessible_endpoints"].append(endpoint)
                        results["vulnerable"] = True
                        results["passed"] = False
                    else:
                        results["protected_endpoints"].append(endpoint)
            except Exception:
                results["protected_endpoints"].append(endpoint)

        return results

    async def test_invalid_credentials(
        self, session: aiohttp.ClientSession, base_url: str, auth_methods: List[str]
    ) -> Dict[str, Any]:
        """Test API response to invalid credentials"""
        results = {"passed": True, "tests": {}}

        test_endpoints = ["/api/login", "/api/auth", "/oauth/token"]

        for method in auth_methods:
            method_results = {"responses": [], "secure": True}

            for endpoint in test_endpoints:
                try:
                    url = urljoin(base_url, endpoint)

                    if method == "api_key":
                        headers = {"Authorization": "Bearer invalid_key_12345"}
                        async with session.get(url, headers=headers) as response:
                            method_results["responses"].append(
                                {
                                    "endpoint": endpoint,
                                    "status": response.status,
                                    "headers": dict(response.headers),
                                }
                            )

                    elif method == "basic":
                        headers = {
                            "Authorization": "Basic aW52YWxpZDppbnZhbGlk"
                        }  # invalid:invalid
                        async with session.get(url, headers=headers) as response:
                            method_results["responses"].append(
                                {
                                    "endpoint": endpoint,
                                    "status": response.status,
                                    "headers": dict(response.headers),
                                }
                            )

                    # Check for information disclosure
                    if response.status == 200:
                        method_results["secure"] = False
                        results["passed"] = False

                except Exception as e:
                    method_results["responses"].append(
                        {"endpoint": endpoint, "error": str(e)}
                    )

            results["tests"][method] = method_results

        return results

    async def test_brute_force_protection(
        self, session: aiohttp.ClientSession, base_url: str, auth_methods: List[str]
    ) -> Dict[str, Any]:
        """Test brute force protection mechanisms"""
        results = {
            "passed": True,
            "vulnerable": False,
            "rate_limited": False,
            "attempts": [],
        }

        login_endpoint = urljoin(base_url, "/api/login")

        # Attempt multiple failed logins
        for i in range(10):
            try:
                data = {"username": "testuser", "password": f"wrongpassword{i}"}

                start_time = time.time()
                async with session.post(login_endpoint, json=data) as response:
                    end_time = time.time()

                    attempt_result = {
                        "attempt": i + 1,
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "headers": dict(response.headers),
                    }

                    results["attempts"].append(attempt_result)

                    # Check for rate limiting indicators
                    if response.status == 429 or "rate-limit" in response.headers:
                        results["rate_limited"] = True
                        break

                    # Check for increasing response times (potential rate limiting)
                    if (
                        i > 0
                        and attempt_result["response_time"]
                        > results["attempts"][0]["response_time"] * 2
                    ):
                        results["rate_limited"] = True

            except Exception as e:
                results["attempts"].append({"attempt": i + 1, "error": str(e)})

        if not results["rate_limited"]:
            results["vulnerable"] = True
            results["passed"] = False

        return results

    async def test_token_security(
        self, session: aiohttp.ClientSession, base_url: str
    ) -> Dict[str, Any]:
        """Test JWT/Bearer token security"""
        results = {"passed": True, "issues": [], "tests": {}}

        # Test weak/predictable tokens
        weak_tokens = ["token123", "abc123", "12345", "admin", "test"]

        test_endpoint = urljoin(base_url, "/api/user")

        for token in weak_tokens:
            try:
                headers = {"Authorization": f"Bearer {token}"}
                async with session.get(test_endpoint, headers=headers) as response:
                    if response.status == 200:
                        results["issues"].append(f"Weak token accepted: {token}")
                        results["passed"] = False
            except Exception:
                pass

        # Test token format validation
        malformed_tokens = [
            "Bearer",
            "Bearer ",
            "Bearer invalid.token.format",
            "NotBearer validtoken",
        ]

        for token in malformed_tokens:
            try:
                headers = {"Authorization": token}
                async with session.get(test_endpoint, headers=headers) as response:
                    if response.status == 200:
                        results["issues"].append(f"Malformed token accepted: {token}")
                        results["passed"] = False
            except Exception:
                pass

        return results

    async def test_rate_limiting(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test API rate limiting implementation"""
        base_url = api_config.get("base_url", "")
        rate_limits = api_config.get("rate_limits", {})

        analysis = {
            "configured_limits": rate_limits,
            "score": 0,
            "implemented": False,
            "effective": False,
            "bypass_attempts": [],
            "recommendations": [],
        }

        if not base_url:
            analysis["recommendations"].append(
                "Configure base URL for rate limit testing"
            )
            return analysis

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=60)
            ) as session:
                test_endpoint = urljoin(base_url, "/api/test")

                # Test 1: Rapid requests
                rapid_test = await self.test_rapid_requests(session, test_endpoint)
                analysis["rapid_requests"] = rapid_test

                if rapid_test.get("rate_limited", False):
                    analysis["implemented"] = True
                    analysis["score"] += 40

                # Test 2: Different IP addresses (if possible)
                ip_test = await self.test_ip_based_limiting(session, test_endpoint)
                analysis["ip_based"] = ip_test

                if ip_test.get("effective", False):
                    analysis["effective"] = True
                    analysis["score"] += 30

                # Test 3: User-based limiting
                user_test = await self.test_user_based_limiting(session, test_endpoint)
                analysis["user_based"] = user_test

                if user_test.get("effective", False):
                    analysis["score"] += 30

                # Generate recommendations
                if not analysis["implemented"]:
                    analysis["recommendations"].append(
                        "Implement rate limiting to prevent abuse"
                    )

                if analysis["implemented"] and not analysis["effective"]:
                    analysis["recommendations"].append(
                        "Improve rate limiting effectiveness"
                    )

        except Exception as e:
            analysis["error"] = str(e)
            analysis["recommendations"].append("Fix rate limiting test configuration")

        return analysis

    async def test_rapid_requests(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> Dict[str, Any]:
        """Test rapid request handling"""
        results = {
            "rate_limited": False,
            "requests_sent": 0,
            "responses": [],
            "rate_limit_triggered_at": None,
        }

        # Send rapid requests
        for i in range(self.security_config["rate_limit_test_requests"]):
            try:
                start_time = time.time()
                async with session.get(endpoint) as response:
                    end_time = time.time()

                    response_data = {
                        "request_number": i + 1,
                        "status": response.status,
                        "response_time": end_time - start_time,
                        "headers": dict(response.headers),
                    }

                    results["responses"].append(response_data)
                    results["requests_sent"] += 1

                    # Check for rate limiting
                    if (
                        response.status == 429
                        or "rate-limit" in str(response.headers).lower()
                    ):
                        results["rate_limited"] = True
                        results["rate_limit_triggered_at"] = i + 1
                        break

                    # Small delay to avoid overwhelming the server
                    await asyncio.sleep(0.01)

            except Exception as e:
                results["responses"].append({"request_number": i + 1, "error": str(e)})
                break

        return results

    async def test_ip_based_limiting(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> Dict[str, Any]:
        """Test IP-based rate limiting"""
        # Note: This is a simplified test as we can't easily change IP addresses
        results = {"effective": False, "test_method": "header_spoofing", "attempts": []}

        # Try different X-Forwarded-For headers
        test_ips = ["192.168.1.1", "10.0.0.1", "172.16.0.1", "203.0.113.1"]

        for ip in test_ips:
            try:
                headers = {"X-Forwarded-For": ip, "X-Real-IP": ip}
                async with session.get(endpoint, headers=headers) as response:
                    results["attempts"].append(
                        {
                            "ip": ip,
                            "status": response.status,
                            "headers": dict(response.headers),
                        }
                    )
            except Exception as e:
                results["attempts"].append({"ip": ip, "error": str(e)})

        # Check if different responses for different IPs
        statuses = [
            attempt.get("status")
            for attempt in results["attempts"]
            if "status" in attempt
        ]
        if len(set(statuses)) > 1:
            results["effective"] = True

        return results

    async def test_user_based_limiting(
        self, session: aiohttp.ClientSession, endpoint: str
    ) -> Dict[str, Any]:
        """Test user-based rate limiting"""
        results = {"effective": False, "test_users": [], "different_limits": False}

        # Test with different user tokens (if available)
        test_tokens = ["user1_token", "user2_token", "admin_token"]

        for token in test_tokens:
            user_results = {"token": token, "requests": [], "rate_limited": False}

            headers = {"Authorization": f"Bearer {token}"}

            # Send multiple requests for this user
            for i in range(20):
                try:
                    async with session.get(endpoint, headers=headers) as response:
                        user_results["requests"].append(
                            {"request": i + 1, "status": response.status}
                        )

                        if response.status == 429:
                            user_results["rate_limited"] = True
                            break

                except Exception:
                    break

            results["test_users"].append(user_results)

        # Check if rate limiting varies by user
        rate_limited_counts = [
            len(user["requests"])
            for user in results["test_users"]
            if user["rate_limited"]
        ]
        if len(set(rate_limited_counts)) > 1:
            results["different_limits"] = True
            results["effective"] = True

        return results

    async def assess_data_privacy(self, api_config: Dict[str, Any]) -> Dict[str, Any]:
        """Assess data privacy and protection measures"""
        analysis = {
            "score": 0,
            "privacy_policy": {"exists": False, "url": None},
            "data_collection": {"minimal": False, "disclosed": False},
            "user_rights": {"access": False, "deletion": False, "portability": False},
            "consent_management": {"implemented": False, "granular": False},
            "data_retention": {"policy_exists": False, "automated_deletion": False},
            "third_party_sharing": {"disclosed": False, "controlled": False},
            "recommendations": [],
        }

        base_url = api_config.get("base_url", "")

        if not base_url:
            analysis["recommendations"].append(
                "Configure base URL for privacy assessment"
            )
            return analysis

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                # Check for privacy policy
                privacy_urls = ["/privacy", "/privacy-policy", "/legal/privacy"]
                for url in privacy_urls:
                    try:
                        full_url = urljoin(base_url, url)
                        async with session.get(full_url) as response:
                            if response.status == 200:
                                analysis["privacy_policy"]["exists"] = True
                                analysis["privacy_policy"]["url"] = full_url
                                analysis["score"] += 20
                                break
                    except Exception:
                        continue

                # Check for data subject rights endpoints
                rights_endpoints = {
                    "access": ["/api/data-access", "/api/user/data"],
                    "deletion": ["/api/delete-account", "/api/user/delete"],
                    "portability": ["/api/export-data", "/api/user/export"],
                }

                for right, endpoints in rights_endpoints.items():
                    for endpoint in endpoints:
                        try:
                            full_url = urljoin(base_url, endpoint)
                            async with session.get(full_url) as response:
                                if response.status in [
                                    200,
                                    401,
                                    403,
                                ]:  # Endpoint exists
                                    analysis["user_rights"][right] = True
                                    analysis["score"] += 15
                                    break
                        except Exception:
                            continue

                # Check for consent management
                consent_endpoints = ["/api/consent", "/api/preferences"]
                for endpoint in consent_endpoints:
                    try:
                        full_url = urljoin(base_url, endpoint)
                        async with session.get(full_url) as response:
                            if response.status in [200, 401, 403]:
                                analysis["consent_management"]["implemented"] = True
                                analysis["score"] += 10
                                break
                    except Exception:
                        continue

                # Generate recommendations
                if not analysis["privacy_policy"]["exists"]:
                    analysis["recommendations"].append(
                        "Create and publish privacy policy"
                    )

                if not any(analysis["user_rights"].values()):
                    analysis["recommendations"].append(
                        "Implement data subject rights endpoints"
                    )

                if not analysis["consent_management"]["implemented"]:
                    analysis["recommendations"].append(
                        "Implement consent management system"
                    )

        except Exception as e:
            analysis["error"] = str(e)
            analysis["recommendations"].append("Fix privacy assessment configuration")

        return analysis

    async def conduct_penetration_test(
        self, api_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Conduct basic penetration testing"""
        analysis = {
            "score": 100,
            "vulnerabilities_found": [],
            "tests_conducted": [],
            "recommendations": [],
        }

        base_url = api_config.get("base_url", "")

        if not base_url:
            analysis["recommendations"].append(
                "Configure base URL for penetration testing"
            )
            return analysis

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:
                # Test each vulnerability category
                for category, payloads in self.security_config[
                    "penetration_test_payloads"
                ].items():
                    test_result = await self.test_vulnerability_category(
                        session, base_url, category, payloads
                    )
                    analysis["tests_conducted"].append(test_result)

                    if test_result.get("vulnerable", False):
                        analysis["vulnerabilities_found"].extend(
                            test_result.get("vulnerabilities", [])
                        )
                        analysis["score"] -= test_result.get("score_impact", 10)

                # Ensure score doesn't go below 0
                analysis["score"] = max(0, analysis["score"])

                # Generate recommendations based on findings
                if analysis["vulnerabilities_found"]:
                    analysis["recommendations"].append(
                        "Address identified security vulnerabilities immediately"
                    )
                    analysis["recommendations"].append(
                        "Implement input validation and sanitization"
                    )
                    analysis["recommendations"].append(
                        "Use parameterized queries to prevent injection attacks"
                    )
                    analysis["recommendations"].append(
                        "Implement proper output encoding"
                    )

        except Exception as e:
            analysis["error"] = str(e)
            analysis["recommendations"].append("Fix penetration testing configuration")

        return analysis

    async def test_vulnerability_category(
        self,
        session: aiohttp.ClientSession,
        base_url: str,
        category: str,
        payloads: List[str],
    ) -> Dict[str, Any]:
        """Test a specific vulnerability category"""
        result = {
            "category": category,
            "vulnerable": False,
            "vulnerabilities": [],
            "score_impact": 0,
            "tested_endpoints": [],
        }

        # Common test endpoints
        test_endpoints = ["/api/search", "/api/user", "/api/data", "/login"]

        for endpoint in test_endpoints:
            for payload in payloads:
                try:
                    full_url = urljoin(base_url, endpoint)

                    # Test different injection points
                    test_cases = [
                        {"params": {"q": payload}},  # Query parameter
                        {"json": {"input": payload}},  # JSON body
                        {"headers": {"X-Test": payload}},  # Header
                    ]

                    for test_case in test_cases:
                        async with session.get(full_url, **test_case) as response:
                            response_text = await response.text()

                            # Check for vulnerability indicators
                            if self.is_vulnerable_response(
                                category, payload, response, response_text
                            ):
                                vulnerability = {
                                    "endpoint": endpoint,
                                    "payload": payload,
                                    "injection_point": list(test_case.keys())[0],
                                    "response_status": response.status,
                                    "evidence": response_text[:200],  # First 200 chars
                                }

                                result["vulnerabilities"].append(vulnerability)
                                result["vulnerable"] = True
                                result["score_impact"] = self.get_vulnerability_impact(
                                    category
                                )

                except Exception:
                    continue  # Continue testing other payloads

            result["tested_endpoints"].append(endpoint)

        return result

    def is_vulnerable_response(
        self,
        category: str,
        payload: str,
        response: aiohttp.ClientResponse,
        response_text: str,
    ) -> bool:
        """Check if response indicates vulnerability"""
        if category == "sql_injection":
            # Look for SQL error messages
            sql_errors = ["sql syntax", "mysql_fetch", "ora-", "postgresql", "sqlite_"]
            return any(error in response_text.lower() for error in sql_errors)

        elif category == "xss":
            # Look for reflected payload
            return payload in response_text

        elif category == "command_injection":
            # Look for command output
            command_indicators = ["uid=", "gid=", "root:", "/bin/", "windows"]
            return any(
                indicator in response_text.lower() for indicator in command_indicators
            )

        elif category == "path_traversal":
            # Look for file contents
            file_indicators = ["root:x:", "[boot loader]", "etc/passwd"]
            return any(
                indicator in response_text.lower() for indicator in file_indicators
            )

        elif category == "ldap_injection":
            # Look for LDAP errors or unexpected data
            ldap_errors = ["ldap", "invalid dn syntax", "bad search filter"]
            return any(error in response_text.lower() for error in ldap_errors)

        return False

    def get_vulnerability_impact(self, category: str) -> int:
        """Get score impact for vulnerability category"""
        impacts = {
            "sql_injection": 30,
            "xss": 20,
            "command_injection": 35,
            "path_traversal": 25,
            "ldap_injection": 20,
        }
        return impacts.get(category, 15)

    async def validate_compliance(
        self, api_config: Dict[str, Any]
    ) -> List[ComplianceRequirement]:
        """Validate compliance with various regulations"""
        compliance_results = []

        # Check each compliance framework
        for framework_name, framework in self.compliance_frameworks.items():
            for req_id, req_description in framework["requirements"].items():
                # Assess compliance for this requirement
                status = await self.assess_compliance_requirement(
                    api_config, framework_name, req_id, req_description
                )

                compliance_results.append(
                    ComplianceRequirement(
                        regulation=framework_name,
                        requirement_id=req_id,
                        description=req_description,
                        status=status["status"],
                        evidence=status["evidence"],
                        remediation_steps=status["remediation_steps"],
                        deadline=status.get("deadline"),
                        risk_level=status["risk_level"],
                    )
                )

        return compliance_results

    async def assess_compliance_requirement(
        self, api_config: Dict[str, Any], framework: str, req_id: str, description: str
    ) -> Dict[str, Any]:
        """Assess a specific compliance requirement"""
        # This is a simplified assessment - in practice, this would be much more detailed
        assessment = {
            "status": "unknown",
            "evidence": [],
            "remediation_steps": [],
            "risk_level": "medium",
        }

        # GDPR-specific assessments
        if framework == "GDPR":
            if req_id == "data_minimization":
                # Check if API collects minimal data
                if api_config.get("data_collection", {}).get("minimal", False):
                    assessment["status"] = "compliant"
                    assessment["evidence"].append(
                        "API configured for minimal data collection"
                    )
                else:
                    assessment["status"] = "non_compliant"
                    assessment["remediation_steps"].append(
                        "Review and minimize data collection"
                    )

            elif req_id == "consent_management":
                # Check for consent endpoints
                if api_config.get("consent_endpoints", False):
                    assessment["status"] = "compliant"
                    assessment["evidence"].append(
                        "Consent management endpoints available"
                    )
                else:
                    assessment["status"] = "non_compliant"
                    assessment["remediation_steps"].append(
                        "Implement consent management system"
                    )

        # SOC2-specific assessments
        elif framework == "SOC2":
            if req_id == "security_controls":
                # Check security score
                security_score = api_config.get("security_score", 0)
                if security_score >= 80:
                    assessment["status"] = "compliant"
                    assessment["evidence"].append(
                        f"Security score: {security_score}/100"
                    )
                else:
                    assessment["status"] = "partial"
                    assessment["remediation_steps"].append("Improve security controls")

        # PCI DSS-specific assessments
        elif framework == "PCI_DSS":
            if req_id == "data_transmission":
                # Check SSL/TLS
                if api_config.get("ssl_enabled", False):
                    assessment["status"] = "compliant"
                    assessment["evidence"].append("SSL/TLS encryption enabled")
                else:
                    assessment["status"] = "non_compliant"
                    assessment["remediation_steps"].append("Enable SSL/TLS encryption")
                    assessment["risk_level"] = "high"

        return assessment

    async def assess_vulnerabilities(
        self, api_config: Dict[str, Any]
    ) -> List[SecurityVulnerability]:
        """Assess security vulnerabilities"""
        vulnerabilities = []

        # Check for common vulnerabilities based on configuration

        # 1. Weak authentication
        auth_methods = api_config.get("auth_methods", [])
        if not auth_methods or "none" in auth_methods:
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="high",
                    category="authentication",
                    description="No authentication mechanism configured",
                    recommendation="Implement strong authentication (OAuth2, JWT, API keys)",
                    cve_id=None,
                    affected_endpoints=["all"],
                    remediation_effort="medium",
                    compliance_impact=["GDPR", "SOC2", "HIPAA"],
                )
            )

        # 2. Missing HTTPS
        base_url = api_config.get("base_url", "")
        if base_url and not base_url.startswith("https://"):
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="high",
                    category="encryption",
                    description="API does not use HTTPS encryption",
                    recommendation="Enable HTTPS/SSL encryption for all endpoints",
                    cve_id=None,
                    affected_endpoints=["all"],
                    remediation_effort="low",
                    compliance_impact=["PCI_DSS", "HIPAA", "SOC2"],
                )
            )

        # 3. No rate limiting
        rate_limits = api_config.get("rate_limits", {})
        if not rate_limits:
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="medium",
                    category="availability",
                    description="No rate limiting configured",
                    recommendation="Implement rate limiting to prevent abuse and DoS attacks",
                    cve_id=None,
                    affected_endpoints=["all"],
                    remediation_effort="medium",
                    compliance_impact=["SOC2"],
                )
            )

        # 4. Weak API key format
        api_key_format = api_config.get("api_key_format", "")
        if api_key_format and len(api_key_format) < 32:
            vulnerabilities.append(
                SecurityVulnerability(
                    severity="medium",
                    category="authentication",
                    description="API keys may be too short or predictable",
                    recommendation="Use cryptographically secure, long API keys (32+ characters)",
                    cve_id=None,
                    affected_endpoints=["authenticated"],
                    remediation_effort="low",
                    compliance_impact=["SOC2"],
                )
            )

        return vulnerabilities

    def calculate_security_score(self, result: SecurityTestResult) -> float:
        """Calculate overall security score"""
        scores = []

        # SSL Certificate score
        ssl_score = result.ssl_certificate.get("score", 0)
        scores.append(ssl_score * 0.2)  # 20% weight

        # Authentication security score
        auth_score = result.authentication_security.get("score", 0)
        scores.append(auth_score * 0.25)  # 25% weight

        # Rate limiting score
        rate_score = result.rate_limiting.get("score", 0)
        scores.append(rate_score * 0.15)  # 15% weight

        # Data privacy score
        privacy_score = result.data_privacy.get("score", 0)
        scores.append(privacy_score * 0.15)  # 15% weight

        # Penetration test score
        pentest_score = result.penetration_test.get("score", 0)
        scores.append(pentest_score * 0.25)  # 25% weight

        # Calculate weighted average
        total_score = sum(scores)

        # Apply vulnerability penalties
        for vuln in result.vulnerabilities:
            if vuln.severity == "critical":
                total_score -= 20
            elif vuln.severity == "high":
                total_score -= 10
            elif vuln.severity == "medium":
                total_score -= 5
            elif vuln.severity == "low":
                total_score -= 2

        return max(0, min(100, total_score))

    def calculate_security_grade(self, score: float) -> str:
        """Calculate security grade based on score"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "A-"
        elif score >= 80:
            return "B+"
        elif score >= 75:
            return "B"
        elif score >= 70:
            return "B-"
        elif score >= 65:
            return "C+"
        elif score >= 60:
            return "C"
        elif score >= 55:
            return "C-"
        elif score >= 50:
            return "D"
        else:
            return "F"

    def generate_security_recommendations(
        self, result: SecurityTestResult
    ) -> List[str]:
        """Generate security recommendations based on test results"""
        recommendations = []

        # SSL/TLS recommendations
        ssl_issues = result.ssl_certificate.get("issues", [])
        if ssl_issues:
            recommendations.extend(result.ssl_certificate.get("recommendations", []))

        # Authentication recommendations
        auth_issues = result.authentication_security.get("issues", [])
        if auth_issues:
            recommendations.extend(
                result.authentication_security.get("recommendations", [])
            )

        # Rate limiting recommendations
        rate_recommendations = result.rate_limiting.get("recommendations", [])
        recommendations.extend(rate_recommendations)

        # Privacy recommendations
        privacy_recommendations = result.data_privacy.get("recommendations", [])
        recommendations.extend(privacy_recommendations)

        # Penetration test recommendations
        pentest_recommendations = result.penetration_test.get("recommendations", [])
        recommendations.extend(pentest_recommendations)

        # Vulnerability-based recommendations
        for vuln in result.vulnerabilities:
            recommendations.append(vuln.recommendation)

        # Compliance recommendations
        for compliance in result.compliance_status:
            if compliance.status in ["non_compliant", "partial"]:
                recommendations.extend(compliance.remediation_steps)

        # Remove duplicates and return
        return list(set(recommendations))

    async def save_security_result(self, result: SecurityTestResult):
        """Save security test result to disk"""
        result_file = self.results_dir / f"{result.api_key}_security_result.json"

        try:
            # Convert dataclass to dict for JSON serialization
            result_dict = asdict(result)

            with open(result_file, "w") as f:
                json.dump(result_dict, f, indent=2, default=str)

            logger.info(f"Saved security result for {result.api_key}")

        except Exception as e:
            logger.error(f"Failed to save security result for {result.api_key}: {e}")

    async def generate_compliance_report(
        self, apis: List[str] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        if apis is None:
            apis = list(self.security_results.keys())

        report = {
            "generated_at": datetime.now().isoformat(),
            "apis_assessed": len(apis),
            "overall_compliance": {},
            "framework_compliance": {},
            "critical_issues": [],
            "recommendations": [],
            "api_details": {},
        }

        # Analyze compliance across all APIs
        framework_stats = {}

        for api_key in apis:
            if api_key not in self.security_results:
                continue

            result = self.security_results[api_key]
            report["api_details"][api_key] = {
                "security_grade": result.security_grade,
                "overall_score": result.overall_score,
                "critical_vulnerabilities": len(
                    [v for v in result.vulnerabilities if v.severity == "critical"]
                ),
                "compliance_issues": len(
                    [c for c in result.compliance_status if c.status == "non_compliant"]
                ),
            }

            # Aggregate framework compliance
            for compliance in result.compliance_status:
                framework = compliance.regulation
                if framework not in framework_stats:
                    framework_stats[framework] = {
                        "total_requirements": 0,
                        "compliant": 0,
                        "non_compliant": 0,
                        "partial": 0,
                        "unknown": 0,
                    }

                framework_stats[framework]["total_requirements"] += 1
                framework_stats[framework][compliance.status] += 1

            # Collect critical issues
            for vuln in result.vulnerabilities:
                if vuln.severity == "critical":
                    report["critical_issues"].append(
                        {
                            "api": api_key,
                            "vulnerability": vuln.description,
                            "recommendation": vuln.recommendation,
                        }
                    )

        # Calculate framework compliance percentages
        for framework, stats in framework_stats.items():
            compliance_rate = (
                (stats["compliant"] / stats["total_requirements"] * 100)
                if stats["total_requirements"] > 0
                else 0
            )
            report["framework_compliance"][framework] = {
                "compliance_rate": compliance_rate,
                "status": (
                    "compliant"
                    if compliance_rate >= 90
                    else "partial" if compliance_rate >= 70 else "non_compliant"
                ),
                **stats,
            }

        # Overall compliance score
        if framework_stats:
            overall_compliance_rate = sum(
                fc["compliance_rate"] for fc in report["framework_compliance"].values()
            ) / len(report["framework_compliance"])
            report["overall_compliance"] = {
                "rate": overall_compliance_rate,
                "status": (
                    "compliant"
                    if overall_compliance_rate >= 90
                    else "partial" if overall_compliance_rate >= 70 else "non_compliant"
                ),
            }

        # Generate top recommendations
        all_recommendations = []
        for api_key in apis:
            if api_key in self.security_results:
                all_recommendations.extend(
                    self.security_results[api_key].recommendations
                )

        # Count recommendation frequency
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

        # Top 10 most common recommendations
        report["recommendations"] = sorted(
            recommendation_counts.items(), key=lambda x: x[1], reverse=True
        )[:10]

        return report

    async def scan_all_apis(
        self, parallel: bool = True, max_workers: int = 5
    ) -> Dict[str, SecurityTestResult]:
        """Scan all configured APIs for security and compliance"""
        if not self.config_manager:
            logger.error("API config manager not available")
            return {}

        api_configs = self.config_manager.api_configs

        if parallel:
            # Parallel scanning
            semaphore = asyncio.Semaphore(max_workers)

            async def scan_with_semaphore(api_key, config):
                async with semaphore:
                    return await self.scan_api_security(api_key, asdict(config))

            tasks = [
                scan_with_semaphore(api_key, config)
                for api_key, config in api_configs.items()
                if config.is_configured
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    api_key = list(api_configs.keys())[i]
                    logger.error(f"Scan failed for {api_key}: {result}")
                else:
                    self.security_results[result.api_key] = result

        else:
            # Sequential scanning
            for api_key, config in api_configs.items():
                if config.is_configured:
                    try:
                        result = await self.scan_api_security(api_key, asdict(config))
                        self.security_results[result.api_key] = result
                    except Exception as e:
                        logger.error(f"Scan failed for {api_key}: {e}")

        return self.security_results

    def interactive_menu(self):
        """Interactive security and compliance management menu"""
        while True:
            print("\n🔒 API Security & Compliance Validator")
            print("=" * 50)
            print("1. 🔍 Scan single API")
            print("2. 🔍 Scan all APIs")
            print("3. 📊 View security results")
            print("4. 📋 Generate compliance report")
            print("5. 🛡️  View vulnerabilities")
            print("6. ⚖️  Check compliance status")
            print("7. 💡 Security recommendations")
            print("8. 📄 Export security report")
            print("9. ⚙️  Configure security settings")
            print("10. ❌ Exit")

            choice = input("\nSelect option (1-10): ").strip()

            if choice == "1":
                asyncio.run(self.interactive_scan_single_api())
            elif choice == "2":
                asyncio.run(self.interactive_scan_all_apis())
            elif choice == "3":
                self.show_security_results()
            elif choice == "4":
                asyncio.run(self.interactive_compliance_report())
            elif choice == "5":
                self.show_vulnerabilities()
            elif choice == "6":
                self.show_compliance_status()
            elif choice == "7":
                self.show_security_recommendations()
            elif choice == "8":
                asyncio.run(self.interactive_export_report())
            elif choice == "9":
                self.configure_security_settings()
            elif choice == "10":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please try again.")

    async def interactive_scan_single_api(self):
        """Interactive single API security scan"""
        if not self.config_manager:
            print("❌ API config manager not available")
            return

        api_configs = self.config_manager.api_configs
        configured_apis = [
            key for key, config in api_configs.items() if config.is_configured
        ]

        if not configured_apis:
            print("❌ No configured APIs found")
            return

        print("\n📋 Available APIs:")
        for i, api_key in enumerate(configured_apis, 1):
            print(f"{i}. {api_key}")

        try:
            choice = int(input("\nSelect API to scan (number): ")) - 1
            if 0 <= choice < len(configured_apis):
                api_key = configured_apis[choice]
                config = api_configs[api_key]

                print(f"\n🔍 Scanning {api_key}...")
                result = await self.scan_api_security(api_key, asdict(config))

                print(f"\n✅ Scan completed!")
                print(f"Security Grade: {result.security_grade}")
                print(f"Overall Score: {result.overall_score:.1f}/100")
                print(f"Vulnerabilities: {len(result.vulnerabilities)}")
                print(
                    f"Compliance Issues: {len([c for c in result.compliance_status if c.status == 'non_compliant'])}"
                )
            else:
                print("❌ Invalid selection")
        except ValueError:
            print("❌ Invalid input")

    async def interactive_scan_all_apis(self):
        """Interactive all APIs security scan"""
        print("\n🔍 Scanning all configured APIs...")

        parallel = input("Use parallel scanning? (y/n): ").lower().startswith("y")

        if parallel:
            try:
                max_workers = int(
                    input("Max parallel workers (1-10, default 5): ") or "5"
                )
                max_workers = max(1, min(10, max_workers))
            except ValueError:
                max_workers = 5
        else:
            max_workers = 1

        results = await self.scan_all_apis(parallel=parallel, max_workers=max_workers)

        print(f"\n✅ Scan completed! Processed {len(results)} APIs")

        # Summary statistics
        grades = [result.security_grade for result in results.values()]
        avg_score = (
            sum(result.overall_score for result in results.values()) / len(results)
            if results
            else 0
        )

        print(f"Average Security Score: {avg_score:.1f}/100")
        print(
            f"Grade Distribution: {dict(zip(*np.unique(grades, return_counts=True))) if grades else 'None'}"
        )

    def show_security_results(self):
        """Display security scan results"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n🔒 Security Scan Results")
        print("=" * 60)

        for api_key, result in self.security_results.items():
            print(f"\n📊 {api_key}")
            print(f"   Grade: {result.security_grade} ({result.overall_score:.1f}/100)")
            print(f"   Vulnerabilities: {len(result.vulnerabilities)}")
            print(f"   Last Scan: {result.test_timestamp[:19]}")

            # Show critical vulnerabilities
            critical_vulns = [
                v for v in result.vulnerabilities if v.severity == "critical"
            ]
            if critical_vulns:
                print(f"   ⚠️  Critical Issues: {len(critical_vulns)}")

    async def interactive_compliance_report(self):
        """Interactive compliance report generation"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n📋 Generating compliance report...")

        apis = list(self.security_results.keys())
        report = await self.generate_compliance_report(apis)

        print(f"\n📊 Compliance Report")
        print("=" * 50)
        print(f"APIs Assessed: {report['apis_assessed']}")
        print(f"Overall Compliance: {report['overall_compliance'].get('rate', 0):.1f}%")

        print("\n🏛️ Framework Compliance:")
        for framework, stats in report["framework_compliance"].items():
            status_emoji = (
                "✅"
                if stats["status"] == "compliant"
                else "⚠️" if stats["status"] == "partial" else "❌"
            )
            print(f"   {status_emoji} {framework}: {stats['compliance_rate']:.1f}%")

        if report["critical_issues"]:
            print(f"\n🚨 Critical Issues ({len(report['critical_issues'])})")
            for issue in report["critical_issues"][:5]:  # Show first 5
                print(f"   • {issue['api']}: {issue['vulnerability']}")

        # Save report
        report_file = (
            self.reports_dir
            / f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n💾 Report saved to: {report_file}")

    def show_vulnerabilities(self):
        """Display vulnerability summary"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n🛡️ Vulnerability Summary")
        print("=" * 50)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        all_vulnerabilities = []

        for api_key, result in self.security_results.items():
            for vuln in result.vulnerabilities:
                severity_counts[vuln.severity] += 1
                all_vulnerabilities.append((api_key, vuln))

        print(f"Total Vulnerabilities: {len(all_vulnerabilities)}")
        print(f"🔴 Critical: {severity_counts['critical']}")
        print(f"🟠 High: {severity_counts['high']}")
        print(f"🟡 Medium: {severity_counts['medium']}")
        print(f"🟢 Low: {severity_counts['low']}")

        # Show critical vulnerabilities
        critical_vulns = [
            (api, vuln)
            for api, vuln in all_vulnerabilities
            if vuln.severity == "critical"
        ]
        if critical_vulns:
            print("\n🚨 Critical Vulnerabilities:")
            for api_key, vuln in critical_vulns[:10]:  # Show first 10
                print(f"   • {api_key}: {vuln.description}")

    def show_compliance_status(self):
        """Display compliance status summary"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n⚖️ Compliance Status Summary")
        print("=" * 50)

        framework_stats = {}

        for api_key, result in self.security_results.items():
            for compliance in result.compliance_status:
                framework = compliance.regulation
                if framework not in framework_stats:
                    framework_stats[framework] = {
                        "compliant": 0,
                        "non_compliant": 0,
                        "partial": 0,
                        "total": 0,
                    }

                framework_stats[framework][compliance.status] += 1
                framework_stats[framework]["total"] += 1

        for framework, stats in framework_stats.items():
            compliance_rate = (
                (stats["compliant"] / stats["total"] * 100) if stats["total"] > 0 else 0
            )
            status_emoji = (
                "✅"
                if compliance_rate >= 90
                else "⚠️" if compliance_rate >= 70 else "❌"
            )

            print(f"\n{status_emoji} {framework}")
            print(f"   Compliance Rate: {compliance_rate:.1f}%")
            print(f"   Compliant: {stats['compliant']}/{stats['total']}")
            print(f"   Non-Compliant: {stats['non_compliant']}")
            print(f"   Partial: {stats['partial']}")

    def show_security_recommendations(self):
        """Display security recommendations"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n💡 Security Recommendations")
        print("=" * 50)

        all_recommendations = []
        for result in self.security_results.values():
            all_recommendations.extend(result.recommendations)

        # Count recommendation frequency
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1

        # Sort by frequency
        sorted_recommendations = sorted(
            recommendation_counts.items(), key=lambda x: x[1], reverse=True
        )

        print(f"Top {min(15, len(sorted_recommendations))} Recommendations:")
        for i, (recommendation, count) in enumerate(sorted_recommendations[:15], 1):
            print(f"{i:2d}. {recommendation} (affects {count} APIs)")

    async def interactive_export_report(self):
        """Interactive security report export"""
        if not self.security_results:
            print("❌ No security results available. Run a scan first.")
            return

        print("\n📄 Export Security Report")
        print("1. JSON format")
        print("2. CSV format")
        print("3. HTML format")

        choice = input("Select format (1-3): ").strip()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if choice == "1":
            await self.export_json_report(timestamp)
        elif choice == "2":
            await self.export_csv_report(timestamp)
        elif choice == "3":
            await self.export_html_report(timestamp)
        else:
            print("❌ Invalid choice")

    async def export_json_report(self, timestamp: str):
        """Export security report in JSON format"""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_apis": len(self.security_results),
                "average_score": sum(
                    r.overall_score for r in self.security_results.values()
                )
                / len(self.security_results),
                "total_vulnerabilities": sum(
                    len(r.vulnerabilities) for r in self.security_results.values()
                ),
            },
            "results": {
                api_key: asdict(result)
                for api_key, result in self.security_results.items()
            },
        }

        report_file = self.reports_dir / f"security_report_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report_data, f, indent=2, default=str)

        print(f"✅ JSON report exported to: {report_file}")

    async def export_csv_report(self, timestamp: str):
        """Export security report in CSV format"""
        import csv

        report_file = self.reports_dir / f"security_report_{timestamp}.csv"

        with open(report_file, "w", newline="") as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(
                [
                    "API Name",
                    "Security Grade",
                    "Overall Score",
                    "Vulnerabilities",
                    "Critical Vulns",
                    "High Vulns",
                    "Medium Vulns",
                    "Low Vulns",
                    "Compliance Issues",
                    "Last Scan",
                ]
            )

            # Data rows
            for api_key, result in self.security_results.items():
                vuln_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
                for vuln in result.vulnerabilities:
                    vuln_counts[vuln.severity] += 1

                compliance_issues = len(
                    [c for c in result.compliance_status if c.status == "non_compliant"]
                )

                writer.writerow(
                    [
                        api_key,
                        result.security_grade,
                        result.overall_score,
                        len(result.vulnerabilities),
                        vuln_counts["critical"],
                        vuln_counts["high"],
                        vuln_counts["medium"],
                        vuln_counts["low"],
                        compliance_issues,
                        result.test_timestamp[:19],
                    ]
                )

        print(f"✅ CSV report exported to: {report_file}")

    async def export_html_report(self, timestamp: str):
        """Export security report in HTML format"""
        html_content = self.generate_html_report()

        report_file = self.reports_dir / f"security_report_{timestamp}.html"
        with open(report_file, "w") as f:
            f.write(html_content)

        print(f"✅ HTML report exported to: {report_file}")

    def generate_html_report(self) -> str:
        """Generate HTML security report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>API Security & Compliance Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .summary {{ background: #ecf0f1; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .api-result {{ border: 1px solid #bdc3c7; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .grade-A {{ background: #d5f4e6; }}
        .grade-B {{ background: #fef9e7; }}
        .grade-C {{ background: #fdf2e9; }}
        .grade-D {{ background: #fadbd8; }}
        .grade-F {{ background: #f8d7da; }}
        .vulnerability {{ margin: 5px 0; padding: 5px; border-left: 3px solid #e74c3c; }}
        .critical {{ border-left-color: #c0392b; background: #fadbd8; }}
        .high {{ border-left-color: #e67e22; background: #fdeaa7; }}
        .medium {{ border-left-color: #f39c12; background: #fcf3cf; }}
        .low {{ border-left-color: #27ae60; background: #d5f4e6; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 API Security & Compliance Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <p><strong>Total APIs:</strong> {len(self.security_results)}</p>
        <p><strong>Average Score:</strong> {sum(r.overall_score for r in self.security_results.values()) / len(self.security_results):.1f}/100</p>
        <p><strong>Total Vulnerabilities:</strong> {sum(len(r.vulnerabilities) for r in self.security_results.values())}</p>
    </div>
"""

        for api_key, result in self.security_results.items():
            grade_class = f"grade-{result.security_grade[0]}"

            html += f"""
    <div class="api-result {grade_class}">
        <h3>🔧 {api_key}</h3>
        <p><strong>Security Grade:</strong> {result.security_grade} ({result.overall_score:.1f}/100)</p>
        <p><strong>Last Scan:</strong> {result.test_timestamp[:19]}</p>
        
        <h4>🛡️ Vulnerabilities ({len(result.vulnerabilities)})</h4>
"""

            for vuln in result.vulnerabilities[:10]:  # Show first 10
                html += f'<div class="vulnerability {vuln.severity}"><strong>{vuln.severity.upper()}:</strong> {vuln.description}</div>\n'

            html += "</div>\n"

        html += """
</body>
</html>
"""

        return html

    def configure_security_settings(self):
        """Configure security testing settings"""
        print("\n⚙️ Security Settings Configuration")
        print("=" * 40)

        print(f"Current timeout: {self.security_config['timeout']}s")
        new_timeout = input(
            "New timeout (seconds, press Enter to keep current): "
        ).strip()
        if new_timeout.isdigit():
            self.security_config["timeout"] = int(new_timeout)

        print(f"Current max retries: {self.security_config['max_retries']}")
        new_retries = input("New max retries (press Enter to keep current): ").strip()
        if new_retries.isdigit():
            self.security_config["max_retries"] = int(new_retries)

        print(
            f"Current rate limit test requests: {self.security_config['rate_limit_test_requests']}"
        )
        new_requests = input(
            "New rate limit test requests (press Enter to keep current): "
        ).strip()
        if new_requests.isdigit():
            self.security_config["rate_limit_test_requests"] = int(new_requests)

        print("✅ Settings updated!")


def main():
    """Main function"""
    print("🔒 API Security & Compliance Validator")
    print("Comprehensive security validation for 100+ APIs")
    print("=" * 60)

    validator = APISecurityCompliance()

    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == "scan-all":
            asyncio.run(validator.scan_all_apis())
        elif command == "report":
            asyncio.run(validator.generate_compliance_report())
        elif command == "interactive":
            validator.interactive_menu()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: scan-all, report, interactive")
    else:
        validator.interactive_menu()


if __name__ == "__main__":
    main()
