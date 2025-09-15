#!/usr/bin/env python3
""""""
TTS Engine Debug Test
""""""

import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO)

try:
    from backend.tts_engine import TTSEngine

    print("✅ TTS Engine imports successful")

    try:
        engine = TTSEngine()
        print("✅ TTS Engine initialized successfully")
        print(f"📁 Cache directory: {engine.cache_dir}")
        print(f"🎯 Default config: {engine.default_config}")
        print(f"📊 Available models: {len(engine.available_models)}")

        # List first few models
        if engine.available_models:
            print("🎤 Sample models:")
            for i, (model_name, model_info) in enumerate(list(engine.available_models.items())[:3]):
                print(f"  {i + 1}. {model_name}")

    except Exception as e:
        print(f"❌ TTS Engine initialization failed: {e}")
        print(f"Error type: {type(e).__name__}")

        import traceback

        traceback.print_exc()

except ImportError as e:
    print(f"❌ TTS Engine import failed: {e}")
    print("This might be due to missing Coqui TTS dependency")
    print("Install with: pip install TTS")