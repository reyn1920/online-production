#!/usr/bin/env python3
"""
TTS Engine - Coqui TTS Integration for TRAE.AI

This module provides high - quality text - to - speech generation using Coqui TTS,
replacing the proprietary Speechelo Pro RPA system with a direct, local integration.

Features:
- Multiple voice models and languages
- Emotion and style control
- Batch processing capabilities
- Audio format optimization
- Real - time synthesis

Author: TRAE.AI Content Generation System
Version: 1.0.0
"""

import logging
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import librosa
import numpy as np
import torch
from scipy.io import wavfile

try:
    from TTS.api import TTS
    from TTS.utils.manage import ModelManager
    from TTS.utils.synthesizer import Synthesizer

    TTS_AVAILABLE = True
except ImportError:
    print("Coqui TTS not installed. Install with: pip install TTS")
    TTS_AVAILABLE = False

    # Create dummy classes to prevent import errors

    class TTS:
        pass

    class ModelManager:
        pass

    class Synthesizer:
        pass


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VoiceConfig:
    """Configuration for voice synthesis."""

    model_name: str
    language: str = "en"
    speaker: Optional[str] = None
    emotion: Optional[str] = None
    speed: float = 1.0
    pitch: float = 1.0
    volume: float = 1.0
    sample_rate: int = 22050
    format: str = "wav"


@dataclass
class SynthesisResult:
    """Result of text - to - speech synthesis."""

    audio_path: str
    text: str
    voice_config: VoiceConfig
    duration: float
    sample_rate: int
    created_at: datetime
    metadata: Dict[str, Any]


