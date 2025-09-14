#!/usr/bin/env python3
"""
TRAE.AI Content Agent - Production Implementation
AI - powered content creation and management service

This service handles:
- Multi - format content generation (articles, videos, podcasts, social media)
- AI - powered writing with GPT - 4, Claude, and Gemini
- Video creation with voiceovers and animations
- Image generation and processing
- SEO optimization and keyword research
- Content scheduling and publishing
- Performance analytics and optimization
"""

import asyncio
import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
import openai
import redis
from anthropic import Anthropic
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from loguru import logger
from PIL import Image, ImageDraw, ImageFont
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

try:
    import moviepy.editor as mp

except ImportError:
    logger.warning("MoviePy not available - video editing features disabled")
    mp = None

import google.generativeai as genai
import spacy
from gtts import gTTS
from textstat import flesch_kincaid_grade, flesch_reading_ease

# from elevenlabs import generate, Voice  # Commented out due to Python 3.13 compatibility
try:
    from elevenlabs import Voice, generate

except ImportError:
    logger.warning("ElevenLabs not available, using gTTS for audio generation")
    generate = None
    Voice = None

import tweepy
from facebook import GraphAPI
from linkedin_api import Linkedin
from wordpress_xmlrpc import Client as WordPressClient
from wordpress_xmlrpc.compat import xmlrpc_client
from wordpress_xmlrpc.methods import posts

try:
    import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
    from stability_sdk import client

except ImportError:
    logger.warning("Stability SDK not available - Stability AI image generation disabled")
    client = None
    generation = None

from concurrent.futures import ThreadPoolExecutor

import aiofiles
import nltk
from cachetools import TTLCache
from nltk.sentiment import SentimentIntensityAnalyzer
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from tenacity import retry, stop_after_attempt, wait_exponential
from textblob import TextBlob

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY - MM - DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level="INFO",
)
logger.add("logs/content_agent.log", rotation="100 MB", retention="30 days", level="DEBUG")

# Configuration


class Config:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./content_agent.db")

    # Redis
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # AI APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

    # Social Media APIs
    TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
    TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
    TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
    TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
    FACEBOOK_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
    LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

    # Content Management
    WORDPRESS_URL = os.getenv("WORDPRESS_URL")
    WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
    WORDPRESS_PASSWORD = os.getenv("WORDPRESS_PASSWORD")

    # Email Marketing
    MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

    # System
    USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "info")

    # Performance
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "10"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", "3600"))
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))


config = Config()

# Database Models
Base = declarative_base()


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    title = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # article, video, podcast, social_post, ebook
    content = Column(Text)
    item_metadata = Column(JSON)  # Renamed from 'metadata' to avoid SQLAlchemy conflict
    status = Column(String, default="draft")  # draft, published, scheduled, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)
    author = Column(String)
    tags = Column(JSON)
    seo_score = Column(Float)
    engagement_metrics = Column(JSON)
    ai_model_used = Column(String)
    generation_params = Column(JSON)
    file_paths = Column(JSON)
    publishing_channels = Column(JSON)


class ContentTemplate(Base):
    __tablename__ = "content_templates"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    name = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    template = Column(Text, nullable=False)
    variables = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)


class ContentSchedule(Base):
    __tablename__ = "content_schedule"

    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    content_id = Column(String, nullable=False)
    channel = Column(String, nullable=False)
    scheduled_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, published, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    published_at = Column(DateTime)
    error_message = Column(Text)


# Pydantic Models


class ContentRequest(BaseModel):
    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Type of content to generate")
    topic: str = Field(..., description="Main topic or subject")
    target_audience: str = Field(default="general", description="Target audience")
    tone: str = Field(default="professional", description="Content tone")
    length: str = Field(default="medium", description="Content length")
    keywords: List[str] = Field(default=[], description="SEO keywords")
    ai_model: str = Field(default="gpt - 4", description="AI model to use")
    include_images: bool = Field(default=True, description="Include generated images")
    include_video: bool = Field(default=False, description="Generate video content")
    include_audio: bool = Field(default=False, description="Generate audio/voiceover")
    publishing_channels: List[str] = Field(default=[], description="Channels to publish to")
    schedule_time: Optional[datetime] = Field(None, description="Schedule publication time")
    template_id: Optional[str] = Field(None, description="Template to use")
    custom_instructions: Optional[str] = Field(None, description="Additional instructions")


class ContentResponse(BaseModel):
    id: str
    title: str
    content_type: str
    content: str
    item_metadata: Dict[str, Any]  # Renamed from 'metadata' to match database column
    status: str
    created_at: datetime
    file_paths: Dict[str, str]
    seo_score: float
    estimated_engagement: Dict[str, float]


class BulkContentRequest(BaseModel):
    topics: List[str] = Field(..., description="List of topics to generate content for")
    content_type: str = Field(..., description="Type of content to generate")
    base_template: Optional[str] = Field(None, description="Base template for all content")
    common_settings: ContentRequest = Field(..., description="Common settings for all content")


class ContentAnalytics(BaseModel):
    total_content: int
    content_by_type: Dict[str, int]
    engagement_metrics: Dict[str, float]
    top_performing_content: List[Dict[str, Any]]
    seo_performance: Dict[str, float]
    ai_model_performance: Dict[str, Dict[str, float]]
    publishing_success_rate: Dict[str, float]


