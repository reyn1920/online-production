#!/usr/bin/env python3
"""
AI Model Generation Repair Script

This script diagnoses and repairs common issues with AI model generation,
specifically for the Linly - Talker avatar generation system.

Author: Trae AI Assistant
Date: 2025 - 01 - 27
"""

import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("model_repair.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class ModelGenerationRepair:
    """Comprehensive repair system for AI model generation issues."""

    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.linly_talker_path = self.base_path / "models" / "linly_talker"
        self.checkpoints_path = self.linly_talker_path / "checkpoints"
        self.backend_path = self.base_path / "backend"

        # Critical model files that should exist
        self.required_checkpoints = [
            "wav2lip_gan.pth",
            "SadTalker_V0.0.2_256.safetensors",
            "mapping_00109 - model.pth.tar",
            "Obama_ave.pth",
            "Obama.json",
        ]

        # Critical directories
        self.required_dirs = [
            "GPT_SoVITS/pretrained_models",
            "MuseTalk",
            "gfpgan/weights",
        ]

    def check_environment(self) -> Dict[str, Any]:
        """Check the current environment and identify issues."""
        logger.info("🔍 Checking environment...")

        issues = []
        status = {
            "checkpoints_exist": False,
            "models_downloaded": False,
            "test_mode_disabled": False,
            "services_running": False,
            "issues": issues,
        }

        # Check if checkpoints directory exists and has content
        if not self.checkpoints_path.exists():
            issues.append("Checkpoints directory does not exist")
        else:
            checkpoint_files = (
                list(self.checkpoints_path.glob("*.pth"))
                + list(self.checkpoints_path.glob("*.safetensors"))
                + list(self.checkpoints_path.glob("*.tar"))
            )

            if len(checkpoint_files) < 3:  # Should have multiple checkpoint files
                issues.append(
                    f"Only {
                        len(checkpoint_files)} checkpoint files found, expected more"
                )
            else:
                status["checkpoints_exist"] = True
                logger.info(f"✅ Found {len(checkpoint_files)} checkpoint files")

        # Check for required model files
        missing_files = []
        for required_file in self.required_checkpoints:
            if not (self.checkpoints_path / required_file).exists():
                missing_files.append(required_file)

        if missing_files:
            issues.append(
                f"Missing required checkpoint files: {
                    ', '.join(missing_files)}"
            )
        else:
            status["models_downloaded"] = True
            logger.info("✅ All required checkpoint files found")

        # Check avatar engines configuration
        avatar_engines_file = self.backend_path / "services" / "avatar_engines.py"
        if avatar_engines_file.exists():
            with open(avatar_engines_file, "r") as f:
                content = f.read()
                if "'test_mode': False" in content:
                    status["test_mode_disabled"] = True
                    logger.info("✅ Test mode is disabled")
                else:
                    issues.append("Avatar engines still in test mode")
        else:
            issues.append("Avatar engines configuration file not found")

        # Check if download is in progress
        download_processes = self._check_download_processes()
        if download_processes:
            logger.info(
                f"📥 Model download in progress: {
                    len(download_processes)} processes"
            )
            status["download_in_progress"] = True

        return status

    def _check_download_processes(self) -> List[str]:
        """Check if model download processes are running."""
        try:
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, check=True
            )

            download_processes = []
            for line in result.stdout.split("\\n"):
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "download_models.sh",
                        "huggingface_download",
                        "modelscope_download",
                    ]
                ):
                    download_processes.append(line.strip())

            return download_processes
        except subprocess.CalledProcessError:
            return []

    def repair_test_mode(self) -> bool:
        """Disable test mode in avatar engines."""
        logger.info("🔧 Repairing test mode configuration...")

        avatar_engines_file = self.backend_path / "services" / "avatar_engines.py"
        if not avatar_engines_file.exists():
            logger.error("Avatar engines file not found")
            return False

        try:
            with open(avatar_engines_file, "r") as f:
                content = f.read()

            # Replace test_mode: True with test_mode: False
            updated_content = content.replace("'test_mode': True", "'test_mode': False")

            if updated_content != content:
                with open(avatar_engines_file, "w") as f:
                    f.write(updated_content)
                logger.info("✅ Test mode disabled successfully")
                return True
            else:
                logger.info("✅ Test mode already disabled")
                return True

        except Exception as e:
            logger.error(f"Failed to repair test mode: {e}")
            return False

    def download_missing_models(self) -> bool:
        """Download missing model files."""
        logger.info("📥 Downloading missing models...")

        if not self.linly_talker_path.exists():
            logger.error("Linly - Talker directory not found")
            return False

        download_script = self.linly_talker_path / "scripts" / "download_models.sh"
        if not download_script.exists():
            logger.error("Download script not found")
            return False

        try:
            # Try Huggingface download (option 2)
            logger.info("Starting model download from Huggingface...")
            process = subprocess.Popen(
                ["bash", str(download_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(self.linly_talker_path),
            )

            # Send option 2 (Huggingface) to the script
            stdout, stderr = process.communicate(input="2\\n")

            if process.returncode == 0:
                logger.info("✅ Model download completed successfully")
                return True
            else:
                logger.error(f"Model download failed: {stderr}")
                return False

        except Exception as e:
            logger.error(f"Failed to start model download: {e}")
            return False

    def restart_services(self) -> bool:
        """Restart avatar generation services."""
        logger.info("🔄 Restarting avatar generation services...")

        try:
            # Kill existing demo processes
            subprocess.run(
                ["pkill", "-f", "demo_app.py"],
                check=False,  # Don't fail if no process found
            )

            # Wait a moment for cleanup

            import time

            time.sleep(2)

            # Start the demo app
            demo_script = self.linly_talker_path / "demo_app.py"
            if demo_script.exists():
                logger.info("Starting Linly - Talker demo...")
                subprocess.Popen(
                    ["python", str(demo_script)], cwd=str(self.linly_talker_path)
                )
                logger.info("✅ Services restarted")
                return True
            else:
                logger.error("Demo script not found")
                return False

        except Exception as e:
            logger.error(f"Failed to restart services: {e}")
            return False

    def create_fallback_config(self) -> bool:
        """Create a fallback configuration for model generation."""
        logger.info("🛠️ Creating fallback configuration...")

        fallback_config = {
            "avatar_generation": {
                "fallback_mode": True,
                "use_basic_models": True,
                "skip_heavy_processing": True,
                "enable_caching": True,
            },
            "model_paths": {
                "wav2lip": "checkpoints/wav2lip_gan.pth",
                "sadtalker": "checkpoints/SadTalker_V0.0.2_256.safetensors",
                "mapping": "checkpoints/mapping_00109 - model.pth.tar",
            },
            "performance": {
                "max_video_length": 30,
                "reduce_quality_if_needed": True,
                "timeout_seconds": 120,
            },
        }

        try:
            config_file = self.base_path / "config" / "fallback_avatar_config.json"
            config_file.parent.mkdir(exist_ok=True)

            with open(config_file, "w") as f:
                json.dump(fallback_config, f, indent=2)

            logger.info(f"✅ Fallback configuration created: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create fallback config: {e}")
            return False

    def run_comprehensive_repair(self) -> Dict[str, Any]:
        """Run a comprehensive repair of the model generation system."""
        logger.info("🚀 Starting comprehensive model generation repair...")

        # Step 1: Diagnose current state
        status = self.check_environment()
        logger.info(f"Current status: {json.dumps(status, indent = 2)}")

        repair_results = {
            "initial_status": status,
            "repairs_attempted": [],
            "repairs_successful": [],
            "final_status": None,
        }

        # Step 2: Repair test mode
        if not status.get("test_mode_disabled", False):
            repair_results["repairs_attempted"].append("test_mode_repair")
            if self.repair_test_mode():
                repair_results["repairs_successful"].append("test_mode_repair")

        # Step 3: Download models if needed
        if not status.get("models_downloaded", False):
            repair_results["repairs_attempted"].append("model_download")
            if self.download_missing_models():
                repair_results["repairs_successful"].append("model_download")

        # Step 4: Create fallback configuration
        repair_results["repairs_attempted"].append("fallback_config")
        if self.create_fallback_config():
            repair_results["repairs_successful"].append("fallback_config")

        # Step 5: Restart services
        repair_results["repairs_attempted"].append("service_restart")
        if self.restart_services():
            repair_results["repairs_successful"].append("service_restart")

        # Step 6: Final status check
        repair_results["final_status"] = self.check_environment()

        logger.info("🎉 Comprehensive repair completed!")
        logger.info(f"Repair results: {json.dumps(repair_results, indent = 2)}")

        return repair_results


def main():
    """Main function to run the repair script."""
    print("🔧 AI Model Generation Repair Tool")
    print("===================================")

    # Get base path from command line or use current directory
    base_path = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    # Initialize repair system
    repair_system = ModelGenerationRepair(base_path)

    # Run comprehensive repair
    results = repair_system.run_comprehensive_repair()

    # Print summary
    print("\\n📊 REPAIR SUMMARY")
    print("==================")
    print(f"Repairs attempted: {len(results['repairs_attempted'])}")
    print(f"Repairs successful: {len(results['repairs_successful'])}")

    if results["repairs_successful"]:
        print("\\n✅ Successful repairs:")
        for repair in results["repairs_successful"]:
            print(f"  - {repair}")

    remaining_issues = results["final_status"].get("issues", [])
    if remaining_issues:
        print("\\n⚠️ Remaining issues:")
        for issue in remaining_issues:
            print(f"  - {issue}")
    else:
        print("\\n🎉 All issues resolved!")

    print("\\n📝 Check 'model_repair.log' for detailed logs.")

    return 0 if not remaining_issues else 1


if __name__ == "__main__":
    sys.exit(main())
