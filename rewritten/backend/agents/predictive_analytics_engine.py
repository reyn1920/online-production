#!/usr/bin/env python3
""""""
Predictive Analytics Engine - Layer 3 of Maxed - Out Automation
Upgrades Research Agent to predict viral content success and optimize content strategy.
""""""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Machine learning imports
try:
    import joblib
    from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder, StandardScaler

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

from backend.agents.base_agents import BaseAgent
from backend.agents.research_tools import ResearchAgent
from backend.secret_store import SecretStore


class ContentType(Enum):
    VIDEO = "video"
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    PODCAST = "podcast"
    INFOGRAPHIC = "infographic"


class SuccessMetric(Enum):
    VIEWS = "views"
    ENGAGEMENT = "engagement"
    SHARES = "shares"
    COMMENTS = "comments"
    CONVERSION = "conversion"
    VIRAL_SCORE = "viral_score"


@dataclass
class ContentFeatures:
    title: str
    description: str
    keywords: List[str]
    content_type: ContentType
    duration_minutes: Optional[float] = None
    word_count: Optional[int] = None
    thumbnail_colors: Optional[List[str]] = None
    publish_time: Optional[datetime] = None
    topic_category: Optional[str] = None
    sentiment_score: Optional[float] = None
    readability_score: Optional[float] = None
    trending_keywords_count: Optional[int] = None


@dataclass
class ContentPerformance:
    content_id: str
    features: ContentFeatures
    views_30d: int
    engagement_rate: float
    shares: int
    comments: int
    conversion_rate: float
    viral_score: float
    success_factors: List[str]
    performance_date: datetime


@dataclass
class PredictionResult:
    content_features: ContentFeatures
    predicted_views: int
    predicted_engagement: float
    viral_probability: float
    success_score: float
    confidence_interval: Tuple[float, float]
    optimization_suggestions: List[str]
    risk_factors: List[str]
    best_publish_time: datetime