# Metrics
content_generation_counter = Counter(
    "content_generation_total", "Total content generated", ["content_type", "ai_model"]
)
content_generation_duration = Histogram(
    "content_generation_duration_seconds",
    "Content generation duration",
    ["content_type"],
)
api_request_counter = Counter("api_requests_total", "Total API requests", ["endpoint", "method"])
api_request_duration = Histogram(
    "api_request_duration_seconds", "API request duration", ["endpoint"]
)
error_counter = Counter("errors_total", "Total errors", ["error_type"])
active_tasks_gauge = Gauge("active_tasks", "Number of active tasks")
cache_hit_counter = Counter("cache_hits_total", "Cache hits")
cache_miss_counter = Counter("cache_misses_total", "Cache misses")

# Initialize services
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
redis_client = redis.from_url(config.REDIS_URL)
cache = TTLCache(maxsize=1000, ttl=config.CACHE_TTL)
scheduler = AsyncIOScheduler()

# AI Clients
if config.OPENAI_API_KEY:
    openai.api_key = config.OPENAI_API_KEY
    openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
else:
    openai_client = None

if config.ANTHROPIC_API_KEY:
    anthropic_client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
else:
    anthropic_client = None

if config.GOOGLE_AI_API_KEY:
    genai.configure(api_key=config.GOOGLE_AI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini - pro")
else:
    gemini_model = None

if config.STABILITY_API_KEY:
    stability_api = client.StabilityInferenceAPI(
        host="grpc.stability.ai:443",
        key=config.STABILITY_API_KEY,
        verbose=True,
    )
else:
    stability_api = None

# Load NLP models
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    logger.warning("spaCy model not found. Some NLP features will be limited.")
    nlp = None

try:
    nltk.download("vader_lexicon", quiet=True)
    sentiment_analyzer = SentimentIntensityAnalyzer()
except Exception:
    logger.warning("NLTK sentiment analyzer not available.")
    sentiment_analyzer = None

# Content Generation Engine


class ContentGenerator:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=config.MAX_WORKERS)
        self.embedding_model = SentenceTransformer("all - MiniLM - L6 - v2")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate_text_content(self, request: ContentRequest) -> str:
        """Generate text content using AI models"""
        try:
            prompt = self._build_content_prompt(request)

            if request.ai_model.startswith("gpt") and openai_client:
                return await self._generate_with_openai(prompt, request)
            elif request.ai_model.startswith("claude") and anthropic_client:
                return await self._generate_with_anthropic(prompt, request)
            elif request.ai_model.startswith("gemini") and gemini_model:
                return await self._generate_with_gemini(prompt, request)
            else:
                # No AI model available
                raise HTTPException(
                    status_code=503,
                    detail="No AI model available for content generation. Please configure API keys.",
                )

        except Exception as e:
            logger.error(f"Error generating text content: {e}")
            error_counter.labels(error_type="text_generation").inc()
            raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")

    def _build_content_prompt(self, request: ContentRequest) -> str:
        """Build optimized prompt for content generation"""
        prompt_parts = [
            f"Create a {request.content_type} about '{request.topic}'",
            f"Target audience: {request.target_audience}",
            f"Tone: {request.tone}",
            f"Length: {request.length}",
        ]

        if request.keywords:
            prompt_parts.append(f"Include these keywords naturally: {', '.join(request.keywords)}")

        if request.custom_instructions:
            prompt_parts.append(f"Additional instructions: {request.custom_instructions}")

        # Content type specific instructions
        if request.content_type == "article":
            prompt_parts.append("Structure: Introduction, main sections with headers, conclusion")
            prompt_parts.append("Include actionable insights and examples")
        elif request.content_type == "social_post":
            prompt_parts.append("Make it engaging and shareable")
            prompt_parts.append("Include relevant hashtags")
        elif request.content_type == "video_script":
            prompt_parts.append("Include scene descriptions and timing cues")
            prompt_parts.append("Write for spoken delivery")
        elif request.content_type == "podcast_script":
            prompt_parts.append("Include natural conversation flow")
            prompt_parts.append("Add pause indicators and emphasis notes")

        return "\\n\\n".join(prompt_parts)

    async def _generate_with_openai(self, prompt: str, request: ContentRequest) -> str:
        """Generate content using OpenAI GPT models"""
        try:
            response = await asyncio.to_thread(
                openai_client.chat.completions.create,
                model=request.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content creator specializing in engaging, SEO - optimized content.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=self._get_max_tokens(request.length),
                temperature=0.7,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    async def _generate_with_anthropic(self, prompt: str, request: ContentRequest) -> str:
        """Generate content using Anthropic Claude"""
        try:
            response = await asyncio.to_thread(
                anthropic_client.messages.create,
                model=request.ai_model,
                max_tokens=self._get_max_tokens(request.length),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def _generate_with_gemini(self, prompt: str, request: ContentRequest) -> str:
        """Generate content using Google Gemini"""
        try:
            response = await asyncio.to_thread(
                gemini_model.generate_content,
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=self._get_max_tokens(request.length),
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise

    def _get_max_tokens(self, length: str) -> int:
        """Get max tokens based on content length"""
        length_map = {"short": 500, "medium": 1500, "long": 3000, "very_long": 5000}
        return length_map.get(length, 1500)


# Image Generation Engine


class ImageGenerator:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=3600)

    async def generate_image(
        self, prompt: str, style: str = "realistic", size: str = "1024x1024"
    ) -> str:
        """Generate image using AI models"""
        try:
            cache_key = f"img_{hash(prompt)}_{style}_{size}"
            if cache_key in self.cache:
                cache_hit_counter.inc()
                return self.cache[cache_key]

            cache_miss_counter.inc()

            if stability_api:
                image_path = await self._generate_with_stability(prompt, style, size)
            elif openai_client:
                image_path = await self._generate_with_dalle(prompt, size)
            else:
                image_path = await self._generate_placeholder_image(prompt, size)

            self.cache[cache_key] = image_path
            return image_path

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            error_counter.labels(error_type="image_generation").inc()
            return await self._generate_placeholder_image(prompt, size)

    async def _generate_with_stability(self, prompt: str, style: str, size: str) -> str:
        """Generate image using Stability AI"""
        try:
            width, height = map(int, size.split("x"))

            answers = stability_api.generate(
                prompt=prompt,
                seed=42,
                steps=30,
                cfg_scale=8.0,
                width=width,
                height=height,
                samples=1,
                sampler=generation.SAMPLER_K_DPMPP_2M,
            )

            for resp in answers:
                for artifact in resp.artifacts:
                    if artifact.finish_reason == generation.FILTER:
                        logger.warning("Image generation filtered by safety")
                        continue
                    if artifact.type == generation.ARTIFACT_IMAGE:
                        filename = f"output/generated_image_{uuid4().hex}.png"
                        with open(filename, "wb") as f:
                            f.write(artifact.binary)
                        return filename

            raise Exception("No valid image generated")

        except Exception as e:
            logger.error(f"Stability AI error: {e}")
            raise

    async def _generate_with_dalle(self, prompt: str, size: str) -> str:
        """Generate image using DALL - E"""
        try:
            response = await asyncio.to_thread(
                openai_client.images.generate,
                model="dall - e - 3",
                prompt=prompt,
                size=size,
                quality="standard",
                n=1,
            )

            image_url = response.data[0].url

            # Download and save image
            async with httpx.AsyncClient() as client:
                img_response = await client.get(image_url)
                filename = f"output/dalle_image_{uuid4().hex}.png"

                async with aiofiles.open(filename, "wb") as f:
                    await f.write(img_response.content)

                return filename

        except Exception as e:
            logger.error(f"DALL - E error: {e}")
            raise

    async def _generate_placeholder_image(self, prompt: str, size: str) -> str:
        """Generate placeholder image"""
        try:
            width, height = map(int, size.split("x"))

            # Create placeholder image
            img = Image.new("RGB", (width, height), color="lightblue")
            draw = ImageDraw.Draw(img)

            # Add text
            text = f"Generated Image\\n{prompt[:50]}..."
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except Exception:
                font = ImageFont.load_default()

            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2

            draw.text((x, y), text, fill="darkblue", font=font)

            filename = f"output/placeholder_image_{uuid4().hex}.png"
            img.save(filename)

            return filename

        except Exception as e:
            logger.error(f"Error creating placeholder image: {e}")
            raise


# Video Generation Engine


class VideoGenerator:
    def __init__(self):
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)

    async def generate_video(
        self, script: str, images: List[str], audio_path: Optional[str] = None
    ) -> str:
        """Generate video from script, images, and audio"""
        try:
            # Create video clips from images
            clips = []

            for i, image_path in enumerate(images):
                if os.path.exists(image_path):
                    clip = mp.ImageClip(image_path, duration=3)
                    clips.append(clip)

            if not clips:
                raise Exception("No valid images for video creation")

            # Concatenate clips
            video = mp.concatenate_videoclips(clips, method="compose")

            # Add audio if provided
            if audio_path and os.path.exists(audio_path):
                audio = mp.AudioFileClip(audio_path)
                video = video.set_audio(audio)

            # Export video
            output_path = f"output/generated_video_{uuid4().hex}.mp4"
            video.write_videofile(
                output_path,
                fps=24,
                codec="libx264",
                audio_codec="aac",
                temp_audiofile=str(self.temp_dir / "temp_audio.m4a"),
                remove_temp=True,
            )

            # Clean up
            video.close()
            if audio_path:
                audio.close()

            return output_path

        except Exception as e:
            logger.error(f"Error generating video: {e}")
            error_counter.labels(error_type="video_generation").inc()
            raise


# Audio Generation Engine


class AudioGenerator:
    def __init__(self):
        pass

    async def generate_audio(self, text: str, voice: str = "alloy", speed: float = 1.0) -> str:
        """Generate audio from text"""
        try:
            if config.ELEVENLABS_API_KEY:
                return await self._generate_with_elevenlabs(text, voice)
            elif openai_client:
                return await self._generate_with_openai_tts(text, voice, speed)
            else:
                return await self._generate_with_gtts(text)

        except Exception as e:
            logger.error(f"Error generating audio: {e}")
            error_counter.labels(error_type="audio_generation").inc()
            raise

    async def _generate_with_elevenlabs(self, text: str, voice: str) -> str:
        """Generate audio using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=Voice(voice_id=voice),
                api_key=config.ELEVENLABS_API_KEY,
            )

            filename = f"output/elevenlabs_audio_{uuid4().hex}.mp3"
            with open(filename, "wb") as f:
                f.write(audio)

            return filename

        except Exception as e:
            logger.error(f"ElevenLabs error: {e}")
            raise

    async def _generate_with_openai_tts(self, text: str, voice: str, speed: float) -> str:
        """Generate audio using OpenAI TTS"""
        try:
            response = await asyncio.to_thread(
                openai_client.audio.speech.create,
                model="tts - 1",
                voice=voice,
                input=text,
                speed=speed,
            )

            filename = f"output/openai_tts_{uuid4().hex}.mp3"
            response.stream_to_file(filename)

            return filename

        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            raise

    async def _generate_with_gtts(self, text: str) -> str:
        """Generate audio using Google TTS"""
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            filename = f"output/gtts_audio_{uuid4().hex}.mp3"

            await asyncio.to_thread(tts.save, filename)

            return filename

        except Exception as e:
            logger.error(f"gTTS error: {e}")
            raise


# SEO Analyzer


class SEOAnalyzer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)

    def analyze_content(self, content: str, keywords: List[str]) -> Dict[str, Any]:
        """Analyze content for SEO metrics"""
        try:
            analysis = {
                "readability": self._analyze_readability(content),
                "keyword_density": self._analyze_keyword_density(content, keywords),
                "content_structure": self._analyze_structure(content),
                "sentiment": self._analyze_sentiment(content),
                "word_count": len(content.split()),
                "character_count": len(content),
                "estimated_reading_time": len(content.split()) / 200,  # Average reading speed
                "seo_score": 0.0,
            }

            # Calculate overall SEO score
            analysis["seo_score"] = self._calculate_seo_score(analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return {"error": str(e), "seo_score": 0.0}

    def _analyze_readability(self, content: str) -> Dict[str, float]:
        """Analyze content readability"""
        try:
            return {
                "flesch_reading_ease": flesch_reading_ease(content),
                "flesch_kincaid_grade": flesch_kincaid_grade(content),
            }
        except Exception:
            return {"flesch_reading_ease": 0.0, "flesch_kincaid_grade": 0.0}

    def _analyze_keyword_density(self, content: str, keywords: List[str]) -> Dict[str, float]:
        """Analyze keyword density"""
        content_lower = content.lower()
        word_count = len(content.split())

        densities = {}
        for keyword in keywords:
            count = content_lower.count(keyword.lower())
            density = (count / word_count) * 100 if word_count > 0 else 0
            densities[keyword] = density

        return densities

    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze content structure"""
        lines = content.split("\\n")

        return {
            "has_headings": any(line.startswith("#") for line in lines),
            "paragraph_count": len(
                [line for line in lines if line.strip() and not line.startswith("#")]
            ),
            "heading_count": len([line for line in lines if line.startswith("#")]),
            "list_count": len(
                [line for line in lines if line.strip().startswith(("-", "*", "1."))]
            ),
        }

    def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Analyze content sentiment"""
        try:
            if sentiment_analyzer:
                scores = sentiment_analyzer.polarity_scores(content)
                return scores
            else:
                # Fallback using TextBlob
                blob = TextBlob(content)
                return {
                    "compound": blob.sentiment.polarity,
                    "pos": max(0, blob.sentiment.polarity),
                    "neu": 1 - abs(blob.sentiment.polarity),
                    "neg": max(0, -blob.sentiment.polarity),
                }
        except Exception:
            return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}

    def _calculate_seo_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall SEO score"""
        score = 0.0

        # Readability score (0 - 30 points)
        flesch_score = analysis["readability"].get("flesch_reading_ease", 0)
        if flesch_score >= 60:
            score += 30
        elif flesch_score >= 30:
            score += 20
        else:
            score += 10

        # Word count score (0 - 20 points)
        word_count = analysis["word_count"]
        if 300 <= word_count <= 2000:
            score += 20
        elif word_count >= 100:
            score += 10

        # Structure score (0 - 25 points)
        structure = analysis["content_structure"]
        if structure["has_headings"]:
            score += 10
        if structure["paragraph_count"] >= 3:
            score += 10
        if structure["list_count"] > 0:
            score += 5

        # Keyword density score (0 - 25 points)
        keyword_densities = analysis["keyword_density"]
        if keyword_densities:
            avg_density = sum(keyword_densities.values()) / len(keyword_densities)
            if 1 <= avg_density <= 3:
                score += 25
            elif 0.5 <= avg_density <= 5:
                score += 15
            else:
                score += 5

        return min(score, 100.0)


# Content Publisher


class ContentPublisher:
    def __init__(self):
        self.social_clients = self._initialize_social_clients()
        self.cms_clients = self._initialize_cms_clients()

    def _initialize_social_clients(self) -> Dict[str, Any]:
        """Initialize social media clients"""
        clients = {}

        # Twitter
        if all(
            [
                config.TWITTER_API_KEY,
                config.TWITTER_API_SECRET,
                config.TWITTER_ACCESS_TOKEN,
                config.TWITTER_ACCESS_TOKEN_SECRET,
            ]
        ):
            try:
                auth = tweepy.OAuthHandler(config.TWITTER_API_KEY, config.TWITTER_API_SECRET)
                auth.set_access_token(
                    config.TWITTER_ACCESS_TOKEN, config.TWITTER_ACCESS_TOKEN_SECRET
                )
                clients["twitter"] = tweepy.API(auth)
            except Exception as e:
                logger.error(f"Twitter client initialization failed: {e}")

        # Facebook
        if config.FACEBOOK_ACCESS_TOKEN:
            try:
                clients["facebook"] = GraphAPI(access_token=config.FACEBOOK_ACCESS_TOKEN)
            except Exception as e:
                logger.error(f"Facebook client initialization failed: {e}")

        # LinkedIn
        if config.LINKEDIN_ACCESS_TOKEN:
            try:
                clients["linkedin"] = Linkedin("", "", authenticate=True)
            except Exception as e:
                logger.error(f"LinkedIn client initialization failed: {e}")

        return clients

    def _initialize_cms_clients(self) -> Dict[str, Any]:
        """Initialize CMS clients"""
        clients = {}

        # WordPress
        if all([config.WORDPRESS_URL, config.WORDPRESS_USERNAME, config.WORDPRESS_PASSWORD]):
            try:
                clients["wordpress"] = WordPressClient(
                    config.WORDPRESS_URL,
                    config.WORDPRESS_USERNAME,
                    config.WORDPRESS_PASSWORD,
                )
            except Exception as e:
                logger.error(f"WordPress client initialization failed: {e}")

        return clients

    async def publish_content(self, content_id: str, channels: List[str]) -> Dict[str, Any]:
        """Publish content to specified channels"""
        results = {}

        # Get content from database
        db = SessionLocal()
        try:
            content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
            if not content_item:
                raise HTTPException(status_code=404, detail="Content not found")

            for channel in channels:
                try:
                    if channel in self.social_clients:
                        result = await self._publish_to_social(content_item, channel)
                    elif channel in self.cms_clients:
                        result = await self._publish_to_cms(content_item, channel)
                    else:
                        result = {
                            "success": False,
                            "error": f"Unknown channel: {channel}",
                        }

                    results[channel] = result

                except Exception as e:
                    logger.error(f"Error publishing to {channel}: {e}")
                    results[channel] = {"success": False, "error": str(e)}

            # Update content status
            if any(r.get("success") for r in results.values()):
                content_item.status = "published"
                content_item.published_at = datetime.utcnow()

            db.commit()

        finally:
            db.close()

        return results

    async def _publish_to_social(self, content_item: ContentItem, channel: str) -> Dict[str, Any]:
        """Publish content to social media"""
        try:
            client = self.social_clients[channel]

            if channel == "twitter":
                # Truncate content for Twitter
                tweet_text = content_item.content[:280]
                status = await asyncio.to_thread(client.update_status, tweet_text)
                return {
                    "success": True,
                    "post_id": status.id,
                    "url": f"https://twitter.com/user/status/{status.id}",
                }

            elif channel == "facebook":
                response = await asyncio.to_thread(
                    client.put_object,
                    parent_object="me",
                    connection_name="feed",
                    message=content_item.content,
                )
                return {"success": True, "post_id": response["id"]}

            elif channel == "linkedin":
                # LinkedIn publishing would require more complex setup
                return {
                    "success": False,
                    "error": "LinkedIn publishing not fully implemented",
                }

        except Exception as e:
            logger.error(f"Social media publishing error: {e}")
            return {"success": False, "error": str(e)}

    async def _publish_to_cms(self, content_item: ContentItem, channel: str) -> Dict[str, Any]:
        """Publish content to CMS"""
        try:
            client = self.cms_clients[channel]

            if channel == "wordpress":
                post = xmlrpc_client.WordPressPost()
                post.title = content_item.title
                post.content = content_item.content
                post.post_status = "publish"

                if content_item.tags:
                    post.terms_names = {"post_tag": content_item.tags}

                post_id = await asyncio.to_thread(client.call, posts.NewPost(post))
                return {"success": True, "post_id": post_id}

        except Exception as e:
            logger.error(f"CMS publishing error: {e}")
            return {"success": False, "error": str(e)}


# Main Content Agent Class


class TraeAIContentAgent:
    def __init__(self):
        self.content_generator = ContentGenerator()
        self.image_generator = ImageGenerator()
        self.video_generator = VideoGenerator()
        self.audio_generator = AudioGenerator()
        self.seo_analyzer = SEOAnalyzer()
        self.content_publisher = ContentPublisher()

        # Create tables
        Base.metadata.create_all(bind=engine)

    async def create_content(self, request: ContentRequest) -> ContentResponse:
        """Create comprehensive content based on request"""
        start_time = time.time()
        active_tasks_gauge.inc()

        try:
            # Generate unique ID
            content_id = str(uuid4())

            # Generate main content
            logger.info(f"Generating {request.content_type} content: {request.title}")
            content = await self.content_generator.generate_text_content(request)

            # Analyze SEO
            seo_analysis = self.seo_analyzer.analyze_content(content, request.keywords)

            # Generate additional assets
            file_paths = {}

            if request.include_images:
                try:
                    image_prompt = f"{request.topic} - {request.title}"
                    image_path = await self.image_generator.generate_image(image_prompt)
                    file_paths["featured_image"] = image_path
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")

            if request.include_audio:
                try:
                    audio_path = await self.audio_generator.generate_audio(content)
                    file_paths["audio"] = audio_path
                except Exception as e:
                    logger.error(f"Audio generation failed: {e}")

            if request.include_video and "featured_image" in file_paths:
                try:
                    video_path = await self.video_generator.generate_video(
                        content, [file_paths["featured_image"]], file_paths.get("audio")
                    )
                    file_paths["video"] = video_path
                except Exception as e:
                    logger.error(f"Video generation failed: {e}")

            # Save to database
            db = SessionLocal()
            try:
                content_item = ContentItem(
                    id=content_id,
                    title=request.title,
                    content_type=request.content_type,
                    content=content,
                    item_metadata={
                        "topic": request.topic,
                        "target_audience": request.target_audience,
                        "tone": request.tone,
                        "length": request.length,
                        "keywords": request.keywords,
                        "custom_instructions": request.custom_instructions,
                    },
                    status="draft",
                    author="TRAE.AI",
                    tags=request.keywords,
                    seo_score=seo_analysis["seo_score"],
                    ai_model_used=request.ai_model,
                    generation_params=request.dict(),
                    file_paths=file_paths,
                    publishing_channels=request.publishing_channels,
                )

                db.add(content_item)
                db.commit()

                # Schedule publishing if requested
                if request.schedule_time and request.publishing_channels:
                    await self._schedule_publishing(
                        content_id, request.publishing_channels, request.schedule_time
                    )

            finally:
                db.close()

            # Update metrics
            content_generation_counter.labels(
                content_type=request.content_type, ai_model=request.ai_model
            ).inc()

            duration = time.time() - start_time
            content_generation_duration.labels(content_type=request.content_type).observe(duration)

            # Estimate engagement
            estimated_engagement = self._estimate_engagement(seo_analysis, request.content_type)

            return ContentResponse(
                id=content_id,
                title=request.title,
                content_type=request.content_type,
                content=content,
                item_metadata=seo_analysis,
                status="draft",
                created_at=datetime.utcnow(),
                file_paths=file_paths,
                seo_score=seo_analysis["seo_score"],
                estimated_engagement=estimated_engagement,
            )

        except Exception as e:
            logger.error(f"Content creation failed: {e}")
            error_counter.labels(error_type="content_creation").inc()
            raise HTTPException(status_code=500, detail=f"Content creation failed: {str(e)}")

        finally:
            active_tasks_gauge.dec()

    async def _schedule_publishing(
        self, content_id: str, channels: List[str], schedule_time: datetime
    ):
        """Schedule content publishing"""
        db = SessionLocal()
        try:
            for channel in channels:
                schedule_item = ContentSchedule(
                    content_id=content_id, channel=channel, scheduled_time=schedule_time
                )
                db.add(schedule_item)

            db.commit()

            # Add to scheduler
            scheduler.add_job(
                self._publish_scheduled_content,
                "date",
                run_date=schedule_time,
                args=[content_id, channels],
                id=f"publish_{content_id}_{int(schedule_time.timestamp())}",
            )

        finally:
            db.close()

    async def _publish_scheduled_content(self, content_id: str, channels: List[str]):
        """Publish scheduled content"""
        try:
            results = await self.content_publisher.publish_content(content_id, channels)
            logger.info(f"Published content {content_id} to channels: {results}")
        except Exception as e:
            logger.error(f"Scheduled publishing failed for {content_id}: {e}")

    def _estimate_engagement(
        self, seo_analysis: Dict[str, Any], content_type: str
    ) -> Dict[str, float]:
        """Estimate content engagement metrics"""
        base_engagement = {
            "article": {"views": 1000, "shares": 50, "comments": 10},
            "social_post": {"likes": 100, "shares": 20, "comments": 5},
            "video": {"views": 500, "likes": 25, "comments": 8},
            "podcast": {"listens": 200, "shares": 15, "comments": 3},
        }

        base = base_engagement.get(content_type, {"engagement": 100})

        # Adjust based on SEO score
        multiplier = seo_analysis["seo_score"] / 100

        return {key: int(value * multiplier) for key, value in base.items()}

    async def get_analytics(self) -> ContentAnalytics:
        """Get content analytics"""
        db = SessionLocal()
        try:
            # Get all content items
            content_items = db.query(ContentItem).all()

            # Calculate metrics
            total_content = len(content_items)

            content_by_type = {}
            for item in content_items:
                content_by_type[item.content_type] = content_by_type.get(item.content_type, 0) + 1

            # Calculate engagement metrics
            engagement_metrics = {
                "average_seo_score": sum(item.seo_score or 0 for item in content_items)
                / max(total_content, 1),
                "published_content": len(
                    [item for item in content_items if item.status == "published"]
                ),
                "draft_content": len([item for item in content_items if item.status == "draft"]),
            }

            # Top performing content
            top_performing = sorted(content_items, key=lambda x: x.seo_score or 0, reverse=True)[:5]

            top_performing_content = [
                {
                    "id": item.id,
                    "title": item.title,
                    "content_type": item.content_type,
                    "seo_score": item.seo_score,
                    "created_at": item.created_at.isoformat(),
                }
                for item in top_performing
            ]

            # SEO performance
            seo_performance = {
                "average_score": engagement_metrics["average_seo_score"],
                "high_quality_content": len(
                    [item for item in content_items if (item.seo_score or 0) >= 80]
                ),
                "needs_improvement": len(
                    [item for item in content_items if (item.seo_score or 0) < 60]
                ),
            }

            # AI model performance
            ai_model_performance = {}
            for item in content_items:
                if item.ai_model_used:
                    if item.ai_model_used not in ai_model_performance:
                        ai_model_performance[item.ai_model_used] = {
                            "count": 0,
                            "avg_score": 0,
                        }
                    ai_model_performance[item.ai_model_used]["count"] += 1

            for model in ai_model_performance:
                model_items = [item for item in content_items if item.ai_model_used == model]
                avg_score = sum(item.seo_score or 0 for item in model_items) / len(model_items)
                ai_model_performance[model]["avg_score"] = avg_score

            # Publishing success rate
            publishing_success_rate = {
                "overall": len([item for item in content_items if item.status == "published"])
                / max(total_content, 1)
            }

            return ContentAnalytics(
                total_content=total_content,
                content_by_type=content_by_type,
                engagement_metrics=engagement_metrics,
                top_performing_content=top_performing_content,
                seo_performance=seo_performance,
                ai_model_performance=ai_model_performance,
                publishing_success_rate=publishing_success_rate,
            )

        finally:
            db.close()


# Initialize the agent
agent = TraeAIContentAgent()

# Database dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting TRAE.AI Content Agent")
    scheduler.start()
    yield
    # Shutdown
    logger.info("Shutting down TRAE.AI Content Agent")
    scheduler.shutdown()


app = FastAPI(
    title="TRAE.AI Content Agent",
    description="AI - powered content creation and management service",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "content - agent",
        "version": "1.0.0",
    }


@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()


@app.post("/api/content/create", response_model=ContentResponse)
async def create_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """Create new content"""
    api_request_counter.labels(endpoint="create_content", method="POST").inc()

    with api_request_duration.labels(endpoint="create_content").time():
        return await agent.create_content(request)


@app.post("/api/content/bulk - create")
async def bulk_create_content(request: BulkContentRequest, background_tasks: BackgroundTasks):
    """Create multiple content items"""
    api_request_counter.labels(endpoint="bulk_create_content", method="POST").inc()

    results = []
    for topic in request.topics:
        content_request = request.common_settings.copy()
        content_request.topic = topic
        content_request.title = f"{content_request.title} - {topic}"

        try:
            result = await agent.create_content(content_request)
            results.append({"topic": topic, "success": True, "content_id": result.id})
        except Exception as e:
            results.append({"topic": topic, "success": False, "error": str(e)})

    return {"results": results}


@app.get("/api/content/{content_id}")
async def get_content(content_id: str, db: Session = Depends(get_db)):
    """Get content by ID"""
    api_request_counter.labels(endpoint="get_content", method="GET").inc()

    content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not content_item:
        raise HTTPException(status_code=404, detail="Content not found")

    return content_item


@app.get("/api/content")
async def list_content(
    content_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List content with filters"""
    api_request_counter.labels(endpoint="list_content", method="GET").inc()

    query = db.query(ContentItem)

    if content_type:
        query = query.filter(ContentItem.content_type == content_type)
    if status:
        query = query.filter(ContentItem.status == status)

    content_items = query.offset(offset).limit(limit).all()
    total = query.count()

    return {"items": content_items, "total": total, "limit": limit, "offset": offset}


@app.post("/api/content/{content_id}/publish")
async def publish_content(content_id: str, channels: List[str], background_tasks: BackgroundTasks):
    """Publish content to specified channels"""
    api_request_counter.labels(endpoint="publish_content", method="POST").inc()

    results = await agent.content_publisher.publish_content(content_id, channels)
    return {"content_id": content_id, "results": results}


@app.post("/api/content/{content_id}/schedule")
async def schedule_content(
    content_id: str,
    channels: List[str],
    schedule_time: datetime,
    background_tasks: BackgroundTasks,
):
    """Schedule content publishing"""
    api_request_counter.labels(endpoint="schedule_content", method="POST").inc()

    await agent._schedule_publishing(content_id, channels, schedule_time)
    return {
        "content_id": content_id,
        "scheduled_time": schedule_time,
        "channels": channels,
    }


@app.get("/api/content/{content_id}/files/{file_type}")
async def get_content_file(content_id: str, file_type: str, db: Session = Depends(get_db)):
    """Get content file (image, video, audio)"""
    api_request_counter.labels(endpoint="get_content_file", method="GET").inc()

    content_item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not content_item:
        raise HTTPException(status_code=404, detail="Content not found")

    if not content_item.file_paths or file_type not in content_item.file_paths:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = content_item.file_paths[file_type]
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(file_path)


@app.get("/api/analytics", response_model=ContentAnalytics)
async def get_analytics():
    """Get content analytics"""
    api_request_counter.labels(endpoint="get_analytics", method="GET").inc()

    return await agent.get_analytics()


@app.post("/api/content/analyze - seo")
async def analyze_seo(content: str, keywords: List[str]):
    """Analyze content for SEO"""
    api_request_counter.labels(endpoint="analyze_seo", method="POST").inc()

    analysis = agent.seo_analyzer.analyze_content(content, keywords)
    return analysis


@app.post("/api/content/generate - image")
async def generate_image(prompt: str, style: str = "realistic", size: str = "1024x1024"):
    """Generate image from prompt"""
    api_request_counter.labels(endpoint="generate_image", method="POST").inc()

    image_path = await agent.image_generator.generate_image(prompt, style, size)
    return {"image_path": image_path}


@app.post("/api/content/generate - audio")
async def generate_audio(text: str, voice: str = "alloy", speed: float = 1.0):
    """Generate audio from text"""
    api_request_counter.labels(endpoint="generate_audio", method="POST").inc()

    audio_path = await agent.audio_generator.generate_audio(text, voice, speed)
    return {"audio_path": audio_path}


@app.post("/api/content/generate - video")
async def generate_video(script: str, images: List[str], audio_path: Optional[str] = None):
    """Generate video from script and assets"""
    api_request_counter.labels(endpoint="generate_video", method="POST").inc()

    video_path = await agent.video_generator.generate_video(script, images, audio_path)
    return {"video_path": video_path}


@app.get("/api/templates")
async def list_templates(db: Session = Depends(get_db)):
    """List content templates"""
    api_request_counter.labels(endpoint="list_templates", method="GET").inc()

    templates = db.query(ContentTemplate).all()
    return templates


@app.post("/api/templates")
async def create_template(template_data: dict, db: Session = Depends(get_db)):
    """Create content template"""
    api_request_counter.labels(endpoint="create_template", method="POST").inc()

    template = ContentTemplate(
        name=template_data["name"],
        content_type=template_data["content_type"],
        template=template_data["template"],
        variables=template_data.get("variables", []),
    )

    db.add(template)
    db.commit()
    db.refresh(template)

    return template


@app.get("/api/schedule")
async def get_schedule(db: Session = Depends(get_db)):
    """Get content publishing schedule"""
    api_request_counter.labels(endpoint="get_schedule", method="GET").inc()

    schedule_items = (
        db.query(ContentSchedule)
        .filter(ContentSchedule.status == "pending")
        .order_by(ContentSchedule.scheduled_time)
        .all()
    )

    return schedule_items


# Background tasks
@scheduler.scheduled_job("interval", minutes=5)
async def process_scheduled_content():
    """Process scheduled content publishing"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        due_items = (
            db.query(ContentSchedule)
            .filter(
                ContentSchedule.status == "pending",
                ContentSchedule.scheduled_time <= now,
            )
            .all()
        )

        for item in due_items:
            try:
                results = await agent.content_publisher.publish_content(
                    item.content_id, [item.channel]
                )

                if results.get(item.channel, {}).get("success"):
                    item.status = "published"
                    item.published_at = datetime.utcnow()
                else:
                    item.status = "failed"
                    item.error_message = results.get(item.channel, {}).get("error", "Unknown error")

                db.commit()

            except Exception as e:
                logger.error(f"Failed to publish scheduled content {item.id}: {e}")
                item.status = "failed"
                item.error_message = str(e)
                db.commit()

    finally:
        db.close()


@scheduler.scheduled_job("interval", hours=1)
async def cleanup_old_files():
    """Clean up old generated files"""
    try:
        output_dir = Path("output")
        temp_dir = Path("temp")

        # Remove files older than 24 hours
        cutoff_time = time.time() - (24 * 60 * 60)

        for directory in [output_dir, temp_dir]:
            if directory.exists():
                for file_path in directory.iterdir():
                    if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                        try:
                            file_path.unlink()
                            logger.info(f"Cleaned up old file: {file_path}")
                        except Exception as e:
                            logger.error(f"Failed to delete {file_path}: {e}")

    except Exception as e:
        logger.error(f"File cleanup failed: {e}")


@scheduler.scheduled_job("interval", hours=6)
async def update_content_metrics():
    """Update content performance metrics"""
    db = SessionLocal()
    try:
        # Update engagement metrics for published content
        published_content = db.query(ContentItem).filter(ContentItem.status == "published").all()

        for content in published_content:
            # Simulate engagement metrics update
            # In production, this would fetch real metrics from social platforms
            if not content.engagement_metrics:
                content.engagement_metrics = {
                    "views": 0,
                    "likes": 0,
                    "shares": 0,
                    "comments": 0,
                }

            # Simulate metric growth
            growth_factor = 1.1 if content.seo_score > 70 else 1.05
            for metric in content.engagement_metrics:
                content.engagement_metrics[metric] = int(
                    content.engagement_metrics[metric] * growth_factor
                )

        db.commit()

    except Exception as e:
        logger.error(f"Metrics update failed: {e}")

    finally:
        db.close()


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    error_counter.labels(error_type="http_error").inc()
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "timestamp": datetime.utcnow().isoformat()},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    error_counter.labels(error_type="general_error").inc()
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    # Create output directories
    Path("output").mkdir(exist_ok=True)
    Path("temp").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

    logger.info("Starting TRAE.AI Content Agent")
    logger.info(f"Environment: {config.ENVIRONMENT}")
    logger.info(f"Use Mock: {config.USE_MOCK}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=config.ENVIRONMENT == "development",
        log_level=config.LOG_LEVEL.lower(),
    )
