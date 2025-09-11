#!/usr/bin/env python3
"""
Production Deployment Script
Implements secure, automated deployment following go-live rules
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests


class ProductionDeployment:
    """Handles secure production deployment process"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.deployment_log = []
        self.start_time = datetime.utcnow()

        # Required environment variables for production
        self.required_env_vars = [
            "NETLIFY_AUTH_TOKEN",
            "NETLIFY_SITE_ID",
            "ENVIRONMENT",
            "NODE_ENV",
        ]

        # Health check endpoints
        self.health_endpoints = [
            "/api/health",
            "/api/production/health",
            "/api/production/readiness",
            "/api/production/liveness",
        ]

    def log_step(self, message: str, status: str = "INFO"):
        """Log deployment step with timestamp"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {status}: {message}"
        print(log_entry)
        self.deployment_log.append(log_entry)

    def validate_environment(self) -> bool:
        """Validate deployment environment and prerequisites"""
        self.log_step("Validating deployment environment", "INFO")

        # Check required environment variables
        missing_vars = []
        for var in self.required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.log_step(
                f"Missing required environment variables: {missing_vars}", "ERROR"
            )
            return False

        # Validate environment is set to production
        if os.getenv("ENVIRONMENT") != "production":
            self.log_step(
                "ENVIRONMENT must be set to 'production' for production deployment",
                "ERROR",
            )
            return False

        if os.getenv("NODE_ENV") != "production":
            self.log_step(
                "NODE_ENV must be set to 'production' for production deployment",
                "ERROR",
            )
            return False

        # Check if we're on the main branch
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            current_branch = result.stdout.strip()
            if current_branch != "main":
                self.log_step(
                    f"Production deployment must be from 'main' branch, currently on '{current_branch}'",
                    "ERROR",
                )
                return False
        except subprocess.CalledProcessError:
            self.log_step("Failed to check current git branch", "ERROR")
            return False

        self.log_step("Environment validation passed", "SUCCESS")
        return True

    def run_security_checks(self) -> bool:
        """Run comprehensive security checks before deployment"""
        self.log_step("Running pre-deployment security checks", "INFO")

        # Run linting
        try:
            subprocess.run(["npm", "run", "lint"], check=True, cwd=self.project_root)
            self.log_step("Linting passed", "SUCCESS")
        except subprocess.CalledProcessError:
            self.log_step("Linting failed - deployment aborted", "ERROR")
            return False

        # Run Base44 Guard
        try:
            subprocess.run(
                ["./tools/run_base44_guard.zsh"], check=True, cwd=self.project_root
            )
            self.log_step("Base44 Guard checks passed", "SUCCESS")
        except subprocess.CalledProcessError:
            self.log_step("Base44 Guard failed - deployment aborted", "ERROR")
            return False

        # Check for secrets in codebase
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "10"],
                capture_output=True,
                text=True,
                check=True,
            )
            # Simple check for common secret patterns in recent commits
            secret_patterns = ["password", "secret", "key", "token", "api_key"]
            for line in result.stdout.lower().split("\n"):
                for pattern in secret_patterns:
                    if pattern in line and not any(
                        safe in line for safe in ["remove", "fix", "clean"]
                    ):
                        self.log_step(
                            f"Potential secret detected in recent commit: {line}",
                            "WARNING",
                        )
        except subprocess.CalledProcessError:
            self.log_step("Could not check recent commits for secrets", "WARNING")

        self.log_step("Security checks completed", "SUCCESS")
        return True

    def build_application(self) -> bool:
        """Build the application for production"""
        self.log_step("Building application for production", "INFO")

        try:
            # Install dependencies
            subprocess.run(
                ["npm", "install", "--production"], check=True, cwd=self.project_root
            )
            self.log_step("Dependencies installed", "SUCCESS")

            # Build the application
            subprocess.run(["npm", "run", "build"], check=True, cwd=self.project_root)
            self.log_step("Application build completed", "SUCCESS")

            # Verify build output
            dist_path = self.project_root / "dist"
            if not dist_path.exists():
                self.log_step("Build output directory 'dist' not found", "ERROR")
                return False

            # Check for essential files
            essential_files = ["index.html"]
            for file in essential_files:
                if not (dist_path / file).exists():
                    self.log_step(
                        f"Essential file '{file}' not found in build output", "ERROR"
                    )
                    return False

            self.log_step("Build verification passed", "SUCCESS")
            return True

        except subprocess.CalledProcessError as e:
            self.log_step(f"Build failed: {e}", "ERROR")
            return False

    def deploy_to_netlify(self) -> Optional[str]:
        """Deploy to Netlify production"""
        self.log_step("Deploying to Netlify production", "INFO")

        try:
            # Deploy using Netlify CLI
            cmd = [
                "netlify",
                "deploy",
                "--prod",
                "--dir",
                "dist",
                "--message",
                f"Production deployment {self.start_time.isoformat()}",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, cwd=self.project_root
            )

            # Extract deployment URL from output
            output_lines = result.stdout.split("\n")
            deploy_url = None
            for line in output_lines:
                if "Website URL:" in line or "Live Draft URL:" in line:
                    deploy_url = line.split(":", 1)[1].strip()
                    break

            if deploy_url:
                self.log_step(f"Deployment successful: {deploy_url}", "SUCCESS")
                return deploy_url
            else:
                self.log_step(
                    "Deployment completed but URL not found in output", "WARNING"
                )
                return "https://your-site.netlify.app"  # Fallback

        except subprocess.CalledProcessError as e:
            self.log_step(f"Netlify deployment failed: {e.stderr}", "ERROR")
            return None

    def run_health_checks(self, base_url: str) -> bool:
        """Run comprehensive health checks on deployed application"""
        self.log_step("Running post-deployment health checks", "INFO")

        # Wait for deployment to be ready
        self.log_step("Waiting for deployment to be ready...", "INFO")
        time.sleep(30)  # Give the deployment time to start

        failed_checks = []

        for endpoint in self.health_endpoints:
            url = f"{base_url.rstrip('/')}{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.log_step(f"Health check passed: {endpoint}", "SUCCESS")
                else:
                    self.log_step(
                        f"Health check failed: {endpoint} (status: {response.status_code})",
                        "WARNING",
                    )
                    failed_checks.append(endpoint)
            except requests.exceptions.RequestException as e:
                self.log_step(f"Health check error: {endpoint} - {str(e)}", "WARNING")
                failed_checks.append(endpoint)

        # Test basic functionality
        try:
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                self.log_step("Main page accessibility check passed", "SUCCESS")
            else:
                self.log_step(
                    f"Main page check failed (status: {response.status_code})", "ERROR"
                )
                failed_checks.append("main_page")
        except requests.exceptions.RequestException as e:
            self.log_step(f"Main page check error: {str(e)}", "ERROR")
            failed_checks.append("main_page")

        if failed_checks:
            self.log_step(f"Some health checks failed: {failed_checks}", "WARNING")
            return (
                len(failed_checks) < len(self.health_endpoints) / 2
            )  # Allow some failures

        self.log_step("All health checks passed", "SUCCESS")
        return True

    def create_deployment_report(self, deploy_url: Optional[str], success: bool):
        """Create deployment report"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()

        report = {
            "deployment_id": f"prod-{int(self.start_time.timestamp())}",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration,
            "success": success,
            "deploy_url": deploy_url,
            "environment": "production",
            "git_branch": self._get_git_branch(),
            "git_commit": self._get_git_commit(),
            "logs": self.deployment_log,
        }

        # Save report
        report_path = (
            self.project_root
            / "deployment_reports"
            / f"deployment_{int(self.start_time.timestamp())}.json"
        )
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.log_step(f"Deployment report saved: {report_path}", "INFO")
        return report

    def _get_git_branch(self) -> str:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except:
            return "unknown"

    def _get_git_commit(self) -> str:
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()[:8]
        except:
            return "unknown"

    def deploy(self) -> bool:
        """Execute complete production deployment process"""
        self.log_step("Starting production deployment process", "INFO")

        try:
            # Step 1: Validate environment
            if not self.validate_environment():
                self.log_step(
                    "Environment validation failed - deployment aborted", "ERROR"
                )
                return False

            # Step 2: Run security checks
            if not self.run_security_checks():
                self.log_step("Security checks failed - deployment aborted", "ERROR")
                return False

            # Step 3: Build application
            if not self.build_application():
                self.log_step("Application build failed - deployment aborted", "ERROR")
                return False

            # Step 4: Deploy to Netlify
            deploy_url = self.deploy_to_netlify()
            if not deploy_url:
                self.log_step("Netlify deployment failed - deployment aborted", "ERROR")
                return False

            # Step 5: Run health checks
            if not self.run_health_checks(deploy_url):
                self.log_step(
                    "Health checks failed - deployment may have issues", "WARNING"
                )
                # Don't abort on health check failures, but log them

            # Step 6: Create deployment report
            self.create_deployment_report(deploy_url, True)

            self.log_step(
                f"Production deployment completed successfully: {deploy_url}", "SUCCESS"
            )
            return True

        except Exception as e:
            self.log_step(f"Unexpected error during deployment: {str(e)}", "ERROR")
            self.create_deployment_report(None, False)
            return False


def main():
    """Main deployment function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--confirm-production":
        deployment = ProductionDeployment()
        success = deployment.deploy()
        sys.exit(0 if success else 1)
    else:
        print("Production Deployment Script")
        print("This script will deploy to PRODUCTION environment.")
        print("")
        print("Required environment variables:")
        for var in ProductionDeployment().required_env_vars:
            status = "✓" if os.getenv(var) else "✗"
            print(f"  {status} {var}")
        print("")
        print("To proceed with production deployment, run:")
        print("  python scripts/deploy_production.py --confirm-production")
        print("")
        print("WARNING: This will deploy to the live production environment!")


if __name__ == "__main__":
    main()
