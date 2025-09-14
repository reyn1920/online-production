#!/usr/bin/env python3
"""
Dedicated Knowledge Bases System

Creates \
    and manages channel - specific database tables for evidence - based content creation.
Each channel gets its own set of specialized tables based on its topic area.
"""

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List

try:
    from .universal_channel_protocol import ChannelType, get_protocol

except ImportError:
    # Fallback for development

    import os
    import sys

    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from universal_channel_protocol import ChannelType, get_protocol


class KnowledgeEntryType(Enum):
    FACT = "fact"
    STATISTIC = "statistic"
    QUOTE = "quote"
    STUDY = "study"
    CASE_STUDY = "case_study"
    EXAMPLE = "example"
    DEFINITION = "definition"
    TREND = "trend"
    PREDICTION = "prediction"
    ANALYSIS = "analysis"


@dataclass
class KnowledgeEntry:
    """Represents a knowledge base entry"""

    entry_id: str
    channel_id: str
    entry_type: KnowledgeEntryType
    title: str
    content: str
    source: str
    credibility_score: float
    relevance_score: float
    tags: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DedicatedKnowledgeBases:
    """
    Manages channel - specific knowledge base tables and content
    """

    def __init__(self, db_path: str = "data/right_perspective.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.protocol = get_protocol()
        self.table_schemas = self._initialize_table_schemas()
        self._ensure_base_tables()

    def _initialize_table_schemas(self) -> Dict[ChannelType, Dict[str, str]]:
        """Initialize table schemas for different channel types"""
        return {
            ChannelType.TECH: {
                "tech_specs": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_tech_specs (
                        spec_id TEXT PRIMARY KEY,
                            product_name TEXT NOT NULL,
                            category TEXT NOT NULL,
                            specifications TEXT NOT NULL,
                            performance_metrics TEXT,
                            price_range TEXT,
                            release_date TEXT,
                            manufacturer TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            source_url TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "product_reviews": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_product_reviews (
                        review_id TEXT PRIMARY KEY,
                            product_name TEXT NOT NULL,
                            reviewer_name TEXT,
                            rating REAL,
                            review_summary TEXT,
                            pros TEXT,
                            cons TEXT,
                            verdict TEXT,
                            review_date TEXT,
                            source_publication TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "tech_trends": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_tech_trends (
                        trend_id TEXT PRIMARY KEY,
                            trend_name TEXT NOT NULL,
                            description TEXT,
                            impact_level TEXT,
                            adoption_rate TEXT,
                            key_players TEXT,
                            market_size TEXT,
                            predictions TEXT,
                            source_analysis TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
            ChannelType.WELLNESS: {
                "health_studies": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_health_studies (
                        study_id TEXT PRIMARY KEY,
                            study_title TEXT NOT NULL,
                            researchers TEXT,
                            institution TEXT,
                            study_type TEXT,
                            sample_size INTEGER,
                            duration TEXT,
                            key_findings TEXT,
                            methodology TEXT,
                            limitations TEXT,
                            publication_journal TEXT,
                            publication_date TEXT,
                            doi TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "expert_quotes": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_expert_quotes (
                        quote_id TEXT PRIMARY KEY,
                            expert_name TEXT NOT NULL,
                            credentials TEXT,
                            institution TEXT,
                            quote_text TEXT NOT NULL,
                            context TEXT,
                            topic_area TEXT,
                            source_interview TEXT,
                            quote_date TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "wellness_tips": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_wellness_tips (
                        tip_id TEXT PRIMARY KEY,
                            category TEXT NOT NULL,
                            tip_title TEXT NOT NULL,
                            tip_content TEXT NOT NULL,
                            scientific_backing TEXT,
                            difficulty_level TEXT,
                            time_commitment TEXT,
                            expected_benefits TEXT,
                            precautions TEXT,
                            expert_source TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
            ChannelType.FINANCE: {
                "market_data": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_market_data (
                        data_id TEXT PRIMARY KEY,
                            asset_type TEXT NOT NULL,
                            asset_name TEXT NOT NULL,
                            current_price REAL,
                            price_change REAL,
                            volume REAL,
                            market_cap REAL,
                            pe_ratio REAL,
                            dividend_yield REAL,
                            analyst_rating TEXT,
                            data_date TEXT,
                            data_source TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "economic_indicators": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_economic_indicators (
                        indicator_id TEXT PRIMARY KEY,
                            indicator_name TEXT NOT NULL,
                            current_value REAL,
                            previous_value REAL,
                            change_percentage REAL,
                            reporting_period TEXT,
                            reporting_agency TEXT,
                            significance TEXT,
                            market_impact TEXT,
                            historical_context TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "investment_strategies": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_investment_strategies (
                        strategy_id TEXT PRIMARY KEY,
                            strategy_name TEXT NOT NULL,
                            description TEXT,
                            risk_level TEXT,
                            time_horizon TEXT,
                            expected_returns TEXT,
                            asset_allocation TEXT,
                            pros TEXT,
                            cons TEXT,
                            expert_opinion TEXT,
                            case_studies TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
            ChannelType.POLITICAL: {
                "political_facts": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_political_facts (
                        fact_id TEXT PRIMARY KEY,
                            claim TEXT NOT NULL,
                            fact_check_result TEXT NOT NULL,
                            evidence TEXT,
                            sources TEXT,
                            fact_checker TEXT,
                            politician_or_entity TEXT,
                            statement_date TEXT,
                            context TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "policy_analysis": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_policy_analysis (
                        analysis_id TEXT PRIMARY KEY,
                            policy_name TEXT NOT NULL,
                            policy_description TEXT,
                            proposed_by TEXT,
                            support_arguments TEXT,
                            opposition_arguments TEXT,
                            economic_impact TEXT,
                            social_impact TEXT,
                            expert_opinions TEXT,
                            historical_precedents TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "voting_records": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_voting_records (
                        record_id TEXT PRIMARY KEY,
                            politician_name TEXT NOT NULL,
                            bill_name TEXT NOT NULL,
                            vote TEXT NOT NULL,
                            bill_description TEXT,
                            vote_date TEXT,
                            party_affiliation TEXT,
                            constituency TEXT,
                            bill_outcome TEXT,
                            significance TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
            ChannelType.BUSINESS: {
                "company_profiles": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_company_profiles (
                        profile_id TEXT PRIMARY KEY,
                            company_name TEXT NOT NULL,
                            industry TEXT,
                            founded_year INTEGER,
                            headquarters TEXT,
                            ceo TEXT,
                            employee_count INTEGER,
                            revenue TEXT,
                            market_cap TEXT,
                            business_model TEXT,
                            key_products TEXT,
                            competitive_advantages TEXT,
                            recent_news TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "business_strategies": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_business_strategies (
                        strategy_id TEXT PRIMARY KEY,
                            strategy_name TEXT NOT NULL,
                            description TEXT,
                            industry_application TEXT,
                            success_factors TEXT,
                            implementation_steps TEXT,
                            case_studies TEXT,
                            expert_insights TEXT,
                            potential_pitfalls TEXT,
                            roi_expectations TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "market_insights": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_market_insights (
                        insight_id TEXT PRIMARY KEY,
                            market_segment TEXT NOT NULL,
                            insight_title TEXT NOT NULL,
                            insight_description TEXT,
                            market_size TEXT,
                            growth_rate TEXT,
                            key_trends TEXT,
                            opportunities TEXT,
                            challenges TEXT,
                            key_players TEXT,
                            data_sources TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
            ChannelType.SCIENCE: {
                "research_papers": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_research_papers (
                        paper_id TEXT PRIMARY KEY,
                            title TEXT NOT NULL,
                            authors TEXT,
                            journal TEXT,
                            publication_date TEXT,
                            doi TEXT,
                            abstract TEXT,
                            key_findings TEXT,
                            methodology TEXT,
                            significance TEXT,
                            field_of_study TEXT,
                            citation_count INTEGER,
                            peer_reviewed BOOLEAN,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "scientific_discoveries": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_scientific_discoveries (
                        discovery_id TEXT PRIMARY KEY,
                            discovery_name TEXT NOT NULL,
                            field TEXT,
                            researchers TEXT,
                            institution TEXT,
                            discovery_date TEXT,
                            description TEXT,
                            implications TEXT,
                            applications TEXT,
                            future_research TEXT,
                            media_coverage TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
                "expert_profiles": """
                    CREATE TABLE IF NOT EXISTS {channel_id}_expert_profiles (
                        expert_id TEXT PRIMARY KEY,
                            name TEXT NOT NULL,
                            field_of_expertise TEXT,
                            institution TEXT,
                            credentials TEXT,
                            notable_work TEXT,
                            publications TEXT,
                            awards TEXT,
                            current_research TEXT,
                            contact_info TEXT,
                            credibility_score REAL DEFAULT 0.0,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """,
            },
        }

    def _ensure_base_tables(self):
        """Ensure base knowledge management tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Knowledge entries master table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_entries (
                    entry_id TEXT PRIMARY KEY,
                        channel_id TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        entry_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source TEXT,
                        credibility_score REAL DEFAULT 0.0,
                        relevance_score REAL DEFAULT 0.0,
                        tags TEXT,
                        metadata TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                )
            """
            )

            # Knowledge usage tracking
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_usage (
                    usage_id TEXT PRIMARY KEY,
                        entry_id TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        content_id TEXT,
                        usage_context TEXT,
                        effectiveness_score REAL,
                        used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (entry_id) REFERENCES knowledge_entries (entry_id),
                        FOREIGN KEY (channel_id) REFERENCES channels (channel_id)
                )
            """
            )

            # Knowledge source tracking
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS knowledge_sources (
                    source_id TEXT PRIMARY KEY,
                        source_name TEXT NOT NULL,
                        source_type TEXT NOT NULL,
                        base_url TEXT,
                        credibility_rating REAL DEFAULT 0.0,
                        last_accessed TIMESTAMP,
                        access_frequency INTEGER DEFAULT 0,
                        quality_metrics TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.commit()

    def create_channel_knowledge_tables(self, channel_id: str) -> bool:
        """Create knowledge base tables for a specific channel"""
        config = self.protocol.get_channel_config(channel_id)
        if not config:
            self.logger.error(f"Channel {channel_id} not found")
            return False

        channel_type = config.channel_type
        if channel_type not in self.table_schemas:
            self.logger.warning(f"No schema defined for channel type {channel_type}")
            return False

        schemas = self.table_schemas[channel_type]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            try:
                for table_name, schema in schemas.items():
                    # Replace placeholder with actual channel_id
                    formatted_schema = schema.format(channel_id=channel_id)
                    cursor.execute(formatted_schema)

                    self.logger.info(f"Created table {channel_id}_{table_name}")

                conn.commit()
                return True

            except sqlite3.Error as e:
                self.logger.error(f"Error creating tables for {channel_id}: {e}")
                conn.rollback()
                return False

    def add_knowledge_entry(
        self, channel_id: str, table_name: str, entry_data: Dict[str, Any]
    ) -> str:
        """Add a knowledge entry to a channel's specific table"""
        config = self.protocol.get_channel_config(channel_id)
        if not config:
            raise ValueError(f"Channel {channel_id} not found")

        # Generate entry ID
        entry_id = f"{channel_id}_{table_name}_{datetime.now().strftime('%Y % m%d_ % H%M % S')}_{hash(str(entry_data)) % 10000}"

        # Add to specific table
        full_table_name = f"{channel_id}_{table_name}"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """,
                (full_table_name,),
            )

            if not cursor.fetchone():
                # Create tables if they don't exist
                self.create_channel_knowledge_tables(channel_id)

            # Prepare data for insertion
            columns = list(entry_data.keys())
            if "created_at" not in columns:
                entry_data["created_at"] = datetime.now().isoformat()
            if "updated_at" not in columns:
                entry_data["updated_at"] = datetime.now().isoformat()

            # Add primary key if not present
            primary_key_field = self._get_primary_key_field(table_name)
            if primary_key_field not in entry_data:
                entry_data[primary_key_field] = entry_id

            columns = list(entry_data.keys())
            placeholders = ", ".join(["?" for _ in columns])
            values = [entry_data[col] for col in columns]

            # Insert into specific table
            insert_query = f"INSERT OR REPLACE INTO {full_table_name} ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(insert_query, values)

            # Also add to master knowledge_entries table
            cursor.execute(
                """
                INSERT OR REPLACE INTO knowledge_entries
                (entry_id, channel_id, table_name, entry_type, title, content, source,
                    credibility_score, relevance_score, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry_id,
                    channel_id,
                    table_name,
                    entry_data.get("entry_type", "general"),
                    entry_data.get("title", entry_data.get("name", "Untitled")),
                    str(entry_data.get("content", entry_data.get("description", ""))),
                    entry_data.get("source", entry_data.get("source_url", "")),
                    entry_data.get("credibility_score", 0.0),
                    entry_data.get("relevance_score", 0.0),
                    json.dumps(entry_data.get("tags", [])),
                    json.dumps(
                        {
                            k: v
                            for k, v in entry_data.items()
                            if k not in ["title", "content", "source"]
                        }
                    ),
                    entry_data["created_at"],
                    entry_data["updated_at"],
                ),
            )

            conn.commit()

        return entry_id

    def _get_primary_key_field(self, table_name: str) -> str:
        """Get the primary key field name for a table type"""
        primary_key_map = {
            "tech_specs": "spec_id",
            "product_reviews": "review_id",
            "tech_trends": "trend_id",
            "health_studies": "study_id",
            "expert_quotes": "quote_id",
            "wellness_tips": "tip_id",
            "market_data": "data_id",
            "economic_indicators": "indicator_id",
            "investment_strategies": "strategy_id",
            "political_facts": "fact_id",
            "policy_analysis": "analysis_id",
            "voting_records": "record_id",
            "company_profiles": "profile_id",
            "business_strategies": "strategy_id",
            "market_insights": "insight_id",
            "research_papers": "paper_id",
            "scientific_discoveries": "discovery_id",
            "expert_profiles": "expert_id",
        }
        return primary_key_map.get(table_name, "entry_id")

    def get_knowledge_entries(
        self,
        channel_id: str,
        table_name: str = None,
        entry_type: str = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Get knowledge entries for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = "SELECT * FROM knowledge_entries WHERE channel_id = ?"
            params = [channel_id]

            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)

            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)

            query += " ORDER BY credibility_score DESC, created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            entries = []
            for row in rows:
                entry = dict(row)
                entry["tags"] = json.loads(entry.get("tags", "[]"))
                entry["metadata"] = json.loads(entry.get("metadata", "{}"))
                entries.append(entry)

            return entries

    def search_knowledge_base(
        self,
        channel_id: str,
        search_term: str,
        table_name: str = None,
        min_credibility: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Search knowledge base for relevant entries"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
                SELECT *,
                    (CASE
                        WHEN title LIKE ? THEN 3
                        WHEN content LIKE ? THEN 2
                        WHEN tags LIKE ? THEN 1
                        ELSE 0
                       END) as search_relevance
                FROM knowledge_entries
                WHERE channel_id = ?
                  AND credibility_score >= ?
                  AND (title LIKE ? OR content LIKE ? OR tags LIKE ?)
            """

            params = [
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%",  # For relevance scoring
                channel_id,
                min_credibility,
                f"%{search_term}%",
                f"%{search_term}%",
                f"%{search_term}%",  # For filtering
            ]

            if table_name:
                query += " AND table_name = ?"
                params.append(table_name)

            query += " ORDER BY search_relevance DESC, credibility_score DESC LIMIT 20"

            cursor.execute(query, params)
            rows = cursor.fetchall()

            results = []
            for row in rows:
                entry = dict(row)
                entry["tags"] = json.loads(entry.get("tags", "[]"))
                entry["metadata"] = json.loads(entry.get("metadata", "{}"))
                results.append(entry)

            return results

    def get_evidence_for_topic(
        self, channel_id: str, topic: str, evidence_types: List[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get evidence - based content for a specific topic"""
        if not evidence_types:
            evidence_types = ["fact", "statistic", "study", "quote", "example"]

        evidence = {}

        for evidence_type in evidence_types:
            entries = self.search_knowledge_base(
                channel_id=channel_id, search_term=topic, min_credibility=0.6
            )

            # Filter by evidence type
            filtered_entries = [
                entry
                for entry in entries
                if entry.get("entry_type", "").lower() == evidence_type.lower()
            ]

            evidence[evidence_type] = filtered_entries[:5]  # Top 5 for each type

        return evidence

    def update_credibility_score(self, entry_id: str, new_score: float):
        """Update credibility score for an entry"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Update in master table
            cursor.execute(
                """
                UPDATE knowledge_entries
                SET credibility_score = ?, updated_at = ?
                WHERE entry_id = ?
            """,
                (new_score, datetime.now().isoformat(), entry_id),
            )

            # Get table info to update specific table
            cursor.execute(
                """
                SELECT channel_id, table_name FROM knowledge_entries
                WHERE entry_id = ?
            """,
                (entry_id,),
            )

            result = cursor.fetchone()
            if result:
                channel_id, table_name = result
                full_table_name = f"{channel_id}_{table_name}"
                primary_key = self._get_primary_key_field(table_name)

                # Update in specific table
                update_query = f"""
                    UPDATE {full_table_name}
                    SET credibility_score = ?, updated_at = ?
                    WHERE {primary_key} = ?
                """
                cursor.execute(update_query, (new_score, datetime.now().isoformat(), entry_id))

            conn.commit()

    def track_knowledge_usage(
        self,
        entry_id: str,
        channel_id: str,
        content_id: str = None,
        usage_context: str = None,
        effectiveness_score: float = None,
    ):
        """Track usage of knowledge entries for optimization"""
        usage_id = (
            f"usage_{datetime.now().strftime('%Y % m%d_ % H%M % S')}_{hash(entry_id) % 10000}"
        )

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO knowledge_usage
                (usage_id,
    entry_id,
    channel_id,
    content_id,
    usage_context,
    effectiveness_score,
    used_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    usage_id,
                    entry_id,
                    channel_id,
                    content_id,
                    usage_context,
                    effectiveness_score,
                    datetime.now().isoformat(),
                ),
            )
            conn.commit()

    def get_channel_knowledge_stats(self, channel_id: str) -> Dict[str, Any]:
        """Get knowledge base statistics for a channel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Total entries
            cursor.execute(
                """
                SELECT COUNT(*) FROM knowledge_entries WHERE channel_id = ?
            """,
                (channel_id,),
            )
            total_entries = cursor.fetchone()[0]

            # Entries by type
            cursor.execute(
                """
                SELECT entry_type, COUNT(*) FROM knowledge_entries
                WHERE channel_id = ? GROUP BY entry_type
            """,
                (channel_id,),
            )
            entries_by_type = dict(cursor.fetchall())

            # Average credibility
            cursor.execute(
                """
                SELECT AVG(credibility_score) FROM knowledge_entries
                WHERE channel_id = ?
            """,
                (channel_id,),
            )
            avg_credibility = cursor.fetchone()[0] or 0.0

            # Usage statistics
            cursor.execute(
                """
                SELECT COUNT(*), AVG(effectiveness_score) FROM knowledge_usage
                WHERE channel_id = ?
            """,
                (channel_id,),
            )
            usage_stats = cursor.fetchone()
            total_usage = usage_stats[0] if usage_stats else 0
            avg_effectiveness = usage_stats[1] if usage_stats and usage_stats[1] else 0.0

            return {
                "total_entries": total_entries,
                "entries_by_type": entries_by_type,
                "average_credibility": round(avg_credibility, 2),
                "total_usage": total_usage,
                "average_effectiveness": round(avg_effectiveness, 2),
                "knowledge_density": round(total_entries / max(1, total_usage), 2),
            }

    def get_recommended_evidence(
        self, channel_id: str, content_topic: str, content_type: str = "video"
    ) -> Dict[str, Any]:
        """Get recommended evidence for content creation"""
        # Search for relevant evidence
        evidence = self.get_evidence_for_topic(channel_id, content_topic)

        # Get channel config for context
        config = self.protocol.get_channel_config(channel_id)

        recommendations = {
            "primary_evidence": [],
            "supporting_facts": [],
            "expert_quotes": [],
            "statistics": [],
            "case_studies": [],
            "credibility_notes": [],
        }

        # Categorize evidence by type and quality
        for evidence_type, entries in evidence.items():
            for entry in entries:
                credibility = entry.get("credibility_score", 0.0)

                if credibility >= 0.8:
                    recommendations["primary_evidence"].append(
                        {
                            "type": evidence_type,
                            "content": entry.get("content", ""),
                            "source": entry.get("source", ""),
                            "credibility": credibility,
                        }
                    )
                elif credibility >= 0.6:
                    if evidence_type == "quote":
                        recommendations["expert_quotes"].append(entry)
                    elif evidence_type == "statistic":
                        recommendations["statistics"].append(entry)
                    elif evidence_type == "case_study":
                        recommendations["case_studies"].append(entry)
                    else:
                        recommendations["supporting_facts"].append(entry)

                # Add credibility notes for transparency
                if credibility < 0.7:
                    recommendations["credibility_notes"].append(
                        f"Note: {entry.get('title', 'Entry')} has moderate credibility ({credibility:.1f}). Verify before use."
                    )

        return recommendations


# Global instance
knowledge_bases = DedicatedKnowledgeBases()


def get_knowledge_bases() -> DedicatedKnowledgeBases:
    """Get the global Dedicated Knowledge Bases instance"""
    return knowledge_bases