class TTSEngine:
    """High - quality text - to - speech engine using Coqui TTS."""

    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize TTS Engine.

        Args:
            cache_dir: Directory to cache models and audio files
        """
        self.tts_available = TTS_AVAILABLE

        if not self.tts_available:
            logger.warning("TTS Engine initialized in disabled mode - Coqui TTS not available")
            self.models_cache = {}
            self.available_models = {}
            self.default_config = None
            return

        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".trae_tts_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.models_cache = {}
        self.available_models = self._get_available_models()
        self.default_config = VoiceConfig(
            model_name="tts_models/en/ljspeech/tacotron2 - DDC",
            language="en",
            speed=1.0,
            pitch=1.0,
            volume=1.0,
        )

        logger.info(f"TTS Engine initialized with {len(self.available_models)} available models")

    def _get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get list of available TTS models."""
        if not self.tts_available:
            return {}

        try:
            manager = ModelManager()
            models = manager.list_models()

            # Organize models by type and language
            organized_models = {
                "multilingual": [],
                "english": [],
                "other_languages": [],
            }

            for model in models:
                if "multilingual" in model.lower():
                    organized_models["multilingual"].append(model)
                elif "/en/" in model:
                    organized_models["english"].append(model)
                else:
                    organized_models["other_languages"].append(model)

            return organized_models
        except Exception as e:
            logger.error(f"Error getting available models: {e}")
            return {"english": ["tts_models/en/ljspeech/tacotron2 - DDC"]}

    def _load_model(self, model_name: str) -> TTS:
        """Load and cache TTS model."""
        if model_name in self.models_cache:
            return self.models_cache[model_name]

        try:
            logger.info(f"Loading TTS model: {model_name}")
            tts = TTS(model_name=model_name, progress_bar=True)

            # Move to GPU if available
            if torch.cuda.is_available():
                tts = tts.to("cuda")
                logger.info("Model moved to GPU")

            self.models_cache[model_name] = tts
            return tts
        except Exception as e:
            logger.error(f"Error loading model {model_name}: {e}")
            # Fallback to default model
            if model_name != self.default_config.model_name:
                return self._load_model(self.default_config.model_name)
            raise

    def synthesize_text(
        self,
        text: str,
        voice_config: Optional[VoiceConfig] = None,
        output_path: Optional[str] = None,
    ) -> SynthesisResult:
        """Synthesize text to speech.

        Args:
            text: Text to synthesize
            voice_config: Voice configuration
            output_path: Output file path (optional)

        Returns:
            SynthesisResult with audio file path and metadata
        """
        if not self.tts_available:
            raise RuntimeError("TTS Engine is not available - Coqui TTS not installed")

        if not text.strip():
            raise ValueError("Text cannot be empty")

        config = voice_config or self.default_config

        # Generate output path if not provided
        if not output_path:
            timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
            filename = f"tts_{timestamp}.{config.format}"
            output_path = str(self.cache_dir / filename)

        try:
            # Load model
            tts = self._load_model(config.model_name)

            # Synthesize audio
            logger.info(f"Synthesizing text: {text[:50]}...")
            start_time = datetime.now()

            # Generate audio
            if config.speaker and hasattr(tts, "speakers") and tts.speakers:
                # Multi - speaker model
                tts.tts_to_file(text=text, speaker=config.speaker, file_path=output_path)
            else:
                # Single speaker model
                tts.tts_to_file(text=text, file_path=output_path)

            synthesis_time = (datetime.now() - start_time).total_seconds()

            # Post - process audio if needed
            if config.speed != 1.0 or config.pitch != 1.0 or config.volume != 1.0:
                output_path = self._post_process_audio(
                    output_path, config.speed, config.pitch, config.volume
                )

            # Get audio duration
            duration = self._get_audio_duration(output_path)

            result = SynthesisResult(
                audio_path=output_path,
                text=text,
                voice_config=config,
                duration=duration,
                sample_rate=config.sample_rate,
                created_at=datetime.now(),
                metadata={
                    "synthesis_time": synthesis_time,
                    "model_name": config.model_name,
                    "text_length": len(text),
                    "words_count": len(text.split()),
                    "gpu_used": torch.cuda.is_available(),
                },
            )

            logger.info(f"Synthesis completed in {synthesis_time:.2f}s, duration: {duration:.2f}s")
            return result

        except Exception as e:
            logger.error(f"Error synthesizing text: {e}")
            raise

    def _post_process_audio(
        self, audio_path: str, speed: float, pitch: float, volume: float
    ) -> str:
        """Post - process audio with speed, pitch, and volume adjustments."""
        try:
            # Load audio
            y, sr = librosa.load(audio_path, sr=None)

            # Adjust speed (time stretching)
            if speed != 1.0:
                y = librosa.effects.time_stretch(y, rate=speed)

            # Adjust pitch
            if pitch != 1.0:
                n_steps = 12 * np.log2(pitch)  # Convert to semitones
                y = librosa.effects.pitch_shift(y, sr=sr, n_steps=n_steps)

            # Adjust volume
            if volume != 1.0:
                y = y * volume

            # Save processed audio
            processed_path = audio_path.replace(".wav", "_processed.wav")
            wavfile.write(processed_path, sr, (y * 32767).astype(np.int16))

            # Remove original file
            os.remove(audio_path)

            return processed_path

        except Exception as e:
            logger.error(f"Error post - processing audio: {e}")
            return audio_path  # Return original if processing fails

    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration in seconds."""
        try:
            y, sr = librosa.load(audio_path, sr=None)
            return len(y) / sr
        except Exception as e:
            logger.error(f"Error getting audio duration: {e}")
            return 0.0

    def batch_synthesize(
        self,
        texts: List[str],
        voice_config: Optional[VoiceConfig] = None,
        output_dir: Optional[str] = None,
    ) -> List[SynthesisResult]:
        """Synthesize multiple texts in batch.

        Args:
            texts: List of texts to synthesize
            voice_config: Voice configuration
            output_dir: Output directory for audio files

        Returns:
            List of SynthesisResult objects
        """
        if not texts:
            return []

        config = voice_config or self.default_config
        output_dir = Path(output_dir) if output_dir else self.cache_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        total_texts = len(texts)

        logger.info(f"Starting batch synthesis of {total_texts} texts")

        for i, text in enumerate(texts, 1):
            try:
                timestamp = datetime.now().strftime("%Y % m%d_ % H%M % S")
                filename = f"batch_{i:03d}_{timestamp}.{config.format}"
                output_path = str(output_dir / filename)

                result = self.synthesize_text(text, config, output_path)
                results.append(result)

                logger.info(f"Completed {i}/{total_texts}: {text[:30]}...")

            except Exception as e:
                logger.error(f"Error synthesizing text {i}: {e}")
                continue

        logger.info(f"Batch synthesis completed: {len(results)}/{total_texts} successful")
        return results

    def get_available_voices(self, language: str = "en") -> List[str]:
        """Get available voices for a language.

        Args:
            language: Language code (e.g., 'en', 'es', 'fr')

        Returns:
            List of available voice model names
        """
        voices = []

        # Add multilingual models
        voices.extend(self.available_models.get("multilingual", []))

        # Add language - specific models
        if language == "en":
            voices.extend(self.available_models.get("english", []))
        else:
            # Filter other language models
            for model in self.available_models.get("other_languages", []):
                if f"/{language}/" in model:
                    voices.append(model)

        return voices

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary with model information
        """
        try:
            tts = self._load_model(model_name)

            info = {
                "model_name": model_name,
                "language": "unknown",
                "speakers": [],
                "sample_rate": getattr(tts, "sample_rate", 22050),
                "is_multi_speaker": False,
                "is_multi_lingual": False,
            }

            # Extract language from model name
            if "/en/" in model_name:
                info["language"] = "en"
            elif "/es/" in model_name:
                info["language"] = "es"
            elif "/fr/" in model_name:
                info["language"] = "fr"
            elif "multilingual" in model_name.lower():
                info["is_multi_lingual"] = True

            # Check for speakers
            if hasattr(tts, "speakers") and tts.speakers:
                info["speakers"] = tts.speakers
                info["is_multi_speaker"] = True

            return info

        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return {"model_name": model_name, "error": str(e)}

    def cleanup_cache(self, max_age_days: int = 7) -> int:
        """Clean up old cached audio files.

        Args:
            max_age_days: Maximum age of files to keep in days

        Returns:
            Number of files deleted
        """
        try:
            deleted_count = 0
            current_time = datetime.now()

            for file_path in self.cache_dir.glob("*.wav"):
                file_age = current_time - datetime.fromtimestamp(file_path.stat().st_mtime)

                if file_age.days > max_age_days:
                    file_path.unlink()
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} old audio files")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0


