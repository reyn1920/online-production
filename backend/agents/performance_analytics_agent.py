#!/usr/bin/env python3
"""
Performance Analytics Agent

Advanced performance analytics with predictive content scoring using statistical models.
Provides comprehensive analytics, trend analysis, and machine learning-based predictions
for content performance optimization.

Features:
- Predictive content scoring using multiple algorithms
- Statistical trend analysis and forecasting
- Performance pattern recognition
- Content optimization recommendations
- Real-time analytics dashboard data
- Machine learning model training and inference
"""

import os
import json
import sqlite3
import logging
import asyncio
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import statistics
from collections import defaultdict

# Statistical and ML imports
try:
    from scipy import stats
    from scipy.optimize import curve_fit
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression, Ridge
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, r2_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class PredictionModel(Enum):
    """Available prediction models."""
    LINEAR_REGRESSION = "linear_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    POLYNOMIAL_REGRESSION = "polynomial_regression"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ENSEMBLE = "ensemble"


class MetricType(Enum):
    """Types of performance metrics."""
    ENGAGEMENT_RATE = "engagement_rate"
    VIEW_COUNT = "view_count"
    SUBSCRIBER_GROWTH = "subscriber_growth"
    WATCH_TIME = "watch_time"
    CLICK_THROUGH_RATE = "ctr"
    REVENUE = "revenue"
    COMMENT_SENTIMENT = "comment_sentiment"
    VIRAL_COEFFICIENT = "viral_coefficient"


