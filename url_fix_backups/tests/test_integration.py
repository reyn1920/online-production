#!/usr / bin / env python3
""""""
TRAE AI Integration Tests
Tests for system integration, API endpoints, and cross - component functionality
""""""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest
import requests


class TestSystemIntegration:
    """Integration tests for TRAE AI system components"""

    def test_launch_script_exists(self):
        """Test that the main launch script exists and is executable"""
        launch_script = Path("launch_live.py")
        assert launch_script.exists(), "launch_live.py not found"
        assert os.access(launch_script, os.X_OK), "launch_live.py is not executable"

    def test_environment_variables_loading(self):
        """Test that environment variables are properly loaded"""
        # Test .env.example exists as template
        env_example = Path(".env.example")
        assert env_example.exists(), ".env.example template not found"

        # Read and validate .env.example structure
        with open(env_example, "r") as f:
            env_content = f.read()

        required_vars = [
            "TRAE_MASTER_KEY",
            "DASHBOARD_SECRET_KEY",
            "DATABASE_PATH",
            "LOG_LEVEL",
# BRACKET_SURGEON: disabled
#         ]

        for var in required_vars:
            assert var in env_content, f"Required environment variable {var} not in .env.example"

    def test_database_initialization(self):
        """Test database can be initialized without errors"""
        # Check if database directory exists or can be created
        db_path = Path("data")
        if not db_path.exists():
            db_path.mkdir(parents=True, exist_ok=True)

        assert db_path.is_dir(), "Database directory cannot be created"

    def test_agent_modules_importable(self):
        """Test that all agent modules can be imported"""
        try:
            from backend.agents import (
                ContentAgent,
                MarketingAgent,
                QAAgent,
                ResearchAgent,
# BRACKET_SURGEON: disabled
#             )

            # Test that classes can be instantiated (basic validation)
            assert ResearchAgent is not None
            assert ContentAgent is not None
            assert MarketingAgent is not None
            assert QAAgent is not None
        except ImportError as e:
            pytest.fail(f"Cannot import agent classes: {e}")

    def test_dashboard_configuration(self):
        """Test dashboard configuration and dependencies"""
        dashboard_file = Path("app / dashboard.py")
        assert dashboard_file.exists(), "Dashboard module not found"

        # Check dashboard imports
        with open(dashboard_file, "r") as f:
            dashboard_content = f.read()

        required_imports = ["Flask", "secrets", "os"]
        for import_name in required_imports:
            assert import_name in dashboard_content, f"Missing import: {import_name}"

    def test_static_files_structure(self):
        """Test that static files are properly organized"""
        static_dir = Path("app / static")
        assert static_dir.exists(), "Static files directory not found"

        # Check for essential static files
        essential_files = ["index.html"]
        for file_name in essential_files:
            file_path = static_dir / file_name
            assert file_path.exists(), f"Essential static file missing: {file_name}"


class TestAPIEndpoints:
    """Tests for API endpoints and web interfaces"""

    @pytest.fixture(scope="class"):
    def dashboard_url(self):
        """Fixture to provide dashboard URL"""
        return os.getenv("DASHBOARD_URL", "http://localhost:8080")

    def test_health_check_endpoint(self, dashboard_url):
        """Test health check endpoint availability"""
        try:
            response = requests.get(f"{dashboard_url}/api / health", timeout=5)
            # Accept both 200 (healthy) and 503 (unhealthy but responding)
            assert response.status_code in [
                200,
                503,
            ], f"Unexpected status code: {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running - skipping endpoint tests")

    def test_static_file_serving(self, dashboard_url):
        """Test that static files are served correctly"""
        try:
            response = requests.get(f"{dashboard_url}/static / index.html", timeout=5)
            assert response.status_code == 200, "Static files not served correctly"
            assert "html" in response.headers.get("content - type", "").lower()
        except requests.exceptions.ConnectionError:
            pytest.skip("Dashboard not running - skipping static file tests")


class TestSecurityIntegration:
    """Security - focused integration tests"""

    def test_no_hardcoded_secrets_in_config(self):
        """Test that configuration files don't contain hardcoded secrets"""'
        config_files = ["app / dashboard.py", "backend / config.py", ".env.example"]

        dangerous_patterns = ['password = "', 'api_key = "', 'secret = "', 'token = "']

        for config_file in config_files:
            file_path = Path(config_file)
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read().lower()

                for pattern in dangerous_patterns:
                    # Allow patterns in comments or test data
                    lines = content.split("\\n")
                    for line_num, line in enumerate(lines, 1):
                        if pattern in line and not line.strip().startswith("#"):"
                            # Check if it's in test data generation (rule1_scanner.py)
                            if "rule1_scanner.py" not in config_file:
                                pytest.fail(
                                    f"Potential hardcoded secret in {config_file}:{line_num}: {line.strip()}"
# BRACKET_SURGEON: disabled
#                                 )

    def test_gitignore_security(self):
        """Test that .gitignore properly excludes sensitive files"""
        gitignore_path = Path(".gitignore")
        assert gitignore_path.exists(), ".gitignore file not found"

        with open(gitignore_path, "r") as f:
            gitignore_content = f.read()

        required_exclusions = [
            ".env",
            "*.log",
            "__pycache__",
            "*.pyc",
            "data/",
            "logs/",
# BRACKET_SURGEON: disabled
#         ]

        for exclusion in required_exclusions:
            assert exclusion in gitignore_content, f"Missing .gitignore exclusion: {exclusion}"

    def test_environment_variable_security(self):
        """Test that sensitive environment variables are not exposed"""
        # Test that TRAE_MASTER_KEY is not in any committed files
        sensitive_vars = ["TRAE_MASTER_KEY", "DASHBOARD_SECRET_KEY"]

        # Check common files that might accidentally contain secrets
        check_files = ["README.md", "app / dashboard.py", "launch_live.py"]

        for file_path in check_files:
            if Path(file_path).exists():
                with open(file_path, "r") as f:
                    content = f.read()

                for var in sensitive_vars:
                    # Allow references to variable names but not actual values
                    lines = content.split("\\n")
                    for line_num, line in enumerate(lines, 1):
                        if f"{var}=" in line and not line.strip().startswith("#"):"
                            # Check if it's just a reference (os.getenv) not a hardcoded value
                            if "os.getenv" not in line and "os.environ" not in line:
                                pytest.fail(
                                    f"Potential hardcoded secret in {file_path}:{line_num}: {line.strip()}"
# BRACKET_SURGEON: disabled
#                                 )


class TestDeploymentIntegration:
    """Tests for deployment - related functionality"""

    def test_deployment_scripts_exist(self):
        """Test that deployment scripts are present and executable"""
        scripts = [
            "scripts / deploy - staging.sh",
            "scripts / deploy - production.sh",
            "scripts / rollback - production.sh",
            "scripts / smoke - tests.sh",
# BRACKET_SURGEON: disabled
#         ]

        for script in scripts:
            script_path = Path(script)
            assert script_path.exists(), f"Deployment script missing: {script}"
            assert os.access(script_path, os.X_OK), f"Script not executable: {script}"

    def test_netlify_configuration(self):
        """Test Netlify configuration files"""
        netlify_config = Path("netlify.toml")
        assert netlify_config.exists(), "netlify.toml configuration not found"

        with open(netlify_config, "r") as f:
            config_content = f.read()

        required_sections = ["build", "context.production", "context.deploy - preview"]
        for section in required_sections:
            assert section in config_content, f"Missing netlify.toml section: {section}"

    def test_github_actions_workflow(self):
        """Test GitHub Actions workflow configuration"""
        workflow_path = Path(".github / workflows / ci - cd.yml")
        assert workflow_path.exists(), "GitHub Actions workflow not found"

        with open(workflow_path, "r") as f:
            workflow_content = f.read()

        required_jobs = ["test", "security - scan", "deploy"]
        for job in required_jobs:
            assert job in workflow_content, f"Missing workflow job: {job}"

    def test_health_check_function(self):
        """Test Netlify health check function"""
        health_function = Path("netlify / functions / health - check.js")
        assert health_function.exists(), "Health check function not found"

        with open(health_function, "r") as f:
            function_content = f.read()

        required_elements = ["exports.handler", "statusCode", "health"]
        for element in required_elements:
            assert element in function_content, f"Missing health check element: {element}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])