#!/usr/bin/env python3
"""
Generate Test Video - Create Actual MP4 Using Simple ffmpeg Commands

This script creates real MP4 videos using the simplest possible ffmpeg commands
that work reliably across all systems.

Author: TRAE.AI System
Version: 3.0.0
"""

import logging
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SimpleVideoGenerator:
    """Simple video generator using basic ffmpeg commands."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.output_dir = self.project_root / "output" / "test_videos"

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Output directory: {self.output_dir}")

    def check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("ffmpeg is available")
                return True
            else:
                logger.error("ffmpeg not found")
                return False
        except FileNotFoundError:
            logger.error("ffmpeg not installed")
            return False

    def create_basic_video(self, title: str, duration: int = 10) -> str:
        """Create a basic video with solid color background and simple text."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = (
            title.replace(" ", "_").replace(":", "").replace("/", "").replace("'", "")
        )
        video_path = self.output_dir / f"video_{safe_title}_{timestamp}.mp4"

        try:
            # Create simple video with color background and text
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output file
                "-f",
                "lavfi",
                "-i",
                f"color=c=blue:size=1280x720:duration={duration}",
                "-vf",
                f"drawtext=text='{title}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-t",
                str(duration),
                str(video_path),
            ]

            logger.info(f"Creating basic video: {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Video created successfully: {video_path}")
                return str(video_path)
            else:
                logger.error(f"Video creation failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Could not create video: {e}")
            return None

    def create_audio_video(self, title: str, duration: int = 10) -> str:
        """Create a video with both visual and audio components."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = (
            title.replace(" ", "_").replace(":", "").replace("/", "").replace("'", "")
        )
        video_path = self.output_dir / f"audio_video_{safe_title}_{timestamp}.mp4"

        try:
            # Create video with audio
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                f"color=c=green:size=1280x720:duration={duration}",
                "-f",
                "lavfi",
                "-i",
                f"sine=frequency=440:duration={duration}",
                "-vf",
                f"drawtext=text='{title}':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-t",
                str(duration),
                "-shortest",
                str(video_path),
            ]

            logger.info(f"Creating audio video: {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Audio video created successfully: {video_path}")
                return str(video_path)
            else:
                logger.error(f"Audio video creation failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Could not create audio video: {e}")
            return None

    def create_demo_video(self) -> str:
        """Create a demo video showcasing the system."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        video_path = self.output_dir / f"TRAE_AI_Demo_{timestamp}.mp4"

        try:
            # Create demo video
            cmd = [
                "ffmpeg",
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=red:size=1280x720:duration=15",
                "-f",
                "lavfi",
                "-i",
                "sine=frequency=523:duration=15",
                "-vf",
                "drawtext=text='TRAE.AI Production System':fontcolor=white:fontsize=42:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v",
                "libx264",
                "-c:a",
                "aac",
                "-pix_fmt",
                "yuv420p",
                "-t",
                "15",
                "-shortest",
                str(video_path),
            ]

            logger.info(f"Creating demo video: {video_path}")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Demo video created successfully: {video_path}")
                return str(video_path)
            else:
                logger.error(f"Demo video creation failed: {result.stderr}")
                return None

        except Exception as e:
            logger.error(f"Could not create demo video: {e}")
            return None

    def generate_all_videos(self) -> dict:
        """Generate all test videos."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "videos_created": [],
            "errors": [],
        }

        # Check prerequisites
        if not self.check_ffmpeg():
            results["errors"].append("ffmpeg not available")
            return results

        # Video generation tasks
        video_tasks = [
            ("create_basic_video", "AI Revolution 2024", 8),
            ("create_basic_video", "TRAE.AI Platform", 8),
            ("create_audio_video", "Future of Technology", 10),
            ("create_audio_video", "Creative AI Systems", 10),
            ("create_demo_video",),
        ]

        for task in video_tasks:
            try:
                method_name = task[0]
                method = getattr(self, method_name)

                if method_name == "create_demo_video":
                    video_path = method()
                    task_name = "Demo Video"
                else:
                    video_path = method(task[1], task[2])
                    task_name = f"{method_name.replace('create_', '').replace('_', ' ').title()}: {task[1]}"

                if video_path and Path(video_path).exists():
                    file_size = Path(video_path).stat().st_size
                    results["videos_created"].append(
                        {
                            "name": task_name,
                            "path": video_path,
                            "size_mb": round(file_size / (1024 * 1024), 2),
                        }
                    )
                    logger.info(f"✓ Created: {task_name}")
                else:
                    results["errors"].append(f"Failed to create: {task_name}")
                    logger.error(f"✗ Failed: {task_name}")

            except Exception as e:
                error_msg = f"Error creating {task[0]}: {str(e)}"
                results["errors"].append(error_msg)
                logger.error(error_msg)

        return results


def main():
    """Main function to generate test videos."""
    logger.info("Starting Simple Video Generation")

    generator = SimpleVideoGenerator()
    results = generator.generate_all_videos()

    # Print results
    print("\n" + "=" * 70)
    print("🎬 TRAE.AI VIDEO GENERATION RESULTS")
    print("=" * 70)
    print(f"📅 Timestamp: {results['timestamp']}")
    print(f"✅ Videos Created: {len(results['videos_created'])}")
    print(f"❌ Errors: {len(results['errors'])}")

    if results["videos_created"]:
        print("\n🎥 Successfully Created Videos:")
        total_size = 0
        for video in results["videos_created"]:
            print(f"   📹 {video['name']}")
            print(f"      📁 {video['path']}")
            print(f"      📊 Size: {video['size_mb']} MB")
            total_size += video["size_mb"]
        print(f"\n📈 Total Size: {total_size:.2f} MB")

    if results["errors"]:
        print("\n⚠️  Errors Encountered:")
        for error in results["errors"]:
            print(f"   ❌ {error}")

    print("\n" + "=" * 70)
    print(f"📂 Output Directory: {generator.output_dir}")
    print("🚀 Video generation completed!")

    if results["videos_created"]:
        print("\n💡 Next Steps:")
        print("   • Review generated MP4 files")
        print("   • Test video playback")
        print("   • Integrate with production pipeline")
        print("   • Use videos for system demonstrations")

    print("=" * 70)


if __name__ == "__main__":
    main()
