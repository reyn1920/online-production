#!/usr / bin / env python3
""""""
Creative Environment Setup Script

This script creates and manages an isolated Python virtual environment
specifically for creative tools (Linly - Talker, Blender, AI models) to
prevent dependency conflicts with the main application.

Usage:
    python scripts / setup_creative_environment.py [--force] [--update]

Options:
    --force: Force recreation of the environment even if it exists
    --update: Update existing environment with new dependencies
""""""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class CreativeEnvironmentManager:
    """Manages the isolated creative environment setup and maintenance."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.creative_env_path = self.project_root / "venv_creative"
        self.requirements_file = self.project_root / "requirements_creative.txt"
        self.main_env_path = self.project_root / "venv"

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are available."""
        logger.info("Checking prerequisites...")

        # Check Python version
        if sys.version_info < (3, 8):
            logger.error("Python 3.8 or higher is required")
            return False

        # Check if requirements file exists
        if not self.requirements_file.exists():
            logger.error(f"Requirements file not found: {self.requirements_file}")
            return False

        # Check if virtualenv is available
        try:
            subprocess.run(
                [sys.executable, "-m", "venv", "--help"],
                capture_output=True,
                check=True,
# BRACKET_SURGEON: disabled
#             )
        except subprocess.CalledProcessError:
            logger.error("Python venv module is not available")
            return False

        logger.info("All prerequisites satisfied")
        return True

    def create_environment(self, force: bool = False) -> bool:
        """Create the creative virtual environment."""
        if self.creative_env_path.exists():
            if not force:
                logger.info(f"Creative environment already exists at {self.creative_env_path}")
                return True
            else:
                logger.info("Removing existing creative environment...")
                shutil.rmtree(self.creative_env_path)

        logger.info(f"Creating creative environment at {self.creative_env_path}...")

        try:
            # Create virtual environment
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "venv",
                    str(self.creative_env_path),
                    "--prompt",
                    "creative - pipeline",
# BRACKET_SURGEON: disabled
#                 ],
                check=True,
# BRACKET_SURGEON: disabled
#             )

            logger.info("Creative environment created successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create creative environment: {e}")
            return False

    def get_pip_executable(self) -> str:
        """Get the pip executable path for the creative environment."""
        if os.name == "nt":  # Windows
            return str(self.creative_env_path / "Scripts" / "pip.exe")
        else:  # Unix - like
            return str(self.creative_env_path / "bin" / "pip")

    def get_python_executable(self) -> str:
        """Get the Python executable path for the creative environment."""
        if os.name == "nt":  # Windows
            return str(self.creative_env_path / "Scripts" / "python.exe")
        else:  # Unix - like
            return str(self.creative_env_path / "bin" / "python")

    def install_dependencies(self) -> bool:
        """Install creative dependencies in the isolated environment."""
        logger.info("Installing creative dependencies...")

        pip_executable = self.get_pip_executable()

        try:
            # Upgrade pip first
            subprocess.run([pip_executable, "install", "--upgrade", "pip"], check=True)

            # Install wheel for better package compilation
            subprocess.run([pip_executable, "install", "wheel"], check=True)

            # Install creative dependencies
            subprocess.run(
                [pip_executable, "install", "-r", str(self.requirements_file)],
                check=True,
# BRACKET_SURGEON: disabled
#             )

            logger.info("Creative dependencies installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False

    def create_activation_script(self) -> bool:
        """Create a convenient activation script."""
        logger.info("Creating activation script...")

        script_content = f"""#!/bin / bash"""
# Creative Environment Activation Script
# This script activates the isolated creative environment

echo "Activating creative environment..."
source "{self.creative_env_path}/bin / activate"
echo "Creative environment activated. Python: $(which python)"
echo "Available creative tools:"
echo "  - Linly - Talker dependencies"
echo "  - Blender Python API"
echo "  - AI model libraries"
echo "  - Video / Audio processing tools"
echo ""
echo "To deactivate, run: deactivate"
""""""

        script_path = self.project_root / "activate_creative.sh"

        try:
            with open(script_path, "w") as f:
                f.write(script_content)

            # Make script executable
            os.chmod(script_path, 0o755)

            logger.info(f"Activation script created: {script_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create activation script: {e}")
            return False

    def create_environment_info(self) -> bool:
        """Create environment information file."""
        info_content = f"""# Creative Environment Information"""

This directory contains an isolated Python virtual environment specifically
for creative tools and AI models used in the TRAE.AI pipeline.

## Purpose
- Isolate creative tool dependencies from main application
- Prevent version conflicts between different components
- Ensure stable operation of Linly - Talker, Blender, and AI models

## Contents
- Pinned versions of all creative dependencies
- PyTorch and related ML libraries
- Video / Audio processing tools
- 3D modeling and rendering utilities
- Face detection and processing libraries

## Usage
Activate this environment before running creative tasks:
```bash
source venv_creative / bin / activate
# or use the convenience script:
./activate_creative.sh
```

## Maintenance
To update this environment:
```bash
python scripts / setup_creative_environment.py --update
```

## Environment Path
{self.creative_env_path}

## Requirements File
{self.requirements_file}

## Created: {subprocess.check_output(['date']).decode().strip()}
""""""

        info_path = self.creative_env_path / "ENVIRONMENT_INFO.md"

        try:
            with open(info_path, "w") as f:
                f.write(info_content)

            logger.info(f"Environment info created: {info_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create environment info: {e}")
            return False

    def verify_installation(self) -> bool:
        """Verify that packages from requirements file are installed correctly."""
        logger.info("Verifying installation...")

        python_executable = self.get_python_executable()

        # Read packages from requirements file
        packages_to_verify = []
        try:
            with open(self.requirements_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):"
                        # Extract package name (before any version specifiers)
                        package_name = line.split(">=")[0].split("==")[0].split("<")[0].strip()
                        if package_name:
                            # Map common package names to import names
                            import_name = {
                                "opencv - python": "cv2",
                                "Pillow": "PIL",
                                "PyYAML": "yaml",
                                "scikit - image": "skimage",
                                "scikit - learn": "sklearn",
                                "ffmpeg - python": "ffmpeg",
                            }.get(package_name, package_name)
                            packages_to_verify.append((package_name, import_name))
        except Exception as e:
            logger.warning(f"Could not read requirements file: {e}")
            return True  # Skip verification if requirements file is empty or unreadable

        if not packages_to_verify:
            logger.info("No packages to verify (empty requirements file)")
            return True

        for package_name, import_name in packages_to_verify:
            try:
                result = subprocess.run(
                    [
                        python_executable,
                        "-c",
                        f"import {import_name}; print(f'{package_name} imported successfully')",
# BRACKET_SURGEON: disabled
#                     ],
                    capture_output=True,
                    text=True,
                    check=True,
# BRACKET_SURGEON: disabled
#                 )

                logger.info(f"✓ {package_name}: {result.stdout.strip()}")

            except subprocess.CalledProcessError as e:
                logger.error(f"✗ {package_name}: Failed to import - {e.stderr}")
                return False

        logger.info("All key packages verified successfully")
        return True

    def update_environment(self) -> bool:
        """Update existing environment with new dependencies."""
        if not self.creative_env_path.exists():
            logger.error("Creative environment does not exist. Create it first.")
            return False

        logger.info("Updating creative environment...")
        return self.install_dependencies()

    def get_environment_status(self) -> dict:
        """Get status information about the creative environment."""
        status = {
            "exists": self.creative_env_path.exists(),
            "path": str(self.creative_env_path),
            "requirements_file": str(self.requirements_file),
            "requirements_exists": self.requirements_file.exists(),
# BRACKET_SURGEON: disabled
#         }

        if status["exists"]:
            python_executable = self.get_python_executable()
            try:
                # Get Python version
                result = subprocess.run(
                    [python_executable, "--version"],
                    capture_output=True,
                    text=True,
                    check=True,
# BRACKET_SURGEON: disabled
#                 )
                status["python_version"] = result.stdout.strip()

                # Get installed packages count
                result = subprocess.run(
                    [self.get_pip_executable(), "list", "--format = freeze"],
                    capture_output=True,
                    text=True,
                    check=True,
# BRACKET_SURGEON: disabled
#                 )
                status["installed_packages"] = len(result.stdout.strip().split("\\n"))

            except subprocess.CalledProcessError:
                status["python_version"] = "Unknown"
                status["installed_packages"] = 0

        return status

    def setup_complete_environment(self, force: bool = False, update: bool = False) -> bool:
        """Complete setup process for the creative environment."""
        logger.info("Starting creative environment setup...")

        if update:
            return self.update_environment()

        if not self.check_prerequisites():
            return False

        if not self.create_environment(force):
            return False

        if not self.install_dependencies():
            return False

        if not self.create_activation_script():
            return False

        if not self.create_environment_info():
            return False

        if not self.verify_installation():
            return False

        logger.info("Creative environment setup completed successfully!")
        logger.info(f"Environment location: {self.creative_env_path}")
        logger.info(f"Activation script: {self.project_root}/activate_creative.sh")

        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup isolated creative environment for TRAE.AI")
    parser.add_argument("--force", action="store_true", help="Force recreation of environment")
    parser.add_argument("--update", action="store_true", help="Update existing environment")
    parser.add_argument("--status", action="store_true", help="Show environment status")

    args = parser.parse_args()

    # Get project root (assuming script is in scripts/ subdirectory)
    project_root = Path(__file__).parent.parent

    manager = CreativeEnvironmentManager(str(project_root))

    if args.status:
        status = manager.get_environment_status()
        print("\\nCreative Environment Status:")
        print(f"  Exists: {status['exists']}")
        print(f"  Path: {status['path']}")
        print(f"  Requirements file: {status['requirements_exists']}")
        if status["exists"]:
            print(f"  Python version: {status.get('python_version', 'Unknown')}")
            print(f"  Installed packages: {status.get('installed_packages', 0)}")
        return

    success = manager.setup_complete_environment(force=args.force, update=args.update)

    if success:
        print("\\n🎉 Creative environment setup completed successfully!")
        print("\\nNext steps:")
        print("1. Activate the environment: ./activate_creative.sh")
        print("2. Test creative tools: python -c 'import torch; print(torch.__version__)'")
        print("3. Update self_repair_agent.py to use this environment for creative tasks")
        sys.exit(0)
    else:
        print("\\n❌ Creative environment setup failed. Check logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()