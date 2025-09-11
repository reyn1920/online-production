#!/usr/bin/env python3
"""
TRAE.AI OBS Studio Automation Integration

Provides comprehensive automation for OBS Studio live streaming and recording.
Supports scene management, source control, streaming automation, recording workflows,
and integration with the AI CEO content production pipeline.

Features:
- OBS WebSocket API integration
- Scene and source management
- Automated streaming workflows
- Recording session control
- Real-time monitoring
- Multi-platform streaming
- Automated scene switching
- Audio/video source control
- Stream health monitoring
- Integration with content pipeline

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import platform
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil
import websockets

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.secret_store import SecretStore


class StreamingPlatform(Enum):
    """Supported streaming platforms."""

    YOUTUBE = "youtube"
    TWITCH = "twitch"
    FACEBOOK = "facebook"
    LINKEDIN = "linkedin"
    CUSTOM_RTMP = "custom_rtmp"


class RecordingFormat(Enum):
    """Recording output formats."""

    MP4 = "mp4"
    MKV = "mkv"
    MOV = "mov"
    FLV = "flv"


class StreamQuality(Enum):
    """Stream quality presets."""

    LOW = "low"  # 480p, 1000 kbps
    MEDIUM = "medium"  # 720p, 2500 kbps
    HIGH = "high"  # 1080p, 4500 kbps
    ULTRA = "ultra"  # 1080p, 8000 kbps
    CUSTOM = "custom"


class SourceType(Enum):
    """OBS source types."""

    DISPLAY_CAPTURE = "monitor_capture"
    WINDOW_CAPTURE = "window_capture"
    CAMERA = "dshow_input"
    AUDIO_INPUT = "wasapi_input_capture"
    AUDIO_OUTPUT = "wasapi_output_capture"
    MEDIA_SOURCE = "ffmpeg_source"
    IMAGE_SOURCE = "image_source"
    TEXT_SOURCE = "text_gdiplus"
    BROWSER_SOURCE = "browser_source"
    GAME_CAPTURE = "game_capture"


@dataclass
class StreamConfig:
    """Stream configuration."""

    platform: StreamingPlatform
    stream_key: str
    server_url: str
    quality: StreamQuality
    title: str
    description: str = ""
    category: str = ""
    tags: List[str] = None
    thumbnail_path: Optional[str] = None
    scheduled_start: Optional[str] = None
    auto_start: bool = False
    auto_stop: bool = False
    max_duration: Optional[int] = None  # minutes
    metadata: Dict[str, Any] = None


@dataclass
class RecordingConfig:
    """Recording configuration."""

    output_path: str
    format: RecordingFormat
    quality: StreamQuality
    filename_format: str = "%CCYY-%MM-%DD %hh-%mm-%ss"
    auto_start: bool = False
    auto_stop: bool = False
    max_duration: Optional[int] = None  # minutes
    split_file_time: Optional[int] = None  # minutes
    metadata: Dict[str, Any] = None


@dataclass
class SceneItem:
    """OBS scene item configuration."""

    name: str
    source_type: SourceType
    settings: Dict[str, Any]
    transform: Dict[str, Any] = None
    visible: bool = True
    locked: bool = False
    group_name: Optional[str] = None
    filters: List[Dict[str, Any]] = None


@dataclass
class Scene:
    """OBS scene configuration."""

    name: str
    items: List[SceneItem]
    transitions: Dict[str, Any] = None
    hotkeys: Dict[str, str] = None
    metadata: Dict[str, Any] = None


@dataclass
class StreamSession:
    """Active streaming session."""

    id: str
    config: StreamConfig
    status: str = "idle"  # idle, starting, live, stopping, stopped, error
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: int = 0  # seconds
    viewers: int = 0
    bitrate: float = 0.0
    fps: float = 0.0
    dropped_frames: int = 0
    total_frames: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class RecordingSession:
    """Active recording session."""

    id: str
    config: RecordingConfig
    status: str = "idle"  # idle, recording, paused, stopped, error
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration: int = 0  # seconds
    file_size: int = 0  # bytes
    output_file: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class OBSAutomation:
    """
    Comprehensive OBS Studio automation system for streaming and recording.
    Integrates with TRAE.AI content pipeline for automated live content creation.
    """

    def __init__(
        self,
        obs_host: str = "localhost",
        obs_port: int = 4455,
        obs_password: Optional[str] = None,
        secrets_db_path: str = "data/secrets.sqlite",
    ):
        self.logger = setup_logger("obs_automation")
        self.secret_store = SecretStore(secrets_db_path)

        # OBS WebSocket configuration
        self.obs_host = obs_host
        self.obs_port = obs_port
        self.obs_password = obs_password
        self.obs_websocket = None
        self.connected = False

        # Session management
        self.stream_sessions = {}
        self.recording_sessions = {}
        self.active_scene = None
        self.scenes = {}

        # Monitoring
        self.stats_callback = None
        self.event_callbacks = {}
        self.monitoring_task = None

        # Quality presets
        self.quality_presets = {
            StreamQuality.LOW: {
                "video": {"width": 854, "height": 480, "fps": 30, "bitrate": 1000},
                "audio": {"bitrate": 128, "sample_rate": 44100},
            },
            StreamQuality.MEDIUM: {
                "video": {"width": 1280, "height": 720, "fps": 30, "bitrate": 2500},
                "audio": {"bitrate": 160, "sample_rate": 44100},
            },
            StreamQuality.HIGH: {
                "video": {"width": 1920, "height": 1080, "fps": 30, "bitrate": 4500},
                "audio": {"bitrate": 192, "sample_rate": 48000},
            },
            StreamQuality.ULTRA: {
                "video": {"width": 1920, "height": 1080, "fps": 60, "bitrate": 8000},
                "audio": {"bitrate": 320, "sample_rate": 48000},
            },
        }

        # Platform configurations
        self.platform_configs = {
            StreamingPlatform.YOUTUBE: {
                "server": "rtmp://a.rtmp.youtube.com/live2",
                "service": "YouTube - RTMPS",
            },
            StreamingPlatform.TWITCH: {
                "server": "rtmp://live.twitch.tv/app",
                "service": "Twitch",
            },
            StreamingPlatform.FACEBOOK: {
                "server": "rtmps://live-api-s.facebook.com:443/rtmp",
                "service": "Facebook Live",
            },
        }

        self.logger.info("OBS Automation initialized")

    async def initialize(self) -> bool:
        """Initialize OBS automation system."""
        try:
            # Load credentials
            await self._load_credentials()

            # Check if OBS is running
            if not self._is_obs_running():
                self.logger.warning(
                    "OBS Studio is not running. Please start OBS Studio."
                )
                return False

            # Connect to OBS WebSocket
            if await self._connect_to_obs():
                self.logger.info("Connected to OBS Studio")

                # Load current scenes
                await self._load_scenes()

                # Start monitoring
                await self._start_monitoring()

                return True
            else:
                self.logger.error("Failed to connect to OBS Studio")
                return False

        except Exception as e:
            self.logger.error(f"Failed to initialize OBS automation: {e}")
            return False

    async def _load_credentials(self):
        """Load OBS and streaming credentials."""
        try:
            # Load OBS WebSocket password
            obs_password = self.secret_store.get_secret("obs_websocket_password")
            if obs_password:
                self.obs_password = obs_password

            # Load streaming platform credentials
            for platform in StreamingPlatform:
                key_name = f"{platform.value}_stream_key"
                stream_key = self.secret_store.get_secret(key_name)
                if stream_key:
                    self.logger.info(f"Loaded {platform.value} credentials")

        except Exception as e:
            self.logger.warning(f"Could not load credentials: {e}")

    def _is_obs_running(self) -> bool:
        """Check if OBS Studio is running."""
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                if "obs" in proc.info["name"].lower():
                    return True
            return False
        except Exception:
            return False

    async def _connect_to_obs(self) -> bool:
        """Connect to OBS WebSocket server."""
        try:
            uri = f"ws://{self.obs_host}:{self.obs_port}"
            self.obs_websocket = await websockets.connect(uri)

            # Perform authentication if password is set
            if self.obs_password:
                await self._authenticate()

            self.connected = True
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to OBS: {e}")
            return False

    async def _authenticate(self):
        """Authenticate with OBS WebSocket."""
        try:
            # Get authentication info
            auth_request = {"op": 1, "d": {"rpcVersion": 1}}  # Hello

            await self.obs_websocket.send(json.dumps(auth_request))
            response = await self.obs_websocket.recv()
            hello_data = json.loads(response)

            if hello_data.get("op") == 0:  # Hello response
                auth_data = hello_data.get("d", {}).get("authentication", {})

                if auth_data:
                    challenge = auth_data.get("challenge")
                    salt = auth_data.get("salt")

                    # Generate authentication response
                    secret = base64.b64encode(
                        hashlib.sha256((self.obs_password + salt).encode()).digest()
                    ).decode()

                    auth_response = base64.b64encode(
                        hashlib.sha256((secret + challenge).encode()).digest()
                    ).decode()

                    # Send authentication
                    identify_request = {
                        "op": 1,  # Identify
                        "d": {"rpcVersion": 1, "authentication": auth_response},
                    }

                    await self.obs_websocket.send(json.dumps(identify_request))
                    response = await self.obs_websocket.recv()
                    identify_data = json.loads(response)

                    if identify_data.get("op") == 2:  # Identified
                        self.logger.info("OBS authentication successful")
                    else:
                        raise Exception("Authentication failed")

        except Exception as e:
            self.logger.error(f"OBS authentication error: {e}")
            raise

    async def _send_request(self, request_type: str, request_data: Dict = None) -> Dict:
        """Send request to OBS WebSocket."""
        if not self.connected or not self.obs_websocket:
            raise Exception("Not connected to OBS")

        request_id = str(uuid.uuid4())
        request = {
            "op": 6,  # Request
            "d": {
                "requestType": request_type,
                "requestId": request_id,
                "requestData": request_data or {},
            },
        }

        await self.obs_websocket.send(json.dumps(request))

        # Wait for response
        while True:
            response = await self.obs_websocket.recv()
            data = json.loads(response)

            if data.get("op") == 7 and data.get("d", {}).get("requestId") == request_id:
                return data.get("d", {})

    async def _load_scenes(self):
        """Load current scenes from OBS."""
        try:
            # Get scene list
            response = await self._send_request("GetSceneList")
            scenes_data = response.get("responseData", {})

            self.active_scene = scenes_data.get("currentProgramSceneName")

            for scene_data in scenes_data.get("scenes", []):
                scene_name = scene_data.get("sceneName")

                # Get scene items
                items_response = await self._send_request(
                    "GetSceneItemList", {"sceneName": scene_name}
                )

                items_data = items_response.get("responseData", {}).get(
                    "sceneItems", []
                )

                scene_items = []
                for item_data in items_data:
                    scene_item = SceneItem(
                        name=item_data.get("sourceName", ""),
                        source_type=SourceType.DISPLAY_CAPTURE,  # Default, would need to query actual type
                        settings={},
                        visible=item_data.get("sceneItemEnabled", True),
                        locked=item_data.get("sceneItemLocked", False),
                    )
                    scene_items.append(scene_item)

                self.scenes[scene_name] = Scene(name=scene_name, items=scene_items)

            self.logger.info(f"Loaded {len(self.scenes)} scenes from OBS")

        except Exception as e:
            self.logger.error(f"Failed to load scenes: {e}")

    async def _start_monitoring(self):
        """Start monitoring OBS events and stats."""
        try:
            self.monitoring_task = asyncio.create_task(self._monitor_events())
            self.logger.info("Started OBS monitoring")
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")

    async def _monitor_events(self):
        """Monitor OBS events."""
        try:
            while self.connected:
                try:
                    response = await asyncio.wait_for(
                        self.obs_websocket.recv(), timeout=1.0
                    )

                    data = json.loads(response)

                    if data.get("op") == 5:  # Event
                        event_data = data.get("d", {})
                        event_type = event_data.get("eventType")

                        await self._handle_event(event_type, event_data)

                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    self.logger.error(f"Event monitoring error: {e}")
                    break

        except Exception as e:
            self.logger.error(f"Monitoring task error: {e}")

    async def _handle_event(self, event_type: str, event_data: Dict):
        """Handle OBS events."""
        try:
            if event_type == "StreamStateChanged":
                state = event_data.get("eventData", {}).get("outputState")
                await self._handle_stream_state_change(state)

            elif event_type == "RecordStateChanged":
                state = event_data.get("eventData", {}).get("outputState")
                await self._handle_record_state_change(state)

            elif event_type == "CurrentProgramSceneChanged":
                scene_name = event_data.get("eventData", {}).get("sceneName")
                self.active_scene = scene_name
                self.logger.info(f"Scene changed to: {scene_name}")

            # Call registered callbacks
            if event_type in self.event_callbacks:
                callback = self.event_callbacks[event_type]
                if callback:
                    await callback(event_data)

        except Exception as e:
            self.logger.error(f"Event handling error: {e}")

    async def _handle_stream_state_change(self, state: str):
        """Handle stream state changes."""
        for session in self.stream_sessions.values():
            if session.status in ["starting", "live"]:
                if state == "OBS_WEBSOCKET_OUTPUT_STARTED":
                    session.status = "live"
                    session.start_time = datetime.now().isoformat()
                    self.logger.info(f"Stream {session.id} started")

                elif state == "OBS_WEBSOCKET_OUTPUT_STOPPED":
                    session.status = "stopped"
                    session.end_time = datetime.now().isoformat()
                    if session.start_time:
                        duration = (
                            datetime.now() - datetime.fromisoformat(session.start_time)
                        ).total_seconds()
                        session.duration = int(duration)
                    self.logger.info(f"Stream {session.id} stopped")

    async def _handle_record_state_change(self, state: str):
        """Handle recording state changes."""
        for session in self.recording_sessions.values():
            if session.status in ["recording", "paused"]:
                if state == "OBS_WEBSOCKET_OUTPUT_STARTED":
                    session.status = "recording"
                    session.start_time = datetime.now().isoformat()
                    self.logger.info(f"Recording {session.id} started")

                elif state == "OBS_WEBSOCKET_OUTPUT_STOPPED":
                    session.status = "stopped"
                    session.end_time = datetime.now().isoformat()
                    if session.start_time:
                        duration = (
                            datetime.now() - datetime.fromisoformat(session.start_time)
                        ).total_seconds()
                        session.duration = int(duration)
                    self.logger.info(f"Recording {session.id} stopped")

    async def create_scene(self, scene: Scene) -> bool:
        """Create a new scene in OBS."""
        try:
            # Create scene
            await self._send_request("CreateScene", {"sceneName": scene.name})

            # Add scene items
            for item in scene.items:
                # Create source if it doesn't exist
                await self._create_source(item)

                # Add source to scene
                await self._send_request(
                    "CreateSceneItem",
                    {
                        "sceneName": scene.name,
                        "sourceName": item.name,
                        "sceneItemEnabled": item.visible,
                    },
                )

            self.scenes[scene.name] = scene
            self.logger.info(f"Created scene: {scene.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to create scene: {e}")
            return False

    async def _create_source(self, item: SceneItem):
        """Create a source in OBS."""
        try:
            # Check if source already exists
            try:
                await self._send_request("GetSourceSettings", {"sourceName": item.name})
                return  # Source already exists
            except:
                pass  # Source doesn't exist, create it

            # Create source
            await self._send_request(
                "CreateSource",
                {
                    "sourceName": item.name,
                    "sourceKind": item.source_type.value,
                    "sourceSettings": item.settings,
                },
            )

        except Exception as e:
            self.logger.error(f"Failed to create source {item.name}: {e}")

    async def switch_scene(self, scene_name: str) -> bool:
        """Switch to a different scene."""
        try:
            await self._send_request(
                "SetCurrentProgramScene", {"sceneName": scene_name}
            )

            self.active_scene = scene_name
            self.logger.info(f"Switched to scene: {scene_name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to switch scene: {e}")
            return False

    async def start_streaming(self, config: StreamConfig) -> str:
        """Start streaming with specified configuration."""
        try:
            session_id = str(uuid.uuid4())

            # Configure streaming settings
            await self._configure_streaming(config)

            # Start stream
            await self._send_request("StartStream")

            # Create session
            session = StreamSession(id=session_id, config=config, status="starting")

            self.stream_sessions[session_id] = session

            self.logger.info(f"Started streaming session: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Failed to start streaming: {e}")
            raise

    async def _configure_streaming(self, config: StreamConfig):
        """Configure OBS streaming settings."""
        try:
            # Get platform configuration
            platform_config = self.platform_configs.get(config.platform, {})

            # Set stream service
            service_settings = {
                "service": platform_config.get("service", "Custom"),
                "server": config.server_url or platform_config.get("server"),
                "key": config.stream_key,
            }

            await self._send_request(
                "SetStreamServiceSettings", {"streamServiceSettings": service_settings}
            )

            # Set video settings based on quality
            if config.quality in self.quality_presets:
                quality_config = self.quality_presets[config.quality]
                video_settings = quality_config["video"]

                await self._send_request(
                    "SetVideoSettings",
                    {
                        "baseWidth": video_settings["width"],
                        "baseHeight": video_settings["height"],
                        "outputWidth": video_settings["width"],
                        "outputHeight": video_settings["height"],
                        "fpsNumerator": video_settings["fps"],
                        "fpsDenominator": 1,
                    },
                )

        except Exception as e:
            self.logger.error(f"Failed to configure streaming: {e}")
            raise

    async def stop_streaming(self, session_id: str) -> bool:
        """Stop streaming session."""
        try:
            if session_id not in self.stream_sessions:
                raise ValueError(f"Stream session not found: {session_id}")

            session = self.stream_sessions[session_id]
            session.status = "stopping"

            await self._send_request("StopStream")

            self.logger.info(f"Stopped streaming session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop streaming: {e}")
            return False

    async def start_recording(self, config: RecordingConfig) -> str:
        """Start recording with specified configuration."""
        try:
            session_id = str(uuid.uuid4())

            # Configure recording settings
            await self._configure_recording(config)

            # Start recording
            await self._send_request("StartRecord")

            # Create session
            session = RecordingSession(id=session_id, config=config, status="recording")

            self.recording_sessions[session_id] = session

            self.logger.info(f"Started recording session: {session_id}")
            return session_id

        except Exception as e:
            self.logger.error(f"Failed to start recording: {e}")
            raise

    async def _configure_recording(self, config: RecordingConfig):
        """Configure OBS recording settings."""
        try:
            # Set recording path and format
            record_settings = {
                "rec_format": config.format.value,
                "filename_formatting": config.filename_format,
            }

            if config.output_path:
                record_settings["rec_folder"] = config.output_path

            await self._send_request(
                "SetRecordDirectory", {"recordDirectory": config.output_path}
            )

        except Exception as e:
            self.logger.error(f"Failed to configure recording: {e}")
            raise

    async def stop_recording(self, session_id: str) -> bool:
        """Stop recording session."""
        try:
            if session_id not in self.recording_sessions:
                raise ValueError(f"Recording session not found: {session_id}")

            session = self.recording_sessions[session_id]
            session.status = "stopping"

            await self._send_request("StopRecord")

            self.logger.info(f"Stopped recording session: {session_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop recording: {e}")
            return False

    async def get_stream_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get streaming statistics."""
        try:
            if session_id not in self.stream_sessions:
                return None

            # Get stream status
            response = await self._send_request("GetStreamStatus")
            stream_data = response.get("responseData", {})

            session = self.stream_sessions[session_id]

            # Update session stats
            if stream_data.get("outputActive"):
                session.duration = (
                    stream_data.get("outputDuration", 0) // 1000000
                )  # Convert from nanoseconds
                session.bitrate = (
                    stream_data.get("outputBytes", 0) * 8 / 1000
                )  # Convert to kbps
                session.total_frames = stream_data.get("outputTotalFrames", 0)
                session.dropped_frames = stream_data.get("outputSkippedFrames", 0)

            return {
                "session_id": session_id,
                "status": session.status,
                "duration": session.duration,
                "bitrate": session.bitrate,
                "fps": stream_data.get("outputFPS", 0),
                "total_frames": session.total_frames,
                "dropped_frames": session.dropped_frames,
                "drop_percentage": (
                    session.dropped_frames / max(session.total_frames, 1)
                )
                * 100,
            }

        except Exception as e:
            self.logger.error(f"Failed to get stream stats: {e}")
            return None

    async def get_recording_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get recording statistics."""
        try:
            if session_id not in self.recording_sessions:
                return None

            # Get record status
            response = await self._send_request("GetRecordStatus")
            record_data = response.get("responseData", {})

            session = self.recording_sessions[session_id]

            # Update session stats
            if record_data.get("outputActive"):
                session.duration = (
                    record_data.get("outputDuration", 0) // 1000000
                )  # Convert from nanoseconds
                session.file_size = record_data.get("outputBytes", 0)
                session.output_file = record_data.get("outputPath")

            return {
                "session_id": session_id,
                "status": session.status,
                "duration": session.duration,
                "file_size": session.file_size,
                "output_file": session.output_file,
                "recording_active": record_data.get("outputActive", False),
            }

        except Exception as e:
            self.logger.error(f"Failed to get recording stats: {e}")
            return None

    async def create_automated_workflow(
        self, workflow_name: str, scenes: List[Scene], schedule: List[Dict[str, Any]]
    ) -> str:
        """Create an automated streaming/recording workflow."""
        try:
            workflow_id = str(uuid.uuid4())

            # Create scenes
            for scene in scenes:
                await self.create_scene(scene)

            # Store workflow configuration
            workflow_config = {
                "id": workflow_id,
                "name": workflow_name,
                "scenes": [scene.name for scene in scenes],
                "schedule": schedule,
                "created_at": datetime.now().isoformat(),
            }

            # Schedule workflow execution
            asyncio.create_task(self._execute_workflow(workflow_config))

            self.logger.info(f"Created automated workflow: {workflow_name}")
            return workflow_id

        except Exception as e:
            self.logger.error(f"Failed to create workflow: {e}")
            raise

    async def _execute_workflow(self, workflow_config: Dict[str, Any]):
        """Execute automated workflow."""
        try:
            schedule = workflow_config.get("schedule", [])

            for step in schedule:
                action = step.get("action")
                delay = step.get("delay", 0)
                params = step.get("params", {})

                # Wait for delay
                if delay > 0:
                    await asyncio.sleep(delay)

                # Execute action
                if action == "switch_scene":
                    scene_name = params.get("scene_name")
                    if scene_name:
                        await self.switch_scene(scene_name)

                elif action == "start_stream":
                    config = StreamConfig(**params)
                    await self.start_streaming(config)

                elif action == "stop_stream":
                    session_id = params.get("session_id")
                    if session_id:
                        await self.stop_streaming(session_id)

                elif action == "start_recording":
                    config = RecordingConfig(**params)
                    await self.start_recording(config)

                elif action == "stop_recording":
                    session_id = params.get("session_id")
                    if session_id:
                        await self.stop_recording(session_id)

                self.logger.info(f"Executed workflow action: {action}")

        except Exception as e:
            self.logger.error(f"Workflow execution error: {e}")

    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for OBS events."""
        self.event_callbacks[event_type] = callback
        self.logger.info(f"Registered callback for event: {event_type}")

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of OBS automation system."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {},
        }

        # Check OBS connection
        health["components"]["obs_connection"] = {
            "connected": self.connected,
            "host": self.obs_host,
            "port": self.obs_port,
        }

        # Check OBS process
        health["components"]["obs_process"] = {"running": self._is_obs_running()}

        # Check active sessions
        health["components"]["sessions"] = {
            "active_streams": len(
                [s for s in self.stream_sessions.values() if s.status == "live"]
            ),
            "active_recordings": len(
                [s for s in self.recording_sessions.values() if s.status == "recording"]
            ),
            "total_scenes": len(self.scenes),
        }

        # Overall status
        if not self.connected or not self._is_obs_running():
            health["status"] = "unhealthy"

        return health

    async def cleanup(self):
        """Cleanup resources and connections."""
        try:
            # Stop monitoring
            if self.monitoring_task:
                self.monitoring_task.cancel()

            # Stop active streams
            for session_id in list(self.stream_sessions.keys()):
                session = self.stream_sessions[session_id]
                if session.status == "live":
                    await self.stop_streaming(session_id)

            # Stop active recordings
            for session_id in list(self.recording_sessions.keys()):
                session = self.recording_sessions[session_id]
                if session.status == "recording":
                    await self.stop_recording(session_id)

            # Close WebSocket connection
            if self.obs_websocket:
                await self.obs_websocket.close()

            self.connected = False
            self.logger.info("OBS automation cleanup completed")

        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")


# Example usage and testing
if __name__ == "__main__":

    async def test_obs_automation():
        automation = OBSAutomation()

        # Initialize
        if await automation.initialize():
            print("OBS automation initialized successfully")

            # Health check
            health = await automation.health_check()
            print(f"Health status: {health['status']}")
            print(f"Components: {health['components']}")

            # Test scene creation
            test_scene = Scene(
                name="Test Scene",
                items=[
                    SceneItem(
                        name="Display Capture",
                        source_type=SourceType.DISPLAY_CAPTURE,
                        settings={"monitor": 0},
                    )
                ],
            )

            try:
                await automation.create_scene(test_scene)
                print(f"Created test scene: {test_scene.name}")

                # Switch to test scene
                await automation.switch_scene(test_scene.name)
                print(f"Switched to scene: {test_scene.name}")

            except Exception as e:
                print(f"Scene operations failed: {e}")

            # Cleanup
            await automation.cleanup()
        else:
            print("Failed to initialize OBS automation")

    # Run test
    asyncio.run(test_obs_automation())
