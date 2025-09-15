#!/usr/bin/env python3
""""""
Basic Video Generator - Simple MP4 Creation Tool

This tool creates MP4 videos from static background images and audio files
using ffmpeg. It's designed to be a reliable fallback for video generation'
that bypasses complex avatar processing.

Author: TRAE.AI System
Version: 1.0.0
""""""

import os
import subprocess
from pathlib import Path

from utils.logger import setup_logger


def create_basic_video(
    background_image_path: str, audio_path: str, output_path: str
# BRACKET_SURGEON: disabled
# ) -> bool:
    """"""
    Generates a simple MP4 video from a static image and an audio file using ffmpeg.

    Args:
        background_image_path (str): Path to the background image (jpg, png, etc.)
        audio_path (str): Path to the audio file (mp3,
    wav,
# BRACKET_SURGEON: disabled
#     etc.) - can be None for silent video
        output_path (str): Path where the output MP4 video will be saved

    Returns:
        bool: True on success, False on failure
    """"""
    logger = setup_logger()

    # Validate background image exists
    if not os.path.exists(background_image_path):
        logger.error(f"Background image not found: {background_image_path}")
        return False

    # Check if audio file exists, create silent video if not
    use_audio = audio_path and os.path.exists(audio_path)
    if audio_path and not use_audio:
        logger.warning(f"Audio file not found: {audio_path}, creating silent video")

    # Ensure output directory exists
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents = True, exist_ok = True)

    # Build ffmpeg command based on audio availability
    if use_audio:
        # Command with audio
        command = [
            "ffmpeg",
                "-loop",
                "1",
                "-i",
                background_image_path,
                "-i",
                audio_path,
                "-vf",
                "scale = 1920:1080,format = yuv420p",  # Standard 1080p
            "-c:v",
                "libx264",
                "-tune",
                "stillimage",  # Optimize for static image
            "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",  # End video when audio ends
            "-y",  # Overwrite output file if it exists
            output_path,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]
    else:
        # Command for silent video (10 seconds duration)
        command = [
            "ffmpeg",
                "-loop",
                "1",
                "-i",
                background_image_path,
                "-vf",
                "scale = 1920:1080,format = yuv420p",  # Standard 1080p
            "-c:v",
                "libx264",
                "-tune",
                "stillimage",  # Optimize for static image
            "-t",
                "10",  # 10 seconds duration for silent video
            "-y",  # Overwrite output file if it exists
            output_path,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

    try:
        logger.info(f"Generating basic video at: {output_path}")
        logger.info(f"Background: {background_image_path}")
        if use_audio:
            logger.info(f"Audio: {audio_path}")
        else:
            logger.info("Creating silent video (10 seconds)")

        result = subprocess.run(command,
    check = True,
    capture_output = True,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     text = True)

        # Verify output file was created
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            file_size_mb = os.path.getsize(output_path)/(1024 * 1024)
            logger.info(f"✅ Basic video generated successfully: {file_size_mb:.2f} MB")
            return True
        else:
            logger.error("Output file was not created or is empty")
            return False

    except subprocess.CalledProcessError as e:
        logger.error("ffmpeg command failed")
        logger.error(f"ffmpeg stderr: {e.stderr}")
        logger.error(f"ffmpeg stdout: {e.stdout}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during video generation: {str(e)}")
        return False


def create_basic_video_with_defaults(
    audio_path: str, title: str = "Video", output_dir: str = None
# BRACKET_SURGEON: disabled
# ) -> str:
    """"""
    Creates a basic video using default background and naming conventions.

    Args:
        audio_path (str): Path to the audio file
        title (str): Title for the video (used in filename)
        output_dir (str): Output directory (defaults to ./output/basic_videos/)

    Returns:
        str: Path to the generated video file, or None if failed
    """"""
    logger = setup_logger()

    # Set default output directory
    if output_dir is None:
        output_dir = Path("./output/basic_videos")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents = True, exist_ok = True)

    # Create default background if it doesn't exist
    background_path = Path("./assets/backgrounds/default_background.jpg")
    if not background_path.exists():
        # Create a simple colored background using ffmpeg
        background_path.parent.mkdir(parents = True, exist_ok = True)
        create_default_background(str(background_path))

    # Generate output filename
    safe_title = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     ).rstrip()
    safe_title = safe_title.replace(" ", "_")

    from datetime import datetime

    timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
    output_filename = f"basic_video_{safe_title}_{timestamp}.mp4"
    output_path = output_dir/output_filename

    # Generate the video
    success = create_basic_video(str(background_path), audio_path, str(output_path))

    if success:
        logger.info(f"Video created: {output_path}")
        return str(output_path)
    else:
        logger.error("Failed to create basic video")
        return None


def create_default_background(output_path: str) -> bool:
    """"""
    Creates a default background image using ffmpeg.

    Args:
        output_path (str): Path where the background image will be saved

    Returns:
        bool: True on success, False on failure
    """"""
    logger = setup_logger()

    # Create a gradient background with TRAE.AI branding
    command = [
        "ffmpeg",
            "-f",
            "lavfi",
            "-i",
            "color = c=#1e3c72:size = 1920x1080:duration = 1","
            "-vf",
            (
            "drawtext = text='TRAE.AI':"
            "fontcolor = white:fontsize = 120:x=(w - text_w)/2:y=(h - text_h)/2 - 100,"
            "drawtext = text='Production System':"
            "fontcolor=#FFD700:fontsize = 60:x=(w - text_w)/2:y=(h - text_h)/2 + 50""
# BRACKET_SURGEON: disabled
#         ),
            "-frames:v",
            "1",
            "-y",
            output_path,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ]

    try:
        logger.info(f"Creating default background: {output_path}")
        subprocess.run(command, check = True, capture_output = True, text = True)
        logger.info("✅ Default background created successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create default background: {e.stderr}")
        return False

if __name__ == "__main__":
    # Test the basic video generator

        import sys

    if len(sys.argv) < 3:
        print(
            "Usage: python basic_video_generator.py <background_image> <audio_file> [output_file]"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        sys.exit(1)

    background = sys.argv[1]
    audio = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) > 3 else "./test_basic_video.mp4"

    success = create_basic_video(background, audio, output)
    if success:
        print(f"✅ Video created successfully: {output}")
    else:
        print("❌ Video creation failed")
        sys.exit(1)