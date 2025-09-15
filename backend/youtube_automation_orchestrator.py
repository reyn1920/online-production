#!/usr/bin/env python3
"""""""""
TRAE.AI YouTube Automation Orchestrator
""""""
Comprehensive YouTube automation system that integrates all YouTube automation
capabilities including content creation, scheduling, analytics, engagement,
SEO optimization, and cross - platform promotion.
"""

TRAE.AI YouTube Automation Orchestrator



""""""


Features:



- Automated content pipeline from RSS to published videos
- AI - powered video creation with thumbnails and SEO optimization
- Intelligent scheduling based on audience analytics
- Automated comment engagement and community management
- Performance tracking and optimization
- Multi - channel network management
- Cross - platform promotion integration
- Security - compliant API management

Author: TRAE.AI System
Version: 1.0.0

"""

import asyncio
import json
import os
import queue
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.logger import setup_logger

from backend.agents.content_agent import ContentAgent
from backend.agents.marketing_agent import MarketingAgent
from backend.agents.youtube_engagement_agent import YouTubeEngagementAgent

# Import existing modules

from backend.integrations.youtube_integration import (
    YouTubeIntegration,
 )

from backend.pipelines.hollywood_pipeline import HollywoodPipeline
from content_automation_pipeline import (
    ContentAutomationPipeline,
 )


class AutomationStatus(Enum):
    """YouTube automation pipeline status."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class ContentStrategy(Enum):
    """Content creation strategies."""

    NEWS_REACTIVE = "news_reactive"  # React to breaking news
    TREND_FOLLOWING = "trend_following"  # Follow trending topics
    EDUCATIONAL = "educational"  # Create educational content
    ENTERTAINMENT = "entertainment"  # Entertainment - focused content
    MIXED = "mixed"  # Combination of strategies


class SchedulingStrategy(Enum):
    """Video scheduling strategies."""

    OPTIMAL_TIMING = "optimal_timing"  # Based on audience analytics
    CONSISTENT_SCHEDULE = "consistent_schedule"  # Regular posting schedule
    TREND_BASED = "trend_based"  # Schedule based on trending topics
    COMPETITIVE_ANALYSIS = "competitive_analysis"  # Based on competitor analysis


@dataclass
class YouTubeChannel:
    """
YouTube channel configuration.


    channel_id: str
    name: str
    niche: str
    target_audience: str
    content_strategy: ContentStrategy
    scheduling_strategy: SchedulingStrategy
    upload_frequency: int  # videos per week
    optimal_times: List[str]  # optimal posting times
    keywords: List[str]
    competitor_channels: List[str]
   
""""""

    active: bool = True
   

    
   
"""
@dataclass
class AutomationMetrics:
    """
YouTube automation performance metrics.


    videos_created: int = 0
    videos_uploaded: int = 0
    total_views: int = 0
    total_subscribers: int = 0
    engagement_rate: float = 0.0
    comments_replied: int = 0
    revenue_generated: float = 0.0
    seo_score: float = 0.0
    automation_efficiency: float = 0.0
   
""""""

    last_updated: datetime = None
   

    
   
"""
class YouTubeAutomationOrchestrator:
   """

    
   

    TODO: Add documentation
   
""""""

    Master orchestrator for all YouTube automation capabilities.
    Integrates content creation, scheduling, analytics, engagement, and optimization.
   

    
   
""""""
    
   """
    def __init__(self, config_path: str = "config/youtube_automation.json"):
        self.logger = setup_logger("youtube_automation")
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize database
        self.db_path = self.config.get("database_path", "data/youtube_automation.sqlite")
        self._init_database()

        # Initialize components
        self.youtube_integration = YouTubeIntegration()
        self.engagement_agent = YouTubeEngagementAgent()
        self.marketing_agent = MarketingAgent()
        self.content_agent = ContentAgent()
        self.hollywood_pipeline = HollywoodPipeline()
        self.content_pipeline = ContentAutomationPipeline()

        # Load channels configuration
        self.channels = self._load_channels()

        # Automation state
        self.status = AutomationStatus.STOPPED
        self.metrics = AutomationMetrics()
        self.running = False
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Queues for different automation tasks
        self.content_queue = queue.PriorityQueue()
        self.upload_queue = queue.Queue()
        self.engagement_queue = queue.Queue()
        self.analytics_queue = queue.Queue()

        self.logger.info("YouTube Automation Orchestrator initialized")

    def _load_config(self) -> Dict[str, Any]:
        """
Load automation configuration.

        
"""
        try:
        """"""
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
        """

        try:
        

       
""""""
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")

        # Default configuration
        return {
            "database_path": "data/youtube_automation.sqlite",
            "content_generation": {
                "enabled": True,
                "max_daily_videos": 5,
                "quality_threshold": 0.8,
                "auto_publish": False,
             },
            "scheduling": {
                "enabled": True,
                "analyze_optimal_times": True,
                "respect_frequency_limits": True,
             },
            "engagement": {
                "enabled": True,
                "auto_reply": True,
                "max_daily_replies": 50,
                "sentiment_threshold": 0.6,
             },
            "analytics": {
                "enabled": True,
                "tracking_interval": 3600,  # 1 hour
                "optimization_enabled": True,
             },
            "seo": {
                "enabled": True,
                "keyword_research": True,
                "trend_analysis": True,
                "competitor_analysis": True,
             },
            "security": {
                "rate_limiting": True,
                "api_quota_management": True,
                "credential_rotation": True,
             },
         }

    def _load_channels(self) -> List[YouTubeChannel]:
        """
