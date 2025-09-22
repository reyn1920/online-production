#!/bin/bash

# Trae AI FastAPI Server Startup Script
# This script activates the virtual environment and starts the FastAPI server

echo "🚀 Starting Trae AI FastAPI Server..."

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Please create one first:"
    echo "   python -m venv .venv"
    echo "   source .venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source .venv/bin/activate

# Check if FastAPI is installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ FastAPI not found. Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📋 API Documentation available at http://localhost:8000/docs"
echo "🔍 Health check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the FastAPI server with uvicorn
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload