#!/usr / bin / env python3
""""""
Test Avatar Generation Functionality

This script tests the avatar generation system to verify that models are working properly.
""""""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set minimal environment variables
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "test - secret - key - for - avatar - testing - only"
os.environ["DEBUG"] = "true"

try:

    from backend.services.avatar_engines import AvatarEngineManager, generate_avatar

    print("✅ Successfully imported avatar engine modules")
except ImportError as e:
    print(f"❌ Failed to import avatar engines: {e}")
    sys.exit(1)


async def test_avatar_generation():
    """Test the avatar generation functionality."""
    print("🧪 Testing Avatar Generation System")
    print("===================================")

    # Initialize the avatar engine manager
    try:
        manager = AvatarEngineManager()
        print(f"✅ Avatar Engine Manager initialized")
        print(f"📊 Available engines: {list(manager.engines.keys())}")

        # Initialize all engines
        print("\\n🔧 Initializing engines...")
        init_results = await manager.initialize_all_engines()
        print(f"📊 Engine initialization results: {init_results}")

    except Exception as e:
        print(f"❌ Failed to initialize Avatar Engine Manager: {e}")

        import traceback

        print(f"📊 Traceback: {traceback.format_exc()}")
        return False

    # Test engine registration
    for engine_name, engine in manager.engines.items():
        print(f"\\n🔧 Testing engine: {engine_name}")
        print(f"   Test mode: {getattr(engine, 'test_mode', 'Unknown')}")
        print(f"   Initialized: {getattr(engine, 'initialized', 'Unknown')}")

        # Try to get engine info
        try:
            info = (
                engine.get_engine_info()
                if hasattr(engine, "get_engine_info")
                else "No info method"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            print(f"   Engine info: {info}")
        except Exception as e:
            print(f"   ⚠️ Could not get engine info: {e}")

    # Test avatar generation with sample data
    print("\\n🎬 Testing avatar generation...")

    test_text = "Hello, this is a test of the avatar generation system."
    voice_settings = {
        "voice_style": "neutral",
            "speed": 1.0,
            "pitch": 1.0,
            "volume": 1.0,
# BRACKET_SURGEON: disabled
#             }
    video_settings = {
        "avatar_style": "professional",
            "duration": 5,
            "resolution": "720p",
            "fps": 25,
# BRACKET_SURGEON: disabled
#             }

    try:
        result = await generate_avatar(test_text, voice_settings, video_settings)
        print(f"✅ Avatar generation completed successfully!")
        print(f"📊 Result type: {type(result)}")
        print(
            f"📊 Result keys: {result.keys() if isinstance(result,"
# BRACKET_SURGEON: disabled
#     dict) else 'Not a dict'}""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if isinstance(result, dict):
            if "video_url" in result:
                print(f"🎥 Video URL: {result['video_url']}")
            if "audio_url" in result:
                print(f"🔊 Audio URL: {result['audio_url']}")
            if "status" in result:
                print(f"📈 Status: {result['status']}")
            if "error" in result:
                print(f"⚠️ Error: {result['error']}")

        return True

    except Exception as e:
        print(f"❌ Avatar generation failed: {e}")
        print(f"📊 Error type: {type(e)}")

        import traceback

        print(f"📊 Traceback: {traceback.format_exc()}")
        return False


def main():
    """Main test function."""
    print("🚀 Starting Avatar Generation Test")
    print("===================================")

    # Check if models exist
    models_path = project_root/"models"/"linly_talker" / "checkpoints"
    if models_path.exists():
        checkpoint_files = list(models_path.glob("*.pth")) + list(
            models_path.glob("*.safetensors")
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        print(f"📁 Found {len(checkpoint_files)} checkpoint files in {models_path}")
        for file in checkpoint_files[:5]:  # Show first 5 files
            print(f"   - {file.name}")
        if len(checkpoint_files) > 5:
            print(f"   ... and {len(checkpoint_files) - 5} more files")
    else:
        print(f"⚠️ Models directory not found: {models_path}")

    # Run the async test
    try:
        success = asyncio.run(test_avatar_generation())

        print("\\n📊 TEST SUMMARY")
        print("===============")
        if success:
            print("🎉 Avatar generation test PASSED!")
            print("✅ Models are loaded and working properly")
            return 0
        else:
            print("❌ Avatar generation test FAILED")
            print("⚠️ There may be issues with model loading or configuration")
            return 1

    except Exception as e:
        print(f"\\n💥 Test crashed with error: {e}")

        import traceback

        print(f"📊 Full traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())