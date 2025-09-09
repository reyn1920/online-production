#!/usr/bin/env python3
"""
Content Automation Pipeline - Integrated News-to-Video System

This module creates a complete automation pipeline that:
1. Monitors RSS feeds for breaking news and trending topics
2. Identifies content opportunities and hypocrisy tracking
3. Automatically generates video scripts, voice, and visuals
4. Produces multi-format content (video, audio, text)
5. Schedules and publishes content across platforms

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import queue
import hashlib
import logging
from enum import Enum

# Import existing modules
from breaking_news_watcher import RSSIntelligenceEngine, NewsArticle, TrendData
from backend.agents.content_agent import ContentAgent
from backend.content.automated_author import AutomatedAuthor, ContentType
from tools.basic_video_generator import create_basic_video
from utils.logger import get_logger

logger = get_logger(__name__)

class ContentPriority(Enum):
    """Content generation priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4

class ContentFormat(Enum):
    """Supported content output formats."""
    VIDEO = "video"
    AUDIO = "audio"
    ARTICLE = "article"
    SOCIAL_POST = "social_post"
    NEWSLETTER = "newsletter"
    PODCAST = "podcast"

@dataclass
class ContentOpportunity:
    """Represents an identified content creation opportunity."""
    id: str
    topic: str
    angle: str
    priority: ContentPriority
    formats: List[ContentFormat]
    source_articles: List[str]
    keywords: List[str]
    estimated_engagement: float
    deadline: datetime
    created_at: datetime
    metadata: Dict[str, Any]