Load YouTube channels configuration.

        
"""
        try:
        """
            channels_config_path = "config/channels.youtube.json"
        """

        try:
        

       
""""""
            if os.path.exists(channels_config_path):
                with open(channels_config_path, "r") as f:
                    data = json.load(f)
                    channels = []
                    for channel_data in data.get("channels", []):
                        channel = YouTubeChannel(
                            channel_id=channel_data.get("id", ""),
                            name=channel_data.get("name", ""),
                            niche=channel_data.get("niche", "general"),
                            target_audience=channel_data.get("target_audience", "general"),
                            content_strategy=ContentStrategy(
                                channel_data.get("content_strategy", "mixed")
                             ),
                            scheduling_strategy=SchedulingStrategy(
                                channel_data.get("scheduling_strategy", "optimal_timing")
                             ),
                            upload_frequency=channel_data.get("upload_frequency", 3),
                            optimal_times=channel_data.get(
                                "optimal_times", ["10:00", "14:00", "18:00"]
                             ),
                            keywords=channel_data.get("keywords", []),
                            competitor_channels=channel_data.get("competitors", []),
                         )
                        channels.append(channel)
                    return channels
        except Exception as e:
            self.logger.error(f"Error loading channels: {e}")

        # Default channel configuration
        return [
            YouTubeChannel(
                channel_id="default",
                name="TRAE.AI Channel",
                niche="AI Technology",
                target_audience="Tech enthusiasts, developers, AI researchers",
                content_strategy=ContentStrategy.EDUCATIONAL,
                scheduling_strategy=SchedulingStrategy.OPTIMAL_TIMING,
                upload_frequency=5,
                optimal_times=["10:00", "14:00", "18:00"],
                keywords=["AI", "automation", "technology", "tutorial"],
                competitor_channels=[],
             )
         ]

    def _init_database(self):
        """
Initialize automation database.

       
""""""

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
       

        
       
"""
        with sqlite3.connect(self.db_path) as conn:
            # Automation jobs table
            conn.execute(
               """

                
               

                CREATE TABLE IF NOT EXISTS automation_jobs (
                    id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        job_type TEXT,
                        status TEXT,
                        priority INTEGER,
                        data TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP,
                        completed_at TIMESTAMP
                 )
            
""""""

            

             
            
"""
             )
            """"""
        
       """

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
       

        
       
"""
            # Video production queue
            conn.execute(
               """

                
               

                CREATE TABLE IF NOT EXISTS video_queue (
                    id TEXT PRIMARY KEY,
                        channel_id TEXT,
                        title TEXT,
                        description TEXT,
                        tags TEXT,
                        thumbnail_path TEXT,
                        video_path TEXT,
                        scheduled_time TIMESTAMP,
                        status TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP
                 )
            