class PredictiveAnalyticsEngine(BaseAgent):
    """Advanced predictive analytics for viral content optimization."""

    def __init__(self, db_path: str = "data/right_perspective.db"):
        super().__init__()
        self.db_path = db_path
        self.secret_store = SecretStore()
        self.logger = logging.getLogger(__name__)
        self.research_agent = ResearchAgent()

        # Model storage
        self.models_dir = Path("data/predictive_models")
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Feature extractors
        self.scaler = StandardScaler()
        self.label_encoders = {}

        # Prediction models
        self.models = {
            SuccessMetric.VIEWS: None,
            SuccessMetric.ENGAGEMENT: None,
            SuccessMetric.VIRAL_SCORE: None,
# BRACKET_SURGEON: disabled
#         }

        # Performance tracking
        self.prediction_accuracy = defaultdict(list)

        self._init_database()
        self._load_or_train_models()

    def _init_database(self):
        """Initialize predictive analytics database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """"""
                CREATE TABLE IF NOT EXISTS content_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        keywords TEXT,
                        content_type TEXT NOT NULL,
                        duration_minutes REAL,
                        word_count INTEGER,
                        thumbnail_colors TEXT,
                        publish_time TIMESTAMP,
                        topic_category TEXT,
                        sentiment_score REAL,
                        readability_score REAL,
                        trending_keywords_count INTEGER,
                        views_30d INTEGER DEFAULT 0,
                        engagement_rate REAL DEFAULT 0.0,
                        shares INTEGER DEFAULT 0,
                        comments INTEGER DEFAULT 0,
                        conversion_rate REAL DEFAULT 0.0,
                        viral_score REAL DEFAULT 0.0,
                        success_factors TEXT,
                        performance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# BRACKET_SURGEON: disabled
#                 );

                CREATE TABLE IF NOT EXISTS prediction_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prediction_id TEXT UNIQUE NOT NULL,
                        content_features TEXT NOT NULL,
                        predicted_views INTEGER,
                        predicted_engagement REAL,
                        viral_probability REAL,
                        success_score REAL,
                        confidence_lower REAL,
                        confidence_upper REAL,
                        optimization_suggestions TEXT,
                        risk_factors TEXT,
                        best_publish_time TIMESTAMP,
                        actual_performance TEXT,
                        prediction_accuracy REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# BRACKET_SURGEON: disabled
#                 );

                CREATE TABLE IF NOT EXISTS trending_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern_type TEXT NOT NULL,
                        pattern_data TEXT NOT NULL,
                        confidence_score REAL NOT NULL,
                        trend_strength REAL NOT NULL,
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        active BOOLEAN DEFAULT TRUE
# BRACKET_SURGEON: disabled
#                 );

                CREATE TABLE IF NOT EXISTS success_factors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        factor_name TEXT NOT NULL,
                        factor_type TEXT NOT NULL,
                        impact_score REAL NOT NULL,
                        frequency INTEGER DEFAULT 1,
                        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(factor_name, factor_type)
# BRACKET_SURGEON: disabled
#                 );
            """"""
# BRACKET_SURGEON: disabled
#             )

    def _load_or_train_models(self):
        """Load existing models or train new ones."""
        if not ML_AVAILABLE:
            self.logger.warning("ML libraries not available, using heuristic predictions")
            return

        try:
            # Try to load existing models
            for metric in self.models.keys():
                model_path = self.models_dir / f"{metric.value}_model.joblib"
                if model_path.exists():
                    self.models[metric] = joblib.load(model_path)
                    self.logger.info(f"Loaded {metric.value} model")

            # Load scalers and encoders
            scaler_path = self.models_dir / "scaler.joblib"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)

            # If no models exist, train with synthetic data
            if all(model is None for model in self.models.values()):
                self._train_initial_models()

        except Exception as e:
            self.logger.error(f"Model loading error: {e}")
            self._train_initial_models()

    def _train_initial_models(self):
        """Train initial models with synthetic and historical data."""
        if not ML_AVAILABLE:
            return

        try:
            # Generate synthetic training data
            training_data = self._generate_synthetic_training_data(1000)

            if len(training_data) < 50:
                self.logger.warning("Insufficient training data, using heuristic predictions")
                return

            # Prepare features and targets
            X, y_views, y_engagement, y_viral = self._prepare_training_data(training_data)

            if X.shape[0] == 0:
                self.logger.warning("No valid training features, using heuristic predictions")
                return

            # Train models
            self.models[SuccessMetric.VIEWS] = RandomForestRegressor(
                n_estimators=100, random_state=42
# BRACKET_SURGEON: disabled
#             )
            self.models[SuccessMetric.ENGAGEMENT] = GradientBoostingRegressor(random_state=42)
            self.models[SuccessMetric.VIRAL_SCORE] = RandomForestRegressor(
                n_estimators=100, random_state=42
# BRACKET_SURGEON: disabled
#             )

            # Fit models
            self.models[SuccessMetric.VIEWS].fit(X, y_views)
            self.models[SuccessMetric.ENGAGEMENT].fit(X, y_engagement)
            self.models[SuccessMetric.VIRAL_SCORE].fit(X, y_viral)

            # Save models
            for metric, model in self.models.items():
                if model is not None:
                    model_path = self.models_dir / f"{metric.value}_model.joblib"
                    joblib.dump(model, model_path)

            # Save scaler
            scaler_path = self.models_dir / "scaler.joblib"
            joblib.dump(self.scaler, scaler_path)

            self.logger.info("Initial models trained and saved")

        except Exception as e:
            self.logger.error(f"Model training error: {e}")

    def _generate_synthetic_training_data(self, num_samples: int) -> List[ContentPerformance]:
        """Generate synthetic training data for initial model training."""
        training_data = []

        # Content categories and their typical performance patterns
        categories = {
            "tech_tutorials": {
                "base_views": 5000,
                "engagement_mult": 1.2,
                "viral_chance": 0.15,
# BRACKET_SURGEON: disabled
#             },
            "entertainment": {
                "base_views": 15000,
                "engagement_mult": 1.8,
                "viral_chance": 0.25,
# BRACKET_SURGEON: disabled
#             },
            "education": {
                "base_views": 3000,
                "engagement_mult": 1.0,
                "viral_chance": 0.08,
# BRACKET_SURGEON: disabled
#             },
            "news": {"base_views": 8000, "engagement_mult": 0.9, "viral_chance": 0.12},
            "lifestyle": {
                "base_views": 7000,
                "engagement_mult": 1.4,
                "viral_chance": 0.18,
# BRACKET_SURGEON: disabled
#             },
# BRACKET_SURGEON: disabled
#         }

        trending_keywords = [
            "AI",
            "automation",
            "productivity",
            "viral",
            "trending",
            "2024",
            "tips",
            "secrets",
            "ultimate",
            "guide",
            "hack",
            "boost",
            "transform",
            "master",
# BRACKET_SURGEON: disabled
#         ]

        for i in range(num_samples):
            # Random content features
            category = np.random.choice(list(categories.keys()))
            cat_data = categories[category]

            # Title generation with viral elements
            title_templates = [
                f"Ultimate {category.replace('_', ' ').title()} Guide",
                f"10 {category.replace('_', ' ').title()} Secrets",
                f"How to Master {category.replace('_', ' ').title()}",
                f"Transform Your {category.replace('_', ' ').title()}",
# BRACKET_SURGEON: disabled
#             ]

            title = np.random.choice(title_templates)
            if np.random.random() < 0.3:  # 30% chance of trending keyword
                title += f" with {np.random.choice(trending_keywords)}"

            # Features
            features = ContentFeatures(
                title=title,
                description=f"Comprehensive guide about {category.replace('_', ' ')}",
                keywords=np.random.choice(trending_keywords, size=np.random.randint(3, 8)).tolist(),
                content_type=ContentType.VIDEO,
                duration_minutes=np.random.uniform(5, 30),
                word_count=np.random.randint(500, 3000),
                thumbnail_colors=["#FF6B6B", "#4ECDC4", "#45B7D1"],"
                topic_category=category,
                sentiment_score=np.random.uniform(0.3, 0.9),
                readability_score=np.random.uniform(60, 90),
                trending_keywords_count=len([k for k in trending_keywords if k in title.lower()]),
# BRACKET_SURGEON: disabled
#             )

            # Performance calculation with realistic patterns
            base_views = cat_data["base_views"]

            # Title impact
            title_score = 1.0
            if any(word in title.lower() for word in ["ultimate", "secrets", "hack"]):
                title_score *= 1.3
            if features.trending_keywords_count > 0:
                title_score *= 1 + features.trending_keywords_count * 0.1

            # Duration impact
            duration_score = 1.0
            if features.duration_minutes:
                if 8 <= features.duration_minutes <= 15:  # Sweet spot
                    duration_score = 1.2
                elif features.duration_minutes > 20:
                    duration_score = 0.8

            # Sentiment impact
            sentiment_score = features.sentiment_score or 0.5

            # Calculate performance
            views = int(
                base_views
                * title_score
                * duration_score
                * sentiment_score
                * np.random.uniform(0.5, 2.0)
# BRACKET_SURGEON: disabled
#             )
            engagement_rate = (
                cat_data["engagement_mult"] * sentiment_score * np.random.uniform(0.02, 0.12)
# BRACKET_SURGEON: disabled
#             )
            shares = int(views * engagement_rate * np.random.uniform(0.1, 0.3))
            comments = int(views * engagement_rate * np.random.uniform(0.05, 0.15))

            # Viral score calculation
            viral_factors = [
                features.trending_keywords_count * 0.1,
                (engagement_rate - 0.05) * 10,
                title_score - 1.0,
                (sentiment_score - 0.5) * 2,
# BRACKET_SURGEON: disabled
#             ]
            viral_score = min(1.0, max(0.0, sum(viral_factors)))

            performance = ContentPerformance(
                content_id=f"synthetic_{i}",
                features=features,
                views_30d=views,
                engagement_rate=engagement_rate,
                shares=shares,
                comments=comments,
                conversion_rate=np.random.uniform(0.01, 0.05),
                viral_score=viral_score,
                success_factors=(
                    ["title_optimization", "trending_keywords"] if viral_score > 0.6 else []
# BRACKET_SURGEON: disabled
#                 ),
                performance_date=datetime.now() - timedelta(days=np.random.randint(1, 365)),
# BRACKET_SURGEON: disabled
#             )

            training_data.append(performance)

        return training_data

    def _prepare_training_data(
        self, training_data: List[ContentPerformance]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Prepare training data for machine learning models."""
        features_list = []
        views_list = []
        engagement_list = []
        viral_list = []

        for performance in training_data:
            try:
                # Extract numerical features
                feature_vector = self._extract_feature_vector(performance.features)
                if feature_vector is not None:
                    features_list.append(feature_vector)
                    views_list.append(performance.views_30d)
                    engagement_list.append(performance.engagement_rate)
                    viral_list.append(performance.viral_score)
            except Exception as e:
                self.logger.warning(f"Feature extraction error: {e}")
                continue

        if not features_list:
            return np.array([]), np.array([]), np.array([]), np.array([])

        X = np.array(features_list)

        # Fit scaler on training data
        X_scaled = self.scaler.fit_transform(X)

        return (
            X_scaled,
            np.array(views_list),
            np.array(engagement_list),
            np.array(viral_list),
# BRACKET_SURGEON: disabled
#         )

    def _extract_feature_vector(self, features: ContentFeatures) -> Optional[np.ndarray]:
        """Extract numerical feature vector from content features."""
        try:
            vector = []

            # Title features
            title_length = len(features.title)
            title_word_count = len(features.title.split())
            title_has_numbers = bool(re.search(r"\\d", features.title))
            title_has_question = "?" in features.title
            title_has_exclamation = "!" in features.title

            vector.extend(
                [
                    title_length,
                    title_word_count,
                    int(title_has_numbers),
                    int(title_has_question),
                    int(title_has_exclamation),
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )

            # Content features
            vector.extend(
                [
                    features.duration_minutes or 10.0,
                    features.word_count or 1000,
                    features.sentiment_score or 0.5,
                    features.readability_score or 70.0,
                    features.trending_keywords_count or 0,
# BRACKET_SURGEON: disabled
#                 ]
# BRACKET_SURGEON: disabled
#             )

            # Keyword features
            keyword_count = len(features.keywords) if features.keywords else 0
            avg_keyword_length = (
                np.mean([len(k) for k in features.keywords]) if features.keywords else 5.0
# BRACKET_SURGEON: disabled
#             )

            vector.extend([keyword_count, avg_keyword_length])

            # Time features (if publish_time available)
            if features.publish_time:
                hour = features.publish_time.hour
                day_of_week = features.publish_time.weekday()
                vector.extend([hour, day_of_week])
            else:
                vector.extend([12, 2])  # Default values

            # Content type encoding
            content_type_encoded = hash(features.content_type.value) % 10
            vector.append(content_type_encoded)

            return np.array(vector, dtype=float)

        except Exception as e:
            self.logger.error(f"Feature vector extraction error: {e}")
            return None

    async def predict_content_success(self, features: ContentFeatures) -> PredictionResult:
        """Predict content success using trained models."""
        try:
            # Extract feature vector
            feature_vector = self._extract_feature_vector(features)

            if feature_vector is None:
                return self._fallback_prediction(features)

            # Scale features
            X = feature_vector.reshape(1, -1)

            if ML_AVAILABLE and self.models[SuccessMetric.VIEWS] is not None:
                try:
                    X_scaled = self.scaler.transform(X)

                    # Make predictions
                    predicted_views = max(
                        0, int(self.models[SuccessMetric.VIEWS].predict(X_scaled)[0])
# BRACKET_SURGEON: disabled
#                     )
                    predicted_engagement = max(
                        0.0, self.models[SuccessMetric.ENGAGEMENT].predict(X_scaled)[0]
# BRACKET_SURGEON: disabled
#                     )
                    viral_score = max(
                        0.0,
                        min(
                            1.0,
                            self.models[SuccessMetric.VIRAL_SCORE].predict(X_scaled)[0],
# BRACKET_SURGEON: disabled
#                         ),
# BRACKET_SURGEON: disabled
#                     )

                except Exception as e:
                    self.logger.error(f"ML prediction error: {e}")
                    return self._fallback_prediction(features)
            else:
                return self._fallback_prediction(features)

            # Calculate success score
            success_score = self._calculate_success_score(
                predicted_views, predicted_engagement, viral_score
# BRACKET_SURGEON: disabled
#             )

            # Generate optimization suggestions
            optimization_suggestions = await self._generate_optimization_suggestions(
                features, success_score
# BRACKET_SURGEON: disabled
#             )

            # Identify risk factors
            risk_factors = self._identify_risk_factors(features)

            # Determine best publish time
            best_publish_time = await self._optimize_publish_time(features)

            # Calculate confidence interval (simplified)
            confidence_lower = success_score * 0.8
            confidence_upper = success_score * 1.2

            result = PredictionResult(
                content_features=features,
                predicted_views=predicted_views,
                predicted_engagement=predicted_engagement,
                viral_probability=viral_score,
                success_score=success_score,
                confidence_interval=(confidence_lower, confidence_upper),
                optimization_suggestions=optimization_suggestions,
                risk_factors=risk_factors,
                best_publish_time=best_publish_time,
# BRACKET_SURGEON: disabled
#             )

            # Store prediction for tracking
            await self._store_prediction(result)

            return result

        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return self._fallback_prediction(features)

    def _fallback_prediction(self, features: ContentFeatures) -> PredictionResult:
        """Fallback heuristic prediction when ML models are unavailable."""
        # Heuristic scoring based on content features
        base_score = 0.5

        # Title analysis
        title_lower = features.title.lower()
        viral_words = ["ultimate", "secret", "hack", "transform", "master", "boost"]
        title_score = sum(0.1 for word in viral_words if word in title_lower)

        # Keyword analysis
        trending_bonus = (features.trending_keywords_count or 0) * 0.05

        # Sentiment bonus
        sentiment_bonus = (features.sentiment_score or 0.5) * 0.2

        # Duration optimization (8 - 15 minutes is optimal for videos)
        duration_score = 0.1
        if features.duration_minutes:
            if 8 <= features.duration_minutes <= 15:
                duration_score = 0.2
            elif features.duration_minutes > 20:
                duration_score = 0.05

        success_score = min(
            1.0,
            base_score + title_score + trending_bonus + sentiment_bonus + duration_score,
# BRACKET_SURGEON: disabled
#         )

        # Estimate views and engagement based on success score
        predicted_views = int(success_score * 10000)
        predicted_engagement = success_score * 0.08
        viral_probability = max(0.0, success_score - 0.6)

        return PredictionResult(
            content_features=features,
            predicted_views=predicted_views,
            predicted_engagement=predicted_engagement,
            viral_probability=viral_probability,
            success_score=success_score,
            confidence_interval=(success_score * 0.7, success_score * 1.3),
            optimization_suggestions=[
                "Add trending keywords",
                "Optimize title for engagement",
# BRACKET_SURGEON: disabled
#             ],
            risk_factors=["Limited historical data"] if success_score < 0.4 else [],
            best_publish_time=datetime.now().replace(hour=14, minute=0, second=0, microsecond=0),
# BRACKET_SURGEON: disabled
#         )

    def _calculate_success_score(self, views: int, engagement: float, viral_score: float) -> float:
        """Calculate overall success score from predictions."""
        # Normalize metrics
        views_norm = min(1.0, views / 50000)  # Normalize to 50k views
        engagement_norm = min(1.0, engagement / 0.15)  # Normalize to 15% engagement

        # Weighted combination
        success_score = views_norm * 0.4 + engagement_norm * 0.3 + viral_score * 0.3

        return min(1.0, success_score)

    async def _generate_optimization_suggestions(
        self, features: ContentFeatures, success_score: float
    ) -> List[str]:
        """Generate AI - powered optimization suggestions."""
        suggestions = []

        try:
            # Title optimization
            if len(features.title) < 40:
                suggestions.append("Consider expanding title to 40 - 60 characters for better SEO")
            elif len(features.title) > 70:
                suggestions.append("Shorten title to under 70 characters for better visibility")

            # Keyword optimization
            if not features.keywords or len(features.keywords) < 3:
                suggestions.append("Add 3 - 5 relevant keywords to improve discoverability")

            # Trending keywords
            if (features.trending_keywords_count or 0) == 0:
                suggestions.append(
                    "Include trending keywords like 'AI', '2024', \"
#     or 'ultimate' in title"
# BRACKET_SURGEON: disabled
#                 )

            # Duration optimization
            if features.content_type == ContentType.VIDEO:
                if not features.duration_minutes:
                    suggestions.append(
                        "Aim for 8 - 15 minute video duration for optimal engagement"
# BRACKET_SURGEON: disabled
#                     )
                elif features.duration_minutes < 5:
                    suggestions.append(
                        "Consider extending video to 8+ minutes for better algorithm performance"
# BRACKET_SURGEON: disabled
#                     )
                elif features.duration_minutes > 20:
                    suggestions.append(
                        "Consider breaking into shorter segments \"
#     or series for better retention"
# BRACKET_SURGEON: disabled
#                     )

            # Sentiment optimization
            if (features.sentiment_score or 0.5) < 0.6:
                suggestions.append(
                    "Use more positive, engaging language to improve sentiment score"
# BRACKET_SURGEON: disabled
#                 )

            # Success score specific suggestions
            if success_score < 0.3:
                suggestions.extend(
                    [
                        "Consider researching trending topics in your niche",
                        "Analyze top - performing content for title patterns",
                        "Add emotional hooks or curiosity gaps to title",
# BRACKET_SURGEON: disabled
#                     ]
# BRACKET_SURGEON: disabled
#                 )
            elif success_score < 0.6:
                suggestions.extend(
                    [
                        "Optimize thumbnail with bright, contrasting colors",
                        "Add specific numbers or timeframes to title",
                        "Consider collaboration opportunities",
# BRACKET_SURGEON: disabled
#                     ]
# BRACKET_SURGEON: disabled
#                 )

            # AI - generated suggestions using Ollama
            ai_suggestions = await self._get_ai_optimization_insights(features, success_score)
            suggestions.extend(ai_suggestions)

        except Exception as e:
            self.logger.error(f"Optimization suggestion error: {e}")

        return suggestions[:8]  # Limit to top 8 suggestions

    async def _get_ai_optimization_insights(
        self, features: ContentFeatures, success_score: float
    ) -> List[str]:
        """Get AI - powered optimization insights using Ollama."""
        try:
            prompt = f""""""
            Analyze this content and provide 3 specific optimization suggestions:

            Title: {features.title}
            Content Type: {features.content_type.value}
            Keywords: {features.keywords}
            Current Success Score: {success_score:.2f}/1.0
            Duration: {features.duration_minutes} minutes
            Topic: {features.topic_category}

            Provide actionable suggestions to improve viral potential and engagement.
            Format as a simple list of suggestions.
            """"""

            import requests

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "llama3.2", "prompt": prompt, "stream": False},
                timeout=15,
# BRACKET_SURGEON: disabled
#             )

            if response.status_code == 200:
                result = response.json()
                ai_text = result["response"]

                # Extract suggestions from AI response
                suggestions = []
                for line in ai_text.split("\\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("•") or line[0].isdigit()):
                        # Clean up the suggestion
                        suggestion = re.sub(r"^[-•\\d\\.\\s]+", "", line).strip()
                        if suggestion and len(suggestion) > 10:
                            suggestions.append(suggestion)

                return suggestions[:3]

        except Exception as e:
            self.logger.error(f"AI optimization insights error: {e}")

        return []

    def _identify_risk_factors(self, features: ContentFeatures) -> List[str]:
        """Identify potential risk factors that could hurt performance."""
        risks = []

        # Title risks
        if len(features.title) > 80:
            risks.append("Title too long - may be truncated in search results")

        if not any(char.isdigit() for char in features.title):
            risks.append("No numbers in title - specific metrics often perform better")

        # Content risks
        if features.content_type == ContentType.VIDEO and features.duration_minutes:
            if features.duration_minutes > 25:
                risks.append("Long duration may hurt retention rates")
            elif features.duration_minutes < 3:
                risks.append("Very short content may not satisfy search intent")

        # Keyword risks
        if not features.keywords or len(features.keywords) < 2:
            risks.append("Insufficient keywords for proper categorization")

        # Sentiment risks
        if (features.sentiment_score or 0.5) < 0.4:
            risks.append("Negative sentiment may reduce shareability")

        # Trending risks
        if (features.trending_keywords_count or 0) == 0:
            risks.append("No trending keywords - may miss current interest waves")

        return risks

    async def _optimize_publish_time(self, features: ContentFeatures) -> datetime:
        """Determine optimal publish time based on content type and audience data."""
        try:
            # Get historical performance data by time
            optimal_hours = await self._get_optimal_publish_hours(features.content_type)

            # Default optimal times by content type
            default_hours = {
                ContentType.VIDEO: 14,  # 2 PM
                ContentType.BLOG_POST: 10,  # 10 AM
                ContentType.SOCIAL_POST: 12,  # 12 PM
                ContentType.PODCAST: 7,  # 7 AM
                ContentType.INFOGRAPHIC: 15,  # 3 PM
# BRACKET_SURGEON: disabled
#             }

            optimal_hour = optimal_hours or default_hours.get(features.content_type, 14)

            # Find next occurrence of optimal time
            now = datetime.now()
            next_publish = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)

            # If time has passed today, schedule for tomorrow
            if next_publish <= now:
                next_publish += timedelta(days=1)

            # Avoid weekends for business content
            if (
                features.topic_category in ["tech_tutorials", "education"]
                and next_publish.weekday() >= 5
# BRACKET_SURGEON: disabled
#             ):
                days_to_monday = 7 - next_publish.weekday()
                next_publish += timedelta(days=days_to_monday)

            return next_publish

        except Exception as e:
            self.logger.error(f"Publish time optimization error: {e}")
            return datetime.now() + timedelta(hours=2)

    async def _get_optimal_publish_hours(self, content_type: ContentType) -> Optional[int]:
        """Get optimal publish hour based on historical data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """"""
                    SELECT strftime('%H',
# BRACKET_SURGEON: disabled
#     publish_time) as hour,
    AVG(viral_score) as avg_score
                    FROM content_performance
                    WHERE content_type = ? AND publish_time IS NOT NULL
                    GROUP BY hour
                    ORDER BY avg_score DESC
                    LIMIT 1
                    ""","""
                    (content_type.value,),
# BRACKET_SURGEON: disabled
#                 )

                result = cursor.fetchone()
                if result and result[0]:
                    return int(result[0])

        except Exception as e:
            self.logger.error(f"Optimal hours query error: {e}")

        return None

    async def _store_prediction(self, result: PredictionResult):
        """Store prediction result for accuracy tracking."""
        try:
            prediction_id = hashlib.md5(
                f"{result.content_features.title}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:12]

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """"""
                    INSERT OR REPLACE INTO prediction_results
                    (prediction_id,
    content_features,
    predicted_views,
    predicted_engagement,
                        viral_probability, success_score, confidence_lower, confidence_upper,
# BRACKET_SURGEON: disabled
#                          optimization_suggestions, risk_factors, best_publish_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ""","""
                    (
                        prediction_id,
                        json.dumps(
                            {
                                "title": result.content_features.title,
                                "content_type": result.content_features.content_type.value,
                                "keywords": result.content_features.keywords,
                                "duration_minutes": result.content_features.duration_minutes,
# BRACKET_SURGEON: disabled
#                             }
# BRACKET_SURGEON: disabled
#                         ),
                        result.predicted_views,
                        result.predicted_engagement,
                        result.viral_probability,
                        result.success_score,
                        result.confidence_interval[0],
                        result.confidence_interval[1],
                        json.dumps(result.optimization_suggestions),
                        json.dumps(result.risk_factors),
                        result.best_publish_time,
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )

        except Exception as e:
            self.logger.error(f"Prediction storage error: {e}")

    async def update_actual_performance(self, content_id: str, performance: ContentPerformance):
        """Update with actual performance data to improve model accuracy."""
        try:
            # Store performance data
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """"""
                    INSERT OR REPLACE INTO content_performance
                    (content_id,
    title,
    description,
    keywords,
    content_type,
    duration_minutes,
                        word_count, topic_category, sentiment_score, readability_score,
                         trending_keywords_count, views_30d, engagement_rate, shares, comments,
# BRACKET_SURGEON: disabled
#                          conversion_rate, viral_score, success_factors, performance_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ""","""
                    (
                        performance.content_id,
                        performance.features.title,
                        performance.features.description,
                        json.dumps(performance.features.keywords),
                        performance.features.content_type.value,
                        performance.features.duration_minutes,
                        performance.features.word_count,
                        performance.features.topic_category,
                        performance.features.sentiment_score,
                        performance.features.readability_score,
                        performance.features.trending_keywords_count,
                        performance.views_30d,
                        performance.engagement_rate,
                        performance.shares,
                        performance.comments,
                        performance.conversion_rate,
                        performance.viral_score,
                        json.dumps(performance.success_factors),
                        performance.performance_date,
# BRACKET_SURGEON: disabled
#                     ),
# BRACKET_SURGEON: disabled
#                 )

            # Retrain models periodically
            await self._check_retrain_models()

        except Exception as e:
            self.logger.error(f"Performance update error: {e}")

    async def _check_retrain_models(self):
        """Check if models need retraining based on new data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM content_performance WHERE created_at > datetime('now', '-7 days')"
# BRACKET_SURGEON: disabled
#                 )
                new_data_count = cursor.fetchone()[0]

                # Retrain if we have 50+ new data points
                if new_data_count >= 50:
                    self.logger.info(f"Retraining models with {new_data_count} new data points")
                    await self._retrain_models()

        except Exception as e:
            self.logger.error(f"Retrain check error: {e}")

    async def _retrain_models(self):
        """Retrain models with updated data."""
        if not ML_AVAILABLE:
            return

        try:
            # Get all performance data
            training_data = await self._load_performance_data()

            if len(training_data) < 100:
                self.logger.warning("Insufficient data for retraining")
                return

            # Prepare training data
            X, y_views, y_engagement, y_viral = self._prepare_training_data(training_data)

            if X.shape[0] < 50:
                return

            # Retrain models
            for metric in self.models.keys():
                if metric == SuccessMetric.VIEWS:
                    self.models[metric] = RandomForestRegressor(n_estimators=150, random_state=42)
                    self.models[metric].fit(X, y_views)
                elif metric == SuccessMetric.ENGAGEMENT:
                    self.models[metric] = GradientBoostingRegressor(random_state=42)
                    self.models[metric].fit(X, y_engagement)
                elif metric == SuccessMetric.VIRAL_SCORE:
                    self.models[metric] = RandomForestRegressor(n_estimators=150, random_state=42)
                    self.models[metric].fit(X, y_viral)

            # Save updated models
            for metric, model in self.models.items():
                if model is not None:
                    model_path = self.models_dir / f"{metric.value}_model.joblib"
                    joblib.dump(model, model_path)

            self.logger.info("Models retrained successfully")

        except Exception as e:
            self.logger.error(f"Model retraining error: {e}")

    async def _load_performance_data(self) -> List[ContentPerformance]:
        """Load performance data from database."""
        performance_data = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """"""
                    SELECT content_id, title, description, keywords, content_type, duration_minutes,
                        word_count, topic_category, sentiment_score, readability_score,
                               trending_keywords_count, views_30d, engagement_rate, shares, comments,
                               conversion_rate, viral_score, success_factors, performance_date
                    FROM content_performance
                    ORDER BY performance_date DESC
                    """"""
# BRACKET_SURGEON: disabled
#                 )

                for row in cursor.fetchall():
                    try:
                        keywords = json.loads(row[3]) if row[3] else []
                        success_factors = json.loads(row[17]) if row[17] else []

                        features = ContentFeatures(
                            title=row[1],
                            description=row[2],
                            keywords=keywords,
                            content_type=ContentType(row[4]),
                            duration_minutes=row[5],
                            word_count=row[6],
                            topic_category=row[7],
                            sentiment_score=row[8],
                            readability_score=row[9],
                            trending_keywords_count=row[10],
# BRACKET_SURGEON: disabled
#                         )

                        performance = ContentPerformance(
                            content_id=row[0],
                            features=features,
                            views_30d=row[11],
                            engagement_rate=row[12],
                            shares=row[13],
                            comments=row[14],
                            conversion_rate=row[15],
                            viral_score=row[16],
                            success_factors=success_factors,
                            performance_date=datetime.fromisoformat(row[18]),
# BRACKET_SURGEON: disabled
#                         )

                        performance_data.append(performance)

                    except Exception as e:
                        self.logger.warning(f"Performance data parsing error: {e}")
                        continue

        except Exception as e:
            self.logger.error(f"Performance data loading error: {e}")

        return performance_data

    def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get analytics data for the dashboard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Prediction accuracy
                cursor = conn.execute(
                    """"""
                    SELECT AVG(prediction_accuracy) as avg_accuracy,
                        COUNT(*) as total_predictions
                    FROM prediction_results
                    WHERE prediction_accuracy IS NOT NULL
                    """"""
# BRACKET_SURGEON: disabled
#                 )
                accuracy_data = cursor.fetchone()

                # Recent predictions
                cursor = conn.execute(
                    """"""
                    SELECT success_score, viral_probability, created_at
                    FROM prediction_results
                    ORDER BY created_at DESC
                    LIMIT 10
                    """"""
# BRACKET_SURGEON: disabled
#                 )
                recent_predictions = cursor.fetchall()

                # Top success factors
                cursor = conn.execute(
                    """"""
                    SELECT factor_name, impact_score, frequency
                    FROM success_factors
                    ORDER BY impact_score DESC
                    LIMIT 5
                    """"""
# BRACKET_SURGEON: disabled
#                 )
                success_factors = cursor.fetchall()

                return {
                    "prediction_accuracy": {
                        "average": accuracy_data[0] if accuracy_data[0] else 0.0,
                        "total_predictions": (accuracy_data[1] if accuracy_data[1] else 0),
# BRACKET_SURGEON: disabled
#                     },
                    "recent_predictions": [
                        {
                            "success_score": pred[0],
                            "viral_probability": pred[1],
                            "created_at": pred[2],
# BRACKET_SURGEON: disabled
#                         }
                        for pred in recent_predictions
# BRACKET_SURGEON: disabled
#                     ],
                    "top_success_factors": [
                        {
                            "factor": factor[0],
                            "impact": factor[1],
                            "frequency": factor[2],
# BRACKET_SURGEON: disabled
#                         }
                        for factor in success_factors
# BRACKET_SURGEON: disabled
#                     ],
                    "model_status": {
                        "views_model": self.models[SuccessMetric.VIEWS] is not None,
                        "engagement_model": self.models[SuccessMetric.ENGAGEMENT] is not None,
                        "viral_model": self.models[SuccessMetric.VIRAL_SCORE] is not None,
                        "ml_available": ML_AVAILABLE,
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }

        except Exception as e:
            self.logger.error(f"Analytics dashboard error: {e}")
            return {
                "prediction_accuracy": {"average": 0.0, "total_predictions": 0},
                "recent_predictions": [],
                "top_success_factors": [],
                "model_status": {
                    "views_model": False,
                    "engagement_model": False,
                    "viral_model": False,
                    "ml_available": ML_AVAILABLE,
# BRACKET_SURGEON: disabled
#                 },
# BRACKET_SURGEON: disabled
#             }


# Example usage and testing
if __name__ == "__main__":
    import asyncio

    async def test_predictive_analytics():
        engine = PredictiveAnalyticsEngine()

        # Test content features
        test_features = ContentFeatures(
            title="Ultimate AI Automation Guide for 2024",
            description="Complete guide to AI automation tools and strategies",
            keywords=["AI", "automation", "productivity", "2024", "guide"],
            content_type=ContentType.VIDEO,
            duration_minutes=12.5,
            word_count=1500,
            topic_category="tech_tutorials",
            sentiment_score=0.8,
            readability_score=75.0,
            trending_keywords_count=3,
# BRACKET_SURGEON: disabled
#         )

        # Get prediction
        prediction = await engine.predict_content_success(test_features)

        print("Prediction Results:")
        print(f"Success Score: {prediction.success_score:.2f}")
        print(f"Predicted Views: {prediction.predicted_views:,}")
        print(f"Predicted Engagement: {prediction.predicted_engagement:.2%}")
        print(f"Viral Probability: {prediction.viral_probability:.2%}")
        print(f"Best Publish Time: {prediction.best_publish_time}")
        print(f"Optimization Suggestions: {prediction.optimization_suggestions}")
        print(f"Risk Factors: {prediction.risk_factors}")

        # Get analytics
        analytics = engine.get_analytics_dashboard_data()
        print(f"\\nAnalytics: {analytics}")

    asyncio.run(test_predictive_analytics())