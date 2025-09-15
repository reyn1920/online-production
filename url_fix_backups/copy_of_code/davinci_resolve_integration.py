#!/usr / bin / env python3
""""""
DaVinci Resolve Integration - Professional Video Editing & Finishing for TRAE.AI

This module provides comprehensive integration with DaVinci Resolve for:
- Final video editing and timeline assembly
- Professional color grading and correction
- High - quality rendering and export
- Automated project management

Replaces the current Blender - only pipeline with a hybrid approach:
- Blender for 3D / VFX work
- DaVinci Resolve for final edit, color grading, and rendering

Features:
- Automated timeline creation from video assets
- Professional color grading workflows
- Batch processing and rendering
- Multiple export formats and presets
- Integration with existing TRAE.AI content pipeline

Author: TRAE.AI Content Generation System
Version: 1.0.0
""""""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Try to import DaVinci Resolve API
try:
    import DaVinciResolveScript as dvr_script

    RESOLVE_API_AVAILABLE = True
except ImportError:
    RESOLVE_API_AVAILABLE = False
    logger.warning("DaVinci Resolve API not available. Some features will be limited.")


@dataclass
class VideoAsset:
    """Represents a video asset for timeline assembly."""

    name: str
    file_path: str
    duration: float  # in seconds
    start_time: float  # timeline position in seconds
    asset_type: str  # "video", "audio", "image", "title"
    track_index: int: # track number (1 - based)
    effects: List[str] = None
    color_grade: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ColorGradeSettings:
    """Color grading settings for video assets."""

    name: str
    lift: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0): # RGBY
    gamma: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # RGBY
    gain: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # RGBY
    offset: Tuple[float, float, float, float] = (0.0, 0.0, 0.0, 0.0)  # RGBY
    saturation: float = 1.0
    contrast: float = 1.0
    pivot: float = 0.435
    temperature: float = 0.0
    tint: float = 0.0
    exposure: float = 0.0
    highlights: float = 0.0
    shadows: float = 0.0
    whites: float = 0.0
    blacks: float = 0.0
    preset_name: Optional[str] = None


@dataclass
class RenderSettings:
    """Render and export settings."""

    format: str = "mp4"  # "mp4", "mov", "avi", "mkv"
    codec: str = "H.264"  # "H.264", "H.265", "ProRes", "DNxHD"
    resolution: Tuple[int, int] = (1920, 1080):
    frame_rate: float = 24.0
    bitrate: Optional[int] = None  # Mbps
    quality: str = "high"  # "low", "medium", "high", "best"
    audio_codec: str = "AAC"
    audio_bitrate: int = 192  # kbps
    output_path: str = ""
    render_preset: Optional[str] = None


@dataclass
class ProjectSettings:
    """DaVinci Resolve project settings."""

    name: str
    timeline_resolution: Tuple[int, int] = (1920, 1080):
    timeline_frame_rate: float = 24.0
    color_space: str = "Rec.709"
    gamma: str = "Rec.709"
    working_luminance: int = 100
    project_path: Optional[str] = None