""""""

            

             
            
"""
             )
            """

             
            

            # Performance metrics
            conn.execute(
               
""""""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT,
                        metric_type TEXT,
                        value REAL,
                        timestamp TIMESTAMP
                 )
            """"""

            

             
            
"""
             )
            """"""
             
            """

             )
            

             
            
"""
            # SEO optimization data
            conn.execute(
               """

                
               

                CREATE TABLE IF NOT EXISTS seo_data (
                    id TEXT PRIMARY KEY,
                        video_id TEXT,
                        keywords TEXT,
                        trending_topics TEXT,
                        competitor_analysis TEXT,
                        optimization_score REAL,
                        created_at TIMESTAMP
                 )
            
""""""

            

             
            
"""
             )
            """

             
            

            conn.commit()
            
""""""

             )
            

             
            
"""
    async def start_automation(self) -> bool:
        """
Start the YouTube automation pipeline.

        
"""
        try:
        """"""
            if self.status == AutomationStatus.RUNNING:
                self.logger.warning("Automation already running")
        """

        try:
        

       
""""""
                return True

            self.logger.info("Starting YouTube automation pipeline...")
            self.status = AutomationStatus.STARTING
            self.running = True

            # Start automation threads
            automation_tasks = [
                self._content_generation_loop(),
                self._scheduling_loop(),
                self._engagement_loop(),
                self._analytics_loop(),
                self._seo_optimization_loop(),
             ]

            # Run all automation tasks concurrently
            await asyncio.gather(*automation_tasks)

            self.status = AutomationStatus.RUNNING
            self.logger.info("YouTube automation pipeline started successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error starting automation: {e}")
            self.status = AutomationStatus.ERROR
            return False

    async def stop_automation(self) -> bool:
        """Stop the YouTube automation pipeline."""
        try:
            self.logger.info("Stopping YouTube automation pipeline...")
            self.running = False
            self.status = AutomationStatus.STOPPED

            # Shutdown executor
            self.executor.shutdown(wait=True)

            self.logger.info("YouTube automation pipeline stopped")
            return True

        except Exception as e:
            self.logger.error(f"Error stopping automation: {e}")
            return False

    async def _content_generation_loop(self):
        """
Main content generation automation loop.

        while self.running:
            
"""
            try:
            """"""
                if not self.config["content_generation"]["enabled"]:
                    await asyncio.sleep(300)  # 5 minutes
                    continue
            """

            try:
            

           
""""""
                # Generate content for each active channel
                for channel in self.channels:
                    if not channel.active:
                        continue

                    # Check if channel needs new content
                    if await self._should_create_content(channel):
                        await self._create_channel_content(channel)

                await asyncio.sleep(1800)  # 30 minutes

            except Exception as e:
                self.logger.error(f"Error in content generation loop: {e}")
                await asyncio.sleep(300)

    async def _should_create_content(self, channel: YouTubeChannel) -> bool:
        """
Determine if channel needs new content based on strategy and schedule.

        try:
           
""""""

            # Check daily video limit
           

            
           
"""
            daily_limit = self.config["content_generation"]["max_daily_videos"]
           """

            
           

            # Check daily video limit
           
