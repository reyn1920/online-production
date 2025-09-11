#!/usr / bin / env python3
"""
Channel Executor - Reads roadmap CSV and generates MP4 + PDF outputs
Integrates with Hollywood pipeline for complete content generation
"""

import asyncio
import csv
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.core.ci import cap_reel_minutes
from backend.core.secret_store_bridge import get_secret_store
from backend.integrations.video.ffmpeg_builder import make_slideshow_with_audio
from backend.pipelines.hollywood_pipeline import HollywoodPipeline
from backend.util.pdf_generator import PDFGenerator
from backend.util.video_utils import VideoProcessor

logger = logging.getLogger(__name__)


class ChannelExecutor:
    """Executes channel roadmap to produce MP4 videos and PDF products"""


    def __init__(self):
        self.secret_store = get_secret_store()
        self.hollywood_pipeline = HollywoodPipeline()
        self.pdf_generator = PDFGenerator()
        self.video_processor = VideoProcessor()

        # Setup output directories
        self.outputs_dir = Path("outputs")
        self.videos_dir = self.outputs_dir / "videos"
        self.pdfs_dir = self.outputs_dir / "pdfs"
        self.audio_dir = self.outputs_dir / "audio"

        for dir_path in [
            self.outputs_dir,
                self.videos_dir,
                self.pdfs_dir,
                self.audio_dir,
                ]:
            dir_path.mkdir(exist_ok = True)


    def load_roadmap(
        self, roadmap_path: str = "channel_roadmaps_10.csv"
    ) -> List[Dict[str, Any]]:
        """Load channel roadmap from CSV file"""
        roadmap = []

        try:
            with open(roadmap_path, "r", encoding="utf - 8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Clean and validate row data
                    channel_data = {
                        "channel_id": row.get("channel_id", "").strip(),
                            "channel_name": row.get("channel_name", "").strip(),
                            "niche": row.get("niche", "").strip(),
                            "content_type": row.get("content_type", "educational").strip(),
                            "target_audience": row.get("target_audience", "").strip(),
                            "video_length": int(row.get("video_length", 300)),  # seconds
                        "upload_frequency": row.get(
                            "upload_frequency", "weekly"
                        ).strip(),
                            "monetization_strategy": row.get(
                            "monetization_strategy", ""
                        ).strip(),
                            "voice_style": row.get("voice_style", "professional").strip(),
                            "avatar_type": row.get("avatar_type", "realistic").strip(),
                            "background_music": row.get(
                            "background_music", "ambient"
                        ).strip(),
                            "pdf_product_type": row.get(
                            "pdf_product_type", "ebook"
                        ).strip(),
                            "keywords": row.get("keywords", "").strip().split(","),
                            "description_template": row.get(
                            "description_template", ""
                        ).strip(),
                            }

                    if channel_data["channel_id"]:
                        roadmap.append(channel_data)

            logger.info(f"Loaded {len(roadmap)} channels from roadmap")
            return roadmap

        except FileNotFoundError:
            logger.error(f"Roadmap file not found: {roadmap_path}")
            return []
        except Exception as e:
            logger.error(f"Error loading roadmap: {e}")
            return []


    async def execute_channel(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single channel to produce video and PDF"""
        channel_id = channel_data["channel_id"]
        logger.info(f"Executing channel: {channel_id}")

        execution_result = {
            "channel_id": channel_id,
                "status": "started",
                "timestamp": datetime.now().isoformat(),
                "outputs": {},
                "errors": [],
                }

        try:
            # Generate content script based on channel data
            script_content = await self._generate_script(channel_data)
            if not script_content:
                raise Exception("Failed to generate script content")

            # Generate video using Hollywood pipeline
            video_result = await self._generate_video(channel_data, script_content)
            execution_result["outputs"]["video"] = video_result

            # Generate PDF product
            pdf_result = await self._generate_pdf_product(channel_data, script_content)
            execution_result["outputs"]["pdf"] = pdf_result

            # Generate thumbnail
            thumbnail_result = await self._generate_thumbnail(
                channel_data, video_result
            )
            execution_result["outputs"]["thumbnail"] = thumbnail_result

            execution_result["status"] = "completed"
            logger.info(f"Channel {channel_id} executed successfully")

        except Exception as e:
            error_msg = f"Channel execution failed: {str(e)}"
            logger.error(error_msg)
            execution_result["errors"].append(error_msg)
            execution_result["status"] = "failed"

        return execution_result


    async def _generate_script(self, channel_data: Dict[str, Any]) -> Optional[str]:
        """Generate video script based on channel data"""
        try:
            # Use channel niche and target audience to generate relevant content
            niche = channel_data["niche"]
            audience = channel_data["target_audience"]
            content_type = channel_data["content_type"]
            video_length = channel_data["video_length"]

            # Estimate word count (average 150 words per minute)
            target_words = int((video_length / 60) * 150)

            # Generate script using AI (placeholder for actual implementation)
            script_prompt = f"""
            Create a {content_type} video script for a {niche} channel.
            Target audience: {audience}
            Video length: {video_length} seconds
            Target word count: {target_words} words

            The script should be engaging, informative, and suitable for text - to - speech.
            Include clear sections for introduction, main content, and conclusion.
            """

            # For now, return a template script
            script_content = f"""
            Welcome to our {niche} channel! Today we're exploring an exciting topic that will help {audience}.

            [INTRODUCTION - 30 seconds]
            In this video, we'll cover the essential aspects of {niche} that every {audience} should know.

            [MAIN CONTENT - {video_length - 60} seconds]
            Let's dive into the key points that will make a real difference in your understanding of {niche}.

            [CONCLUSION - 30 seconds]
            Thank you for watching! Don't forget to subscribe for more {content_type} content about {niche}.
            """

            return script_content.strip()

        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return None


    async def _generate_video(
        self, channel_data: Dict[str, Any], script: str
    ) -> Dict[str, Any]:
        """Generate video using Hollywood pipeline"""
        channel_id = channel_data["channel_id"]

        # Prepare video generation parameters
        video_params = {
            "script": script,
                "voice_style": channel_data["voice_style"],
                "avatar_type": channel_data["avatar_type"],
                "background_music": channel_data["background_music"],
                "video_length": channel_data["video_length"],
                "output_path": str(
                self.videos_dir
                / f"{channel_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            ),
                }

        # Generate video using Hollywood pipeline
        video_result = await self.hollywood_pipeline.generate_video(video_params)

        return video_result


    async def _generate_pdf_product(
        self, channel_data: Dict[str, Any], script: str
    ) -> Dict[str, Any]:
        """Generate PDF product (ebook, lead magnet, etc.)"""
        channel_id = channel_data["channel_id"]
        product_type = channel_data["pdf_product_type"]

        # Prepare PDF content based on script and channel data
        pdf_content = {
            "title": f"{channel_data['channel_name']} - {product_type.title()}",
                "subtitle": f"Complete Guide to {channel_data['niche']}",
                "content": script,
                "niche": channel_data["niche"],
                "target_audience": channel_data["target_audience"],
                "keywords": channel_data["keywords"],
                }

        output_path = (
            self.pdfs_dir
            / f"{channel_id}_{product_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )

        # Generate PDF
        pdf_result = await self.pdf_generator.generate_product_pdf(
            pdf_content, str(output_path)
        )

        return pdf_result


    async def _generate_thumbnail(
        self, channel_data: Dict[str, Any], video_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate video thumbnail"""
        if not video_result.get("success") or not video_result.get("output_path"):
            return {"success": False, "error": "No video to generate thumbnail from"}

        video_path = video_result["output_path"]
        thumbnail_path = str(
            self.outputs_dir / "thumbnails" / f"{Path(video_path).stem}_thumb.jpg"
        )

        # Create thumbnails directory
        Path(thumbnail_path).parent.mkdir(exist_ok = True)

        try:
            # Extract frame at 10% of video duration for thumbnail
            cmd = [
                "ffmpeg",
                    "-i",
                    video_path,
                    "-ss",
                    "00:00:10",  # 10 seconds in
                "-vframes",
                    "1",
                    "-y",  # Overwrite output
                thumbnail_path,
                    ]

            result = subprocess.run(cmd, capture_output = True, text = True, timeout = 60)

            if result.returncode == 0 and Path(thumbnail_path).exists():
                return {
                    "success": True,
                        "thumbnail_path": thumbnail_path,
                        "size": Path(thumbnail_path).stat().st_size,
                        }
            else:
                return {"success": False, "error": f"FFmpeg failed: {result.stderr}"}

        except Exception as e:
            return {"success": False, "error": f"Thumbnail generation failed: {str(e)}"}


    async def execute_roadmap(
        self,
            roadmap_path: str = "channel_roadmaps_10.csv",
            channel_filter: Optional[str] = None,
            ) -> Dict[str, Any]:
        """Execute entire roadmap or specific channel"""
        roadmap = self.load_roadmap(roadmap_path)

        if not roadmap:
            return {
                "success": False,
                    "error": "No channels loaded from roadmap",
                    "results": [],
                    }

        # Filter channels if specified
        if channel_filter:
            roadmap = [ch for ch in roadmap if channel_filter in ch["channel_id"]]

        if not roadmap:
            return {
                "success": False,
                    "error": f"No channels match filter: {channel_filter}",
                    "results": [],
                    }

        logger.info(f"Executing {len(roadmap)} channels")

        # Execute channels
        results = []
        for channel_data in roadmap:
            try:
                result = await self.execute_channel(channel_data)
                results.append(result)

                # Add delay between channels to prevent resource exhaustion
                await asyncio.sleep(2)

            except Exception as e:
                error_result = {
                    "channel_id": channel_data.get("channel_id", "unknown"),
                        "status": "failed",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                        }
                results.append(error_result)

        # Summary
        successful = len([r for r in results if r["status"] == "completed"])
        failed = len([r for r in results if r["status"] == "failed"])

        return {
            "success": successful > 0,
                "total_channels": len(roadmap),
                "successful": successful,
                "failed": failed,
                "results": results,
                "timestamp": datetime.now().isoformat(),
                }


    def run_channel_once(self, channel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper for executing a single channel"""
        return asyncio.run(self.execute_channel(channel_data))


    def get_execution_status(self) -> Dict[str, Any]:
        """Get current execution status and output summary"""
        status = {
            "videos_count": len(list(self.videos_dir.glob("*.mp4"))),
                "pdfs_count": len(list(self.pdfs_dir.glob("*.pdf"))),
                "audio_count": len(list(self.audio_dir.glob("*.wav"))),
                "total_video_size": sum(
                f.stat().st_size for f in self.videos_dir.glob("*.mp4")
            ),
                "total_pdf_size": sum(
                f.stat().st_size for f in self.pdfs_dir.glob("*.pdf")
            ),
                "latest_outputs": {
                "videos": [
                    f.name
                    for f in sorted(
                        self.videos_dir.glob("*.mp4"),
                            key = lambda x: x.stat().st_mtime,
                            reverse = True,
                            )[:5]
                ],
                    "pdfs": [
                    f.name
                    for f in sorted(
                        self.pdfs_dir.glob("*.pdf"),
                            key = lambda x: x.stat().st_mtime,
                            reverse = True,
                            )[:5]
                ],
                    },
                }

        return status


def run_channel_once(
    csv_path: str, video_dir: str = "outputs / videos", pdf_dir: str = "outputs / pdfs"
) -> Dict[str, Any]:
    """Synchronous function to run a single channel from CSV roadmap"""
    try:
        executor = ChannelExecutor()
        roadmap = executor.load_roadmap(csv_path)

        if not roadmap:
            return {
                "status": "error",
                    "error": "No channels found in roadmap",
                    "csv_path": csv_path,
                    }

        # Execute first channel from roadmap
        channel_data = roadmap[0]
        result = asyncio.run(executor.execute_channel(channel_data))

        return {
            "status": "success",
                "channel_executed": channel_data.get("channel_name", "Unknown"),
                "video_dir": video_dir,
                "pdf_dir": pdf_dir,
                "result": result,
                }

    except Exception as e:
        return {"status": "error", "error": str(e), "csv_path": csv_path}

if __name__ == "__main__":
    # Test channel executor


        async def test_executor():
        executor = ChannelExecutor()

        # Test with a single channel
        test_channel = {
            "channel_id": "test_channel_001",
                "channel_name": "Test Educational Channel",
                "niche": "technology",
                "content_type": "educational",
                "target_audience": "tech enthusiasts",
                "video_length": 180,
                "voice_style": "professional",
                "avatar_type": "realistic",
                "background_music": "ambient",
                "pdf_product_type": "ebook",
                "keywords": ["technology", "innovation", "future"],
                }

        result = await executor.execute_channel(test_channel)
        print(f"Execution result: {json.dumps(result, indent = 2)}")

        status = executor.get_execution_status()
        print(f"Status: {json.dumps(status, indent = 2)}")

    asyncio.run(test_executor())


def capability_reel():
    """Generate capability reel with CI - aware timing"""
    # Build lines for the capability reel
    lines = [
        "TRAE.AI System Capabilities",
            "Multi - Agent Content Generation",
            "Advanced Video Processing",
            "Real - time Dashboard Monitoring",
            "Secure Secret Management",
            "Automated Channel Execution",
            "PDF Product Generation",
            "Hollywood Pipeline Integration",
            "Compliance & Security Scanning",
            "Operational Excellence",
            ]

    out_dir = os.path.join("assets", "releases", f"CapabilityReel_{int(time.time())}")
    reel = make_slideshow_with_audio(lines, out_dir, total_minutes = cap_reel_minutes(20))
    return {"out_dir": out_dir, "mp4": reel, "lines": len(lines)}
