#!/usr/bin/env python3
"""
RouteLL Credit Monitoring and Alerting System
Provides real - time credit tracking, usage analytics, and automated alerts
"""

import json
import logging
import os
import sqlite3
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Dict, List, Optional


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class UsageMetric:
    """Usage metric data structure"""

    timestamp: datetime
    credits_used: int
    model_used: str
    response_time_ms: int
    success: bool
    user_id: Optional[str] = None
    request_type: Optional[str] = None


@dataclass
class Alert:
    """Alert data structure"""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_data: Optional[Dict] = None
    acknowledged: bool = False


class CreditMonitor:
    """Advanced credit monitoring and alerting system"""

    def __init__(self, config_path: str = None, db_path: str = None):
        """Initialize credit monitor"""
        self.config = self._load_config(config_path)
        self.db_path = (
            db_path or "/Users/thomasbrianreynolds/online production/data/routellm_usage.db"
        )
        self.logger = self._setup_logging()
        self.alert_handlers: List[Callable] = []
        self.monitoring_active = False
        self.monitor_thread = None

        # Initialize database
        self._init_database()

        # Load current usage state
        self.current_usage = self._load_current_usage()

        # Setup default alert handlers
        self._setup_default_alerts()

    def _load_config(self, config_path: str) -> Dict:
        """Load monitoring configuration"""
        if config_path is None:
            config_path = "/Users/thomasbrianreynolds/online production/config/routellm_config.json"

        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config if file not found
            return {
                "credit_system": {
                    "monthly_credits": 20000,
                    "warning_thresholds": {
                        "75_percent": 15000,
                        "90_percent": 18000,
                        "95_percent": 19000,
                    },
                },
                "monitoring": {
                    "credit_tracking": {
                        "daily_usage_limit": 2000,
                        "hourly_usage_limit": 200,
                        "update_frequency_seconds": 60,
                    }
                },
            }

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for monitor"""
        logger = logging.getLogger("routellm_monitor")
        logger.setLevel(logging.INFO)

        # Create logs directory
        log_dir = "/Users/thomasbrianreynolds/online production/logs"
        os.makedirs(log_dir, exist_ok=True)

        # File handler
        handler = logging.FileHandler(f"{log_dir}/routellm_monitor.log")
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        return logger

    def _init_database(self):
        """Initialize SQLite database for usage tracking"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create usage metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS usage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    credits_used INTEGER NOT NULL,
                    model_used TEXT NOT NULL,
                    response_time_ms INTEGER NOT NULL,
                    success BOOLEAN NOT NULL,
                    user_id TEXT,
                    request_type TEXT
            )
        """
        )

        # Create alerts table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metric_data TEXT,
                    acknowledged BOOLEAN DEFAULT FALSE
            )
        """
        )

        # Create daily summaries table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_summaries (
                date TEXT PRIMARY KEY,
                    total_credits_used INTEGER NOT NULL,
                    total_requests INTEGER NOT NULL,
                    avg_response_time_ms REAL NOT NULL,
                    success_rate REAL NOT NULL,
                    top_models TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()

    def _load_current_usage(self) -> Dict:
        """Load current usage statistics from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get today's usage
        today = datetime.now().date().isoformat()
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(credits_used), 0) as daily_credits,
                    COUNT(*) as daily_requests
            FROM usage_metrics
            WHERE DATE(timestamp) = ?
        """,
            (today,),
        )

        daily_result = cursor.fetchone()
        daily_credits, daily_requests = daily_result or (0, 0)

        # Get this hour's usage
        current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(credits_used), 0) as hourly_credits,
                    COUNT(*) as hourly_requests
            FROM usage_metrics
            WHERE timestamp >= ?
        """,
            (current_hour.isoformat(),),
        )

        hourly_result = cursor.fetchone()
        hourly_credits, hourly_requests = hourly_result or (0, 0)

        # Get monthly usage (current month)
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(credits_used), 0) as monthly_credits,
                    COUNT(*) as monthly_requests
            FROM usage_metrics
            WHERE timestamp >= ?
        """,
            (month_start.isoformat(),),
        )

        monthly_result = cursor.fetchone()
        monthly_credits, monthly_requests = monthly_result or (0, 0)

        conn.close()

        monthly_limit = self.config["credit_system"]["monthly_credits"]

        return {
            "daily_credits": daily_credits,
            "daily_requests": daily_requests,
            "hourly_credits": hourly_credits,
            "hourly_requests": hourly_requests,
            "monthly_credits": monthly_credits,
            "monthly_requests": monthly_requests,
            "monthly_limit": monthly_limit,
            "remaining_credits": monthly_limit - monthly_credits,
            "usage_percentage": (
                (monthly_credits / monthly_limit) * 100 if monthly_limit > 0 else 0
            ),
        }

    def record_usage(self, metric: UsageMetric):
        """Record a usage metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO usage_metrics
            (timestamp,
    credits_used,
    model_used,
    response_time_ms,
    success,
    user_id,
    request_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                metric.timestamp.isoformat(),
                metric.credits_used,
                metric.model_used,
                metric.response_time_ms,
                metric.success,
                metric.user_id,
                metric.request_type,
            ),
        )

        conn.commit()
        conn.close()

        # Update current usage
        self.current_usage = self._load_current_usage()

        # Check for alerts
        self._check_usage_alerts()

        self.logger.info(
            f"Recorded usage: {metric.credits_used} credits, model: {metric.model_used}"
        )

    def _check_usage_alerts(self):
        """Check current usage against thresholds and trigger alerts"""
        usage_pct = self.current_usage["usage_percentage"]
        monthly_credits = self.current_usage["monthly_credits"]
        daily_credits = self.current_usage["daily_credits"]
        hourly_credits = self.current_usage["hourly_credits"]

        thresholds = self.config["credit_system"]["warning_thresholds"]
        daily_limit = self.config["monitoring"]["credit_tracking"]["daily_usage_limit"]
        hourly_limit = self.config["monitoring"]["credit_tracking"]["hourly_usage_limit"]

        # Monthly usage alerts
        if usage_pct >= 95 and not self._recent_alert_exists("CRITICAL_USAGE_95"):
            self._trigger_alert(
                Alert(
                    level=AlertLevel.CRITICAL,
                    title="Critical: 95% Credit Usage Reached",
                    message=f"Monthly credit usage has reached {usage_pct:.1f}% ({monthly_credits}/{self.current_usage['monthly_limit']} credits). Immediate action required.",
                    timestamp=datetime.now(),
                    metric_data=self.current_usage,
                )
            )
        elif usage_pct >= 90 and not self._recent_alert_exists("WARNING_USAGE_90"):
            self._trigger_alert(
                Alert(
                    level=AlertLevel.WARNING,
                    title="Warning: 90% Credit Usage Reached",
                    message=f"Monthly credit usage has reached {usage_pct:.1f}% ({monthly_credits}/{self.current_usage['monthly_limit']} credits). Consider optimizing usage.",
                    timestamp=datetime.now(),
                    metric_data=self.current_usage,
                )
            )
        elif usage_pct >= 75 and not self._recent_alert_exists("INFO_USAGE_75"):
            self._trigger_alert(
                Alert(
                    level=AlertLevel.INFO,
                    title="Info: 75% Credit Usage Reached",
                    message=f"Monthly credit usage has reached {usage_pct:.1f}% ({monthly_credits}/{self.current_usage['monthly_limit']} credits).",
                    timestamp=datetime.now(),
                    metric_data=self.current_usage,
                )
            )

        # Daily usage alerts
        if daily_credits >= daily_limit and not self._recent_alert_exists("DAILY_LIMIT_REACHED"):
            self._trigger_alert(
                Alert(
                    level=AlertLevel.WARNING,
                    title="Daily Credit Limit Reached",
                    message=f"Daily credit usage has reached the limit: {daily_credits}/{daily_limit} credits.",
                    timestamp=datetime.now(),
                    metric_data={
                        "daily_usage": daily_credits,
                        "daily_limit": daily_limit,
                    },
                )
            )

        # Hourly usage alerts
        if hourly_credits >= hourly_limit and not self._recent_alert_exists("HOURLY_LIMIT_REACHED"):
            self._trigger_alert(
                Alert(
                    level=AlertLevel.WARNING,
                    title="Hourly Credit Limit Reached",
                    message=f"Hourly credit usage has reached the limit: {hourly_credits}/{hourly_limit} credits.",
                    timestamp=datetime.now(),
                    metric_data={
                        "hourly_usage": hourly_credits,
                        "hourly_limit": hourly_limit,
                    },
                )
            )

    def _recent_alert_exists(self, alert_type: str, hours: int = 1) -> bool:
        """Check if a similar alert was triggered recently"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute(
            """
            SELECT COUNT(*) FROM alerts
            WHERE title LIKE ? AND timestamp > ?
        """,
            (f"%{alert_type}%", cutoff_time.isoformat()),
        )

        count = cursor.fetchone()[0]
        conn.close()

        return count > 0

    def _trigger_alert(self, alert: Alert):
        """Trigger an alert through all registered handlers"""
        # Store alert in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO alerts (level, title, message, timestamp, metric_data)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                alert.level.value,
                alert.title,
                alert.message,
                alert.timestamp.isoformat(),
                json.dumps(alert.metric_data) if alert.metric_data else None,
            ),
        )

        conn.commit()
        conn.close()

        # Trigger all alert handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler failed: {str(e)}")

        self.logger.warning(f"Alert triggered: {alert.title} - {alert.message}")

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add a custom alert handler"""
        self.alert_handlers.append(handler)

    def _setup_default_alerts(self):
        """Setup default alert handlers"""

        # Console alert handler

        def console_alert_handler(alert: Alert):
            print(f"\\n🚨 ALERT [{alert.level.value.upper()}]: {alert.title}")
            print(f"📝 {alert.message}")
            print(f"⏰ {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\\n")

        self.add_alert_handler(console_alert_handler)

        # File alert handler

        def file_alert_handler(alert: Alert):
            alert_log_path = "/Users/thomasbrianreynolds/online production/logs/routellm_alerts.log"
            os.makedirs(os.path.dirname(alert_log_path), exist_ok=True)

            with open(alert_log_path, "a") as f:
                f.write(
                    f"[{alert.timestamp.isoformat()}] {alert.level.value.upper()}: {alert.title}\\n"
                )
                f.write(f"Message: {alert.message}\\n")
                if alert.metric_data:
                    f.write(f"Data: {json.dumps(alert.metric_data)}\\n")
                f.write("---\\n")

        self.add_alert_handler(file_alert_handler)

    def get_usage_summary(self, days: int = 7) -> Dict:
        """Get usage summary for the specified number of days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()

        # Get daily breakdown
        cursor.execute(
            """
            SELECT
                DATE(timestamp) as date,
                    SUM(credits_used) as credits,
                    COUNT(*) as requests,
                    AVG(response_time_ms) as avg_response_time,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0/COUNT(*) as success_rate
            FROM usage_metrics
            WHERE DATE(timestamp) >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        """,
            (start_date,),
        )

        daily_data = cursor.fetchall()

        # Get model usage breakdown
        cursor.execute(
            """
            SELECT
                model_used,
                    SUM(credits_used) as total_credits,
                    COUNT(*) as total_requests,
                    AVG(response_time_ms) as avg_response_time
            FROM usage_metrics
            WHERE DATE(timestamp) >= ?
            GROUP BY model_used
            ORDER BY total_credits DESC
        """,
            (start_date,),
        )

        model_data = cursor.fetchall()

        conn.close()

        return {
            "period_days": days,
            "current_usage": self.current_usage,
            "daily_breakdown": [
                {
                    "date": row[0],
                    "credits": row[1],
                    "requests": row[2],
                    "avg_response_time_ms": round(row[3], 2) if row[3] else 0,
                    "success_rate": round(row[4], 2) if row[4] else 0,
                }
                for row in daily_data
            ],
            "model_breakdown": [
                {
                    "model": row[0],
                    "total_credits": row[1],
                    "total_requests": row[2],
                    "avg_response_time_ms": round(row[3], 2) if row[3] else 0,
                }
                for row in model_data
            ],
        }

    def get_recent_alerts(self, hours: int = 24) -> List[Dict]:
        """Get recent alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_time = datetime.now() - timedelta(hours=hours)
        cursor.execute(
            """
            SELECT level, title, message, timestamp, acknowledged
            FROM alerts
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        """,
            (cutoff_time.isoformat(),),
        )

        alerts = cursor.fetchall()
        conn.close()

        return [
            {
                "level": row[0],
                "title": row[1],
                "message": row[2],
                "timestamp": row[3],
                "acknowledged": bool(row[4]),
            }
            for row in alerts
        ]

    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Credit monitoring started")

    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.logger.info("Credit monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        update_frequency = self.config["monitoring"]["credit_tracking"]["update_frequency_seconds"]

        while self.monitoring_active:
            try:
                # Update current usage
                self.current_usage = self._load_current_usage()

                # Check for alerts
                self._check_usage_alerts()

                # Generate daily summary if needed
                self._generate_daily_summary_if_needed()

                time.sleep(update_frequency)

            except Exception as e:
                self.logger.error(f"Monitoring loop error: {str(e)}")
                time.sleep(60)  # Wait longer on error

    def _generate_daily_summary_if_needed(self):
        """Generate daily summary if it doesn't exist for yesterday"""
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if summary already exists
        cursor.execute("SELECT COUNT(*) FROM daily_summaries WHERE date = ?", (yesterday,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            return

        # Generate summary for yesterday
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(credits_used), 0) as total_credits,
                    COUNT(*) as total_requests,
                    COALESCE(AVG(response_time_ms), 0) as avg_response_time,
                    COALESCE(SUM(CASE WHEN success THEN 1 ELSE 0 END) * 100.0/COUNT(*),
    0) as success_rate
            FROM usage_metrics
            WHERE DATE(timestamp) = ?
        """,
            (yesterday,),
        )

        summary_data = cursor.fetchone()

        # Get top models
        cursor.execute(
            """
            SELECT model_used, COUNT(*) as usage_count
            FROM usage_metrics
            WHERE DATE(timestamp) = ?
            GROUP BY model_used
            ORDER BY usage_count DESC
            LIMIT 5
        """,
            (yesterday,),
        )

        top_models = [f"{row[0]}({row[1]})" for row in cursor.fetchall()]

        # Insert summary
        cursor.execute(
            """
            INSERT INTO daily_summaries
            (date,
    total_credits_used,
    total_requests,
    avg_response_time_ms,
    success_rate,
    top_models)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                yesterday,
                summary_data[0],
                summary_data[1],
                summary_data[2],
                summary_data[3],
                json.dumps(top_models),
            ),
        )

        conn.commit()
        conn.close()

        self.logger.info(f"Generated daily summary for {yesterday}")


# Example usage
if __name__ == "__main__":
    # Initialize monitor
    monitor = CreditMonitor()

    # Start monitoring
    monitor.start_monitoring()

    # Simulate some usage
    test_metric = UsageMetric(
        timestamp=datetime.now(),
        credits_used=10,
        model_used="route - llm",
        response_time_ms=1500,
        success=True,
        user_id="test_user",
        request_type="chat_completion",
    )

    monitor.record_usage(test_metric)

    # Get usage summary
    summary = monitor.get_usage_summary(days=7)
    print(f"Usage Summary: {json.dumps(summary, indent = 2)}")

    # Get recent alerts
    alerts = monitor.get_recent_alerts(hours=24)
    print(f"Recent Alerts: {json.dumps(alerts, indent = 2)}")

    # Keep running for a bit
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass
    finally:
        monitor.stop_monitoring()
