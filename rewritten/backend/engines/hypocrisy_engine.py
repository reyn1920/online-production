#!/usr/bin/env python3
""""""
Hypocrisy Engine - Research Validation System

This module provides a comprehensive engine for detecting, analyzing, and validating
hypocrisy in public statements and research claims. It integrates with the evidence
database to provide research validation capabilities.

Features:
- Statement contradiction detection
- Evidence validation and cross - referencing
- Research claim verification
- Public figure consistency tracking
- Content opportunity identification
- Automated fact - checking integration

Author: TRAE.AI System
Version: 1.0.0
""""""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from backend.database.db_singleton import get_hypocrisy_db_manager
    from backend.database.hypocrisy_db_manager import HypocrisyFinding

except ImportError:
    HypocrisyFinding = None
    get_hypocrisy_db_manager = None
    logging.warning("HypocrisyDatabaseManager not available. Hypocrisy engine will be limited.")

try:
    import nltk
    import requests
    from textblob import TextBlob

except ImportError:
    nltk = None
    TextBlob = None
    requests = None
    logging.warning("NLP libraries not available. Text analysis will be limited.")


@dataclass
class ValidationResult:
    """Result of research validation"""

    is_valid: bool
    confidence_score: float
    contradictions_found: List[Dict[str, Any]]
    evidence_sources: List[str]
    validation_notes: str
    fact_check_status: str = "pending"


@dataclass
class ResearchClaim:
    """Research claim to be validated"""

    claim_text: str
    source: str
    author: Optional[str] = None
    date_published: Optional[datetime] = None
    topic_tags: Optional[List[str]] = None
    context: Optional[str] = None


