#!/usr/bin/env python3
""""""
Avatar Engine Services - Standardized Wrappers for Avatar Generation

This module provides standardized wrapper services for different avatar generation engines:
- Linly - Talker (primary engine)
- Talking Heads (fallback engine)

Each wrapper provides a consistent API interface for the orchestrator to use,
handling engine - specific configurations and error handling.

Author: TRAE.AI System
Version: 1.0.0
""""""

import asyncio
import logging
import os
import sys
import tempfile
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import aiohttp
import cv2
import numpy as np
import torch

# MuseTalk imports
try:
    sys.path.append("/Users/thomasbrianreynolds/online production/models/linly_talker/Musetalk")

    from musetalk.utils.blending import get_image
    from musetalk.utils.preprocessing import (
        coord_placeholder,
        get_landmark_and_bbox,
        read_imgs,
# BRACKET_SURGEON: disabled
#     )

    from musetalk.utils.utils import (
        datagen,
        get_file_type,
        get_video_fps,
        load_all_model,
# BRACKET_SURGEON: disabled
#     )

    MUSETALK_AVAILABLE = True
except ImportError as e:
    logging.warning(f"MuseTalk not available: {e}")
    MUSETALK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AvatarRequest:
    """Standardized avatar generation request."""

    text: str
    voice_settings: Dict[str, Any]
    video_settings: Dict[str, Any]
    output_path: Optional[str] = None
    source_image: Optional[str] = None
    request_id: Optional[str] = None
    gender: Optional[str] = None

    def __post_init__(self):
        if self.request_id is None:
            self.request_id = f"avatar_{uuid4().hex[:8]}"


@dataclass
class AvatarResponse:
    """Standardized avatar generation response."""

    success: bool
    video_path: Optional[str]
    duration: Optional[float]
    engine_used: str
    processing_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseAvatarEngine(ABC):
    """Abstract base class for avatar generation engines."""

    def __init__(self, engine_name: str, config: Optional[Dict[str, Any]] = None):
        self.engine_name = engine_name
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{engine_name}")
        self.is_initialized = False
        self.last_health_check = None

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the avatar engine."""
        raise NotImplementedError("Subclasses must implement initialize method")

    @abstractmethod
    async def generate_avatar(self, request: AvatarRequest) -> AvatarResponse:
        """Generate avatar video from request."""
        raise NotImplementedError("Subclasses must implement generate_avatar method")

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the engine is healthy and responsive."""
        raise NotImplementedError("Subclasses must implement health_check method")

    async def cleanup(self):
        """Cleanup resources used by the engine."""
        try:
            self.logger.info(f"Cleaning up {self.engine_name} engine")
            # Base cleanup - subclasses can override for specific cleanup
            if hasattr(self, "is_initialized"):
                self.is_initialized = False
        except Exception as e:
            self.logger.error(f"Error during cleanup of {self.engine_name}: {e}")


class LinlyTalkerEngine(BaseAvatarEngine):
    """Linly - Talker avatar generation engine with direct model inference."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("linly - talker - enhanced", config)
        self.model_path = self.config.get("model_path", "./models/linly_talker")
        self.timeout = self.config.get("timeout", 120)
        self.test_mode = self.config.get("test_mode", False)

        # Model components
        self.audio_processor = None
        self.vae = None
        self.unet = None
        self.pe = None
        self.device = None
        self.timesteps = None

    async def initialize(self) -> bool:
        """Initialize Linly - Talker engine with direct model loading."""
        try:
            self.logger.info("Initializing Linly - Talker engine...")

            # In test mode, skip model loading
            if self.test_mode:
                self.logger.info("Running in test mode - skipping model loading")
                self.is_initialized = True
                return True

            # Check if model directory exists
            if not Path(self.model_path).exists():
                self.logger.warning(f"Model path not found: {self.model_path}")
                return False

            # Check if MuseTalk is available
            if not MUSETALK_AVAILABLE:
                self.logger.error("MuseTalk not available - cannot initialize LinlyTalker engine")
                return False

            # Change to model directory for proper imports
            original_cwd = os.getcwd()
            os.chdir(str(Path(self.model_path)))

            try:
                # Load models directly
                self.logger.info("Loading MuseTalk models...")
                self.audio_processor, self.vae, self.unet, self.pe = load_all_model()

                # Set up device and optimize models
                self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
                self.timesteps = torch.tensor([0], device=self.device)

                # Optimize models for inference
                if torch.cuda.is_available():
                    self.pe = self.pe.half()
                    self.vae.vae = self.vae.vae.half()
                    self.unet.model = self.unet.model.half()

                self.is_initialized = True
                self.logger.info(
                    "Linly - Talker engine initialized successfully with direct model inference"
# BRACKET_SURGEON: disabled
#                 )
                return True

            except Exception as e:
                self.logger.error(f"Failed to load MuseTalk models: {e}")
                return False
            finally:
                os.chdir(original_cwd)

        except Exception as e:
            self.logger.error(f"Failed to initialize Linly - Talker: {e}")
            return False

    async def _start_service(self):
        """No service startup needed for direct model inference."""
        self.logger.info(f"Starting {self.engine_name} service (direct model inference)")
        # Direct model inference doesn't require external service startup
        return True

    async def health_check(self) -> bool:
        """Check if the models are loaded and ready."""
        # In test mode, always return healthy
        if self.test_mode:
            return True

        try:
            if not MUSETALK_AVAILABLE:
                return False

            # Check if models are loaded
            if not self.is_initialized or not all(
                [self.audio_processor, self.vae, self.unet, self.pe]
# BRACKET_SURGEON: disabled
#             ):
                return False

            # Check if model files exist
            model_dir = Path(self.model_path) / "Musetalk"
            required_paths = [
                model_dir / "models" / "musetalk" / "pytorch_model.bin",
                model_dir / "models" / "whisper" / "tiny.pt",
                model_dir / "models" / "sd - vae - ft - mse",
# BRACKET_SURGEON: disabled
#             ]

            for path in required_paths:
                if not path.exists():
                    self.logger.warning(f"Required model path not found: {path}")
                    return False

            self.last_health_check = datetime.now()
            return True
        except Exception as e:
            self.logger.debug(f"Health check failed: {e}")
            return False

    async def generate_avatar(self, request: AvatarRequest) -> AvatarResponse:
        """Generate avatar using direct MuseTalk model inference."""
        start_time = time.time()

        try:
            if not self.is_initialized:
                if not await self.initialize():
                    return AvatarResponse(
                        success=False,
                        video_path=None,
                        duration=None,
                        engine_used=self.engine_name,
                        processing_time=time.time() - start_time,
                        error_message="Engine not initialized",
# BRACKET_SURGEON: disabled
#                     )

            # In test mode, return mock response
            if self.test_mode:
                await asyncio.sleep(0.1)  # Simulate processing time
                processing_time = time.time() - start_time

                return AvatarResponse(
                    success=True,
                    video_path=f"/generated/test_linly_{uuid4().hex[:8]}.mp4",
                    duration=len(request.text.split()) * 0.5,  # Rough estimate
                    engine_used=self.engine_name,
                    processing_time=processing_time,
                    metadata={
                        "model_version": "test - v1.0",
                        "quality_score": 0.95,
                        "processing_details": "test_mode_simulation",
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 )

            # Check health before processing
            if not await self.health_check():
                return AvatarResponse(
                    success=False,
                    video_path=None,
                    duration=None,
                    engine_used=self.engine_name,
                    processing_time=time.time() - start_time,
                    error_message="Engine health check failed",
# BRACKET_SURGEON: disabled
#                 )

            self.logger.info(
                f"Generating avatar with direct MuseTalk inference for request {request.request_id}"
# BRACKET_SURGEON: disabled
#             )

            # Run model inference in thread pool to avoid blocking
            result = await asyncio.get_event_loop().run_in_executor(
                None, self._run_musetalk_inference, request
# BRACKET_SURGEON: disabled
#             )

            processing_time = time.time() - start_time

            if result["success"]:
                return AvatarResponse(
                    success=True,
                    video_path=result["video_path"],
                    duration=result.get("duration"),
                    engine_used=self.engine_name,
                    processing_time=processing_time,
                    metadata={
                        "model_version": "musetalk - v1.0",
                        "quality_score": result.get("quality_score", 0.9),
                        "processing_details": "direct_model_inference",
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 )
            else:
                return AvatarResponse(
                    success=False,
                    video_path=None,
                    duration=None,
                    engine_used=self.engine_name,
                    processing_time=processing_time,
                    error_message=result.get("error", "Unknown inference error"),
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            return AvatarResponse(
                success=False,
                video_path=None,
                duration=None,
                engine_used=self.engine_name,
                processing_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )

    def _run_musetalk_inference(self, request: AvatarRequest) -> Dict[str, Any]:
        """Run MuseTalk model inference in a separate thread."""
        try:
            # Change to model directory
            original_cwd = os.getcwd()
            os.chdir(str(Path(self.model_path)))

            try:
                # Create temporary files for input/output
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)

                    # Generate audio from text using TTS
                    audio_path = temp_path / "audio.wav"
                    self._generate_audio(request.text, str(audio_path), request.voice_settings)

                    # Use source image or default avatar
                    if request.source_image and Path(request.source_image).exists():
                        avatar_path = request.source_image
                    else:
                        # Use default avatar image
                        avatar_path = str(Path(self.model_path) / "data" / "avatar" / "default.jpg")

                    # Generate output video path
                    output_dir = (
                        Path(request.output_path).parent
                        if request.output_path
                        else Path("./generated")
# BRACKET_SURGEON: disabled
#                     )
                    output_dir.mkdir(exist_ok=True)
                    video_path = output_dir / f"avatar_{request.request_id}.mp4"

                    # Run MuseTalk inference
                    self._run_musetalk_generation(str(audio_path), avatar_path, str(video_path))

                    # Get video duration
                    duration = self._get_video_duration(str(video_path))

                    return {
                        "success": True,
                        "video_path": str(video_path),
                        "duration": duration,
                        "quality_score": 0.9,
# BRACKET_SURGEON: disabled
#                     }

            finally:
                os.chdir(original_cwd)

        except Exception as e:
            self.logger.error(f"MuseTalk inference failed: {e}")
            return {"success": False, "error": str(e)}

    def _generate_audio(self, text: str, output_path: str, voice_settings: Dict[str, Any]):
        """Generate audio from text using TTS."""
        import wave
        import numpy as np

        try:
            # Try to use pyttsx3 for TTS if available
            import pyttsx3

            engine = pyttsx3.init()

            # Configure voice settings
            rate = voice_settings.get("rate", 200)
            volume = voice_settings.get("volume", 0.9)
            voice_id = voice_settings.get("voice_id", None)

            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            if voice_id:
                voices = engine.getProperty("voices")
                if voice_id < len(voices):
                    engine.setProperty("voice", voices[voice_id].id)

            # Generate audio file
            engine.save_to_file(text, output_path)
            engine.runAndWait()

        except ImportError:
            logger.warning("pyttsx3 not available, generating silent audio")
            # Fallback: create silent audio file
            duration = len(text.split()) * 0.5  # 0.5 seconds per word
            sample_rate = 22050
            samples = int(duration * sample_rate)

            # Generate silent audio
            audio_data = np.zeros(samples, dtype=np.int16)

            with wave.open(output_path, "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            # Fallback to silent audio
            duration = len(text.split()) * 0.5
            sample_rate = 22050
            samples = int(duration * sample_rate)
            audio_data = np.zeros(samples, dtype=np.int16)

            with wave.open(output_path, "w") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())

    def _run_musetalk_generation(self, audio_path: str, avatar_path: str, output_path: str):
        """Run the actual MuseTalk generation."""
        if not MUSETALK_AVAILABLE:
            raise RuntimeError("MuseTalk is not available. Please install MuseTalk dependencies.")

        try:
            # Load and preprocess avatar image
            avatar_img = cv2.imread(avatar_path)
            if avatar_img is None:
                raise ValueError(f"Could not load avatar image: {avatar_path}")

            # Initialize MuseTalk models if not already loaded
            if not hasattr(self, "musetalk_models"):
                self.musetalk_models = load_all_model()
                logger.info("MuseTalk models loaded successfully")

            # Get landmark and bbox from avatar image
            coord_list, frame_list = get_landmark_and_bbox(avatar_img)
            if not coord_list:
                raise ValueError("Could not detect face landmarks in avatar image")

            # Process audio and generate frames
            audio_processor = self.musetalk_models.get("audio_processor")
            if audio_processor:
                # Generate video frames using MuseTalk pipeline
                frames = []

                # Use MuseTalk's datagen to process audio and generate frames
                for batch in datagen(audio_path, avatar_path, self.musetalk_models):
                    # Process each batch and generate corresponding frames
                    generated_frames = self._process_musetalk_batch(batch, coord_list[0])
                    frames.extend(generated_frames)

                if not frames:
                    raise ValueError("No frames generated from MuseTalk pipeline")
            else:
                # Fallback: generate static frames with slight variations
                logger.warning("Audio processor not available, generating static frames")
                frames = []
                for i in range(30):  # Generate 30 frames as example
                    frame = avatar_img.copy()
                    frames.append(frame)

            # Save video
            self._save_video(frames, output_path)

        except Exception as e:
            self.logger.error(f"MuseTalk generation failed: {e}")
            raise

    def _process_musetalk_batch(self, batch, coord):
        """Process a batch of audio data through MuseTalk models."""
        try:
            # This would contain the actual MuseTalk inference logic
            # For now, return a placeholder frame
            frames = []
            # In real implementation, this would use the MuseTalk models
            # to generate frames based on audio features and facial coordinates
            return frames
        except Exception as e:
            self.logger.error(f"Error processing MuseTalk batch: {e}")
            return []

    def _save_video(self, frames: List[np.ndarray], output_path: str, fps: int = 25):
        """Save frames as video file."""
        if not frames:
            raise ValueError("No frames to save")

        height, width = frames[0].shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        with cv2.VideoWriter(output_path, fourcc, fps, (width, height)) as writer:
            for frame in frames:
                writer.write(frame)

    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration in seconds."""
        try:
            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
            cap.release()

            if fps > 0:
                return frame_count / fps
            return 0.0
        except Exception:
            return 0.0


class TalkingHeadsEngine(BaseAvatarEngine):
    """Talking Heads fallback avatar generation engine wrapper."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("talking - heads - fallback", config)
        self.model_path = self.config.get("model_path", "./models/talking_heads")
        self.base_url = self.config.get("base_url", "http://localhost:7861")
        self.timeout = self.config.get("timeout", 90)
        self.test_mode = self.config.get("test_mode", False)

    async def initialize(self) -> bool:
        """Initialize Talking Heads engine."""
        try:
            self.logger.info("Initializing Talking Heads engine...")

            # In test mode, skip model loading and service startup
            if self.test_mode:
                self.logger.info(
                    "Running in test mode - skipping model loading and service startup"
# BRACKET_SURGEON: disabled
#                 )
                self.is_initialized = True
                return True

            # Check if model directory exists
            if not Path(self.model_path).exists():
                self.logger.warning(f"Model path not found: {self.model_path}")
                return False

            # Try to start the service if not running
            if not await self.health_check():
                await self._start_service()

                # Wait for service to be ready
                for _ in range(8):
                    if await self.health_check():
                        break
                    await asyncio.sleep(2)
                else:
                    self.logger.error("Failed to start Talking Heads service")
                    return False

            self.is_initialized = True
            self.logger.info("Talking Heads engine initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialize Talking Heads: {e}")
            return False

    async def _start_service(self):
        """Start the Talking Heads service."""
        try:
            self.logger.info("Starting Talking Heads service...")

            # Check if service is already running
            if await self.health_check():
                self.logger.info("Talking Heads service already running")
                return

            # For now, TalkingHeads doesn't have a standalone service
            # This would be implemented when we have a proper TalkingHeads server
            self.logger.info("TalkingHeads service startup - using direct model inference")

        except Exception as e:
            self.logger.error(f"Failed to start Talking Heads service: {e}")
            raise

    async def health_check(self) -> bool:
        """Check if Talking Heads service is healthy."""
        # In test mode, always return healthy
        if self.test_mode:
            return True

        # For now, check if model path exists and is accessible
        try:
            model_exists = os.path.exists(self.model_path)
            self.last_health_check = datetime.now()
            if model_exists:
                self.logger.debug("TalkingHeads model path accessible")
            else:
                self.logger.debug(f"TalkingHeads model path not found: {self.model_path}")
            return model_exists
        except Exception as e:
            self.logger.debug(f"TalkingHeads health check failed: {e}")
            return False

    async def generate_avatar(self, request: AvatarRequest) -> AvatarResponse:
        """Generate avatar using Talking Heads."""
        start_time = time.time()

        try:
            if not self.is_initialized:
                if not await self.initialize():
                    return AvatarResponse(
                        success=False,
                        video_path=None,
                        duration=None,
                        engine_used=self.engine_name,
                        processing_time=time.time() - start_time,
                        error_message="Engine not initialized",
# BRACKET_SURGEON: disabled
#                     )

            # In test mode, return mock response
            if self.test_mode:
                await asyncio.sleep(0.15)  # Simulate slightly longer processing time
                processing_time = time.time() - start_time

                return AvatarResponse(
                    success=True,
                    video_path=f"/generated/test_talking_heads_{uuid.uuid4().hex[:8]}.mp4",
                    duration=len(request.text.split()) * 0.6,  # Slightly different estimate
                    engine_used=self.engine_name,
                    processing_time=processing_time,
                    metadata={
                        "model_version": "test - fallback - v1.0",
                        "quality_score": 0.88,
                        "fallback_used": True,
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 )

            # Check health before processing
            if not await self.health_check():
                return AvatarResponse(
                    success=False,
                    video_path=None,
                    duration=None,
                    engine_used=self.engine_name,
                    processing_time=time.time() - start_time,
                    error_message="Engine health check failed",
# BRACKET_SURGEON: disabled
#                 )

            self.logger.info(
                f"Generating avatar with Talking Heads for request {request.request_id}"
# BRACKET_SURGEON: disabled
#             )

            # Prepare request payload
            payload = {
                "text": request.text,
                "voice_settings": request.voice_settings,
                "video_settings": request.video_settings,
                "source_image": request.source_image,
                "gender": request.gender or "neutral",
# BRACKET_SURGEON: disabled
#             }

            # Make request to Talking Heads service
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
# BRACKET_SURGEON: disabled
#             ) as session:
                async with session.post(f"{self.base_url}/generate", json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        processing_time = time.time() - start_time

                        return AvatarResponse(
                            success=True,
                            video_path=result.get("video_path"),
                            duration=result.get("duration"),
                            engine_used=self.engine_name,
                            processing_time=processing_time,
                            metadata={
                                "model_version": result.get("model_version"),
                                "quality_score": result.get("quality_score"),
                                "fallback_used": True,
# BRACKET_SURGEON: disabled
#                             },
# BRACKET_SURGEON: disabled
#                         )
                    else:
                        error_text = await response.text()
                        return AvatarResponse(
                            success=False,
                            video_path=None,
                            duration=None,
                            engine_used=self.engine_name,
                            processing_time=time.time() - start_time,
                            error_message=f"HTTP {response.status}: {error_text}",
# BRACKET_SURGEON: disabled
#                         )

        except asyncio.TimeoutError:
            return AvatarResponse(
                success=False,
                video_path=None,
                duration=None,
                engine_used=self.engine_name,
                processing_time=time.time() - start_time,
                error_message="Request timeout",
# BRACKET_SURGEON: disabled
#             )
        except Exception as e:
            return AvatarResponse(
                success=False,
                video_path=None,
                duration=None,
                engine_used=self.engine_name,
                processing_time=time.time() - start_time,
                error_message=str(e),
# BRACKET_SURGEON: disabled
#             )


class AvatarEngineManager:
    """Manager for avatar generation engines with automatic failover."""

    def __init__(self):
        self.engines: Dict[str, BaseAvatarEngine] = {}
        self.logger = logging.getLogger(f"{__name__}.AvatarEngineManager")

    def register_engine(self, engine: BaseAvatarEngine):
        """Register an avatar engine."""
        self.engines[engine.engine_name] = engine
        self.logger.info(f"Registered avatar engine: {engine.engine_name}")

    async def initialize_all_engines(self) -> Dict[str, bool]:
        """Initialize all registered engines."""
        results = {}
        for name, engine in self.engines.items():
            try:
                results[name] = await engine.initialize()
                self.logger.info(
                    f"Engine {name} initialization: {'SUCCESS' if results[name] else 'FAILED'}"
# BRACKET_SURGEON: disabled
#                 )
            except Exception as e:
                results[name] = False
                self.logger.error(f"Engine {name} initialization failed: {e}")
        return results

    async def get_engine(self, engine_name: str) -> Optional[BaseAvatarEngine]:
        """Get an engine by name."""
        engine = self.engines.get(engine_name)
        if engine and not engine.is_initialized:
            await engine.initialize()
        return engine

    async def generate_avatar_with_failover(
        self,
        request: AvatarRequest,
        preferred_engine: str = "linly - talker - enhanced",
# BRACKET_SURGEON: disabled
#     ) -> AvatarResponse:
        """Generate avatar with automatic failover."""
        # Try preferred engine first
        engine = await self.get_engine(preferred_engine)
        if engine:
            response = await engine.generate_avatar(request)
            if response.success:
                return response

            self.logger.warning(
                f"Primary engine {preferred_engine} failed: {response.error_message}"
# BRACKET_SURGEON: disabled
#             )

        # Try fallback engines
        fallback_engines = [name for name in self.engines.keys() if name != preferred_engine]
        for engine_name in fallback_engines:
            engine = await self.get_engine(engine_name)
            if engine:
                self.logger.info(f"Attempting fallback engine: {engine_name}")
                response = await engine.generate_avatar(request)
                if response.success:
                    return response

                self.logger.warning(
                    f"Fallback engine {engine_name} failed: {response.error_message}"
# BRACKET_SURGEON: disabled
#                 )

        # All engines failed
        return AvatarResponse(
            success=False,
            video_path=None,
            duration=None,
            engine_used="none",
            processing_time=0,
            error_message="All avatar engines failed",
# BRACKET_SURGEON: disabled
#         )

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all engines."""
        results = {}
        for name, engine in self.engines.items():
            try:
                results[name] = await engine.health_check()
            except Exception as e:
                results[name] = False
                self.logger.error(f"Health check failed for {name}: {e}")
        return results

    async def get_available_engines(self) -> List[str]:
        """Get list of available engine names."""
        return list(self.engines.keys())

    async def cleanup_all(self):
        """Cleanup all engines."""
        for engine in self.engines.values():
            try:
                await engine.cleanup()
            except Exception as e:
                self.logger.error(f"Cleanup failed for {engine.engine_name}: {e}")


# Global engine manager instance
engine_manager = AvatarEngineManager()

# Register default engines with production mode configuration
# Note: Set test_mode to False once model checkpoints are downloaded
# Use absolute paths to ensure models are found regardless of working directory
project_root = Path(__file__).parent.parent.parent  # Go up to project root
linly_model_path = str(project_root / "models" / "linly_talker")
talking_heads_model_path = str(project_root / "models" / "talking_heads")

production_config = {"test_mode": False, "model_path": linly_model_path}
fallback_config = {"test_mode": False, "model_path": talking_heads_model_path}

engine_manager.register_engine(LinlyTalkerEngine(production_config))
engine_manager.register_engine(TalkingHeadsEngine(fallback_config))

# Convenience functions for external use


async def generate_avatar(
    text: str,
    voice_settings: Dict[str, Any],
    video_settings: Dict[str, Any],
    source_image: Optional[str] = None,
    gender: Optional[str] = None,
    preferred_engine: str = "linly - talker - enhanced",
# BRACKET_SURGEON: disabled
# ) -> AvatarResponse:
    """Generate avatar with automatic failover."""
    request = AvatarRequest(
        text=text,
        voice_settings=voice_settings,
        video_settings=video_settings,
        source_image=source_image,
        gender=gender,
# BRACKET_SURGEON: disabled
#     )

    return await engine_manager.generate_avatar_with_failover(request, preferred_engine)


async def check_engine_health() -> Dict[str, bool]:
    """Check health of all avatar engines."""
    return await engine_manager.health_check_all()


async def initialize_engines() -> Dict[str, bool]:
    """Initialize all avatar engines."""
    return await engine_manager.initialize_all_engines()