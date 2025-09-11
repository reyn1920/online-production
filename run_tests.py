#!/usr/bin/env python3
"""
TRAE AI Production Readiness Test Suite Runner

This script provides a single entry point to run all tests with proper
environment setup and comprehensive reporting.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit             # Run only unit tests
    python run_tests.py --integration      # Run only integration tests
    python run_tests.py --security         # Run only security tests
    python run_tests.py --fast             # Skip slow tests
    python run_tests.py --coverage         # Run with coverage report
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Ensure we're in the project root
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)

# Add project paths to Python path
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "app"))


class TestRunner:
    """Professional test runner for TRAE AI system."""

    def __init__(self):
        self.start_time = None
        self.results = {}

    def setup_environment(self):
        """Setup test environment variables."""
        os.environ["TRAE_MASTER_KEY"] = "TRAE_AI_MASTER_2024"
        os.environ["TESTING"] = "1"
        os.environ["LOG_LEVEL"] = "WARNING"  # Reduce noise during tests
        os.environ["DATABASE_PATH"] = "test_trae_ai.db"

        # Create test data directory if needed
        test_data_dir = PROJECT_ROOT / "test_data"
        test_data_dir.mkdir(exist_ok=True)

    def run_pytest(self, args=None):
        """Run pytest with specified arguments."""
        cmd = ["python", "-m", "pytest"]

        if args:
            cmd.extend(args)

        print(f"\n🚀 Running: {' '.join(cmd)}")
        print("=" * 60)

        try:
            result = subprocess.run(cmd, capture_output=False, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False

    def run_unit_tests(self):
        """Run unit tests only."""
        return self.run_pytest(["-m", "unit", "--tb=short"])

    def run_integration_tests(self):
        """Run integration tests only."""
        return self.run_pytest(["-m", "integration", "--tb=short"])

    def run_security_tests(self):
        """Run security tests only."""
        return self.run_pytest(["-m", "security", "--tb=short"])

    def run_fast_tests(self):
        """Run all tests except slow ones."""
        return self.run_pytest(["-m", "not slow", "--tb=short"])

    def run_with_coverage(self):
        """Run tests with coverage reporting."""
        return self.run_pytest(
            [
                "--cov=backend",
                "--cov=app",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-fail-under=70",
            ]
        )

    def run_all_tests(self):
        """Run the complete test suite."""
        return self.run_pytest(["--tb=short"])

    def cleanup_test_artifacts(self):
        """Clean up test artifacts."""
        artifacts = [
            "test_trae_ai.db",
            "test_right_perspective.db",
            ".pytest_cache",
            "htmlcov",
            "__pycache__",
        ]

        for artifact in artifacts:
            artifact_path = PROJECT_ROOT / artifact
            if artifact_path.exists():
                if artifact_path.is_file():
                    artifact_path.unlink()
                elif artifact_path.is_dir():
                    import shutil

                    shutil.rmtree(artifact_path)

    def print_summary(self, success, duration):
        """Print test run summary."""
        print("\n" + "=" * 60)
        print("🧪 TRAE AI TEST SUITE SUMMARY")
        print("=" * 60)

        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"Status: {status}")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if success:
            print("\n🎉 All tests passed! System is production ready.")
        else:
            print("\n⚠️  Some tests failed. Review output above for details.")
            print("Fix failing tests before deploying to production.")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="TRAE AI Test Suite Runner")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--security", action="store_true", help="Run security tests only"
    )
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up test artifacts"
    )

    args = parser.parse_args()

    runner = TestRunner()

    # Cleanup if requested
    if args.cleanup:
        print("🧹 Cleaning up test artifacts...")
        runner.cleanup_test_artifacts()
        print("✅ Cleanup complete.")
        return 0

    # Setup environment
    print("🔧 Setting up test environment...")
    runner.setup_environment()

    start_time = time.time()
    success = False

    try:
        # Run appropriate test suite
        if args.unit:
            success = runner.run_unit_tests()
        elif args.integration:
            success = runner.run_integration_tests()
        elif args.security:
            success = runner.run_security_tests()
        elif args.fast:
            success = runner.run_fast_tests()
        elif args.coverage:
            success = runner.run_with_coverage()
        else:
            success = runner.run_all_tests()

    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    finally:
        duration = time.time() - start_time
        runner.print_summary(success, duration)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
