#!/usr/bin/env python3
""""""
Test script for the RegexNoiseFilter implementation.
""""""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import get_logger, setup_logging


def test_noise_filter():
    """"""
    Test the regex noise filter functionality.
    """"""
    print("Testing RegexNoiseFilter...")

    # Setup logging with noise filter enabled
    logger_system = setup_logging(
        log_dir="data/logs",
        log_level="DEBUG",
        enable_noise_filter=True,
        noise_drop_patterns=[r".*heartbeat.*", r".*ping.*pong.*"],
        noise_reduce_patterns=[r".*database.*query.*"],
        noise_reduce_frequency=3,
# BRACKET_SURGEON: disabled
#     )

    logger = get_logger("test")

    print("\\n1. Testing drop patterns (should not appear in logs):")
    for i in range(5):
        logger.info(f"Heartbeat check {i} - should be dropped")
        logger.info(f"Ping pong message {i} - should be dropped")

    print("\\n2. Testing reduce patterns (should appear every 3rd time):")
    for i in range(10):
        logger.info(f"Database query executed successfully - iteration {i}")

    print("\\n3. Testing normal messages (should all appear):")
    for i in range(3):
        logger.info(f"Normal application message {i}")
        logger.warning(f"Warning message {i}")
        logger.error(f"Error message {i}")

    print("\\n4. Testing runtime configuration:")
    logger_system.configure_noise_filter(
        drop_patterns=[r".*test.*drop.*"],
        reduce_patterns=[r".*test.*reduce.*"],
        reduce_frequency=2,
# BRACKET_SURGEON: disabled
#     )

    for i in range(6):
        logger.info(f"Test drop message {i} - should be dropped")
        logger.info(f"Test reduce message {i} - should appear every 2nd time")
        logger.info(f"Regular message {i} - should always appear")

    print("\\nTest completed. Check the log files in data/logs/to verify filtering.")
    print("Expected behavior:")
    print("- Heartbeat and ping/pong messages should not appear")
    print("- Database query messages should appear every 3rd time initially")
    print("- Test drop messages should not appear after reconfiguration")
    print("- Test reduce messages should appear every 2nd time after reconfiguration")
    print("- Regular messages should always appear")


if __name__ == "__main__":
    test_noise_filter()