""""""
            today_count = await self._get_today_video_count(channel.channel_id)

            if today_count >= daily_limit:
                return False

            # Check upload frequency
            weekly_target = channel.upload_frequency
            week_count = await self._get_week_video_count(channel.channel_id)

            if week_count >= weekly_target:
                return False

            # Check for trending opportunities based on strategy
            if channel.content_strategy == ContentStrategy.NEWS_REACTIVE:
                return await self._has_breaking_news_opportunity(channel)
            elif channel.content_strategy == ContentStrategy.TREND_FOLLOWING:
                return await self._has_trending_opportunity(channel)
            else:
                return True  # Always create content for other strategies

        except Exception as e:
            self.logger.error(f"Error checking content creation need: {e}")
            return False

    async def _create_channel_content(self, channel: YouTubeChannel):
        """Create content for a specific channel."""
        try:
            self.logger.info(f"Creating content for channel: {channel.name}")

            # Generate content opportunity
            opportunity = await self._generate_content_opportunity(channel)
            if not opportunity:
                return

            # Create video project
            project = await self._create_video_project(channel, opportunity)
            if not project:
                return

            # Generate video content
            video_result = await self._generate_video_content(project)
            if not video_result:
                return

            # Optimize for SEO
            seo_result = await self._optimize_video_seo(project, video_result)

            # Schedule for upload
            await self._schedule_video_upload(channel, project, video_result, seo_result)

            self.metrics.videos_created += 1
            self.logger.info(f"Content created successfully for {channel.name}")

        except Exception as e:
            self.logger.error(f"Error creating channel content: {e}")

    async def _generate_content_opportunity(
        self, channel: YouTubeChannel
    ) -> Optional[Dict[str, Any]]:
        """
Generate content opportunity based on channel strategy.

        
"""
        try:
        """"""
            if channel.content_strategy == ContentStrategy.NEWS_REACTIVE:
                # Use content automation pipeline for news - based content
        """

        try:
        

                opportunities = self.content_pipeline.identify_opportunities()
                if opportunities:
                    
"""
                    return opportunities[0]  # Take highest priority
                    """"""
            elif channel.content_strategy == ContentStrategy.TREND_FOLLOWING:
                # Analyze trending topics in channel niche
                    """
                    return opportunities[0]  # Take highest priority
                    """
                trending_topics = await self._get_trending_topics(channel.niche)
                if trending_topics:
                    return {
                        "topic": trending_topics[0]["topic"],
                        "angle": f"Expert analysis of {trending_topics[0]['topic']}",
                        "keywords": trending_topics[0]["keywords"],
                        "priority": "high",
                     }

            elif channel.content_strategy == ContentStrategy.EDUCATIONAL:
                # Generate educational content based on channel keywords
                return {
                    "topic": f"How to master {channel.keywords[0] if channel.keywords else 'technology'}",
                    "angle": "Step - by - step tutorial",
                    "keywords": channel.keywords,
                    "priority": "medium",
                 }

            # Default content opportunity
            return {
                "topic": f"Latest insights in {channel.niche}",
                "angle": "Expert perspective",
                "keywords": channel.keywords,
                "priority": "medium",
             }

        except Exception as e:
            self.logger.error(f"Error generating content opportunity: {e}")
            return None

    async def _scheduling_loop(self):
        """
Video scheduling and publishing automation loop.

        while self.running:
            
"""
            try:
            """"""
                if not self.config["scheduling"]["enabled"]:
                    await asyncio.sleep(300)
                    continue
            """

            try:
            

           
""""""
                # Check for videos ready to upload
                await self._process_upload_queue()

                # Optimize scheduling for each channel
                for channel in self.channels:
                    if channel.active:
                        await self._optimize_channel_schedule(channel)

                await asyncio.sleep(600)  # 10 minutes

            except Exception as e:
                self.logger.error(f"Error in scheduling loop: {e}")
                await asyncio.sleep(300)

    async def _engagement_loop(self):
        """
Community engagement automation loop.

        while self.running:
            
"""
            try:
            """"""
                if not self.config["engagement"]["enabled"]:
                    await asyncio.sleep(300)
                    continue
            """

            try:
            

           
""""""
                # Process engagement for each channel
                for channel in self.channels:
                    if channel.active:
                        await self._process_channel_engagement(channel)

                await asyncio.sleep(900)  # 15 minutes

            except Exception as e:
                self.logger.error(f"Error in engagement loop: {e}")
                await asyncio.sleep(300)

    async def _analytics_loop(self):
        """
Analytics tracking and optimization loop.

        while self.running:
            
"""
            try:
            """"""
                if not self.config["analytics"]["enabled"]:
                    await asyncio.sleep(3600)
                    continue
            """

            try:
            

           
""""""
                # Collect analytics for each channel
                for channel in self.channels:
                    if channel.active:
                        await self._collect_channel_analytics(channel)

                # Update automation metrics
                await self._update_automation_metrics()

                await asyncio.sleep(self.config["analytics"]["tracking_interval"])

            except Exception as e:
                self.logger.error(f"Error in analytics loop: {e}")
                await asyncio.sleep(3600)

    async def _seo_optimization_loop(self):
        """
