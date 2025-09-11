#!/usr / bin / env python3
"""
API Monetization System
Provides API key management, usage tracking, rate limiting, and billing
"""

import json
import logging
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from contextlib import contextmanager

from flask import Flask, jsonify, request
from flask_cors import CORS

logging.basicConfig(level = logging.INFO)
logger = logging.getLogger(__name__)


class APIMonetization:


    def __init__(self, db_path: str = "data / api_monetization.db"):
        self.db_path = db_path
        self.app = Flask(__name__)
        CORS(self.app)
        self._db_lock = threading.Lock()
        self._init_database()
        self._setup_routes()

    @contextmanager


    def _get_db_connection(self, timeout = 30.0):
        """Get database connection with proper error handling and WAL mode"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout = timeout)
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode = WAL')
            conn.execute('PRAGMA synchronous = NORMAL')
            conn.execute('PRAGMA cache_size = 10000')
            conn.execute('PRAGMA temp_store = memory')
            yield conn
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower():
                logger.warning(f"Database lock detected, retrying: {e}")
                time.sleep(0.1)
                # Retry once with shorter timeout
                if conn:
                    conn.close()
                conn = sqlite3.connect(self.db_path, timeout = 5.0)
                conn.execute('PRAGMA journal_mode = WAL')
                yield conn
            else:
                raise
        finally:
            if conn:
                conn.close()


    def _init_database(self):
        """Initialize database tables for API monetization"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # API keys table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_keys (
                    api_key TEXT PRIMARY KEY,
                        customer_email TEXT NOT NULL,
                        plan_type TEXT DEFAULT 'basic',
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            # API usage tracking table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS api_usage (
                    id TEXT PRIMARY KEY,
                        api_key TEXT NOT NULL,
                        endpoint TEXT NOT NULL,
                        requests_count INTEGER DEFAULT 1,
                        usage_date TEXT NOT NULL,
                        customer_id TEXT NOT NULL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (api_key) REFERENCES api_keys (api_key)
                )
            """
            )

            # Billing records table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS billing_records (
                    id TEXT PRIMARY KEY,
                        api_key TEXT NOT NULL,
                        billing_period TEXT NOT NULL,
                        total_requests INTEGER DEFAULT 0,
                        base_cost REAL DEFAULT 0,
                        overage_cost REAL DEFAULT 0,
                        total_cost REAL DEFAULT 0,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (api_key) REFERENCES api_keys (api_key)
                )
            """
            )

            conn.commit()
        logger.info("API monetization database initialized")


    def _setup_routes(self):
        """Setup Flask routes for API monetization"""

        @self.app.route("/api / monetization / generate - key", methods=["POST"])


        def generate_api_key():
            """Generate a new API key for a customer"""
            try:
                data = request.get_json()
                customer_email = data.get("customer_email")
                plan_type = data.get("plan_type", "basic")

                if not customer_email:
                    return (
                        jsonify({"success": False, "error": "Customer email required"}),
                            400,
                            )

                # Generate unique API key
                api_key = f"ak_{int(time.time())}_{hash(customer_email) % 10000}"

                # Store API key
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO api_keys
                        (api_key, customer_email, plan_type, status, created_at)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            api_key,
                                customer_email,
                                plan_type,
                                "active",
                                datetime.now().isoformat(),
                                ),
                            )

                    conn.commit()

                return jsonify(
                    {
                        "success": True,
                            "api_key": api_key,
                            "plan_type": plan_type,
                            "rate_limits": self._get_rate_limits(plan_type),
                            }
                )

            except Exception as e:
                logger.error(f"Error generating API key: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / monetization / validate - key", methods=["POST"])


        def validate_api_key():
            """Validate an API key and check rate limits"""
            try:
                data = request.get_json()
                api_key = data.get("api_key")
                endpoint = data.get("endpoint", "general")

                if not api_key:
                    return jsonify({"success": False, "error": "API key required"}), 400

                # Check if API key exists and is active
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute(
                        """
                        SELECT customer_email, plan_type, status FROM api_keys
                        WHERE api_key = ?
                    """,
                        (api_key,),
                            )

                    result = cursor.fetchone()
                    if not result:
                        return jsonify({"success": False, "error": "Invalid API key"}), 401

                    customer_email, plan_type, status = result

                    if status != "active":
                        return (
                            jsonify({"success": False, "error": "API key is inactive"}),
                                401,
                                )

                # Check rate limits
                rate_limit_ok, remaining_requests = self._check_rate_limit(
                    api_key, endpoint, plan_type
                )

                if not rate_limit_ok:
                    return (
                        jsonify(
                            {
                                "success": False,
                                    "error": "Rate limit exceeded",
                                    "remaining_requests": 0,
                                    }
                        ),
                            429,
                            )

                # Record API usage
                self._record_api_usage(api_key, endpoint, customer_email)

                return jsonify(
                    {
                        "success": True,
                            "customer_email": customer_email,
                            "plan_type": plan_type,
                            "remaining_requests": remaining_requests,
                            }
                )

            except Exception as e:
                logger.error(f"Error validating API key: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / monetization / usage/<api_key>", methods=["GET"])


        def get_api_usage(api_key):
            """Get API usage statistics for a key"""
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    # Get current month usage
                    current_month = datetime.now().strftime("%Y-%m")
                    cursor.execute(
                        """
                        SELECT endpoint, SUM(requests_count) as total_requests
                        FROM api_usage
                        WHERE api_key = ? AND strftime('%Y-%m', usage_date) = ?
                        GROUP BY endpoint
                    """,
                        (api_key, current_month),
                            )

                    usage_by_endpoint = {}
                    total_requests = 0

                    for row in cursor.fetchall():
                        endpoint, requests = row
                        usage_by_endpoint[endpoint] = requests
                        total_requests += requests

                    # Get plan info
                    cursor.execute(
                        """
                        SELECT plan_type FROM api_keys WHERE api_key = ?
                    """,
                        (api_key,),
                            )

                    result = cursor.fetchone()
                    plan_type = result[0] if result else "basic"

                rate_limits = self._get_rate_limits(plan_type)

                return jsonify(
                    {
                        "success": True,
                            "api_key": api_key,
                            "plan_type": plan_type,
                            "current_month": current_month,
                            "total_requests": total_requests,
                            "usage_by_endpoint": usage_by_endpoint,
                            "rate_limits": rate_limits,
                            "remaining_requests": max(
                            0, rate_limits["monthly_limit"] - total_requests
                        ),
                            }
                )

            except Exception as e:
                logger.error(f"Error getting API usage: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / monetization / billing/<api_key>", methods=["GET"])


        def get_api_billing(api_key):
            """Calculate billing for API usage"""
            try:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    # Get current month usage
                    current_month = datetime.now().strftime("%Y-%m")
                    cursor.execute(
                        """
                        SELECT SUM(requests_count) as total_requests
                        FROM api_usage
                        WHERE api_key = ? AND strftime('%Y-%m', usage_date) = ?
                    """,
                        (api_key, current_month),
                            )

                    result = cursor.fetchone()
                    total_requests = result[0] if result and result[0] else 0

                    # Get plan info
                    cursor.execute(
                        """
                        SELECT plan_type, customer_email FROM api_keys WHERE api_key = ?
                    """,
                        (api_key,),
                            )

                    result = cursor.fetchone()
                    if not result:
                        return (
                            jsonify({"success": False, "error": "API key not found"}),
                                404,
                                )

                    plan_type, customer_email = result

                # Calculate billing
                billing_info = self._calculate_api_billing(plan_type, total_requests)
                billing_info.update(
                    {
                        "api_key": api_key,
                            "customer_email": customer_email,
                            "billing_period": current_month,
                            "total_requests": total_requests,
                            }
                )

                return jsonify({"success": True, "billing": billing_info})

            except Exception as e:
                logger.error(f"Error calculating API billing: {e}")
                return jsonify({"success": False, "error": str(e)}), 500

        @self.app.route("/api / monetization / plans", methods=["GET"])


        def get_plans():
            """Get available API plans"""
            plans = {
                "basic": {
                    "name": "Basic API Plan",
                        "price": 9.99,
                        "requests_per_minute": 60,
                        "requests_per_hour": 1000,
                        "monthly_limit": 10000,
                        "cost_per_request": 0.001,
                        "features": [
                        "Basic API Access",
                            "Email Support",
                            "Standard Rate Limits",
                            ],
                        },
                    "pro": {
                    "name": "Pro API Plan",
                        "price": 29.99,
                        "requests_per_minute": 300,
                        "requests_per_hour": 10000,
                        "monthly_limit": 100000,
                        "cost_per_request": 0.0008,
                        "features": [
                        "Enhanced API Access",
                            "Priority Support",
                            "Higher Rate Limits",
                            "Analytics Dashboard",
                            ],
                        },
                    "enterprise": {
                    "name": "Enterprise API Plan",
                        "price": 99.99,
                        "requests_per_minute": 1000,
                        "requests_per_hour": 50000,
                        "monthly_limit": 1000000,
                        "cost_per_request": 0.0005,
                        "features": [
                        "Full API Access",
                            "24 / 7 Support",
                            "Custom Rate Limits",
                            "Advanced Analytics",
                            "Dedicated Account Manager",
                            ],
                        },
                    }

            return jsonify({"success": True, "plans": plans})


    def _get_rate_limits(self, plan_type):
        """Get rate limits for a plan type"""
        limits = {
            "basic": {
                "requests_per_minute": 60,
                    "requests_per_hour": 1000,
                    "monthly_limit": 10000,
                    "cost_per_request": 0.001,
                    },
                "pro": {
                "requests_per_minute": 300,
                    "requests_per_hour": 10000,
                    "monthly_limit": 100000,
                    "cost_per_request": 0.0008,
                    },
                "enterprise": {
                "requests_per_minute": 1000,
                    "requests_per_hour": 50000,
                    "monthly_limit": 1000000,
                    "cost_per_request": 0.0005,
                    },
                }
        return limits.get(plan_type, limits["basic"])


    def _check_rate_limit(self, api_key, endpoint, plan_type):
        """Check if API key has exceeded rate limits"""
        try:
            limits = self._get_rate_limits(plan_type)

            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                # Check monthly limit
                current_month = datetime.now().strftime("%Y-%m")
                cursor.execute(
                    """
                    SELECT SUM(requests_count) as total_requests
                    FROM api_usage
                    WHERE api_key = ? AND strftime('%Y-%m', usage_date) = ?
                """,
                    (api_key, current_month),
                        )

                result = cursor.fetchone()
                monthly_usage = result[0] if result and result[0] else 0

                if monthly_usage >= limits["monthly_limit"]:
                    return False, 0

                # Check hourly limit (aggregate across all endpoints for this API key)
                current_hour = datetime.now().strftime("%Y-%m-%d %H")
                cursor.execute(
                    """
                    SELECT SUM(requests_count) as hourly_requests
                    FROM api_usage
                    WHERE api_key = ? AND strftime('%Y-%m-%d %H', created_at) = ?
                """,
                    (api_key, current_hour),
                        )

                result = cursor.fetchone()
                hourly_usage = result[0] if result and result[0] else 0

                if hourly_usage >= limits["requests_per_hour"]:
                    return False, limits["monthly_limit"] - monthly_usage

                # Check per - minute limit (aggregate across all endpoints for this API key)
                current_minute = datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute(
                    """
                    SELECT SUM(requests_count) as minute_requests
                    FROM api_usage
                    WHERE api_key = ? AND strftime('%Y-%m-%d %H:%M', created_at) = ?
                """,
                    (api_key, current_minute),
                        )

                result = cursor.fetchone()
                minute_usage = result[0] if result and result[0] else 0

                if minute_usage >= limits["requests_per_minute"]:
                    return False, limits["monthly_limit"] - monthly_usage

                return True, limits["monthly_limit"] - monthly_usage

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return False, 0


    def _record_api_usage(self, api_key, endpoint, customer_email):
        """Record API usage for billing and rate limiting"""
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()

                current_time = datetime.now()
                usage_date = current_time.date().isoformat()
                # Generate more unique ID to avoid UNIQUE constraint failures
                import random

                usage_id = f"usage_{int(time.time() * 1000000)}_{hash(api_key) % 10000}_{random.randint(1000, 9999)}"

                # Always create a new record for each request to enable proper rate limiting
                # This allows us to track individual requests with precise timestamps
                cursor.execute(
                    """
                    INSERT INTO api_usage
                    (id, api_key, endpoint, requests_count, usage_date, customer_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        usage_id,
                            api_key,
                            endpoint,
                            1,
                            usage_date,
                            customer_email,
                            current_time.isoformat(),
                            ),
                        )

                conn.commit()

        except Exception as e:
            logger.error(f"Error recording API usage: {e}")


    def _calculate_api_billing(self, plan_type, total_requests):
        """Calculate billing amount for API usage"""
        limits = self._get_rate_limits(plan_type)

        base_cost = {"basic": 9.99, "pro": 29.99, "enterprise": 99.99}.get(
            plan_type, 9.99
        )

        # Calculate overage if any
        monthly_limit = limits["monthly_limit"]
        cost_per_request = limits["cost_per_request"]

        if total_requests > monthly_limit:
            overage_requests = total_requests - monthly_limit
            overage_cost = overage_requests * cost_per_request
            total_cost = base_cost + overage_cost
        else:
            overage_requests = 0
            overage_cost = 0
            total_cost = base_cost

        return {
            "plan_type": plan_type,
                "base_cost": base_cost,
                "included_requests": monthly_limit,
                "total_requests": total_requests,
                "overage_requests": overage_requests,
                "overage_cost": overage_cost,
                "total_cost": total_cost,
                "cost_per_request": cost_per_request,
                }


    def run(self, host="0.0.0.0", port = 5002, debug = False):
        """Run the API monetization server"""
        logger.info(f"Starting API Monetization server on {host}:{port}")
        self.app.run(host = host, port = port, debug = debug)

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    import os

    os.makedirs("data", exist_ok = True)

    # Initialize and run API monetization system
    api_monetization = APIMonetization()
    api_monetization.run(debug = True)
