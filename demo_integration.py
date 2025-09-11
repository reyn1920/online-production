#!/usr/bin/env python3
"""
Linly Talker + DaVinci Resolve + Blender Integration Demo

This script demonstrates how to use the AI video production pipeline
with sample content and configurations.

Usage:
    python demo_integration.py
"""

import os
import sys
import time
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ai_video_pipeline import AIVideoProductionPipeline


def create_sample_assets():
    """Create sample assets for demonstration"""

    assets_dir = "/Users/thomasbrianreynolds/online production/sample_assets"
    os.makedirs(assets_dir, exist_ok=True)

    # Sample script content
    sample_scripts = {
        "welcome": """
        Hello and welcome to our AI-powered video production demonstration.
        Today, I'll show you how artificial intelligence can create 
        professional-quality videos with minimal human intervention.
        This technology represents the future of content creation.
        """,
        "business_presentation": """
        Good morning, team. Let me present our quarterly results.
        Our revenue has grown by 25% this quarter, exceeding all expectations.
        The new AI integration features have been particularly successful,
        driving both customer satisfaction and operational efficiency.
        """,
        "educational": """
        In this lesson, we'll explore the fundamentals of machine learning.
        Machine learning is a subset of artificial intelligence that enables
        computers to learn and improve from experience without being explicitly programmed.
        Let's dive into the key concepts and practical applications.
        """,
    }

    # Save sample scripts
    for name, content in sample_scripts.items():
        script_path = os.path.join(assets_dir, f"{name}_script.txt")
        with open(script_path, "w") as f:
            f.write(content.strip())
        print(f"✓ Created sample script: {script_path}")

    return assets_dir, sample_scripts


def run_system_check():
    """Run comprehensive system check"""

    print("\n" + "=" * 60)
    print("AI VIDEO PRODUCTION PIPELINE - SYSTEM CHECK")
    print("=" * 60)

    # Initialize pipeline
    config_path = "/Users/thomasbrianreynolds/online production/pipeline_config.json"
    pipeline = AIVideoProductionPipeline(config_path)

    return pipeline


def demo_basic_integration():
    """Demonstrate basic integration workflow"""

    print("\n" + "=" * 60)
    print("DEMO: BASIC AI AVATAR GENERATION")
    print("=" * 60)

    # Create sample assets
    assets_dir, sample_scripts = create_sample_assets()

    # Initialize pipeline
    config_path = "/Users/thomasbrianreynolds/online production/pipeline_config.json"
    pipeline = AIVideoProductionPipeline(config_path)

    # Use welcome script
    script_text = sample_scripts["welcome"]

    print(f"\nScript to be processed:")
    print(f"'{script_text[:100]}...'")

    # Run pipeline
    result = pipeline.run_complete_pipeline(
        script_text=script_text, environment_type="studio"
    )

    return result


def demo_advanced_integration():
    """Demonstrate advanced integration with custom assets"""

    print("\n" + "=" * 60)
    print("DEMO: ADVANCED INTEGRATION WITH CUSTOM ASSETS")
    print("=" * 60)

    # Create sample assets
    assets_dir, sample_scripts = create_sample_assets()

    # Initialize pipeline
    config_path = "/Users/thomasbrianreynolds/online production/pipeline_config.json"
    pipeline = AIVideoProductionPipeline(config_path)

    # Use business presentation script
    script_text = sample_scripts["business_presentation"]

    # Look for existing assets (these would be user-provided)
    character_image = None
    voice_sample = None
    additional_assets = []

    # Check for sample assets in the directory
    for ext in [".jpg", ".jpeg", ".png"]:
        img_path = os.path.join(assets_dir, f"character{ext}")
        if os.path.exists(img_path):
            character_image = img_path
            break

    for ext in [".wav", ".mp3", ".m4a"]:
        voice_path = os.path.join(assets_dir, f"voice_sample{ext}")
        if os.path.exists(voice_path):
            voice_sample = voice_path
            break

    # Look for additional assets
    for file_path in Path(assets_dir).glob("*"):
        if file_path.suffix.lower() in [".mp4", ".mov", ".avi", ".png", ".jpg"]:
            if (
                "background" in file_path.name.lower()
                or "logo" in file_path.name.lower()
            ):
                additional_assets.append(str(file_path))

    print(f"\nAssets found:")
    print(f"Character image: {character_image or 'None'}")
    print(f"Voice sample: {voice_sample or 'None'}")
    print(f"Additional assets: {len(additional_assets)} files")

    # Run pipeline
    result = pipeline.run_complete_pipeline(
        script_text=script_text,
        character_image=character_image,
        voice_sample=voice_sample,
        additional_assets=additional_assets,
        environment_type="studio",
    )

    return result


