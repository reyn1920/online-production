#!/usr / bin / env python3
"""
Research Validation Service

This module provides a service layer that integrates the HypocrisyEngine with
research agents, enabling automated research validation and fact - checking.

Features:
- Research claim validation
- Automated fact - checking integration
- Evidence cross - referencing
- Content opportunity identification
- Research quality scoring
- Validation reporting

Author: TRAE.AI System
Version: 1.0.0
"""

import asyncio
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    from backend.engines.hypocrisy_engine import (HypocrisyEngine, ResearchClaim,
        ValidationResult)
except ImportError:
    HypocrisyEngine = None
    ValidationResult = None
    ResearchClaim = None
    logging.warning(
        "HypocrisyEngine not available. Research validation will be limited."
    )

try:
    from backend.database.hypocrisy_db_manager import HypocrisyDatabaseManager
except ImportError:
    HypocrisyDatabaseManager = None
    logging.warning("HypocrisyDatabaseManager not available.")

@dataclass


class ResearchValidationRequest:
    """Request for research validation"""

    content: str
    source_url: Optional[str] = None
    author: Optional[str] = None
    topic: Optional[str] = None
    validation_type: str = "claim"  # 'claim', 'statement', 'fact'
    priority: str = "medium"  # 'low', 'medium', 'high'
    context: Optional[str] = None
    requested_by: Optional[str] = None

@dataclass


class ResearchValidationResponse:
    """Response from research validation"""

    request_id: str
    is_valid: bool
    confidence_score: float
    validation_status: str  # 'validated', 'disputed', 'inconclusive', 'error'
    contradictions_found: List[Dict[str, Any]]
    evidence_sources: List[str]
    validation_notes: str
    recommendations: List[str]
    content_opportunities: List[Dict[str, Any]]
    processing_time_ms: int
    timestamp: datetime


