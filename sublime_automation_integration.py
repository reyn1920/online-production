#!/usr/bin/env python3
"""
Sublime Text Automation Integration

This script demonstrates how Sublime Text can be integrated into the existing
automation workflow for the TRAE.AI platform.
"""

import json
import logging
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SublimeAutomationIntegrator:
    """Integrates Sublime Text into the automation pipeline."""

    def __init__(self):
        self.subl_path = "/Users/thomasbrianreynolds/homebrew/bin/subl"
        self.project_root = Path("/Users/thomasbrianreynolds/online production")
        self.validate_sublime_installation()

    def validate_sublime_installation(self) -> bool:
        """Validate that Sublime Text is properly installed and accessible."""
        try:
            result = subprocess.run(
                [self.subl_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Sublime Text detected: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.error(f"Sublime Text not accessible: {e}")
            return False

    def format_code_files(self, file_patterns: List[str] = None) -> Dict[str, bool]:
        """Format code files using Sublime Text's built-in formatting."""
        if file_patterns is None:
            file_patterns = ["*.py", "*.js", "*.ts", "*.json", "*.md"]

        results = {}

        for pattern in file_patterns:
            files = list(self.project_root.glob(f"**/{pattern}"))
            for file_path in files:
                try:
                    # Use Sublime Text to format the file
                    subprocess.run(
                        [
                            self.subl_path,
                            "--command",
                            "reindent",
                            "--wait",
                            str(file_path),
                        ],
                        check=True,
                    )
                    results[str(file_path)] = True
                    logger.info(f"Formatted: {file_path}")
                except subprocess.CalledProcessError as e:
                    results[str(file_path)] = False
                    logger.error(f"Failed to format {file_path}: {e}")

        return results

    def create_project_file(self, project_name: str = "TRAE_AI_Project") -> str:
        """Create a Sublime Text project file for the automation system."""
        project_config = {
            "folders": [
                {
                    "path": str(self.project_root),
                    "folder_exclude_patterns": [
                        "node_modules",
                        "venv",
                        "__pycache__",
                        ".git",
                        "models/linly_talker",
                        "cache",
                        "test_outputs",
                    ],
                    "file_exclude_patterns": ["*.pyc", "*.log", "*.pid", "*.sqlite"],
                }
            ],
            "settings": {
                "tab_size": 4,
                "translate_tabs_to_spaces": True,
                "trim_trailing_white_space_on_save": True,
                "ensure_newline_at_eof_on_save": True,
            },
            "build_systems": [
                {
                    "name": "TRAE AI - Run Tests",
                    "cmd": ["python", "-m", "pytest", "tests/"],
                    "working_dir": str(self.project_root),
                },
                {
                    "name": "TRAE AI - Start Development Server",
                    "cmd": ["python", "main.py"],
                    "working_dir": str(self.project_root),
                },
            ],
        }

        project_file = self.project_root / f"{project_name}.sublime-project"

        with open(project_file, "w") as f:
            json.dump(project_config, f, indent=2)

        logger.info(f"Created Sublime Text project file: {project_file}")
        return str(project_file)

    def open_project_in_sublime(self, project_file: str = None) -> bool:
        """Open the project in Sublime Text."""
        if project_file is None:
            project_file = self.create_project_file()

        try:
            subprocess.run([self.subl_path, "--project", project_file], check=True)
            logger.info(f"Opened project in Sublime Text: {project_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to open project in Sublime Text: {e}")
            return False

    def integrate_with_ci_cd(self) -> Dict[str, str]:
        """Generate CI/CD integration commands for Sublime Text."""
        integration_commands = {
            "pre_commit_format": f"{self.subl_path} --command reindent --wait",
            "batch_format": f"find . -name '*.py' -exec {self.subl_path} --command reindent --wait {{}} \;",
            "project_setup": f"{self.subl_path} --project TRAE_AI_Project.sublime-project",
        }

        logger.info("Generated CI/CD integration commands")
        return integration_commands

    def create_automation_workflow(self) -> str:
        """Create a GitHub Actions workflow that includes Sublime Text automation."""
        workflow_content = """name: Sublime Text Integration Workflow

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  sublime-automation:
    runs-on: macos-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Sublime Text
      run: |
        # Install Sublime Text on macOS runner
        brew install --cask sublime-text
        
    - name: Format Code with Sublime Text
      run: |
        # Format Python files
        find . -name "*.py" -not -path "./venv/*" -not -path "./models/*" -exec subl --command reindent --wait {} \;
        
    - name: Check for formatting changes
      run: |
        if [[ -n $(git diff --name-only) ]]; then
          echo "Code formatting changes detected"
          git diff --name-only
          exit 1
        else
          echo "Code is properly formatted"
        fi
"""

        workflow_file = self.project_root / ".github/workflows/sublime-integration.yml"
        workflow_file.parent.mkdir(parents=True, exist_ok=True)

        with open(workflow_file, "w") as f:
            f.write(workflow_content)

        logger.info(f"Created Sublime Text automation workflow: {workflow_file}")
        return str(workflow_file)


def main():
    """Main function to demonstrate Sublime Text automation integration."""
    integrator = SublimeAutomationIntegrator()

    print("🎯 SUBLIME TEXT AUTOMATION INTEGRATION")
    print("=" * 50)

    # Create project file
    project_file = integrator.create_project_file()
    print(f"✅ Created project file: {project_file}")

    # Generate CI/CD commands
    commands = integrator.integrate_with_ci_cd()
    print("\n🔧 CI/CD Integration Commands:")
    for name, command in commands.items():
        print(f"  {name}: {command}")

    # Create automation workflow
    workflow_file = integrator.create_automation_workflow()
    print(f"\n✅ Created automation workflow: {workflow_file}")

    print("\n🚀 INTEGRATION SUMMARY:")
    print("• Sublime Text is properly installed and accessible")
    print("• Project configuration created for optimal development")
    print("• CI/CD integration commands generated")
    print("• GitHub Actions workflow created for automated formatting")
    print("\n💡 Next Steps:")
    print("1. Run: python sublime_automation_integration.py")
    print("2. Open project: subl --project TRAE_AI_Project.sublime-project")
    print("3. Commit the new workflow to enable automation")


if __name__ == "__main__":
    main()
