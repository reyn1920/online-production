#!/usr/bin/env python3
"""
TRAE.AI Revenue Tracker - Comprehensive Revenue Analytics & Forecasting System
Tracks all income streams, provides real - time analytics, forecasting, and alerts
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
import mailchimp3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import stripe
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query

# API Clients

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger
from plotly.subplots import make_subplots
from pydantic import BaseModel
from scipy import stats
from sendgrid import SendGridAPIClient
from sklearn.ensemble import RandomForestRegressor

# Analytics and Forecasting

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy import (Boolean, Column, DateTime, Float, Integer, Numeric, String,

    Text, create_engine)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Time series forecasting
try:

    from prophet import Prophet

    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available for advanced forecasting")

# Import existing services
try:

    from backend.services.cost_tracking_service import CostTrackingService

except ImportError:
    CostTrackingService = None

try:

    from backend.services.ai_revenue_integration import AIRevenueIntegration, ai_revenue_integration

except ImportError:
    AIRevenueIntegration = None
    ai_revenue_integration = None

# Load environment variables
load_dotenv()

Base = declarative_base()


class RevenueConfig:
    """Configuration for the revenue tracker"""


    def __init__(self):
        # YouTube Analytics
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        self.youtube_channel_id = os.getenv("YOUTUBE_CHANNEL_ID")

        # E - commerce APIs
        self.gumroad_access_token = os.getenv("GUMROAD_ACCESS_TOKEN")
        self.stripe_api_key = os.getenv("STRIPE_API_KEY")
        self.paypal_client_id = os.getenv("PAYPAL_CLIENT_ID")
        self.paypal_client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

        # Email Marketing
        self.mailchimp_api_key = os.getenv("MAILCHIMP_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")

        # Affiliate Networks
        self.amazon_associates_tag = os.getenv("AMAZON_ASSOCIATES_TAG")
        self.commission_junction_api_key = os.getenv("COMMISSION_JUNCTION_API_KEY")

        # Social Media
        self.twitter_bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        self.instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///revenue_tracker.db")

        # Directories
        self.data_dir = Path("data")
        self.reports_dir = Path("reports")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

        # Alert thresholds
        self.revenue_alert_threshold = float(
            os.getenv("REVENUE_ALERT_THRESHOLD", "1000.0")
        )
        self.growth_alert_threshold = float(
            os.getenv("GROWTH_ALERT_THRESHOLD", "0.1")
        )  # 10%

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok = True)
        self.reports_dir.mkdir(exist_ok = True)

# Database Models


class RevenueStream(Base):
    __tablename__ = "revenue_streams"

    id = Column(Integer, primary_key = True)
    source = Column(String(100), nullable = False)  # youtube, gumroad, affiliate, etc.
    platform = Column(String(100), nullable = False)
    amount = Column(Numeric(10, 2), nullable = False)
    currency = Column(String(3), default="USD")
    transaction_id = Column(String(255))
    description = Column(Text)
    metadata = Column(Text)  # JSON string for additional data
    recorded_at = Column(DateTime, default = datetime.utcnow)
    transaction_date = Column(DateTime, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)


class RevenueGoal(Base):
    __tablename__ = "revenue_goals"

    id = Column(Integer, primary_key = True)
    name = Column(String(255), nullable = False)
    target_amount = Column(Numeric(10, 2), nullable = False)
    current_amount = Column(Numeric(10, 2), default = 0)
    target_date = Column(DateTime, nullable = False)
    source_filter = Column(String(255))  # Filter by specific sources
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default = datetime.utcnow)
    updated_at = Column(DateTime, default = datetime.utcnow, onupdate = datetime.utcnow)


class RevenueAlert(Base):
    __tablename__ = "revenue_alerts"

    id = Column(Integer, primary_key = True)
    alert_type = Column(String(100), nullable = False)  # threshold, goal, anomaly
    message = Column(Text, nullable = False)
    severity = Column(String(50), default="info")  # info, warning, critical
    triggered_at = Column(DateTime, default = datetime.utcnow)
    acknowledged = Column(Boolean, default = False)
    metadata = Column(Text)  # JSON string for additional data


class RevenueForecast(Base):
    __tablename__ = "revenue_forecasts"

    id = Column(Integer, primary_key = True)
    forecast_date = Column(DateTime, nullable = False)
    predicted_amount = Column(Numeric(10, 2), nullable = False)
    confidence_lower = Column(Numeric(10, 2))
    confidence_upper = Column(Numeric(10, 2))
    model_used = Column(String(100), nullable = False)
    source_filter = Column(String(255))
    created_at = Column(DateTime, default = datetime.utcnow)

# Request/Response Models


class RevenueStreamRequest(BaseModel):
    source: str
    platform: str
    amount: float
    currency: str = "USD"
    transaction_id: Optional[str] = None
    description: Optional[str] = None
    transaction_date: datetime
    metadata: Optional[Dict[str, Any]] = None


class RevenueGoalRequest(BaseModel):
    name: str
    target_amount: float
    target_date: datetime
    source_filter: Optional[str] = None


class AnalyticsRequest(BaseModel):
    start_date: datetime
    end_date: datetime
    sources: Optional[List[str]] = None
    group_by: str = "day"  # day, week, month


class ForecastRequest(BaseModel):
    days_ahead: int = 30
    sources: Optional[List[str]] = None
    model: str = "linear"  # linear, prophet, random_forest


class YouTubeAnalytics:
    """YouTube revenue and analytics tracker"""


    def __init__(self, config: RevenueConfig):
        self.config = config
        self.session = None  # Will be initialized with aiohttp session
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.service = None
        self._initialize_youtube_service()


    def _initialize_youtube_service(self):
        """Initialize YouTube Analytics API service"""
        if self.config.youtube_api_key:
            try:
                self.service = build(
                    "youtubeAnalytics", "v2", developerKey = self.config.youtube_api_key
                )
                logger.info("✅ YouTube Analytics service initialized")
            except Exception as e:
                logger.error(f"YouTube Analytics initialization failed: {e}")


    async def get_revenue_data(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get YouTube revenue data"""
        if not self.service:
            logger.error("YouTube Analytics service not initialized")
            raise Exception("YouTube Analytics service required")

        try:
            # Get monetization data
            response = (
                self.service.reports()
                .query(
                    ids = f"channel=={self.config.youtube_channel_id}",
                        startDate = start_date.strftime("%Y-%m-%d"),
                        endDate = end_date.strftime("%Y-%m-%d"),
                        metrics="estimatedRevenue,monetizedPlaybacks,playbackBasedCpm",
                        dimensions="day",
                        )
                .execute()
            )

            revenue_data = []
            if "rows" in response:
                for row in response["rows"]:
                    revenue_data.append(
                        {
                            "date": datetime.strptime(row[0], "%Y-%m-%d"),
                                "revenue": float(row[1]) if row[1] else 0.0,
                                "monetized_playbacks": int(row[2]) if row[2] else 0,
                                "cpm": float(row[3]) if row[3] else 0.0,
                                }
                    )

            return revenue_data

        except Exception as e:
            logger.error(f"YouTube revenue data fetch failed: {e}")
            raise


