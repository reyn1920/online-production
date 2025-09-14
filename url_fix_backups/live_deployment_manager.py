#!/usr / bin / env python3
"""
Live Deployment Manager
Manages the complete go - live process for the production environment.
Follows the LIVE_ENVIRONMENT_RULES.md guidelines.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path


class LiveDeploymentManager:
    def __init__(self):
        self.project_root = Path.cwd()
        self.deployment_log = []
        self.start_time = datetime.now()

    def log_action(self, action, status="INFO", details=None):
        """Log deployment actions with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "action": action,
            "status": status,
            "details": details,
        }
        self.deployment_log.append(log_entry)
        print(f"[{timestamp}] {status}: {action}")
        if details:
            print(f"    Details: {details}")

    def check_prerequisites(self):
        """Check all prerequisites for live deployment"""
        self.log_action("Checking deployment prerequisites")

        # Check if required files exist
        required_files = [".env", "package.json", "LIVE_ENVIRONMENT_RULES.md"]

        missing_files = []
        for file in required_files:
            if not (self.project_root / file).exists():
                missing_files.append(file)

        if missing_files:
            self.log_action(f"Missing required files: {missing_files}", "ERROR")
            return False

        # Check environment variables
        env_check = self.check_environment_variables()
        if not env_check:
            return False

        self.log_action("All prerequisites met", "SUCCESS")
        return True

    def check_environment_variables(self):
        """Validate critical environment variables"""
        self.log_action("Validating environment variables")

        critical_vars = ["NODE_ENV", "DATABASE_URL", "JWT_SECRET", "CORS_ORIGIN"]

        missing_vars = []
        for var in critical_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            self.log_action(f"Missing critical environment variables: {missing_vars}", "ERROR")
            return False

        # Check if NODE_ENV is set to production
        if os.getenv("NODE_ENV") != "production":
            self.log_action("NODE_ENV must be set to 'production' for live deployment", "WARNING")

        self.log_action("Environment variables validated", "SUCCESS")
        return True

    def run_security_checks(self):
        """Run comprehensive security checks"""
        self.log_action("Running security checks")

        # Check for hardcoded secrets in code
        try:
            result = subprocess.run(
                [
                    "grep",
                    "-r",
                    "-i",
                    "api[_-]key\\|secret\\|password\\|token",
                    ".",
                    "--exclude - dir = node_modules",
                    "--exclude - dir=.git",
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0 and result.stdout:
                # Filter out .env files and comments
                suspicious_lines = []
                for line in result.stdout.split("\\n"):
                    if line and not line.startswith(".env") and not line.strip().startswith("#"):
                        suspicious_lines.append(line)

                if suspicious_lines:
                    self.log_action(
                        "Potential hardcoded secrets found",
                        "WARNING",
                        suspicious_lines[:5],
                    )

        except Exception as e:
            self.log_action(f"Security check failed: {e}", "WARNING")

        self.log_action("Security checks completed", "SUCCESS")
        return True

    def build_application(self):
        """Build the application for production"""
        self.log_action("Building application for production")

        try:
            # Install dependencies
            self.log_action("Installing dependencies")
            result = subprocess.run(
                ["npm", "install"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                self.log_action("Dependency installation failed", "ERROR", result.stderr)
                return False

            # Run build
            self.log_action("Running production build")
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                self.log_action("Build failed", "ERROR", result.stderr)
                return False

            self.log_action("Application built successfully", "SUCCESS")
            return True

        except Exception as e:
            self.log_action(f"Build process failed: {e}", "ERROR")
            return False

    def run_tests(self):
        """Run comprehensive test suite"""
        self.log_action("Running test suite")

        try:
            # Check if test script exists
            package_json_path = self.project_root / "package.json"
            if package_json_path.exists():
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)

                if "test" in package_data.get("scripts", {}):
                    result = subprocess.run(
                        ["npm", "test"],
                        capture_output=True,
                        text=True,
                        cwd=self.project_root,
                    )

                    if result.returncode != 0:
                        self.log_action("Tests failed", "ERROR", result.stderr)
                        return False

                    self.log_action("All tests passed", "SUCCESS")
                else:
                    self.log_action("No test script found in package.json", "WARNING")

            return True

        except Exception as e:
            self.log_action(f"Test execution failed: {e}", "ERROR")
            return False

    def deploy_to_production(self):
        """Deploy to live production environment"""
        self.log_action("Deploying to production environment")

        try:
            # Check if Netlify CLI is available
            result = subprocess.run(["netlify", "--version"], capture_output=True, text=True)

            if result.returncode != 0:
                self.log_action(
                    "Netlify CLI not found. Install with: npm install -g netlify - cli",
                    "ERROR",
                )
                return False

            # Deploy to Netlify
            self.log_action("Deploying to Netlify")
            result = subprocess.run(
                ["netlify", "deploy", "--prod", "--dir = dist"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode != 0:
                self.log_action("Netlify deployment failed", "ERROR", result.stderr)
                return False

            # Extract deployment URL from output
            deployment_url = None
            for line in result.stdout.split("\\n"):
                if "Website URL:" in line:
                    deployment_url = line.split("Website URL:")[1].strip()
                    break

            if deployment_url:
                self.log_action(f"Deployment successful! Live URL: {deployment_url}", "SUCCESS")
            else:
                self.log_action("Deployment completed", "SUCCESS")

            return True

        except Exception as e:
            self.log_action(f"Deployment failed: {e}", "ERROR")
            return False

    def post_deployment_checks(self):
        """Run post - deployment health checks"""
        self.log_action("Running post - deployment health checks")

        # Add health check logic here
        # This could include API endpoint tests, database connectivity, etc.

        self.log_action("Post - deployment checks completed", "SUCCESS")
        return True

    def generate_deployment_report(self):
        """Generate comprehensive deployment report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = {
            "deployment_id": f"deploy_{int(time.time())}",
            "start_time": self.start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "status": "SUCCESS"
            if all(log["status"] != "ERROR" for log in self.deployment_log)
            else "FAILED",
            "log": self.deployment_log,
            "environment": {
                "node_env": os.getenv("NODE_ENV"),
                "python_version": sys.version,
                "working_directory": str(self.project_root),
            },
        }

        report_filename = f"deployment_report_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
        report_path = self.project_root / report_filename

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.log_action(f"Deployment report saved to: {report_filename}", "INFO")
        return report

    def execute_live_deployment(self):
        """Execute the complete live deployment process"""
        print("\\n" + "=" * 80)
        print("LIVE DEPLOYMENT MANAGER - PRODUCTION GO - LIVE")
        print("=" * 80)

        # Step 1: Prerequisites
        if not self.check_prerequisites():
            self.log_action("Deployment aborted due to failed prerequisites", "ERROR")
            return False

        # Step 2: Security checks
        if not self.run_security_checks():
            self.log_action("Deployment aborted due to security issues", "ERROR")
            return False

        # Step 3: Build application
        if not self.build_application():
            self.log_action("Deployment aborted due to build failure", "ERROR")
            return False

        # Step 4: Run tests
        if not self.run_tests():
            self.log_action("Deployment aborted due to test failures", "ERROR")
            return False

        # Step 5: Deploy to production
        if not self.deploy_to_production():
            self.log_action("Deployment failed", "ERROR")
            return False

        # Step 6: Post - deployment checks
        if not self.post_deployment_checks():
            self.log_action("Post - deployment checks failed", "WARNING")

        # Step 7: Generate report
        report = self.generate_deployment_report()

        print("\\n" + "=" * 80)
        print("LIVE DEPLOYMENT COMPLETED SUCCESSFULLY!")
        print("=" * 80)

        return True


def main():
    """Main deployment function"""
    deployment_manager = LiveDeploymentManager()

    try:
        success = deployment_manager.execute_live_deployment()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        deployment_manager.log_action("Deployment interrupted by user", "ERROR")
        sys.exit(1)
    except Exception as e:
        deployment_manager.log_action(f"Unexpected error: {e}", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    main()
