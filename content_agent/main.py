#!/usr/bin/env python3
"""
TRAE.AI Content Agent - Hollywood-Level Creative Pipeline
Handles video creation, TTS, avatar generation, and content automation
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import requests
import feedparser
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger
from dotenv import load_dotenv
import openai
from TTS.api import TTS
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import ffmpeg
try:
    from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
except ImportError:
    logger.warning("MoviePy not available - video editing features disabled")
    VideoFileClip = AudioFileClip = CompositeVideoClip = TextClip = None

# Load environment variables
load_dotenv()

class ContentConfig:
    """Configuration for the content agent"""
    def __init__(self):
        self.use_mock = os.getenv('USE_MOCK', 'false').lower() == 'true'
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.coqui_api_key = os.getenv('COQUI_API_KEY')
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        
        # Use relative paths that work in any environment
        base_dir = Path.cwd()
        self.output_dir = base_dir / 'output'
        self.data_dir = base_dir / 'data'
        self.log_level = os.getenv('LOG_LEVEL', 'INFO')
        
        # Ensure directories exist
        self.output_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

class ContentRequest(BaseModel):
    """Request model for content creation"""
    type: str = 'video'
    topic: str
    format: str = 'educational'
    duration: int = 300  # seconds
    style: Optional[str] = 'professional'
    voice: Optional[str] = 'default'
    resolution: Optional[str] = '1920x1080'

class ContentResponse(BaseModel):
    """Response model for content creation"""
    content_id: str
    type: str
    title: str
    description: str
    transcript: str
    file_path: str
    duration: float
    created_at: datetime
    metadata: Dict[str, Any]

class NewsWatcher:
    """Watches RSS feeds for breaking news and trending topics"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
        self.rss_feeds = [
            'https://feeds.bbci.co.uk/news/rss.xml',
            'https://rss.cnn.com/rss/edition.rss',
            'https://feeds.reuters.com/reuters/topNews',
            'https://feeds.npr.org/1001/rss.xml',
            'https://techcrunch.com/feed/',
            'https://feeds.ycombinator.com/hackernews'
        ]
    
    def get_trending_topics(self, limit: int = 10) -> List[Dict[str, str]]:
        """Get trending topics from RSS feeds"""
        topics = []
        
        for feed_url in self.rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:3]:  # Top 3 from each feed
                    topics.append({
                        'title': entry.title,
                        'summary': entry.get('summary', ''),
                        'link': entry.link,
                        'published': entry.get('published', ''),
                        'source': feed.feed.get('title', 'Unknown')
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch from {feed_url}: {e}")
        
        # Sort by recency and return top items
        return topics[:limit]

class ScriptGenerator:
    """Generates video scripts using OpenAI"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
        if config.openai_api_key:
            openai.api_key = config.openai_api_key
    
    async def generate_script(self, topic: str, duration: int, style: str = 'educational') -> Dict[str, str]:
        """Generate a video script for the given topic"""
        if self.config.use_mock:
            return self._generate_mock_script(topic, duration)
        
        try:
            prompt = f"""
Create a compelling {duration}-second video script about: {topic}

Style: {style}
Format: Educational and engaging
Target: General audience interested in current events and technology

Requirements:
- Hook viewers in the first 5 seconds
- Present information clearly and concisely
- Include surprising facts or insights
- End with a thought-provoking question or call-to-action
- Write in a conversational, accessible tone
- Include natural pauses for emphasis

Return JSON with:
- title: Catchy video title
- description: Brief description for social media
- script: Full narration script with timing cues
- key_points: List of main points covered
- tags: Relevant hashtags/keywords
"""
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional video script writer specializing in educational content that goes viral."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                script_data = json.loads(content)
                return script_data
            except json.JSONDecodeError:
                # Fallback if not valid JSON
                return {
                    'title': f"Breaking: {topic}",
                    'description': f"Latest insights on {topic}",
                    'script': content,
                    'key_points': [topic],
                    'tags': ['#news', '#trending', '#education']
                }
                
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return self._generate_mock_script(topic, duration)
    
    def _generate_mock_script(self, topic: str, duration: int) -> Dict[str, str]:
        """Generate a mock script for testing"""
        return {
            'title': f"Breaking Analysis: {topic}",
            'description': f"Deep dive into {topic} and its implications",
            'script': f"Welcome to today's analysis of {topic}. This is a fascinating development that could change everything. Let me break down what this means for you and why it matters. [Pause] The key insight here is that {topic} represents a significant shift in how we think about technology and society. What do you think about this development? Let me know in the comments below.",
            'key_points': [topic, 'analysis', 'implications'],
            'tags': ['#breaking', '#analysis', '#tech']
        }

class TTSEngine:
    """Text-to-Speech engine using Coqui TTS"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
        self.tts = None
        self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize the TTS engine"""
        try:
            # Use Coqui TTS with a high-quality model
            self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
            logger.info("✅ TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.tts = None
    
    async def generate_audio(self, text: str, output_path: str, voice: str = 'default') -> str:
        """Generate audio from text"""
        if self.config.use_mock or not self.tts:
            return self._generate_mock_audio(text, output_path)
        
        try:
            # Generate audio using Coqui TTS
            self.tts.tts_to_file(text=text, file_path=output_path)
            logger.info(f"✅ Audio generated: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return self._generate_mock_audio(text, output_path)
    
    def _generate_mock_audio(self, text: str, output_path: str) -> str:
        """Generate mock audio file for testing"""
        # Create a silent audio file for testing
        duration = len(text.split()) * 0.5  # Rough estimate: 0.5 seconds per word
        
        # Generate silent audio using ffmpeg
        try:
            (
                ffmpeg
                .input('anullsrc=channel_layout=stereo:sample_rate=44100', f='lavfi', t=duration)
                .output(output_path)
                .overwrite_output()
                .run(quiet=True)
            )
            logger.info(f"✅ Mock audio generated: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Mock audio generation failed: {e}")
            return output_path

class AvatarGenerator:
    """Generates 3D avatars and visual content"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
    
    def create_avatar_video(self, script_data: Dict, audio_path: str, output_path: str) -> str:
        """Create avatar video with synchronized audio"""
        try:
            # For now, create a simple video with text overlay
            # In production, this would integrate with MakeHuman/Daz3D/Blender
            return self._create_text_video(script_data, audio_path, output_path)
            
        except Exception as e:
            logger.error(f"Avatar video creation failed: {e}")
            return self._create_text_video(script_data, audio_path, output_path)
    
    def _create_text_video(self, script_data: Dict, audio_path: str, output_path: str) -> str:
        """Create a video with text overlay and background"""
        try:
            # Get audio duration
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create background
            background = self._create_background(1920, 1080, duration)
            
            # Create title text
            title_clip = TextClip(
                script_data.get('title', 'TRAE.AI Content'),
                fontsize=72,
                color='white',
                font='Arial-Bold'
            ).set_position('center').set_duration(duration)
            
            # Create subtitle text (key points)
            key_points = script_data.get('key_points', [])
            subtitle_text = ' • '.join(key_points[:3]) if key_points else 'AI-Generated Content'
            
            subtitle_clip = TextClip(
                subtitle_text,
                fontsize=36,
                color='lightblue',
                font='Arial'
            ).set_position(('center', 'bottom')).set_duration(duration)
            
            # Composite video
            final_video = CompositeVideoClip([
                background,
                title_clip,
                subtitle_clip
            ]).set_audio(audio_clip)
            
            # Write video file
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Clean up
            audio_clip.close()
            final_video.close()
            
            logger.info(f"✅ Video created: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Text video creation failed: {e}")
            # Create minimal video file
            return self._create_minimal_video(output_path, 10)
    
    def _create_background(self, width: int, height: int, duration: float) -> VideoFileClip:
        """Create animated background"""
        # Create a gradient background
        def make_frame(t):
            # Animated gradient
            color1 = np.array([20, 30, 60])  # Dark blue
            color2 = np.array([60, 30, 100])  # Purple
            
            # Create gradient that shifts over time
            shift = int(t * 10) % height
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            for y in range(height):
                ratio = (y + shift) % height / height
                color = color1 * (1 - ratio) + color2 * ratio
                frame[y, :] = color
            
            return frame
        
        try:
            from moviepy.editor import VideoClip
        except ImportError:
            logger.warning("MoviePy VideoClip not available")
            VideoClip = None
            return None
        return VideoClip(make_frame, duration=duration)
    
    def _create_minimal_video(self, output_path: str, duration: int) -> str:
        """Create minimal video file for testing"""
        try:
            (
                ffmpeg
                .input('color=c=blue:size=1920x1080:duration=' + str(duration), f='lavfi')
                .output(output_path, vcodec='libx264', pix_fmt='yuv420p')
                .overwrite_output()
                .run(quiet=True)
            )
            return output_path
        except Exception as e:
            logger.error(f"Minimal video creation failed: {e}")
            return output_path

class ContentAgent:
    """Main content agent that orchestrates content creation"""
    
    def __init__(self, config: ContentConfig):
        self.config = config
        self.app = FastAPI(title="TRAE.AI Content Agent", version="1.0.0")
        self.news_watcher = NewsWatcher(config)
        self.script_generator = ScriptGenerator(config)
        self.tts_engine = TTSEngine(config)
        self.avatar_generator = AvatarGenerator(config)
        self.setup_logging()
        self.setup_routes()
    
    def setup_logging(self):
        """Configure logging"""
        logger.remove()
        logger.add(
            sys.stdout,
            level=self.config.log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        logger.add(
            "/app/logs/content_agent.log",
            rotation="1 day",
            retention="30 days",
            level=self.config.log_level
        )
    
    def setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "tts_available": self.tts_engine.tts is not None,
                "openai_configured": bool(self.config.openai_api_key)
            }
        
        @self.app.get("/trending")
        async def get_trending_topics():
            """Get trending topics from news feeds"""
            topics = self.news_watcher.get_trending_topics()
            return {"topics": topics, "count": len(topics)}
        
        @self.app.post("/create", response_model=ContentResponse)
        async def create_content(request: ContentRequest, background_tasks: BackgroundTasks):
            """Create content based on request"""
            try:
                content_id = f"content_{int(datetime.now().timestamp())}"
                logger.info(f"🎬 Creating content: {content_id}")
                
                # Generate script
                script_data = await self.script_generator.generate_script(
                    request.topic, request.duration, request.format
                )
                
                # Generate audio
                audio_path = str(self.config.output_dir / f"{content_id}_audio.wav")
                await self.tts_engine.generate_audio(
                    script_data['script'], audio_path, request.voice
                )
                
                # Generate video
                video_path = str(self.config.output_dir / f"{content_id}_video.mp4")
                self.avatar_generator.create_avatar_video(
                    script_data, audio_path, video_path
                )
                
                # Get video duration
                try:
                    video_clip = VideoFileClip(video_path)
                    actual_duration = video_clip.duration
                    video_clip.close()
                except:
                    actual_duration = request.duration
                
                response = ContentResponse(
                    content_id=content_id,
                    type=request.type,
                    title=script_data['title'],
                    description=script_data['description'],
                    transcript=script_data['script'],
                    file_path=video_path,
                    duration=actual_duration,
                    created_at=datetime.now(),
                    metadata={
                        'audio_path': audio_path,
                        'key_points': script_data.get('key_points', []),
                        'tags': script_data.get('tags', []),
                        'style': request.style,
                        'voice': request.voice,
                        'resolution': request.resolution
                    }
                )
                
                logger.info(f"✅ Content created successfully: {content_id}")
                return response
                
            except Exception as e:
                logger.error(f"❌ Content creation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/content/{content_id}")
        async def get_content(content_id: str):
            """Get content by ID"""
            video_path = self.config.output_dir / f"{content_id}_video.mp4"
            if video_path.exists():
                return {
                    "content_id": content_id,
                    "file_path": str(video_path),
                    "exists": True,
                    "size_mb": video_path.stat().st_size / (1024 * 1024)
                }
            else:
                raise HTTPException(status_code=404, detail="Content not found")
    
    async def start_server(self):
        """Start the content agent server"""
        import uvicorn
        
        logger.info("🎬 Starting TRAE.AI Content Agent")
        logger.info(f"📊 Mock mode: {self.config.use_mock}")
        logger.info(f"🎤 TTS available: {self.tts_engine.tts is not None}")
        
        config = uvicorn.Config(
            app=self.app,
            host="0.0.0.0",
            port=8001,
            log_level=self.config.log_level.lower()
        )
        server = uvicorn.Server(config)
        await server.serve()

async def main():
    """Main entry point"""
    config = ContentConfig()
    agent = ContentAgent(config)
    await agent.start_server()

if __name__ == "__main__":
    asyncio.run(main())