#!/usr / bin / env python3
""""""
Minimal FastAPI server for debugging
""""""

import logging
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# BRACKET_SURGEON: disabled
# )
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Online Production API - Minimal",
    description="Minimal version for debugging",
    version="1.0.0",
# BRACKET_SURGEON: disabled
# )

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app",
# BRACKET_SURGEON: disabled
#     ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
# BRACKET_SURGEON: disabled
# )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Minimal server is running"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Online Production API - Minimal Mode",
        "status": "running",
        "endpoints": ["/health", "/docs"],
# BRACKET_SURGEON: disabled
#     }


if __name__ == "__main__":
    # Get configuration from environment
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))

    logger.info(f"🚀 Starting minimal server on {host}:{port}")
    logger.info(f"📖 API docs: http://{host}:{port}/docs")
    logger.info(f"❤️ Health check: http://{host}:{port}/health")

    uvicorn.run(app, host=host, port=port, reload=False, log_level="info")