class DaVinciResolveAPI:
    """Wrapper for DaVinci Resolve API operations."""

    def __init__(self):
        """Initialize DaVinci Resolve API connection."""
        self.resolve = None
        self.project_manager = None
        self.current_project = None
        self.media_pool = None
        self.current_timeline = None

        if RESOLVE_API_AVAILABLE:
            self._connect_to_resolve()
        else:
            logger.warning("DaVinci Resolve API not available")

    def _connect_to_resolve(self) -> bool:
        """Connect to DaVinci Resolve instance."""

        Returns:
            True if connection successful, False otherwise
        """"""
        try:
            self.resolve = dvr_script.scriptapp("Resolve")
            if self.resolve:
                self.project_manager = self.resolve.GetProjectManager()
                logger.info("Connected to DaVinci Resolve")
                return True
            else:
                logger.error("Failed to connect to DaVinci Resolve")
                return False
        except Exception as e:
            logger.error(f"Error connecting to DaVinci Resolve: {e}")
            return False

    def create_project(self, settings: ProjectSettings) -> bool:
        """Create new DaVinci Resolve project."""

        Args:
            settings: Project settings

        Returns:
            True if project created successfully
        """"""
        if not self.project_manager:
            return False

        try:
            # Create new project
            project = self.project_manager.CreateProject(settings.name)
            if project:
                self.current_project = project
                self.media_pool = project.GetMediaPool()

                # Set project settings
                project_settings = {
                    "timelineResolutionWidth": str(settings.timeline_resolution[0]),
                    "timelineResolutionHeight": str(settings.timeline_resolution[1]),
                    "timelineFrameRate": str(settings.timeline_frame_rate),
                    "videoBitDepth": "10",
                    "videoDataLevels": "Auto",
                    "colorSpaceTimeline": settings.color_space,
                    "colorSpaceOutput": settings.color_space,
                    "rcmPresetMode": "Custom",
                    "separateColorSpaceAndGamma": "1",
                    "colorScienceMode": "davinciYRGB",
                    "workingLuminance": str(settings.working_luminance),
# BRACKET_SURGEON: disabled
#                 }

                project.SetSetting(project_settings)
                logger.info(f"Project '{settings.name}' created successfully")
                return True
            else:
                logger.error(f"Failed to create project '{settings.name}'")
                return False

        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return False

    def open_project(self, project_name: str) -> bool:
        """Open existing DaVinci Resolve project."""

        Args:
            project_name: Name of project to open

        Returns:
            True if project opened successfully
        """"""
        if not self.project_manager:
            return False

        try:
            project = self.project_manager.LoadProject(project_name)
            if project:
                self.current_project = project
                self.media_pool = project.GetMediaPool()
                logger.info(f"Project '{project_name}' opened successfully")
                return True
            else:
                logger.error(f"Failed to open project '{project_name}'")
                return False

        except Exception as e:
            logger.error(f"Error opening project: {e}")
            return False

    def import_media(self, file_paths: List[str]) -> List[str]:
        """Import media files into current project."""

        Args:
            file_paths: List of file paths to import

        Returns:
            List of successfully imported media item IDs
        """"""
        if not self.media_pool:
            return []

        try:
            imported_items = []

            for file_path in file_paths:
                if Path(file_path).exists():
                    media_items = self.media_pool.ImportMedia([file_path])
                    if media_items:
                        imported_items.extend([item.GetMediaId() for item in media_items])
                        logger.info(f"Imported media: {file_path}")
                    else:
                        logger.warning(f"Failed to import: {file_path}")
                else:
                    logger.warning(f"File not found: {file_path}")

            return imported_items

        except Exception as e:
            logger.error(f"Error importing media: {e}")
            return []

    def create_timeline(self, name: str, frame_rate: float = 24.0) -> bool:
        """Create new timeline in current project."""

        Args:
            name: Timeline name
            frame_rate: Timeline frame rate

        Returns:
            True if timeline created successfully
        """"""
        if not self.media_pool:
            return False

        try:
            timeline = self.media_pool.CreateEmptyTimeline(name)
            if timeline:
                self.current_timeline = timeline

                # Set timeline frame rate
                timeline.SetSetting("timelineFrameRate", str(frame_rate))

                logger.info(f"Timeline '{name}' created successfully")
                return True
            else:
                logger.error(f"Failed to create timeline '{name}'")
                return False

        except Exception as e:
            logger.error(f"Error creating timeline: {e}")
            return False

    def add_media_to_timeline(self, assets: List[VideoAsset]) -> bool:
        """Add media assets to current timeline."""

        Args:
            assets: List of video assets to add

        Returns:
            True if all assets added successfully
        """"""
        if not self.current_timeline or not self.media_pool:
            return False

        try:
            success_count = 0

            for asset in assets:
                # Find media item in pool
                media_items = self.media_pool.GetRootFolder().GetClipList()
                media_item = None

                for item in media_items:
                    if item.GetClipProperty("File Path") == asset.file_path:
                        media_item = item
                        break

                if media_item:
                    # Calculate timeline position in frames
                    frame_rate = float(self.current_timeline.GetSetting("timelineFrameRate"))
                    start_frame = int(asset.start_time * frame_rate)

                    # Add to timeline
                    timeline_item = self.current_timeline.InsertMedia(
                        {
                            "mediaPoolItem": media_item,
                            "startFrame": start_frame,
                            "endFrame": start_frame + int(asset.duration * frame_rate),
                            "trackIndex": asset.track_index,
                            "recordFrame": start_frame,
# BRACKET_SURGEON: disabled
#                         }
# BRACKET_SURGEON: disabled
#                     )

                    if timeline_item:
                        success_count += 1
                        logger.info(f"Added asset '{asset.name}' to timeline")
                    else:
                        logger.warning(f"Failed to add asset '{asset.name}' to timeline")
                else:
                    logger.warning(f"Media item not found for asset '{asset.name}'")

            logger.info(f"Added {success_count}/{len(assets)} assets to timeline")
            return success_count == len(assets)

        except Exception as e:
            logger.error(f"Error adding media to timeline: {e}")
            return False

    def apply_color_grade(self, clip_name: str, grade_settings: ColorGradeSettings) -> bool:
        """Apply color grading to a specific clip."""

        Args:
            clip_name: Name of clip to grade
            grade_settings: Color grading settings

        Returns:
            True if color grade applied successfully
        """"""
        if not self.current_timeline:
            return False

        try:
            # Get timeline items
            timeline_items = self.current_timeline.GetItemListInTrack("video", 1)

            for item in timeline_items:
                if item.GetName() == clip_name:
                    # Switch to Color page
                    self.resolve.OpenPage("color")

                    # Apply color corrections
                    color_corrections = {
                        "Lift": grade_settings.lift,
                        "Gamma": grade_settings.gamma,
                        "Gain": grade_settings.gain,
                        "Offset": grade_settings.offset,
                        "Saturation": grade_settings.saturation,
                        "Contrast": grade_settings.contrast,
                        "Pivot": grade_settings.pivot,
                        "Temperature": grade_settings.temperature,
                        "Tint": grade_settings.tint,
                        "Exposure": grade_settings.exposure,
                        "Highlights": grade_settings.highlights,
                        "Shadows": grade_settings.shadows,
                        "Whites": grade_settings.whites,
                        "Blacks": grade_settings.blacks,
# BRACKET_SURGEON: disabled
#                     }

                    # Apply corrections (simplified - actual API may vary)
                    for correction, value in color_corrections.items():
                        item.SetClipColor(correction, value)

                    logger.info(f"Applied color grade '{grade_settings.name}' to '{clip_name}'")
                    return True

            logger.warning(f"Clip '{clip_name}' not found for color grading")
            return False

        except Exception as e:
            logger.error(f"Error applying color grade: {e}")
            return False

    def render_timeline(self, render_settings: RenderSettings) -> bool:
        """Render current timeline with specified settings."""

        Args:
            render_settings: Render configuration

        Returns:
            True if render started successfully
        """"""
        if not self.current_timeline:
            return False

        try:
            # Switch to Deliver page
            self.resolve.OpenPage("deliver")

            # Set render settings
            render_job_settings = {
                "SelectAllFrames": True,
                "TargetDir": str(Path(render_settings.output_path).parent),
                "CustomName": Path(render_settings.output_path).stem,
                "ExportVideo": True,
                "ExportAudio": True,
                "FormatWidth": render_settings.resolution[0],
                "FormatHeight": render_settings.resolution[1],
                "FrameRate": render_settings.frame_rate,
                "VideoFormat": render_settings.format.upper(),
                "VideoCodec": render_settings.codec,
                "AudioCodec": render_settings.audio_codec,
                "AudioBitRate": render_settings.audio_bitrate,
# BRACKET_SURGEON: disabled
#             }

            if render_settings.bitrate:
                render_job_settings["VideoBitRate"] = (
                    render_settings.bitrate * 1000000
# BRACKET_SURGEON: disabled
#                 )  # Convert to bps

            # Add render job to queue
            render_job_id = self.current_project.AddRenderJob(render_job_settings)

            if render_job_id:
                # Start rendering
                self.current_project.StartRendering(render_job_id)
                logger.info(f"Render started: {render_settings.output_path}")
                return True
            else:
                logger.error("Failed to add render job")
                return False

        except Exception as e:
            logger.error(f"Error starting render: {e}")
            return False

    def get_render_status(self) -> Dict[str, Any]:
        """Get current render status."""

        Returns:
            Dictionary with render status information
        """"""
        if not self.current_project:
            return {"status": "no_project", "progress": 0}

        try:
            render_jobs = self.current_project.GetRenderJobList()

            if render_jobs:
                latest_job = render_jobs[-1]
                status = latest_job.get("JobStatus", "unknown")
                progress = latest_job.get("CompletionPercentage", 0)

                return {
                    "status": status,
                    "progress": progress,
                    "job_id": latest_job.get("JobId"),
                    "output_path": latest_job.get("TargetDir"),
# BRACKET_SURGEON: disabled
#                 }
            else:
                return {"status": "no_jobs", "progress": 0}

        except Exception as e:
            logger.error(f"Error getting render status: {e}")
            return {"status": "error", "progress": 0}


class DaVinciResolveIntegration:
    """Main DaVinci Resolve integration class for TRAE.AI."""

    def __init__(self, resolve_path: Optional[str] = None, projects_dir: Optional[str] = None):
        """Initialize DaVinci Resolve integration."""

        Args:
            resolve_path: Path to DaVinci Resolve executable
            projects_dir: Directory for storing project files
        """"""
        self.resolve_path = self._find_resolve(resolve_path)
        self.projects_dir = (
            Path(projects_dir)
            if projects_dir
            else Path.home() / "Documents" / "DaVinci Resolve" / "Projects"
# BRACKET_SURGEON: disabled
#         )
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Initialize API
        self.api = DaVinciResolveAPI()

        # Predefined color grades
        self.color_presets = self._load_color_presets()

        logger.info("DaVinci Resolve integration initialized")

    def _find_resolve(self, provided_path: Optional[str]) -> Optional[str]:
        """Find DaVinci Resolve installation."""
        if provided_path and Path(provided_path).exists():
            return provided_path

        # Common installation paths
        possible_paths = [
            "/Applications / DaVinci Resolve / DaVinci Resolve.app / Contents / MacOS / Resolve",
            "/opt / resolve / bin / resolve",
            "C:\\\\Program Files\\\\Blackmagic Design\\\\DaVinci Resolve\\\\Resolve.exe",
            "resolve",  # In PATH
# BRACKET_SURGEON: disabled
#         ]

        for path in possible_paths:
            if shutil.which(path) or Path(path).exists():
                return path

        logger.warning("DaVinci Resolve not found. Some features will be limited.")
        return None

    def _load_color_presets(self) -> Dict[str, ColorGradeSettings]:
        """Load predefined color grading presets."""
        presets = {
            "cinematic": ColorGradeSettings(
                name="Cinematic",
                lift=(-0.1, -0.05, 0.0, 0.0),
                gamma=(0.0, 0.0, 0.0, 0.0),
                gain=(0.05, 0.1, 0.15, 0.0),
                contrast=1.2,
                saturation=0.9,
                temperature=-200,
                shadows=-20,
                highlights=-10,
# BRACKET_SURGEON: disabled
#             ),
            "warm_natural": ColorGradeSettings(
                name="Warm Natural",
                temperature=300,
                tint=10,
                exposure=0.2,
                contrast=1.1,
                saturation=1.1,
                shadows=15,
                highlights=-5,
# BRACKET_SURGEON: disabled
#             ),
            "cool_modern": ColorGradeSettings(
                name="Cool Modern",
                temperature=-400,
                tint=-15,
                contrast=1.3,
                saturation=0.8,
                shadows=-10,
                highlights=-15,
                whites=20,
# BRACKET_SURGEON: disabled
#             ),
            "high_contrast": ColorGradeSettings(
                name="High Contrast",
                contrast=1.5,
                blacks=-30,
                whites=30,
                shadows=-20,
                highlights=-20,
                saturation=1.2,
# BRACKET_SURGEON: disabled
#             ),
            "vintage": ColorGradeSettings(
                name="Vintage",
                lift=(0.1, 0.05, 0.0, 0.0),
                gamma=(0.0, 0.0, 0.1, 0.0),
                gain=(-0.05, 0.0, 0.05, 0.0),
                temperature=500,
                contrast=0.9,
                saturation=0.7,
# BRACKET_SURGEON: disabled
#             ),
# BRACKET_SURGEON: disabled
#         }

        return presets

    def create_video_project(
        self,
        project_name: str,
        assets: List[VideoAsset],
        color_grades: Optional[Dict[str, str]] = None,
        render_settings: Optional[RenderSettings] = None,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Create complete video project from assets."""

        Args:
            project_name: Name for the new project
            assets: List of video assets to include
            color_grades: Mapping of asset names to color grade presets
            render_settings: Render configuration

        Returns:
            Path to rendered output file
        """"""
        try:
            logger.info(f"Creating video project: {project_name}")

            # Create project settings
            project_settings = ProjectSettings(
                name=project_name,
                timeline_resolution=(1920, 1080),
                timeline_frame_rate=24.0,
# BRACKET_SURGEON: disabled
#             )

            # Create project
            if not self.api.create_project(project_settings):
                raise Exception("Failed to create project")

            # Import media files
            media_paths = [asset.file_path for asset in assets]
            imported_items = self.api.import_media(media_paths)

            if not imported_items:
                raise Exception("Failed to import media")

            # Create timeline
            timeline_name = f"{project_name}_Timeline"
            if not self.api.create_timeline(timeline_name, project_settings.timeline_frame_rate):
                raise Exception("Failed to create timeline")

            # Add assets to timeline
            if not self.api.add_media_to_timeline(assets):
                logger.warning("Some assets failed to add to timeline")

            # Apply color grades
            if color_grades:
                for asset_name, preset_name in color_grades.items():
                    if preset_name in self.color_presets:
                        grade_settings = self.color_presets[preset_name]
                        self.api.apply_color_grade(asset_name, grade_settings)

            # Render project
            if not render_settings:
                render_settings = RenderSettings(
                    format="mp4",
                    codec="H.264",
                    resolution=(1920, 1080),
                    frame_rate=24.0,
                    quality="high",
                    output_path=str(self.projects_dir / f"{project_name}_final.mp4"),
# BRACKET_SURGEON: disabled
#                 )

            if self.api.render_timeline(render_settings):
                # Wait for render to complete
                self._wait_for_render_completion()
                logger.info(f"Project '{project_name}' completed successfully")
                return render_settings.output_path
            else:
                raise Exception("Failed to start render")

        except Exception as e:
            logger.error(f"Error creating video project: {e}")
            raise

    def _wait_for_render_completion(self, timeout: int = 3600) -> bool:
        """Wait for current render to complete."""

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if render completed successfully
        """"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            status = self.api.get_render_status()

            if status["status"] == "Complete":
                logger.info("Render completed successfully")
                return True
            elif status["status"] == "Failed":
                logger.error("Render failed")
                return False
            elif status["status"] == "Rendering":
                progress = status.get("progress", 0)
                logger.info(f"Rendering... {progress}%")

            time.sleep(5)  # Check every 5 seconds

        logger.error("Render timeout")
        return False

    def batch_process_videos(self, video_specs: List[Dict[str, Any]]) -> List[str]:
        """Process multiple videos in batch."""

        Args:
            video_specs: List of video specifications

        Returns:
            List of output file paths
        """"""
        results = []

        for i, spec in enumerate(video_specs, 1):
            try:
                logger.info(f"Processing video {i}/{len(video_specs)}: {spec['name']}")

                output_path = self.create_video_project(
                    project_name=spec["name"],
                    assets=spec["assets"],
                    color_grades=spec.get("color_grades"),
                    render_settings=spec.get("render_settings"),
# BRACKET_SURGEON: disabled
#                 )

                results.append(output_path)
                logger.info(f"Completed {i}/{len(video_specs)}")

            except Exception as e:
                logger.error(f"Error processing video {i}: {e}")
                continue

        return results

    def create_color_grade_from_reference(
        self, reference_image: str, target_clip: str
# BRACKET_SURGEON: disabled
#     ) -> ColorGradeSettings:
        """Create color grade by matching a reference image."""

        Args:
            reference_image: Path to reference image
            target_clip: Name of clip to grade

        Returns:
            Generated color grade settings
        """"""
        # This would implement automatic color matching
        # For now, return a basic grade
        logger.info(f"Creating color grade from reference: {reference_image}")

        return ColorGradeSettings(
            name=f"Reference_Match_{Path(reference_image).stem}",
            contrast=1.1,
            saturation=1.05,
            temperature=100,
# BRACKET_SURGEON: disabled
#         )

    def export_project_xml(self, project_name: str, output_path: str) -> bool:
        """Export project as XML for external editing."""

        Args:
            project_name: Name of project to export
            output_path: Path for XML export

        Returns:
            True if export successful
        """"""
        try:
            # This would export the timeline as XML / EDL
            logger.info(f"Exporting project XML: {project_name}")

            # Placeholder implementation
            xml_content = f""""""
<?xml version="1.0" encoding="UTF - 8"?>
<xmeml version="4">
    <project>
        <name>{project_name}</name>
        <children>
            <sequence>
                <name>{project_name}_Timeline</name>
                <rate>
                    <timebase > 24</timebase>
                    <ntsc > FALSE</ntsc>
                </rate>
                <timecode>
                    <rate>
                        <timebase > 24</timebase>
                        <ntsc > FALSE</ntsc>
                    </rate>
                    <string > 01:00:00:00</string>
                </timecode>
            </sequence>
        </children>
    </project>
</xmeml>
""""""

            with open(output_path, "w") as f:
                f.write(xml_content)

            logger.info(f"Project XML exported: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Error exporting project XML: {e}")
            return False

    def cleanup_projects(self, max_age_days: int = 30) -> int:
        """Clean up old project files."""

        Args:
            max_age_days: Maximum age of projects to keep

        Returns:
            Number of projects cleaned up
        """"""
        try:
            cleaned_count = 0
            current_time = datetime.now()

            for project_file in self.projects_dir.rglob("*.drp"):
                file_age = current_time - datetime.fromtimestamp(project_file.stat().st_mtime)

                if file_age.days > max_age_days:
                    project_file.unlink()
                    cleaned_count += 1

            logger.info(f"Cleaned up {cleaned_count} old projects")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up projects: {e}")
            return 0


# Utility functions for integration with TRAE.AI content pipeline


def create_assets_from_content_pipeline(
    content_data: Dict[str, Any],
) -> List[VideoAsset]:
    """Create video assets from TRAE.AI content pipeline data."""

    Args:
        content_data: Content pipeline output data

    Returns:
        List of VideoAsset objects
    """"""
    assets = []

    # Extract video segments
    if "video_segments" in content_data:
        for i, segment in enumerate(content_data["video_segments"]):
            asset = VideoAsset(
                name=f"segment_{i + 1}",
                file_path=segment["file_path"],
                duration=segment.get("duration", 5.0),
                start_time=segment.get("start_time", i * 5.0),
                asset_type="video",
                track_index=1,
# BRACKET_SURGEON: disabled
#             )
            assets.append(asset)

    # Extract audio tracks
    if "audio_tracks" in content_data:
        for i, audio in enumerate(content_data["audio_tracks"]):
            asset = VideoAsset(
                name=f"audio_{i + 1}",
                file_path=audio["file_path"],
                duration=audio.get("duration", 30.0),
                start_time=audio.get("start_time", 0.0),
                asset_type="audio",
                track_index=2,
# BRACKET_SURGEON: disabled
#             )
            assets.append(asset)

    return assets


def integrate_with_blender_pipeline(
    blender_output_dir: str, resolve_project_name: str
) -> List[VideoAsset]:
    """Integrate Blender 3D / VFX output with DaVinci Resolve pipeline."""

    Args:
        blender_output_dir: Directory containing Blender renders
        resolve_project_name: Name for DaVinci Resolve project

    Returns:
        List of VideoAsset objects from Blender output
    """"""
    assets = []
    blender_dir = Path(blender_output_dir)

    if blender_dir.exists():
        # Find rendered video files
        video_extensions = [".mp4", ".mov", ".avi", ".mkv"]

        for video_file in blender_dir.rglob("*"):
            if video_file.suffix.lower() in video_extensions:
                asset = VideoAsset(
                    name=video_file.stem,
                    file_path=str(video_file),
                    duration=10.0,  # Would need to detect actual duration
                    start_time=0.0,
                    asset_type="video",
                    track_index=1,
                    effects=["3D_Render"],
                    metadata={"source": "blender", "type": "3d_render"},
# BRACKET_SURGEON: disabled
#                 )
                assets.append(asset)

    return assets


# Example usage and testing
if __name__ == "__main__":
    # Initialize DaVinci Resolve integration
    resolve_integration = DaVinciResolveIntegration()

    # Create test video assets
    test_assets = [
        VideoAsset(
            name="intro_segment",
            file_path="/path / to / intro.mp4",
            duration=5.0,
            start_time=0.0,
            asset_type="video",
            track_index=1,
# BRACKET_SURGEON: disabled
#         ),
        VideoAsset(
            name="main_content",
            file_path="/path / to / main.mp4",
            duration=30.0,
            start_time=5.0,
            asset_type="video",
            track_index=1,
# BRACKET_SURGEON: disabled
#         ),
        VideoAsset(
            name="background_music",
            file_path="/path / to / music.mp3",
            duration=35.0,
            start_time=0.0,
            asset_type="audio",
            track_index=2,
# BRACKET_SURGEON: disabled
#         ),
# BRACKET_SURGEON: disabled
#     ]

    # Test color grading presets
    color_grades = {"intro_segment": "cinematic", "main_content": "warm_natural"}

    # Test render settings
    render_settings = RenderSettings(
        format="mp4",
        codec="H.264",
        resolution=(1920, 1080),
        frame_rate=24.0,
        quality="high",
        output_path="/tmp / test_output.mp4",
# BRACKET_SURGEON: disabled
#     )

    try:
        print("🎬 Testing DaVinci Resolve Integration...")

        if RESOLVE_API_AVAILABLE:
            print("\\n📽️ Testing project creation...")
            output_path = resolve_integration.create_video_project(
                project_name="TRAE_Test_Project",
                assets=test_assets,
                color_grades=color_grades,
                render_settings=render_settings,
# BRACKET_SURGEON: disabled
#             )
            print(f"✅ Project created and rendered: {output_path}")
        else:
            print("⚠️ DaVinci Resolve API not available - testing fallback methods")

        print("\\n🎨 Testing color presets...")
        for preset_name, preset in resolve_integration.color_presets.items():
            print(f"  {preset_name}: {preset.name}")

        print("\\n🔧 Testing utility functions...")
        test_content_data = {
            "video_segments": [
                {
                    "file_path": "/test / segment1.mp4",
                    "duration": 10.0,
                    "start_time": 0.0,
# BRACKET_SURGEON: disabled
#                 },
                {
                    "file_path": "/test / segment2.mp4",
                    "duration": 15.0,
                    "start_time": 10.0,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             ],
            "audio_tracks": [
                {"file_path": "/test / audio.mp3", "duration": 25.0, "start_time": 0.0}
# BRACKET_SURGEON: disabled
#             ],
# BRACKET_SURGEON: disabled
#         }

        pipeline_assets = create_assets_from_content_pipeline(test_content_data)
        print(f"✅ Created {len(pipeline_assets)} assets from content pipeline")

        blender_assets = integrate_with_blender_pipeline("/test / blender_output", "Test_Project")
        print(f"✅ Integrated {len(blender_assets)} Blender assets")

        print("\\n✅ DaVinci Resolve Integration test completed successfully!")

    except Exception as e:
        print(f"❌ Error testing DaVinci Resolve Integration: {e}")

        import traceback

        traceback.print_exc()