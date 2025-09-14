#!/usr / bin / env python3
"""
Audio Sample Generation Script

Generates production - ready audio content samples using available TTS engines
(gTTS, pyttsx3, and system TTS) for demonstration purposes.

Author: TRAE.AI Content Generation System
Version: 1.0.0
"""

import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

try:
    import gtts
    import pygame
    import pyttsx3

except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install gtts pyttsx3 pygame")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Output directory
OUTPUT_DIR = Path(__file__).parent / "output" / "audio_samples"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Sample texts for different use cases
SAMPLE_TEXTS = {
    "professional_intro": {
        "text": "Welcome to our AI - powered content generation platform. Experience studio - quality voice synthesis with emotional control \
    and perfect pronunciation. Transform your ideas into professional audio content in seconds.",
        "category": "Professional",
        "use_case": "Corporate introduction",
    },
    "casual_demo": {
        "text": "Hey there! Check out this amazing AI system that creates incredible content in just seconds. It's like having a Hollywood studio right in your computer!",
        "category": "Casual",
        "use_case": "Product demo",
    },
    "educational_content": {
        "text": "In this lesson, we'll explore the fascinating world of artificial intelligence \
    and machine learning. These technologies are revolutionizing how we create \
    and consume digital content.",
        "category": "Educational",
        "use_case": "E - learning narration",
    },
    "storytelling": {
        "text": "Once upon a time, in a world where creativity knew no bounds, there lived an AI that could bring any story to life with the power of voice \
    and imagination.",
        "category": "Narrative",
        "use_case": "Storytelling",
    },
    "news_broadcast": {
        "text": "Breaking news: Revolutionary AI technology now enables anyone to create professional - grade audio content without expensive equipment \
    or studio time.",
        "category": "News",
        "use_case": "News broadcast",
    },
    "commercial_ad": {
        "text": "Don't miss out on the future of content creation! Our AI - powered platform delivers studio - quality results at lightning speed. Try it today \
    and transform your creative workflow forever.",
        "category": "Commercial",
        "use_case": "Advertisement",
    },
}

# Voice configurations for different styles
VOICE_CONFIGS = {
    "gtts_english": {
        "engine": "gtts",
        "language": "en",
        "speed": 1.0,
        "volume": 1.0,
        "sample_rate": 22050,
        "format": "mp3",
    },
    "pyttsx3_default": {
        "engine": "pyttsx3",
        "language": "en",
        "speed": 1.0,
        "volume": 0.9,
        "sample_rate": 22050,
        "format": "wav",
    },
    "pyttsx3_fast": {
        "engine": "pyttsx3",
        "language": "en",
        "speed": 1.3,
        "volume": 0.9,
        "sample_rate": 22050,
        "format": "wav",
    },
    "pyttsx3_slow": {
        "engine": "pyttsx3",
        "language": "en",
        "speed": 0.8,
        "volume": 0.9,
        "sample_rate": 22050,
        "format": "wav",
    },
    "system_tts": {
        "engine": "system",
        "language": "en",
        "speed": 1.0,
        "volume": 1.0,
        "sample_rate": 44100,
        "format": "wav",
    },
}