@dataclass
class ContentProject:
    """Represents a content creation project in progress."""
    id: str
    opportunity_id: str
    title: str
    format: ContentFormat
    status: str  # planning, scripting, production, review, published
    script: Optional[str]
    assets: List[str]
    output_files: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ContentAutomationPipeline:
    """Main content automation pipeline orchestrator."""
    
    def __init__(self, config_path: str = "content_automation_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Initialize components
        self.rss_engine = RSSIntelligenceEngine()
        self.content_agent = ContentAgent()
        self.automated_author = AutomatedAuthor()
        
        # Pipeline state
        self.running = False
        self.opportunity_queue = queue.PriorityQueue()
        self.project_queue = queue.Queue()
        
        # Database setup
        self.db_path = "content_automation.db"
        self._init_automation_tables()
        
        # Content generation settings
        self.generation_settings = {
            'video': {
                'duration_range': (60, 180),  # 1-3 minutes
                'style': 'professional',
                'voice_profile': 'authoritative',
                'avatar_profile': 'news_anchor'
            },
            'article': {
                'word_count_range': (800, 1500),
                'tone': 'analytical',
                'format': 'blog_post'
            },
            'social_post': {
                'character_limit': 280,
                'hashtag_count': 3,
                'include_media': True
            }
        }
        
        logger.info("Content Automation Pipeline initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load pipeline configuration."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Create default config
            default_config = {
                'monitoring_interval': 15,  # minutes
                'content_generation_interval': 30,  # minutes
                'max_daily_content': 10,
                'priority_keywords': [
                    'breaking', 'urgent', 'scandal', 'controversy',
                    'hypocrisy', 'contradiction', 'exposed'
                ],
                'content_formats': ['video', 'article', 'social_post'],
                'auto_publish': False,
                'quality_threshold': 0.7
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            return default_config
    
    def _init_automation_tables(self):
        """Initialize database tables for automation pipeline."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Content opportunities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_opportunities (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                angle TEXT NOT NULL,
                priority INTEGER NOT NULL,
                formats TEXT NOT NULL,
                source_articles TEXT,
                keywords TEXT,
                estimated_engagement REAL,
                deadline TIMESTAMP,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Content projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_projects (
                id TEXT PRIMARY KEY,
                opportunity_id TEXT,
                title TEXT NOT NULL,
                format TEXT NOT NULL,
                status TEXT DEFAULT 'planning',
                script TEXT,
                assets TEXT,
                output_files TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (opportunity_id) REFERENCES content_opportunities (id)
            )
        """)
        
        # Content performance tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS content_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT,
                platform TEXT,
                views INTEGER DEFAULT 0,
                engagement_rate REAL DEFAULT 0.0,
                shares INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                published_at TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES content_projects (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Content automation database tables initialized")
    
    def identify_content_opportunities(self) -> List[ContentOpportunity]:
        """Analyze RSS data to identify content creation opportunities."""
        opportunities = []
        
        try:
            # Get trending topics from RSS engine
            trending_topics = self.rss_engine.get_trending_topics(limit=20)
            
            # Get recent hypocrisy opportunities
            hypocrisy_data = self._get_hypocrisy_opportunities()
            
            # Analyze trending topics for content potential
            for trend in trending_topics:
                opportunity = self._analyze_trend_for_content(trend)
                if opportunity:
                    opportunities.append(opportunity)
            
            # Analyze hypocrisy opportunities
            for hyp_data in hypocrisy_data:
                opportunity = self._create_hypocrisy_content_opportunity(hyp_data)
                if opportunity:
                    opportunities.append(opportunity)
            
            # Store opportunities in database
            for opp in opportunities:
                self._store_content_opportunity(opp)
            
            logger.info(f"Identified {len(opportunities)} content opportunities")
            
        except Exception as e:
            logger.error(f"Error identifying content opportunities: {e}")
        
        return opportunities
    
    def _analyze_trend_for_content(self, trend: TrendData) -> Optional[ContentOpportunity]:
        """Analyze a trending topic for content creation potential."""
        try:
            # Calculate content potential score
            engagement_score = min(trend.frequency * 0.1 + trend.trend_score * 0.3, 1.0)
            
            # Skip low-potential topics
            if engagement_score < 0.3:
                return None
            
            # Determine priority based on keywords and engagement
            priority = ContentPriority.MEDIUM
            if any(keyword in trend.keyword.lower() for keyword in self.config['priority_keywords']):
                priority = ContentPriority.HIGH
            if engagement_score > 0.8:
                priority = ContentPriority.URGENT
            
            # Determine suitable formats
            formats = [ContentFormat.ARTICLE, ContentFormat.SOCIAL_POST]
            if engagement_score > 0.6:
                formats.append(ContentFormat.VIDEO)
            
            # Generate content angle
            angle = self._generate_content_angle(trend.keyword, trend.sources)
            
            opportunity = ContentOpportunity(
                id=hashlib.md5(f"{trend.keyword}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                topic=trend.keyword,
                angle=angle,
                priority=priority,
                formats=formats,
                source_articles=trend.related_articles,
                keywords=[trend.keyword] + trend.keyword.split(),
                estimated_engagement=engagement_score,
                deadline=datetime.now() + timedelta(hours=24),
                created_at=datetime.now(),
                metadata={
                    'trend_score': trend.trend_score,
                    'frequency': trend.frequency,
                    'sources': trend.sources
                }
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error analyzing trend {trend.keyword}: {e}")
            return None
    
    def _get_hypocrisy_opportunities(self) -> List[Dict[str, Any]]:
        """Get recent hypocrisy tracking opportunities from database."""
        try:
            conn = sqlite3.connect(self.rss_engine.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM hypocrisy_tracker 
                WHERE created_at > datetime('now', '-7 days')
                AND content_used = FALSE
                ORDER BY severity_score DESC, confidence_score DESC
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            hypocrisy_data = []
            for row in results:
                data = dict(zip(columns, row))
                hypocrisy_data.append(data)
            
            conn.close()
            return hypocrisy_data
            
        except Exception as e:
            logger.error(f"Error fetching hypocrisy opportunities: {e}")
            return []
    
    def _create_hypocrisy_content_opportunity(self, hyp_data: Dict[str, Any]) -> Optional[ContentOpportunity]:
        """Create content opportunity from hypocrisy data."""
        try:
            # Calculate engagement potential
            severity = hyp_data.get('severity_score', 5)
            confidence = hyp_data.get('confidence_score', 0.5)
            engagement_score = (severity / 10.0) * confidence
            
            # High-impact hypocrisy gets priority
            priority = ContentPriority.HIGH if severity >= 7 else ContentPriority.MEDIUM
            
            # Generate compelling angle
            subject = hyp_data.get('subject_name', 'Unknown')
            contradiction_type = hyp_data.get('contradiction_type', 'direct')
            
            angle = f"Exposing {subject}'s {contradiction_type} contradiction: A detailed analysis"
            
            opportunity = ContentOpportunity(
                id=hashlib.md5(f"hyp_{hyp_data['id']}_{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                topic=f"{subject} Hypocrisy",
                angle=angle,
                priority=priority,
                formats=[ContentFormat.VIDEO, ContentFormat.ARTICLE],
                source_articles=[hyp_data.get('source_1', ''), hyp_data.get('source_2', '')],
                keywords=[subject, 'hypocrisy', 'contradiction', contradiction_type],
                estimated_engagement=engagement_score,
                deadline=datetime.now() + timedelta(hours=12),  # Urgent for hypocrisy
                created_at=datetime.now(),
                metadata={
                    'hypocrisy_id': hyp_data['id'],
                    'severity_score': severity,
                    'confidence_score': confidence,
                    'subject_type': hyp_data.get('subject_type', 'unknown')
                }
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Error creating hypocrisy opportunity: {e}")
            return None
    
    def _generate_content_angle(self, topic: str, sources: List[str]) -> str:
        """Generate a compelling content angle for a topic."""
        angles = [
            f"Breaking: What the mainstream media isn't telling you about {topic}",
            f"The hidden truth behind {topic} - An investigative analysis",
            f"Why {topic} matters more than you think - A deep dive",
            f"Exposing the real story behind {topic}",
            f"The {topic} controversy: Facts vs. Fiction"
        ]
        
        # Simple selection based on topic characteristics
        if 'scandal' in topic.lower() or 'controversy' in topic.lower():
            return f"Exposing the real story behind {topic}"
        elif 'breaking' in topic.lower():
            return f"Breaking: What the mainstream media isn't telling you about {topic}"
        else:
            return f"The hidden truth behind {topic} - An investigative analysis"
    
    def generate_content_from_opportunity(self, opportunity: ContentOpportunity) -> List[ContentProject]:
        """Generate content projects from an opportunity."""
        projects = []
        
        try:
            for content_format in opportunity.formats:
                project = self._create_content_project(opportunity, content_format)
                if project:
                    projects.append(project)
            
            logger.info(f"Generated {len(projects)} content projects for opportunity: {opportunity.topic}")
            
        except Exception as e:
            logger.error(f"Error generating content from opportunity {opportunity.id}: {e}")
        
        return projects
    
    def _create_content_project(self, opportunity: ContentOpportunity, content_format: ContentFormat) -> Optional[ContentProject]:
        """Create a specific content project."""
        try:
            project_id = hashlib.md5(f"{opportunity.id}_{content_format.value}_{datetime.now().isoformat()}".encode()).hexdigest()[:12]
            
            # Generate title based on format
            if content_format == ContentFormat.VIDEO:
                title = f"VIDEO: {opportunity.angle}"
            elif content_format == ContentFormat.ARTICLE:
                title = f"ANALYSIS: {opportunity.angle}"
            else:
                title = opportunity.angle
            
            project = ContentProject(
                id=project_id,
                opportunity_id=opportunity.id,
                title=title,
                format=content_format,
                status='planning',
                script=None,
                assets=[],
                output_files=[],
                metadata={
                    'priority': opportunity.priority.value,
                    'keywords': opportunity.keywords,
                    'source_articles': opportunity.source_articles,
                    'estimated_engagement': opportunity.estimated_engagement
                },
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            # Store project in database
            self._store_content_project(project)
            
            # Generate script/content
            self._generate_project_script(project, opportunity)
            
            return project
            
        except Exception as e:
            logger.error(f"Error creating content project: {e}")
            return None
    
    def _generate_project_script(self, project: ContentProject, opportunity: ContentOpportunity):
        """Generate script/content for a project."""
        try:
            if project.format == ContentFormat.VIDEO:
                script = self._generate_video_script(opportunity)
            elif project.format == ContentFormat.ARTICLE:
                script = self._generate_article_content(opportunity)
            elif project.format == ContentFormat.SOCIAL_POST:
                script = self._generate_social_post(opportunity)
            else:
                script = f"Content for {opportunity.topic}: {opportunity.angle}"
            
            project.script = script
            project.status = 'scripted'
            project.updated_at = datetime.now()
            
            # Update in database
            self._update_content_project(project)
            
            logger.info(f"Generated script for project {project.id}")
            
        except Exception as e:
            logger.error(f"Error generating script for project {project.id}: {e}")
    
    def _generate_video_script(self, opportunity: ContentOpportunity) -> str:
        """Generate video script using content agent."""
        try:
            # Use automated author for script generation
            prompt = f"""
            Create a compelling video script for: {opportunity.angle}
            
            Topic: {opportunity.topic}
            Keywords: {', '.join(opportunity.keywords)}
            
            The script should:
            1. Hook viewers in the first 10 seconds
            2. Present facts and analysis
            3. Include call-to-action
            4. Be 2-3 minutes when spoken
            5. Maintain journalistic integrity
            
            Format as a proper video script with timing cues.
            """
            
            # Generate using automated author
            script = self.automated_author.ollama.generate(
                prompt, 
                "You are an expert video script writer for investigative journalism.",
                temperature=0.7
            )
            
            return script
            
        except Exception as e:
            logger.error(f"Error generating video script: {e}")
            return f"Video script for: {opportunity.angle}"
    
    def _generate_article_content(self, opportunity: ContentOpportunity) -> str:
        """Generate article content."""
        try:
            # Create writing project
            project = self.automated_author.create_project(
                title=opportunity.angle,
                content_type=ContentType.BLOG_SERIES,
                target_audience="Informed citizens seeking truth",
                target_word_count=1200,
                persona_name="investigative_journalist",
                topic=opportunity.topic,
                key_themes=opportunity.keywords
            )
            
            # Generate first chapter
            if project.chapters:
                content = self.automated_author.write_chapter(project, project.chapters[0])
                return content
            
            return f"Article content for: {opportunity.angle}"
            
        except Exception as e:
            logger.error(f"Error generating article content: {e}")
            return f"Article content for: {opportunity.angle}"
    
    def _generate_social_post(self, opportunity: ContentOpportunity) -> str:
        """Generate social media post."""
        try:
            prompt = f"""
            Create a compelling social media post about: {opportunity.topic}
            
            Angle: {opportunity.angle}
            Keywords: {', '.join(opportunity.keywords[:3])}
            
            Requirements:
            - Under 280 characters
            - Include 2-3 relevant hashtags
            - Create urgency and engagement
            - Maintain credibility
            """
            
            post = self.automated_author.ollama.generate(
                prompt,
                "You are a social media expert focused on news and current events.",
                temperature=0.8,
                max_tokens=100
            )
            
            return post
            
        except Exception as e:
            logger.error(f"Error generating social post: {e}")
            return f"Breaking: {opportunity.topic} - {opportunity.angle[:100]}..."
    
    def produce_video_content(self, project: ContentProject) -> bool:
        """Produce video content from script."""
        try:
            if not project.script or project.format != ContentFormat.VIDEO:
                return False
            
            # Extract video parameters
            settings = self.generation_settings['video']
            duration = settings['duration_range'][1]  # Use max duration
            
            # Generate video using basic video generator
            output_dir = Path("output/videos")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            video_filename = f"{project.id}_video.mp4"
            video_path = output_dir / video_filename
            
            # Create background image if needed
            background_path = output_dir / f"{project.id}_background.jpg"
            self._create_video_background(background_path, project.title)
            
            # Generate video
            success = create_basic_video(
                output_path=str(video_path),
                duration=duration,
                background_image=str(background_path),
                title_text=project.title[:50],  # Truncate for display
                subtitle_text=f"Analysis by TRAE.AI"
            )
            
            if success:
                project.output_files.append(str(video_path))
                project.status = 'completed'
                project.updated_at = datetime.now()
                self._update_content_project(project)
                
                logger.info(f"Video production completed for project {project.id}")
                return True
            
        except Exception as e:
            logger.error(f"Error producing video for project {project.id}: {e}")
        
        return False
    
    def _create_video_background(self, output_path: Path, title: str):
        """Create a background image for video."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create background
            img = Image.new('RGB', (1920, 1080), color=(20, 30, 50))
            draw = ImageDraw.Draw(img)
            
            # Add gradient effect
            for y in range(1080):
                alpha = y / 1080.0
                color = (int(20 + alpha * 30), int(30 + alpha * 40), int(50 + alpha * 60))
                draw.line([(0, y), (1920, y)], fill=color)
            
            # Add title overlay
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 72)
            except:
                font = ImageFont.load_default()
            
            # Wrap text
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                bbox = draw.textbbox((0, 0), test_line, font=font)
                if bbox[2] > 1700:  # Max width
                    if len(current_line) > 1:
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        lines.append(word)
                        current_line = []
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Draw text lines
            y_offset = 400
            for line in lines[:3]:  # Max 3 lines
                bbox = draw.textbbox((0, 0), line, font=font)
                x = (1920 - bbox[2]) // 2
                draw.text((x, y_offset), line, fill=(255, 255, 255), font=font)
                y_offset += 100
            
            img.save(output_path)
            
        except Exception as e:
            logger.error(f"Error creating video background: {e}")
            # Create simple fallback
            try:
                img = Image.new('RGB', (1920, 1080), color=(50, 50, 100))
                img.save(output_path)
            except:
                pass
    
    def _store_content_opportunity(self, opportunity: ContentOpportunity):
        """Store content opportunity in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO content_opportunities
                (id, topic, angle, priority, formats, source_articles, keywords, 
                 estimated_engagement, deadline, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity.id,
                opportunity.topic,
                opportunity.angle,
                opportunity.priority.value,
                json.dumps([f.value for f in opportunity.formats]),
                json.dumps(opportunity.source_articles),
                json.dumps(opportunity.keywords),
                opportunity.estimated_engagement,
                opportunity.deadline.isoformat(),
                json.dumps(opportunity.metadata)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing content opportunity: {e}")
    
    def _store_content_project(self, project: ContentProject):
        """Store content project in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO content_projects
                (id, opportunity_id, title, format, status, script, assets, 
                 output_files, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                project.id,
                project.opportunity_id,
                project.title,
                project.format.value,
                project.status,
                project.script,
                json.dumps(project.assets),
                json.dumps(project.output_files),
                json.dumps(project.metadata),
                project.updated_at.isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing content project: {e}")
    
    def _update_content_project(self, project: ContentProject):
        """Update content project in database."""
        self._store_content_project(project)  # Same as store with REPLACE
    
    async def run_automation_pipeline(self):
        """Run the main automation pipeline."""
        self.running = True
        logger.info("Starting Content Automation Pipeline")
        
        while self.running:
            try:
                # Phase 1: Monitor and identify opportunities
                logger.info("Phase 1: Identifying content opportunities")
                opportunities = self.identify_content_opportunities()
                
                # Phase 2: Generate content projects
                logger.info("Phase 2: Generating content projects")
                all_projects = []
                for opportunity in opportunities[:5]:  # Limit to top 5
                    projects = self.generate_content_from_opportunity(opportunity)
                    all_projects.extend(projects)
                
                # Phase 3: Produce content
                logger.info("Phase 3: Producing content")
                for project in all_projects:
                    if project.format == ContentFormat.VIDEO:
                        self.produce_video_content(project)
                
                # Wait for next cycle
                await asyncio.sleep(self.config['content_generation_interval'] * 60)
                
            except Exception as e:
                logger.error(f"Error in automation pipeline: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def stop_automation_pipeline(self):
        """Stop the automation pipeline."""
        self.running = False
        logger.info("Content Automation Pipeline stopped")
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status and metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count opportunities
            cursor.execute("SELECT COUNT(*) FROM content_opportunities WHERE status = 'pending'")
            pending_opportunities = cursor.fetchone()[0]
            
            # Count projects by status
            cursor.execute("SELECT status, COUNT(*) FROM content_projects GROUP BY status")
            project_stats = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM content_projects 
                WHERE created_at > datetime('now', '-24 hours')
            """)
            recent_projects = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'running': self.running,
                'pending_opportunities': pending_opportunities,
                'project_stats': project_stats,
                'recent_projects_24h': recent_projects,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting pipeline status: {e}")
            return {'error': str(e)}

if __name__ == "__main__":
    # Example usage
    pipeline = ContentAutomationPipeline()
    
    # Run a single cycle
    print("Running content automation cycle...")
    opportunities = pipeline.identify_content_opportunities()
    print(f"Found {len(opportunities)} opportunities")
    
    if opportunities:
        # Generate content for first opportunity
        projects = pipeline.generate_content_from_opportunity(opportunities[0])
        print(f"Generated {len(projects)} content projects")
        
        # Produce video if available
        for project in projects:
            if project.format == ContentFormat.VIDEO:
                success = pipeline.produce_video_content(project)
                print(f"Video production: {'Success' if success else 'Failed'}")
    
    # Show status
    status = pipeline.get_pipeline_status()
    print(f"Pipeline status: {json.dumps(status, indent=2)}")