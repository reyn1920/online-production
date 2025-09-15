#!/usr / bin / env python3
""""""
Evidence - Based Scripting Module for The Right Perspective

This module implements the evidence - based scripting requirement from the Protected Channel Protocol.
It ensures that every Right Perspective video script is backed by verifiable facts, quotes, and
counter - evidence from the right_perspective.db database.

Part of the TRAE.AI Master Orchestrator Protected Channel System.
""""""

import json
import logging
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class EvidenceBasedScripting:
    """"""
    Evidence - based scripting engine for The Right Perspective channel.

    This class enforces the requirement that every video script must be backed by
    verifiable facts, quotes, \
#     and counter - evidence from the right_perspective.db database.
    """"""


    def __init__(self, db_path: str = "./right_perspective.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)

        # Protected Channel validation
        self._validate_protected_channel()

        # Initialize evidence database
        self._init_evidence_database()

        self.logger.info(
            "Evidence - Based Scripting initialized for The Right Perspective (PROTECTED)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )


    def _validate_protected_channel(self):
        """Validate this is being used for The Right Perspective protected channel."""
        # This method ensures the evidence - based scripting is only used for protected content
        self.channel_protection = {
            "channel_name": "The Right Perspective",
                "protection_level": "MAXIMUM",
                "evidence_required": True,
                "fact_checking_mandatory": True,
                "source_verification": True,
# BRACKET_SURGEON: disabled
#                 }


    def _init_evidence_database(self):
        """Initialize connection to the evidence database."""
        try:
            if not self.db_path.exists():
                self.logger.warning(f"Evidence database not found at {self.db_path}")
                return

            # Test database connection
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Verify evidence table exists
            cursor.execute(
                """"""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='evidence'
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            if not cursor.fetchone():
                self.logger.error("Evidence table not found in database")
                conn.close()
                return

            conn.close()
            self.logger.info("Evidence database connection verified")

        except Exception as e:
            self.logger.error(f"Failed to initialize evidence database: {e}")


    async def generate_evidence_based_script(
        self, topic: str, script_template: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """"""
        Generate a Right Perspective video script with mandatory evidence integration.

        Args:
            topic: The main topic / subject of the video
            script_template: Base script template to enhance with evidence
            requirements: Script requirements including tone, duration, etc.

        Returns:
            Dict containing the evidence - enhanced script and supporting data
        """"""
        try:
            self.logger.info(f"Generating evidence - based script for topic: {topic}")

            # Step 1: Extract evidence from database
            evidence_data = await self._extract_topic_evidence(topic)

            if (
                not evidence_data["facts"]
                and not evidence_data["quotes"]
                and not evidence_data["statistics"]
# BRACKET_SURGEON: disabled
#             ):
                self.logger.warning(f"No evidence found for topic: {topic}")
                return {
                    "success": False,
                        "error": "EVIDENCE_REQUIRED_BUT_NOT_FOUND",
                        "message": f"No verifiable evidence found in database for topic: {topic}",
                        "evidence_requirement": "MANDATORY_FOR_RIGHT_PERSPECTIVE",
# BRACKET_SURGEON: disabled
#                         }

            # Step 2: Analyze script template for evidence insertion points
            insertion_points = self._identify_evidence_insertion_points(script_template)

            # Step 3: Generate evidence - enhanced script
            enhanced_script = await self._integrate_evidence_into_script(
                script_template, evidence_data, insertion_points, requirements
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            # Step 4: Validate evidence integration
            validation_result = self._validate_evidence_integration(
                enhanced_script, evidence_data
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            if not validation_result["valid"]:
                return {
                    "success": False,
                        "error": "EVIDENCE_INTEGRATION_FAILED",
                        "validation_issues": validation_result["issues"],
# BRACKET_SURGEON: disabled
#                         }

            # Step 5: Generate evidence report
            evidence_report = self._generate_evidence_report(evidence_data, topic)

            return {
                "success": True,
                    "enhanced_script": enhanced_script,
                    "evidence_data": evidence_data,
                    "evidence_report": evidence_report,
                    "validation": validation_result,
                    "topic": topic,
                    "evidence_count": {
                    "facts": len(evidence_data["facts"]),
                        "quotes": len(evidence_data["quotes"]),
                        "statistics": len(evidence_data["statistics"]),
# BRACKET_SURGEON: disabled
#                         },
                    "created_at": datetime.now().isoformat(),
                    "protection_level": "RIGHT_PERSPECTIVE_PROTECTED",
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            self.logger.error(f"Evidence - based script generation failed: {e}")
            return {"success": False, "error": str(e), "topic": topic}


    async def _extract_topic_evidence(
        self, topic: str
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Extract all relevant evidence for a given topic from the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Search for evidence related to the topic (case - insensitive,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     partial matches)
            search_terms = self._generate_search_terms(topic)

            evidence_data = {"facts": [], "quotes": [], "statistics": []}

            for search_term in search_terms:
                # Query evidence table
                cursor.execute(
                    """"""
                    SELECT id, topic, content, source_url, content_type, date_added
                    FROM evidence
                    WHERE LOWER(topic) LIKE LOWER(?) OR LOWER(content) LIKE LOWER(?)
                    ORDER BY date_added DESC
                ""","""
                    (f"%{search_term}%", f"%{search_term}%"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

                results = cursor.fetchall()

                for row in results:
                    evidence_item = {
                        "id": row[0],
                            "topic": row[1],
                            "content": row[2],
                            "source_url": row[3],
                            "content_type": row[4],
                            "date_added": row[5],
                            "search_term": search_term,
# BRACKET_SURGEON: disabled
#                             }

                    # Categorize by content type
                    content_type = row[4].lower() if row[4] else "fact"
                    if content_type == "quote":
                        evidence_data["quotes"].append(evidence_item)
                    elif content_type == "statistic":
                        evidence_data["statistics"].append(evidence_item)
                    else:
                        evidence_data["facts"].append(evidence_item)

            conn.close()

            # Remove duplicates
            evidence_data = self._remove_duplicate_evidence(evidence_data)

            self.logger.info(
                f"Extracted evidence: {len(evidence_data['facts'])} facts, "
                f"{len(evidence_data['quotes'])} quotes, {len(evidence_data['statistics'])} statistics"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            return evidence_data

        except Exception as e:
            self.logger.error(f"Failed to extract evidence for topic '{topic}': {e}")
            return {"facts": [], "quotes": [], "statistics": []}


    def _generate_search_terms(self, topic: str) -> List[str]:
        """Generate search terms from the main topic."""
        # Basic keyword extraction and expansion
        terms = [topic.lower()]

        # Split topic into individual words
        words = re.findall(r"\\b\\w+\\b", topic.lower())
        terms.extend(words)

        # Remove common stop words
        stop_words = {
            "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
# BRACKET_SURGEON: disabled
#                 }
        terms = [term for term in terms if term not in stop_words and len(term) > 2]

        return list(set(terms))  # Remove duplicates


    def _remove_duplicate_evidence(
        self, evidence_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Remove duplicate evidence items based on content similarity."""
        for category in evidence_data:
            seen_content = set()
            unique_items = []

            for item in evidence_data[category]:
                content_key = item["content"].lower().strip()
                if content_key not in seen_content:
                    seen_content.add(content_key)
                    unique_items.append(item)

            evidence_data[category] = unique_items

        return evidence_data


    def _identify_evidence_insertion_points(
        self, script_template: str
    ) -> List[Dict[str, Any]]:
        """Identify optimal points in the script to insert evidence."""
        insertion_points = []

        # Look for common patterns where evidence should be inserted
        patterns = [
            (r"\\b(claim|claims|statement|statements)\\b", "fact_needed"),
                (r"\\b(according to|sources say|reports indicate)\\b", "quote_needed"),
                (
                r"\\b(statistics show|data reveals|numbers indicate)\\b",
                    "statistic_needed",
# BRACKET_SURGEON: disabled
#                     ),
                (r"\\b(evidence shows|proof|research indicates)\\b", "evidence_needed"),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]

        for i, line in enumerate(script_template.split("\\n")):
            for pattern, evidence_type in patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    insertion_points.append(
                        {
                            "line_number": i,
                                "line_content": line,
                                "evidence_type": evidence_type,
                                "position": "after_line",
# BRACKET_SURGEON: disabled
#                                 }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        return insertion_points


    async def _integrate_evidence_into_script(
        self,
            script_template: str,
            evidence_data: Dict[str, List[Dict[str, Any]]],
            insertion_points: List[Dict[str, Any]],
            requirements: Dict[str, Any],
# BRACKET_SURGEON: disabled
#             ) -> str:
        """Integrate evidence into the script template."""
        lines = script_template.split("\\n")
        enhanced_lines = []

        evidence_used = {"facts": 0, "quotes": 0, "statistics": 0}

        for i, line in enumerate(lines):
            enhanced_lines.append(line)

            # Check if this line needs evidence insertion
            for insertion_point in insertion_points:
                if insertion_point["line_number"] == i:
                    evidence_type = insertion_point["evidence_type"]

                    # Select appropriate evidence
                    if "fact" in evidence_type and evidence_data["facts"]:
                        if evidence_used["facts"] < len(evidence_data["facts"]):
                            fact = evidence_data["facts"][evidence_used["facts"]]
                            enhanced_lines.append(f"\\n[EVIDENCE: {fact['content']}]")
                            if fact["source_url"]:
                                enhanced_lines.append(f"[SOURCE: {fact['source_url']}]")
                            evidence_used["facts"] += 1

                    elif "quote" in evidence_type and evidence_data["quotes"]:
                        if evidence_used["quotes"] < len(evidence_data["quotes"]):
                            quote = evidence_data["quotes"][evidence_used["quotes"]]
                            enhanced_lines.append(f"\\n[QUOTE: \\"{quote['content']}\\"]")
                            if quote["source_url"]:
                                enhanced_lines.append(
                                    f"[SOURCE: {quote['source_url']}]"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
                            evidence_used["quotes"] += 1

                    elif "statistic" in evidence_type and evidence_data["statistics"]:
                        if evidence_used["statistics"] < len(
                            evidence_data["statistics"]
# BRACKET_SURGEON: disabled
#                         ):
                            stat = evidence_data["statistics"][
                                evidence_used["statistics"]
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                             ]
                            enhanced_lines.append(f"\\n[STATISTIC: {stat['content']}]")
                            if stat["source_url"]:
                                enhanced_lines.append(f"[SOURCE: {stat['source_url']}]")
                            evidence_used["statistics"] += 1

        # Add any remaining evidence at the end if not all was used
        remaining_evidence = []

        for fact in evidence_data["facts"][evidence_used["facts"] :]:
            remaining_evidence.append(f"[ADDITIONAL FACT: {fact['content']}]")
            if fact["source_url"]:
                remaining_evidence.append(f"[SOURCE: {fact['source_url']}]")

        for quote in evidence_data["quotes"][evidence_used["quotes"] :]:
            remaining_evidence.append(f"[ADDITIONAL QUOTE: \\"{quote['content']}\\"]")
            if quote["source_url"]:
                remaining_evidence.append(f"[SOURCE: {quote['source_url']}]")

        for stat in evidence_data["statistics"][evidence_used["statistics"] :]:
            remaining_evidence.append(f"[ADDITIONAL STATISTIC: {stat['content']}]")
            if stat["source_url"]:
                remaining_evidence.append(f"[SOURCE: {stat['source_url']}]")

        if remaining_evidence:
            enhanced_lines.append("\\n\\n--- ADDITIONAL SUPPORTING EVIDENCE ---")
            enhanced_lines.extend(remaining_evidence)

        return "\\n".join(enhanced_lines)


    def _validate_evidence_integration(
        self, enhanced_script: str, evidence_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Validate that evidence has been properly integrated into the script."""
        validation_result = {
            "valid": True,
                "issues": [],
                "evidence_integration_score": 0.0,
# BRACKET_SURGEON: disabled
#                 }

        # Check if evidence markers are present
        evidence_markers = ["[EVIDENCE:", "[QUOTE:", "[STATISTIC:", "[SOURCE:"]
        markers_found = sum(
            1 for marker in evidence_markers if marker in enhanced_script
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if markers_found == 0:
            validation_result["valid"] = False
            validation_result["issues"].append(
                "No evidence markers found in enhanced script"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Calculate evidence integration score
        total_evidence = (
            len(evidence_data["facts"])
            + len(evidence_data["quotes"])
            + len(evidence_data["statistics"])
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        if total_evidence > 0:
            validation_result["evidence_integration_score"] = min(
                markers_found / total_evidence, 1.0
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Check for minimum evidence requirements
        if (
            validation_result["evidence_integration_score"] < 0.3
# BRACKET_SURGEON: disabled
#         ):  # At least 30% of evidence should be integrated
            validation_result["valid"] = False
            validation_result["issues"].append(
                "Insufficient evidence integration (minimum 30% required)"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        return validation_result


    def _generate_evidence_report(
        self, evidence_data: Dict[str, List[Dict[str, Any]]], topic: str
    ) -> Dict[str, Any]:
        """Generate a comprehensive evidence report for the script."""
        return {
            "topic": topic,
                "evidence_summary": {
                "total_facts": len(evidence_data["facts"]),
                    "total_quotes": len(evidence_data["quotes"]),
                    "total_statistics": len(evidence_data["statistics"]),
                    "total_evidence_items": len(evidence_data["facts"])
                + len(evidence_data["quotes"])
                + len(evidence_data["statistics"]),
# BRACKET_SURGEON: disabled
#                     },
                "source_breakdown": self._analyze_evidence_sources(evidence_data),
                "evidence_quality_score": self._calculate_evidence_quality_score(
                evidence_data
# BRACKET_SURGEON: disabled
#             ),
                "recommendations": self._generate_evidence_recommendations(evidence_data),
                "generated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }


    def _analyze_evidence_sources(
        self, evidence_data: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Analyze the sources of evidence."""
        sources = []

        for category in evidence_data:
            for item in evidence_data[category]:
                if item.get("source_url"):
                    sources.append(item["source_url"])

        unique_sources = list(set(sources))

        return {
            "total_sources": len(sources),
                "unique_sources": len(unique_sources),
                "source_diversity_score": len(unique_sources) / max(len(sources), 1),
                "sources_with_urls": len([s for s in sources if s]),
# BRACKET_SURGEON: disabled
#                 }


    def _calculate_evidence_quality_score(
        self, evidence_data: Dict[str, List[Dict[str, Any]]]
# BRACKET_SURGEON: disabled
#     ) -> float:
        """Calculate an overall quality score for the evidence."""
        total_items = 0
        quality_points = 0

        for category in evidence_data:
            for item in evidence_data[category]:
                total_items += 1

                # Points for having a source URL
                if item.get("source_url"):
                    quality_points += 1

                # Points for content length (more detailed = higher quality)
                if len(item.get("content", "")) > 50:
                    quality_points += 1

                # Points for recent evidence
                if item.get("date_added"):
                    quality_points += 0.5

        return quality_points / max(total_items * 2.5, 1)  # Normalize to 0 - 1 scale


    def _generate_evidence_recommendations(
        self, evidence_data: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Generate recommendations for improving evidence quality."""
        recommendations = []

        total_evidence = (
            len(evidence_data["facts"])
            + len(evidence_data["quotes"])
            + len(evidence_data["statistics"])
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        if total_evidence < 3:
            recommendations.append(
                "Consider adding more evidence to strengthen the script"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        if len(evidence_data["quotes"]) == 0:
            recommendations.append("Adding direct quotes would enhance credibility")

        if len(evidence_data["statistics"]) == 0:
            recommendations.append(
                "Including statistics would provide stronger factual support"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        # Check for sources
        items_without_sources = 0
        for category in evidence_data:
            for item in evidence_data[category]:
                if not item.get("source_url"):
                    items_without_sources += 1

        if items_without_sources > 0:
            recommendations.append(
                f"{items_without_sources} evidence items lack source URLs"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

        return recommendations


    async def add_evidence_to_database(
        self,
            topic: str,
            content: str,
            source_url: Optional[str] = None,
            content_type: str = "fact",
# BRACKET_SURGEON: disabled
#             ) -> bool:
        """Add new evidence to the database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            cursor.execute(
                """"""
                INSERT INTO evidence (topic,
    content,
    source_url,
    content_type,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     date_added)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ""","""
                (topic, content, source_url, content_type),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            conn.commit()
            conn.close()

            self.logger.info(
                f"Added evidence to database: {content_type} for topic '{topic}'"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return True

        except Exception as e:
            self.logger.error(f"Failed to add evidence to database: {e}")
            return False


    async def get_evidence_statistics(self) -> Dict[str, Any]:
        """Get statistics about the evidence database."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # Get total counts by type
            cursor.execute(
                """"""
                SELECT content_type, COUNT(*)
                FROM evidence
                GROUP BY content_type
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            type_counts = dict(cursor.fetchall())

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM evidence")
            total_count = cursor.fetchone()[0]

            # Get recent additions
            cursor.execute(
                """"""
                SELECT COUNT(*) FROM evidence
                WHERE date_added >= datetime('now', '-7 days')
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            recent_count = cursor.fetchone()[0]

            conn.close()

            return {
                "total_evidence_items": total_count,
                    "evidence_by_type": type_counts,
                    "recent_additions_7_days": recent_count,
                    "database_health": "healthy" if total_count > 0 else "empty",
# BRACKET_SURGEON: disabled
#                     }

        except Exception as e:
            self.logger.error(f"Failed to get evidence statistics: {e}")
            return {"error": str(e)}

if __name__ == "__main__":
    # Example usage

    import asyncio


    async def test_evidence_scripting():
        scripting = EvidenceBasedScripting()

        # Test script template
        template = """"""
        Welcome to The Right Perspective!

        Today we're discussing political hypocrisy.'

        According to sources, politicians often contradict themselves.

        Statistics show that public trust in government is declining.

        The evidence shows a clear pattern of inconsistency.

        That's all for today's episode!
        """"""

        result = await scripting.generate_evidence_based_script(
            topic="political hypocrisy",
                script_template = template,
                requirements={"tone": "satirical", "duration": 300},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        print(json.dumps(result, indent = 2))

    asyncio.run(test_evidence_scripting())