class TrendDirection(Enum):
    """Trend direction indicators."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"


@dataclass
class ContentFeatures:
    """Features extracted from content for prediction."""
    title_length: int
    description_length: int
    tag_count: int
    upload_hour: int
    upload_day: int
    duration_minutes: float
    thumbnail_quality_score: float
    topic_relevance_score: float
    seasonal_factor: float
    competition_density: float
    trending_alignment: float
    historical_performance: float


@dataclass
class PredictionResult:
    """Result of content performance prediction."""
    predicted_value: float
    confidence_interval: Tuple[float, float]
    model_accuracy: float
    feature_importance: Dict[str, float]
    prediction_date: datetime
    model_used: str
    factors_analysis: Dict[str, Any]


@dataclass
class TrendAnalysis:
    """Comprehensive trend analysis result."""
    metric_type: str
    trend_direction: TrendDirection
    trend_strength: float
    seasonal_component: Optional[Dict[str, float]]
    forecast_7_days: List[float]
    forecast_30_days: List[float]
    change_points: List[datetime]
    statistical_significance: float
    r_squared: float


@dataclass
class PerformanceInsight:
    """Actionable performance insight."""
    insight_type: str
    title: str
    description: str
    impact_score: float
    confidence: float
    recommended_actions: List[str]
    supporting_data: Dict[str, Any]
    priority: str


class PerformanceAnalyticsAgent:
    """Advanced performance analytics with predictive modeling."""
    
    def __init__(self, config_path: str = "config/state.json"):
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
        # Database paths
        self.db_path = "data/performance_analytics.db"
        self.models_path = "data/ml_models"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(self.models_path, exist_ok=True)
        
        # Initialize components
        self._init_database()
        self._load_config()
        
        # ML models cache
        self.trained_models = {}
        self.scalers = {}
        
        # Analytics settings
        self.min_data_points = 10
        self.confidence_level = 0.95
        self.forecast_horizon_days = 30
        
    def _load_config(self):
        """Load configuration settings."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = {}
                
            # Analytics-specific config
            self.analytics_config = self.config.get('performance_analytics', {
                'enabled': True,
                'prediction_models': ['random_forest', 'gradient_boosting'],
                'update_frequency_hours': 6,
                'min_training_samples': 50,
                'feature_selection_threshold': 0.05
            })
            
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            self.config = {}
            self.analytics_config = {'enabled': True}
    
    def _init_database(self):
        """Initialize the analytics database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Content performance history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_performance (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id TEXT NOT NULL,
                        platform TEXT NOT NULL,
                        title TEXT,
                        upload_date TIMESTAMP,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        share_count INTEGER DEFAULT 0,
                        watch_time_minutes REAL DEFAULT 0,
                        engagement_rate REAL DEFAULT 0,
                        ctr REAL DEFAULT 0,
                        revenue REAL DEFAULT 0,
                        subscriber_gain INTEGER DEFAULT 0,
                        duration_minutes REAL,
                        thumbnail_url TEXT,
                        tags JSON,
                        category TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Content features for ML
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS content_features (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id TEXT NOT NULL,
                        title_length INTEGER,
                        description_length INTEGER,
                        tag_count INTEGER,
                        upload_hour INTEGER,
                        upload_day INTEGER,
                        duration_minutes REAL,
                        thumbnail_quality_score REAL,
                        topic_relevance_score REAL,
                        seasonal_factor REAL,
                        competition_density REAL,
                        trending_alignment REAL,
                        historical_performance REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Predictions history
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS predictions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        content_id TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        predicted_value REAL NOT NULL,
                        actual_value REAL,
                        confidence_lower REAL,
                        confidence_upper REAL,
                        model_used TEXT,
                        model_accuracy REAL,
                        prediction_date TIMESTAMP,
                        evaluation_date TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Trend analysis results
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trend_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        metric_type TEXT NOT NULL,
                        platform TEXT,
                        trend_direction TEXT,
                        trend_strength REAL,
                        r_squared REAL,
                        statistical_significance REAL,
                        analysis_period_days INTEGER,
                        forecast_data JSON,
                        change_points JSON,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Performance insights
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS performance_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        insight_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        description TEXT,
                        impact_score REAL,
                        confidence REAL,
                        priority TEXT,
                        recommended_actions JSON,
                        supporting_data JSON,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_perf_id ON content_performance(content_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_perf_date ON content_performance(upload_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_content ON predictions(content_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_metric ON predictions(metric_type)")
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Database initialization error: {e}")
    
    async def predict_content_performance(self, content_metadata: Dict[str, Any], 
                                        metric_type: MetricType = MetricType.ENGAGEMENT_RATE) -> PredictionResult:
        """Predict content performance using ML models."""
        try:
            if not self.analytics_config.get('enabled', True):
                return self._get_fallback_prediction(metric_type)
            
            # Extract features from content
            features = self._extract_content_features(content_metadata)
            
            # Get or train model
            model_name = self._select_best_model(metric_type)
            model, scaler = await self._get_trained_model(metric_type, model_name)
            
            if model is None:
                return self._get_fallback_prediction(metric_type)
            
            # Prepare feature vector
            feature_vector = self._features_to_vector(features)
            if scaler:
                feature_vector = scaler.transform([feature_vector])
            else:
                feature_vector = [feature_vector]
            
            # Make prediction
            prediction = model.predict(feature_vector)[0]
            
            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(
                model, feature_vector, metric_type
            )
            
            # Get feature importance
            feature_importance = self._get_feature_importance(model, features)
            
            # Analyze factors
            factors_analysis = self._analyze_prediction_factors(features, prediction)
            
            result = PredictionResult(
                predicted_value=max(0, prediction),
                confidence_interval=confidence_interval,
                model_accuracy=self._get_model_accuracy(metric_type, model_name),
                feature_importance=feature_importance,
                prediction_date=datetime.now(timezone.utc),
                model_used=model_name,
                factors_analysis=factors_analysis
            )
            
            # Store prediction
            await self._store_prediction(content_metadata.get('id'), result, metric_type)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prediction error: {e}")
            return self._get_fallback_prediction(metric_type)
    
    async def analyze_performance_trends(self, platform: str = None, 
                                       days: int = 30) -> List[TrendAnalysis]:
        """Analyze performance trends using statistical methods."""
        try:
            trends = []
            
            for metric_type in MetricType:
                trend = await self._analyze_metric_trend(metric_type, platform, days)
                if trend:
                    trends.append(trend)
            
            # Store trend analysis
            await self._store_trend_analysis(trends)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Trend analysis error: {e}")
            return []
    
    async def generate_performance_insights(self) -> List[PerformanceInsight]:
        """Generate actionable performance insights."""
        try:
            insights = []
            
            # Analyze recent performance patterns
            pattern_insights = await self._analyze_performance_patterns()
            insights.extend(pattern_insights)
            
            # Identify optimization opportunities
            optimization_insights = await self._identify_optimization_opportunities()
            insights.extend(optimization_insights)
            
            # Detect anomalies
            anomaly_insights = await self._detect_performance_anomalies()
            insights.extend(anomaly_insights)
            
            # Competitive analysis insights
            competitive_insights = await self._analyze_competitive_position()
            insights.extend(competitive_insights)
            
            # Store insights
            await self._store_insights(insights)
            
            return sorted(insights, key=lambda x: x.impact_score, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Insights generation error: {e}")
            return []
    
    async def get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive analytics data for dashboard."""
        try:
            # Performance overview
            overview = await self._get_performance_overview()
            
            # Recent trends
            trends = await self.analyze_performance_trends(days=7)
            
            # Top insights
            insights = await self.generate_performance_insights()
            top_insights = insights[:5]
            
            # Model performance metrics
            model_metrics = await self._get_model_performance_metrics()
            
            # Prediction accuracy over time
            accuracy_history = await self._get_prediction_accuracy_history()
            
            return {
                'overview': overview,
                'trends': [asdict(trend) for trend in trends],
                'insights': [asdict(insight) for insight in top_insights],
                'model_metrics': model_metrics,
                'accuracy_history': accuracy_history,
                'last_updated': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Dashboard data error: {e}")
            return {'error': str(e)}
    
    def _extract_content_features(self, content_metadata: Dict[str, Any]) -> ContentFeatures:
        """Extract ML features from content metadata."""
        try:
            upload_date = datetime.fromisoformat(
                content_metadata.get('upload_date', datetime.now().isoformat())
            )
            
            return ContentFeatures(
                title_length=len(content_metadata.get('title', '')),
                description_length=len(content_metadata.get('description', '')),
                tag_count=len(content_metadata.get('tags', [])),
                upload_hour=upload_date.hour,
                upload_day=upload_date.weekday(),
                duration_minutes=content_metadata.get('duration_minutes', 0),
                thumbnail_quality_score=content_metadata.get('thumbnail_quality_score', 0.5),
                topic_relevance_score=content_metadata.get('topic_relevance_score', 0.5),
                seasonal_factor=self._calculate_seasonal_factor(upload_date),
                competition_density=content_metadata.get('competition_density', 0.5),
                trending_alignment=content_metadata.get('trending_alignment', 0.5),
                historical_performance=content_metadata.get('historical_performance', 0.5)
            )
            
        except Exception as e:
            self.logger.error(f"Feature extraction error: {e}")
            return ContentFeatures(
                title_length=50, description_length=200, tag_count=5,
                upload_hour=12, upload_day=1, duration_minutes=10,
                thumbnail_quality_score=0.5, topic_relevance_score=0.5,
                seasonal_factor=1.0, competition_density=0.5,
                trending_alignment=0.5, historical_performance=0.5
            )
    
    def _features_to_vector(self, features: ContentFeatures) -> List[float]:
        """Convert features to numerical vector for ML."""
        return [
            features.title_length,
            features.description_length,
            features.tag_count,
            features.upload_hour,
            features.upload_day,
            features.duration_minutes,
            features.thumbnail_quality_score,
            features.topic_relevance_score,
            features.seasonal_factor,
            features.competition_density,
            features.trending_alignment,
            features.historical_performance
        ]
    
    def _calculate_seasonal_factor(self, date: datetime) -> float:
        """Calculate seasonal factor for the given date."""
        try:
            # Simple seasonal calculation based on month and day
            month_factor = 1.0 + 0.2 * np.sin(2 * np.pi * date.month / 12)
            day_factor = 1.0 + 0.1 * np.sin(2 * np.pi * date.weekday() / 7)
            return month_factor * day_factor
        except:
            return 1.0
    
    async def _get_trained_model(self, metric_type: MetricType, model_name: str) -> Tuple[Any, Any]:
        """Get or train ML model for the specified metric."""
        try:
            cache_key = f"{metric_type.value}_{model_name}"
            
            # Check cache
            if cache_key in self.trained_models:
                return self.trained_models[cache_key], self.scalers.get(cache_key)
            
            # Load training data
            X, y = await self._load_training_data(metric_type)
            
            if len(X) < self.analytics_config.get('min_training_samples', 50):
                self.logger.warning(f"Insufficient training data for {metric_type.value}")
                return None, None
            
            # Train model
            model, scaler = await self._train_model(X, y, model_name)
            
            # Cache model
            self.trained_models[cache_key] = model
            if scaler:
                self.scalers[cache_key] = scaler
            
            return model, scaler
            
        except Exception as e:
            self.logger.error(f"Model training error: {e}")
            return None, None
    
    async def _load_training_data(self, metric_type: MetricType) -> Tuple[List[List[float]], List[float]]:
        """Load training data for the specified metric."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get performance data with features
                cursor.execute("""
                    SELECT cf.*, cp.engagement_rate, cp.view_count, cp.watch_time_minutes,
                           cp.ctr, cp.revenue, cp.subscriber_gain
                    FROM content_features cf
                    JOIN content_performance cp ON cf.content_id = cp.content_id
                    WHERE cp.upload_date > datetime('now', '-90 days')
                    ORDER BY cp.upload_date DESC
                """)
                
                rows = cursor.fetchall()
                
                if not rows:
                    return [], []
                
                X = []
                y = []
                
                for row in rows:
                    # Extract features (skip id and content_id)
                    features = list(row[2:14])  # Feature columns
                    
                    # Extract target based on metric type
                    if metric_type == MetricType.ENGAGEMENT_RATE:
                        target = row[14] or 0  # engagement_rate
                    elif metric_type == MetricType.VIEW_COUNT:
                        target = row[15] or 0  # view_count
                    elif metric_type == MetricType.WATCH_TIME:
                        target = row[16] or 0  # watch_time_minutes
                    elif metric_type == MetricType.CLICK_THROUGH_RATE:
                        target = row[17] or 0  # ctr
                    elif metric_type == MetricType.REVENUE:
                        target = row[18] or 0  # revenue
                    elif metric_type == MetricType.SUBSCRIBER_GROWTH:
                        target = row[19] or 0  # subscriber_gain
                    else:
                        target = row[14] or 0  # default to engagement_rate
                    
                    X.append(features)
                    y.append(target)
                
                return X, y
                
        except Exception as e:
            self.logger.error(f"Training data loading error: {e}")
            return [], []
    
    async def _train_model(self, X: List[List[float]], y: List[float], 
                          model_name: str) -> Tuple[Any, Any]:
        """Train ML model with the given data."""
        try:
            if not SKLEARN_AVAILABLE:
                return self._train_simple_model(X, y)
            
            X_array = np.array(X)
            y_array = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_array, y_array, test_size=0.2, random_state=42
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Select and train model
            if model_name == PredictionModel.RANDOM_FOREST.value:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            elif model_name == PredictionModel.GRADIENT_BOOSTING.value:
                model = GradientBoostingRegressor(n_estimators=100, random_state=42)
            elif model_name == PredictionModel.LINEAR_REGRESSION.value:
                model = Ridge(alpha=1.0)
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42)
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = r2_score(y_test, y_pred)
            
            self.logger.info(f"Model {model_name} trained with R² = {accuracy:.3f}")
            
            return model, scaler
            
        except Exception as e:
            self.logger.error(f"Model training error: {e}")
            return self._train_simple_model(X, y)
    
    def _train_simple_model(self, X: List[List[float]], y: List[float]) -> Tuple[Any, Any]:
        """Train simple linear regression model without sklearn."""
        try:
            # Simple linear regression using numpy
            if len(X) == 0 or len(y) == 0:
                return None, None
            
            X_array = np.array(X)
            y_array = np.array(y)
            
            # Add bias term
            X_with_bias = np.column_stack([np.ones(len(X)), X_array])
            
            # Normal equation: theta = (X^T X)^(-1) X^T y
            try:
                theta = np.linalg.solve(X_with_bias.T @ X_with_bias, X_with_bias.T @ y_array)
            except np.linalg.LinAlgError:
                # Use pseudo-inverse if matrix is singular
                theta = np.linalg.pinv(X_with_bias.T @ X_with_bias) @ X_with_bias.T @ y_array
            
            # Create simple model object
            class SimpleLinearModel:
                def __init__(self, coefficients):
                    self.coef_ = coefficients[1:]  # Exclude bias
                    self.intercept_ = coefficients[0]
                
                def predict(self, X):
                    X_array = np.array(X)
                    if X_array.ndim == 1:
                        X_array = X_array.reshape(1, -1)
                    return X_array @ self.coef_ + self.intercept_
            
            model = SimpleLinearModel(theta)
            return model, None
            
        except Exception as e:
            self.logger.error(f"Simple model training error: {e}")
            return None, None
    
    def _select_best_model(self, metric_type: MetricType) -> str:
        """Select the best model for the given metric type."""
        # Model selection based on metric characteristics
        model_preferences = {
            MetricType.ENGAGEMENT_RATE: PredictionModel.RANDOM_FOREST.value,
            MetricType.VIEW_COUNT: PredictionModel.GRADIENT_BOOSTING.value,
            MetricType.WATCH_TIME: PredictionModel.RANDOM_FOREST.value,
            MetricType.CLICK_THROUGH_RATE: PredictionModel.LINEAR_REGRESSION.value,
            MetricType.REVENUE: PredictionModel.GRADIENT_BOOSTING.value,
            MetricType.SUBSCRIBER_GROWTH: PredictionModel.RANDOM_FOREST.value
        }
        
        return model_preferences.get(metric_type, PredictionModel.RANDOM_FOREST.value)
    
    def _calculate_confidence_interval(self, model: Any, feature_vector: List[List[float]], 
                                     metric_type: MetricType) -> Tuple[float, float]:
        """Calculate confidence interval for prediction."""
        try:
            prediction = model.predict(feature_vector)[0]
            
            # Simple confidence interval based on historical variance
            variance = self._get_metric_variance(metric_type)
            margin = 1.96 * np.sqrt(variance)  # 95% confidence interval
            
            return (max(0, prediction - margin), prediction + margin)
            
        except Exception as e:
            self.logger.error(f"Confidence interval calculation error: {e}")
            return (0, 1)
    
    def _get_metric_variance(self, metric_type: MetricType) -> float:
        """Get historical variance for the metric type."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if metric_type == MetricType.ENGAGEMENT_RATE:
                    cursor.execute("SELECT engagement_rate FROM content_performance WHERE engagement_rate > 0")
                elif metric_type == MetricType.VIEW_COUNT:
                    cursor.execute("SELECT view_count FROM content_performance WHERE view_count > 0")
                else:
                    cursor.execute("SELECT engagement_rate FROM content_performance WHERE engagement_rate > 0")
                
                values = [row[0] for row in cursor.fetchall()]
                
                if len(values) > 1:
                    return statistics.variance(values)
                else:
                    return 0.01  # Default small variance
                    
        except Exception as e:
            self.logger.error(f"Variance calculation error: {e}")
            return 0.01
    
    def _get_feature_importance(self, model: Any, features: ContentFeatures) -> Dict[str, float]:
        """Get feature importance from the model."""
        try:
            feature_names = [
                'title_length', 'description_length', 'tag_count',
                'upload_hour', 'upload_day', 'duration_minutes',
                'thumbnail_quality_score', 'topic_relevance_score',
                'seasonal_factor', 'competition_density',
                'trending_alignment', 'historical_performance'
            ]
            
            if hasattr(model, 'feature_importances_'):
                importances = model.feature_importances_
            elif hasattr(model, 'coef_'):
                importances = np.abs(model.coef_)
            else:
                # Equal importance for simple models
                importances = np.ones(len(feature_names)) / len(feature_names)
            
            return dict(zip(feature_names, importances))
            
        except Exception as e:
            self.logger.error(f"Feature importance error: {e}")
            return {}
    
    def _analyze_prediction_factors(self, features: ContentFeatures, 
                                  prediction: float) -> Dict[str, Any]:
        """Analyze factors contributing to the prediction."""
        try:
            factors = {
                'content_quality': {
                    'title_optimization': min(features.title_length / 60, 1.0),
                    'description_completeness': min(features.description_length / 500, 1.0),
                    'tag_utilization': min(features.tag_count / 10, 1.0)
                },
                'timing_factors': {
                    'upload_hour_score': self._score_upload_hour(features.upload_hour),
                    'day_of_week_score': self._score_upload_day(features.upload_day),
                    'seasonal_alignment': features.seasonal_factor
                },
                'market_conditions': {
                    'competition_level': 1.0 - features.competition_density,
                    'trending_alignment': features.trending_alignment,
                    'topic_relevance': features.topic_relevance_score
                },
                'production_quality': {
                    'thumbnail_quality': features.thumbnail_quality_score,
                    'duration_optimization': self._score_duration(features.duration_minutes),
                    'historical_performance': features.historical_performance
                }
            }
            
            return factors
            
        except Exception as e:
            self.logger.error(f"Factor analysis error: {e}")
            return {}
    
    def _score_upload_hour(self, hour: int) -> float:
        """Score upload hour (peak hours get higher scores)."""
        # Peak hours: 6-9 AM, 12-2 PM, 7-10 PM
        peak_hours = [6, 7, 8, 9, 12, 13, 14, 19, 20, 21, 22]
        return 1.0 if hour in peak_hours else 0.6
    
    def _score_upload_day(self, day: int) -> float:
        """Score upload day (weekdays typically better)."""
        # Monday=0, Sunday=6
        weekday_scores = [0.9, 1.0, 1.0, 0.95, 0.85, 0.7, 0.6]
        return weekday_scores[day] if 0 <= day < 7 else 0.8
    
    def _score_duration(self, duration: float) -> float:
        """Score content duration (optimal ranges get higher scores)."""
        if 8 <= duration <= 12:  # Optimal range
            return 1.0
        elif 5 <= duration <= 15:  # Good range
            return 0.8
        elif 3 <= duration <= 20:  # Acceptable range
            return 0.6
        else:
            return 0.4
    
    async def _analyze_metric_trend(self, metric_type: MetricType, 
                                  platform: str, days: int) -> Optional[TrendAnalysis]:
        """Analyze trend for a specific metric."""
        try:
            # Get historical data
            data = await self._get_metric_history(metric_type, platform, days)
            
            if len(data) < self.min_data_points:
                return None
            
            # Perform trend analysis
            trend_direction, trend_strength = self._calculate_trend(data)
            
            # Statistical significance
            significance = self._calculate_trend_significance(data)
            
            # Seasonal decomposition (simplified)
            seasonal_component = self._detect_seasonality(data)
            
            # Forecasting
            forecast_7 = self._forecast_values(data, 7)
            forecast_30 = self._forecast_values(data, 30)
            
            # Change point detection
            change_points = self._detect_change_points(data)
            
            # R-squared for trend fit
            r_squared = self._calculate_trend_r_squared(data)
            
            return TrendAnalysis(
                metric_type=metric_type.value,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                seasonal_component=seasonal_component,
                forecast_7_days=forecast_7,
                forecast_30_days=forecast_30,
                change_points=change_points,
                statistical_significance=significance,
                r_squared=r_squared
            )
            
        except Exception as e:
            self.logger.error(f"Trend analysis error for {metric_type}: {e}")
            return None
    
    async def _get_metric_history(self, metric_type: MetricType, 
                                platform: str, days: int) -> List[Tuple[datetime, float]]:
        """Get historical data for metric analysis."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Build query based on metric type
                metric_column = {
                    MetricType.ENGAGEMENT_RATE: 'engagement_rate',
                    MetricType.VIEW_COUNT: 'view_count',
                    MetricType.WATCH_TIME: 'watch_time_minutes',
                    MetricType.CLICK_THROUGH_RATE: 'ctr',
                    MetricType.REVENUE: 'revenue',
                    MetricType.SUBSCRIBER_GROWTH: 'subscriber_gain'
                }.get(metric_type, 'engagement_rate')
                
                query = f"""
                    SELECT upload_date, AVG({metric_column}) as avg_value
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-{days} days')
                """
                
                if platform:
                    query += f" AND platform = '{platform}'"
                
                query += " GROUP BY DATE(upload_date) ORDER BY upload_date"
                
                cursor.execute(query)
                rows = cursor.fetchall()
                
                return [(datetime.fromisoformat(row[0]), row[1] or 0) for row in rows]
                
        except Exception as e:
            self.logger.error(f"Metric history error: {e}")
            return []
    
    def _calculate_trend(self, data: List[Tuple[datetime, float]]) -> Tuple[TrendDirection, float]:
        """Calculate trend direction and strength."""
        try:
            if len(data) < 2:
                return TrendDirection.STABLE, 0.0
            
            values = [point[1] for point in data]
            
            # Linear regression for trend
            x = np.arange(len(values))
            
            if SCIPY_AVAILABLE:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            else:
                # Simple slope calculation
                slope = (values[-1] - values[0]) / (len(values) - 1)
                r_value = 0.5  # Default correlation
            
            # Determine trend direction
            if abs(slope) < 0.01:  # Threshold for stability
                direction = TrendDirection.STABLE
            elif slope > 0:
                direction = TrendDirection.INCREASING
            else:
                direction = TrendDirection.DECREASING
            
            # Calculate volatility
            volatility = np.std(values) / (np.mean(values) + 1e-6)
            if volatility > 0.5:
                direction = TrendDirection.VOLATILE
            
            strength = abs(r_value) if SCIPY_AVAILABLE else min(abs(slope) * 10, 1.0)
            
            return direction, strength
            
        except Exception as e:
            self.logger.error(f"Trend calculation error: {e}")
            return TrendDirection.STABLE, 0.0
    
    def _calculate_trend_significance(self, data: List[Tuple[datetime, float]]) -> float:
        """Calculate statistical significance of trend."""
        try:
            if len(data) < 3 or not SCIPY_AVAILABLE:
                return 0.5
            
            values = [point[1] for point in data]
            x = np.arange(len(values))
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Return 1 - p_value (higher = more significant)
            return max(0, min(1, 1 - p_value))
            
        except Exception as e:
            self.logger.error(f"Significance calculation error: {e}")
            return 0.5
    
    def _detect_seasonality(self, data: List[Tuple[datetime, float]]) -> Optional[Dict[str, float]]:
        """Detect seasonal patterns in the data."""
        try:
            if len(data) < 14:  # Need at least 2 weeks
                return None
            
            # Group by day of week
            day_values = defaultdict(list)
            for date, value in data:
                day_values[date.weekday()].append(value)
            
            # Calculate average for each day
            day_averages = {}
            for day, values in day_values.items():
                if values:
                    day_averages[f"day_{day}"] = statistics.mean(values)
            
            return day_averages if day_averages else None
            
        except Exception as e:
            self.logger.error(f"Seasonality detection error: {e}")
            return None
    
    def _forecast_values(self, data: List[Tuple[datetime, float]], days: int) -> List[float]:
        """Forecast future values using simple methods."""
        try:
            if len(data) < 3:
                return [data[-1][1]] * days if data else [0] * days
            
            values = [point[1] for point in data]
            
            # Simple exponential smoothing
            alpha = 0.3  # Smoothing parameter
            forecast = []
            last_value = values[-1]
            
            # Calculate trend
            recent_trend = (values[-1] - values[-3]) / 2 if len(values) >= 3 else 0
            
            for i in range(days):
                # Exponential smoothing with trend
                next_value = last_value + recent_trend * (1 - alpha) ** i
                forecast.append(max(0, next_value))
            
            return forecast
            
        except Exception as e:
            self.logger.error(f"Forecasting error: {e}")
            return [0] * days
    
    def _detect_change_points(self, data: List[Tuple[datetime, float]]) -> List[datetime]:
        """Detect significant change points in the data."""
        try:
            if len(data) < 10:
                return []
            
            values = [point[1] for point in data]
            dates = [point[0] for point in data]
            change_points = []
            
            # Simple change point detection using moving averages
            window = min(5, len(values) // 3)
            
            for i in range(window, len(values) - window):
                before_avg = statistics.mean(values[i-window:i])
                after_avg = statistics.mean(values[i:i+window])
                
                # Significant change threshold
                if abs(after_avg - before_avg) > 0.2 * before_avg:
                    change_points.append(dates[i])
            
            return change_points
            
        except Exception as e:
            self.logger.error(f"Change point detection error: {e}")
            return []
    
    def _calculate_trend_r_squared(self, data: List[Tuple[datetime, float]]) -> float:
        """Calculate R-squared for trend fit."""
        try:
            if len(data) < 3:
                return 0.0
            
            values = [point[1] for point in data]
            x = np.arange(len(values))
            
            if SCIPY_AVAILABLE:
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
                return r_value ** 2
            else:
                # Simple correlation calculation
                mean_x = statistics.mean(x)
                mean_y = statistics.mean(values)
                
                numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(len(x)))
                denominator_x = sum((x[i] - mean_x) ** 2 for i in range(len(x)))
                denominator_y = sum((values[i] - mean_y) ** 2 for i in range(len(values)))
                
                if denominator_x * denominator_y == 0:
                    return 0.0
                
                correlation = numerator / (denominator_x * denominator_y) ** 0.5
                return correlation ** 2
                
        except Exception as e:
            self.logger.error(f"R-squared calculation error: {e}")
            return 0.0
    
    def _get_fallback_prediction(self, metric_type: MetricType) -> PredictionResult:
        """Get fallback prediction when ML models fail."""
        # Default predictions based on typical performance
        defaults = {
            MetricType.ENGAGEMENT_RATE: 0.05,
            MetricType.VIEW_COUNT: 1000,
            MetricType.WATCH_TIME: 300,
            MetricType.CLICK_THROUGH_RATE: 0.03,
            MetricType.REVENUE: 10.0,
            MetricType.SUBSCRIBER_GROWTH: 5
        }
        
        predicted_value = defaults.get(metric_type, 0.05)
        
        return PredictionResult(
            predicted_value=predicted_value,
            confidence_interval=(predicted_value * 0.5, predicted_value * 1.5),
            model_accuracy=0.6,
            feature_importance={},
            prediction_date=datetime.now(timezone.utc),
            model_used="fallback",
            factors_analysis={}
        )
    
    async def _store_prediction(self, content_id: str, result: PredictionResult, 
                              metric_type: MetricType):
        """Store prediction result in database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO predictions (
                        content_id, metric_type, predicted_value,
                        confidence_lower, confidence_upper, model_used,
                        model_accuracy, prediction_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    content_id, metric_type.value, result.predicted_value,
                    result.confidence_interval[0], result.confidence_interval[1],
                    result.model_used, result.model_accuracy,
                    result.prediction_date.isoformat()
                ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Prediction storage error: {e}")
    
    async def _store_trend_analysis(self, trends: List[TrendAnalysis]):
        """Store trend analysis results."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for trend in trends:
                    cursor.execute("""
                        INSERT INTO trend_analysis (
                            metric_type, trend_direction, trend_strength,
                            r_squared, statistical_significance,
                            analysis_period_days, forecast_data, change_points
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trend.metric_type, trend.trend_direction.value,
                        trend.trend_strength, trend.r_squared,
                        trend.statistical_significance, 30,
                        json.dumps({
                            'forecast_7': trend.forecast_7_days,
                            'forecast_30': trend.forecast_30_days
                        }),
                        json.dumps([cp.isoformat() for cp in trend.change_points])
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Trend storage error: {e}")
    
    async def _store_insights(self, insights: List[PerformanceInsight]):
        """Store performance insights."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for insight in insights:
                    cursor.execute("""
                        INSERT INTO performance_insights (
                            insight_type, title, description, impact_score,
                            confidence, priority, recommended_actions, supporting_data
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        insight.insight_type, insight.title, insight.description,
                        insight.impact_score, insight.confidence, insight.priority,
                        json.dumps(insight.recommended_actions),
                        json.dumps(insight.supporting_data)
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Insights storage error: {e}")
    
    async def _analyze_performance_patterns(self) -> List[PerformanceInsight]:
        """Analyze performance patterns to generate insights."""
        insights = []
        
        try:
            # Analyze upload timing patterns
            timing_insight = await self._analyze_timing_patterns()
            if timing_insight:
                insights.append(timing_insight)
            
            # Analyze content length patterns
            length_insight = await self._analyze_length_patterns()
            if length_insight:
                insights.append(length_insight)
            
            # Analyze engagement patterns
            engagement_insight = await self._analyze_engagement_patterns()
            if engagement_insight:
                insights.append(engagement_insight)
            
        except Exception as e:
            self.logger.error(f"Pattern analysis error: {e}")
        
        return insights
    
    async def _identify_optimization_opportunities(self) -> List[PerformanceInsight]:
        """Identify content optimization opportunities."""
        insights = []
        
        try:
            # Low-performing content analysis
            underperforming = await self._find_underperforming_content()
            if underperforming:
                insights.append(PerformanceInsight(
                    insight_type="optimization",
                    title="Underperforming Content Detected",
                    description=f"Found {len(underperforming)} pieces of content with below-average performance",
                    impact_score=0.8,
                    confidence=0.9,
                    recommended_actions=[
                        "Review content quality and engagement factors",
                        "Optimize titles and thumbnails",
                        "Adjust posting schedule",
                        "Improve content promotion strategy"
                    ],
                    supporting_data={"underperforming_count": len(underperforming)},
                    priority="high"
                ))
            
        except Exception as e:
            self.logger.error(f"Optimization analysis error: {e}")
        
        return insights
    
    async def _detect_performance_anomalies(self) -> List[PerformanceInsight]:
        """Detect performance anomalies."""
        insights = []
        
        try:
            # Check for sudden performance drops
            recent_performance = await self._get_recent_performance_metrics()
            historical_avg = await self._get_historical_average_performance()
            
            if recent_performance and historical_avg:
                performance_ratio = recent_performance / historical_avg
                
                if performance_ratio < 0.7:  # 30% drop
                    insights.append(PerformanceInsight(
                        insight_type="anomaly",
                        title="Performance Drop Detected",
                        description=f"Recent performance is {(1-performance_ratio)*100:.1f}% below historical average",
                        impact_score=0.9,
                        confidence=0.8,
                        recommended_actions=[
                            "Investigate recent content changes",
                            "Check for algorithm updates",
                            "Review competitor activity",
                            "Analyze audience feedback"
                        ],
                        supporting_data={
                            "recent_performance": recent_performance,
                            "historical_average": historical_avg,
                            "performance_ratio": performance_ratio
                        },
                        priority="high"
                    ))
            
        except Exception as e:
            self.logger.error(f"Anomaly detection error: {e}")
        
        return insights
    
    async def _analyze_competitive_position(self) -> List[PerformanceInsight]:
        """Analyze competitive position."""
        insights = []
        
        try:
            # Placeholder for competitive analysis
            # This would integrate with external APIs for competitor data
            insights.append(PerformanceInsight(
                insight_type="competitive",
                title="Competitive Analysis Available",
                description="Regular competitive analysis helps maintain market position",
                impact_score=0.6,
                confidence=0.7,
                recommended_actions=[
                    "Monitor competitor content strategies",
                    "Analyze trending topics in your niche",
                    "Identify content gaps and opportunities"
                ],
                supporting_data={},
                priority="medium"
            ))
            
        except Exception as e:
            self.logger.error(f"Competitive analysis error: {e}")
        
        return insights
    
    async def _get_performance_overview(self) -> Dict[str, Any]:
        """Get performance overview statistics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Recent performance metrics
                cursor.execute("""
                    SELECT 
                        AVG(engagement_rate) as avg_engagement,
                        AVG(view_count) as avg_views,
                        AVG(watch_time_minutes) as avg_watch_time,
                        COUNT(*) as total_content
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-30 days')
                """)
                
                row = cursor.fetchone()
                
                return {
                    'avg_engagement_rate': row[0] or 0,
                    'avg_view_count': row[1] or 0,
                    'avg_watch_time': row[2] or 0,
                    'total_content_30_days': row[3] or 0,
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Performance overview error: {e}")
            return {}
    
    async def _get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get ML model performance metrics."""
        try:
            metrics = {}
            
            for metric_type in MetricType:
                accuracy = self._get_model_accuracy(metric_type, "random_forest")
                metrics[metric_type.value] = {
                    'accuracy': accuracy,
                    'model_type': self._select_best_model(metric_type),
                    'last_trained': datetime.now(timezone.utc).isoformat()
                }
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Model metrics error: {e}")
            return {}
    
    def _get_model_accuracy(self, metric_type: MetricType, model_name: str) -> float:
        """Get cached model accuracy or default."""
        # This would be stored during training
        # For now, return reasonable defaults
        return 0.75
    
    async def _get_prediction_accuracy_history(self) -> List[Dict[str, Any]]:
        """Get prediction accuracy over time."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(prediction_date) as date,
                        AVG(model_accuracy) as avg_accuracy,
                        COUNT(*) as prediction_count
                    FROM predictions
                    WHERE prediction_date > datetime('now', '-30 days')
                    GROUP BY DATE(prediction_date)
                    ORDER BY date
                """)
                
                return [{
                    'date': row[0],
                    'accuracy': row[1] or 0,
                    'count': row[2] or 0
                } for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Accuracy history error: {e}")
            return []
    
    # Helper methods for insights
    async def _analyze_timing_patterns(self) -> Optional[PerformanceInsight]:
        """Analyze upload timing patterns."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get performance by hour of day
                cursor.execute("""
                    SELECT 
                        CAST(strftime('%H', upload_date) AS INTEGER) as hour,
                        AVG(engagement_rate) as avg_engagement,
                        COUNT(*) as content_count
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-30 days')
                    GROUP BY hour
                    HAVING content_count >= 3
                    ORDER BY avg_engagement DESC
                """)
                
                hour_data = cursor.fetchall()
                if not hour_data:
                    return None
                
                best_hour = hour_data[0][0]
                best_engagement = hour_data[0][1]
                worst_hour = hour_data[-1][0]
                worst_engagement = hour_data[-1][1]
                
                # Get performance by day of week
                cursor.execute("""
                    SELECT 
                        CAST(strftime('%w', upload_date) AS INTEGER) as day_of_week,
                        AVG(engagement_rate) as avg_engagement,
                        COUNT(*) as content_count
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-30 days')
                    GROUP BY day_of_week
                    HAVING content_count >= 2
                    ORDER BY avg_engagement DESC
                """)
                
                day_data = cursor.fetchall()
                
                # Calculate impact score based on performance difference
                performance_variance = (best_engagement - worst_engagement) / best_engagement if best_engagement > 0 else 0
                impact_score = min(0.9, performance_variance * 2)  # Scale to 0-0.9
                
                if impact_score < 0.1:  # Not significant enough
                    return None
                
                day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
                best_day = day_names[day_data[0][0]] if day_data else 'Unknown'
                
                return PerformanceInsight(
                    insight_type="timing_optimization",
                    title="Optimal Upload Timing Identified",
                    description=f"Content uploaded at {best_hour}:00 on {best_day} shows {performance_variance*100:.1f}% better engagement",
                    impact_score=impact_score,
                    confidence=0.8,
                    recommended_actions=[
                        f"Schedule content uploads around {best_hour}:00",
                        f"Focus on {best_day} uploads for maximum engagement",
                        f"Avoid uploading at {worst_hour}:00 when possible",
                        "Test different time slots to validate patterns"
                    ],
                    supporting_data={
                        "best_hour": best_hour,
                        "best_engagement": best_engagement,
                        "worst_hour": worst_hour,
                        "worst_engagement": worst_engagement,
                        "best_day": best_day,
                        "performance_variance": performance_variance
                    },
                    priority="medium"
                )
                
        except Exception as e:
            self.logger.error(f"Timing pattern analysis error: {e}")
            return None
    
    async def _analyze_length_patterns(self) -> Optional[PerformanceInsight]:
        """Analyze content length patterns."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get content features with performance data
                cursor.execute("""
                    SELECT 
                        cf.title_length,
                        cf.description_length,
                        cf.tag_count,
                        cp.engagement_rate,
                        cp.view_count,
                        cp.revenue
                    FROM content_features cf
                    JOIN content_performance cp ON cf.content_id = cp.content_id
                    WHERE cp.upload_date > datetime('now', '-60 days')
                    AND cf.title_length > 0
                    AND cf.description_length > 0
                """)
                
                data = cursor.fetchall()
                if len(data) < 10:  # Need sufficient data
                    return None
                
                # Analyze title length patterns
                title_lengths = [row[0] for row in data]
                engagements = [row[3] for row in data]
                
                # Create length buckets
                short_titles = [(t, e) for t, e in zip(title_lengths, engagements) if t <= 50]
                medium_titles = [(t, e) for t, e in zip(title_lengths, engagements) if 50 < t <= 80]
                long_titles = [(t, e) for t, e in zip(title_lengths, engagements) if t > 80]
                
                if not all([short_titles, medium_titles, long_titles]):
                    return None
                
                short_avg = sum(e for _, e in short_titles) / len(short_titles)
                medium_avg = sum(e for _, e in medium_titles) / len(medium_titles)
                long_avg = sum(e for _, e in long_titles) / len(long_titles)
                
                # Find best performing length category
                length_performance = [
                    ("short", short_avg, "≤50 characters"),
                    ("medium", medium_avg, "51-80 characters"),
                    ("long", long_avg, ">80 characters")
                ]
                length_performance.sort(key=lambda x: x[1], reverse=True)
                
                best_category = length_performance[0]
                worst_category = length_performance[-1]
                
                # Calculate impact score
                performance_diff = (best_category[1] - worst_category[1]) / best_category[1] if best_category[1] > 0 else 0
                impact_score = min(0.85, performance_diff * 1.5)
                
                if impact_score < 0.15:  # Not significant enough
                    return None
                
                # Analyze description length correlation
                desc_lengths = [row[1] for row in data]
                avg_desc_length = sum(desc_lengths) / len(desc_lengths)
                
                # Find optimal tag count
                tag_counts = [row[2] for row in data]
                tag_engagement = {}
                for tag_count, engagement in zip(tag_counts, engagements):
                    if tag_count not in tag_engagement:
                        tag_engagement[tag_count] = []
                    tag_engagement[tag_count].append(engagement)
                
                optimal_tags = max(tag_engagement.keys(), 
                                 key=lambda k: sum(tag_engagement[k]) / len(tag_engagement[k]) if tag_engagement[k] else 0)
                
                return PerformanceInsight(
                    insight_type="content_length_optimization",
                    title="Content Length Optimization Opportunity",
                    description=f"{best_category[0].title()} titles ({best_category[2]}) perform {performance_diff*100:.1f}% better than other lengths",
                    impact_score=impact_score,
                    confidence=0.75,
                    recommended_actions=[
                        f"Optimize titles to {best_category[2]} for better engagement",
                        f"Target description length around {int(avg_desc_length)} characters",
                        f"Use approximately {optimal_tags} tags per content",
                        "A/B test different title lengths to validate patterns",
                        "Monitor engagement changes after length optimization"
                    ],
                    supporting_data={
                        "best_title_category": best_category[0],
                        "best_engagement": best_category[1],
                        "performance_difference": performance_diff,
                        "optimal_description_length": int(avg_desc_length),
                        "optimal_tag_count": optimal_tags,
                        "sample_size": len(data)
                    },
                    priority="medium"
                )
                
        except Exception as e:
            self.logger.error(f"Length pattern analysis error: {e}")
            return None
    
    async def _analyze_engagement_patterns(self) -> Optional[PerformanceInsight]:
        """Analyze engagement patterns and anomalies."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get recent engagement data with timestamps
                cursor.execute("""
                    SELECT 
                        upload_date,
                        engagement_rate,
                        view_count,
                        comment_count,
                        like_count,
                        share_count
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-30 days')
                    ORDER BY upload_date
                """)
                
                data = cursor.fetchall()
                if len(data) < 7:  # Need at least a week of data
                    return None
                
                engagement_rates = [row[1] for row in data]
                view_counts = [row[2] for row in data]
                
                # Calculate engagement statistics
                avg_engagement = statistics.mean(engagement_rates)
                median_engagement = statistics.median(engagement_rates)
                std_engagement = statistics.stdev(engagement_rates) if len(engagement_rates) > 1 else 0
                
                # Detect anomalies (values beyond 2 standard deviations)
                anomalies = []
                for i, rate in enumerate(engagement_rates):
                    if abs(rate - avg_engagement) > 2 * std_engagement:
                        anomalies.append((data[i][0], rate, "high" if rate > avg_engagement else "low"))
                
                # Analyze engagement trend over time
                if len(engagement_rates) >= 5:
                    # Simple trend analysis using linear regression
                    x_values = list(range(len(engagement_rates)))
                    if SCIPY_AVAILABLE:
                        slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, engagement_rates)
                        trend_strength = abs(r_value)
                        is_significant = p_value < 0.05
                    else:
                        # Fallback: simple slope calculation
                        slope = (engagement_rates[-1] - engagement_rates[0]) / len(engagement_rates)
                        trend_strength = min(1.0, abs(slope) * 10)  # Normalize
                        is_significant = trend_strength > 0.3
                else:
                    slope = 0
                    trend_strength = 0
                    is_significant = False
                
                # Analyze engagement distribution
                high_performers = [rate for rate in engagement_rates if rate > avg_engagement + std_engagement]
                low_performers = [rate for rate in engagement_rates if rate < avg_engagement - std_engagement]
                
                # Calculate engagement consistency score
                consistency_score = 1 - (std_engagement / avg_engagement) if avg_engagement > 0 else 0
                consistency_score = max(0, min(1, consistency_score))
                
                # Determine insight priority and impact
                if len(anomalies) > len(data) * 0.2:  # More than 20% anomalies
                    priority = "high"
                    impact_score = 0.8
                    insight_type = "engagement_volatility"
                    title = "High Engagement Volatility Detected"
                    description = f"Engagement shows high volatility with {len(anomalies)} anomalies in {len(data)} posts"
                elif slope < -0.01 and is_significant:  # Declining trend
                    priority = "high"
                    impact_score = 0.7
                    insight_type = "engagement_decline"
                    title = "Declining Engagement Trend"
                    description = f"Engagement rate declining by {abs(slope)*100:.2f}% per post over recent period"
                elif slope > 0.01 and is_significant:  # Growing trend
                    priority = "medium"
                    impact_score = 0.6
                    insight_type = "engagement_growth"
                    title = "Positive Engagement Trend"
                    description = f"Engagement rate improving by {slope*100:.2f}% per post - maintain current strategy"
                elif consistency_score < 0.5:  # Low consistency
                    priority = "medium"
                    impact_score = 0.5
                    insight_type = "engagement_inconsistency"
                    title = "Inconsistent Engagement Performance"
                    description = f"Engagement varies significantly (consistency score: {consistency_score:.2f})"
                else:
                    return None  # No significant patterns found
                
                # Generate recommendations based on analysis
                recommendations = []
                if len(anomalies) > 0:
                    recommendations.append("Investigate content that caused engagement spikes or drops")
                    recommendations.append("Analyze successful content patterns for replication")
                
                if slope < 0 and is_significant:
                    recommendations.extend([
                        "Review recent content strategy changes",
                        "Analyze competitor performance for market shifts",
                        "Consider A/B testing new content formats"
                    ])
                elif slope > 0 and is_significant:
                    recommendations.extend([
                        "Continue current successful content strategy",
                        "Scale up production of high-performing content types",
                        "Document successful patterns for team reference"
                    ])
                
                if consistency_score < 0.5:
                    recommendations.extend([
                        "Establish content quality guidelines",
                        "Implement content review process before publishing",
                        "Focus on consistent posting schedule and format"
                    ])
                
                return PerformanceInsight(
                    insight_type=insight_type,
                    title=title,
                    description=description,
                    impact_score=impact_score,
                    confidence=0.8 if is_significant else 0.6,
                    recommended_actions=recommendations,
                    supporting_data={
                        "average_engagement": avg_engagement,
                        "median_engagement": median_engagement,
                        "std_deviation": std_engagement,
                        "consistency_score": consistency_score,
                        "trend_slope": slope,
                        "trend_strength": trend_strength,
                        "anomaly_count": len(anomalies),
                        "high_performers": len(high_performers),
                        "low_performers": len(low_performers),
                        "sample_size": len(data)
                    },
                    priority=priority
                )
                
        except Exception as e:
            self.logger.error(f"Engagement pattern analysis error: {e}")
            return None
    
    async def _find_underperforming_content(self) -> List[str]:
        """Find underperforming content IDs."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT content_id
                    FROM content_performance
                    WHERE engagement_rate < (
                        SELECT AVG(engagement_rate) * 0.5
                        FROM content_performance
                        WHERE upload_date > datetime('now', '-30 days')
                    )
                    AND upload_date > datetime('now', '-30 days')
                """)
                
                return [row[0] for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Underperforming content search error: {e}")
            return []
    
    async def _get_recent_performance_metrics(self) -> Optional[float]:
        """Get recent performance average."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT AVG(engagement_rate)
                    FROM content_performance
                    WHERE upload_date > datetime('now', '-7 days')
                """)
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception as e:
            self.logger.error(f"Recent performance error: {e}")
            return None
    
    async def _get_historical_average_performance(self) -> Optional[float]:
        """Get historical average performance."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT AVG(engagement_rate)
                    FROM content_performance
                    WHERE upload_date BETWEEN datetime('now', '-60 days') 
                    AND datetime('now', '-30 days')
                """)
                
                result = cursor.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception as e:
            self.logger.error(f"Historical performance error: {e}")
            return None


if __name__ == "__main__":
    # Example usage
    async def main():
        agent = PerformanceAnalyticsAgent()
        
        # Example content metadata
        content = {
            'id': 'test_content_001',
            'title': 'How to Build Amazing AI Applications',
            'description': 'A comprehensive guide to building AI applications with modern tools and frameworks.',
            'tags': ['AI', 'programming', 'tutorial', 'technology'],
            'duration_minutes': 12.5,
            'upload_date': datetime.now().isoformat(),
            'thumbnail_quality_score': 0.8,
            'topic_relevance_score': 0.9,
            'competition_density': 0.6,
            'trending_alignment': 0.7,
            'historical_performance': 0.75
        }
        
        # Test prediction
        prediction = await agent.predict_content_performance(content)
        print(f"Predicted engagement rate: {prediction.predicted_value:.3f}")
        print(f"Confidence interval: {prediction.confidence_interval}")
        
        # Test trend analysis
        trends = await agent.analyze_performance_trends()
        print(f"Found {len(trends)} trend analyses")
        
        # Test insights generation
        insights = await agent.generate_performance_insights()
        print(f"Generated {len(insights)} performance insights")
        
        # Test dashboard data
        dashboard_data = await agent.get_analytics_dashboard_data()
        print(f"Dashboard data keys: {list(dashboard_data.keys())}")
    
    # Run the example
    asyncio.run(main())