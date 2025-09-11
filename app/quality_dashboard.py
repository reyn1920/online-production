#!/usr / bin / env python3
"""
Quality Metrics Dashboard
Provides real - time quality tracking and visualization for AI benchmark compliance
"""

import json
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS
import requests

@dataclass


class QualityRecord:
    """Quality assessment record"""
    id: str
    content_hash: str
    content_type: str
    validation_id: str
    consensus_score: float
    passed_threshold: bool
    provider_scores: Dict[str, Dict[str, float]]
    recommendations: List[str]
    timestamp: datetime
    response_time_ms: int


class QualityDashboard:
    """Quality metrics dashboard for tracking benchmark compliance"""


    def __init__(self, db_path: str = "quality_metrics.db", benchmark_api_url: str = "http://localhost:5003"):
        self.app = Flask(__name__, template_folder='templates', static_folder='static')
        CORS(self.app)

        self.db_path = db_path
        self.benchmark_api_url = benchmark_api_url
        self.db_lock = threading.Lock()

        self._init_database()
        self._setup_routes()

        print("Quality Dashboard initialized")


    def _init_database(self):
        """Initialize SQLite database for quality metrics"""
        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Quality records table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_records (
                    id TEXT PRIMARY KEY,
                        content_hash TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        validation_id TEXT NOT NULL,
                        consensus_score REAL NOT NULL,
                        passed_threshold BOOLEAN NOT NULL,
                        provider_scores TEXT NOT NULL,
                        recommendations TEXT NOT NULL,
                        timestamp DATETIME NOT NULL,
                        response_time_ms INTEGER NOT NULL
                )
            """)

            # Quality trends table for aggregated metrics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quality_trends (
                    date TEXT PRIMARY KEY,
                        total_validations INTEGER NOT NULL,
                        passed_validations INTEGER NOT NULL,
                        average_score REAL NOT NULL,
                        average_response_time REAL NOT NULL
                )
            """)

            conn.commit()

    @contextmanager


    def _get_db_connection(self):
        """Get database connection with proper locking"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout = 30.0)
            conn.execute('PRAGMA journal_mode = WAL')
            try:
                yield conn
            finally:
                conn.close()


    def _setup_routes(self):
        """Setup Flask routes for the dashboard"""

        @self.app.route('/')


        def dashboard_home():
            """Main dashboard page"""
            return render_template('quality_dashboard.html')

        @self.app.route('/api / quality / validate', methods=['POST'])


        def validate_content():
            """Validate content and store results"""
            try:
                data = request.get_json()
                content = data.get('content', '')
                content_type = data.get('type', 'general')
                providers = data.get('providers', ['chatgpt', 'gemini', 'abacus'])

                if not content:
                    return jsonify({
                        'success': False,
                            'error': 'Content is required'
                    }), 400

                # Call benchmark API
                benchmark_response = requests.post(
                    f"{self.benchmark_api_url}/api / benchmark / validate",
                        json={
                        'content': content,
                            'type': content_type,
                            'providers': providers
                    },
                        timeout = 30
                )

                if benchmark_response.status_code != 200:
                    return jsonify({
                        'success': False,
                            'error': 'Benchmark API error'
                    }), 500

                result = benchmark_response.json()

                # Store quality record
                record = self._store_quality_record(content, content_type, result)

                # Update trends
                self._update_quality_trends()

                return jsonify({
                    'success': True,
                        'record_id': record.id,
                        'validation_id': result['validation_id'],
                        'consensus_score': result['consensus_score'],
                        'passed_threshold': result['passed_threshold'],
                        'metrics': result['metrics'],
                        'recommendations': result['recommendations']
                })

            except requests.RequestException as e:
                return jsonify({
                    'success': False,
                        'error': f'Benchmark service unavailable: {str(e)}'
                }), 503
            except Exception as e:
                return jsonify({
                    'success': False,
                        'error': str(e)
                }), 500

        @self.app.route('/api / quality / metrics', methods=['GET'])


        def get_quality_metrics():
            """Get quality metrics and statistics"""
            try:
                days = int(request.args.get('days', 7))

                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    # Get recent records
                    cursor.execute("""
                        SELECT * FROM quality_records
                        WHERE timestamp >= datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                        LIMIT 100
                    """.format(days))

                    records = []
                    for row in cursor.fetchall():
                        records.append({
                            'id': row[0],
                                'content_hash': row[1],
                                'content_type': row[2],
                                'validation_id': row[3],
                                'consensus_score': row[4],
                                'passed_threshold': bool(row[5]),
                                'provider_scores': json.loads(row[6]),
                                'recommendations': json.loads(row[7]),
                                'timestamp': row[8],
                                'response_time_ms': row[9]
                        })

                    # Get summary statistics
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total,
                                SUM(CASE WHEN passed_threshold = 1 THEN 1 ELSE 0 END) as passed,
                                AVG(consensus_score) as avg_score,
                                AVG(response_time_ms) as avg_response_time,
                                MIN(consensus_score) as min_score,
                                MAX(consensus_score) as max_score
                        FROM quality_records
                        WHERE timestamp >= datetime('now', '-{} days')
                    """.format(days))

                    stats_row = cursor.fetchone()
                    stats = {
                        'total_validations': stats_row[0] or 0,
                            'passed_validations': stats_row[1] or 0,
                            'pass_rate': (stats_row[1] / stats_row[0] * 100) if stats_row[0] > 0 else 0,
                            'average_score': round(stats_row[2] or 0, 2),
                            'average_response_time': round(stats_row[3] or 0, 2),
                            'min_score': stats_row[4] or 0,
                            'max_score': stats_row[5] or 0
                    }

                    # Get trends data
                    cursor.execute("""
                        SELECT * FROM quality_trends
                        WHERE date >= date('now', '-{} days')
                        ORDER BY date DESC
                    """.format(days))

                    trends = []
                    for row in cursor.fetchall():
                        trends.append({
                            'date': row[0],
                                'total_validations': row[1],
                                'passed_validations': row[2],
                                'average_score': row[3],
                                'average_response_time': row[4]
                        })

                return jsonify({
                    'success': True,
                        'records': records,
                        'statistics': stats,
                        'trends': trends
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                        'error': str(e)
                }), 500

        @self.app.route('/api / quality / providers', methods=['GET'])


        def get_provider_status():
            """Get benchmark provider status"""
            try:
                response = requests.get(
                    f"{self.benchmark_api_url}/api / benchmark / providers",
                        timeout = 10
                )

                if response.status_code == 200:
                    return jsonify(response.json())
                else:
                    return jsonify({
                        'success': False,
                            'error': 'Provider status unavailable'
                    }), 503

            except requests.RequestException:
                return jsonify({
                    'success': False,
                        'error': 'Benchmark service unavailable'
                }), 503

        @self.app.route('/api / quality / export', methods=['GET'])


        def export_quality_data():
            """Export quality data as JSON"""
            try:
                days = int(request.args.get('days', 30))

                with self._get_db_connection() as conn:
                    cursor = conn.cursor()

                    cursor.execute("""
                        SELECT * FROM quality_records
                        WHERE timestamp >= datetime('now', '-{} days')
                        ORDER BY timestamp DESC
                    """.format(days))

                    records = []
                    for row in cursor.fetchall():
                        records.append({
                            'id': row[0],
                                'content_hash': row[1],
                                'content_type': row[2],
                                'validation_id': row[3],
                                'consensus_score': row[4],
                                'passed_threshold': bool(row[5]),
                                'provider_scores': json.loads(row[6]),
                                'recommendations': json.loads(row[7]),
                                'timestamp': row[8],
                                'response_time_ms': row[9]
                        })

                return jsonify({
                    'success': True,
                        'export_date': datetime.now().isoformat(),
                        'records_count': len(records),
                        'records': records
                })

            except Exception as e:
                return jsonify({
                    'success': False,
                        'error': str(e)
                }), 500


    def _store_quality_record(self, content: str, content_type: str, result: Dict[str, Any]) -> QualityRecord:
        """Store quality validation record in database"""
        import hashlib

        content_hash = hashlib.md5(content.encode()).hexdigest()
        record_id = f"qr_{int(datetime.now().timestamp() * 1000)}_{content_hash[:8]}"

        # Extract provider scores
        provider_scores = {}
        for metric in result.get('metrics', []):
            provider_scores[metric['provider']] = {
                'correctness': metric['correctness'],
                    'clarity': metric['clarity'],
                    'professionalism': metric['professionalism'],
                    'overall_score': metric['overall_score'],
                    'response_time_ms': metric['response_time_ms']
            }

        record = QualityRecord(
            id = record_id,
                content_hash = content_hash,
                content_type = content_type,
                validation_id = result['validation_id'],
                consensus_score = result['consensus_score'],
                passed_threshold = result['passed_threshold'],
                provider_scores = provider_scores,
                recommendations = result['recommendations'],
                timestamp = datetime.now(),
                response_time_ms = sum(m['response_time_ms'] for m in result.get('metrics', []))
        )

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO quality_records (
                    id, content_hash, content_type, validation_id,
                        consensus_score, passed_threshold, provider_scores,
                        recommendations, timestamp, response_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.id,
                    record.content_hash,
                    record.content_type,
                    record.validation_id,
                    record.consensus_score,
                    record.passed_threshold,
                    json.dumps(record.provider_scores),
                    json.dumps(record.recommendations),
                    record.timestamp.isoformat(),
                    record.response_time_ms
            ))

            conn.commit()

        return record


    def _update_quality_trends(self):
        """Update daily quality trends"""
        today = datetime.now().date().isoformat()

        with self._get_db_connection() as conn:
            cursor = conn.cursor()

            # Get today's statistics
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                        SUM(CASE WHEN passed_threshold = 1 THEN 1 ELSE 0 END) as passed,
                        AVG(consensus_score) as avg_score,
                        AVG(response_time_ms) as avg_response_time
                FROM quality_records
                WHERE date(timestamp) = ?
            """, (today,))

            row = cursor.fetchone()
            if row and row[0] > 0:
                # Insert or update trend record
                cursor.execute("""
                    INSERT OR REPLACE INTO quality_trends (
                        date, total_validations, passed_validations,
                            average_score, average_response_time
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    today,
                        row[0],
                        row[1] or 0,
                        round(row[2] or 0, 2),
                        round(row[3] or 0, 2)
                ))

                conn.commit()


    def run(self, host='0.0.0.0', port = 5004, debug = False):
        """Run the quality dashboard server"""
        print(f"Starting Quality Dashboard on {host}:{port}")
        self.app.run(host = host, port = port, debug = debug)

if __name__ == '__main__':
    # Initialize and run the quality dashboard
    dashboard = QualityDashboard()
    dashboard.run(debug = True)
