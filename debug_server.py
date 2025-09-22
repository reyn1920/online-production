#!/usr/bin/env python3
"""
Debug server for Trae AI FastAPI Application
This script starts the FastAPI server with debugpy for remote debugging.
"""
import debugpy
import uvicorn
from backend.api.main import app


def start_debug_server():
    """Start the FastAPI server with debugpy enabled."""
    # Enable debugpy for remote debugging
    debugpy.listen(("0.0.0.0", 5678))
    print("🐛 Debugpy listening on port 5678")
    print("🔗 Attach your debugger to localhost:5678")

    # Optionally wait for debugger to attach
    # debugpy.wait_for_client()

    # Start the FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True, log_level="info")


if __name__ == "__main__":
    start_debug_server()