def create_installation_guide():
    """Create installation and setup guide"""

    guide_content = """
# AI Video Production Pipeline - Installation Guide

## Prerequisites

### 1. Linly Talker Setup
```bash
# Clone Linly Talker repository
git clone https://github.com/Kedreamix/Linly-Talker.git
cd Linly-Talker

# Install dependencies
pip install -r requirements.txt

# Start Linly Talker service
python app.py
# Service will be available at http://localhost:7860
```

### 2. DaVinci Resolve Setup
1. Install DaVinci Resolve (free or Studio version)
2. Enable external scripting:
   - Go to DaVinci Resolve > Preferences
   - Navigate to System > General
   - Enable "External scripting using"
   - Select "Local" or "Network" as needed

### 3. Blender Setup
```bash
# Install Blender (macOS)
brew install --cask blender

# Or download from https://www.blender.org/download/
# Ensure 'blender' command is available in PATH
```

### 4. Python Dependencies
```bash
pip install requests pathlib
```

## Quick Start

### 1. Basic Demo
```bash
python demo_integration.py
```

### 2. Custom Script
```bash
python ai_video_pipeline.py --script "Your custom script here" --environment studio
```

### 3. With Custom Assets
```bash
python ai_video_pipeline.py \
    --script "Your script" \
    --image "/path/to/character.jpg" \
    --voice "/path/to/voice_sample.wav" \
    --environment studio
```

## Configuration

Edit `pipeline_config.json` to customize:
- Linly Talker API endpoint
- Blender executable path
- Output directories
- Render settings
- Performance options

## Troubleshooting

### Common Issues

1. **Linly Talker not responding**
   - Check if service is running on port 7860
   - Verify firewall settings
   - Check console output for errors

2. **DaVinci Resolve API not available**
   - Ensure external scripting is enabled
   - Check if DaVinci Resolve is running
   - Verify installation paths

3. **Blender command not found**
   - Add Blender to system PATH
   - Update executable path in config
   - Test with: `blender --version`

### Performance Tips

1. **GPU Acceleration**
   - Enable CUDA for Blender rendering
   - Use GPU-accelerated AI models in Linly Talker

2. **Memory Management**
   - Adjust memory limits in config
   - Close unnecessary applications
   - Use SSD for temp directories

3. **Parallel Processing**
   - Increase max_workers for multi-core systems
   - Enable GPU acceleration where available

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review component documentation:
   - Linly Talker: https://github.com/Kedreamix/Linly-Talker
   - DaVinci Resolve: Blackmagic Design documentation
   - Blender: https://docs.blender.org/
"""

    guide_path = "/Users/thomasbrianreynolds/online production/INSTALLATION_GUIDE.md"
    with open(guide_path, "w") as f:
        f.write(guide_content)

    print(f"✓ Created installation guide: {guide_path}")
    return guide_path


def main():
    """Main demo function"""

    print("\n" + "=" * 80)
    print("LINLY TALKER + DAVINCI RESOLVE + BLENDER INTEGRATION DEMO")
    print("=" * 80)

    try:
        # Create installation guide
        create_installation_guide()

        # Run system check
        pipeline = run_system_check()

        # Ask user what demo to run
        print("\nAvailable demos:")
        print("1. Basic integration (simple avatar generation)")
        print("2. Advanced integration (with custom assets)")
        print("3. System check only")
        print("4. Exit")

        while True:
            try:
                choice = input("\nSelect demo (1-4): ").strip()

                if choice == "1":
                    result = demo_basic_integration()
                    break
                elif choice == "2":
                    result = demo_advanced_integration()
                    break
                elif choice == "3":
                    print("\n✓ System check completed")
                    return
                elif choice == "4":
                    print("\nExiting demo")
                    return
                else:
                    print("Invalid choice. Please select 1-4.")
                    continue

            except KeyboardInterrupt:
                print("\n\nDemo interrupted by user")
                return

        # Display results
        if "result" in locals():
            print("\n" + "=" * 60)
            print("DEMO RESULTS")
            print("=" * 60)

            if result["success"]:
                print("✓ Demo completed successfully!")
                print(
                    f"Processing time: {result.get('processing_time', 0):.2f} seconds"
                )

                if "final_video" in result:
                    print(f"Final video: {result['final_video']}")

                print("\nGenerated files:")
                for key, path in result.items():
                    if key.endswith("_video") and path and os.path.exists(path):
                        size_mb = os.path.getsize(path) / (1024 * 1024)
                        print(f"  {key}: {path} ({size_mb:.1f} MB)")
            else:
                print("✗ Demo failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
                print(
                    f"Processing time: {result.get('processing_time', 0):.2f} seconds"
                )

        print("\n" + "=" * 60)
        print("NEXT STEPS")
        print("=" * 60)
        print("1. Review the generated files in the output directory")
        print("2. Check the installation guide for setup instructions")
        print("3. Customize the pipeline configuration as needed")
        print("4. Try with your own scripts and assets")

    except Exception as e:
        print(f"\n✗ Demo failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
