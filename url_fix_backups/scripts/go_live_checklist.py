#!/usr / bin / env python3
""""""
Go - Live Checklist Validator
Comprehensive validation of all go - live requirements before production deployment
""""""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests


class GoLiveValidator:
    """Validates all go - live requirements and readiness"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.checks = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_check(self, name: str, status: str, message: str, critical: bool = True):
        """Add a check result"""
        self.checks.append(
            {
                "name": name,
                "status": status,
                "message": message,
                "critical": critical,
                "timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

    def check_environment_setup(self) -> bool:
        """Check environment configuration"""
        print("🔧 Checking Environment Setup...")

        # Check required files exist
        required_files = [
            ".env.example",
            ".env.production",
            "netlify.toml",
            ".github / workflows / ci - cd.yml",
            "package.json",
            "requirements.txt",
# BRACKET_SURGEON: disabled
#         ]

        all_files_exist = True
        for file in required_files:
            file_path = self.project_root / file
            if file_path.exists():
                self.add_check(f"File: {file}", "PASS", f"Required file exists: {file}")
            else:
                self.add_check(f"File: {file}", "FAIL", f"Required file missing: {file}")
                all_files_exist = False

        # Check environment variables
        required_env_vars = [
            "NETLIFY_AUTH_TOKEN",
            "NETLIFY_SITE_ID",
            "ENVIRONMENT",
            "NODE_ENV",
# BRACKET_SURGEON: disabled
#         ]

        env_vars_set = True
        for var in required_env_vars:
            if os.getenv(var):
                self.add_check(f"Env: {var}", "PASS", f"Environment variable set: {var}")
            else:
                self.add_check(f"Env: {var}", "FAIL", f"Environment variable missing: {var}")
                env_vars_set = False

        return all_files_exist and env_vars_set

    def check_security_configuration(self) -> bool:
        """Check security configuration"""
        print("🔒 Checking Security Configuration...")

        security_files = [
            "backend / security / content_validator.py",
            "backend / routers / production_health.py",
# BRACKET_SURGEON: disabled
#         ]

        security_ok = True
        for file in security_files:
            file_path = self.project_root / file
            if file_path.exists():
                self.add_check(f"Security: {file}", "PASS", f"Security component exists: {file}")
            else:
                self.add_check(f"Security: {file}", "FAIL", f"Security component missing: {file}")
                security_ok = False

        # Check GitHub Actions workflow has security scanning
        workflow_path = self.project_root / ".github / workflows / ci - cd.yml"
        if workflow_path.exists():
            with open(workflow_path, "r") as f:
                workflow_content = f.read()

            security_tools = ["codeql", "bandit", "safety", "gitleaks", "semgrep"]
            for tool in security_tools:
                if tool.lower() in workflow_content.lower():
                    self.add_check(
                        f"Security Tool: {tool}",
                        "PASS",
                        f"Security tool configured: {tool}",
# BRACKET_SURGEON: disabled
#                     )
                else:
                    self.add_check(
                        f"Security Tool: {tool}",
                        "WARN",
                        f"Security tool not found: {tool}",
                        critical=False,
# BRACKET_SURGEON: disabled
#                     )

        return security_ok

    def check_ci_cd_pipeline(self) -> bool:
        """Check CI / CD pipeline configuration"""
        print("🚀 Checking CI / CD Pipeline...")

        workflow_path = self.project_root / ".github / workflows / ci - cd.yml"
        if not workflow_path.exists():
            self.add_check("CI / CD Workflow", "FAIL", "GitHub Actions workflow file missing")
            return False

        with open(workflow_path, "r") as f:
            workflow_content = f.read()

        # Check for required jobs
        required_jobs = [
            "code - quality",
            "security - scan",
            "test",
            "deploy - production",
# BRACKET_SURGEON: disabled
#         ]
        pipeline_ok = True

        for job in required_jobs:
            if job in workflow_content:
                self.add_check(f"CI / CD Job: {job}", "PASS", f"Required job configured: {job}")
            else:
                self.add_check(f"CI / CD Job: {job}", "FAIL", f"Required job missing: {job}")
                pipeline_ok = False

        # Check for workflow_dispatch trigger
        if "workflow_dispatch" in workflow_content:
            self.add_check("Manual Deployment", "PASS", "Manual deployment trigger configured")
        else:
            self.add_check("Manual Deployment", "FAIL", "Manual deployment trigger missing")
            pipeline_ok = False

        return pipeline_ok

    def check_build_system(self) -> bool:
        """Check build system configuration"""
        print("🔨 Checking Build System...")

        # Check package.json
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            with open(package_json_path, "r") as f:
                package_data = json.load(f)

            required_scripts = ["build", "lint", "start"]
            build_ok = True

            for script in required_scripts:
                if script in package_data.get("scripts", {}):
                    self.add_check(
                        f"NPM Script: {script}",
                        "PASS",
                        f"Required script configured: {script}",
# BRACKET_SURGEON: disabled
#                     )
                else:
                    self.add_check(
                        f"NPM Script: {script}",
                        "FAIL",
                        f"Required script missing: {script}",
# BRACKET_SURGEON: disabled
#                     )
                    build_ok = False
        else:
            self.add_check("Package.json", "FAIL", "package.json file missing")
            build_ok = False

        # Check Netlify configuration
        netlify_config_path = self.project_root / "netlify.toml"
        if netlify_config_path.exists():
            self.add_check("Netlify Config", "PASS", "Netlify configuration file exists")
        else:
            self.add_check("Netlify Config", "FAIL", "Netlify configuration file missing")
            build_ok = False

        return build_ok

    def check_health_monitoring(self) -> bool:
        """Check health monitoring setup"""
        print("💓 Checking Health Monitoring...")

        health_endpoints = [
            "backend / routers / production_health.py",
            "app / dashboard.py",  # Assuming dashboard has health checks
# BRACKET_SURGEON: disabled
#         ]

        monitoring_ok = True
        for endpoint in health_endpoints:
            endpoint_path = self.project_root / endpoint
            if endpoint_path.exists():
                self.add_check(
                    f"Health Endpoint: {endpoint}",
                    "PASS",
                    f"Health monitoring component exists: {endpoint}",
# BRACKET_SURGEON: disabled
#                 )
            else:
                self.add_check(
                    f"Health Endpoint: {endpoint}",
                    "WARN",
                    f"Health monitoring component missing: {endpoint}",
                    critical=False,
# BRACKET_SURGEON: disabled
#                 )

        return monitoring_ok

    def check_content_validation(self) -> bool:
        """Check content validation system"""
        print("🛡️ Checking Content Validation...")

        validator_path = self.project_root / "backend / security / content_validator.py"
        if validator_path.exists():
            self.add_check("Content Validator", "PASS", "Content validation system exists")
            return True
        else:
            self.add_check("Content Validator", "FAIL", "Content validation system missing")
            return False

    def check_secrets_management(self) -> bool:
        """Check secrets management"""
        print("🔐 Checking Secrets Management...")

        secrets_ok = True

        # Check for hardcoded secrets (basic scan)
        dangerous_patterns = ["password", "secret", "key", "token", "api_key"]

        try:
            # Scan Python files for potential hardcoded secrets
            result = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-i",
                    "--include=*.py",
                    "|".join(dangerous_patterns),
                    str(self.project_root),
# BRACKET_SURGEON: disabled
#                 ],
                capture_output=True,
                text=True,
# BRACKET_SURGEON: disabled
#             )

            if result.returncode == 0 and result.stdout.strip():
                # Found potential secrets
                lines = result.stdout.strip().split("\\n")
                secret_files = set()
                for line in lines:
                    if ":" in line:
                        file_path = line.split(":", 1)[0]
                        secret_files.add(file_path)

                for file_path in secret_files:
                    self.add_check(
                        f"Secret Scan: {file_path}",
                        "WARN",
                        f"Potential hardcoded secrets detected in: {file_path}",
                        critical=False,
# BRACKET_SURGEON: disabled
#                     )
            else:
                self.add_check("Secret Scan", "PASS", "No obvious hardcoded secrets detected")

        except subprocess.CalledProcessError:
            self.add_check("Secret Scan", "WARN", "Could not perform secret scan", critical=False)

        # Check .env files are in .gitignore
        gitignore_path = self.project_root / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                gitignore_content = f.read()

            if ".env" in gitignore_content:
                self.add_check("Gitignore .env", "PASS", ".env files are ignored by git")
            else:
                self.add_check("Gitignore .env", "FAIL", ".env files not ignored by git")
                secrets_ok = False

        return secrets_ok

    def check_deployment_readiness(self) -> bool:
        """Check deployment readiness"""
        print("🎯 Checking Deployment Readiness...")

        readiness_ok = True

        # Check git status
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
# BRACKET_SURGEON: disabled
#             )
            if result.stdout.strip():
                self.add_check("Git Status", "WARN", "Uncommitted changes detected", critical=False)
            else:
                self.add_check("Git Status", "PASS", "Working directory clean")
        except subprocess.CalledProcessError:
            self.add_check("Git Status", "WARN", "Could not check git status", critical=False)

        # Check current branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show - current"],
                capture_output=True,
                text=True,
                check=True,
# BRACKET_SURGEON: disabled
#             )
            current_branch = result.stdout.strip()
            if current_branch == "main":
                self.add_check("Git Branch", "PASS", "On main branch")
            else:
                self.add_check(
                    "Git Branch",
                    "FAIL",
                    f"Not on main branch (currently on: {current_branch})",
# BRACKET_SURGEON: disabled
#                 )
                readiness_ok = False
        except subprocess.CalledProcessError:
            self.add_check("Git Branch", "FAIL", "Could not determine current branch")
            readiness_ok = False

        # Check deployment script exists
        deploy_script_path = self.project_root / "scripts / deploy_production.py"
        if deploy_script_path.exists():
            self.add_check("Deployment Script", "PASS", "Production deployment script exists")
        else:
            self.add_check("Deployment Script", "FAIL", "Production deployment script missing")
            readiness_ok = False

        return readiness_ok

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all go - live validation checks"""
        print("🚀 Starting Go - Live Validation Checklist")
        print("=" * 50)

        # Run all check categories
        checks = [
            ("Environment Setup", self.check_environment_setup),
            ("Security Configuration", self.check_security_configuration),
            ("CI / CD Pipeline", self.check_ci_cd_pipeline),
            ("Build System", self.check_build_system),
            ("Health Monitoring", self.check_health_monitoring),
            ("Content Validation", self.check_content_validation),
            ("Secrets Management", self.check_secrets_management),
            ("Deployment Readiness", self.check_deployment_readiness),
# BRACKET_SURGEON: disabled
#         ]

        category_results = {}
        for category_name, check_func in checks:
            print(f"\\n{category_name}:")
            category_results[category_name] = check_func()

        # Generate summary
        print("\\n" + "=" * 50)
        print("📊 GO - LIVE VALIDATION SUMMARY")
        print("=" * 50)

        critical_failures = [
            check for check in self.checks if check["status"] == "FAIL" and check["critical"]
# BRACKET_SURGEON: disabled
#         ]

        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"⚠️  Warnings: {self.warnings}")
        print(f"🚨 Critical Failures: {len(critical_failures)}")

        if critical_failures:
            print("\\n🚨 CRITICAL ISSUES THAT MUST BE RESOLVED:")
            for failure in critical_failures:
                print(f"  ❌ {failure['name']}: {failure['message']}")

        warnings = [check for check in self.checks if check["status"] == "WARN"]
        if warnings:
            print("\\n⚠️  WARNINGS (RECOMMENDED TO ADDRESS):")
            for warning in warnings:
                print(f"  ⚠️  {warning['name']}: {warning['message']}")

        # Overall readiness assessment
        is_ready = len(critical_failures) == 0

        if is_ready:
            print("\\n🎉 GO - LIVE READINESS: ✅ READY FOR PRODUCTION DEPLOYMENT")
            print("\\nTo deploy to production, run:")
            print("  python scripts / deploy_production.py --confirm - production")
        else:
            print("\\n🛑 GO - LIVE READINESS: ❌ NOT READY FOR PRODUCTION")
            print("\\nPlease resolve all critical issues before attempting deployment.")

        # Save detailed report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "ready_for_production": is_ready,
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "critical_failures": len(critical_failures),
# BRACKET_SURGEON: disabled
#             },
            "category_results": category_results,
            "detailed_checks": self.checks,
# BRACKET_SURGEON: disabled
#         }

        report_path = self.project_root / "go_live_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"\\n📄 Detailed report saved to: {report_path}")

        return report


def main():
    """Main function"""
    validator = GoLiveValidator()
    report = validator.run_all_checks()

    # Exit with appropriate code
    sys.exit(0 if report["ready_for_production"] else 1)


if __name__ == "__main__":
    main()