class GumroadAnalytics:
    """Gumroad sales and revenue tracker"""


    def __init__(self, config: RevenueConfig):
        self.config = config
        self.base_url = "https://api.gumroad.com/v2"


    async def get_sales_data(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get Gumroad sales data"""
        if not self.config.gumroad_access_token:
            logger.error("Gumroad access token not configured")
            raise Exception("Gumroad access token required")

        try:
            headers = {"Authorization": f"Bearer {self.config.gumroad_access_token}"}

            # Get sales data
            response = requests.get(
                f"{self.base_url}/sales",
                    headers = headers,
                    params={
                    "after": start_date.strftime("%Y-%m-%d"),
                        "before": end_date.strftime("%Y-%m-%d"),
                        },
                    )

            if response.status_code == 200:
                sales_data = response.json().get("sales", [])

                processed_data = []
                for sale in sales_data:
                    processed_data.append(
                        {
                            "date": datetime.fromisoformat(
                                sale["created_at"].replace("Z", "+00:00")
                            ),
                                "amount": float(sale["price"])/100,  # Convert cents to dollars
                            "product_name": sale["product_name"],
                                "transaction_id": sale["id"],
                                "currency": sale["currency"],
                                }
                    )

                return processed_data
            else:
                logger.error(f"Gumroad API error: {response.text}")
                raise Exception(f"Gumroad API error: {response.status_code}")

        except Exception as e:
            logger.error(f"Gumroad sales data fetch failed: {e}")
            raise


class AffiliateTracker:
    """Affiliate marketing revenue tracker"""


    def __init__(self, config: RevenueConfig):
        self.config = config


    async def get_affiliate_data(
        self, start_date: datetime, end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get affiliate marketing revenue data from multiple networks"""
        affiliate_data = []
        
        try:
            # Amazon Associates API integration
            amazon_data = await self._get_amazon_associates_data(start_date, end_date)
            affiliate_data.extend(amazon_data)
            
            # Commission Junction (CJ Affiliate) integration
            cj_data = await self._get_commission_junction_data(start_date, end_date)
            affiliate_data.extend(cj_data)
            
            # ShareASale integration
            shareasale_data = await self._get_shareasale_data(start_date, end_date)
            affiliate_data.extend(shareasale_data)
            
            # Impact Radius integration
            impact_data = await self._get_impact_radius_data(start_date, end_date)
            affiliate_data.extend(impact_data)
            
            logger.info(f"Retrieved {len(affiliate_data)} affiliate transactions")
            return affiliate_data
            
        except Exception as e:
            logger.error(f"Error retrieving affiliate data: {e}")
            return []
    
    async def _get_amazon_associates_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get Amazon Associates affiliate data"""
        try:
            # Amazon Associates API requires Product Advertising API 5.0
            amazon_access_key = os.getenv('AMAZON_ACCESS_KEY')
            amazon_secret_key = os.getenv('AMAZON_SECRET_KEY')
            amazon_partner_tag = os.getenv('AMAZON_PARTNER_TAG')
            
            if not all([amazon_access_key, amazon_secret_key, amazon_partner_tag]):
                logger.warning("Amazon Associates credentials not configured")
                return []
            
            # Note: Amazon doesn't provide direct earnings API
            # This would typically require scraping reports or manual CSV import
            # For now, return mock data structure
            return [
                {
                    'source': 'amazon_associates',
                    'platform': 'Amazon',
                    'amount': 0.0,  # Would be populated from actual API/reports
                    'transaction_id': 'amazon_placeholder',
                    'description': 'Amazon Associates earnings (manual import required)',
                    'transaction_date': start_date,
                    'metadata': {'note': 'Requires manual report import'}
                }
            ]
            
        except Exception as e:
            logger.error(f"Amazon Associates data retrieval failed: {e}")
            return []
    
    async def _get_commission_junction_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get Commission Junction affiliate data"""
        try:
            cj_api_key = os.getenv('CJ_API_KEY')
            cj_website_id = os.getenv('CJ_WEBSITE_ID')
            
            if not all([cj_api_key, cj_website_id]):
                logger.warning("Commission Junction credentials not configured")
                return []
            
            # CJ Affiliate API endpoint
            url = 'https://commission-detail.api.cj.com/v3/commissions'
            headers = {
                'Authorization': f'Bearer {cj_api_key}',
                'Accept': 'application/json'
            }
            
            params = {
                'date-type': 'event',
                'start-date': start_date.strftime('%Y-%m-%d'),
                'end-date': end_date.strftime('%Y-%m-%d'),
                'website-id': cj_website_id
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    commissions = data.get('commissions', [])
                    
                    return [
                        {
                            'source': 'commission_junction',
                            'platform': 'CJ Affiliate',
                            'amount': float(commission.get('commission-amount', 0)),
                            'transaction_id': commission.get('commission-id'),
                            'description': f"CJ Commission - {commission.get('advertiser-name', 'Unknown')}",
                            'transaction_date': datetime.fromisoformat(commission.get('event-date')),
                            'metadata': {
                                'advertiser': commission.get('advertiser-name'),
                                'order_id': commission.get('order-id'),
                                'commission_status': commission.get('commission-status')
                            }
                        }
                        for commission in commissions
                    ]
                else:
                    logger.error(f"CJ API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Commission Junction data retrieval failed: {e}")
            return []
    
    async def _get_shareasale_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get ShareASale affiliate data"""
        try:
            shareasale_api_token = os.getenv('SHAREASALE_API_TOKEN')
            shareasale_api_secret = os.getenv('SHAREASALE_API_SECRET')
            shareasale_affiliate_id = os.getenv('SHAREASALE_AFFILIATE_ID')
            
            if not all([shareasale_api_token, shareasale_api_secret, shareasale_affiliate_id]):
                logger.warning("ShareASale credentials not configured")
                return []
            
            # ShareASale API endpoint
            url = 'https://www.shareasale.com/w.cfm'
            
            # Generate API signature (simplified - actual implementation needs proper HMAC)
            import hashlib
            import hmac
            timestamp = str(int(datetime.now().timestamp()))
            
            params = {
                'affiliateId': shareasale_affiliate_id,
                'token': shareasale_api_token,
                'version': '2.3',
                'action': 'activity',
                'dateStart': start_date.strftime('%m/%d/%Y'),
                'dateEnd': end_date.strftime('%m/%d/%Y')
            }
            
            # Note: ShareASale requires specific signature generation
            # This is a simplified implementation
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    # ShareASale returns pipe-delimited data
                    text_data = await response.text()
                    lines = text_data.strip().split('\n')
                    
                    transactions = []
                    for line in lines[1:]:  # Skip header
                        fields = line.split('|')
                        if len(fields) >= 10:
                            transactions.append({
                                'source': 'shareasale',
                                'platform': 'ShareASale',
                                'amount': float(fields[9]) if fields[9] else 0.0,  # Commission amount
                                'transaction_id': fields[0],  # Transaction ID
                                'description': f"ShareASale Commission - {fields[2]}",  # Merchant name
                                'transaction_date': datetime.strptime(fields[1], '%m/%d/%Y'),
                                'metadata': {
                                    'merchant': fields[2],
                                    'order_number': fields[3],
                                    'commission_status': fields[8]
                                }
                            })
                    
                    return transactions
                else:
                    logger.error(f"ShareASale API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"ShareASale data retrieval failed: {e}")
            return []
    
    async def _get_impact_radius_data(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get Impact Radius affiliate data"""
        try:
            impact_api_key = os.getenv('IMPACT_API_KEY')
            impact_account_sid = os.getenv('IMPACT_ACCOUNT_SID')
            
            if not all([impact_api_key, impact_account_sid]):
                logger.warning("Impact Radius credentials not configured")
                return []
            
            # Impact Radius API endpoint
            url = f'https://api.impact.com/Mediapartners/{impact_account_sid}/Actions'
            headers = {
                'Authorization': f'Basic {impact_api_key}',
                'Accept': 'application/json'
            }
            
            params = {
                'StartDate': start_date.strftime('%Y-%m-%d'),
                'EndDate': end_date.strftime('%Y-%m-%d'),
                'ActionDateStart': start_date.strftime('%Y-%m-%d'),
                'ActionDateEnd': end_date.strftime('%Y-%m-%d')
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    actions = data.get('Actions', [])
                    
                    return [
                        {
                            'source': 'impact_radius',
                            'platform': 'Impact Radius',
                            'amount': float(action.get('Payout', 0)),
                            'transaction_id': action.get('Id'),
                            'description': f"Impact Commission - {action.get('CampaignName', 'Unknown')}",
                            'transaction_date': datetime.fromisoformat(action.get('EventDate')),
                            'metadata': {
                                'campaign': action.get('CampaignName'),
                                'action_tracker': action.get('ActionTrackerName'),
                                'state': action.get('State')
                            }
                        }
                        for action in actions
                        if action.get('State') == 'APPROVED'
                    ]
                else:
                    logger.error(f"Impact Radius API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Impact Radius data retrieval failed: {e}")
            return []


class RevenueForecaster:
    """Advanced revenue forecasting using multiple models"""


    def __init__(self, config: RevenueConfig):
        self.config = config


    async def generate_forecast(
        self, historical_data: pd.DataFrame, days_ahead: int = 30, model: str = "linear"
    ) -> Dict[str, Any]:
        """Generate revenue forecast using specified model"""
        try:
            if len(historical_data) < 7:
                logger.warning("Insufficient historical data for forecasting")
                return self._generate_simple_forecast(historical_data, days_ahead)

            if model == "linear":
                return await self._linear_forecast(historical_data, days_ahead)
            elif model == "prophet" and PROPHET_AVAILABLE:
                return await self._prophet_forecast(historical_data, days_ahead)
            elif model == "random_forest":
                return await self._random_forest_forecast(historical_data, days_ahead)
            else:
                return await self._linear_forecast(historical_data, days_ahead)

        except Exception as e:
            logger.error(f"Forecasting failed: {e}")
            return self._generate_simple_forecast(historical_data, days_ahead)


    async def _linear_forecast(
        self, data: pd.DataFrame, days_ahead: int
    ) -> Dict[str, Any]:
        """Linear regression forecast"""
        # Prepare data
        data = data.sort_values("date")
        data["days_since_start"] = (data["date"] - data["date"].min()).dt.days

        X = data[["days_since_start"]].values
        y = data["amount"].values

        # Train model
        model = LinearRegression()
        model.fit(X, y)

        # Generate predictions
        last_day = data["days_since_start"].max()
        future_days = np.arange(last_day + 1, last_day + days_ahead + 1).reshape(-1, 1)
        predictions = model.predict(future_days)

        # Calculate confidence intervals (simple approach)
        residuals = y - model.predict(X)
        mse = np.mean(residuals**2)
        std_error = np.sqrt(mse)

        forecast_dates = [
            data["date"].max() + timedelta(days = i) for i in range(1, days_ahead + 1)
        ]

        forecast_data = []
        for i, (date, pred) in enumerate(zip(forecast_dates, predictions)):
            forecast_data.append(
                {
                    "date": date,
                        "predicted_amount": max(0, pred),
                        "confidence_lower": max(0, pred - 1.96 * std_error),
                        "confidence_upper": pred + 1.96 * std_error,
                        }
            )

        # Calculate model metrics
        train_predictions = model.predict(X)
        mae = mean_absolute_error(y, train_predictions)
        rmse = np.sqrt(mean_squared_error(y, train_predictions))

        return {
            "model": "linear_regression",
                "forecast": forecast_data,
                "metrics": {"mae": mae, "rmse": rmse, "r2_score": model.score(X, y)},
                "total_predicted": sum(f["predicted_amount"] for f in forecast_data),
                }


    async def _prophet_forecast(
        self, data: pd.DataFrame, days_ahead: int
    ) -> Dict[str, Any]:
        """Prophet forecast (if available)"""
        # Prepare data for Prophet
        prophet_data = data[["date", "amount"]].copy()
        prophet_data.columns = ["ds", "y"]

        # Train Prophet model
        model = Prophet(
            daily_seasonality = True,
                weekly_seasonality = True,
                yearly_seasonality = False if len(data) < 365 else True,
                )
        model.fit(prophet_data)

        # Generate future dates
        future = model.make_future_dataframe(periods = days_ahead)
        forecast = model.predict(future)

        # Extract forecast data
        future_forecast = forecast.tail(days_ahead)
        forecast_data = []

        for _, row in future_forecast.iterrows():
            forecast_data.append(
                {
                    "date": row["ds"],
                        "predicted_amount": max(0, row["yhat"]),
                        "confidence_lower": max(0, row["yhat_lower"]),
                        "confidence_upper": row["yhat_upper"],
                        }
            )

        return {
            "model": "prophet",
                "forecast": forecast_data,
                "metrics": {
                "mae": "N/A",  # Prophet doesn't provide simple MAE
                "rmse": "N/A",
                    "trend": (
                    "increasing"
                    if forecast["trend"].iloc[-1] > forecast["trend"].iloc[0]
                    else "decreasing"
                ),
                    },
                "total_predicted": sum(f["predicted_amount"] for f in forecast_data),
                }


    async def _random_forest_forecast(
        self, data: pd.DataFrame, days_ahead: int
    ) -> Dict[str, Any]:
        """Random Forest forecast"""
        # Feature engineering
        data = data.sort_values("date")
        data["day_of_week"] = data["date"].dt.dayofweek
        data["day_of_month"] = data["date"].dt.day
        data["month"] = data["date"].dt.month
        data["days_since_start"] = (data["date"] - data["date"].min()).dt.days

        # Create lagged features
        for lag in [1, 7, 14]:
            data[f"amount_lag_{lag}"] = data["amount"].shift(lag)

        # Remove rows with NaN values
        data = data.dropna()

        if len(data) < 20:
            return await self._linear_forecast(data[["date", "amount"]], days_ahead)

        # Prepare features
        feature_cols = ["day_of_week", "day_of_month", "month", "days_since_start"] + [
            f"amount_lag_{lag}" for lag in [1, 7, 14]
        ]

        X = data[feature_cols].values
        y = data["amount"].values

        # Train model
        model = RandomForestRegressor(n_estimators = 100, random_state = 42)
        model.fit(X, y)

        # Generate predictions (simplified approach)
        last_row = data.iloc[-1]
        predictions = []

        for i in range(days_ahead):
            future_date = data["date"].max() + timedelta(days = i + 1)

            # Create features for prediction
            features = [
                future_date.weekday(),
                    future_date.day,
                    future_date.month,
                    last_row["days_since_start"] + i + 1,
                    last_row["amount"] if i == 0 else predictions[-1],  # lag_1
                (
                    data["amount"].iloc[-7] if len(data) >= 7 else last_row["amount"]
                ),  # lag_7
                (
                    data["amount"].iloc[-14] if len(data) >= 14 else last_row["amount"]
                ),  # lag_14
            ]

            pred = model.predict([features])[0]
            predictions.append(max(0, pred))

        # Calculate confidence intervals (using prediction std)
        train_predictions = model.predict(X)
        residuals = y - train_predictions
        std_error = np.std(residuals)

        forecast_dates = [
            data["date"].max() + timedelta(days = i) for i in range(1, days_ahead + 1)
        ]

        forecast_data = []
        for date, pred in zip(forecast_dates, predictions):
            forecast_data.append(
                {
                    "date": date,
                        "predicted_amount": pred,
                        "confidence_lower": max(0, pred - 1.96 * std_error),
                        "confidence_upper": pred + 1.96 * std_error,
                        }
            )

        # Calculate metrics
        mae = mean_absolute_error(y, train_predictions)
        rmse = np.sqrt(mean_squared_error(y, train_predictions))

        return {
            "model": "random_forest",
                "forecast": forecast_data,
                "metrics": {
                "mae": mae,
                    "rmse": rmse,
                    "feature_importance": dict(
                    zip(feature_cols, model.feature_importances_)
                ),
                    },
                "total_predicted": sum(predictions),
                }


    def _generate_simple_forecast(
        self, data: pd.DataFrame, days_ahead: int
    ) -> Dict[str, Any]:
        """Simple average - based forecast for insufficient data"""
        if len(data) == 0:
            avg_amount = 0
        else:
            avg_amount = data["amount"].mean()

        forecast_dates = [
            datetime.now() + timedelta(days = i) for i in range(1, days_ahead + 1)
        ]

        forecast_data = []
        for date in forecast_dates:
            forecast_data.append(
                {
                    "date": date,
                        "predicted_amount": avg_amount,
                        "confidence_lower": avg_amount * 0.8,
                        "confidence_upper": avg_amount * 1.2,
                        }
            )

        return {
            "model": "simple_average",
                "forecast": forecast_data,
                "metrics": {"note": "Insufficient data for advanced forecasting"},
                "total_predicted": avg_amount * days_ahead,
                }


class RevenueTracker:
    """Main revenue tracking system"""


    def __init__(self, config: RevenueConfig):
        self.config = config
        self.app = FastAPI(title="TRAE.AI Revenue Tracker", version="1.0.0")

        # Initialize database
        self.engine = create_engine(config.database_url)
        Base.metadata.create_all(self.engine)
        SessionLocal = sessionmaker(autocommit = False,
    autoflush = False,
    bind = self.engine)
        self.db_session = SessionLocal()

        # Initialize components
        self.youtube_analytics = YouTubeAnalytics(config)
        self.gumroad_analytics = GumroadAnalytics(config)
        self.affiliate_tracker = AffiliateTracker(config)
        self.forecaster = RevenueForecaster(config)
        self.ai_revenue_integration = ai_revenue_integration

        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()

        self.setup_logging()
        self.setup_routes()
        self.setup_scheduler()


    def setup_logging(self):
        """Configure logging"""
        logger.remove()
        logger.add(
            sys.stdout,
                level = self.config.log_level,
                format="<green>{time:YYYY - MM - DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                )
        logger.add(
            "/app/logs/revenue_tracker.log",
                rotation="1 day",
                retention="30 days",
                level = self.config.log_level,
                )


    def setup_scheduler(self):
        """Setup automated data collection"""
        # Collect revenue data every hour
        self.scheduler.add_job(
            self.collect_all_revenue_data,
                CronTrigger(minute = 0),  # Every hour
            id="collect_revenue_data",
                )

        # Generate daily reports
        self.scheduler.add_job(
            self.generate_daily_report,
                CronTrigger(hour = 9, minute = 0),  # 9 AM daily
            id="daily_report",
                )

        # Check revenue goals and alerts
        self.scheduler.add_job(
            self.check_goals_and_alerts,
                CronTrigger(minute="*/30"),  # Every 30 minutes
            id="check_alerts",
                )


    def setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/health")


        async def health_check():
            return {
                "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "youtube_configured": bool(self.config.youtube_api_key),
                    "gumroad_configured": bool(self.config.gumroad_access_token),
                    "database_connected": True,
                    }

        @self.app.post("/revenue/record")


        async def record_revenue(request: RevenueStreamRequest):
            """Record a revenue transaction"""
            try:
                logger.info(
                    f"💰 Recording revenue: ${request.amount} from {request.source}"
                )

                revenue_stream = RevenueStream(
                    source = request.source,
                        platform = request.platform,
                        amount = Decimal(str(request.amount)),
                        currency = request.currency,
                        transaction_id = request.transaction_id,
                        description = request.description,
                        metadata = json.dumps(request.metadata) if request.metadata else None,
                        transaction_date = request.transaction_date,
                        )

                self.db_session.add(revenue_stream)
                self.db_session.commit()

                # Check if this triggers any alerts
                await self.check_revenue_alerts(revenue_stream)

                return {
                    "success": True,
                        "revenue_id": revenue_stream.id,
                        "amount": float(revenue_stream.amount),
                        "source": revenue_stream.source,
                        }

            except Exception as e:
                logger.error(f"Revenue recording failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.get("/revenue/analytics")


        async def get_analytics(
            start_date: datetime = Query(...),
                end_date: datetime = Query(...),
                sources: Optional[str] = Query(None),
                group_by: str = Query("day"),
                ):
            """Get revenue analytics"""
            try:
                logger.info(f"📊 Generating analytics from {start_date} to {end_date}")

                # Build query
                query = self.db_session.query(RevenueStream).filter(
                    RevenueStream.transaction_date >= start_date,
                        RevenueStream.transaction_date <= end_date,
                        )

                if sources:
                    source_list = sources.split(",")
                    query = query.filter(RevenueStream.source.in_(source_list))

                revenue_data = query.all()

                # Convert to DataFrame for analysis
                df = pd.DataFrame(
                    [
                        {
                            "date": r.transaction_date,
                                "amount": float(r.amount),
                                "source": r.source,
                                "platform": r.platform,
                                }
                        for r in revenue_data
                    ]
                )

                if df.empty:
                    return {
                        "total_revenue": 0,
                            "transaction_count": 0,
                            "average_transaction": 0,
                            "daily_breakdown": [],
                            "source_breakdown": {},
                            }

                # Group by specified period
                if group_by == "day":
                    df["period"] = df["date"].dt.date
                elif group_by == "week":
                    df["period"] = df["date"].dt.to_period("W")
                elif group_by == "month":
                    df["period"] = df["date"].dt.to_period("M")

                # Calculate analytics
                total_revenue = df["amount"].sum()
                transaction_count = len(df)
                average_transaction = df["amount"].mean()

                # Daily breakdown
                daily_breakdown = df.groupby("period")["amount"].sum().reset_index()
                daily_breakdown["period"] = daily_breakdown["period"].astype(str)

                # Source breakdown
                source_breakdown = df.groupby("source")["amount"].sum().to_dict()

                return {
                    "total_revenue": round(total_revenue, 2),
                        "transaction_count": transaction_count,
                        "average_transaction": round(average_transaction, 2),
                        "daily_breakdown": daily_breakdown.to_dict("records"),
                        "source_breakdown": {
                        k: round(v, 2) for k, v in source_breakdown.items()
                    },
                        }

            except Exception as e:
                logger.error(f"Analytics generation failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.post("/revenue/forecast")


        async def generate_forecast(request: ForecastRequest):
            """Generate revenue forecast"""
            try:
                logger.info(
                    f"🔮 Generating {request.days_ahead}-day forecast using {request.model}"
                )

                # Get historical data
                end_date = datetime.now()
                start_date = end_date - timedelta(days = 90)  # Use last 90 days

                query = self.db_session.query(RevenueStream).filter(
                    RevenueStream.transaction_date >= start_date,
                        RevenueStream.transaction_date <= end_date,
                        )

                if request.sources:
                    query = query.filter(RevenueStream.source.in_(request.sources))

                revenue_data = query.all()

                # Convert to DataFrame
                df = pd.DataFrame(
                    [
                        {"date": r.transaction_date.date(), "amount": float(r.amount)}
                        for r in revenue_data
                    ]
                )

                if df.empty:
                    return {
                        "success": False,
                            "message": "No historical data available for forecasting",
                            }

                # Group by day and sum amounts
                daily_df = df.groupby("date")["amount"].sum().reset_index()
                daily_df["date"] = pd.to_datetime(daily_df["date"])

                # Generate forecast
                forecast_result = await self.forecaster.generate_forecast(
                    daily_df, request.days_ahead, request.model
                )

                # Save forecast to database
                for forecast_point in forecast_result["forecast"]:
                    forecast_record = RevenueForecast(
                        forecast_date = forecast_point["date"],
                            predicted_amount = Decimal(
                            str(forecast_point["predicted_amount"])
                        ),
                            confidence_lower = Decimal(
                            str(forecast_point.get("confidence_lower", 0))
                        ),
                            confidence_upper = Decimal(
                            str(forecast_point.get("confidence_upper", 0))
                        ),
                            model_used = forecast_result["model"],
                            source_filter=(
                            ",".join(request.sources) if request.sources else None
                        ),
                            )
                    self.db_session.add(forecast_record)

                self.db_session.commit()

                return {
                    "success": True,
                        "model": forecast_result["model"],
                        "forecast": forecast_result["forecast"],
                        "metrics": forecast_result["metrics"],
                        "total_predicted": round(forecast_result["total_predicted"], 2),
                        }

            except Exception as e:
                logger.error(f"Forecast generation failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.post("/goals/create")


        async def create_revenue_goal(request: RevenueGoalRequest):
            """Create a revenue goal"""
            try:
                logger.info(
                    f"🎯 Creating revenue goal: {request.name} - ${request.target_amount}"
                )

                goal = RevenueGoal(
                    name = request.name,
                        target_amount = Decimal(str(request.target_amount)),
                        target_date = request.target_date,
                        source_filter = request.source_filter,
                        )

                self.db_session.add(goal)
                self.db_session.commit()

                return {
                    "success": True,
                        "goal_id": goal.id,
                        "name": goal.name,
                        "target_amount": float(goal.target_amount),
                        "target_date": goal.target_date.isoformat(),
                        }

            except Exception as e:
                logger.error(f"Goal creation failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.get("/goals/progress")


        async def get_goal_progress():
            """Get progress on all revenue goals"""
            try:
                goals = (
                    self.db_session.query(RevenueGoal)
                    .filter(RevenueGoal.status == "active")
                    .all()
                )

                goal_progress = []

                for goal in goals:
                    # Calculate current progress
                    query = self.db_session.query(RevenueStream).filter(
                        RevenueStream.transaction_date >= goal.created_at,
                            RevenueStream.transaction_date <= datetime.now(),
                            )

                    if goal.source_filter:
                        sources = goal.source_filter.split(",")
                        query = query.filter(RevenueStream.source.in_(sources))

                    current_amount = sum(float(r.amount) for r in query.all())
                    progress_percentage = (
                        current_amount/float(goal.target_amount)
                    ) * 100

                    # Update goal in database
                    goal.current_amount = Decimal(str(current_amount))

                    goal_progress.append(
                        {
                            "goal_id": goal.id,
                                "name": goal.name,
                                "target_amount": float(goal.target_amount),
                                "current_amount": current_amount,
                                "progress_percentage": round(progress_percentage, 2),
                                "target_date": goal.target_date.isoformat(),
                                "days_remaining": (goal.target_date - datetime.now()).days,
                                "status": (
                                "completed" if progress_percentage >= 100 else "active"
                            ),
                                }
                    )

                self.db_session.commit()

                return {
                    "goals": goal_progress,
                        "total_goals": len(goals),
                        "completed_goals": len(
                        [g for g in goal_progress if g["status"] == "completed"]
                    ),
                        }

            except Exception as e:
                logger.error(f"Goal progress calculation failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.get("/alerts")


        async def get_alerts():
            """Get recent revenue alerts"""
            try:
                alerts = (
                    self.db_session.query(RevenueAlert)
                    .filter(RevenueAlert.acknowledged is False)
                    .order_by(RevenueAlert.triggered_at.desc())
                    .limit(50)
                    .all()
                )

                return {
                    "alerts": [
                        {
                            "id": alert.id,
                                "type": alert.alert_type,
                                "message": alert.message,
                                "severity": alert.severity,
                                "triggered_at": alert.triggered_at.isoformat(),
                                }
                        for alert in alerts
                    ],
                        "total_unacknowledged": len(alerts),
                        }

            except Exception as e:
                logger.error(f"Alert retrieval failed: {e}")
                raise HTTPException(status_code = 500, detail = str(e))

        @self.app.post("/data/collect")


        async def collect_revenue_data(background_tasks: BackgroundTasks):
            """Manually trigger revenue data collection"""
            background_tasks.add_task(self.collect_all_revenue_data)
            return {"message": "Revenue data collection started"}


    async def collect_all_revenue_data(self):
        """Collect revenue data from all sources"""
        try:
            logger.info("🔄 Collecting revenue data from all sources")

            end_date = datetime.now()
            start_date = end_date - timedelta(days = 7)  # Last 7 days

            # Collect YouTube data
            youtube_data = await self.youtube_analytics.get_revenue_data(
                start_date, end_date
            )
            for data_point in youtube_data:
                if data_point["revenue"] > 0:
                    revenue_stream = RevenueStream(
                        source="youtube",
                            platform="youtube",
                            amount = Decimal(str(data_point["revenue"])),
                            currency="USD",
                            description = f"YouTube ad revenue - {data_point['monetized_playbacks']} monetized playbacks",
                            transaction_date = data_point["date"],
                            metadata = json.dumps(
                            {
                                "monetized_playbacks": data_point[
                                    "monetized_playbacks"
                                ],
                                    "cpm": data_point["cpm"],
                                    }
                        ),
                            )

                    # Check if already exists
                    existing = (
                        self.db_session.query(RevenueStream)
                        .filter(
                            RevenueStream.source == "youtube",
                                RevenueStream.transaction_date == data_point["date"],
                                )
                        .first()
                    )

                    if not existing:
                        self.db_session.add(revenue_stream)

            # Collect Gumroad data
            gumroad_data = await self.gumroad_analytics.get_sales_data(
                start_date, end_date
            )
            for sale in gumroad_data:
                revenue_stream = RevenueStream(
                    source="gumroad",
                        platform="gumroad",
                        amount = Decimal(str(sale["amount"])),
                        currency = sale["currency"],
                        transaction_id = sale["transaction_id"],
                        description = f"Product sale: {sale['product_name']}",
                        transaction_date = sale["date"],
                        )

                # Check if already exists
                existing = (
                    self.db_session.query(RevenueStream)
                    .filter(RevenueStream.transaction_id == sale["transaction_id"])
                    .first()
                )

                if not existing:
                    self.db_session.add(revenue_stream)

            # Collect affiliate data
            try:
                affiliate_data = await self.affiliate_tracker.get_affiliate_data(
                    start_date, end_date
                )
                for commission in affiliate_data:
                    revenue_stream = RevenueStream(
                        source="affiliate",
                        platform=commission["network"],
                        amount=Decimal(str(commission["amount"])),
                        currency="USD",
                        transaction_id=commission["transaction_id"],
                        description=f"Affiliate commission - {commission['network']}",
                        transaction_date=commission["date"],
                    )

                    # Check if already exists
                    existing = (
                        self.db_session.query(RevenueStream)
                        .filter(
                            RevenueStream.transaction_id == commission["transaction_id"]
                        )
                        .first()
                    )

                    if not existing:
                        self.db_session.add(revenue_stream)
            except Exception as e:
                logger.info(f"Affiliate data collection failed: {e}")

            # Collect AI platform revenue data
            if self.ai_revenue_integration:
                try:
                    ai_revenue_data = await self.ai_revenue_integration.get_ai_platform_revenue(
                        start_date, end_date
                    )
                    for ai_revenue in ai_revenue_data:
                        revenue_stream = RevenueStream(
                            source="ai_platform",
                                platform = ai_revenue["platform"],
                                amount = Decimal(str(ai_revenue["amount"])),
                                currency = ai_revenue.get("currency", "USD"),
                                transaction_id = ai_revenue.get("transaction_id"),
                                description = f"AI platform revenue - {ai_revenue['platform']}: {ai_revenue.get('description', '')}",
                                transaction_date = ai_revenue["date"],
                                metadata = json.dumps(ai_revenue.get("metadata", {})),
                                )

                        # Check if already exists
                        existing = None
                        if ai_revenue.get("transaction_id"):
                            existing = (
                                self.db_session.query(RevenueStream)
                                .filter(
                                    RevenueStream.transaction_id == ai_revenue["transaction_id"]
                                )
                                .first()
                            )
                        else:
                            # For records without transaction_id, check by platform \
    and date
                            existing = (
                                self.db_session.query(RevenueStream)
                                .filter(
                                    RevenueStream.source == "ai_platform",
                                        RevenueStream.platform == ai_revenue["platform"],
                                        RevenueStream.transaction_date == ai_revenue["date"],
                                        RevenueStream.amount == Decimal(str(ai_revenue["amount"]))
                                )
                                .first()
                            )

                        if not existing:
                            self.db_session.add(revenue_stream)
                except Exception as e:
                    logger.error(f"AI platform revenue collection failed: {e}")

            self.db_session.commit()
            logger.info("✅ Revenue data collection completed")

        except Exception as e:
            logger.error(f"Revenue data collection failed: {e}")


    async def check_revenue_alerts(self, revenue_stream: RevenueStream):
        """Check if revenue triggers any alerts"""
        try:
            # Check daily revenue threshold
            today = datetime.now().date()
            daily_revenue = (
                self.db_session.query(RevenueStream)
                .filter(
                    RevenueStream.transaction_date >= today,
                        RevenueStream.transaction_date < today + timedelta(days = 1),
                        )
                .all()
            )

            total_daily = sum(float(r.amount) for r in daily_revenue)

            if total_daily >= self.config.revenue_alert_threshold:
                alert = RevenueAlert(
                    alert_type="threshold",
                        message = f"Daily revenue threshold reached: ${total_daily:.2f}",
                        severity="info",
                        )
                self.db_session.add(alert)

            # Check for large single transactions
            if float(revenue_stream.amount) >= 100:  # $100+ transaction
                alert = RevenueAlert(
                    alert_type="large_transaction",
                        message = f"Large transaction: ${revenue_stream.amount} from {revenue_stream.source}",
                        severity="info",
                        metadata = json.dumps(
                        {
                            "revenue_id": revenue_stream.id,
                                "source": revenue_stream.source,
                                "amount": float(revenue_stream.amount),
                                }
                    ),
                        )
                self.db_session.add(alert)

            self.db_session.commit()

        except Exception as e:
            logger.error(f"Alert checking failed: {e}")


    async def check_goals_and_alerts(self):
        """Check revenue goals and generate alerts"""
        try:
            # Check goal progress
            goals = (
                self.db_session.query(RevenueGoal)
                .filter(RevenueGoal.status == "active")
                .all()
            )

            for goal in goals:
                # Calculate current progress
                query = self.db_session.query(RevenueStream).filter(
                    RevenueStream.transaction_date >= goal.created_at,
                        RevenueStream.transaction_date <= datetime.now(),
                        )

                if goal.source_filter:
                    sources = goal.source_filter.split(",")
                    query = query.filter(RevenueStream.source.in_(sources))

                current_amount = sum(float(r.amount) for r in query.all())
                progress_percentage = (current_amount/float(goal.target_amount)) * 100

                # Update goal
                goal.current_amount = Decimal(str(current_amount))

                # Check for goal completion
                if progress_percentage >= 100 and goal.status == "active":
                    goal.status = "completed"
                    alert = RevenueAlert(
                        alert_type="goal",
                            message = f"Revenue goal '{goal.name}' completed! Target: ${goal.target_amount}, Achieved: ${current_amount:.2f}",
                            severity="info",
                            )
                    self.db_session.add(alert)

                # Check for goal deadline approaching
                days_remaining = (goal.target_date - datetime.now()).days
                if days_remaining <= 7 and progress_percentage < 80:
                    alert = RevenueAlert(
                        alert_type="goal",
                            message = f"Revenue goal '{goal.name}' deadline approaching. {days_remaining} days left, {progress_percentage:.1f}% complete",
                            severity="warning",
                            )
                    self.db_session.add(alert)

            self.db_session.commit()

        except Exception as e:
            logger.error(f"Goal and alert checking failed: {e}")


    async def generate_daily_report(self):
        """Generate daily revenue report"""
        try:
            logger.info("📊 Generating daily revenue report")

            yesterday = datetime.now().date() - timedelta(days = 1)

            # Get yesterday's revenue
            daily_revenue = (
                self.db_session.query(RevenueStream)
                .filter(
                    RevenueStream.transaction_date >= yesterday,
                        RevenueStream.transaction_date < yesterday + timedelta(days = 1),
                        )
                .all()
            )

            if not daily_revenue:
                logger.info("No revenue data for yesterday")
                return

            # Calculate metrics
            total_revenue = sum(float(r.amount) for r in daily_revenue)
            transaction_count = len(daily_revenue)

            # Group by source
            source_breakdown = {}
            for revenue in daily_revenue:
                source = revenue.source
                if source not in source_breakdown:
                    source_breakdown[source] = 0
                source_breakdown[source] += float(revenue.amount)

            # Create report
            report = {
                "date": yesterday.isoformat(),
                    "total_revenue": round(total_revenue, 2),
                    "transaction_count": transaction_count,
                    "average_transaction": round(
                    total_revenue/transaction_count if transaction_count > 0 else 0, 2
                ),
                    "source_breakdown": {
                    k: round(v, 2) for k, v in source_breakdown.items()
                },
                    }

            # Save report
            report_path = (
                self.config.reports_dir/f"daily_report_{yesterday.isoformat()}.json"
            )
            with open(report_path, "w") as f:
                json.dump(report, f, indent = 2)

            logger.info(
                f"✅ Daily report generated: ${total_revenue:.2f} from {transaction_count} transactions"
            )

        except Exception as e:
            logger.error(f"Daily report generation failed: {e}")


    async def start_server(self):
        """Start the revenue tracker server"""

        import uvicorn

        logger.info("💰 Starting TRAE.AI Revenue Tracker")
        logger.info(f"📊 Mock mode: {self.config.use_mock}")
        logger.info(f"📺 YouTube configured: {bool(self.config.youtube_api_key)}")
        logger.info(f"🛒 Gumroad configured: {bool(self.config.gumroad_access_token)}")

        # Start scheduler
        self.scheduler.start()
        logger.info("⏰ Scheduler started")

        config = uvicorn.Config(
            app = self.app,
                host="0.0.0.0",
                port = 8004,
                log_level = self.config.log_level.lower(),
                )
        server = uvicorn.Server(config)
        await server.serve()


async def main():
    """Main entry point"""
    config = RevenueConfig()
    tracker = RevenueTracker(config)
    await tracker.start_server()

if __name__ == "__main__":
    asyncio.run(main())
