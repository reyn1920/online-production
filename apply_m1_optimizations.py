#!/usr/bin/env python3
""""""
MacBook Air M1 Quick Optimization Script
Applies immediate performance optimizations based on system analysis
""""""

import os
import subprocess
import sys
from pathlib import Path

class M1QuickOptimizer:
    """Quick optimization script for M1 MacBook Air"""

    def __init__(self):
        self.optimizations_applied = []
        self.errors = []

    def run_command(self, command: str, description: str) -> bool:
        """Run a system command safely"""
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=30
# BRACKET_SURGEON: disabled
#             )

            if result.returncode == 0:
                self.optimizations_applied.append(f"✅ {description}")
                return True
            else:
                self.errors.append(f"❌ {description}: {result.stderr.strip()}")
                return False

        except Exception as e:
            self.errors.append(f"❌ {description}: {str(e)}")
            return False

    def optimize_memory_compression(self):
        """Enable memory compression for better RAM utilization"""
        print("🔧 Optimizing memory compression...")

        # Enable memory compression (requires sudo)
        print("   Note: Memory compression optimization requires admin privileges")
        print("   Run manually: sudo sysctl vm.compressor_mode=4")
        self.optimizations_applied.append("📝 Memory compression command provided (requires manual sudo execution)")

    def optimize_python_environment(self):
        """Optimize Python environment for M1"""
        print("🐍 Optimizing Python environment...")

        # Set MPS environment variables
        env_vars = {
            "PYTORCH_ENABLE_MPS_FALLBACK": "1",
            "PYTORCH_MPS_HIGH_WATERMARK_RATIO": "0.0",
            "OMP_NUM_THREADS": "8",
            "MKL_NUM_THREADS": "8"
# BRACKET_SURGEON: disabled
#         }

        # Create or update .zshrc with M1 optimizations
        zshrc_path = Path.home() / ".zshrc"

        try:
            # Read existing .zshrc
            existing_content = ""
            if zshrc_path.exists():
                with open(zshrc_path, 'r') as f:
                    existing_content = f.read()

            # Add M1 optimizations if not already present
            m1_section = "\n# M1 MacBook Air Optimizations\n""

            for var, value in env_vars.items():
                export_line = f"export {var}={value}\n"
                if export_line.strip() not in existing_content:
                    m1_section += export_line

            # Add Homebrew ARM64 path
            homebrew_path = 'export PATH="/opt/homebrew/bin:$PATH"\n'
            if homebrew_path.strip() not in existing_content:
                m1_section += homebrew_path

            if len(m1_section.strip()) > len("# M1 MacBook Air Optimizations"):"
                with open(zshrc_path, 'a') as f:
                    f.write(m1_section)

                self.optimizations_applied.append("✅ Updated .zshrc with M1 environment variables")
            else:
                self.optimizations_applied.append("✅ .zshrc already optimized for M1")

        except Exception as e:
            self.errors.append(f"❌ Failed to update .zshrc: {str(e)}")

    def optimize_fastapi_config(self):
        """Create optimized FastAPI configuration"""
        print("🚀 Creating optimized FastAPI configuration...")

        config_content = '''# M1 MacBook Air Optimized FastAPI Configuration'''

# Uvicorn Configuration
HOST = "0.0.0.0"
PORT = 8080
WORKERS = 4  # Optimal for M1 8-core system
WORKER_CLASS = "uvicorn.workers.UvicornWorker"
MAX_REQUESTS = 1000
MAX_REQUESTS_JITTER = 100
KEEPALIVE = 2

# Memory Management
WORKER_CONNECTIONS = 1000
WORKER_TMP_DIR = "/tmp"

# M1 Specific Optimizations
USE_UVLOOP = True  # Enable uvloop for better async performance
USE_MPS = True     # Enable Metal Performance Shaders

# Environment Variables for M1
import os
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["OMP_NUM_THREADS"] = "8"
os.environ["MKL_NUM_THREADS"] = "8"

# Gunicorn Configuration
bind = f"{HOST}:{PORT}"
workers = WORKERS
worker_class = WORKER_CLASS
max_requests = MAX_REQUESTS
max_requests_jitter = MAX_REQUESTS_JITTER
keepalive = KEEPALIVE
worker_connections = WORKER_CONNECTIONS
worker_tmp_dir = WORKER_TMP_DIR

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%%(h)s %%(l)s %%(u)s %%(t)s "%%(r)s" %%(s)s %%(b)s "%%(f)s" "%%(a)s" %%(D)s'
''''''

        try:
            config_path = Path("fastapi_m1_config.py")
            with open(config_path, 'w') as f:
                f.write(config_content)

            self.optimizations_applied.append(f"✅ Created optimized FastAPI config: {config_path}")

        except Exception as e:
            self.errors.append(f"❌ Failed to create FastAPI config: {str(e)}")

    def create_docker_optimization(self):
        """Create M1-optimized Dockerfile"""
        print("🐳 Creating M1-optimized Docker configuration...")

        dockerfile_content = '''# M1 MacBook Air Optimized Dockerfile'''
FROM --platform=linux/arm64 python:3.11-slim

# Set environment variables for M1 optimization
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTORCH_ENABLE_MPS_FALLBACK=1 \
    OMP_NUM_THREADS=8 \
    MKL_NUM_THREADS=8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Use optimized startup command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
''''''

        docker_compose_content = '''# M1 MacBook Air Optimized Docker Compose'''
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      platforms:
        - linux/arm64
    ports:
      - "8080:8080"
    environment:
      - PYTORCH_ENABLE_MPS_FALLBACK=1
      - OMP_NUM_THREADS=8
      - MKL_NUM_THREADS=8
    volumes:
      - .:/app
    restart: unless-stopped

  # Optional: Add Redis for caching (ARM64 optimized)
  redis:
    image: redis:7-alpine
    platform: linux/arm64
    ports:
      - "6379:6379"
    restart: unless-stopped
''''''

        try:
            # Create Dockerfile
            dockerfile_path = Path("Dockerfile.m1")
            with open(dockerfile_path, 'w') as f:
                f.write(dockerfile_content)

            # Create docker-compose
            compose_path = Path("docker-compose.m1.yml")
            with open(compose_path, 'w') as f:
                f.write(docker_compose_content)

            self.optimizations_applied.extend([
                f"✅ Created M1-optimized Dockerfile: {dockerfile_path}",
                f"✅ Created M1-optimized Docker Compose: {compose_path}"
# BRACKET_SURGEON: disabled
#             ])

        except Exception as e:
            self.errors.append(f"❌ Failed to create Docker configs: {str(e)}")

    def create_optimization_script(self):
        """Create a startup script with M1 optimizations"""
        print("📜 Creating M1 optimization startup script...")

        script_content = '''#!/bin/bash'''
# M1 MacBook Air Optimization Startup Script

echo "🍎 Starting M1 MacBook Air Optimizations..."

# Set M1-specific environment variables
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export OMP_NUM_THREADS=8
export MKL_NUM_THREADS=8
export DOCKER_BUILDKIT=1

# Add Homebrew ARM64 to PATH
export PATH="/opt/homebrew/bin:$PATH"

echo "✅ Environment variables set for M1 optimization"

# Check if uvloop is installed
if ! python -c "import uvloop" 2>/dev/null; then
    echo "📦 Installing uvloop for better async performance..."
    pip install uvloop
fi

# Start FastAPI with M1-optimized settings
echo "🚀 Starting FastAPI with M1 optimizations..."

if [ -f "fastapi_m1_config.py" ]; then
    echo "Using M1-optimized configuration"
    gunicorn -c fastapi_m1_config.py main:app
else
    echo "Using default M1-optimized settings"
    uvicorn main:app --host 0.0.0.0 --port 8080 --workers 4
fi
''''''

        try:
            script_path = Path("start_m1_optimized.sh")
            with open(script_path, 'w') as f:
                f.write(script_content)

            # Make script executable
            os.chmod(script_path, 0o755)

            self.optimizations_applied.append(f"✅ Created M1 startup script: {script_path}")

        except Exception as e:
            self.errors.append(f"❌ Failed to create startup script: {str(e)}")

    def run_all_optimizations(self):
        """Run all available optimizations"""
        print("🚀 Applying M1 MacBook Air Optimizations...\n")

        # Apply optimizations
        self.optimize_memory_compression()
        self.optimize_python_environment()
        self.optimize_fastapi_config()
        self.create_docker_optimization()
        self.create_optimization_script()

        # Print results
        print("\n" + "="*80)
        print("🎉 M1 Optimization Results")
        print("="*80)

        if self.optimizations_applied:
            print("\n✅ SUCCESSFULLY APPLIED:")
            for opt in self.optimizations_applied:
                print(f"   {opt}")

        if self.errors:
            print("\n❌ ERRORS ENCOUNTERED:")
            for error in self.errors:
                print(f"   {error}")

        print("\n💡 NEXT STEPS:")
        print("   1. Restart your terminal to apply .zshrc changes")
        print("   2. Run: source ~/.zshrc")
        print("   3. Install uvloop: pip install uvloop")
        print("   4. Use the created startup script: ./start_m1_optimized.sh")
        print("   5. For memory compression: sudo sysctl vm.compressor_mode=4")

        print("\n🔧 CONFIGURATION FILES CREATED:")
        print("   • fastapi_m1_config.py - Optimized FastAPI configuration")
        print("   • Dockerfile.m1 - M1-optimized Docker container")
        print("   • docker-compose.m1.yml - M1-optimized Docker Compose")
        print("   • start_m1_optimized.sh - M1 startup script")

        print("\n" + "="*80)

        return len(self.errors) == 0

def main():
    """Main function"""
    optimizer = M1QuickOptimizer()

    try:
        success = optimizer.run_all_optimizations()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n⚠️ Optimization interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())