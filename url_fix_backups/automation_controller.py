#!/usr / bin / env python3
""""""
Automation Controller - Master Control System

This module provides centralized control and monitoring for all automation systems:
1. Content Automation Pipeline
2. RSS Intelligence Engine
3. Agent Task Management
4. Performance Monitoring
5. API Integration

Author: TRAE.AI System
Version: 1.0.0
""""""

import asyncio
import json
import sqlite3
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from utils.logger import get_logger

from breaking_news_watcher import RSSIntelligenceEngine

# Import automation components

from content_automation_pipeline import (ContentAutomationPipeline, ContentFormat,

# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     ContentPriority)

logger = get_logger(__name__)

@dataclass


class AutomationStatus:
    """System - wide automation status."""

    content_pipeline_running: bool
    rss_monitoring_active: bool
    total_opportunities: int
    active_projects: int
    completed_today: int
    error_count: int
    last_update: datetime
    uptime_hours: float


class AutomationController:
    """Master controller for all automation systems."""


    def __init__(self, config_path: str = "automation_config.json"):
        self.config_path = config_path
        self.config = self._load_config()

        # Initialize components
        self.content_pipeline = ContentAutomationPipeline()
        self.rss_engine = RSSIntelligenceEngine()

        # Control state
        self.running = False
        self.start_time = datetime.now()
        self.error_count = 0

        # Threading
        self.content_thread = None
        self.rss_thread = None
        self.monitor_thread = None

        # Performance tracking
        self.performance_db = "automation_performance.db"
        self._init_performance_tracking()

        # Flask API for integration
        self.api = Flask(__name__)
        CORS(self.api)
        self._setup_api_routes()

        logger.info("Automation Controller initialized")


    def _load_config(self) -> Dict[str, Any]:
        """Load automation configuration."""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            default_config = {
                "auto_start": True,
                    "content_pipeline_enabled": True,
                    "rss_monitoring_enabled": True,
                    "api_port": 8082,
                    "monitoring_interval": 60,  # seconds
                "max_daily_content": 20,
                    "error_threshold": 10,
                    "performance_retention_days": 30,
                    "notification_webhooks": [],
                    "quality_gates": {
                    "min_engagement_score": 0.4,
                        "max_error_rate": 0.1,
                        "min_success_rate": 0.8,
# BRACKET_SURGEON: disabled
#                         },
# BRACKET_SURGEON: disabled
#                     }

            with open(self.config_path, "w") as f:
                json.dump(default_config, f, indent = 2)

            return default_config


    def _init_performance_tracking(self):
        """Initialize performance tracking database."""
        conn = sqlite3.connect(self.performance_db)
        cursor = conn.cursor()

        # System metrics table
        cursor.execute(
            """"""
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    component TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metadata TEXT
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Error tracking table
        cursor.execute(
            """"""
            CREATE TABLE IF NOT EXISTS error_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    component TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT,
                    stack_trace TEXT,
                    resolved BOOLEAN DEFAULT FALSE
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Content production metrics
        cursor.execute(
            """"""
            CREATE TABLE IF NOT EXISTS content_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    content_type TEXT NOT NULL,
                    production_time_seconds REAL,
                    quality_score REAL,
                    engagement_prediction REAL,
                    success BOOLEAN DEFAULT TRUE,
                    project_id TEXT
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
        """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        conn.commit()
        conn.close()
        logger.info("Performance tracking database initialized")


    def start_automation(self):
        """Start all automation systems."""
        if self.running:
            logger.warning("Automation already running")
            return

        self.running = True
        self.start_time = datetime.now()
        self.error_count = 0

        logger.info("Starting automation systems...")

        try:
            # Start RSS monitoring
            if self.config["rss_monitoring_enabled"]:
                self.rss_thread = threading.Thread(
                    target = self._run_rss_monitoring, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                self.rss_thread.start()
                logger.info("RSS monitoring started")

            # Start content pipeline
            if self.config["content_pipeline_enabled"]:
                self.content_thread = threading.Thread(
                    target = self._run_content_pipeline, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                self.content_thread.start()
                logger.info("Content pipeline started")

            # Start performance monitoring
            self.monitor_thread = threading.Thread(
                target = self._run_performance_monitoring, daemon = True
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            self.monitor_thread.start()
            logger.info("Performance monitoring started")

            logger.info("All automation systems started successfully")

        except Exception as e:
            logger.error(f"Error starting automation: {e}")
            self.stop_automation()
            raise


    def stop_automation(self):
        """Stop all automation systems."""
        if not self.running:
            return

        logger.info("Stopping automation systems...")

        self.running = False

        # Stop components
        if hasattr(self.content_pipeline, "stop_automation_pipeline"):
            self.content_pipeline.stop_automation_pipeline()

        if hasattr(self.rss_engine, "stop_monitoring"):
            self.rss_engine.stop_monitoring()

        # Wait for threads to finish
        for thread in [self.content_thread, self.rss_thread, self.monitor_thread]:
            if thread and thread.is_alive():
                thread.join(timeout = 5)

        logger.info("Automation systems stopped")


    def _run_rss_monitoring(self):
        """Run RSS monitoring in background thread."""
        try:
            asyncio.run(self.rss_engine.run_continuous_monitoring())
        except Exception as e:
            logger.error(f"RSS monitoring error: {e}")
            self._log_error("rss_engine", "monitoring_error", str(e))
            self.error_count += 1


    def _run_content_pipeline(self):
        """Run content pipeline in background thread."""
        try:
            asyncio.run(self.content_pipeline.run_automation_pipeline())
        except Exception as e:
            logger.error(f"Content pipeline error: {e}")
            self._log_error("content_pipeline", "pipeline_error", str(e))
            self.error_count += 1


    def _run_performance_monitoring(self):
        """Run performance monitoring loop."""
        while self.running:
            try:
                self._collect_performance_metrics()
                time.sleep(self.config["monitoring_interval"])
            except Exception as e:
                logger.error(f"Performance monitoring error: {e}")
                self._log_error("monitor", "metrics_error", str(e))
                time.sleep(60)  # Wait longer on error


    def _collect_performance_metrics(self):
        """Collect and store performance metrics."""
        try:
            timestamp = datetime.now()

            # Get content pipeline metrics
            pipeline_status = self.content_pipeline.get_pipeline_status()

            # Store metrics
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()

            # System uptime
            if self.start_time:
                uptime_hours = (timestamp - self.start_time).total_seconds()/3600
                cursor.execute(
                    "INSERT INTO system_metrics (component,"
    metric_name,
    metric_value) VALUES (?, ?, ?)","
                        ("system", "uptime_hours", uptime_hours),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

            # Error count
            cursor.execute(
                "INSERT INTO system_metrics (component,"
    metric_name,
    metric_value) VALUES (?, ?, ?)","
                    ("system", "error_count", self.error_count),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            # Content pipeline metrics
            if "pending_opportunities" in pipeline_status:
                cursor.execute(
                    "INSERT INTO system_metrics (component,"
    metric_name,
    metric_value) VALUES (?, ?, ?)","
                        (
                        "content_pipeline",
                            "pending_opportunities",
                            pipeline_status["pending_opportunities"],
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

            if "recent_projects_24h" in pipeline_status:
                cursor.execute(
                    "INSERT INTO system_metrics (component,"
    metric_name,
    metric_value) VALUES (?, ?, ?)","
                        (
                        "content_pipeline",
                            "projects_24h",
                            pipeline_status["recent_projects_24h"],
# BRACKET_SURGEON: disabled
#                             ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")


    def _log_error(
        self, component: str, error_type: str, message: str, stack_trace: str = None
# BRACKET_SURGEON: disabled
#     ):
        """Log error to performance database."""
        try:
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()

            cursor.execute(
                """"""
                INSERT INTO error_log (component,
    error_type,
    error_message,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     stack_trace)
                VALUES (?, ?, ?, ?)
            ""","""
                (component, error_type, message, stack_trace),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error logging error: {e}")


    def get_automation_status(self) -> AutomationStatus:
        """Get comprehensive automation status."""
        try:
            # Get pipeline status
            pipeline_status = self.content_pipeline.get_pipeline_status()

            # Calculate uptime
            uptime_hours = 0
            if self.start_time:
                uptime_hours = (datetime.now() - self.start_time).total_seconds()/3600

            # Get today's completed projects
            conn = sqlite3.connect(self.content_pipeline.db_path)
            cursor = conn.cursor()

            cursor.execute(
                """"""
                SELECT COUNT(*) FROM content_projects
                WHERE status = 'completed'
                AND DATE(updated_at) = DATE('now')
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            completed_today = cursor.fetchone()[0]

            cursor.execute(
                """"""
                SELECT COUNT(*) FROM content_projects
                WHERE status IN ('planning', 'scripting', 'production')
            """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            active_projects = cursor.fetchone()[0]

            conn.close()

            return AutomationStatus(
                content_pipeline_running = pipeline_status.get("running", False),
                    rss_monitoring_active = hasattr(self.rss_engine, "running")
                and self.rss_engine.running,
                    total_opportunities = pipeline_status.get("pending_opportunities",
# BRACKET_SURGEON: disabled
#     0),
                    active_projects = active_projects,
                    completed_today = completed_today,
                    error_count = self.error_count,
                    last_update = datetime.now(),
                    uptime_hours = uptime_hours,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
            return AutomationStatus(
                content_pipeline_running = False,
                    rss_monitoring_active = False,
                    total_opportunities = 0,
                    active_projects = 0,
                    completed_today = 0,
                    error_count = self.error_count,
                    last_update = datetime.now(),
                    uptime_hours = 0,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )


    def _setup_api_routes(self):
        """Setup Flask API routes for automation control."""

        @self.api.route("/api / automation / status", methods=["GET"])


        def get_status():
            """Get automation status."""
            try:
                status = self.get_automation_status()
                return jsonify(asdict(status))
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.api.route("/api / automation / start", methods=["POST"])


        def start_automation_api():
            """Start automation systems."""
            try:
                if not self.running:
                    self.start_automation()
                    return jsonify({"message": "Automation started", "success": True})
                else:
                    return jsonify(
                        {"message": "Automation already running", "success": True}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
            except Exception as e:
                return jsonify({"error": str(e), "success": False}), 500

        @self.api.route("/api / automation / stop", methods=["POST"])


        def stop_automation_api():
            """Stop automation systems."""
            try:
                self.stop_automation()
                return jsonify({"message": "Automation stopped", "success": True})
            except Exception as e:
                return jsonify({"error": str(e), "success": False}), 500

        @self.api.route("/api / automation / content / opportunities", methods=["GET"])


        def get_content_opportunities():
            """Get current content opportunities."""
            try:
                conn = sqlite3.connect(self.content_pipeline.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    SELECT * FROM content_opportunities
                    WHERE status = 'pending'
                    ORDER BY priority DESC, estimated_engagement DESC
                    LIMIT 20
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                opportunities = []
                for row in results:
                    opp = dict(zip(columns, row))
                    # Parse JSON fields
                    if opp["formats"]:
                        opp["formats"] = json.loads(opp["formats"])
                    if opp["keywords"]:
                        opp["keywords"] = json.loads(opp["keywords"])
                    if opp["source_articles"]:
                        opp["source_articles"] = json.loads(opp["source_articles"])
                    if opp["metadata"]:
                        opp["metadata"] = json.loads(opp["metadata"])
                    opportunities.append(opp)

                conn.close()
                return jsonify(opportunities)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.api.route("/api / automation / content / projects", methods=["GET"])


        def get_content_projects():
            """Get current content projects."""
            try:
                conn = sqlite3.connect(self.content_pipeline.db_path)
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    SELECT * FROM content_projects
                    ORDER BY created_at DESC
                    LIMIT 50
                """"""
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]

                projects = []
                for row in results:
                    proj = dict(zip(columns, row))
                    # Parse JSON fields
                    if proj["assets"]:
                        proj["assets"] = json.loads(proj["assets"])
                    if proj["output_files"]:
                        proj["output_files"] = json.loads(proj["output_files"])
                    if proj["metadata"]:
                        proj["metadata"] = json.loads(proj["metadata"])
                    projects.append(proj)

                conn.close()
                return jsonify(projects)

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.api.route("/api / automation / content / generate", methods=["POST"])


        def trigger_content_generation():
            """Manually trigger content generation cycle."""
            try:
                data = request.get_json() or {}
                limit = data.get("limit", 3)

                # Run content generation cycle
                opportunities = self.content_pipeline.identify_content_opportunities()

                generated_projects = []
                for opportunity in opportunities[:limit]:
                    projects = self.content_pipeline.generate_content_from_opportunity(
                        opportunity
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    generated_projects.extend(projects)

                return jsonify(
                    {
                        "success": True,
                            "opportunities_found": len(opportunities),
                            "projects_generated": len(generated_projects),
                            "projects": [
                            {
                                "id": p.id,
                                    "title": p.title,
                                    "format": p.format.value,
                                    "status": p.status,
# BRACKET_SURGEON: disabled
#                                     }
                            for p in generated_projects
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         ],
# BRACKET_SURGEON: disabled
#                             }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            except Exception as e:
                return jsonify({"error": str(e), "success": False}), 500

        @self.api.route("/api / automation / metrics", methods=["GET"])


        def get_performance_metrics():
            """Get performance metrics."""
            try:
                days = request.args.get("days", 7, type = int)

                conn = sqlite3.connect(self.performance_db)
                cursor = conn.cursor()

                cursor.execute(
                    """"""
                    SELECT component, metric_name, AVG(metric_value) as avg_value,
                        COUNT(*) as sample_count
                    FROM system_metrics
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY component, metric_name
                    ORDER BY component, metric_name
                """.format("""
                    days
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                metrics = []
                for row in cursor.fetchall():
                    metrics.append(
                        {
                            "component": row[0],
                                "metric": row[1],
                                "average_value": row[2],
                                "sample_count": row[3],
# BRACKET_SURGEON: disabled
#                                 }
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                # Get recent errors
                cursor.execute(
                    """"""
                    SELECT component, error_type, COUNT(*) as error_count
                    FROM error_log
                    WHERE timestamp > datetime('now', '-{} days')
                    GROUP BY component, error_type
                    ORDER BY error_count DESC
                """.format("""
                    days
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

                errors = []
                for row in cursor.fetchall():
                    errors.append(
                        {"component": row[0], "error_type": row[1], "count": row[2]}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )

                conn.close()

                return jsonify(
                    {"metrics": metrics, "errors": errors, "period_days": days}
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

            except Exception as e:
                return jsonify({"error": str(e)}), 500


    def run_api_server(self, host="0.0.0.0", port = None):
        """Run the API server."""
        if port is None:
            port = self.config["api_port"]

        logger.info(f"Starting Automation API server on {host}:{port}")
        self.api.run(host = host, port = port, debug = False)


    def cleanup(self):
        """Cleanup resources."""
        self.stop_automation()

        # Clean old performance data
        try:
            retention_days = self.config["performance_retention_days"]
            conn = sqlite3.connect(self.performance_db)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM system_metrics WHERE timestamp < datetime('now', '-{} days')".format(
                    retention_days
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            cursor.execute(
                "DELETE FROM error_log WHERE timestamp < datetime('now', '-{} days') AND resolved = TRUE".format(
                    retention_days
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )

            conn.commit()
            conn.close()

            logger.info("Performance data cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point for automation controller."""

    import argparse

    parser = argparse.ArgumentParser(description="TRAE.AI Automation Controller")
    parser.add_argument(
        "--config", default="automation_config.json", help="Configuration file path"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )
    parser.add_argument("--api - only", action="store_true", help="Run API server only")
    parser.add_argument("--port", type = int, default = 8082, help="API server port")
    parser.add_argument("--host", default="0.0.0.0", help="API server host")

    args = parser.parse_args()

    # Create controller
    controller = AutomationController(args.config)

    try:
        if args.api_only:
            # Run API server only
            controller.run_api_server(host = args.host, port = args.port)
        else:
            # Start automation and API server
            if controller.config["auto_start"]:
                controller.start_automation()

            # Run API server (blocking)
            controller.run_api_server(host = args.host, port = args.port)

    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
    finally:
        controller.cleanup()
        logger.info("Automation Controller shutdown complete")

if __name__ == "__main__":
    main()