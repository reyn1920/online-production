#!/usr / bin / env python3
""""""
Watchdog service monitor with debounce logic and restart policy support.
Rule - 1 compliant monitoring system for the runtime environment.
""""""

import logging
import os
import signal
import subprocess
import sys
import time
from collections import deque
from pathlib import Path

import yaml

# Configure logging
logging.basicConfig(
    level = logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )
logger = logging.getLogger("watchdog")

# Debounce tracking
_last_warn = {}


def _should_warn(service_name: str, min_interval = 10):
    """Debounce warning messages to prevent spam."""
    now = time.time()
    t = _last_warn.get(service_name, 0)
    if now - t >= min_interval:
        _last_warn[service_name] = now
        return True
    return False


def load_services_config():
    """Load services configuration from config / services.yaml."""
    config_path = Path("config / services.yaml")
    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return {}

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            return config.get("services", {})
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def is_running(service_name: str) -> bool:
    """Check if a service is running by looking for its process."""
    try:
        # Check for monitoring_system specifically
        if service_name == "monitoring_system":
            result = subprocess.run(
                ["pgrep", "-f", "trae_ai.monitoring_system"],
                    capture_output = True,
                    text = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
            return result.returncode == 0
        return False
    except Exception as e:
        logger.error(f"Error checking if {service_name} is running: {e}")
        return False


def schedule_restart(service_name: str):
    """Schedule a service restart."""
    try:
        if service_name == "monitoring_system":
            # Use the launcher script
            launcher_path = "tools / monitoring_system_launcher.py"
            if os.path.exists(launcher_path):
                subprocess.Popen(
                    [sys.executable, launcher_path],
                        stdout = subprocess.DEVNULL,
                        stderr = subprocess.DEVNULL,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                logger.info(f"Started {service_name} via launcher")
            else:
                # Fallback to direct execution
                subprocess.Popen(
                    [sys.executable, "-m", "trae_ai.monitoring_system"],
                        stdout = subprocess.DEVNULL,
                        stderr = subprocess.DEVNULL,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                logger.info(f"Started {service_name} directly")
    except Exception as e:
        logger.error(f"Failed to restart {service_name}: {e}")


def monitor_services():
    """Main monitoring loop."""
    registry = load_services_config()

    while True:
        try:
            # Check monitoring_system
            if not is_running("monitoring_system"):
                svc = registry.get("monitoring_system", {})

                if _should_warn("monitoring_system", 10):
                    logger.warning("⚠️ Service monitoring_system is not running")

                # Check if service should be restarted
                if (
                    svc.get("critical", False)
                    or svc.get("restart_policy", {}).get("mode") == "always"
# BRACKET_SURGEON: disabled
#                 ):
                    schedule_restart("monitoring_system")
                    logger.info(
                        "🔁 Restart scheduled: monitoring_system (policy = always)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                    # Apply backoff if configured
                    backoff = svc.get("restart_policy", {}).get("backoff_seconds", 2)
                    time.sleep(backoff)
                else:
                    logger.info(
                        "ℹ️ Service monitoring_system marked non - critical,"
    restart skipped (config).""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Sleep before next check
            time.sleep(5)

        except KeyboardInterrupt:
            logger.info("Watchdog shutting down...")
            break
        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(5)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info("Starting watchdog service monitor...")
    monitor_services()

if __name__ == "__main__":
    main()