SEO optimization automation loop.

        while self.running:
            
"""
            try:
            """"""
                if not self.config["seo"]["enabled"]:
                    await asyncio.sleep(1800)
                    continue
            """

            try:
            

           
""""""
                # Optimize SEO for each channel
                for channel in self.channels:
                    if channel.active:
                        await self._optimize_channel_seo(channel)

                await asyncio.sleep(1800)  # 30 minutes

            except Exception as e:
                self.logger.error(f"Error in SEO optimization loop: {e}")
                await asyncio.sleep(1800)

    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status and metrics."""
        return {
            "status": self.status.value,
            "metrics": asdict(self.metrics),
            "channels": len(self.channels),
            "active_channels": len([c for c in self.channels if c.active]),
            "queue_sizes": {
                "content": self.content_queue.qsize(),
                "upload": self.upload_queue.qsize(),
                "engagement": self.engagement_queue.qsize(),
                "analytics": self.analytics_queue.qsize(),
             },
            "config": self.config,
         }

    async def create_manual_video(
        self, channel_id: str, topic: str, priority: str = "medium"
    ) -> Dict[str, Any]:
        """
Manually trigger video creation for specific topic.

        
"""
        try:
        """

            channel = next((c for c in self.channels if c.channel_id == channel_id), None)
        

        try:
        
""""""
        
       """
            if not channel:
                return {"success": False, "error": "Channel not found"}

            opportunity = {
                "topic": topic,
                "angle": f"Expert analysis of {topic}",
                "keywords": channel.keywords,
                "priority": priority,
             }

            project = await self._create_video_project(channel, opportunity)
            if project:
                video_result = await self._generate_video_content(project)
                if video_result:
                    await self._schedule_video_upload(channel, project, video_result, {})
                    return {"success": True, "project_id": project["id"]}

            return {"success": False, "error": "Failed to create video"}

        except Exception as e:
            self.logger.error(f"Error creating manual video: {e}")
            return {"success": False, "error": str(e)}

    # Helper methods (implementation details)

    async def _get_today_video_count(self, channel_id: str) -> int:
        """
Get number of videos created today for channel.

       
""""""

        # Implementation would query database
       

        
       
""""""

        return 0
        

       
""""""

        # Implementation would query database
       

        
       
"""
    async def _get_week_video_count(self, channel_id: str) -> int:
        """
Get number of videos created this week for channel.

       
""""""

        # Implementation would query database
       

        
       
""""""

        return 0
        

       
""""""

        # Implementation would query database
       

        
       
"""
    async def _has_breaking_news_opportunity(self, channel: YouTubeChannel) -> bool:
        """
Check if there are breaking news opportunities.

       
""""""

        # Implementation would check RSS feeds and news sources
       

        
       
""""""

        return False
        

       
""""""

        # Implementation would check RSS feeds and news sources
       

        
       
"""
    async def _has_trending_opportunity(self, channel: YouTubeChannel) -> bool:
        """
Check if there are trending topic opportunities.

       
""""""

        # Implementation would check trending APIs
       

        
       
""""""

        return False
        

       
""""""

        # Implementation would check trending APIs
       

        
       