class AudioSampleGenerator:
    """Generates production - ready audio samples."""

    def __init__(self):
        """Initialize the audio sample generator."""
        self.pyttsx3_engine = pyttsx3.init()
        self.results: List[Dict[str, Any]] = []
        self._setup_pyttsx3()

    def _setup_pyttsx3(self):
        """Configure pyttsx3 engine settings."""
        try:
            # Get available voices
            voices = self.pyttsx3_engine.getProperty("voices")
            if voices:
                # Set default voice (first available)
                self.pyttsx3_engine.setProperty("voice", voices[0].id)

            # Set speech rate and volume
            self.pyttsx3_engine.setProperty("rate", 200)  # Speed
            self.pyttsx3_engine.setProperty("volume", 0.9)  # Volume

            logger.info(f"✅ pyttsx3 engine initialized with {len(voices) if voices else 0} voices")
        except Exception as e:
            logger.error(f"Failed to setup pyttsx3: {e}")

    def generate_all_samples(self) -> Dict[str, Any]:
        """Generate all audio samples."""
        logger.info("🎵 Starting audio sample generation...")

        sample_info = {
            "generation_time": datetime.now().isoformat(),
            "total_samples": 0,
            "successful_samples": 0,
            "failed_samples": 0,
            "samples": [],
        }

        # Generate samples for each text with different voice configs
        for text_key, text_info in SAMPLE_TEXTS.items():
            for voice_key, voice_config in VOICE_CONFIGS.items():
                sample_info["total_samples"] += 1

                try:
                    result = self._generate_sample(text_key, text_info, voice_key, voice_config)

                    if result:
                        self.results.append(result)
                        sample_info["successful_samples"] += 1
                        sample_info["samples"].append(
                            {
                                "text_key": text_key,
                                "voice_key": voice_key,
                                "category": text_info["category"],
                                "use_case": text_info["use_case"],
                                "file_path": result.audio_path,
                                "duration": result.duration,
                                "sample_rate": result.sample_rate,
                                "metadata": result.metadata,
                            }
                        )

                        logger.info(
                            f"✅ Generated: {text_key} + {voice_key} " f"({result.duration:.1f}s)"
                        )
                    else:
                        sample_info["failed_samples"] += 1

                except Exception as e:
                    logger.error(f"❌ Failed to generate {text_key} + {voice_key}: {e}")
                    sample_info["failed_samples"] += 1

        # Generate batch samples
        self._generate_batch_samples(sample_info)

        # Save sample information
        self._save_sample_info(sample_info)

        logger.info(
            f"🎉 Audio sample generation completed! "
            f"{sample_info['successful_samples']}/{sample_info['total_samples']} successful"
        )

        return sample_info

    def _generate_sample(
        self, text_key: str, text_info: Dict, voice_key: str, voice_config: Dict
    ) -> Dict[str, Any]:
        """Generate a single audio sample."""
        # Create filename
        filename = f"{text_key}_{voice_key}.wav"
        output_path = str(OUTPUT_DIR / filename)

        start_time = datetime.now()

        try:
            if voice_key == "gtts_english":
                # Use Google TTS
                tts = gtts.gTTS(text=text_info["text"], lang="en", slow=False)
                tts.save(output_path)

            elif voice_key.startswith("pyttsx3"):
                # Use pyttsx3
                self._generate_with_pyttsx3(text_info["text"], output_path, voice_config)

            elif voice_key == "system_tts":
                # Use system TTS (macOS 'say' command)
                self._generate_with_system_tts(text_info["text"], output_path)

            else:
                raise ValueError(f"Unknown voice engine: {voice_key}")

            synthesis_time = (datetime.now() - start_time).total_seconds()

            # Get file size and duration estimate
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            duration_estimate = len(text_info["text"].split()) * 0.5  # Rough estimate

            result = {
                "audio_path": output_path,
                "text": text_info["text"],
                "voice_config": voice_config,
                "duration": duration_estimate,
                "sample_rate": voice_config.get("sample_rate", 22050),
                "created_at": datetime.now(),
                "metadata": {
                    "synthesis_time": synthesis_time,
                    "voice_engine": voice_key,
                    "text_length": len(text_info["text"]),
                    "words_count": len(text_info["text"].split()),
                    "file_size": file_size,
                },
            }

            return result

        except Exception as e:
            logger.error(f"Failed to generate sample with {voice_key}: {e}")
            return None

    def _generate_with_pyttsx3(self, text: str, output_path: str, config: Dict):
        """Generate audio using pyttsx3."""
        # Configure engine based on config
        if "speed" in config:
            rate = int(200 * config["speed"])
            self.pyttsx3_engine.setProperty("rate", rate)

        if "volume" in config:
            self.pyttsx3_engine.setProperty("volume", config["volume"])

        # Save to file
        self.pyttsx3_engine.save_to_file(text, output_path)
        self.pyttsx3_engine.runAndWait()

    def _generate_with_system_tts(self, text: str, output_path: str):
        """Generate audio using system TTS (macOS say command)."""
        try:
            subprocess.run(
                ["say", "-o", output_path, "--data - format = LEF32@44100", text],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"System TTS failed: {e}")
            raise

    def _generate_batch_samples(self, sample_info: Dict[str, Any]):
        """Generate batch samples to demonstrate batch processing."""
        logger.info("🎵 Generating batch samples...")

        # Create a batch of short texts
        batch_texts = [
            "Welcome to our platform.",
            "Experience AI - powered content creation.",
            "Transform your ideas into reality.",
            "Professional results in seconds.",
            "The future of content is here.",
        ]

        batch_dir = OUTPUT_DIR / "batch_samples"
        batch_dir.mkdir(exist_ok=True)

        batch_results = []

        try:
            for i, text in enumerate(batch_texts, 1):
                filename = f"batch_{i:03d}.wav"
                output_path = str(batch_dir / filename)

                # Use gTTS for batch samples
                tts = gtts.gTTS(text=text, lang="en", slow=False)
                temp_mp3 = str(batch_dir / f"temp_{i}.mp3")
                tts.save(temp_mp3)

                # Convert to WAV if needed (simplified)
                os.rename(temp_mp3, output_path.replace(".wav", ".mp3"))

                batch_results.append(
                    {
                        "text": text,
                        "file_path": output_path.replace(".wav", ".mp3"),
                        "duration": len(text.split()) * 0.5,
                    }
                )

            sample_info["batch_samples"] = {
                "count": len(batch_results),
                "total_duration": sum(r["duration"] for r in batch_results),
                "files": [r["file_path"] for r in batch_results],
            }

            logger.info(f"✅ Generated {len(batch_results)} batch samples")

        except Exception as e:
            logger.error(f"❌ Failed to generate batch samples: {e}")
            sample_info["batch_samples"] = {"error": str(e)}

    def _save_sample_info(self, sample_info: Dict[str, Any]):
        """Save sample information to JSON file."""

        import json

        info_file = OUTPUT_DIR / "sample_info.json"

        try:
            with open(info_file, "w") as f:
                json.dump(sample_info, f, indent=2, default=str)

            logger.info(f"📄 Sample information saved to {info_file}")

        except Exception as e:
            logger.error(f"❌ Failed to save sample info: {e}")

    def get_available_voices(self) -> List[str]:
        """Get list of available voice engines."""
        return list(VOICE_CONFIGS.keys())

    def generate_voice_showcase(self):
        """Generate a showcase of available voices."""
        logger.info("🎤 Generating voice showcase...")

        showcase_text = "This is a demonstration of our AI voice synthesis technology."
        available_voices = self.get_available_voices()

        showcase_dir = OUTPUT_DIR / "voice_showcase"
        showcase_dir.mkdir(exist_ok=True)

        for voice_key in available_voices:
            try:
                voice_config = VOICE_CONFIGS[voice_key]

                filename = f"showcase_{voice_key}.wav"
                output_path = str(showcase_dir / filename)

                text_info = {"text": showcase_text}
                result = self._generate_sample("showcase", text_info, voice_key, voice_config)

                if result:
                    logger.info(f"✅ Generated voice showcase: {voice_key}")
                else:
                    logger.error(f"❌ Failed to generate voice showcase: {voice_key}")

            except Exception as e:
                logger.error(f"❌ Failed to generate voice {voice_key}: {e}")


def main():
    """Main function to generate audio samples."""
    print("🎵 TRAE.AI Audio Sample Generator")
    print("=" * 50)

    try:
        generator = AudioSampleGenerator()

        # Generate all samples
        sample_info = generator.generate_all_samples()

        # Generate voice showcase
        generator.generate_voice_showcase()

        # Print summary
        print("\\n📊 Generation Summary:")
        print(f"Total samples: {sample_info['total_samples']}")
        print(f"Successful: {sample_info['successful_samples']}")
        print(f"Failed: {sample_info['failed_samples']}")
        print(f"Output directory: {OUTPUT_DIR}")

        if sample_info["successful_samples"] > 0:
            total_duration = sum(
                sample["duration"] for sample in sample_info["samples"] if "duration" in sample
            )
            print(f"Total audio duration: {total_duration:.1f} seconds")

        print("\\n🎉 Audio sample generation completed successfully!")

    except Exception as e:
        logger.error(f"❌ Audio sample generation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
