#!/usr / bin / env python3
"""
Marketing Agent Tools Module

Implements comprehensive marketing capabilities including:
- Day One Blitz marketing strategy
- Relentless Optimization Loop for continuous improvement
- Intelligent context - aware affiliate link selection
- Cross - promotion manager with "The Right Perspective" exception handling
"""

import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from urllib.parse import urljoin, urlparse

try:
    import numpy as np
    import pandas as pd
    import requests
    from bs4 import BeautifulSoup
    from textblob import TextBlob

except ImportError as e:
    logging.warning(f"Optional dependency missing: {e}. Some features may be limited.")
    requests = None
    BeautifulSoup = None
    pd = None
    np = None
    TextBlob = None


class MarketingChannel(Enum):
    """Available marketing channels"""

    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    EMAIL = "email"
    BLOG = "blog"
    PODCAST = "podcast"
    REDDIT = "reddit"
    PINTEREST = "pinterest"


class CampaignType(Enum):
    """Types of marketing campaigns"""

    PRODUCT_LAUNCH = "product_launch"
    BRAND_AWARENESS = "brand_awareness"
    LEAD_GENERATION = "lead_generation"
    AFFILIATE_PROMOTION = "affiliate_promotion"
    CONTENT_PROMOTION = "content_promotion"
    RETARGETING = "retargeting"
    SEASONAL = "seasonal"


class OptimizationMetric(Enum):
    """Metrics for optimization tracking"""

    CLICK_THROUGH_RATE = "ctr"
    CONVERSION_RATE = "conversion_rate"
    COST_PER_ACQUISITION = "cpa"
    RETURN_ON_AD_SPEND = "roas"
    ENGAGEMENT_RATE = "engagement_rate"
    REACH = "reach"
    IMPRESSIONS = "impressions"
    REVENUE = "revenue"


class AffiliateNetwork(Enum):
    """Supported affiliate networks"""

    AMAZON_ASSOCIATES = "amazon_associates"
    CLICKBANK = "clickbank"
    COMMISSION_JUNCTION = "commission_junction"
    SHAREASALE = "shareasale"
    IMPACT = "impact"
    RAKUTEN = "rakuten"
    PARTNERSTACK = "partnerstack"
    CUSTOM = "custom"


@dataclass
class MarketingCampaign:
    """Represents a marketing campaign"""

    campaign_id: str
    name: str
    campaign_type: CampaignType
    channels: List[MarketingChannel]
    target_audience: str
    budget: float
    start_date: datetime
    end_date: datetime
    objectives: List[str] = field(default_factory=list)
    content_assets: List[str] = field(default_factory=list)
    metrics: Dict[OptimizationMetric, float] = field(default_factory=dict)
    status: str = "draft"
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class AffiliateLink:
    """Represents an affiliate link with context"""

    product_name: str
    affiliate_url: str
    network: AffiliateNetwork
    commission_rate: float
    product_category: str
    target_keywords: List[str] = field(default_factory=list)
    context_relevance: float = 0.0
    conversion_rate: float = 0.0
    earnings_per_click: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class OptimizationTest:
    """Represents an A / B test or optimization experiment"""

    test_id: str
    name: str
    hypothesis: str
    variants: List[Dict[str, Any]]
    metric: OptimizationMetric
    start_date: datetime
    end_date: Optional[datetime] = None
    sample_size: int = 0
    confidence_level: float = 0.95
    results: Dict[str, Any] = field(default_factory=dict)
    status: str = "running"
    winner: Optional[str] = None


@dataclass
class CrossPromotionRule:
    """Rules for cross - promotion between content"""

    source_content: str
    target_content: str
    relevance_score: float
    promotion_type: str  # "mention", "link", "embed", "recommendation"
    context: str
    exceptions: List[str] = field(default_factory=list)
    is_active: bool = True


