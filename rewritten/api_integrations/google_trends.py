import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from pytrends.request import TrendReq

from .base_api import APIError, BaseAPI, RateLimitConfig

logger = logging.getLogger(__name__)


class GoogleTrendsAPI(BaseAPI):
    """Google Trends API integration using pytrends"""

    def __init__(self, hl: str = "en - US", tz: int = 360):
        # More conservative rate limiting for Google Trends
        rate_config = RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            burst_limit=3,
# BRACKET_SURGEON: disabled
#         )
        super().__init__(rate_config)
        self.hl = hl  # Language
        self.tz = tz  # Timezone offset
        self.pytrends = None

    async def _init_pytrends(self):
        """Initialize pytrends client"""
        if not self.pytrends:
            try:
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                self.pytrends = await loop.run_in_executor(
                    None, lambda: TrendReq(hl=self.hl, tz=self.tz, timeout=(10, 25))
# BRACKET_SURGEON: disabled
#                 )
            except Exception as e:
                raise APIError(f"Failed to initialize Google Trends client: {e}")

    async def health_check(self) -> bool:
        """Check if Google Trends is accessible"""
        try:
            await self._init_pytrends()
            # Test with a simple query
            await self.get_interest_over_time(["python"], timeframe="today 7 - d")
            return True
        except Exception as e:
            logger.error(f"Google Trends health check failed: {e}")
            return False

    async def get_quota_status(self) -> Dict[str, Any]:
        """Get current quota status"""
        return {
            "service": "Google Trends (pytrends)",
            "daily_limit": self.rate_limiter.config.requests_per_day,
            "daily_used": self.rate_limiter.daily_count,
            "hourly_limit": self.rate_limiter.config.requests_per_hour,
            "hourly_used": self.rate_limiter.hourly_count,
            "tokens_available": int(self.rate_limiter.tokens),
# BRACKET_SURGEON: disabled
#         }

    async def get_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = "today 3 - m",
        geo: str = "",
        category: int = 0,
    ) -> Dict[str, Any]:
        """Get interest over time for keywords"""
        await self.rate_limiter.acquire()
        await self._init_pytrends()

        try:
            loop = asyncio.get_event_loop()

            # Build payload
            await loop.run_in_executor(
                None,
                lambda: self.pytrends.build_payload(
                    keywords, cat=category, timeframe=timeframe, geo=geo
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#             )

            # Get interest over time data
            interest_df = await loop.run_in_executor(None, self.pytrends.interest_over_time)

            if interest_df.empty:
                return {"keywords": keywords, "data": [], "timeframe": timeframe}

            # Convert to JSON - serializable format
            data = []
            for index, row in interest_df.iterrows():
                data_point = {"date": index.isoformat()}
                for keyword in keywords:
                    if keyword in row:
                        data_point[keyword] = int(row[keyword])
                data.append(data_point)

            return {
                "keywords": keywords,
                "data": data,
                "timeframe": timeframe,
                "geo": geo,
                "category": category,
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            raise APIError(f"Failed to get interest over time: {e}")

    async def get_trending_searches(self, pn: str = "united_states") -> List[Dict[str, Any]]:
        """Get trending searches for a country"""
        await self.rate_limiter.acquire()
        await self._init_pytrends()

        try:
            loop = asyncio.get_event_loop()
            trending_df = await loop.run_in_executor(
                None, lambda: self.pytrends.trending_searches(pn=pn)
# BRACKET_SURGEON: disabled
#             )

            if trending_df.empty:
                return []

            # Convert to list of dictionaries
            trending_list = []
            for idx, search_term in enumerate(trending_df[0].tolist()):
                trending_list.append({"rank": idx + 1, "search_term": search_term, "country": pn})

            return trending_list

        except Exception as e:
            raise APIError(f"Failed to get trending searches: {e}")

    async def get_related_topics(
        self, keywords: List[str], timeframe: str = "today 3 - m", geo: str = ""
    ) -> Dict[str, Any]:
        """Get related topics for keywords"""
        await self.rate_limiter.acquire()
        await self._init_pytrends()

        try:
            loop = asyncio.get_event_loop()

            # Build payload
            await loop.run_in_executor(
                None,
                lambda: self.pytrends.build_payload(keywords, timeframe=timeframe, geo=geo),
# BRACKET_SURGEON: disabled
#             )

            # Get related topics
            related_topics = await loop.run_in_executor(None, self.pytrends.related_topics)

            result = {"keywords": keywords, "related_topics": {}}

            for keyword in keywords:
                if keyword in related_topics:
                    keyword_topics = {"rising": [], "top": []}

                    # Process rising topics
                    if (
                        "rising" in related_topics[keyword]
                        and related_topics[keyword]["rising"] is not None
# BRACKET_SURGEON: disabled
#                     ):
                        rising_df = related_topics[keyword]["rising"]
                        keyword_topics["rising"] = [
                            {
                                "topic": row["topic_title"],
                                "value": (row["value"] if pd.notna(row["value"]) else "Breakout"),
# BRACKET_SURGEON: disabled
#                             }
                            for _, row in rising_df.iterrows()
# BRACKET_SURGEON: disabled
#                         ]

                    # Process top topics
                    if (
                        "top" in related_topics[keyword]
                        and related_topics[keyword]["top"] is not None
# BRACKET_SURGEON: disabled
#                     ):
                        top_df = related_topics[keyword]["top"]
                        keyword_topics["top"] = [
                            {
                                "topic": row["topic_title"],
                                "value": (int(row["value"]) if pd.notna(row["value"]) else 0),
# BRACKET_SURGEON: disabled
#                             }
                            for _, row in top_df.iterrows()
# BRACKET_SURGEON: disabled
#                         ]

                    result["related_topics"][keyword] = keyword_topics

            return result

        except Exception as e:
            raise APIError(f"Failed to get related topics: {e}")

    async def get_related_queries(
        self, keywords: List[str], timeframe: str = "today 3 - m", geo: str = ""
    ) -> Dict[str, Any]:
        """Get related queries for keywords"""
        await self.rate_limiter.acquire()
        await self._init_pytrends()

        try:
            loop = asyncio.get_event_loop()

            # Build payload
            await loop.run_in_executor(
                None,
                lambda: self.pytrends.build_payload(keywords, timeframe=timeframe, geo=geo),
# BRACKET_SURGEON: disabled
#             )

            # Get related queries
            related_queries = await loop.run_in_executor(None, self.pytrends.related_queries)

            result = {"keywords": keywords, "related_queries": {}}

            for keyword in keywords:
                if keyword in related_queries:
                    keyword_queries = {"rising": [], "top": []}

                    # Process rising queries
                    if (
                        "rising" in related_queries[keyword]
                        and related_queries[keyword]["rising"] is not None
# BRACKET_SURGEON: disabled
#                     ):
                        rising_df = related_queries[keyword]["rising"]
                        keyword_queries["rising"] = [
                            {
                                "query": row["query"],
                                "value": (row["value"] if pd.notna(row["value"]) else "Breakout"),
# BRACKET_SURGEON: disabled
#                             }
                            for _, row in rising_df.iterrows()
# BRACKET_SURGEON: disabled
#                         ]

                    # Process top queries
                    if (
                        "top" in related_queries[keyword]
                        and related_queries[keyword]["top"] is not None
# BRACKET_SURGEON: disabled
#                     ):
                        top_df = related_queries[keyword]["top"]
                        keyword_queries["top"] = [
                            {
                                "query": row["query"],
                                "value": (int(row["value"]) if pd.notna(row["value"]) else 0),
# BRACKET_SURGEON: disabled
#                             }
                            for _, row in top_df.iterrows()
# BRACKET_SURGEON: disabled
#                         ]

                    result["related_queries"][keyword] = keyword_queries

            return result

        except Exception as e:
            raise APIError(f"Failed to get related queries: {e}")

    async def analyze_keyword_trends(
        self, keywords: List[str], timeframe: str = "today 3 - m"
    ) -> Dict[str, Any]:
        """Comprehensive keyword trend analysis"""
        try:
            # Get all trend data concurrently
            interest_task = self.get_interest_over_time(keywords, timeframe)
            topics_task = self.get_related_topics(keywords, timeframe)
            queries_task = self.get_related_queries(keywords, timeframe)

            interest_data, topics_data, queries_data = await asyncio.gather(
                interest_task, topics_task, queries_task
# BRACKET_SURGEON: disabled
#             )

            # Calculate trend metrics
            trend_metrics = self._calculate_trend_metrics(interest_data["data"], keywords)

            return {
                "keywords": keywords,
                "timeframe": timeframe,
                "interest_over_time": interest_data,
                "related_topics": topics_data,
                "related_queries": queries_data,
                "trend_metrics": trend_metrics,
                "analysis_timestamp": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#             }

        except Exception as e:
            raise APIError(f"Failed to analyze keyword trends: {e}")

    def _calculate_trend_metrics(self, data: List[Dict], keywords: List[str]) -> Dict[str, Any]:
        """Calculate trend velocity and momentum metrics"""
        if not data or len(data) < 2:
            return {
                keyword: {"velocity": 0, "momentum": 0, "peak_value": 0} for keyword in keywords
# BRACKET_SURGEON: disabled
#             }

        metrics = {}

        for keyword in keywords:
            values = [point.get(keyword, 0) for point in data if keyword in point]

            if len(values) < 2:
                metrics[keyword] = {"velocity": 0, "momentum": 0, "peak_value": 0}
                continue

            # Calculate velocity (rate of change)
            recent_avg = sum(values[-7:]) / min(7, len(values[-7:]))
            older_avg = sum(values[:7]) / min(7, len(values[:7]))
            velocity = ((recent_avg - older_avg) / max(older_avg, 1)) * 100

            # Calculate momentum (acceleration)
            if len(values) >= 4:
                mid_point = len(values) // 2
                first_half_avg = sum(values[:mid_point]) / mid_point
                second_half_avg = sum(values[mid_point:]) / (len(values) - mid_point)
                momentum = ((second_half_avg - first_half_avg) / max(first_half_avg, 1)) * 100
            else:
                momentum = 0

            metrics[keyword] = {
                "velocity": round(velocity, 2),
                "momentum": round(momentum, 2),
                "peak_value": max(values),
                "current_value": values[-1] if values else 0,
                "average_value": round(sum(values) / len(values), 2),
# BRACKET_SURGEON: disabled
#             }

        return metrics