class HypocrisyEngine:
    """Main engine for hypocrisy detection and research validation"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Get singleton database manager
        self.db_manager = None
        if get_hypocrisy_db_manager:
            self.db_manager = get_hypocrisy_db_manager()

        # Configuration
        self.min_confidence_threshold = self.config.get("min_confidence", 0.7)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.8)
        self.time_gap_threshold_days = self.config.get("time_gap_threshold", 30)

        # Initialize NLP components if available
        self._initialize_nlp()

    def _initialize_nlp(self) -> None:
        """Initialize NLP components for text analysis"""
        try:
            if nltk:
                # Download required NLTK data
                nltk.download("punkt", quiet=True)
                nltk.download("stopwords", quiet=True)
                nltk.download("vader_lexicon", quiet=True)
                self.logger.info("NLP components initialized successfully")
        except Exception as e:
            self.logger.warning(f"Failed to initialize NLP components: {e}")

    async def validate_research_claim(self, claim: ResearchClaim) -> ValidationResult:
        """Validate a research claim against existing evidence database"""
        try:
            self.logger.info(f"Validating research claim: {claim.claim_text[:100]}...")

            # Search for contradictory statements
            contradictions = await self._find_contradictions(claim)

            # Analyze evidence sources
            evidence_sources = await self._gather_evidence_sources(claim)

            # Calculate confidence score
            confidence_score = self._calculate_validation_confidence(
                claim, contradictions, evidence_sources
# BRACKET_SURGEON: disabled
#             )

            # Determine validation status
            is_valid = (
                len(contradictions) == 0 and confidence_score >= self.min_confidence_threshold
# BRACKET_SURGEON: disabled
#             )

            # Generate validation notes
            validation_notes = self._generate_validation_notes(
                claim, contradictions, evidence_sources, confidence_score
# BRACKET_SURGEON: disabled
#             )

            result = ValidationResult(
                is_valid=is_valid,
                confidence_score=confidence_score,
                contradictions_found=contradictions,
                evidence_sources=evidence_sources,
                validation_notes=validation_notes,
                fact_check_status="validated" if is_valid else "disputed",
# BRACKET_SURGEON: disabled
#             )

            self.logger.info(
                f"Validation completed. Valid: {is_valid}, Confidence: {confidence_score:.2f}"
# BRACKET_SURGEON: disabled
#             )
            return result

        except Exception as e:
            self.logger.error(f"Error validating research claim: {e}")
            return ValidationResult(
                is_valid=False,
                confidence_score=0.0,
                contradictions_found=[],
                evidence_sources=[],
                validation_notes=f"Validation failed: {str(e)}",
                fact_check_status="error",
# BRACKET_SURGEON: disabled
#             )

    async def _find_contradictions(self, claim: ResearchClaim) -> List[Dict[str, Any]]:
        """Find contradictory statements in the database"""
        contradictions = []

        if not self.db_manager:
            self.logger.warning("Database manager not available for contradiction search")
            return contradictions

        try:
            # Search for related findings by keywords
            keywords = self._extract_keywords(claim.claim_text)

            for keyword in keywords:
                # Search existing findings
                findings = self.db_manager.search_findings(
                    subject_name=claim.author, min_confidence=0.5, limit=20
# BRACKET_SURGEON: disabled
#                 )

                for finding in findings:
                    # Check for semantic similarity
                    similarity_score = self._calculate_semantic_similarity(
                        claim.claim_text, finding["statement_1"]
# BRACKET_SURGEON: disabled
#                     )

                    if similarity_score > self.similarity_threshold:
                        contradiction = {
                            "finding_id": finding["id"],
                            "contradictory_statement": finding["statement_2"],
                            "original_statement": finding["statement_1"],
                            "similarity_score": similarity_score,
                            "source": finding["source_2"],
                            "date": finding["date_2"],
                            "contradiction_type": finding["contradiction_type"],
                            "severity_score": finding["severity_score"],
# BRACKET_SURGEON: disabled
#                         }
                        contradictions.append(contradiction)

            self.logger.info(f"Found {len(contradictions)} potential contradictions")
            return contradictions

        except Exception as e:
            self.logger.error(f"Error finding contradictions: {e}")
            return []

    async def _gather_evidence_sources(self, claim: ResearchClaim) -> List[str]:
        """Gather supporting or contradicting evidence sources"""
        evidence_sources = []

        try:
            # Add the original source
            if claim.source:
                evidence_sources.append(claim.source)

            # Search database for related evidence
            if self.db_manager:
                findings = self.db_manager.search_findings(
                    subject_name=claim.author, verification_status="verified", limit=10
# BRACKET_SURGEON: disabled
#                 )

                for finding in findings:
                    if finding.get("evidence_links"):
                        evidence_sources.extend(finding["evidence_links"])

                    if finding.get("source_1"):
                        evidence_sources.append(finding["source_1"])
                    if finding.get("source_2"):
                        evidence_sources.append(finding["source_2"])

            # Remove duplicates and return
            return list(set(evidence_sources))

        except Exception as e:
            self.logger.error(f"Error gathering evidence sources: {e}")
            return evidence_sources

    def _calculate_validation_confidence(
        self,
        claim: ResearchClaim,
        contradictions: List[Dict],
        evidence_sources: List[str],
# BRACKET_SURGEON: disabled
#     ) -> float:
        """Calculate confidence score for validation"""
        try:
            base_confidence = 0.5

            # Reduce confidence for contradictions
            contradiction_penalty = len(contradictions) * 0.2

            # Increase confidence for evidence sources
            evidence_bonus = min(len(evidence_sources) * 0.1, 0.3)

            # Adjust for author credibility (if known)
            author_bonus = 0.1 if claim.author else 0.0

            # Adjust for recency
            recency_bonus = 0.0
            if claim.date_published:
                days_old = (datetime.now() - claim.date_published).days
                if days_old < 30:
                    recency_bonus = 0.1
                elif days_old < 90:
                    recency_bonus = 0.05

            confidence = (
                base_confidence
                + evidence_bonus
                + author_bonus
                + recency_bonus
                - contradiction_penalty
# BRACKET_SURGEON: disabled
#             )

            # Clamp to valid range
            return max(0.0, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating validation confidence: {e}")
            return 0.0

    def _generate_validation_notes(
        self,
        claim: ResearchClaim,
        contradictions: List[Dict],
        evidence_sources: List[str],
        confidence_score: float,
# BRACKET_SURGEON: disabled
#     ) -> str:
        """Generate human - readable validation notes"""
        notes = []

        notes.append(f"Claim validation completed with {confidence_score:.2f} confidence.")

        if contradictions:
            notes.append(f"Found {len(contradictions)} potential contradictions:")
            for i, contradiction in enumerate(contradictions[:3], 1):
                notes.append(
                    f"  {i}. Contradictory statement from {contradiction.get('source', 'unknown source')}"
# BRACKET_SURGEON: disabled
#                 )
                notes.append(f"     Similarity: {contradiction.get('similarity_score', 0):.2f}")
        else:
            notes.append("No direct contradictions found in database.")

        if evidence_sources:
            notes.append(f"Evidence gathered from {len(evidence_sources)} sources.")
        else:
            notes.append("Limited evidence sources available.")

        if claim.author:
            notes.append(f"Claim attributed to: {claim.author}")

        return " ".join(notes)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for search"""
        try:
            if not TextBlob:
                # Fallback to simple word extraction
                words = re.findall(r"\\b\\w{4,}\\b", text.lower())
                return list(set(words))[:10]

            blob = TextBlob(text)

            # Extract noun phrases and important words
            keywords = []

            # Add noun phrases
            for phrase in blob.noun_phrases:
                if len(phrase) > 3:
                    keywords.append(phrase)

            # Add important words (nouns, adjectives)
            for word, pos in blob.tags:
                if pos in ["NN", "NNS", "NNP", "NNPS", "JJ", "JJR", "JJS"] and len(word) > 3:
                    keywords.append(word.lower())

            return list(set(keywords))[:15]

        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            return []

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            if not TextBlob:
                # Fallback to simple word overlap
                words1 = set(text1.lower().split())
                words2 = set(text2.lower().split())

                if not words1 or not words2:
                    return 0.0

                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))

                return intersection / union if union > 0 else 0.0

            # Use TextBlob for more sophisticated analysis
            blob1 = TextBlob(text1)
            blob2 = TextBlob(text2)

            # Extract key terms
            terms1 = set(
                [
                    word.lower()
                    for word, pos in blob1.tags
                    if pos
                    in [
                        "NN",
                        "NNS",
                        "NNP",
                        "NNPS",
                        "VB",
                        "VBD",
                        "VBG",
                        "VBN",
                        "VBP",
                        "VBZ",
# BRACKET_SURGEON: disabled
#                     ]
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )
            terms2 = set(
                [
                    word.lower()
                    for word, pos in blob2.tags
                    if pos
                    in [
                        "NN",
                        "NNS",
                        "NNP",
                        "NNPS",
                        "VB",
                        "VBD",
                        "VBG",
                        "VBN",
                        "VBP",
                        "VBZ",
# BRACKET_SURGEON: disabled
#                     ]
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )

            if not terms1 or not terms2:
                return 0.0

            # Calculate Jaccard similarity
            intersection = len(terms1.intersection(terms2))
            union = len(terms1.union(terms2))

            return intersection / union if union > 0 else 0.0

        except Exception as e:
            self.logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0

    async def detect_hypocrisy(
        self,
        subject_name: str,
        new_statement: str,
        source: str,
        context: Optional[str] = None,
    ) -> Optional[HypocrisyFinding]:
        """Detect potential hypocrisy by comparing new statement with existing ones"""
        try:
            if not self.db_manager:
                self.logger.warning("Database manager not available for hypocrisy detection")
                return None

            # Search for existing statements by the same subject
            existing_findings = self.db_manager.search_findings(subject_name=subject_name, limit=50)

            # Check for contradictions
            for finding in existing_findings:
                similarity_score = self._calculate_semantic_similarity(
                    new_statement, finding["statement_1"]
# BRACKET_SURGEON: disabled
#                 )

                # If statements are similar but context suggests contradiction
                if similarity_score > 0.3:  # Some similarity but potentially contradictory
                    contradiction_score = self._analyze_contradiction(
                        new_statement, finding["statement_1"]
# BRACKET_SURGEON: disabled
#                     )

                    if contradiction_score > 0.6:  # Significant contradiction
                        # Create new hypocrisy finding
                        hypocrisy_finding = HypocrisyFinding(
                            subject_name=subject_name,
                            subject_type="person",  # Default, can be refined
                            statement_1=finding["statement_1"],
                            statement_2=new_statement,
                            context_1=finding.get("context_1"),
                            context_2=context,
                            date_1=(
                                datetime.fromisoformat(finding["date_1"])
                                if finding.get("date_1")
                                else None
# BRACKET_SURGEON: disabled
#                             ),
                            date_2=datetime.now(),
                            source_1=finding.get("source_1"),
                            source_2=source,
                            contradiction_type="contextual",
                            severity_score=max(1, min(10, int(contradiction_score * 10))),
                            confidence_score=contradiction_score,
                            verification_status="pending",
                            evidence_links=[source],
                            tags=["auto_detected"],
                            analysis_notes=f"Auto - detected contradiction with similarity {similarity_score:.2f}",
                            public_impact_score=5,  # Default medium impact
                            created_by="hypocrisy_engine",
# BRACKET_SURGEON: disabled
#                         )

                        # Store the finding
                        finding_id = self.db_manager.store_finding(hypocrisy_finding)
                        if finding_id:
                            self.logger.info(f"Detected and stored hypocrisy finding {finding_id}")
                            return hypocrisy_finding

            return None

        except Exception as e:
            self.logger.error(f"Error detecting hypocrisy: {e}")
            return None

    def _analyze_contradiction(self, statement1: str, statement2: str) -> float:
        """Analyze the level of contradiction between two statements"""
        try:
            if not TextBlob:
                # Simple contradiction detection based on negation words
                negation_words = [
                    "not",
                    "no",
                    "never",
                    "none",
                    "nothing",
                    "neither",
                    "nor",
# BRACKET_SURGEON: disabled
#                 ]

                words1 = statement1.lower().split()
                words2 = statement2.lower().split()

                neg_count1 = sum(1 for word in words1 if word in negation_words)
                neg_count2 = sum(1 for word in words2 if word in negation_words)

                # If one has negations and the other doesn't, potential contradiction
                if (neg_count1 > 0) != (neg_count2 > 0):
                    return 0.7

                return 0.3  # Default low contradiction score

            # More sophisticated analysis with TextBlob
            blob1 = TextBlob(statement1)
            blob2 = TextBlob(statement2)

            # Analyze sentiment polarity
            polarity1 = blob1.sentiment.polarity
            polarity2 = blob2.sentiment.polarity

            # If sentiments are opposite, higher contradiction score
            polarity_diff = abs(polarity1 - polarity2)

            # Check for explicit contradictory terms
            contradiction_indicators = [
                ("support", "oppose"),
                ("agree", "disagree"),
                ("yes", "no"),
                ("approve", "disapprove"),
                ("favor", "against"),
                ("for", "against"),
# BRACKET_SURGEON: disabled
#             ]

            contradiction_score = polarity_diff * 0.5

            for term1, term2 in contradiction_indicators:
                if (term1 in statement1.lower() and term2 in statement2.lower()) or (
                    term2 in statement1.lower() and term1 in statement2.lower()
# BRACKET_SURGEON: disabled
#                 ):
                    contradiction_score += 0.3

            return min(1.0, contradiction_score)

        except Exception as e:
            self.logger.error(f"Error analyzing contradiction: {e}")
            return 0.0

    def get_content_opportunities(
        self, limit: int = 10, min_confidence: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Get hypocrisy findings suitable for content creation"""
        try:
            if not self.db_manager:
                self.logger.warning("Database manager not available")
                return []

            opportunities = self.db_manager.get_content_opportunities(
                limit=limit, min_confidence=min_confidence
# BRACKET_SURGEON: disabled
#             )

            # Enhance opportunities with additional analysis
            enhanced_opportunities = []
            for opp in opportunities:
                enhanced_opp = opp.copy()

                # Add content potential score
                enhanced_opp["content_potential_score"] = self._calculate_content_potential(opp)

                # Add suggested content angles
                enhanced_opp["content_angles"] = self._suggest_content_angles(opp)

                enhanced_opportunities.append(enhanced_opp)

            # Sort by content potential
            enhanced_opportunities.sort(key=lambda x: x["content_potential_score"], reverse=True)

            return enhanced_opportunities

        except Exception as e:
            self.logger.error(f"Error getting content opportunities: {e}")
            return []

    def _calculate_content_potential(self, opportunity: Dict[str, Any]) -> float:
        """Calculate content creation potential for a hypocrisy finding"""
        try:
            base_score = opportunity.get("confidence_score", 0.5)

            # Boost for high - profile subjects
            subject_boost = 0.1 if opportunity.get("subject_type") == "politician" else 0.0

            # Boost for recent findings
            recency_boost = 0.0
            if opportunity.get("discovered_at"):
                try:
                    discovered_date = datetime.fromisoformat(opportunity["discovered_at"])
                    days_old = (datetime.now() - discovered_date).days
                    if days_old < 7:
                        recency_boost = 0.2
                    elif days_old < 30:
                        recency_boost = 0.1
                except Exception:
                    pass

            # Boost for high severity
            severity_boost = (opportunity.get("severity_score", 5) - 5) * 0.02

            # Boost for public impact
            impact_boost = (opportunity.get("public_impact_score", 5) - 5) * 0.02

            total_score = base_score + subject_boost + recency_boost + severity_boost + impact_boost

            return max(0.0, min(1.0, total_score))

        except Exception as e:
            self.logger.error(f"Error calculating content potential: {e}")
            return 0.0

    def _suggest_content_angles(self, opportunity: Dict[str, Any]) -> List[str]:
        """Suggest content creation angles for a hypocrisy finding"""
        angles = []

        try:
            contradiction_type = opportunity.get("contradiction_type", "direct")
            subject_name = opportunity.get("subject_name", "Unknown")

            if contradiction_type == "temporal":
                angles.append(f"How {subject_name}'s Position Changed Over Time")'
                angles.append(f"The Evolution of {subject_name}'s Stance")'
            elif contradiction_type == "contextual":
                angles.append(f"{subject_name} Says Different Things to Different Audiences")
                angles.append(f"Context Matters: {subject_name}'s Contradictory Messages")'
            elif contradiction_type == "policy_shift":
                angles.append(f"{subject_name}'s Policy Flip - Flop Exposed")'
                angles.append(f"Before and After: {subject_name}'s Policy Reversal")'
            else:
                angles.append(f"{subject_name}'s Contradictory Statements Revealed")'
                angles.append(f"Fact - Check: {subject_name}'s Inconsistent Claims")'

            # Add general angles
            angles.append(f"Breaking Down {subject_name}'s Contradictions")'
            angles.append(f"What {subject_name} Doesn't Want You to Remember")'

            return angles[:5]  # Return top 5 angles

        except Exception as e:
            self.logger.error(f"Error suggesting content angles: {e}")
            return ["Analysis of Contradictory Statements"]

    def get_engine_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the hypocrisy engine"""
        try:
            if not self.db_manager:
                return {"error": "Database manager not available"}

            # Get database statistics
            db_stats = self.db_manager.get_statistics()

            # Add engine - specific statistics
            engine_stats = {
                "engine_version": "1.0.0",
                "min_confidence_threshold": self.min_confidence_threshold,
                "similarity_threshold": self.similarity_threshold,
                "time_gap_threshold_days": self.time_gap_threshold_days,
                "nlp_available": TextBlob is not None,
                "database_available": self.db_manager is not None,
# BRACKET_SURGEON: disabled
#             }

            return {
                "database_stats": db_stats,
                "engine_config": engine_stats,
                "last_updated": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            self.logger.error(f"Error getting engine statistics: {e}")
            return {"error": str(e)}

    async def batch_validate_claims(self, claims: List[ResearchClaim]) -> List[ValidationResult]:
        """Validate multiple research claims in batch"""
        results = []

        for claim in claims:
            try:
                result = await self.validate_research_claim(claim)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error validating claim: {e}")
                results.append(
                    ValidationResult(
                        is_valid=False,
                        confidence_score=0.0,
                        contradictions_found=[],
                        evidence_sources=[],
                        validation_notes=f"Validation error: {str(e)}",
                        fact_check_status="error",
# BRACKET_SURGEON: disabled
#                     )
# BRACKET_SURGEON: disabled
#                 )

        return results