class DayOneBlitzStrategy:
    """Implements the Day One Blitz marketing strategy"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.active_campaigns: Dict[str, MarketingCampaign] = {}

    async def launch_blitz_campaign(
        self,
        product_name: str,
        target_audience: str,
        budget: float,
        duration_hours: int = 24,
    ) -> MarketingCampaign:
        """Launch a Day One Blitz campaign"""
        try:
            campaign_id = f"blitz_{int(time.time())}"

            # Create comprehensive campaign
            campaign = MarketingCampaign(
                campaign_id=campaign_id,
                name=f"Day One Blitz: {product_name}",
                campaign_type=CampaignType.PRODUCT_LAUNCH,
                channels=self._select_optimal_channels(target_audience),
                target_audience=target_audience,
                budget=budget,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(hours=duration_hours),
                objectives=[
                    "Maximize initial visibility",
                    "Generate early momentum",
                    "Capture early adopters",
                    "Create social proof",
                ],
            )

            # Generate content assets for each channel
            campaign.content_assets = await self._generate_blitz_content(campaign)

            # Execute simultaneous launch across all channels
            await self._execute_simultaneous_launch(campaign)

            # Set up real - time monitoring
            await self._setup_realtime_monitoring(campaign)

            campaign.status = "active"
            self.active_campaigns[campaign_id] = campaign

            self.logger.info(f"Day One Blitz launched for {product_name}")
            return campaign

        except Exception as e:
            self.logger.error(f"Error launching blitz campaign: {e}")
            raise

    def _select_optimal_channels(self, target_audience: str) -> List[MarketingChannel]:
        """Select optimal marketing channels based on target audience"""
        audience_lower = target_audience.lower()

        # Channel selection based on audience
        channels = [
            MarketingChannel.EMAIL,
            MarketingChannel.BLOG,
        ]  # Always include these

        if any(term in audience_lower for term in ["business", "professional", "b2b"]):
            channels.extend([MarketingChannel.LINKEDIN, MarketingChannel.TWITTER])

        if any(term in audience_lower for term in ["young", "gen z", "teen", "student"]):
            channels.extend([MarketingChannel.TIKTOK, MarketingChannel.INSTAGRAM])

        if any(term in audience_lower for term in ["creator", "influencer", "content"]):
            channels.extend([MarketingChannel.YOUTUBE, MarketingChannel.INSTAGRAM])

        if any(term in audience_lower for term in ["tech", "developer", "programmer"]):
            channels.extend([MarketingChannel.REDDIT, MarketingChannel.TWITTER])

        # Always include Facebook for broad reach
        if MarketingChannel.FACEBOOK not in channels:
            channels.append(MarketingChannel.FACEBOOK)

        return list(set(channels))  # Remove duplicates

    async def _generate_blitz_content(self, campaign: MarketingCampaign) -> List[str]:
        """Generate content assets for the blitz campaign"""
        content_assets = []

        for channel in campaign.channels:
            if channel == MarketingChannel.YOUTUBE:
                content_assets.extend(
                    [
                        "Product announcement video",
                        "Behind - the - scenes launch video",
                        "Quick demo / tutorial video",
                    ]
                )

            elif channel == MarketingChannel.FACEBOOK:
                content_assets.extend(
                    [
                        "Launch announcement post",
                        "Product showcase carousel",
                        "Live Q&A session",
                        "User testimonial posts",
                    ]
                )

            elif channel == MarketingChannel.INSTAGRAM:
                content_assets.extend(
                    [
                        "Product reveal stories",
                        "Launch countdown posts",
                        "Behind - the - scenes reels",
                        "User - generated content campaign",
                    ]
                )

            elif channel == MarketingChannel.TWITTER:
                content_assets.extend(
                    [
                        "Launch announcement thread",
                        "Product feature highlights",
                        "Real - time launch updates",
                        "Community engagement tweets",
                    ]
                )

            elif channel == MarketingChannel.EMAIL:
                content_assets.extend(
                    [
                        "Launch announcement email",
                        "Exclusive early access email",
                        "Product walkthrough email series",
                    ]
                )

            elif channel == MarketingChannel.BLOG:
                content_assets.extend(
                    [
                        "Comprehensive launch blog post",
                        "Product development story",
                        "Use case examples post",
                    ]
                )

        return content_assets

    async def _execute_simultaneous_launch(self, campaign: MarketingCampaign) -> None:
        """Execute simultaneous launch across all channels"""
        launch_tasks = []

        for channel in campaign.channels:
            task = asyncio.create_task(self._launch_on_channel(campaign, channel))
            launch_tasks.append(task)

        # Execute all launches simultaneously
        results = await asyncio.gather(*launch_tasks, return_exceptions=True)

        # Log results
        for i, result in enumerate(results):
            channel = campaign.channels[i]
            if isinstance(result, Exception):
                self.logger.error(f"Launch failed on {channel.value}: {result}")
            else:
                self.logger.info(f"Successfully launched on {channel.value}")

    async def _launch_on_channel(
        self, campaign: MarketingCampaign, channel: MarketingChannel
    ) -> bool:
        """Launch campaign on a specific channel"""
        try:
            # Simulate channel - specific launch logic
            await asyncio.sleep(random.uniform(0.5, 2.0))  # Simulate API calls

            # Channel - specific launch actions would go here
            # For now, we'll simulate successful launches

            self.logger.info(f"Launched {campaign.name} on {channel.value}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to launch on {channel.value}: {e}")
            return False

    async def _setup_realtime_monitoring(self, campaign: MarketingCampaign) -> None:
        """Set up real - time monitoring for the campaign"""
        # Initialize metrics tracking
        campaign.metrics = {
            OptimizationMetric.IMPRESSIONS: 0.0,
            OptimizationMetric.REACH: 0.0,
            OptimizationMetric.ENGAGEMENT_RATE: 0.0,
            OptimizationMetric.CLICK_THROUGH_RATE: 0.0,
            OptimizationMetric.CONVERSION_RATE: 0.0,
        }

        # Start monitoring task
        asyncio.create_task(self._monitor_campaign_performance(campaign))

    async def _monitor_campaign_performance(self, campaign: MarketingCampaign) -> None:
        """Monitor campaign performance in real - time"""
        while campaign.status == "active" and datetime.now() < campaign.end_date:
            try:
                # Simulate metrics collection
                await self._collect_campaign_metrics(campaign)

                # Check for optimization opportunities
                await self._check_optimization_triggers(campaign)

                # Wait before next check
                await asyncio.sleep(300)  # Check every 5 minutes

            except Exception as e:
                self.logger.error(f"Error monitoring campaign {campaign.campaign_id}: {e}")
                await asyncio.sleep(60)

    async def _collect_campaign_metrics(self, campaign: MarketingCampaign) -> None:
        """Collect current campaign metrics"""
        # Simulate metric collection from various channels
        # In production, this would integrate with actual APIs

        # Simulate growing metrics over time
        time_elapsed = (datetime.now() - campaign.start_date).total_seconds() / 3600
        growth_factor = min(time_elapsed / 24, 1.0)  # Normalize to 24 hours

        campaign.metrics[OptimizationMetric.IMPRESSIONS] += (
            random.randint(100, 1000) * growth_factor
        )
        campaign.metrics[OptimizationMetric.REACH] += random.randint(50, 500) * growth_factor
        campaign.metrics[OptimizationMetric.ENGAGEMENT_RATE] = random.uniform(0.02, 0.08)
        campaign.metrics[OptimizationMetric.CLICK_THROUGH_RATE] = random.uniform(0.01, 0.05)
        campaign.metrics[OptimizationMetric.CONVERSION_RATE] = random.uniform(0.005, 0.02)

    async def _check_optimization_triggers(self, campaign: MarketingCampaign) -> None:
        """Check if optimization actions should be triggered"""
        # Check for underperforming channels
        if campaign.metrics[OptimizationMetric.CLICK_THROUGH_RATE] < 0.02:
            self.logger.warning(f"Low CTR detected for campaign {campaign.campaign_id}")
            # Trigger optimization actions

        # Check for high - performing opportunities
        if campaign.metrics[OptimizationMetric.ENGAGEMENT_RATE] > 0.06:
            self.logger.info(f"High engagement detected for campaign {campaign.campaign_id}")
            # Scale up successful elements


class RelentlessOptimizationLoop:
    """Implements continuous optimization for marketing campaigns"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.active_tests: Dict[str, OptimizationTest] = {}
        self.optimization_history: List[Dict] = []

    async def start_optimization_loop(self, campaign: MarketingCampaign) -> None:
        """Start the relentless optimization loop for a campaign"""
        try:
            self.logger.info(f"Starting optimization loop for campaign {campaign.campaign_id}")

            # Create optimization task
            asyncio.create_task(self._run_optimization_cycle(campaign))

        except Exception as e:
            self.logger.error(f"Error starting optimization loop: {e}")

    async def _run_optimization_cycle(self, campaign: MarketingCampaign) -> None:
        """Run continuous optimization cycles"""
        cycle_count = 0

        while campaign.status == "active":
            try:
                cycle_count += 1
                self.logger.info(
                    f"Starting optimization cycle {cycle_count} for {campaign.campaign_id}"
                )

                # Analyze current performance
                performance_analysis = await self._analyze_performance(campaign)

                # Identify optimization opportunities
                opportunities = await self._identify_opportunities(campaign, performance_analysis)

                # Create and run tests
                if opportunities:
                    await self._create_optimization_tests(campaign, opportunities)

                # Check existing test results
                await self._check_test_results(campaign)

                # Apply winning variations
                await self._apply_winning_variations(campaign)

                # Wait before next cycle (every 2 hours)
                await asyncio.sleep(7200)

            except Exception as e:
                self.logger.error(f"Error in optimization cycle: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error

    async def _analyze_performance(self, campaign: MarketingCampaign) -> Dict[str, Any]:
        """Analyze current campaign performance"""
        analysis = {
            "overall_performance": "good",  # good, average, poor
            "top_performing_channels": [],
            "underperforming_channels": [],
            "key_insights": [],
            "bottlenecks": [],
        }

        # Analyze channel performance
        for channel in campaign.channels:
            # Simulate channel performance analysis
            channel_ctr = random.uniform(0.01, 0.06)
            channel_conversion = random.uniform(0.005, 0.03)

            if channel_ctr > 0.04 and channel_conversion > 0.02:
                analysis["top_performing_channels"].append(channel.value)
            elif channel_ctr < 0.02 or channel_conversion < 0.01:
                analysis["underperforming_channels"].append(channel.value)

        # Generate insights
        if analysis["top_performing_channels"]:
            analysis["key_insights"].append(
                f"Strong performance on {', '.join(analysis['top_performing_channels'])}"
            )

        if analysis["underperforming_channels"]:
            analysis["key_insights"].append(
                f"Optimization needed for {', '.join(analysis['underperforming_channels'])}"
            )

        return analysis

    async def create_ab_test_for_links(
        self,
        content_context: str,
        candidate_links: List[AffiliateLink],
        test_duration_days: int = 7,
    ) -> str:
        """Create A / B test for affiliate link selection"""
        test_id = f"affiliate_test_{datetime.now().strftime('%Y % m%d_ % H%M % S')}"

        # Select top candidates for testing
        test_links = candidate_links[: min(4, len(candidate_links))]  # Max 4 variants

        test_config = {
            "test_id": test_id,
            "content_context": content_context,
            "variants": [
                {
                    "variant_id": f"variant_{i}",
                    "link": link,
                    "traffic_split": 1.0 / len(test_links),
                }
                for i, link in enumerate(test_links)
            ],
            "start_date": datetime.now(),
            "end_date": datetime.now() + timedelta(days=test_duration_days),
            "metrics": {"clicks": {}, "conversions": {}, "revenue": {}},
            "status": "active",
        }

        # Store test configuration (in production, use proper database)
        if not hasattr(self, "ab_tests"):
            self.ab_tests = {}

        self.ab_tests[test_id] = test_config

        self.logger.info(
            f"Created A / B test {test_id} with {len(test_links)} variants "
            f"for {test_duration_days} days"
        )

        return test_id

    async def get_test_winner(self, test_id: str) -> Optional[AffiliateLink]:
        """Get the winning variant from an A / B test"""
        if not hasattr(self, "ab_tests") or test_id not in self.ab_tests:
            return None

        test = self.ab_tests[test_id]

        if test["status"] != "completed":
            return None

        # Calculate performance for each variant
        best_variant = None
        best_score = 0.0

        for variant in test["variants"]:
            variant_id = variant["variant_id"]
            clicks = test["metrics"]["clicks"].get(variant_id, 0)
            conversions = test["metrics"]["conversions"].get(variant_id, 0)
            revenue = test["metrics"]["revenue"].get(variant_id, 0.0)

            if clicks > 0:
                conversion_rate = conversions / clicks
                epc = revenue / clicks
                score = conversion_rate * 0.6 + epc * 0.4

                if score > best_score:
                    best_score = score
                    best_variant = variant

        return best_variant["link"] if best_variant else None

    async def track_competitor_links(self, competitor_content: str, competitor_id: str) -> None:
        """Track competitor affiliate link usage for intelligence"""
        if not hasattr(self, "competitor_intelligence"):
            self.competitor_intelligence = {}

        # Extract potential affiliate links from competitor content

        import re

        # Common affiliate link patterns
        affiliate_patterns = [
            r"amazon\\.com/[^\\s]*(?:tag=|associate - id=)([^&\\s]+)",
            r"clickbank\\.net/[^\\s]*",
            r"shareasale\\.com/[^\\s]*",
            r"cj\\.com/[^\\s]*",
            r"impact\\.com/[^\\s]*",
        ]

        found_links = []
        for pattern in affiliate_patterns:
            matches = re.findall(pattern, competitor_content, re.IGNORECASE)
            found_links.extend(matches)

        if competitor_id not in self.competitor_intelligence:
            self.competitor_intelligence[competitor_id] = {
                "links": [],
                "last_updated": datetime.now(),
                "content_samples": [],
            }

        competitor_data = self.competitor_intelligence[competitor_id]
        competitor_data["links"].extend(found_links)
        competitor_data["content_samples"].append(
            {
                "content": competitor_content[:500],  # First 500 chars
                "timestamp": datetime.now(),
                "links_found": len(found_links),
            }
        )

        # Keep only recent data
        competitor_data["content_samples"] = competitor_data["content_samples"][-10:]
        competitor_data["last_updated"] = datetime.now()

        self.logger.info(
            f"Updated competitor intelligence for {competitor_id}: "
            f"found {len(found_links)} affiliate links"
        )

    def get_competitor_insights(self, days: int = 30) -> Dict[str, Any]:
        """Get insights from competitor affiliate link analysis"""
        if not hasattr(self, "competitor_intelligence"):
            return {"competitors": 0, "insights": []}

        cutoff_date = datetime.now() - timedelta(days=days)
        insights = []

        for competitor_id, data in self.competitor_intelligence.items():
            if data["last_updated"] > cutoff_date:
                recent_samples = [
                    sample
                    for sample in data["content_samples"]
                    if sample["timestamp"] > cutoff_date
                ]

                if recent_samples:
                    avg_links_per_content = sum(
                        sample["links_found"] for sample in recent_samples
                    ) / len(recent_samples)

                    insights.append(
                        {
                            "competitor_id": competitor_id,
                            "content_samples": len(recent_samples),
                            "avg_links_per_content": avg_links_per_content,
                            "total_unique_links": len(set(data["links"])),
                            "last_activity": data["last_updated"].isoformat(),
                        }
                    )

        return {
            "competitors": len(insights),
            "insights": insights,
            "analysis_period_days": days,
        }

    async def predict_link_performance(
        self, link: AffiliateLink, content_context: str, target_keywords: List[str]
    ) -> Dict[str, float]:
        """Predict link performance using machine learning - like approach"""
        try:
            # Feature extraction
            features = await self._extract_prediction_features(
                link, content_context, target_keywords
            )

            # Simple prediction model (in production, use actual ML model)
            predicted_ctr = self._predict_click_through_rate(features)
            predicted_cr = self._predict_conversion_rate(features)
            predicted_epc = self._predict_earnings_per_click(features)

            # Confidence score based on historical data availability
            confidence = self._calculate_prediction_confidence(link)

            return {
                "predicted_ctr": predicted_ctr,
                "predicted_conversion_rate": predicted_cr,
                "predicted_epc": predicted_epc,
                "confidence_score": confidence,
                "recommendation": self._generate_performance_recommendation(
                    predicted_ctr, predicted_cr, predicted_epc
                ),
            }

        except Exception as e:
            self.logger.error(f"Error predicting link performance: {e}")
            return {
                "predicted_ctr": 0.0,
                "predicted_conversion_rate": 0.0,
                "predicted_epc": 0.0,
                "confidence_score": 0.0,
                "recommendation": "insufficient_data",
            }

    async def _extract_prediction_features(
        self, link: AffiliateLink, content_context: str, target_keywords: List[str]
    ) -> Dict[str, float]:
        """Extract features for performance prediction"""
        features = {}

        # Content features
        features["content_length"] = len(content_context.split())
        features["keyword_density"] = sum(
            content_context.lower().count(kw.lower()) for kw in target_keywords
        ) / max(len(content_context.split()), 1)

        # Link features
        features["commission_rate"] = link.commission_rate
        features["network_reliability"] = self._calculate_commission_value(link)
        features["category_popularity"] = self._get_category_popularity(link.product_category)

        # Historical features
        link_id = f"{link.network.value}_{link.product_name.replace(' ', '_').lower()}"
        history = self.performance_history.get(link_id, [])

        if history:
            recent_performance = history[-5:] if len(history) >= 5 else history
            features["historical_cr"] = sum(r["conversion_rate"] for r in recent_performance) / len(
                recent_performance
            )
            features["historical_epc"] = sum(
                r["earnings_per_click"] for r in recent_performance
            ) / len(recent_performance)
            features["data_points"] = len(history)
        else:
            features["historical_cr"] = 0.0
            features["historical_epc"] = 0.0
            features["data_points"] = 0

        # Temporal features
        features["month"] = datetime.now().month
        features["day_of_week"] = datetime.now().weekday()
        features["seasonal_boost"] = self._calculate_seasonal_boost(link)

        return features

    def _predict_click_through_rate(self, features: Dict[str, float]) -> float:
        """Predict click - through rate using feature - based model"""
        # Simplified prediction model
        base_ctr = 0.02  # 2% base CTR

        # Adjust based on features
        if features["content_length"] > 300:
            base_ctr *= 1.2

        if features["keyword_density"] > 0.02:
            base_ctr *= 1.3

        if features["seasonal_boost"] > 0.1:
            base_ctr *= 1.4

        # Network effect
        base_ctr *= features["network_reliability"]

        return min(base_ctr, 0.15)  # Cap at 15%

    def _predict_conversion_rate(self, features: Dict[str, float]) -> float:
        """Predict conversion rate using feature - based model"""
        if features["data_points"] > 5:
            # Use historical data with trend adjustment
            base_cr = features["historical_cr"]

            # Adjust for recent trends
            if features["seasonal_boost"] > 0.2:
                base_cr *= 1.5
            elif features["seasonal_boost"] > 0.1:
                base_cr *= 1.2
        else:
            # New link prediction
            base_cr = 0.03  # 3% base conversion rate

            # Category - based adjustment
            category_multipliers = {
                "software": 1.2,
                "education": 1.4,
                "health": 1.1,
                "finance": 0.9,
                "lifestyle": 1.0,
            }

            for category, multiplier in category_multipliers.items():
                if category in features.get("product_category", "").lower():
                    base_cr *= multiplier
                    break

        # Commission rate effect (higher commission often means lower CR)
        if features["commission_rate"] > 0.5:
            base_cr *= 0.8
        elif features["commission_rate"] > 0.2:
            base_cr *= 0.9

        return min(base_cr, 0.2)  # Cap at 20%

    def _predict_earnings_per_click(self, features: Dict[str, float]) -> float:
        """Predict earnings per click using feature - based model"""
        if features["data_points"] > 5:
            base_epc = features["historical_epc"]

            # Trend adjustment
            if features["seasonal_boost"] > 0.2:
                base_epc *= 1.3
        else:
            # Estimate based on commission rate and typical order values
            typical_order_values = {
                "software": 100,
                "education": 200,
                "health": 50,
                "finance": 500,
                "lifestyle": 75,
            }

            estimated_order_value = 100  # Default
            for category, value in typical_order_values.items():
                if category in features.get("product_category", "").lower():
                    estimated_order_value = value
                    break

            base_epc = estimated_order_value * features["commission_rate"] * 0.03  # 3% base CR

        return max(base_epc, 0.01)  # Minimum $0.01 EPC

    def _calculate_prediction_confidence(self, link: AffiliateLink) -> float:
        """Calculate confidence score for predictions"""
        link_id = f"{link.network.value}_{link.product_name.replace(' ', '_').lower()}"
        history = self.performance_history.get(link_id, [])

        if len(history) >= 20:
            return 0.9
        elif len(history) >= 10:
            return 0.7
        elif len(history) >= 5:
            return 0.5
        else:
            return 0.2

    def _generate_performance_recommendation(
        self, predicted_ctr: float, predicted_cr: float, predicted_epc: float
    ) -> str:
        """Generate performance recommendation based on predictions"""
        if predicted_epc > 1.0 and predicted_cr > 0.05:
            return "high_potential"
        elif predicted_epc > 0.5 and predicted_cr > 0.03:
            return "good_potential"
        elif predicted_epc > 0.1 and predicted_cr > 0.01:
            return "moderate_potential"
        else:
            return "low_potential"

    def _get_category_popularity(self, category: str) -> float:
        """Get category popularity score (simplified)"""
        popularity_scores = {
            "software": 0.9,
            "education": 0.8,
            "health": 0.7,
            "marketing": 0.8,
            "business": 0.7,
            "finance": 0.6,
            "lifestyle": 0.6,
            "technology": 0.9,
        }

        category_lower = category.lower()
        for cat, score in popularity_scores.items():
            if cat in category_lower:
                return score

        return 0.5  # Default moderate popularity

    async def _identify_opportunities(
        self, campaign: MarketingCampaign, analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify optimization opportunities"""
        opportunities = []

        # Content optimization opportunities
        if campaign.metrics.get(OptimizationMetric.ENGAGEMENT_RATE, 0) < 0.03:
            opportunities.append(
                {
                    "type": "content_optimization",
                    "focus": "engagement",
                    "hypothesis": "Improved content format will increase engagement",
                    "test_variants": [
                        "video_content",
                        "carousel_content",
                        "interactive_content",
                    ],
                }
            )

        # Timing optimization
        if campaign.metrics.get(OptimizationMetric.CLICK_THROUGH_RATE, 0) < 0.025:
            opportunities.append(
                {
                    "type": "timing_optimization",
                    "focus": "posting_schedule",
                    "hypothesis": "Optimal posting times will improve CTR",
                    "test_variants": [
                        "morning_posts",
                        "afternoon_posts",
                        "evening_posts",
                    ],
                }
            )

        # Audience targeting optimization
        if campaign.metrics.get(OptimizationMetric.CONVERSION_RATE, 0) < 0.015:
            opportunities.append(
                {
                    "type": "audience_optimization",
                    "focus": "targeting",
                    "hypothesis": "Refined audience targeting will improve conversions",
                    "test_variants": [
                        "lookalike_audience",
                        "interest_based",
                        "behavioral_targeting",
                    ],
                }
            )

        # Creative optimization
        opportunities.append(
            {
                "type": "creative_optimization",
                "focus": "ad_creative",
                "hypothesis": "New creative variations will improve performance",
                "test_variants": ["headline_a", "headline_b", "headline_c"],
            }
        )

        return opportunities

    async def _create_optimization_tests(
        self, campaign: MarketingCampaign, opportunities: List[Dict[str, Any]]
    ) -> None:
        """Create A / B tests for optimization opportunities"""
        for opportunity in opportunities:
            test_id = f"test_{campaign.campaign_id}_{int(time.time())}"

            # Create test variants
            variants = []
            for variant_name in opportunity["test_variants"]:
                variants.append(
                    {
                        "name": variant_name,
                        "traffic_split": 1.0 / len(opportunity["test_variants"]),
                        "config": self._generate_variant_config(variant_name, opportunity),
                    }
                )

            # Create optimization test
            test = OptimizationTest(
                test_id=test_id,
                name=f"{opportunity['type']} - {opportunity['focus']}",
                hypothesis=opportunity["hypothesis"],
                variants=variants,
                metric=OptimizationMetric.CONVERSION_RATE,  # Default metric
                start_date=datetime.now(),
                sample_size=1000,  # Minimum sample size
            )

            self.active_tests[test_id] = test

            # Start the test
            await self._start_test(test)

            self.logger.info(f"Created optimization test: {test.name}")

    def _generate_variant_config(
        self, variant_name: str, opportunity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate configuration for a test variant"""
        config = {"variant_name": variant_name}

        if opportunity["type"] == "content_optimization":
            config.update(
                {
                    "content_format": variant_name,
                    "engagement_elements": (
                        ["cta_button", "interactive_poll"]
                        if "interactive" in variant_name
                        else ["standard_cta"]
                    ),
                }
            )

        elif opportunity["type"] == "timing_optimization":
            time_configs = {
                "morning_posts": {"post_times": ["08:00", "09:00", "10:00"]},
                "afternoon_posts": {"post_times": ["12:00", "13:00", "14:00"]},
                "evening_posts": {"post_times": ["18:00", "19:00", "20:00"]},
            }
            config.update(time_configs.get(variant_name, {}))

        elif opportunity["type"] == "audience_optimization":
            audience_configs = {
                "lookalike_audience": {
                    "audience_type": "lookalike",
                    "similarity": 0.95,
                },
                "interest_based": {
                    "audience_type": "interests",
                    "interests": ["marketing", "business"],
                },
                "behavioral_targeting": {
                    "audience_type": "behavioral",
                    "behaviors": ["online_shoppers"],
                },
            }
            config.update(audience_configs.get(variant_name, {}))

        return config

    async def _start_test(self, test: OptimizationTest) -> None:
        """Start an optimization test"""
        try:
            # Initialize test tracking
            test.results = {
                "variant_performance": {
                    variant["name"]: {"conversions": 0, "impressions": 0}
                    for variant in test.variants
                },
                "statistical_significance": False,
                "confidence_level": 0.0,
            }

            # Start test monitoring
            asyncio.create_task(self._monitor_test(test))

        except Exception as e:
            self.logger.error(f"Error starting test {test.test_id}: {e}")

    async def _monitor_test(self, test: OptimizationTest) -> None:
        """Monitor an active test"""
        while test.status == "running":
            try:
                # Simulate test data collection
                await self._collect_test_data(test)

                # Check for statistical significance
                await self._check_statistical_significance(test)

                # Check if test should end
                if self._should_end_test(test):
                    await self._end_test(test)
                    break

                # Wait before next check
                await asyncio.sleep(1800)  # Check every 30 minutes

            except Exception as e:
                self.logger.error(f"Error monitoring test {test.test_id}: {e}")
                await asyncio.sleep(300)

    async def _collect_test_data(self, test: OptimizationTest) -> None:
        """Collect data for an active test"""
        for variant in test.variants:
            variant_name = variant["name"]

            # Simulate data collection
            new_impressions = random.randint(10, 100)
            new_conversions = random.randint(0, int(new_impressions * 0.05))

            test.results["variant_performance"][variant_name]["impressions"] += new_impressions
            test.results["variant_performance"][variant_name]["conversions"] += new_conversions

        # Update sample size
        test.sample_size = sum(
            data["impressions"] for data in test.results["variant_performance"].values()
        )

    async def _check_statistical_significance(self, test: OptimizationTest) -> None:
        """Check if test results are statistically significant"""
        # Simplified statistical significance check
        if test.sample_size < 1000:
            return

        variant_performances = test.results["variant_performance"]
        conversion_rates = []

        for variant_data in variant_performances.values():
            if variant_data["impressions"] > 0:
                cr = variant_data["conversions"] / variant_data["impressions"]
                conversion_rates.append(cr)

        if len(conversion_rates) >= 2:
            # Simple significance check (in production, use proper statistical tests)
            max_cr = max(conversion_rates)
            min_cr = min(conversion_rates)

            if max_cr > min_cr * 1.2:  # 20% improvement threshold
                test.results["statistical_significance"] = True
                test.results["confidence_level"] = 0.95

    def _should_end_test(self, test: OptimizationTest) -> bool:
        """Determine if a test should end"""
        # End test if statistically significant and minimum runtime met
        runtime_hours = (datetime.now() - test.start_date).total_seconds() / 3600

        if (
            test.results.get("statistical_significance", False)
            and runtime_hours >= 24
            and test.sample_size >= 1000
        ):
            return True

        # End test if maximum runtime reached
        if runtime_hours >= 168:  # 7 days
            return True

        return False

    async def _end_test(self, test: OptimizationTest) -> None:
        """End a test and determine winner"""
        test.status = "completed"
        test.end_date = datetime.now()

        # Determine winner
        best_variant = None
        best_conversion_rate = 0

        for variant_name, data in test.results["variant_performance"].items():
            if data["impressions"] > 0:
                cr = data["conversions"] / data["impressions"]
                if cr > best_conversion_rate:
                    best_conversion_rate = cr
                    best_variant = variant_name

        test.winner = best_variant

        # Log results
        self.logger.info(f"Test {test.test_id} completed. Winner: {best_variant}")

        # Add to optimization history
        self.optimization_history.append(
            {
                "test_id": test.test_id,
                "test_name": test.name,
                "winner": best_variant,
                "improvement": best_conversion_rate,
                "completed_at": datetime.now().isoformat(),
            }
        )

    async def _check_test_results(self, campaign: MarketingCampaign) -> None:
        """Check results of completed tests"""
        completed_tests = [
            test
            for test in self.active_tests.values()
            if test.status == "completed" and test.winner
        ]

        for test in completed_tests:
            self.logger.info(f"Test {test.test_id} winner: {test.winner}")

    async def _apply_winning_variations(self, campaign: MarketingCampaign) -> None:
        """Apply winning test variations to the campaign"""
        for test in self.active_tests.values():
            if test.status == "completed" and test.winner:
                # Apply winning variation to campaign
                await self._implement_winning_variation(campaign, test)

                # Remove from active tests
                del self.active_tests[test.test_id]

    async def _implement_winning_variation(
        self, campaign: MarketingCampaign, test: OptimizationTest
    ) -> None:
        """Implement a winning test variation"""
        try:
            winning_variant = next(
                variant for variant in test.variants if variant["name"] == test.winner
            )

            # Apply the winning configuration
            # This would integrate with actual marketing platforms
            self.logger.info(
                f"Implementing winning variation '{test.winner}' for campaign {campaign.campaign_id}"
            )

        except Exception as e:
            self.logger.error(f"Error implementing winning variation: {e}")


class AffiliateManager:
    """Intelligent context - aware affiliate link selection engine"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.affiliate_links: Dict[str, AffiliateLink] = {}
        self.performance_history: Dict[str, List[Dict]] = {}

    def add_affiliate_link(self, link: AffiliateLink) -> None:
        """Add an affiliate link to the manager"""
        link_id = f"{link.network.value}_{link.product_name.replace(' ', '_').lower()}"
        self.affiliate_links[link_id] = link
        self.performance_history[link_id] = []

        self.logger.info(f"Added affiliate link: {link.product_name}")

    async def select_optimal_links(
        self, content_context: str, target_keywords: List[str], max_links: int = 3
    ) -> List[AffiliateLink]:
        """Select optimal affiliate links based on content context"""
        try:
            # Calculate relevance scores for all links
            scored_links = []

            for link in self.affiliate_links.values():
                if not link.is_active:
                    continue

                relevance_score = await self._calculate_relevance_score(
                    link, content_context, target_keywords
                )

                link.context_relevance = relevance_score
                scored_links.append(link)

            # Sort by combined score (relevance + performance)
            scored_links.sort(key=lambda x: self._calculate_combined_score(x), reverse=True)

            # Return top links
            selected_links = scored_links[:max_links]

            # Log selection
            self.logger.info(f"Selected {len(selected_links)} affiliate links for content context")

            return selected_links

        except Exception as e:
            self.logger.error(f"Error selecting affiliate links: {e}")
            return []

    async def _calculate_relevance_score(
        self, link: AffiliateLink, content_context: str, target_keywords: List[str]
    ) -> float:
        """Calculate advanced relevance score using multiple AI techniques"""
        score = 0.0
        content_lower = content_context.lower()

        # 1. Enhanced keyword matching with TF - IDF weighting
        matching_keywords = set(target_keywords) & set(link.target_keywords)
        keyword_score = len(matching_keywords) / max(len(target_keywords), 1)

        # Weight keywords by frequency in content
        weighted_keyword_score = 0.0
        for keyword in matching_keywords:
            frequency = content_lower.count(keyword.lower())
            weighted_keyword_score += min(frequency * 0.1, 0.5)  # Cap at 0.5 per keyword

        score += keyword_score * 0.3 + weighted_keyword_score * 0.1

        # 2. Advanced product name relevance with fuzzy matching
        product_words = link.product_name.lower().split()
        exact_matches = sum(1 for word in product_words if word in content_lower)
        partial_matches = sum(
            1
            for word in product_words
            if any(word in content_word for content_word in content_lower.split())
        )

        product_score = (exact_matches * 0.8 + partial_matches * 0.2) / max(len(product_words), 1)
        score += product_score * 0.25

        # 3. Category and subcategory relevance
        category_score = 0.0
        if link.product_category.lower() in content_lower:
            category_score += 0.15

        # Check for related categories
        category_synonyms = self._get_category_synonyms(link.product_category)
        for synonym in category_synonyms:
            if synonym.lower() in content_lower:
                category_score += 0.05
                break

        score += min(category_score, 0.2)

        # 4. Enhanced semantic similarity with context awareness
        if TextBlob:
            try:
                content_blob = TextBlob(content_context)
                product_blob = TextBlob(link.product_name + " " + link.product_category)

                # Sentiment alignment
                content_sentiment = content_blob.sentiment.polarity
                product_sentiment = product_blob.sentiment.polarity
                sentiment_alignment = 1 - abs(content_sentiment - product_sentiment)

                # Word overlap with position weighting
                content_words = list(content_blob.words)
                product_words = list(product_blob.words)

                if content_words and product_words:
                    # Weight words by position (earlier words more important)
                    weighted_overlap = 0.0
                    for i, word in enumerate(content_words[:50]):  # First 50 words
                        if word.lower() in [pw.lower() for pw in product_words]:
                            position_weight = 1.0 - (i / 50) * 0.5  # Decay from 1.0 to 0.5
                            weighted_overlap += position_weight

                    semantic_score = min(weighted_overlap / len(content_words), 0.5)
                    score += semantic_score * 0.1 + sentiment_alignment * 0.05
            except Exception:
                pass

        # 5. Temporal relevance (trending topics, seasonality)
        temporal_score = await self._calculate_temporal_relevance(link, content_context)
        score += temporal_score * 0.1

        # 6. User behavior prediction
        behavior_score = await self._predict_user_engagement(link, content_context, target_keywords)
        score += behavior_score * 0.1

        return min(score, 1.0)

    def _calculate_combined_score(self, link: AffiliateLink) -> float:
        """Calculate intelligent combined score with dynamic weighting"""
        # Dynamic weight adjustment based on link maturity
        days_active = (datetime.now() - link.last_updated).days
        maturity_factor = min(days_active / 30, 1.0)  # Mature after 30 days

        if maturity_factor < 0.3:  # New links - prioritize relevance
            relevance_weight = 0.7
            performance_weight = 0.2
            commission_weight = 0.1
        else:  # Mature links - balance all factors
            relevance_weight = 0.4
            performance_weight = 0.4
            commission_weight = 0.2

        # Enhanced relevance score
        relevance_score = link.context_relevance

        # Advanced performance score with trend analysis
        performance_score = self._calculate_performance_trend(link)

        # Smart commission scoring with network reliability
        commission_score = self._calculate_commission_value(link)

        # Competition factor (lower score if many similar links)
        competition_penalty = self._calculate_competition_penalty(link)

        # Seasonal boost
        seasonal_boost = self._calculate_seasonal_boost(link)

        combined_score = (
            relevance_score * relevance_weight
            + performance_score * performance_weight
            + commission_score * commission_weight
            + seasonal_boost * 0.1
            - competition_penalty * 0.1
        )

        return max(min(combined_score, 1.0), 0.0)

    async def track_link_performance(
        self, link_id: str, clicks: int, conversions: int, revenue: float
    ) -> None:
        """Track performance metrics for an affiliate link"""
        if link_id not in self.affiliate_links:
            return

        link = self.affiliate_links[link_id]

        # Update performance metrics
        if clicks > 0:
            link.conversion_rate = conversions / clicks
            link.earnings_per_click = revenue / clicks

        # Add to performance history
        performance_record = {
            "timestamp": datetime.now().isoformat(),
            "clicks": clicks,
            "conversions": conversions,
            "revenue": revenue,
            "conversion_rate": link.conversion_rate,
            "earnings_per_click": link.earnings_per_click,
        }

        self.performance_history[link_id].append(performance_record)

        # Keep only last 30 records
        if len(self.performance_history[link_id]) > 30:
            self.performance_history[link_id] = self.performance_history[link_id][-30:]

        link.last_updated = datetime.now()

        self.logger.info(
            f"Updated performance for {link.product_name}: {conversions}/{clicks} conversions"
        )

        # Trigger automatic optimization if performance drops
        await self._check_performance_alerts(link_id, link)

    def get_top_performing_links(self, limit: int = 10) -> List[AffiliateLink]:
        """Get top performing affiliate links"""
        active_links = [link for link in self.affiliate_links.values() if link.is_active]

        # Sort by earnings per click
        top_links = sorted(active_links, key=lambda x: x.earnings_per_click, reverse=True)

        return top_links[:limit]

    def _get_category_synonyms(self, category: str) -> List[str]:
        """Get synonyms and related terms for a product category"""
        synonym_map = {
            "software": ["app", "application", "program", "tool", "platform", "system"],
            "marketing": [
                "advertising",
                "promotion",
                "branding",
                "seo",
                "social media",
            ],
            "education": ["learning", "training", "course", "tutorial", "teaching"],
            "health": ["wellness", "fitness", "medical", "healthcare", "nutrition"],
            "business": ["entrepreneurship", "startup", "corporate", "professional"],
            "technology": ["tech", "digital", "online", "internet", "web"],
            "finance": ["money", "investment", "trading", "banking", "cryptocurrency"],
            "lifestyle": ["living", "personal", "home", "family", "relationships"],
        }

        category_lower = category.lower()
        for key, synonyms in synonym_map.items():
            if key in category_lower or category_lower in synonyms:
                return synonyms

        return []

    async def _calculate_temporal_relevance(
        self, link: AffiliateLink, content_context: str
    ) -> float:
        """Calculate temporal relevance based on trends and seasonality"""
        try:
            current_month = datetime.now().month

            # Seasonal relevance mapping
            seasonal_keywords = {
                "christmas": [12, 11],  # Nov - Dec
                "holiday": [11, 12, 1],  # Nov - Jan
                "summer": [6, 7, 8],  # Jun - Aug
                "back to school": [8, 9],  # Aug - Sep
                "new year": [12, 1],  # Dec - Jan
                "valentine": [2],  # Feb
                "fitness": [1, 2, 6],  # Jan, Feb, Jun (New Year, Summer prep)
                "tax": [3, 4],  # Mar - Apr
                "graduation": [5, 6],  # May - Jun
            }

            content_lower = content_context.lower()
            temporal_score = 0.0

            for keyword, months in seasonal_keywords.items():
                if keyword in content_lower or keyword in link.product_name.lower():
                    if current_month in months:
                        temporal_score += 0.3
                    elif abs(min(abs(current_month - m) for m in months)) <= 1:
                        temporal_score += 0.1  # Adjacent months

            # Trending topics boost (simplified - could integrate with Google Trends API)
            trending_keywords = ["ai", "crypto", "nft", "remote work", "sustainability"]
            for keyword in trending_keywords:
                if keyword in content_lower:
                    temporal_score += 0.1

            return min(temporal_score, 0.5)

        except Exception as e:
            self.logger.warning(f"Error calculating temporal relevance: {e}")
            return 0.0

    async def _predict_user_engagement(
        self, link: AffiliateLink, content_context: str, target_keywords: List[str]
    ) -> float:
        """Predict user engagement likelihood using behavioral patterns"""
        try:
            engagement_score = 0.0

            # Content length factor (medium length performs better)
            content_length = len(content_context.split())
            if 200 <= content_length <= 800:
                engagement_score += 0.2
            elif 100 <= content_length <= 1200:
                engagement_score += 0.1

            # Question / CTA presence
            if any(marker in content_context.lower() for marker in ["?", "how to", "why", "what"]):
                engagement_score += 0.1

            # Urgency indicators
            urgency_words = ["limited", "exclusive", "now", "today", "hurry", "sale"]
            if any(word in content_context.lower() for word in urgency_words):
                engagement_score += 0.15

            # Social proof indicators
            social_proof = ["review", "testimonial", "rating", "customers", "users"]
            if any(word in content_context.lower() for word in social_proof):
                engagement_score += 0.1

            # Product - specific engagement patterns
            high_engagement_categories = ["software", "course", "ebook", "template"]
            if any(cat in link.product_category.lower() for cat in high_engagement_categories):
                engagement_score += 0.1

            return min(engagement_score, 0.5)

        except Exception as e:
            self.logger.warning(f"Error predicting user engagement: {e}")
            return 0.0

    def _calculate_performance_trend(self, link: AffiliateLink) -> float:
        """Calculate performance trend with recent data weighting"""
        try:
            link_id = f"{link.network.value}_{link.product_name.replace(' ', '_').lower()}"
            history = self.performance_history.get(link_id, [])

            if len(history) < 2:
                # New link - use current metrics
                return min((link.conversion_rate * 10 + link.earnings_per_click) / 2, 1.0)

            # Calculate trend from recent performance
            recent_records = history[-5:]  # Last 5 records
            older_records = history[-10:-5] if len(history) >= 10 else history[:-5]

            if not older_records:
                return min((link.conversion_rate * 10 + link.earnings_per_click) / 2, 1.0)

            # Calculate average performance for recent vs older periods
            recent_avg_cr = sum(r["conversion_rate"] for r in recent_records) / len(recent_records)
            recent_avg_epc = sum(r["earnings_per_click"] for r in recent_records) / len(
                recent_records
            )

            older_avg_cr = sum(r["conversion_rate"] for r in older_records) / len(older_records)
            older_avg_epc = sum(r["earnings_per_click"] for r in older_records) / len(older_records)

            # Calculate trend multiplier
            cr_trend = recent_avg_cr / max(older_avg_cr, 0.001)
            epc_trend = recent_avg_epc / max(older_avg_epc, 0.001)

            trend_multiplier = (cr_trend + epc_trend) / 2
            base_score = (recent_avg_cr * 10 + recent_avg_epc) / 2

            # Apply trend multiplier with bounds
            trending_score = base_score * min(max(trend_multiplier, 0.5), 2.0)

            return min(trending_score, 1.0)

        except Exception as e:
            self.logger.warning(f"Error calculating performance trend: {e}")
            return min((link.conversion_rate * 10 + link.earnings_per_click) / 2, 1.0)

    def _calculate_commission_value(self, link: AffiliateLink) -> float:
        """Calculate commission value with network reliability factor"""
        # Network reliability scores (based on typical industry performance)
        network_reliability = {
            AffiliateNetwork.AMAZON_ASSOCIATES: 0.9,
            AffiliateNetwork.CLICKBANK: 0.7,
            AffiliateNetwork.COMMISSION_JUNCTION: 0.8,
            AffiliateNetwork.SHAREASALE: 0.8,
            AffiliateNetwork.IMPACT: 0.85,
            AffiliateNetwork.RAKUTEN: 0.85,
            AffiliateNetwork.PARTNERSTACK: 0.75,
            AffiliateNetwork.CUSTOM: 0.6,
        }

        reliability_factor = network_reliability.get(link.network, 0.6)

        # Normalize commission rate (assuming 10% is high)
        normalized_commission = min(link.commission_rate / 0.1, 1.0)

        # Combine commission rate with network reliability
        commission_score = normalized_commission * reliability_factor

        return commission_score

    def _calculate_competition_penalty(self, link: AffiliateLink) -> float:
        """Calculate penalty for high competition in same category"""
        same_category_links = [
            l
            for l in self.affiliate_links.values()
            if l.product_category == link.product_category and l.is_active
        ]

        if len(same_category_links) <= 3:
            return 0.0
        elif len(same_category_links) <= 6:
            return 0.1
        else:
            return 0.2

    def _calculate_seasonal_boost(self, link: AffiliateLink) -> float:
        """Calculate seasonal boost for products"""
        current_month = datetime.now().month

        seasonal_products = {
            "fitness": [1, 2, 6],  # New Year, Summer prep
            "education": [8, 9, 1],  # Back to school, New Year
            "gift": [11, 12],  # Holiday season
            "tax": [3, 4],  # Tax season
            "travel": [5, 6, 7, 8],  # Summer travel
            "fashion": [3, 4, 9, 10],  # Spring / Fall fashion
        }

        product_lower = link.product_name.lower()
        category_lower = link.product_category.lower()

        for product_type, months in seasonal_products.items():
            if product_type in product_lower or product_type in category_lower:
                if current_month in months:
                    return 0.3
                elif any(abs(current_month - m) <= 1 for m in months):
                    return 0.1

        return 0.0

    async def _check_performance_alerts(self, link_id: str, link: AffiliateLink) -> None:
        """Check for performance alerts and trigger optimizations"""
        try:
            history = self.performance_history.get(link_id, [])

            if len(history) < 5:
                return  # Not enough data

            recent_records = history[-3:]
            older_records = history[-6:-3]

            if not older_records:
                return

            # Calculate performance decline
            recent_cr = sum(r["conversion_rate"] for r in recent_records) / len(recent_records)
            older_cr = sum(r["conversion_rate"] for r in older_records) / len(older_records)

            recent_epc = sum(r["earnings_per_click"] for r in recent_records) / len(recent_records)
            older_epc = sum(r["earnings_per_click"] for r in older_records) / len(older_records)

            # Check for significant decline (>30%)
            cr_decline = (older_cr - recent_cr) / max(older_cr, 0.001)
            epc_decline = (older_epc - recent_epc) / max(older_epc, 0.001)

            if cr_decline > 0.3 or epc_decline > 0.3:
                self.logger.warning(
                    f"Performance decline detected for {link.product_name}: "
                    f"CR decline: {cr_decline:.2%}, EPC decline: {epc_decline:.2%}"
                )

                # Trigger optimization actions
                await self._trigger_link_optimization(link_id, link)

            # Check for consistently low performance
            if recent_cr < 0.01 and len(history) > 10:  # Less than 1% conversion
                self.logger.info(
                    f"Low performance detected for {link.product_name}, considering deactivation"
                )
                await self._consider_link_deactivation(link_id, link)

        except Exception as e:
            self.logger.error(f"Error checking performance alerts: {e}")

    async def _trigger_link_optimization(self, link_id: str, link: AffiliateLink) -> None:
        """Trigger optimization actions for underperforming links"""
        optimization_actions = [
            "Update target keywords based on recent trends",
            "Refresh product description and benefits",
            "Test different placement strategies",
            "Review competitor offerings",
            "Update promotional messaging",
        ]

        self.logger.info(
            f"Triggering optimization for {link.product_name}. "
            f"Suggested actions: {', '.join(optimization_actions[:3])}"
        )

        # Could integrate with external optimization systems here

    async def _consider_link_deactivation(self, link_id: str, link: AffiliateLink) -> None:
        """Consider deactivating consistently poor performing links"""
        # Implement business logic for link deactivation
        # For now, just log the recommendation
        self.logger.info(
            f"Consider deactivating {link.product_name} due to consistently low performance. "
            f"Current CR: {link.conversion_rate:.3%}, EPC: ${link.earnings_per_click:.3f}"
        )

    def analyze_link_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze affiliate link performance over specified period"""
        cutoff_date = datetime.now() - timedelta(days=days)

        analysis = {
            "total_links": len(self.affiliate_links),
            "active_links": len([l for l in self.affiliate_links.values() if l.is_active]),
            "top_performers": [],
            "underperformers": [],
            "total_revenue": 0.0,
            "average_conversion_rate": 0.0,
        }

        conversion_rates = []
        total_revenue = 0.0

        for link_id, link in self.affiliate_links.items():
            if not link.is_active:
                continue

            # Calculate recent performance
            recent_records = [
                record
                for record in self.performance_history.get(link_id, [])
                if datetime.fromisoformat(record["timestamp"]) > cutoff_date
            ]

            if recent_records:
                recent_revenue = sum(record["revenue"] for record in recent_records)
                recent_conversions = sum(record["conversions"] for record in recent_records)
                recent_clicks = sum(record["clicks"] for record in recent_records)

                total_revenue += recent_revenue

                if recent_clicks > 0:
                    recent_cr = recent_conversions / recent_clicks
                    conversion_rates.append(recent_cr)

                    if recent_cr > 0.05:  # 5% conversion rate threshold
                        analysis["top_performers"].append(
                            {
                                "product": link.product_name,
                                "conversion_rate": recent_cr,
                                "revenue": recent_revenue,
                            }
                        )
                    elif recent_cr < 0.01:  # 1% conversion rate threshold
                        analysis["underperformers"].append(
                            {
                                "product": link.product_name,
                                "conversion_rate": recent_cr,
                                "revenue": recent_revenue,
                            }
                        )

        analysis["total_revenue"] = total_revenue
        analysis["average_conversion_rate"] = (
            sum(conversion_rates) / len(conversion_rates) if conversion_rates else 0.0
        )

        return analysis


class CrossPromotionManager:
    """Manages cross - promotion between content with "The Right Perspective" exception"""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.promotion_rules: List[CrossPromotionRule] = []
        self.right_perspective_exceptions: Set[str] = set()
        self.perspective_filters: Dict[str, Dict[str, Any]] = {}
        self.exception_reasons: Dict[str, str] = {}
        self.perspective_scores: Dict[str, float] = {}
        self.content_relationships: Dict[str, List[str]] = {}
        self.temporal_exceptions: Dict[str, datetime] = {}
        self.context_sensitive_rules: List[Dict[str, Any]] = []

    def add_promotion_rule(self, rule: CrossPromotionRule) -> None:
        """Add a cross - promotion rule"""
        self.promotion_rules.append(rule)
        self.logger.info(f"Added promotion rule: {rule.source_content} -> {rule.target_content}")

    def add_right_perspective_exception(
        self,
        content_id: str,
        reason: str,
        temporary: bool = False,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Add content to 'The Right Perspective' exception list with advanced handling"""
        self.right_perspective_exceptions.add(content_id)
        self.exception_reasons[content_id] = reason

        if temporary and expires_at:
            self.temporal_exceptions[content_id] = expires_at

        # Log with detailed context
        exception_type = "temporary" if temporary else "permanent"
        self.logger.info(
            f"Added {exception_type} Right Perspective exception for {content_id}: {reason}"
        )

        # Trigger cascade exception check for related content
        self._check_cascade_exceptions(content_id, reason)

    async def generate_cross_promotions(
        self, source_content_id: str, content_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate cross - promotion recommendations with advanced Right Perspective filtering"""
        try:
            # Clean expired temporal exceptions
            self._clean_expired_exceptions()

            # Multi - layer Right Perspective validation
            perspective_check = await self._comprehensive_perspective_check(
                source_content_id, content_metadata
            )

            if not perspective_check["allowed"]:
                self.logger.info(
                    f"Blocking cross - promotion for {source_content_id}: {perspective_check['reason']}"
                )
                return []

            promotions = []

            # Find applicable promotion rules with context sensitivity
            applicable_rules = await self._get_context_aware_rules(
                source_content_id, content_metadata
            )

            for rule in applicable_rules:
                # Advanced target validation
                target_validation = await self._validate_promotion_target(
                    rule, content_metadata, source_content_id
                )

                if not target_validation["valid"]:
                    self.logger.debug(
                        f"Skipping promotion to {rule.target_content}: {target_validation['reason']}"
                    )
                    continue

                # Generate promotion with perspective scoring
                promotion = await self._generate_perspective_aware_promotion(
                    rule, content_metadata, perspective_check["score"]
                )

                if promotion and promotion.get("perspective_score", 0) >= self.config.get(
                    "min_perspective_score", 0.6
                ):
                    promotions.append(promotion)

            # Advanced sorting with multiple factors
            promotions = self._rank_promotions_by_perspective(promotions, content_metadata)

            self.logger.info(
                f"Generated {len(promotions)} perspective - validated cross - promotions for {source_content_id}"
            )
            return promotions

        except Exception as e:
            self.logger.error(f"Critical error in cross - promotion generation: {e}")
            # Implement graceful degradation
            return await self._fallback_promotion_generation(source_content_id, content_metadata)

    def _matches_content(self, rule_pattern: str, content_metadata: Dict[str, Any]) -> bool:
        """Check if content matches a promotion rule pattern"""
        # Simple pattern matching - can be enhanced with regex or ML
        content_text = (
            content_metadata.get("title", "")
            + " "
            + content_metadata.get("description", "")
            + " "
            + " ".join(content_metadata.get("tags", []))
        ).lower()

        return rule_pattern.lower() in content_text

    async def _generate_promotion(
        self, rule: CrossPromotionRule, content_metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Generate a specific promotion based on a rule"""
        try:
            promotion = {
                "type": rule.promotion_type,
                "target_content": rule.target_content,
                "context": rule.context,
                "relevance_score": rule.relevance_score,
                "placement_suggestions": [],
                "content_snippet": "",
            }

            # Generate placement suggestions based on promotion type
            if rule.promotion_type == "mention":
                promotion["placement_suggestions"] = [
                    "In the introduction",
                    "As a related topic reference",
                    "In the conclusion",
                ]
                promotion[
                    "content_snippet"
                ] = f"For more insights on this topic, check out our content on {rule.target_content}."

            elif rule.promotion_type == "link":
                promotion["placement_suggestions"] = [
                    "As a call - to - action button",
                    "In a related resources section",
                    "As an inline text link",
                ]
                promotion["content_snippet"] = f"Learn more: {rule.target_content}"

            elif rule.promotion_type == "embed":
                promotion["placement_suggestions"] = [
                    "As a sidebar widget",
                    "Between content sections",
                    "At the end of the content",
                ]
                promotion["content_snippet"] = f"[EMBED: {rule.target_content}]"

            elif rule.promotion_type == "recommendation":
                promotion["placement_suggestions"] = [
                    'In a "You might also like" section',
                    "As a popup recommendation",
                    "In an email follow - up",
                ]
                promotion["content_snippet"] = f"Recommended: {rule.target_content}"

            return promotion

        except Exception as e:
            self.logger.error(f"Error generating promotion: {e}")
            return None

    def analyze_promotion_performance(self, days: int = 30) -> Dict[str, Any]:
        """Analyze cross - promotion performance"""
        # This would integrate with analytics to track actual performance
        # For now, return simulated analysis

        analysis = {
            "total_promotions": len(self.promotion_rules),
            "active_promotions": len([r for r in self.promotion_rules if r.is_active]),
            "right_perspective_exceptions": len(self.right_perspective_exceptions),
            "top_performing_rules": [],
            "underperforming_rules": [],
            "average_click_through_rate": 0.0,
        }

        # Simulate performance data
        for rule in self.promotion_rules:
            if rule.is_active:
                simulated_ctr = random.uniform(0.01, 0.08)

                if simulated_ctr > 0.05:
                    analysis["top_performing_rules"].append(
                        {
                            "source": rule.source_content,
                            "target": rule.target_content,
                            "ctr": simulated_ctr,
                            "type": rule.promotion_type,
                        }
                    )
                elif simulated_ctr < 0.02:
                    analysis["underperforming_rules"].append(
                        {
                            "source": rule.source_content,
                            "target": rule.target_content,
                            "ctr": simulated_ctr,
                            "type": rule.promotion_type,
                        }
                    )

        return analysis

    def optimize_promotion_rules(self) -> List[str]:
        """Optimize promotion rules based on performance"""
        recommendations = []

        # Analyze rule performance
        performance = self.analyze_promotion_performance()

        # Recommend disabling underperforming rules
        for rule_data in performance["underperforming_rules"]:
            recommendations.append(
                f"Consider disabling promotion from '{rule_data['source']}' to '{rule_data['target']}' (CTR: {rule_data['ctr']:.3f})"
            )

        # Recommend scaling up top performers
        for rule_data in performance["top_performing_rules"]:
            recommendations.append(
                f"Consider expanding promotion from '{rule_data['source']}' to '{rule_data['target']}' (CTR: {rule_data['ctr']:.3f})"
            )

        return recommendations

    def _check_cascade_exceptions(self, content_id: str, reason: str) -> None:
        """Check if exception should cascade to related content"""
        if content_id in self.content_relationships:
            related_content = self.content_relationships[content_id]

            # Apply cascade logic based on reason
            cascade_reasons = {
                "controversial_topic": "Related to controversial content",
                "brand_conflict": "Brand alignment conflict",
                "audience_mismatch": "Audience demographic mismatch",
                "quality_concern": "Quality standards violation",
            }

            if any(cascade_reason in reason.lower() for cascade_reason in cascade_reasons.keys()):
                for related_id in related_content:
                    if related_id not in self.right_perspective_exceptions:
                        cascade_reason = next(
                            (
                                cascade_reasons[key]
                                for key in cascade_reasons.keys()
                                if key in reason.lower()
                            ),
                            "Cascade from related content",
                        )
                        self.add_right_perspective_exception(
                            related_id,
                            f"{cascade_reason}: {content_id}",
                            temporary=True,
                            expires_at=datetime.now() + timedelta(hours=24),
                        )

    def _clean_expired_exceptions(self) -> None:
        """Remove expired temporal exceptions"""
        current_time = datetime.now()
        expired_exceptions = [
            content_id
            for content_id, expires_at in self.temporal_exceptions.items()
            if expires_at <= current_time
        ]

        for content_id in expired_exceptions:
            self.right_perspective_exceptions.discard(content_id)
            del self.temporal_exceptions[content_id]
            if content_id in self.exception_reasons:
                del self.exception_reasons[content_id]
            self.logger.info(f"Removed expired Right Perspective exception for {content_id}")

    async def _comprehensive_perspective_check(
        self, content_id: str, content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform comprehensive Right Perspective validation"""
        # Basic exception check
        if content_id in self.right_perspective_exceptions:
            return {
                "allowed": False,
                "reason": f"Direct exception: {self.exception_reasons.get(content_id, 'Unknown')}",
                "score": 0.0,
            }

        # Content analysis for perspective alignment
        perspective_score = await self._calculate_perspective_score(content_metadata)

        # Context - sensitive filtering
        context_filters = await self._apply_context_filters(content_metadata)

        # Brand safety check
        brand_safety = await self._check_brand_safety(content_metadata)

        # Audience alignment check
        audience_alignment = await self._check_audience_alignment(content_metadata)

        # Calculate composite score
        composite_score = (
            perspective_score * 0.4
            + context_filters["score"] * 0.3
            + brand_safety["score"] * 0.2
            + audience_alignment["score"] * 0.1
        )

        min_threshold = self.config.get("perspective_threshold", 0.7)

        return {
            "allowed": composite_score >= min_threshold,
            "reason": (
                self._get_blocking_reason(
                    {
                        "perspective": perspective_score,
                        "context": context_filters,
                        "brand_safety": brand_safety,
                        "audience": audience_alignment,
                    }
                )
                if composite_score < min_threshold
                else "Approved"
            ),
            "score": composite_score,
            "breakdown": {
                "perspective_score": perspective_score,
                "context_score": context_filters["score"],
                "brand_safety_score": brand_safety["score"],
                "audience_alignment_score": audience_alignment["score"],
            },
        }

    async def _calculate_perspective_score(self, content_metadata: Dict[str, Any]) -> float:
        """Calculate perspective alignment score"""
        try:
            # Analyze content sentiment and tone
            content_text = (
                content_metadata.get("title", "")
                + " "
                + content_metadata.get("description", "")
                + " "
                + " ".join(content_metadata.get("tags", []))
            )

            if not content_text.strip():
                return 0.5  # Neutral score for empty content

            # Sentiment analysis (simplified)
            if TextBlob:
                blob = TextBlob(content_text)
                sentiment_score = (blob.sentiment.polarity + 1) / 2  # Normalize to 0 - 1
            else:
                sentiment_score = 0.5

            # Topic relevance scoring
            topic_score = self._score_topic_relevance(content_metadata)

            # Quality indicators
            quality_score = self._assess_content_quality(content_metadata)

            # Combine scores
            perspective_score = sentiment_score * 0.3 + topic_score * 0.4 + quality_score * 0.3

            return max(0.0, min(1.0, perspective_score))

        except Exception as e:
            self.logger.warning(f"Error calculating perspective score: {e}")
            return 0.5

    def _score_topic_relevance(self, content_metadata: Dict[str, Any]) -> float:
        """Score topic relevance for Right Perspective"""
        # Define topic categories and their perspective scores
        topic_scores = {
            "educational": 0.9,
            "tutorial": 0.9,
            "review": 0.8,
            "entertainment": 0.7,
            "news": 0.6,
            "opinion": 0.5,
            "controversial": 0.2,
            "political": 0.3,
            "adult": 0.1,
        }

        content_text = (
            content_metadata.get("title", "")
            + " "
            + content_metadata.get("description", "")
            + " "
            + " ".join(content_metadata.get("tags", []))
        ).lower()

        # Calculate weighted score based on topic presence
        total_score = 0.0
        total_weight = 0.0

        for topic, score in topic_scores.items():
            if topic in content_text:
                weight = content_text.count(topic)
                total_score += score * weight
                total_weight += weight

        return total_score / total_weight if total_weight > 0 else 0.7  # Default neutral - positive

    def _assess_content_quality(self, content_metadata: Dict[str, Any]) -> float:
        """Assess content quality indicators"""
        quality_indicators = {
            "has_description": 0.2 if content_metadata.get("description") else 0.0,
            "has_tags": 0.2 if content_metadata.get("tags") else 0.0,
            "title_length": min(0.2, len(content_metadata.get("title", "")) / 100),
            "engagement_metrics": min(0.2, content_metadata.get("engagement_score", 0) / 100),
            "production_value": content_metadata.get("production_score", 0.2),
        }

        return sum(quality_indicators.values())

    async def _apply_context_filters(self, content_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Apply context - sensitive filters"""
        filters_passed = 0
        total_filters = 0
        reasons = []

        # Time - based filtering
        current_hour = datetime.now().hour
        if "time_sensitive" in content_metadata:
            total_filters += 1
            if self._is_appropriate_time(content_metadata, current_hour):
                filters_passed += 1
            else:
                reasons.append("Inappropriate timing")

        # Geographic filtering
        if "geo_restrictions" in content_metadata:
            total_filters += 1
            if self._check_geo_compliance(content_metadata):
                filters_passed += 1
            else:
                reasons.append("Geographic restrictions")

        # Platform - specific filtering
        if "platform_rules" in content_metadata:
            total_filters += 1
            if self._check_platform_compliance(content_metadata):
                filters_passed += 1
            else:
                reasons.append("Platform policy violation")

        score = filters_passed / total_filters if total_filters > 0 else 1.0

        return {
            "score": score,
            "passed": filters_passed,
            "total": total_filters,
            "reasons": reasons,
        }

    async def _check_brand_safety(self, content_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check brand safety compliance"""
        safety_score = 1.0
        issues = []

        # Check for brand - unsafe keywords
        unsafe_keywords = self.config.get(
            "unsafe_keywords",
            ["controversy", "scandal", "illegal", "harmful", "offensive"],
        )

        content_text = (
            content_metadata.get("title", "") + " " + content_metadata.get("description", "")
        ).lower()

        for keyword in unsafe_keywords:
            if keyword in content_text:
                safety_score -= 0.2
                issues.append(f"Contains unsafe keyword: {keyword}")

        # Check content rating
        content_rating = content_metadata.get("content_rating", "general")
        if content_rating in ["mature", "adult", "restricted"]:
            safety_score -= 0.3
            issues.append(f"Inappropriate content rating: {content_rating}")

        return {"score": max(0.0, safety_score), "issues": issues}

    async def _check_audience_alignment(self, content_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Check audience alignment"""
        target_demographics = self.config.get("target_demographics", {})
        content_demographics = content_metadata.get("target_audience", {})

        if not target_demographics or not content_demographics:
            return {"score": 0.8}  # Default neutral score

        alignment_score = 0.0
        factors_checked = 0

        # Age alignment
        if "age_range" in target_demographics and "age_range" in content_demographics:
            factors_checked += 1
            if self._check_age_overlap(
                target_demographics["age_range"], content_demographics["age_range"]
            ):
                alignment_score += 0.4

        # Interest alignment
        if "interests" in target_demographics and "interests" in content_demographics:
            factors_checked += 1
            overlap = self._calculate_interest_overlap(
                target_demographics["interests"], content_demographics["interests"]
            )
            alignment_score += overlap * 0.6

        final_score = alignment_score if factors_checked > 0 else 0.8

        return {"score": min(1.0, final_score)}

    def _get_blocking_reason(self, scores: Dict[str, Any]) -> str:
        """Generate human - readable blocking reason"""
        reasons = []

        if scores["perspective"] < 0.5:
            reasons.append("Content perspective misalignment")

        if scores["context"]["score"] < 0.7:
            reasons.extend(scores["context"]["reasons"])

        if scores["brand_safety"]["score"] < 0.7:
            reasons.extend(scores["brand_safety"]["issues"])

        if scores["audience"]["score"] < 0.6:
            reasons.append("Audience demographic mismatch")

        return "; ".join(reasons) if reasons else "Multiple perspective violations"

    async def _get_context_aware_rules(
        self, source_content_id: str, content_metadata: Dict[str, Any]
    ) -> List[CrossPromotionRule]:
        """Get promotion rules with context awareness"""
        base_rules = [
            rule
            for rule in self.promotion_rules
            if rule.is_active and self._matches_content(rule.source_content, content_metadata)
        ]

        # Apply context - sensitive rule modifications
        context_aware_rules = []

        for rule in base_rules:
            # Check if rule has context - sensitive modifications
            modified_rule = await self._apply_context_modifications(rule, content_metadata)
            if modified_rule:
                context_aware_rules.append(modified_rule)

        return context_aware_rules

    async def _apply_context_modifications(
        self, rule: CrossPromotionRule, content_metadata: Dict[str, Any]
    ) -> Optional[CrossPromotionRule]:
        """Apply context - sensitive modifications to promotion rules"""
        # Create a copy of the rule for modification
        modified_rule = CrossPromotionRule(
            source_content=rule.source_content,
            target_content=rule.target_content,
            relevance_score=rule.relevance_score,
            promotion_type=rule.promotion_type,
            context=rule.context,
            exceptions=rule.exceptions.copy(),
            is_active=rule.is_active,
        )

        # Apply time - based modifications
        current_hour = datetime.now().hour
        if current_hour < 9 or current_hour > 21:  # Outside business hours
            modified_rule.relevance_score *= 0.8

        # Apply audience - based modifications
        if "professional" in content_metadata.get("audience_type", ""):
            if rule.promotion_type == "embed":
                modified_rule.promotion_type = "link"  # Less intrusive for professional content

        # Apply content - type modifications
        if content_metadata.get("content_type") == "educational":
            modified_rule.relevance_score *= 1.2  # Boost educational cross - promotions

        return modified_rule

    async def _validate_promotion_target(
        self,
        rule: CrossPromotionRule,
        content_metadata: Dict[str, Any],
        source_content_id: str,
    ) -> Dict[str, Any]:
        """Validate promotion target with advanced checks"""
        # Basic exception check
        if rule.target_content in self.right_perspective_exceptions:
            return {
                "valid": False,
                "reason": f"Target has Right Perspective exception: {self.exception_reasons.get(rule.target_content, 'Unknown')}",
            }

        # Circular promotion check
        if self._creates_circular_promotion(source_content_id, rule.target_content):
            return {"valid": False, "reason": "Would create circular promotion loop"}

        # Content compatibility check
        compatibility_score = await self._check_content_compatibility(
            content_metadata, rule.target_content
        )

        if compatibility_score < self.config.get("min_compatibility_score", 0.6):
            return {
                "valid": False,
                "reason": f"Low content compatibility score: {compatibility_score:.2f}",
            }

        # Frequency capping check
        if self._exceeds_frequency_cap(rule.target_content, source_content_id):
            return {"valid": False, "reason": "Exceeds promotion frequency cap"}

        return {"valid": True, "reason": "Validation passed"}

    async def _generate_perspective_aware_promotion(
        self,
        rule: CrossPromotionRule,
        content_metadata: Dict[str, Any],
        perspective_score: float,
    ) -> Optional[Dict[str, Any]]:
        """Generate promotion with perspective awareness"""
        try:
            base_promotion = await self._generate_promotion(rule, content_metadata)
            if not base_promotion:
                return None

            # Enhance with perspective scoring
            base_promotion["perspective_score"] = perspective_score
            base_promotion["perspective_factors"] = {
                "content_alignment": perspective_score,
                "audience_fit": await self._calculate_audience_fit(rule, content_metadata),
                "timing_appropriateness": self._calculate_timing_score(content_metadata),
                "brand_safety": await self._calculate_brand_safety_score(rule.target_content),
            }

            # Adjust promotion based on perspective score
            if perspective_score < 0.7:
                # Lower visibility for lower - scoring content
                base_promotion["placement_suggestions"] = [
                    suggestion
                    for suggestion in base_promotion["placement_suggestions"]
                    if "prominent" not in suggestion.lower()
                ]

            # Add perspective - based content modifications
            base_promotion["content_snippet"] = self._adjust_content_for_perspective(
                base_promotion["content_snippet"], perspective_score
            )

            return base_promotion

        except Exception as e:
            self.logger.error(f"Error generating perspective - aware promotion: {e}")
            return None

    def _rank_promotions_by_perspective(
        self, promotions: List[Dict[str, Any]], content_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Rank promotions using perspective - aware scoring"""

        def calculate_composite_score(promotion):
            base_score = promotion.get("relevance_score", 0)
            perspective_score = promotion.get("perspective_score", 0)

            # Weight factors based on content type
            content_type = content_metadata.get("content_type", "general")

            if content_type == "educational":
                return base_score * 0.3 + perspective_score * 0.7
            elif content_type == "entertainment":
                return base_score * 0.6 + perspective_score * 0.4
            else:
                return base_score * 0.5 + perspective_score * 0.5

        # Sort by composite score
        promotions.sort(key=calculate_composite_score, reverse=True)

        # Apply diversity filtering to avoid over - promotion of similar content
        diverse_promotions = self._apply_diversity_filter(promotions)

        return diverse_promotions

    async def _fallback_promotion_generation(
        self, source_content_id: str, content_metadata: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Fallback promotion generation with minimal Right Perspective filtering"""
        try:
            self.logger.info(f"Using fallback promotion generation for {source_content_id}")

            # Use only basic exception checking
            if source_content_id in self.right_perspective_exceptions:
                return []

            # Generate minimal safe promotions
            safe_promotions = []

            # Find the safest promotion rules (highest relevance, lowest risk)
            safe_rules = [
                rule
                for rule in self.promotion_rules
                if (
                    rule.is_active
                    and rule.relevance_score > 0.8
                    and rule.target_content not in self.right_perspective_exceptions
                    and rule.promotion_type in ["link", "mention"]
                )  # Safest promotion types
            ]

            for rule in safe_rules[:3]:  # Limit to top 3 safest
                promotion = {
                    "type": rule.promotion_type,
                    "target_content": rule.target_content,
                    "context": "Safe fallback promotion",
                    "relevance_score": rule.relevance_score * 0.8,  # Reduce score for fallback
                    "perspective_score": 0.6,  # Conservative score
                    "placement_suggestions": ["At the end of content"],
                    "content_snippet": f"You might also find this helpful: {rule.target_content}",
                }
                safe_promotions.append(promotion)

            return safe_promotions

        except Exception as e:
            self.logger.error(f"Fallback promotion generation failed: {e}")
            return []

    # Helper methods for the new functionality

    def _is_appropriate_time(self, content_metadata: Dict[str, Any], current_hour: int) -> bool:
        """Check if current time is appropriate for content"""
        time_restrictions = content_metadata.get("time_restrictions", {})
        if not time_restrictions:
            return True

        start_hour = time_restrictions.get("start_hour", 0)
        end_hour = time_restrictions.get("end_hour", 23)

        return start_hour <= current_hour <= end_hour

    def _check_geo_compliance(self, content_metadata: Dict[str, Any]) -> bool:
        """Check geographic compliance"""
        # Simplified geo - compliance check
        restricted_regions = content_metadata.get("geo_restrictions", {}).get("blocked_regions", [])
        current_region = self.config.get("current_region", "US")

        return current_region not in restricted_regions

    def _check_platform_compliance(self, content_metadata: Dict[str, Any]) -> bool:
        """Check platform - specific compliance"""
        platform_rules = content_metadata.get("platform_rules", {})
        current_platform = self.config.get("current_platform", "web")

        platform_restrictions = platform_rules.get(current_platform, {})

        # Check various platform - specific restrictions
        if platform_restrictions.get("blocked", False):
            return False

        if platform_restrictions.get("requires_age_verification", False) and not self.config.get(
            "age_verified", False
        ):
            return False

        return True

    def _check_age_overlap(self, target_range: str, content_range: str) -> bool:
        """Check if age ranges overlap"""
        # Simplified age range overlap check
        age_mappings = {
            "13 - 17": (13, 17),
            "18 - 24": (18, 24),
            "25 - 34": (25, 34),
            "35 - 44": (35, 44),
            "45 - 54": (45, 54),
            "55+": (55, 100),
        }

        target_min, target_max = age_mappings.get(target_range, (0, 100))
        content_min, content_max = age_mappings.get(content_range, (0, 100))

        return not (target_max < content_min or content_max < target_min)

    def _calculate_interest_overlap(
        self, target_interests: List[str], content_interests: List[str]
    ) -> float:
        """Calculate interest overlap percentage"""
        if not target_interests or not content_interests:
            return 0.5

        target_set = set(interest.lower() for interest in target_interests)
        content_set = set(interest.lower() for interest in content_interests)

        intersection = target_set.intersection(content_set)
        union = target_set.union(content_set)

        return len(intersection) / len(union) if union else 0.0

    def _creates_circular_promotion(self, source_id: str, target_id: str) -> bool:
        """Check if promotion would create a circular reference"""
        # Simple circular reference check
        if source_id == target_id:
            return True

        # Check if target already promotes back to source
        for rule in self.promotion_rules:
            if rule.source_content == target_id and rule.target_content == source_id:
                return True

        return False

    async def _check_content_compatibility(
        self, source_metadata: Dict[str, Any], target_content: str
    ) -> float:
        """Check compatibility between source and target content"""
        # Simplified compatibility scoring
        compatibility_score = 0.5  # Base score

        # Category compatibility
        source_category = source_metadata.get("category", "")
        # In a real implementation, you'd fetch target content metadata
        # For now, use a simplified approach

        if source_category:
            compatibility_score += 0.3

        # Topic similarity (simplified)
        source_tags = set(tag.lower() for tag in source_metadata.get("tags", []))
        if source_tags:
            compatibility_score += 0.2

        return min(1.0, compatibility_score)

    def _exceeds_frequency_cap(self, target_content: str, source_content: str) -> bool:
        """Check if promotion exceeds frequency cap"""
        # Simplified frequency capping
        max_promotions_per_day = self.config.get("max_promotions_per_day", 5)

        # In a real implementation, you'd track actual promotion frequency
        # For now, return False (no frequency cap exceeded)
        return False

    async def _calculate_audience_fit(
        self, rule: CrossPromotionRule, content_metadata: Dict[str, Any]
    ) -> float:
        """Calculate how well the promotion fits the audience"""
        # Simplified audience fit calculation
        return 0.8  # Default good fit

    def _calculate_timing_score(self, content_metadata: Dict[str, Any]) -> float:
        """Calculate timing appropriateness score"""
        current_hour = datetime.now().hour

        # Business hours get higher scores for professional content
        if content_metadata.get("content_type") == "professional":
            if 9 <= current_hour <= 17:
                return 1.0
            else:
                return 0.6

        # Entertainment content scores higher in evening
        if content_metadata.get("content_type") == "entertainment":
            if 18 <= current_hour <= 23:
                return 1.0
            else:
                return 0.7

        return 0.8  # Default score

    async def _calculate_brand_safety_score(self, target_content: str) -> float:
        """Calculate brand safety score for target content"""
        # Simplified brand safety scoring
        # In a real implementation, this would analyze the target content
        return 0.9  # Default high safety score

    def _adjust_content_for_perspective(
        self, content_snippet: str, perspective_score: float
    ) -> str:
        """Adjust content snippet based on perspective score"""
        if perspective_score < 0.6:
            # Make content more conservative for lower scores
            return content_snippet.replace("check out", "you might find helpful")
        elif perspective_score > 0.8:
            # Make content more engaging for higher scores
            return content_snippet.replace("you might find helpful", "definitely check out")

        return content_snippet

    def _apply_diversity_filter(self, promotions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply diversity filtering to avoid over - promotion of similar content"""
        if len(promotions) <= 3:
            return promotions

        # Group by promotion type and target category
        diverse_promotions = []
        seen_types = set()

        for promotion in promotions:
            promo_type = promotion.get("type", "")
            if promo_type not in seen_types or len(diverse_promotions) < 2:
                diverse_promotions.append(promotion)
                seen_types.add(promo_type)

            if len(diverse_promotions) >= 5:  # Limit total promotions
                break

        return diverse_promotions


# Example usage and testing
if __name__ == "__main__":

    async def test_marketing_tools():
        """Test the marketing tools"""
        print("Testing Marketing Agent Tools...")

        # Test Day One Blitz Strategy
        print("\\n1. Testing Day One Blitz Strategy...")
        blitz = DayOneBlitzStrategy()

        try:
            campaign = await blitz.launch_blitz_campaign(
                product_name="AI Content Creator Pro",
                target_audience="Content creators and digital marketers",
                budget=5000.0,
                duration_hours=24,
            )

            print(f"Launched campaign: {campaign.name}")
            print(f"Channels: {[c.value for c in campaign.channels]}")
            print(f"Budget: ${campaign.budget:,.2f}")
            print(f"Content assets: {len(campaign.content_assets)}")

            # Wait a bit to see metrics update
            await asyncio.sleep(2)
            print(f"Current impressions: {campaign.metrics.get('impressions', 0):.0f}")

        except Exception as e:
            print(f"Blitz campaign test failed: {e}")

        # Test Relentless Optimization Loop
        print("\\n2. Testing Relentless Optimization Loop...")
        optimizer = RelentlessOptimizationLoop()

        try:
            # Create a sample campaign for optimization
            sample_campaign = MarketingCampaign(
                campaign_id="test_campaign",
                name="Test Optimization Campaign",
                campaign_type=CampaignType.LEAD_GENERATION,
                channels=[MarketingChannel.FACEBOOK, MarketingChannel.GOOGLE],
                target_audience="Business owners",
                budget=2000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=7),
            )

            # Initialize some metrics
            sample_campaign.metrics = {
                OptimizationMetric.CLICK_THROUGH_RATE: 0.015,
                OptimizationMetric.CONVERSION_RATE: 0.008,
                OptimizationMetric.ENGAGEMENT_RATE: 0.025,
            }

            await optimizer.start_optimization_loop(sample_campaign)

            # Wait to see some optimization activity
            await asyncio.sleep(3)

            print(f"Active tests: {len(optimizer.active_tests)}")
            print(f"Optimization history: {len(optimizer.optimization_history)}")

        except Exception as e:
            print(f"Optimization loop test failed: {e}")

        # Test Affiliate Manager
        print("\\n3. Testing Affiliate Manager...")
        affiliate_mgr = AffiliateManager()

        try:
            # Add some sample affiliate links
            sample_links = [
                AffiliateLink(
                    product_name="ConvertKit Email Marketing",
                    affiliate_url="https://convertkit.com?ref = affiliate123",
                    network=AffiliateNetwork.CUSTOM,
                    commission_rate=0.30,
                    product_category="email marketing",
                    target_keywords=["email", "marketing", "automation"],
                    conversion_rate=0.045,
                    earnings_per_click=0.85,
                ),
                AffiliateLink(
                    product_name="Canva Pro Design Tool",
                    affiliate_url="https://canva.com / pro?ref = affiliate456",
                    network=AffiliateNetwork.CUSTOM,
                    commission_rate=0.25,
                    product_category="design tools",
                    target_keywords=["design", "graphics", "templates"],
                    conversion_rate=0.032,
                    earnings_per_click=0.65,
                ),
            ]

            for link in sample_links:
                affiliate_mgr.add_affiliate_link(link)

            # Test link selection
            content_context = "Learn how to create stunning email marketing campaigns that convert"
            target_keywords = ["email", "marketing", "design"]

            selected_links = await affiliate_mgr.select_optimal_links(
                content_context, target_keywords, max_links=2
            )

            print(f"Selected {len(selected_links)} affiliate links:")
            for link in selected_links:
                print(f"  - {link.product_name} (relevance: {link.context_relevance:.3f})")

            # Test performance tracking
            await affiliate_mgr.track_link_performance(
                "custom_convertkit_email_marketing",
                clicks=100,
                conversions=4,
                revenue=340.0,
            )

            # Get performance analysis
            analysis = affiliate_mgr.analyze_link_performance()
            print(f"Total revenue: ${analysis['total_revenue']:.2f}")
            print(f"Average conversion rate: {analysis['average_conversion_rate']:.3f}")

        except Exception as e:
            print(f"Affiliate manager test failed: {e}")

        # Test Cross - Promotion Manager
        print("\\n4. Testing Cross - Promotion Manager...")
        cross_promo = CrossPromotionManager()

        try:
            # Add some promotion rules
            rules = [
                CrossPromotionRule(
                    source_content="email marketing",
                    target_content="Advanced Email Automation Course",
                    relevance_score=0.9,
                    promotion_type="recommendation",
                    context="Related educational content",
                ),
                CrossPromotionRule(
                    source_content="design",
                    target_content="Graphic Design Masterclass",
                    relevance_score=0.85,
                    promotion_type="link",
                    context="Skill development",
                ),
            ]

            for rule in rules:
                cross_promo.add_promotion_rule(rule)

            # Add a Right Perspective exception
            cross_promo.add_right_perspective_exception(
                "controversial_topic_123", "Content contains sensitive political views"
            )

            # Test promotion generation
            content_metadata = {
                "title": "How to Master Email Marketing in 2024",
                "description": "Complete guide to email marketing strategies",
                "tags": ["email", "marketing", "automation"],
            }

            promotions = await cross_promo.generate_cross_promotions(
                "email_marketing_guide_2024", content_metadata
            )

            print(f"Generated {len(promotions)} cross - promotions:")
            for promo in promotions:
                print(
                    f"  - {promo['type']}: {promo['target_content']} (score: {promo['relevance_score']})"
                )

            # Test performance analysis
            performance = cross_promo.analyze_promotion_performance()
            print(f"Active promotions: {performance['active_promotions']}")
            print(f"Right Perspective exceptions: {performance['right_perspective_exceptions']}")

            # Get optimization recommendations
            recommendations = cross_promo.optimize_promotion_rules()
            print(f"Optimization recommendations: {len(recommendations)}")

        except Exception as e:
            print(f"Cross - promotion manager test failed: {e}")

        print("\\nMarketing tools testing completed!")

    # Run the test
    asyncio.run(test_marketing_tools())
