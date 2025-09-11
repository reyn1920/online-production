#!/usr/bin/env python3
"""
DaVinci Resolve Voice Cloning Integration
Provides voice synthesis capabilities for DaVinci Resolve workflows
Supports sample-based voice generation and batch processing
"""

import os
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import subprocess
import tempfile

# Import our voice cloning system
from davinci_voice_cloning import DaVinciVoiceCloner, VoiceSample

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DaVinciResolveVoiceIntegration:
    """Integration layer for DaVinci Resolve voice synthesis"""
    
    def __init__(self, project_name: str = "VoiceProject"):
        self.project_name = project_name
        self.voice_cloner = DaVinciVoiceCloner()
        self.output_dir = Path("output/davinci_resolve")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # DaVinci Resolve compatible formats
        self.supported_formats = {
            "wav": {"codec": "pcm_s24le", "sample_rate": 48000},
            "aiff": {"codec": "pcm_s24be", "sample_rate": 48000},
            "mp3": {"codec": "mp3", "bitrate": "320k"}
        }
        
        logger.info(f"🎬 DaVinci Resolve Voice Integration initialized for project: {project_name}")
    
    def create_voice_project(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a voice project from script data"""
        
        project_info = {
            "project_name": self.project_name,
            "created_at": datetime.now().isoformat(),
            "script_data": script_data,
            "voice_tracks": [],
            "total_duration": 0,
            "output_format": "wav"
        }
        
        logger.info(f"📝 Created voice project: {self.project_name}")
        return project_info
    
    async def generate_voice_track(
        self,
        text: str,
        voice_name: str,
        track_name: str,
        output_format: str = "wav",
        **voice_params
    ) -> Dict[str, Any]:
        """Generate a single voice track for DaVinci Resolve"""
        
        try:
            # Clone voice using our system
            result = await self.voice_cloner.clone_voice(
                text=text,
                voice_sample_name=voice_name,
                engine_name="local",
                **voice_params
            )
            
            if not result["success"]:
                return {"success": False, "error": result.get("error", "Voice cloning failed")}
            
            # Convert to DaVinci Resolve compatible format
            source_path = result["output_path"]
            target_filename = f"{track_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{output_format}"
            target_path = str(self.output_dir / target_filename)
            
            conversion_result = await self._convert_audio_format(
                source_path, target_path, output_format
            )
            
            if conversion_result["success"]:
                track_info = {
                    "track_name": track_name,
                    "text": text,
                    "voice_name": voice_name,
                    "file_path": target_path,
                    "format": output_format,
                    "duration": result.get("duration", 0),
                    "metadata": result.get("metadata", {}),
                    "davinci_compatible": True
                }
                
                logger.info(f"🎤 Generated voice track: {track_name} ({output_format})")
                return {"success": True, "track_info": track_info}
            else:
                return {"success": False, "error": conversion_result.get("error", "Format conversion failed")}
                
        except Exception as e:
            logger.error(f"❌ Voice track generation failed: {e}")
            return {"success": False, "error": str(e)}
    
    async def _convert_audio_format(
        self,
        source_path: str,
        target_path: str,
        target_format: str
    ) -> Dict[str, Any]:
        """Convert audio to DaVinci Resolve compatible format"""
        
        try:
            format_config = self.supported_formats.get(target_format, self.supported_formats["wav"])
            
            # Build ffmpeg command
            cmd = [
                "ffmpeg", "-i", source_path,
                "-acodec", format_config["codec"],
                "-ar", str(format_config["sample_rate"]),
                "-y", target_path
            ]
            
            # Add bitrate for MP3
            if target_format == "mp3":
                cmd.extend(["-b:a", format_config["bitrate"]])
            
            # Execute conversion
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                logger.info(f"✅ Audio converted to {target_format}: {target_path}")
                return {"success": True, "output_path": target_path}
            else:
                error_msg = stderr.decode() if stderr else "Unknown conversion error"
                logger.error(f"❌ Audio conversion failed: {error_msg}")
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            logger.error(f"❌ Audio conversion exception: {e}")
            return {"success": False, "error": str(e)}
    
    async def generate_script_voices(
        self,
        script: List[Dict[str, str]],
        output_format: str = "wav"
    ) -> Dict[str, Any]:
        """Generate voices for an entire script"""
        
        logger.info(f"🎬 Generating voices for script with {len(script)} segments")
        
        project_info = self.create_voice_project({"script": script})
        voice_tracks = []
        failed_tracks = []
        
        for i, segment in enumerate(script):
            track_name = segment.get("track_name", f"track_{i+1:03d}")
            text = segment.get("text", "")
            voice_name = segment.get("voice", "narrator")
            
            if not text.strip():
                logger.warning(f"⚠️ Skipping empty text for track: {track_name}")
                continue
            
            try:
                result = await self.generate_voice_track(
                    text=text,
                    voice_name=voice_name,
                    track_name=track_name,
                    output_format=output_format
                )
                
                if result["success"]:
                    voice_tracks.append(result["track_info"])
                else:
                    failed_tracks.append({
                        "track_name": track_name,
                        "error": result.get("error", "Unknown error")
                    })
                    
            except Exception as e:
                logger.error(f"❌ Failed to generate track {track_name}: {e}")
                failed_tracks.append({
                    "track_name": track_name,
                    "error": str(e)
                })
        
        # Update project info
        project_info["voice_tracks"] = voice_tracks
        project_info["failed_tracks"] = failed_tracks
        project_info["total_duration"] = sum(track.get("duration", 0) for track in voice_tracks)
        project_info["success_rate"] = len(voice_tracks) / len(script) if script else 0
        
        # Save project file
        project_file = self.output_dir / f"{self.project_name}_project.json"
        with open(project_file, 'w') as f:
            json.dump(project_info, f, indent=2)
        
        logger.info(f"✅ Script voice generation completed: {len(voice_tracks)}/{len(script)} successful")
        logger.info(f"📁 Project saved: {project_file}")
        
        return project_info
    
    def create_davinci_resolve_xml(self, project_info: Dict[str, Any]) -> str:
        """Create DaVinci Resolve compatible XML timeline"""
        
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<xmeml version="4">
  <project>
    <name>{project_info["project_name"]}</name>
    <children>
      <sequence>
        <name>{project_info["project_name"]}_Timeline</name>
        <rate>
          <timebase>25</timebase>
          <ntsc>FALSE</ntsc>
        </rate>
        <media>
          <audio>
'''
        
        # Add audio tracks
        for i, track in enumerate(project_info.get("voice_tracks", [])):
            xml_content += f'''            <track>
              <clipitem id="{track["track_name"]}">
                <name>{track["track_name"]}</name>
                <file id="{track["track_name"]}_file">
                  <name>{track["track_name"]}</name>
                  <pathurl>file://{track["file_path"]}</pathurl>
                  <rate>
                    <timebase>25</timebase>
                    <ntsc>FALSE</ntsc>
                  </rate>
                  <media>
                    <audio>
                      <samplecharacteristics>
                        <depth>24</depth>
                        <samplerate>48000</samplerate>
                      </samplecharacteristics>
                    </audio>
                  </media>
                </file>
                <start>0</start>
                <end>{int(track.get("duration", 5) * 25)}</end>
                <in>0</in>
                <out>{int(track.get("duration", 5) * 25)}</out>
              </clipitem>
            </track>
'''
        
        xml_content += '''          </audio>
        </media>
      </sequence>
    </children>
  </project>
</xmeml>'''
        
        # Save XML file
        xml_file = self.output_dir / f"{project_info['project_name']}_timeline.xml"
        with open(xml_file, 'w') as f:
            f.write(xml_content)
        
        logger.info(f"📄 DaVinci Resolve XML created: {xml_file}")
        return str(xml_file)
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice samples"""
        return list(self.voice_cloner.get_voice_samples().keys())
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get summary of the integration capabilities"""
        return {
            "project_name": self.project_name,
            "available_voices": self.get_available_voices(),
            "supported_formats": list(self.supported_formats.keys()),
            "available_engines": self.voice_cloner.get_available_engines(),
            "output_directory": str(self.output_dir)
        }

async def demo_davinci_integration():
    """Demonstrate DaVinci Resolve integration"""
    
    print("\n🎬 DaVinci Resolve Voice Integration Demo")
    print("=" * 60)
    
    # Initialize integration
    integration = DaVinciResolveVoiceIntegration("DemoProject")
    
    # Show capabilities
    summary = integration.get_project_summary()
    print(f"\n📊 Integration Summary:")
    print(f"Available voices: {summary['available_voices']}")
    print(f"Supported formats: {summary['supported_formats']}")
    print(f"Available engines: {summary['available_engines']}")
    
    # Demo script
    demo_script = [
        {
            "track_name": "intro",
            "text": "Welcome to our DaVinci Resolve voice integration demonstration.",
            "voice": "narrator"
        },
        {
            "track_name": "explanation",
            "text": "This system allows you to generate professional voice tracks from text.",
            "voice": "assistant"
        },
        {
            "track_name": "conclusion",
            "text": "Thank you for watching this demonstration of our voice cloning technology.",
            "voice": "presenter"
        }
    ]
    
    print(f"\n🎤 Generating voices for {len(demo_script)} script segments...")
    
    # Generate voices for script
    project_result = await integration.generate_script_voices(
        script=demo_script,
        output_format="wav"
    )
    
    print(f"\n✅ Voice generation completed:")
    print(f"Success rate: {project_result['success_rate']:.1%}")
    print(f"Total duration: {project_result['total_duration']:.1f} seconds")
    print(f"Generated tracks: {len(project_result['voice_tracks'])}")
    
    if project_result.get("failed_tracks"):
        print(f"Failed tracks: {len(project_result['failed_tracks'])}")
    
    # Create DaVinci Resolve XML
    xml_file = integration.create_davinci_resolve_xml(project_result)
    print(f"\n📄 DaVinci Resolve XML timeline created: {xml_file}")
    
    # Show generated files
    print(f"\n📁 Generated files:")
    for track in project_result["voice_tracks"]:
        print(f"  - {track['track_name']}: {track['file_path']}")
    
    print(f"\n🎉 DaVinci Resolve integration demo completed!")
    print(f"\n💡 Usage Instructions:")
    print(f"1. Import the generated audio files into DaVinci Resolve")
    print(f"2. Use the XML timeline file to automatically arrange tracks")
    print(f"3. Sync with your video content and adjust timing as needed")
    print(f"4. Export your final video with professional voice narration")

if __name__ == "__main__":
    asyncio.run(demo_davinci_integration())