#!/usr / bin / env python3
"""
VidScriptPro Debug Test
"""

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent/"backend"))

logging.basicConfig(level = logging.INFO)

try:

    from backend.content.vidscript_pro import VidScriptPro

    print("✅ VidScriptPro imports successful")

    try:
        script_gen = VidScriptPro()
        print("✅ VidScriptPro initialized successfully")
        print(f"🤖 Model: {script_gen.model}")
        print(f"🌐 Base URL: {script_gen.base_url}")
        print(
            f"📊 Available methods: {[attr for attr in dir(script_gen) if not attr.startswith('_') \
    and callable(getattr(script_gen, attr))]}"
        )

    except Exception as e:
        print(f"❌ VidScriptPro initialization failed: {e}")
        print(f"Error type: {type(e).__name__}")

        import traceback

        traceback.print_exc()

except ImportError as e:
    print(f"❌ VidScriptPro import failed: {e}")
    print("This might be due to missing dependencies or Ollama not running")