import os
import sys
from pathlib import Path

import pytest

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSystemIntegrity:
    """Test suite for system integrity and basic functionality."""


    def test_project_structure(self):
        """Verify essential project files and directories exist."""
        required_files = [
            "launch_live.py",
                "requirements.txt",
                "app/static/index.html",
                "backend/__init__.py",
                "utils/__init__.py",
                ]

        for file_path in required_files:
            full_path = project_root/file_path
            assert full_path.exists(), f"Required file missing: {file_path}"


    def test_requirements_file(self):
        """Verify requirements.txt is readable and contains dependencies."""
        requirements_path = project_root/"requirements.txt"
        assert requirements_path.exists(), "requirements.txt not found"

        with open(requirements_path, "r") as f:
            content = f.read()
            assert len(content.strip()) > 0, "requirements.txt is empty"


    def test_launch_script_exists(self):
        """Verify main launch script exists and is readable."""
        launch_script = project_root/"launch_live.py"
        assert launch_script.exists(), "launch_live.py not found"
        assert launch_script.is_file(), "launch_live.py is not a file"


    def test_web_interface_exists(self):
        """Verify web interface files exist."""
        index_html = project_root/"app"/"static"/"index.html"
        assert index_html.exists(), "Web interface index.html not found"

        with open(index_html, "r") as f:
            content = f.read()
            assert "html" in content.lower(), "index.html appears to be invalid"


    def test_backend_structure(self):
        """Verify backend module structure."""
        backend_dir = project_root/"backend"
        assert backend_dir.exists(), "Backend directory not found"
        assert backend_dir.is_dir(), "Backend is not a directory"

        init_file = backend_dir/"__init__.py"
        assert init_file.exists(), "Backend __init__.py not found"


class TestEnvironmentConfiguration:
    """Test suite for environment and configuration validation."""


    def test_python_version(self):
        """Verify Python version compatibility."""
        assert sys.version_info >= (3, 8), "Python 3.8+ required"


    def test_no_hardcoded_secrets(self):
        """Basic check for potential hardcoded secrets in main files."""
        sensitive_patterns = [
            "api_key",
                "secret_key",
                "password",
                "token",
                "auth_token",
                ]

        main_files = [
            project_root/"launch_live.py",
                project_root/"app"/"static"/"index.html",
                ]

        for file_path in main_files:
            if file_path.exists():
                with open(file_path, "r", encoding="utf - 8", errors="ignore") as f:
                    content = f.read().lower()
                    for pattern in sensitive_patterns:
                        # Allow pattern in comments or variable names, but flag suspicious values
                        lines = content.split("\\n")
                        for line in lines:
                            if (
                                pattern in line
                                and "=" in line
                                and not line.strip().startswith("#")
                            ):
                                # Check if it looks like a real secret (not a placeholder)
                                if any(
                                    char in line
                                    for char in ["sk_", "pk_", "Bearer", "Basic"]
                                ):
                                    pytest.fail(
                                        f"Potential hardcoded secret found in {file_path}: {line.strip()}"
                                    )

if __name__ == "__main__":
    pytest.main([__file__, "-v"])