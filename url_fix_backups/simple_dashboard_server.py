#!/usr / bin / env python3
"""
Simple standalone server for comprehensive dashboard
"""

import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Create FastAPI app
app = FastAPI(title="Comprehensive Dashboard")

# Mount static files if they exist
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

try:
    # Import the comprehensive dashboard router

    from routers.comprehensive_dashboard import router as dashboard_router

    app.include_router(dashboard_router, prefix="/comprehensive - dashboard")
    print("✓ Comprehensive dashboard router loaded successfully")
except ImportError as e:
    print(f"✗ Failed to import comprehensive dashboard router: {e}")

    # Create a fallback route
    @app.get("/comprehensive - dashboard")
    async def fallback_dashboard():
        return HTMLResponse(
            """
        <html>
            <head><title > Dashboard Loading...</title></head>
            <body>
                <h1 > Comprehensive Dashboard</h1>
                <p > Dashboard router is being initialized...</p>
                <p > Error: Router import failed</p>
            </body>
        </html>
        """
        )


@app.get("/")
async def root():
    return {"message": "Comprehensive Dashboard Server", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    print("Starting simple dashboard server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
