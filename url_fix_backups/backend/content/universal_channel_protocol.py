#!/usr / bin / env python3
"""
Universal Channel Protocol System

Implements the "Can't - Fail" template for all channels with:
1. Topic - Specific Intelligence Feeds
2. Dedicated Knowledge Bases
3. Unique Channel Personas
4. Universal Relentless Optimization
5. Right Perspective Content Firewall
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set


class ChannelType(Enum):
    TECH = "tech"
    WELLNESS = "wellness"
    FINANCE = "finance"
    LIFESTYLE = "lifestyle"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    POLITICAL = "political"  # Reserved for Right Perspective
    BUSINESS = "business"
    SCIENCE = "science"
    SPORTS = "sports"


class ContentFirewallLevel(Enum):
    NONE = "none"
    STANDARD = "standard"
    STRICT = "strict"  # For Right Perspective
    ABSOLUTE = "absolute"  # Maximum isolation


@dataclass
class ChannelConfig:
    """Configuration for a channel in the Universal Protocol"""

    channel_id: str
    channel_name: str
    channel_type: ChannelType
    persona_id: str
    rss_feeds: List[str]
    knowledge_base_tables: List[str]
    firewall_level: ContentFirewallLevel
    optimization_enabled: bool = True
    cross_promotion_allowed: bool = True
    asset_sharing_allowed: bool = True
    content_repurposing_allowed: bool = True
    created_at: datetime = None
    updated_at: datetime = None


class UniversalChannelProtocol:
    """
    Core system for managing all channels with standardized success strategies
    """

    def __init__(self, db_path: str = "data / right_perspective.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.channels: Dict[str, ChannelConfig] = {}
        self.firewall_rules: Dict[str, Set[str]] = {}
        self._initialize_protocol()

    def _initialize_protocol(self):
        """Initialize the Universal Channel Protocol system"""
        self._create_protocol_tables()
        self._load_existing_channels()
        self._initialize_right_perspective_firewall()
        self.logger.info("Universal Channel Protocol initialized")

    def _create_protocol_tables(self):
        """Create database tables for the Universal Channel Protocol"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Channel configurations table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL UNIQUE,
                        channel_name TEXT NOT NULL,
                        channel_type TEXT NOT NULL,
                        persona_id TEXT NOT NULL,
                        rss_feeds TEXT NOT NULL, -- JSON array
                    knowledge_base_tables TEXT NOT NULL, -- JSON array
                    firewall_level TEXT NOT NULL DEFAULT 'standard',
                        optimization_enabled BOOLEAN DEFAULT 1,
                        cross_promotion_allowed BOOLEAN DEFAULT 1,
                        asset_sharing_allowed BOOLEAN DEFAULT 1,
                        content_repurposing_allowed BOOLEAN DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # RSS feed monitoring table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_rss_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        feed_url TEXT NOT NULL,
                        feed_title TEXT,
                        feed_description TEXT,
                        last_checked TIMESTAMP,
                        last_updated TIMESTAMP,
                        status TEXT DEFAULT 'active', -- active, inactive, error
                        error_count INTEGER DEFAULT 0,
                        last_error TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channel_configs (channel_id)
                )
            """
            )

            # Channel - specific knowledge base entries
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        entry_type TEXT NOT NULL, -- fact, quote, statistic, study, review
                    title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_url TEXT,
                        source_credibility REAL DEFAULT 0.5, -- 0 - 1 credibility score
                    relevance_score REAL DEFAULT 0.5, -- 0 - 1 relevance to channel
                    tags TEXT, -- JSON array of tags
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channel_configs (channel_id)
                )
            """
            )

            # Enhanced author personas for channels
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_personas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        persona_id TEXT NOT NULL UNIQUE,
                        channel_id TEXT NOT NULL,
                        persona_name TEXT NOT NULL,
                        writing_style TEXT NOT NULL,
                        tone_attributes TEXT NOT NULL, -- JSON array
                    vocabulary_level TEXT DEFAULT 'intermediate',
                        humor_style TEXT,
                        expertise_areas TEXT, -- JSON array
                    target_audience TEXT,
                        voice_characteristics TEXT, -- JSON object
                    content_preferences TEXT, -- JSON object
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channel_configs (channel_id)
                )
            """
            )

            # Content firewall rules
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS content_firewall_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        source_channel_id TEXT NOT NULL,
                        target_channel_id TEXT NOT NULL,
                        rule_type TEXT NOT NULL, -- cross_promotion, asset_sharing, content_repurposing
                    action TEXT NOT NULL, -- allow, deny, require_approval
                    reason TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (source_channel_id) REFERENCES channel_configs (channel_id),
                        FOREIGN KEY (target_channel_id) REFERENCES channel_configs (channel_id)
                )
            """
            )

            # Optimization tracking per channel
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS channel_optimization_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel_id TEXT NOT NULL,
                        video_id TEXT NOT NULL,
                        optimization_type TEXT NOT NULL, -- thumbnail, title, description
                    variant_a TEXT NOT NULL,
                        variant_b TEXT NOT NULL,
                        winner TEXT, -- a, b, inconclusive
                    confidence_score REAL,
                        test_duration_hours INTEGER,
                        views_a INTEGER DEFAULT 0,
                        views_b INTEGER DEFAULT 0,
                        ctr_a REAL DEFAULT 0.0,
                        ctr_b REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed_at TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channel_configs (channel_id)
                )
            """
            )

            conn.commit()

    def _load_existing_channels(self):
        """Load existing channel configurations from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM channel_configs")

            for row in cursor.fetchall():
                config = ChannelConfig(
                    channel_id=row[1],
                    channel_name=row[2],
                    channel_type=ChannelType(row[3]),
                    persona_id=row[4],
                    rss_feeds=json.loads(row[5]),
                    knowledge_base_tables=json.loads(row[6]),
                    firewall_level=ContentFirewallLevel(row[7]),
                    optimization_enabled=bool(row[8]),
                    cross_promotion_allowed=bool(row[9]),
                    asset_sharing_allowed=bool(row[10]),
                    content_repurposing_allowed=bool(row[11]),
                    created_at=datetime.fromisoformat(row[12]),
                    updated_at=datetime.fromisoformat(row[13]),
                )
                self.channels[config.channel_id] = config

    def _initialize_right_perspective_firewall(self):
        """Initialize strict firewall rules for Right Perspective channel"""
        right_perspective_id = "right_perspective"

        # Create Right Perspective channel if it doesn't exist
        if right_perspective_id not in self.channels:
            self.create_channel(
                channel_id=right_perspective_id,
                channel_name="The Right Perspective",
                channel_type=ChannelType.POLITICAL,
                persona_config={
                    "persona_name": "Conservative Commentator",
                    "writing_style": "Witty, sarcastic, satirical political commentary",
                    "tone_attributes": [
                        "sarcastic",
                        "witty",
                        "authoritative",
                        "provocative",
                    ],
                    "humor_style": "political_satire",
                    "expertise_areas": [
                        "politics",
                        "current_events",
                        "conservative_ideology",
                    ],
                },
                rss_feeds=[
                    "https://feeds.feedburner.com / breitbart",
                    "https://www.dailywire.com / feeds / rss.xml",
                    "https://townhall.com / feeds / rss",
                ],
                firewall_level=ContentFirewallLevel.STRICT,
            )

        # Set strict firewall rules
        self._set_firewall_rules(
            right_perspective_id,
            {
                "cross_promotion_allowed": False,
                "asset_sharing_allowed": False,
                "content_repurposing_allowed": False,
            },
        )

        # Initialize the firewall instance after protocol is ready
        try:
            from .right_perspective_firewall import RightPerspectiveFirewall

            self._right_perspective_firewall = RightPerspectiveFirewall(protocol=self)
        except Exception as e:
            self.logger.error(f"Failed to initialize Right Perspective Firewall: {e}")
            self._right_perspective_firewall = None

    def create_channel(
        self,
        channel_id: str,
        channel_name: str,
        channel_type: ChannelType,
        persona_config: Dict[str, Any],
        rss_feeds: List[str],
        firewall_level: ContentFirewallLevel = ContentFirewallLevel.STANDARD,
    ) -> ChannelConfig:
        """Create a new channel with the Universal Protocol template"""

        # Generate persona ID
        persona_id = f"{channel_id}_persona"

        # Determine knowledge base tables based on channel type
        knowledge_base_tables = self._get_knowledge_base_tables(channel_type)

        # Create channel configuration
        config = ChannelConfig(
            channel_id=channel_id,
            channel_name=channel_name,
            channel_type=channel_type,
            persona_id=persona_id,
            rss_feeds=rss_feeds,
            knowledge_base_tables=knowledge_base_tables,
            firewall_level=firewall_level,
            optimization_enabled=True,
            cross_promotion_allowed=(firewall_level != ContentFirewallLevel.STRICT),
            asset_sharing_allowed=(firewall_level != ContentFirewallLevel.STRICT),
            content_repurposing_allowed=(firewall_level != ContentFirewallLevel.STRICT),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

        # Save to database
        self._save_channel_config(config)
        self._create_channel_persona(persona_id, channel_id, persona_config)
        self._setup_channel_rss_feeds(channel_id, rss_feeds)
        self._create_channel_knowledge_tables(channel_id, knowledge_base_tables)

        # Store in memory
        self.channels[channel_id] = config

        self.logger.info(f"Created channel '{channel_name}' with Universal Protocol template")
        return config

    def _get_knowledge_base_tables(self, channel_type: ChannelType) -> List[str]:
        """Get appropriate knowledge base table names for channel type"""
        base_tables = ["general_facts", "expert_quotes", "statistics"]

        type_specific_tables = {
            ChannelType.TECH: ["tech_specs", "product_reviews", "innovation_trends"],
            ChannelType.WELLNESS: [
                "health_studies",
                "nutrition_facts",
                "fitness_research",
            ],
            ChannelType.FINANCE: [
                "market_data",
                "economic_indicators",
                "investment_analysis",
            ],
            ChannelType.POLITICAL: [
                "political_facts",
                "voting_records",
                "policy_analysis",
            ],
            ChannelType.BUSINESS: [
                "business_metrics",
                "industry_reports",
                "company_profiles",
            ],
            ChannelType.SCIENCE: [
                "research_papers",
                "scientific_studies",
                "discovery_news",
            ],
            ChannelType.LIFESTYLE: [
                "trend_analysis",
                "consumer_behavior",
                "cultural_insights",
            ],
            ChannelType.EDUCATION: [
                "academic_research",
                "learning_methodologies",
                "educational_stats",
            ],
            ChannelType.ENTERTAINMENT: [
                "industry_news",
                "box_office_data",
                "celebrity_facts",
            ],
            ChannelType.SPORTS: [
                "player_stats",
                "team_performance",
                "sports_analytics",
            ],
        }

        return base_tables + type_specific_tables.get(channel_type, [])

    def _save_channel_config(self, config: ChannelConfig):
        """Save channel configuration to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO channel_configs
                (channel_id, channel_name, channel_type, persona_id, rss_feeds,
                    knowledge_base_tables, firewall_level, optimization_enabled,
                     cross_promotion_allowed, asset_sharing_allowed, content_repurposing_allowed,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    config.channel_id,
                    config.channel_name,
                    config.channel_type.value,
                    config.persona_id,
                    json.dumps(config.rss_feeds),
                    json.dumps(config.knowledge_base_tables),
                    config.firewall_level.value,
                    config.optimization_enabled,
                    config.cross_promotion_allowed,
                    config.asset_sharing_allowed,
                    config.content_repurposing_allowed,
                    config.created_at.isoformat(),
                    config.updated_at.isoformat(),
                ),
            )
            conn.commit()

    def _create_channel_persona(
        self, persona_id: str, channel_id: str, persona_config: Dict[str, Any]
    ):
        """Create persona for the channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO channel_personas
                (persona_id, channel_id, persona_name, writing_style, tone_attributes,
                    vocabulary_level, humor_style, expertise_areas, target_audience,
                     voice_characteristics, content_preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    persona_id,
                    channel_id,
                    persona_config.get("persona_name", "Default Persona"),
                    persona_config.get(
                        "writing_style",
                        "Professional \
    and engaging",
                    ),
                    json.dumps(persona_config.get("tone_attributes", ["informative", "friendly"])),
                    persona_config.get("vocabulary_level", "intermediate"),
                    persona_config.get("humor_style", "light"),
                    json.dumps(persona_config.get("expertise_areas", [])),
                    persona_config.get("target_audience", "General audience"),
                    json.dumps(persona_config.get("voice_characteristics", {})),
                    json.dumps(persona_config.get("content_preferences", {})),
                ),
            )
            conn.commit()

    def _setup_channel_rss_feeds(self, channel_id: str, rss_feeds: List[str]):
        """Setup RSS feed monitoring for the channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for feed_url in rss_feeds:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO channel_rss_feeds
                    (channel_id, feed_url, status)
                    VALUES (?, ?, 'active')
                """,
                    (channel_id, feed_url),
                )

            conn.commit()

    def _create_channel_knowledge_tables(self, channel_id: str, table_names: List[str]):
        """Create knowledge base table entries for the channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for table_name in table_names:
                # Create a placeholder entry to establish the table relationship
                cursor.execute(
                    """
                    INSERT INTO channel_knowledge_base
                    (channel_id, table_name, entry_type, title, content, source_url)
                    VALUES (?, ?, 'system', 'Knowledge Base Initialized',
                        'This knowledge base has been initialized for the channel.', '')
                """,
                    (channel_id, table_name),
                )

            conn.commit()

    def _set_firewall_rules(self, channel_id: str, rules: Dict[str, bool]):
        """Set firewall rules for a channel"""
        config = self.channels.get(channel_id)
        if not config:
            return

        config.cross_promotion_allowed = rules.get("cross_promotion_allowed", True)
        config.asset_sharing_allowed = rules.get("asset_sharing_allowed", True)
        config.content_repurposing_allowed = rules.get("content_repurposing_allowed", True)
        config.updated_at = datetime.now()

        self._save_channel_config(config)

    def check_content_firewall(
        self, source_channel_id: str, target_channel_id: str, action_type: str
    ) -> bool:
        """Check if an action is allowed between channels based on firewall rules"""
        source_config = self.channels.get(source_channel_id)
        target_config = self.channels.get(target_channel_id)

        if not source_config or not target_config:
            return False

        # Right Perspective firewall - absolute isolation
        if source_channel_id == "right_perspective" or target_channel_id == "right_perspective":
            if action_type == "cross_promotion":
                return False
            elif action_type == "asset_sharing":
                return False
            elif action_type == "content_repurposing":
                return False

        # Check source channel permissions
        if action_type == "cross_promotion" and not source_config.cross_promotion_allowed:
            return False
        elif action_type == "asset_sharing" and not source_config.asset_sharing_allowed:
            return False
        elif action_type == "content_repurposing" and not source_config.content_repurposing_allowed:
            return False

        return True

    def get_channel_persona(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get the persona configuration for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM channel_personas WHERE channel_id = ?
            """,
                (channel_id,),
            )

            row = cursor.fetchone()
            if row:
                return {
                    "persona_id": row[1],
                    "channel_id": row[2],
                    "persona_name": row[3],
                    "writing_style": row[4],
                    "tone_attributes": json.loads(row[5]),
                    "vocabulary_level": row[6],
                    "humor_style": row[7],
                    "expertise_areas": json.loads(row[8]),
                    "target_audience": row[9],
                    "voice_characteristics": json.loads(row[10]),
                    "content_preferences": json.loads(row[11]),
                }
        return None

    def get_channel_knowledge_base(
        self, channel_id: str, entry_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get knowledge base entries for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if entry_type:
                cursor.execute(
                    """
                    SELECT * FROM channel_knowledge_base
                    WHERE channel_id = ? AND entry_type = ?
                    ORDER BY relevance_score DESC, created_at DESC
                """,
                    (channel_id, entry_type),
                )
            else:
                cursor.execute(
                    """
                    SELECT * FROM channel_knowledge_base
                    WHERE channel_id = ?
                    ORDER BY relevance_score DESC, created_at DESC
                """,
                    (channel_id,),
                )

            entries = []
            for row in cursor.fetchall():
                entries.append(
                    {
                        "id": row[0],
                        "channel_id": row[1],
                        "table_name": row[2],
                        "entry_type": row[3],
                        "title": row[4],
                        "content": row[5],
                        "source_url": row[6],
                        "source_credibility": row[7],
                        "relevance_score": row[8],
                        "tags": json.loads(row[9]) if row[9] else [],
                        "created_at": row[10],
                        "updated_at": row[11],
                    }
                )

            return entries

    def add_knowledge_entry(
        self,
        channel_id: str,
        table_name: str,
        entry_type: str,
        title: str,
        content: str,
        source_url: str = "",
        credibility: float = 0.5,
        relevance: float = 0.5,
        tags: List[str] = None,
    ) -> bool:
        """Add a knowledge base entry for a channel"""
        if channel_id not in self.channels:
            return False

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO channel_knowledge_base
                (channel_id, table_name, entry_type, title, content, source_url,
                    source_credibility, relevance_score, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    channel_id,
                    table_name,
                    entry_type,
                    title,
                    content,
                    source_url,
                    credibility,
                    relevance,
                    json.dumps(tags or []),
                ),
            )
            conn.commit()

        return True

    def get_channel_rss_feeds(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get RSS feeds for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM channel_rss_feeds WHERE channel_id = ?
            """,
                (channel_id,),
            )

            feeds = []
            for row in cursor.fetchall():
                feeds.append(
                    {
                        "id": row[0],
                        "channel_id": row[1],
                        "feed_url": row[2],
                        "feed_title": row[3],
                        "feed_description": row[4],
                        "last_checked": row[5],
                        "last_updated": row[6],
                        "status": row[7],
                        "error_count": row[8],
                        "last_error": row[9],
                        "created_at": row[10],
                    }
                )

            return feeds

    def start_optimization_test(
        self,
        channel_id: str,
        video_id: str,
        optimization_type: str,
        variant_a: str,
        variant_b: str,
    ) -> str:
        """Start an A / B optimization test for a channel"""
        if channel_id not in self.channels:
            return None

        config = self.channels[channel_id]
        if not config.optimization_enabled:
            return None

        test_id = f"{channel_id}_{video_id}_{optimization_type}_{int(time.time())}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO channel_optimization_log
                (channel_id, video_id, optimization_type, variant_a, variant_b)
                VALUES (?, ?, ?, ?, ?)
            """,
                (channel_id, video_id, optimization_type, variant_a, variant_b),
            )
            conn.commit()

        self.logger.info(
            f"Started {optimization_type} optimization test for {channel_id}: {test_id}"
        )
        return test_id

    def get_all_channels(self) -> Dict[str, ChannelConfig]:
        """Get all channel configurations"""
        return self.channels.copy()

    def get_right_perspective_firewall(self):
        """Get the Right Perspective Firewall instance"""
        return getattr(self, "_right_perspective_firewall", None)

    def get_channel_config(self, channel_id: str) -> Optional[ChannelConfig]:
        """Get configuration for a specific channel"""
        return self.channels.get(channel_id)

    def update_channel_config(self, channel_id: str, updates: Dict[str, Any]) -> bool:
        """Update channel configuration"""
        if channel_id not in self.channels:
            return False

        config = self.channels[channel_id]

        # Update allowed fields
        if "rss_feeds" in updates:
            config.rss_feeds = updates["rss_feeds"]
        if "optimization_enabled" in updates:
            config.optimization_enabled = updates["optimization_enabled"]

        # Don't allow firewall changes for Right Perspective
        if channel_id != "right_perspective":
            if "cross_promotion_allowed" in updates:
                config.cross_promotion_allowed = updates["cross_promotion_allowed"]
            if "asset_sharing_allowed" in updates:
                config.asset_sharing_allowed = updates["asset_sharing_allowed"]
            if "content_repurposing_allowed" in updates:
                config.content_repurposing_allowed = updates["content_repurposing_allowed"]

        config.updated_at = datetime.now()
        self._save_channel_config(config)

        return True


# Global instance
protocol = UniversalChannelProtocol()


def get_protocol() -> UniversalChannelProtocol:
    """Get the global Universal Channel Protocol instance"""
    return protocol