"""
    async def _create_video_project(
        self, channel: YouTubeChannel, opportunity: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
Create video project from opportunity.

       
""""""

        # Implementation would create project structure
       

        
       
"""
        return {
            "id": f"project_{int(time.time())}",
            "channel_id": channel.channel_id,
            "title": opportunity["topic"],
            "status": "created",
         }
       """

        
       

        # Implementation would create project structure
       
""""""

    async def _generate_video_content(self, project: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        
Generate video content using Hollywood pipeline.
"""
        try:
           """

            
           

            # Use Hollywood pipeline for video generation
           
""""""

            result = self.hollywood_pipeline.generate_video(
           

            
           
"""
            # Use Hollywood pipeline for video generation
           """"""
                script_content=project["title"],
                title=project["title"],
                duration=300,  # 5 minutes
             )
            return result
        except Exception as e:
            self.logger.error(f"Error generating video content: {e}")
            return None

    async def _optimize_video_seo(
        self, project: Dict[str, Any], video_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
Optimize video for SEO.

       
""""""

        # Implementation would analyze keywords, trends, competitors
       

        
       
"""
        return {
            "optimized_title": project["title"],
            "optimized_description": f"Learn about {project['title']} in this comprehensive guide.",
            "optimized_tags": ["tutorial", "guide", "education"],
            "seo_score": 8.5,
         }
       """

        
       

        # Implementation would analyze keywords, trends, competitors
       
""""""

    async def _schedule_video_upload(
        self,
        channel: YouTubeChannel,
        project: Dict[str, Any],
        video_result: Dict[str, Any],
        seo_result: Dict[str, Any],
#     ):
        
Schedule video for upload.
"""
        # Implementation would add to upload queue with optimal timing
       """

        
       

        pass
       
""""""

    async def _process_upload_queue(self):
        """
        Process videos ready for upload.
        """
        # Implementation would upload videos using YouTube integration
       """

        
       

        pass
       
""""""

       

        
       
"""
        pass
       """

        
       

    async def _optimize_channel_schedule(self, channel: YouTubeChannel):
        
"""Optimize upload schedule for channel."""

        # Implementation would analyze best posting times
       

        
       
"""
        pass
       """

        
       

    async def _process_channel_engagement(self, channel: YouTubeChannel):
        
"""Process engagement for channel using engagement agent."""
        try:
            # Use existing engagement agent
            await self.engagement_agent.process_engagement_batch()
            self.metrics.comments_replied += 5  # Example increment
        except Exception as e:
            self.logger.error(f"Error processing engagement: {e}")
       """

        
       

        pass
       
""""""

    async def _collect_channel_analytics(self, channel: YouTubeChannel):
        
Collect analytics for channel.
"""
        try:
           """

            
           

            # Use YouTube integration for analytics
           
""""""

            analytics = self.youtube_integration.get_channel_analytics()
           

            
           
"""
            # Use YouTube integration for analytics
           """"""
            if analytics:
                self.metrics.total_views += analytics.view_count
                self.metrics.total_subscribers += analytics.subscriber_count
        except Exception as e:
            self.logger.error(f"Error collecting analytics: {e}")

    async def _update_automation_metrics(self):
        """
Update overall automation metrics.

        self.metrics.last_updated = datetime.now()
       
""""""

        # Calculate automation efficiency
       

        
       
"""
        if self.metrics.videos_created > 0:
            self.metrics.automation_efficiency = (
                self.metrics.videos_uploaded / self.metrics.videos_created
"""

#             ) * 100


       
""""""

        # Calculate automation efficiency
       

        
       
"""
    async def _optimize_channel_seo(self, channel: YouTubeChannel):
        """
Optimize SEO for channel.

        # Implementation would analyze and optimize SEO
       
""""""

        pass
       

        
       
"""
    async def _get_trending_topics(self, niche: str) -> List[Dict[str, Any]]:
        """
Get trending topics for niche.

       
""""""

        # Implementation would fetch trending topics
       

        
       
""""""

        
       

        pass
       
""""""
        return [{"topic": f"Latest {niche} trends", "keywords": [niche, "trends", "2024"]}]


# Factory function


def create_youtube_automation() -> YouTubeAutomationOrchestrator:
    """
Create and return YouTube automation orchestrator instance.

    
"""
    return YouTubeAutomationOrchestrator()
    """"""
    """


    return YouTubeAutomationOrchestrator()

    

   
""""""
# CLI interface for testing
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Automation Orchestrator")
    parser.add_argument("--start", action="store_true", help="Start automation")
    parser.add_argument("--stop", action="store_true", help="Stop automation")
    parser.add_argument("--status", action="store_true", help="Get status")

    args = parser.parse_args()

    orchestrator = create_youtube_automation()

    if args.start:
        asyncio.run(orchestrator.start_automation())
    elif args.stop:
        asyncio.run(orchestrator.stop_automation())
    elif args.status:
        status = orchestrator.get_automation_status()
        print(json.dumps(status, indent=2, default=str))
    else:
        print("Use --start, --stop, or --status")