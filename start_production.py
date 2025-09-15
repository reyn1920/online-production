#!/usr/bin/env python3
""""""
Production Startup Script for TRAE.AI
Loads production environment and starts the application with all services
""""""

import os
import sys

# Load production environment first

from dotenv import load_dotenv

# Load production environment variables
load_dotenv(".env.production", override=True)

# Set environment to production
os.environ["ENVIRONMENT"] = "production"
os.environ["USE_MOCK"] = "false"

print("🚀 Starting TRAE.AI in Production Mode...")
print(f"Environment: {os.getenv('ENVIRONMENT')}")
print(f"Secret Key Set: {'Yes' if os.getenv('SECRET_KEY') else 'No'}")
print(f"Autonomous Mode: {os.getenv('AUTONOMOUS_MODE')}")
print(f"Content Agent: {os.getenv('CONTENT_AGENT_ENABLED', 'true')}")

# Now import and run the main application
if __name__ == "__main__":
    try:
        # Import main after environment is set

        print("✅ Production environment loaded successfully")
    except Exception as e:
        print(f"❌ Failed to start production application: {e}")
        sys.exit(1)