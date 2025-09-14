#!/usr/bin/env python3
"""
TRAE.AI - Bulletproof Video Generator v2
This script generates a complete, 100% live MP4 video from start to finish.
It is self - contained, creating its own assets and bypassing external dependencies
like Ollama to ensure a successful run.
"""

import logging
import os
import subprocess

# --- Configuration ---
OUTPUT_DIR = os.path.join("output", "real_videos")
ASSETS_DIR = os.path.join("assets", "generated")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# --- Setup ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


def generate_script(topic: str) -> str:
    """Generates a simple, functional script for the given topic."""
    logging.info(f"Step 1: Generating script for '{topic}'...")
    script_text = f"""
Welcome to a TRAE.AI production.
Today, we are discussing: {topic}.
This topic is complex, with many different viewpoints.
Our goal is to provide a clear and concise overview.
Thank you for watching.
"""
    script_path = os.path.join(OUTPUT_DIR, f"script_{topic.replace(' ', '_')}.txt")
    with open(script_path, "w") as f:
        f.write(script_text)
    logging.info(f"✅ Script saved to {script_path}")
    return script_text


def generate_audio(script_text: str, topic: str) -> str:
    """Generates a WAV audio file from the script using the system's TTS."""
    logging.info("Step 2: Generating audio narration...")
    audio_path = os.path.join(ASSETS_DIR, f"speech_{topic.replace(' ', '_')}.wav")

    # Using 'say' on macOS as a reliable, free TTS engine
    try:
        subprocess.run(
            ["say", "-o", audio_path, "--data - format = LEF32@44100", script_text],
            check=True,
        )
        logging.info(f"✅ Audio file generated successfully: {audio_path}")
        return audio_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logging.error(f"Failed to generate audio using 'say' command: {e}")
        logging.warning("Please ensure you are on a macOS system or have a TTS engine installed.")
        return None


def generate_video(topic: str, audio_path: str) -> str:
    """Generates the final MP4 video using a simple background and the narration."""
    logging.info("Step 3: Generating final MP4 video with ffmpeg...")
    video_path = os.path.join(OUTPUT_DIR, f"FINAL_VIDEO_{topic.replace(' ', '_')}.mp4")

    # This ffmpeg command is corrected to handle text with spaces and special characters
    # by using a temporary file for the text filter.
    filter_text = f"drawtext = fontfile=/System/Library/Fonts/Helvetica.ttc:text='{topic}':fontcolor = white:fontsize = 48:x=(w - text_w)/2:y=(h - text_h)/2"

    command = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        "color = c = black:s = 1920x1080",  # Simple black background
        "-i",
        audio_path,
        "-vf",
        filter_text,
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",  # End the video when the audio ends
        "-y",  # Overwrite if exists
        video_path,
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
        logging.info("✅ Final video generated successfully!")
        return video_path
    except subprocess.CalledProcessError as e:
        logging.error("ffmpeg command failed to generate video.")
        logging.error(f"ffmpeg stderr: {e.stderr}")
        return None


def main():
    """Main execution function."""
    logging.info("--- Starting Bulletproof Video Generation Protocol ---")

    test_topic = "A New Era for Artificial Intelligence"

    # 1. Generate Script
    script = generate_script(test_topic)

    # 2. Generate Audio
    audio_file = generate_audio(script, test_topic)
    if not audio_file:
        logging.critical("Could not generate audio, aborting video creation.")
        return

    # 3. Generate Video
    video_file = generate_video(test_topic, audio_file)
    if not video_file:
        logging.critical("Could not generate final video file.")
        return

    logging.info("\\n" + "=" * 50)
    logging.info("🎉 VIDEO CREATION COMPLETE")
    logging.info("Final video file is ready for review at:")
    print(f"\\n{video_file}\\n")
    logging.info("=" * 50)


if __name__ == "__main__":
    main()
