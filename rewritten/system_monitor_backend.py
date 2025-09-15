#!/usr/bin/env python3
""""""
System Resource Monitor Backend
A Flask server that provides real-time system statistics via REST API.
""""""

from flask import Flask, jsonify
from flask_cors import CORS
import psutil
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access


@app.route("/api/system-stats", methods=["GET"])
def get_system_stats():
    """"""
    Get current system statistics including CPU and memory usage.

    Returns:
        JSON object with cpu_percent and memory_percent
    """"""
    try:
        # Get CPU usage percentage (1 second interval for accuracy)
        cpu_percent = psutil.cpu_percent(interval=1)

        # Get memory usage statistics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Prepare response data
        stats = {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory_percent, 1),
            "timestamp": psutil.time.time(),
# BRACKET_SURGEON: disabled
#         }

        logger.info(f"System stats: CPU {cpu_percent}%, Memory {memory_percent}%")
        return jsonify(stats)

    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        return (
            jsonify(
                {
                    "error": "Failed to retrieve system statistics",
                    "cpu_percent": 0,
                    "memory_percent": 0,
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             ),
            500,
# BRACKET_SURGEON: disabled
#         )


@app.route("/health", methods=["GET"])
def health_check():
    """"""
    Health check endpoint to verify server is running.
    """"""
    return jsonify({"status": "healthy", "service": "system-monitor-backend"})


if __name__ == "__main__":
    logger.info("Starting System Resource Monitor Backend...")
    logger.info("API endpoint: http://localhost:5001/api/system-stats")
    logger.info("Health check: http://localhost:5001/health")

    # Run the Flask development server
    app.run(host="0.0.0.0", port=5001, debug=True, threaded=True)