#!/usr/bin/env python3
"""
Simple VidScriptPro Test
"""

import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent / "backend"))

logging.basicConfig(level=logging.INFO)

try:
    from backend.content.vidscript_pro import VidScriptPro
    print("✅ VidScriptPro imports successful")
    
    script_gen = VidScriptPro()
    print("✅ VidScriptPro initialized successfully")
    
    # Check available attributes
    attrs = [attr for attr in dir(script_gen) if not attr.startswith('_')]
    print(f"📊 Available attributes: {attrs[:10]}...")  # Show first 10
    
    # Test simple script generation
    print("\n🎬 Testing script generation...")
    try:
        result = script_gen.generate_logline("A day in the life of an AI assistant")
        print(f"✅ Logline generation successful: {len(result)} characters")
        print(f"Sample: {result[:100]}...")
    except Exception as e:
        print(f"❌ Script generation failed: {e}")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()