# Example usage and testing
if __name__ == "__main__":
    # Initialize TTS Engine
    tts_engine = TTSEngine()

    # Test basic synthesis
    test_text = "Hello, this is a test of the new Coqui TTS integration for TRAE.AI. The voice quality should be significantly better than the previous system."

    try:
        # Test with default configuration
        print("🎤 Testing TTS Engine with default configuration...")
        result = tts_engine.synthesize_text(test_text)
        print(f"✅ Synthesis successful: {result.audio_path}")
        print(f"   Duration: {result.duration:.2f}s")
        print(f"   Model: {result.voice_config.model_name}")

        # Test with custom configuration
        print("\\n🎤 Testing with custom voice configuration...")
        custom_config = VoiceConfig(
            model_name="tts_models/en/ljspeech/tacotron2 - DDC",
            language="en",
            speed=1.1,
            pitch=1.05,
            volume=0.9,
        )

        result2 = tts_engine.synthesize_text(
            "This is a test with custom voice settings including speed, pitch, \
    and volume adjustments.",
            voice_config=custom_config,
        )
        print(f"✅ Custom synthesis successful: {result2.audio_path}")

        # Test batch synthesis
        print("\\n🎤 Testing batch synthesis...")
        batch_texts = [
            "First sentence for batch processing.",
            "Second sentence with different content.",
            "Third and final sentence in the batch.",
        ]

        batch_results = tts_engine.batch_synthesize(batch_texts)
        print(f"✅ Batch synthesis completed: {len(batch_results)} files generated")

        # Show available models
        print("\\n📋 Available TTS Models:")
        for category, models in tts_engine.available_models.items():
            print(f"  {category.title()}: {len(models)} models")
            for model in models[:3]:  # Show first 3 models
                print(f"    - {model}")
            if len(models) > 3:
                print(f"    ... and {len(models) - 3} more")

        print("\\n🎉 TTS Engine test completed successfully!")

    except Exception as e:
        print(f"❌ Error testing TTS Engine: {e}")

        import traceback

        traceback.print_exc()