class ResearchValidationService:
    """Service for validating research claims and detecting inconsistencies"""


    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

        # Initialize hypocrisy engine
        self.hypocrisy_engine = None
        if HypocrisyEngine:
            try:
                engine_config = self.config.get("hypocrisy_engine", {})
                self.hypocrisy_engine = HypocrisyEngine(engine_config)
                self.logger.info("Hypocrisy engine initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize hypocrisy engine: {e}")

        # Configuration
        self.max_concurrent_validations = self.config.get(
            "max_concurrent_validations", 5
        )
        self.validation_timeout_seconds = self.config.get(
            "validation_timeout_seconds", 30
        )
        self.cache_results = self.config.get("cache_results", True)

        # Internal state
        self._validation_cache = {}
        self._active_validations = {}


    async def validate_research(
        self, request: ResearchValidationRequest
    ) -> ResearchValidationResponse:
        """Validate a research claim or statement"""
        start_time = datetime.now()
        request_id = f"val_{int(start_time.timestamp() * 1000)}"

        try:
            self.logger.info(
                f"Starting research validation {request_id} for: {request.content[:100]}..."
            )

            # Check cache first
            if self.cache_results:
                cached_result = self._get_cached_result(request)
                if cached_result:
                    self.logger.info(
                        f"Returning cached result for validation {request_id}"
                    )
                    return cached_result

            # Validate using hypocrisy engine
            validation_result = await self._perform_validation(request)

            # Generate recommendations
            recommendations = self._generate_recommendations(request, validation_result)

            # Find content opportunities
            content_opportunities = await self._find_content_opportunities(
                request, validation_result
            )

            # Calculate processing time
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

            # Create response
            response = ResearchValidationResponse(
                request_id = request_id,
                    is_valid = validation_result.is_valid if validation_result else False,
                    confidence_score=(
                    validation_result.confidence_score if validation_result else 0.0
                ),
                    validation_status=(
                    validation_result.fact_check_status
                    if validation_result
                    else "error"
                ),
                    contradictions_found=(
                    validation_result.contradictions_found if validation_result else []
                ),
                    evidence_sources=(
                    validation_result.evidence_sources if validation_result else []
                ),
                    validation_notes=(
                    validation_result.validation_notes
                    if validation_result
                    else "Validation failed"
                ),
                    recommendations = recommendations,
                    content_opportunities = content_opportunities,
                    processing_time_ms = processing_time,
                    timestamp = datetime.now(),
                    )

            # Cache the result
            if self.cache_results:
                self._cache_result(request, response)

            self.logger.info(
                f"Completed validation {request_id} in {processing_time}ms"
            )
            return response

        except Exception as e:
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            self.logger.error(f"Error in research validation {request_id}: {e}")

            return ResearchValidationResponse(
                request_id = request_id,
                    is_valid = False,
                    confidence_score = 0.0,
                    validation_status="error",
                    contradictions_found=[],
                    evidence_sources=[],
                    validation_notes = f"Validation error: {str(e)}",
                    recommendations=["Manual review required due to validation error"],
                    content_opportunities=[],
                    processing_time_ms = processing_time,
                    timestamp = datetime.now(),
                    )


    async def _perform_validation(
        self, request: ResearchValidationRequest
    ) -> Optional[ValidationResult]:
        """Perform the actual validation using the hypocrisy engine"""
        try:
            if not self.hypocrisy_engine:
                self.logger.warning("Hypocrisy engine not available for validation")
                return None

            # Convert request to research claim
            claim = ResearchClaim(
                claim_text = request.content,
                    source = request.source_url or "unknown",
                    author = request.author,
                    date_published = datetime.now(),
                    topic_tags=[request.topic] if request.topic else [],
                    context = request.context,
                    )

            # Validate the claim
            result = await self.hypocrisy_engine.validate_research_claim(claim)

            # If this is a statement from a known person, also check for hypocrisy
            if request.author and request.validation_type == "statement":
                hypocrisy_finding = await self.hypocrisy_engine.detect_hypocrisy(
                    subject_name = request.author,
                        new_statement = request.content,
                        source = request.source_url or "validation_service",
                        context = request.context,
                        )

                if hypocrisy_finding:
                    self.logger.info(
                        f"Detected potential hypocrisy for {request.author}"
                    )
                    # Add hypocrisy information to validation result
                    result.contradictions_found.append(
                        {
                            "type": "hypocrisy_detected",
                                "previous_statement": hypocrisy_finding.statement_1,
                                "current_statement": hypocrisy_finding.statement_2,
                                "confidence": hypocrisy_finding.confidence_score,
                                "severity": hypocrisy_finding.severity_score,
                                }
                    )

            return result

        except Exception as e:
            self.logger.error(f"Error performing validation: {e}")
            return None


    def _generate_recommendations(
        self,
            request: ResearchValidationRequest,
            validation_result: Optional[ValidationResult],
            ) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []

        try:
            if not validation_result:
                recommendations.append(
                    "Manual fact - checking required - automated validation unavailable"
                )
                recommendations.append(
                    "Verify claims through multiple independent sources"
                )
                return recommendations

            if validation_result.is_valid:
                recommendations.append(
                    "Claim appears to be valid based on available evidence"
                )
                if validation_result.confidence_score < 0.8:
                    recommendations.append(
                        "Consider gathering additional supporting evidence"
                    )
                recommendations.append("Monitor for any new contradictory information")
            else:
                recommendations.append("Claim disputed - contradictory evidence found")
                recommendations.append(
                    "Review contradictory sources before publication"
                )

                if validation_result.contradictions_found:
                    recommendations.append(
                        f"Investigate {len(validation_result.contradictions_found)} contradictions identified"
                    )

                recommendations.append("Consider fact - checking with primary sources")

            # Priority - based recommendations
            if request.priority == "high":
                recommendations.append("High priority: Expedite manual review process")
                recommendations.append(
                    "Consider real - time fact - checking before publication"
                )

            # Content - type specific recommendations
            if request.validation_type == "statement" and request.author:
                recommendations.append(
                    f"Cross - reference with {request.author}'s historical statements"
                )
                recommendations.append("Check for context - dependent interpretations")

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Manual review recommended due to processing error"]


    async def _find_content_opportunities(
        self,
            request: ResearchValidationRequest,
            validation_result: Optional[ValidationResult],
            ) -> List[Dict[str, Any]]:
        """Find content creation opportunities based on validation results"""
        opportunities = []

        try:
            if not self.hypocrisy_engine or not validation_result:
                return opportunities

            # If contradictions were found, these could be content opportunities
            if validation_result.contradictions_found:
                for contradiction in validation_result.contradictions_found:
                    opportunity = {
                        "type": "contradiction_analysis",
                            "title": f"Analyzing Contradictory Claims: {request.author or 'Unknown Source'}",
                            "description": f"Investigation into contradictory statements found during validation",
                            "confidence": contradiction.get("similarity_score", 0.5),
                            "potential_impact": "medium",
                            "content_angle": "fact_check",
                            "sources": [contradiction.get("source", request.source_url)],
                            "tags": ["fact - check", "contradiction", "research"],
                            }
                    opportunities.append(opportunity)

            # Get general content opportunities from hypocrisy engine
            if request.author:
                engine_opportunities = self.hypocrisy_engine.get_content_opportunities(
                    limit = 5, min_confidence = 0.6
                )

                for opp in engine_opportunities:
                    if opp.get("subject_name") == request.author:
                        content_opp = {
                            "type": "hypocrisy_expose",
                                "title": f"Exposing Inconsistencies: {request.author}",
                                "description": opp.get(
                                "analysis_notes", "Hypocrisy analysis"
                            ),
                                "confidence": opp.get("confidence_score", 0.5),
                                "potential_impact": (
                                "high"
                                if opp.get("public_impact_score", 5) > 7
                                else "medium"
                            ),
                                "content_angle": "investigative",
                                "sources": opp.get("evidence_links", []),
                                "tags": ["hypocrisy", "investigation", "politics"],
                                }
                        opportunities.append(content_opp)

            return opportunities[:3]  # Return top 3 opportunities

        except Exception as e:
            self.logger.error(f"Error finding content opportunities: {e}")
            return []


    def _get_cached_result(
        self, request: ResearchValidationRequest
    ) -> Optional[ResearchValidationResponse]:
        """Get cached validation result if available and not expired"""
        try:
            cache_key = self._generate_cache_key(request)

            if cache_key in self._validation_cache:
                cached_entry = self._validation_cache[cache_key]

                # Check if cache entry is still valid (1 hour expiry)
                if datetime.now() - cached_entry["timestamp"] < timedelta(hours = 1):
                    return cached_entry["result"]
                else:
                    # Remove expired entry
                    del self._validation_cache[cache_key]

            return None

        except Exception as e:
            self.logger.error(f"Error getting cached result: {e}")
            return None


    def _cache_result(
        self, request: ResearchValidationRequest, response: ResearchValidationResponse
    ) -> None:
        """Cache validation result"""
        try:
            cache_key = self._generate_cache_key(request)

            self._validation_cache[cache_key] = {
                "result": response,
                    "timestamp": datetime.now(),
                    }

            # Clean up old cache entries (keep max 100 entries)
            if len(self._validation_cache) > 100:
                # Remove oldest entries
                sorted_entries = sorted(
                    self._validation_cache.items(), key = lambda x: x[1]["timestamp"]
                )

                for key, _ in sorted_entries[:20]:  # Remove oldest 20
                    del self._validation_cache[key]

        except Exception as e:
            self.logger.error(f"Error caching result: {e}")


    def _generate_cache_key(self, request: ResearchValidationRequest) -> str:
        """Generate cache key for validation request"""
        try:
            # Create a hash - like key based on request content
            key_components = [
                request.content[:200],  # First 200 chars of content
                request.author or "unknown",
                    request.validation_type,
                    request.source_url or "no_source",
                    ]

            return "|".join(key_components).replace(" ", "_").lower()

        except Exception as e:
            self.logger.error(f"Error generating cache key: {e}")
            return f"error_key_{datetime.now().timestamp()}"


    async def batch_validate(
        self, requests: List[ResearchValidationRequest]
    ) -> List[ResearchValidationResponse]:
        """Validate multiple research requests in batch"""
        try:
            self.logger.info(f"Starting batch validation of {len(requests)} requests")

            # Limit concurrent validations
            semaphore = asyncio.Semaphore(self.max_concurrent_validations)


            async def validate_with_semaphore(request):
                async with semaphore:
                    return await self.validate_research(request)

            # Execute validations concurrently
            tasks = [validate_with_semaphore(request) for request in requests]
            results = await asyncio.gather(*tasks, return_exceptions = True)

            # Handle any exceptions
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Error in batch validation {i}: {result}")
                    error_response = ResearchValidationResponse(
                        request_id = f"batch_error_{i}",
                            is_valid = False,
                            confidence_score = 0.0,
                            validation_status="error",
                            contradictions_found=[],
                            evidence_sources=[],
                            validation_notes = f"Batch validation error: {str(result)}",
                            recommendations=["Manual review required"],
                            content_opportunities=[],
                            processing_time_ms = 0,
                            timestamp = datetime.now(),
                            )
                    processed_results.append(error_response)
                else:
                    processed_results.append(result)

            self.logger.info(f"Completed batch validation of {len(requests)} requests")
            return processed_results

        except Exception as e:
            self.logger.error(f"Error in batch validation: {e}")
            return []


    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get statistics about validation service performance"""
        try:
            stats = {
                "service_version": "1.0.0",
                    "cache_size": len(self._validation_cache),
                    "active_validations": len(self._active_validations),
                    "hypocrisy_engine_available": self.hypocrisy_engine is not None,
                    "max_concurrent_validations": self.max_concurrent_validations,
                    "validation_timeout_seconds": self.validation_timeout_seconds,
                    "cache_enabled": self.cache_results,
                    }

            # Add hypocrisy engine stats if available
            if self.hypocrisy_engine:
                engine_stats = self.hypocrisy_engine.get_engine_statistics()
                stats["hypocrisy_engine_stats"] = engine_stats

            return stats

        except Exception as e:
            self.logger.error(f"Error getting validation statistics: {e}")
            return {"error": str(e)}


    def clear_cache(self) -> bool:
        """Clear validation cache"""
        try:
            self._validation_cache.clear()
            self.logger.info("Validation cache cleared")
            return True
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
            return False

# Convenience functions for easy integration


async def validate_claim(
    content: str, author: Optional[str] = None, source: Optional[str] = None
) -> ResearchValidationResponse:
    """Quick validation of a research claim"""
    service = ResearchValidationService()
    request = ResearchValidationRequest(
        content = content, author = author, source_url = source, validation_type="claim"
    )
    return await service.validate_research(request)


async def validate_statement(
    content: str,
        author: str,
        source: Optional[str] = None,
        context: Optional[str] = None,
) -> ResearchValidationResponse:
    """Quick validation of a statement for hypocrisy detection"""
    service = ResearchValidationService()
    request = ResearchValidationRequest(
        content = content,
            author = author,
            source_url = source,
            validation_type="statement",
            context = context,
            )
    return await service.validate_research(request)
