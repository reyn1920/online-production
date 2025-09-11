# analytics.py - Dashboard Analytics and Reporting Module
import json
import random
from collections import defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

@dataclass


class AnalyticsEvent:
    """Represents an analytics event"""

    event_type: str
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    properties: Dict[str, Any] = None


    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class AnalyticsEngine:
    """Main analytics engine for dashboard insights"""


    def __init__(self):
        self.events: List[AnalyticsEvent] = []
        self.sessions: Dict[str, Dict] = {}
        self.user_metrics: Dict[str, Dict] = defaultdict(dict)

        # Initialize with sample data
        self._generate_sample_data()


    def _generate_sample_data(self):
        """Generate sample analytics data for demonstration"""
        now = datetime.now()

        # Generate events for the last 30 days
        for i in range(30):
            date = now - timedelta(days = i)
            daily_events = random.randint(50, 200)

            for j in range(daily_events):
                event_time = date.replace(
                    hour = random.randint(0, 23),
                        minute = random.randint(0, 59),
                        second = random.randint(0, 59),
                        )

                event_types = [
                    "page_view",
                        "api_call",
                        "user_action",
                        "error",
                        "performance_metric",
                        "feature_usage",
                        ]

                event = AnalyticsEvent(
                    event_type = random.choice(event_types),
                        timestamp = event_time,
                        user_id = f"user_{random.randint(1, 100)}",
                        session_id = f"session_{random.randint(1, 500)}",
                        properties={
                        "page": random.choice(
                            ["/dashboard", "/api / status", "/api / metrics", "/health"]
                        ),
                            "duration": random.randint(100, 5000),
                            "status": random.choice(["success", "error", "warning"]),
                            "browser": random.choice(
                            ["Chrome", "Firefox", "Safari", "Edge"]
                        ),
                            "device": random.choice(["desktop", "mobile", "tablet"]),
                            },
                        )
                self.events.append(event)


    def track_event(self, event: AnalyticsEvent):
        """Track a new analytics event"""
        self.events.append(event)


    def get_dashboard_overview(self, days: int = 7) -> Dict[str, Any]:
        """Get dashboard analytics overview"""
        cutoff_date = datetime.now() - timedelta(days = days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]

        total_events = len(recent_events)
        unique_users = len(set(e.user_id for e in recent_events if e.user_id))
        unique_sessions = len(set(e.session_id for e in recent_events if e.session_id))

        # Event type breakdown
        event_types = defaultdict(int)
        for event in recent_events:
            event_types[event.event_type] += 1

        # Daily activity
        daily_activity = defaultdict(int)
        for event in recent_events:
            day_key = event.timestamp.strftime("%Y-%m-%d")
            daily_activity[day_key] += 1

        # Top pages
        page_views = defaultdict(int)
        for event in recent_events:
            if event.properties and "page" in event.properties:
                page_views[event.properties["page"]] += 1

        return {
            "period": f"Last {days} days",
                "total_events": total_events,
                "unique_users": unique_users,
                "unique_sessions": unique_sessions,
                "avg_events_per_user": round(total_events / max(unique_users, 1), 2),
                "event_types": dict(event_types),
                "daily_activity": dict(daily_activity),
                "top_pages": dict(
                sorted(page_views.items(), key = lambda x: x[1], reverse = True)[:10]
            ),
                }


    def get_performance_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get performance analytics"""
        cutoff_date = datetime.now() - timedelta(days = days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]

        # Response times
        response_times = []
        error_count = 0
        success_count = 0

        for event in recent_events:
            if event.properties:
                if "duration" in event.properties:
                    response_times.append(event.properties["duration"])

                status = event.properties.get("status", "unknown")
                if status == "error":
                    error_count += 1
                elif status == "success":
                    success_count += 1

        avg_response_time = (
            sum(response_times) / len(response_times) if response_times else 0
        )
        error_rate = (error_count / max(error_count + success_count, 1)) * 100

        return {
            "avg_response_time_ms": round(avg_response_time, 2),
                "error_rate_percent": round(error_rate, 2),
                "total_requests": len(response_times),
                "errors": error_count,
                "successes": success_count,
                "uptime_percent": round(100 - error_rate, 2),
                }


    def get_user_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get user behavior analytics"""
        cutoff_date = datetime.now() - timedelta(days = days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]

        # Device breakdown
        devices = defaultdict(int)
        browsers = defaultdict(int)

        for event in recent_events:
            if event.properties:
                if "device" in event.properties:
                    devices[event.properties["device"]] += 1
                if "browser" in event.properties:
                    browsers[event.properties["browser"]] += 1

        # User activity patterns
        hourly_activity = defaultdict(int)
        for event in recent_events:
            hour = event.timestamp.hour
            hourly_activity[hour] += 1

        return {
            "device_breakdown": dict(devices),
                "browser_breakdown": dict(browsers),
                "hourly_activity": dict(hourly_activity),
                "peak_hour": (
                max(hourly_activity.items(), key = lambda x: x[1])[0]
                if hourly_activity
                else 0
            ),
                }


    def get_feature_usage(self, days: int = 7) -> Dict[str, Any]:
        """Get feature usage analytics"""
        cutoff_date = datetime.now() - timedelta(days = days)
        recent_events = [
            e
            for e in self.events
            if e.timestamp >= cutoff_date and e.event_type == "feature_usage"
        ]

        feature_usage = defaultdict(int)
        for event in recent_events:
            if event.properties and "feature" in event.properties:
                feature_usage[event.properties["feature"]] += 1

        return {
            "feature_usage": dict(
                sorted(feature_usage.items(), key = lambda x: x[1], reverse = True)
            ),
                "total_feature_interactions": sum(feature_usage.values()),
                }


    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get real - time statistics"""
        now = datetime.now()
        last_hour = now - timedelta(hours = 1)
        last_minute = now - timedelta(minutes = 1)

        recent_events = [e for e in self.events if e.timestamp >= last_hour]
        very_recent_events = [e for e in self.events if e.timestamp >= last_minute]

        return {
            "events_last_hour": len(recent_events),
                "events_last_minute": len(very_recent_events),
                "active_users_estimate": len(
                set(e.user_id for e in recent_events if e.user_id)
            ),
                "current_load": (
                "low"
                if len(very_recent_events) < 10
                else "medium" if len(very_recent_events) < 50 else "high"
            ),
                }


    def generate_report(self, days: int = 7) -> Dict[str, Any]:
        """Generate comprehensive analytics report"""
        return {
            "generated_at": datetime.now().isoformat(),
                "period": f"Last {days} days",
                "overview": self.get_dashboard_overview(days),
                "performance": self.get_performance_metrics(days),
                "users": self.get_user_analytics(days),
                "features": self.get_feature_usage(days),
                "real_time": self.get_real_time_stats(),
                }


    def export_data(self, format: str = "json", days: int = 30) -> str:
        """Export analytics data in specified format"""
        cutoff_date = datetime.now() - timedelta(days = days)
        recent_events = [e for e in self.events if e.timestamp >= cutoff_date]

        if format.lower() == "json":
            data = []
            for event in recent_events:
                event_dict = asdict(event)
                event_dict["timestamp"] = event.timestamp.isoformat()
                data.append(event_dict)
            return json.dumps(data, indent = 2)

        elif format.lower() == "csv":
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            writer.writerow(
                ["timestamp", "event_type", "user_id", "session_id", "properties"]
            )

            # Write data
            for event in recent_events:
                writer.writerow(
                    [
                        event.timestamp.isoformat(),
                            event.event_type,
                            event.user_id or "",
                            event.session_id or "",
                            json.dumps(event.properties or {}),
                            ]
                )

            return output.getvalue()

        else:
            raise ValueError(f"Unsupported format: {format}")

# Global analytics instance
analytics_engine = AnalyticsEngine()

# Utility functions for easy access


def track_page_view(page: str, user_id: str = None, session_id: str = None, **kwargs):
    """Track a page view event"""
    event = AnalyticsEvent(
        event_type="page_view",
            timestamp = datetime.now(),
            user_id = user_id,
            session_id = session_id,
            properties={"page": page, **kwargs},
            )
    analytics_engine.track_event(event)


def track_api_call(
    endpoint: str, method: str, status_code: int, duration_ms: int, **kwargs
):
    """Track an API call event"""
    event = AnalyticsEvent(
        event_type="api_call",
            timestamp = datetime.now(),
            properties={
            "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "duration": duration_ms,
                "status": "success" if 200 <= status_code < 400 else "error",
                **kwargs,
                },
            )
    analytics_engine.track_event(event)


def track_user_action(
    action: str, user_id: str = None, session_id: str = None, **kwargs
):
    """Track a user action event"""
    event = AnalyticsEvent(
        event_type="user_action",
            timestamp = datetime.now(),
            user_id = user_id,
            session_id = session_id,
            properties={"action": action, **kwargs},
            )
    analytics_engine.track_event(event)


def track_feature_usage(feature: str, user_id: str = None, **kwargs):
    """Track feature usage event"""
    event = AnalyticsEvent(
        event_type="feature_usage",
            timestamp = datetime.now(),
            user_id = user_id,
            properties={"feature": feature, **kwargs},
            )
    analytics_engine.track_event(event)
