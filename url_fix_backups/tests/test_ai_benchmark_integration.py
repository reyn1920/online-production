#!/usr / bin / env python3
""""""
Test suite for AI Benchmark Integration System
""""""

import asyncio
import json
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add backend to path for imports

import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from ai_benchmark_integration import (

    AIBenchmarkIntegration,
        BenchmarkProvider,
        QualityMetrics,
        BenchmarkResult
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )


class TestAIBenchmarkIntegration:
    """Test cases for AI Benchmark Integration"""


    def setup_method(self):
        """Setup test environment"""
        self.integration = AIBenchmarkIntegration()
        self.test_content = "This is a test content for quality validation."
        self.test_content_type = "text"


    def test_initialization(self):
        """Test proper initialization of the integration system"""
        assert self.integration is not None
        assert self.integration.quality_threshold == 75.0
        assert len(self.integration.consensus_weight) == 3
        assert self.integration.app is not None


    def test_consensus_weight_sum(self):
        """Test that consensus weights sum to 1.0"""
        total_weight = sum(self.integration.consensus_weight.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow for floating point precision


    def test_quality_metrics_creation(self):
        """Test QualityMetrics dataclass creation"""
        metrics = QualityMetrics(
            correctness = 85.0,
                clarity = 90.0,
                professionalism = 80.0,
                overall_score = 85.0,
                provider="chatgpt",
                timestamp = datetime.now(),
                response_time_ms = 500
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        assert metrics.correctness == 85.0
        assert metrics.clarity == 90.0
        assert metrics.professionalism == 80.0
        assert metrics.overall_score == 85.0
        assert metrics.provider == "chatgpt"
        assert metrics.response_time_ms == 500


    def test_create_validation_prompt(self):
        """Test validation prompt creation"""
        prompt = self.integration._create_validation_prompt(
            self.test_content,
                self.test_content_type
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        assert "Correctness" in prompt
        assert "Clarity" in prompt
        assert "Professionalism" in prompt
        assert self.test_content in prompt
        assert "JSON format" in prompt


    def test_parse_quality_scores_valid_json(self):
        """Test parsing valid JSON quality scores"""
        response_text = ''''''
        {
            "correctness": 85,
                "clarity": 90,
                "professionalism": 80,
                "overall": 85,
                "reasoning": "Good quality content"
# BRACKET_SURGEON: disabled
#         }
        ''''''

        scores = self.integration._parse_quality_scores(response_text)

        assert scores['correctness'] == 85.0
        assert scores['clarity'] == 90.0
        assert scores['professionalism'] == 80.0
        assert scores['overall'] == 85.0


    def test_parse_quality_scores_invalid_json(self):
        """Test parsing invalid JSON returns default scores"""
        response_text = "This is not valid JSON"

        scores = self.integration._parse_quality_scores(response_text)

        assert scores['correctness'] == 50.0
        assert scores['clarity'] == 50.0
        assert scores['professionalism'] == 50.0
        assert scores['overall'] == 50.0


    def test_calculate_consensus_score(self):
        """Test consensus score calculation"""
        metrics = [
            QualityMetrics(
                correctness = 80, clarity = 85, professionalism = 75, overall_score = 80,
                    provider="chatgpt",
    timestamp = datetime.now(),
    response_time_ms = 500
# BRACKET_SURGEON: disabled
#             ),
                QualityMetrics(
                correctness = 85, clarity = 80, professionalism = 85, overall_score = 83,
                    provider="gemini",
    timestamp = datetime.now(),
    response_time_ms = 600
# BRACKET_SURGEON: disabled
#             ),
                QualityMetrics(
                correctness = 75, clarity = 90, professionalism = 80, overall_score = 82,
                    provider="abacus",
    timestamp = datetime.now(),
    response_time_ms = 700
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        consensus = self.integration._calculate_consensus_score(metrics)

        # Should be weighted average: 80 * 0.4 + 83 * 0.35 + 82 * 0.25 = 81.35
        expected = 80 * 0.4 + 83 * 0.35 + 82 * 0.25
        assert abs(consensus - expected) < 0.1


    def test_calculate_consensus_score_empty_metrics(self):
        """Test consensus score with empty metrics list"""
        consensus = self.integration._calculate_consensus_score([])
        assert consensus == 0.0


    def test_generate_recommendations_low_scores(self):
        """Test recommendation generation for low quality scores"""
        metrics = [
            QualityMetrics(
                correctness = 60, clarity = 65, professionalism = 55, overall_score = 60,
                    provider="chatgpt",
    timestamp = datetime.now(),
    response_time_ms = 500
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        recommendations = self.integration._generate_recommendations(metrics, "text")

        assert len(recommendations) >= 3
        assert any("accuracy" in rec.lower() for rec in recommendations)
        assert any("clarity" in rec.lower() for rec in recommendations)
        assert any("professional" in rec.lower() for rec in recommendations)


    def test_generate_recommendations_high_scores(self):
        """Test recommendation generation for high quality scores"""
        metrics = [
            QualityMetrics(
                correctness = 90, clarity = 85, professionalism = 88, overall_score = 88,
                    provider="chatgpt",
    timestamp = datetime.now(),
    response_time_ms = 500
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        recommendations = self.integration._generate_recommendations(metrics, "text")

        assert len(recommendations) == 1
        assert "meets quality standards" in recommendations[0].lower()


    def test_generate_recommendations_code_type(self):
        """Test recommendation generation for code content type"""
        metrics = [
            QualityMetrics(
                correctness = 75, clarity = 80, professionalism = 85, overall_score = 80,
                    provider="chatgpt",
    timestamp = datetime.now(),
    response_time_ms = 500
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        recommendations = self.integration._generate_recommendations(metrics, "code")

        assert any("code" in rec.lower() \
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     or "bug" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio


    async def test_validate_with_abacus_mock(self):
        """Test Abacus AI validation (mocked)"""
        # Set mock API key
        self.integration.abacus_api_key = "test_key"

        metrics = await self.integration._validate_with_abacus(
            self.test_content,
                self.test_content_type
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        assert isinstance(metrics, QualityMetrics)
        assert metrics.provider == "abacus"
        assert 0 <= metrics.correctness <= 100
        assert 0 <= metrics.clarity <= 100
        assert 0 <= metrics.professionalism <= 100
        assert 0 <= metrics.overall_score <= 100

    @pytest.mark.asyncio


    async def test_validate_with_provider_error_handling(self):
        """Test error handling in provider validation"""
        # Test with no API keys configured
        self.integration.openai_client = None
        self.integration.gemini_api_key = None
        self.integration.abacus_api_key = None

        metrics = await self.integration._validate_with_provider(
            self.test_content,
                self.test_content_type,
                BenchmarkProvider.CHATGPT
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Should return default metrics on error
            assert isinstance(metrics, QualityMetrics)
        assert metrics.overall_score == 0.0
        assert metrics.provider == "chatgpt"


    def test_flask_app_routes(self):
        """Test Flask app route registration"""
        with self.integration.app.test_client() as client:
            # Test providers endpoint
            response = client.get('/api / benchmark / providers')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data['success'] is True
            assert 'providers' in data
            assert 'quality_threshold' in data


    def test_flask_validate_endpoint_missing_content(self):
        """Test validation endpoint with missing content"""
        with self.integration.app.test_client() as client:
            response = client.post('/api / benchmark / validate',
                json={},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                      content_type='application / json')

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Content is required' in data['error']

    @patch('ai_benchmark_integration.asyncio.run')


    def test_flask_validate_endpoint_success(self, mock_asyncio_run):
        """Test successful validation endpoint"""
        # Mock the async validation result
        mock_result = BenchmarkResult(
            content = self.test_content,
                metrics=[
                QualityMetrics(
                    correctness = 85, clarity = 90, professionalism = 80, overall_score = 85,
                        provider="chatgpt",
    timestamp = datetime.now(),
    response_time_ms = 500
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ],
                consensus_score = 85.0,
                passed_threshold = True,
                recommendations=["Content meets quality standards"],
                validation_id="test_123"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        mock_asyncio_run.return_value = mock_result

        with self.integration.app.test_client() as client:
            response = client.post('/api / benchmark / validate',
                json={'content': self.test_content},
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                      content_type='application / json')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['consensus_score'] == 85.0
            assert data['passed_threshold'] is True
            assert len(data['metrics']) == 1
            assert len(data['recommendations']) == 1

if __name__ == '__main__':
    pytest.main([__file__, '-v'])