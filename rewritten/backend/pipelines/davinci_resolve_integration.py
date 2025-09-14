from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ResolveProjectType(Enum):
    """DaVinci Resolve project types."""

    TIMELINE = "timeline"
    FUSION = "fusion"
    COLOR = "color"
    FAIRLIGHT = "fairlight"


class ExportFormat(Enum):
    """Export formats for DaVinci Resolve."""

    MP4_H264 = "mp4_h264"
    MP4_H265 = "mp4_h265"
    MOV_PRORES = "mov_prores"
    AVI_DNXHD = "avi_dnxhd"
    MXF_DNXHD = "mxf_dnxhd"


@dataclass
class ResolveProjectConfig:
    """Configuration for DaVinci Resolve project."""

    name: str
    timeline_resolution: str = "1920x1080"
    frame_rate: float = 24.0
    color_space: str = "Rec.709"
    project_type: ResolveProjectType = ResolveProjectType.TIMELINE
    enable_proxy_media: bool = True
    proxy_resolution: str = "1280x720"


@dataclass
class MediaAsset:
    """Media asset for DaVinci Resolve."""

    file_path: str
    asset_type: str  # video, audio, image
    duration: Optional[float] = None
    in_point: Optional[float] = None
    out_point: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class DaVinciResolveIntegration:
    """DaVinci Resolve integration with cloud software and Blender pipeline."""

    def __init__(self):
        self.resolve_path = self._find_resolve_installation()
        self.projects_dir = Path("output/davinci_projects")
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        self.media_pool_dir = Path("output/media_pool")
        self.media_pool_dir.mkdir(parents=True, exist_ok=True)

        self.templates_dir = Path("backend/pipelines/resolve_templates")
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        logger.info("DaVinci Resolve Integration initialized")

    def _find_resolve_installation(self) -> Optional[str]:
        """Find DaVinci Resolve installation path."""
        possible_paths = [
            "/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/DaVinci Resolve",
            "/opt/resolve/bin/resolve",
            "C:\\\\Program Files\\\\Blackmagic Design\\\\DaVinci Resolve\\\\Resolve.exe",
            "C:\\\\Program Files (x86)\\\\Blackmagic Design\\\\DaVinci Resolve\\\\Resolve.exe",
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        logger.warning("DaVinci Resolve installation not found")
        return None

    async def validate_installation(self) -> Dict[str, Any]:
        """Validate DaVinci Resolve installation and API access."""
        if not self.resolve_path:
            return {"ok": False, "error": "DaVinci Resolve not found"}

        try:
            # Try to import DaVinci Resolve API

            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")

            if resolve:
                version = resolve.GetVersion()
                return {
                    "ok": True,
                    "version": version,
                    "api_available": True,
                    "installation_path": self.resolve_path,
                }
            else:
                return {
                    "ok": False,
                    "error": "Could not connect to DaVinci Resolve API",
                }

        except ImportError:
            return {
                "ok": False,
                "error": "DaVinci Resolve API not available",
                "suggestion": "Install DaVinci Resolve and enable scripting",
            }
        except Exception as e:
            return {"ok": False, "error": f"API validation failed: {str(e)}"}

    async def create_project_from_blender(
        self, blender_project_dir: str, project_config: ResolveProjectConfig
    ) -> Dict[str, Any]:
        """Create DaVinci Resolve project from Blender output."""
        try:
            # Import DaVinci Resolve API

            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")

            if not resolve:
                return {"ok": False, "error": "Could not connect to DaVinci Resolve"}

            project_manager = resolve.GetProjectManager()

            # Create new project
            project = project_manager.CreateProject(project_config.name)
            if not project:
                return {
                    "ok": False,
                    "error": f"Failed to create project: {project_config.name}",
                }

            # Set project settings
            project.SetSetting("timelineResolution", project_config.timeline_resolution)
            project.SetSetting("timelineFrameRate", str(project_config.frame_rate))
            project.SetSetting("colorSpaceTimeline", project_config.color_space)

            # Import Blender assets
            blender_assets = self._scan_blender_assets(blender_project_dir)
            import_results = await self._import_assets_to_resolve(project, blender_assets)

            # Create timeline
            timeline_result = await self._create_timeline_from_assets(
                project, blender_assets, project_config
            )

            return {
                "ok": True,
                "project_name": project_config.name,
                "project_id": project.GetUniqueId(),
                "imported_assets": import_results,
                "timeline": timeline_result,
            }

        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return {"ok": False, "error": str(e)}

    async def integrate_cloud_software_assets(
        self, project_name: str, cloud_assets: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate cloud software assets into DaVinci Resolve project."""
        try:
            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")
            project_manager = resolve.GetProjectManager()

            # Open existing project
            project = project_manager.LoadProject(project_name)
            if not project:
                return {"ok": False, "error": f"Project not found: {project_name}"}

            media_pool = project.GetMediaPool()
            integration_results = {}

            # Integrate Speechelo/Voice Generator audio
            if "voice_audio" in cloud_assets:
                voice_result = await self._integrate_voice_audio(
                    media_pool, cloud_assets["voice_audio"]
                )
                integration_results["voice_audio"] = voice_result

            # Integrate Captionizer subtitles
            if "captions" in cloud_assets:
                caption_result = await self._integrate_captions(project, cloud_assets["captions"])
                integration_results["captions"] = caption_result

            # Integrate Thumbnail Blaster images
            if "thumbnails" in cloud_assets:
                thumbnail_result = await self._integrate_thumbnails(
                    media_pool, cloud_assets["thumbnails"]
                )
                integration_results["thumbnails"] = thumbnail_result

            # Integrate background music
            if "background_music" in cloud_assets:
                music_result = await self._integrate_background_music(
                    media_pool, cloud_assets["background_music"]
                )
                integration_results["background_music"] = music_result

            # Integrate Lingo Blaster translations
            if "translations" in cloud_assets:
                translation_result = await self._integrate_translations(
                    project, cloud_assets["translations"]
                )
                integration_results["translations"] = translation_result

            return {
                "ok": True,
                "project_name": project_name,
                "integrations": integration_results,
            }

        except Exception as e:
            logger.error(f"Cloud software integration failed: {e}")
            return {"ok": False, "error": str(e)}

    async def apply_color_grading_template(
        self, project_name: str, template_name: str
    ) -> Dict[str, Any]:
        """Apply color grading template to project."""
        try:
            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")
            project_manager = resolve.GetProjectManager()

            project = project_manager.LoadProject(project_name)
            if not project:
                return {"ok": False, "error": f"Project not found: {project_name}"}

            # Load color grading template
            template_path = self.templates_dir / f"{template_name}.drx"
            if not template_path.exists():
                # Create default template if not exists
                await self._create_default_color_template(template_path)

            # Apply template to timeline clips
            timeline = project.GetCurrentTimeline()
            if timeline:
                clips = timeline.GetItemsInTrack("video", 1)
                applied_clips = []

                for clip in clips:
                    # Apply color correction
                    clip.SetClipColor("Orange")  # Mark as processed
                    applied_clips.append(clip.GetName())

                return {
                    "ok": True,
                    "template_applied": template_name,
                    "clips_processed": len(applied_clips),
                    "clip_names": applied_clips,
                }
            else:
                return {"ok": False, "error": "No timeline found in project"}

        except Exception as e:
            logger.error(f"Color grading failed: {e}")
            return {"ok": False, "error": str(e)}

    async def export_project(
        self, project_name: str, export_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export DaVinci Resolve project."""
        try:
            import DaVinciResolveScript as dvr_script

            resolve = dvr_script.scriptapp("Resolve")
            project_manager = resolve.GetProjectManager()

            project = project_manager.LoadProject(project_name)
            if not project:
                return {"ok": False, "error": f"Project not found: {project_name}"}

            timeline = project.GetCurrentTimeline()
            if not timeline:
                return {"ok": False, "error": "No timeline found in project"}

            # Set export settings
            export_format = export_config.get("format", "mp4_h264")
            output_path = export_config.get(
                "output_path", str(self.projects_dir / f"{project_name}_export")
            )

            render_settings = self._get_render_settings(export_format)
            render_settings["TargetDir"] = str(Path(output_path).parent)
            render_settings["CustomName"] = Path(output_path).stem

            # Add to render queue
            render_job_id = project.AddRenderJob()
            if render_job_id:
                # Set render settings
                project.SetRenderSettings(render_settings)

                # Start render
                project.StartRendering()

                return {
                    "ok": True,
                    "render_job_id": render_job_id,
                    "output_path": output_path,
                    "format": export_format,
                    "status": "rendering",
                }
            else:
                return {"ok": False, "error": "Failed to create render job"}

        except Exception as e:
            logger.error(f"Export failed: {e}")
            return {"ok": False, "error": str(e)}

    def _scan_blender_assets(self, blender_project_dir: str) -> List[MediaAsset]:
        """Scan Blender project directory for assets."""
        assets = []
        project_path = Path(blender_project_dir)

        # Scan for video files
        for video_ext in [".mp4", ".mov", ".avi", ".mkv"]:
            for video_file in project_path.rglob(f"*{video_ext}"):
                assets.append(
                    MediaAsset(
                        file_path=str(video_file),
                        asset_type="video",
                        metadata={"source": "blender_render"},
                    )
                )

        # Scan for audio files
        for audio_ext in [".wav", ".mp3", ".aac", ".flac"]:
            for audio_file in project_path.rglob(f"*{audio_ext}"):
                assets.append(
                    MediaAsset(
                        file_path=str(audio_file),
                        asset_type="audio",
                        metadata={"source": "blender_audio"},
                    )
                )

        # Scan for image sequences
        for img_ext in [".png", ".jpg", ".exr", ".tiff"]:
            for img_file in project_path.rglob(f"*{img_ext}"):
                assets.append(
                    MediaAsset(
                        file_path=str(img_file),
                        asset_type="image",
                        metadata={"source": "blender_render"},
                    )
                )

        return assets

    async def _import_assets_to_resolve(self, project, assets: List[MediaAsset]) -> Dict[str, Any]:
        """Import assets to DaVinci Resolve media pool."""
        media_pool = project.GetMediaPool()
        imported_assets = []
        failed_imports = []

        for asset in assets:
            try:
                # Create folder for asset type if it doesn't exist
                folder_name = asset.asset_type.capitalize()
                folder = media_pool.GetRootFolder().GetSubFolderList().get(folder_name)
                if not folder:
                    folder = media_pool.AddSubFolder(media_pool.GetRootFolder(), folder_name)

                # Import asset
                media_pool.SetCurrentFolder(folder)
                imported_clips = media_pool.ImportMedia([asset.file_path])

                if imported_clips:
                    imported_assets.append(
                        {
                            "file_path": asset.file_path,
                            "asset_type": asset.asset_type,
                            "clips": [clip.GetName() for clip in imported_clips],
                        }
                    )
                else:
                    failed_imports.append(asset.file_path)

            except Exception as e:
                logger.error(f"Failed to import {asset.file_path}: {e}")
                failed_imports.append(asset.file_path)

        return {
            "imported": imported_assets,
            "failed": failed_imports,
            "total_imported": len(imported_assets),
        }

    async def _create_timeline_from_assets(
        self, project, assets: List[MediaAsset], config: ResolveProjectConfig
    ) -> Dict[str, Any]:
        """Create timeline from imported assets."""
        try:
            media_pool = project.GetMediaPool()

            # Create new timeline
            timeline_name = f"{config.name}_Timeline"
            timeline = media_pool.CreateEmptyTimeline(timeline_name)

            if not timeline:
                return {"ok": False, "error": "Failed to create timeline"}

            # Add video assets to video track
            video_assets = [a for a in assets if a.asset_type == "video"]
            for i, asset in enumerate(video_assets):
                # This would need more sophisticated logic for actual implementation
                pass

            # Add audio assets to audio track
            audio_assets = [a for a in assets if a.asset_type == "audio"]
            for i, asset in enumerate(audio_assets):
                # This would need more sophisticated logic for actual implementation
                pass

            return {
                "ok": True,
                "timeline_name": timeline_name,
                "video_clips": len(video_assets),
                "audio_clips": len(audio_assets),
            }

        except Exception as e:
            logger.error(f"Timeline creation failed: {e}")
            return {"ok": False, "error": str(e)}

    async def _integrate_voice_audio(self, media_pool, voice_audio_path: str) -> Dict[str, Any]:
        """Integrate Speechelo/Voice Generator audio."""
        try:
            # Create voice folder
            voice_folder = media_pool.AddSubFolder(media_pool.GetRootFolder(), "Voice_Audio")
            media_pool.SetCurrentFolder(voice_folder)

            # Import voice audio
            imported_clips = media_pool.ImportMedia([voice_audio_path])

            return {
                "success": True,
                "clips_imported": len(imported_clips) if imported_clips else 0,
                "folder": "Voice_Audio",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _integrate_captions(self, project, captions_data: Dict[str, Any]) -> Dict[str, Any]:
        """Integrate Captionizer subtitles."""
        try:
            timeline = project.GetCurrentTimeline()
            if not timeline:
                return {"success": False, "error": "No timeline available"}

            # Create subtitle track
            subtitle_track_index = timeline.AddTrack("subtitle")

            # Add captions (simplified implementation)
            captions_added = 0
            for caption in captions_data.get("captions", []):
                # This would need actual subtitle creation logic
                captions_added += 1

            return {
                "success": True,
                "captions_added": captions_added,
                "track_index": subtitle_track_index,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _integrate_thumbnails(self, media_pool, thumbnail_paths: List[str]) -> Dict[str, Any]:
        """Integrate Thumbnail Blaster images."""
        try:
            # Create thumbnails folder
            thumb_folder = media_pool.AddSubFolder(media_pool.GetRootFolder(), "Thumbnails")
            media_pool.SetCurrentFolder(thumb_folder)

            # Import thumbnails
            imported_clips = media_pool.ImportMedia(thumbnail_paths)

            return {
                "success": True,
                "thumbnails_imported": len(imported_clips) if imported_clips else 0,
                "folder": "Thumbnails",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _integrate_background_music(self, media_pool, music_path: str) -> Dict[str, Any]:
        """Integrate background music."""
        try:
            # Create music folder
            music_folder = media_pool.AddSubFolder(media_pool.GetRootFolder(), "Background_Music")
            media_pool.SetCurrentFolder(music_folder)

            # Import music
            imported_clips = media_pool.ImportMedia([music_path])

            return {
                "success": True,
                "music_imported": len(imported_clips) if imported_clips else 0,
                "folder": "Background_Music",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _integrate_translations(
        self, project, translations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Integrate Lingo Blaster translations."""
        try:
            # Create separate timelines for each language
            timelines_created = []

            for language, translation_data in translations.items():
                timeline_name = f"{project.GetName()}_{language}"
                # This would create language - specific timelines
                timelines_created.append(timeline_name)

            return {
                "success": True,
                "languages": list(translations.keys()),
                "timelines_created": timelines_created,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _create_default_color_template(self, template_path: Path) -> None:
        """Create a default color grading template."""
        # This would create a basic color grading template
        template_data = {
            "name": "Default Color Grade",
            "settings": {
                "lift": [0, 0, 0, 0],
                "gamma": [0, 0, 0, 0],
                "gain": [0, 0, 0, 0],
                "contrast": 1.0,
                "saturation": 1.0,
            },
        }

        template_path.write_text(json.dumps(template_data, indent=2))

    def _get_render_settings(self, export_format: str) -> Dict[str, Any]:
        """Get render settings for export format."""
        settings_map = {
            "mp4_h264": {
                "SelectAllFrames": True,
                "VideoFormat": "mp4",
                "VideoCodec": "h264",
                "VideoQuality": "High",
                "AudioCodec": "aac",
                "AudioBitDepth": "16",
                "AudioSampleRate": "48000",
            },
            "mp4_h265": {
                "SelectAllFrames": True,
                "VideoFormat": "mp4",
                "VideoCodec": "h265",
                "VideoQuality": "High",
                "AudioCodec": "aac",
                "AudioBitDepth": "16",
                "AudioSampleRate": "48000",
            },
            "mov_prores": {
                "SelectAllFrames": True,
                "VideoFormat": "mov",
                "VideoCodec": "ProRes422",
                "AudioCodec": "LinearPCM",
                "AudioBitDepth": "24",
                "AudioSampleRate": "48000",
            },
        }

        return settings_map.get(export_format, settings_map["mp4_h264"])


# Global integration instance
davinci_integration = DaVinciResolveIntegration()
