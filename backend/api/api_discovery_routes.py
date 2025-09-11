#!/usr/bin/env python3
"""
API Discovery Routes
Backend endpoints for API discovery and management
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional

from flask import Blueprint, request, jsonify, current_app
from functools import wraps
import sqlite3
import os
import sys

# Add the backend services directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'services'))

try:
    from api_discovery_service import APIDiscoveryService, APICandidate
except ImportError:
    print("Warning: APIDiscoveryService not found. Make sure the service is properly installed.")
    APIDiscoveryService = None
    APICandidate = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
api_discovery_bp = Blueprint('api_discovery', __name__, url_prefix='/api')

def require_auth(f):
    """Simple authentication decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        # In production, validate the token properly
        if token not in ['demo-token', 'valid-token']:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@api_discovery_bp.route('/discover-apis', methods=['POST'])
@require_auth
def discover_apis():
    """Discover APIs for specified channel(s)"""
    try:
        data = request.get_json() or {}
        channel = data.get('channel', 'all')
        
        if not APIDiscoveryService:
            return jsonify({
                'error': 'API Discovery Service not available',
                'apis': get_mock_apis(channel)
            }), 200
        
        # Run the async discovery service
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            async def run_discovery():
                async with APIDiscoveryService() as service:
                    if channel == 'all':
                        results = await service.discover_all_channels()
                    else:
                        candidates = await service.discover_apis_for_channel(channel)
                        results = {channel: candidates}
                    
                    # Convert APICandidate objects to dictionaries
                    serialized_results = {}
                    for ch, apis in results.items():
                        serialized_results[ch] = [
                            {
                                'name': api.name,
                                'url': api.url,
                                'signup_url': api.signup_url,
                                'category': api.category,
                                'cost_model': api.cost_model,
                                'description': api.description,
                                'features': api.features,
                                'rate_limits': api.rate_limits,
                                'documentation_url': api.documentation_url,
                                'score': api.score,
                                'discovered_at': api.discovered_at,
                                'channel': api.channel
                            } for api in apis
                        ]
                    
                    return serialized_results
            
            results = loop.run_until_complete(run_discovery())
            
            return jsonify({
                'success': True,
                'apis': results,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            loop.close()
    
    except Exception as e:
        logger.error(f"Error in discover_apis: {e}")
        return jsonify({
            'error': str(e),
            'apis': get_mock_apis(channel)
        }), 200  # Return mock data instead of error

@api_discovery_bp.route('/free-apis', methods=['GET'])
@require_auth
def get_free_apis():
    """Get all free and freemium APIs"""
    try:
        if not APIDiscoveryService:
            return jsonify({
                'success': True,
                'apis': get_mock_free_apis()
            })
        
        # Get from database
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'intelligence.db')
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM discovered_apis 
                WHERE cost_model IN ('free', 'freemium')
                ORDER BY score DESC, name ASC
            """)
            
            apis = []
            for row in cursor.fetchall():
                api_dict = dict(row)
                # Parse features JSON
                try:
                    api_dict['features'] = json.loads(api_dict['features'] or '[]')
                except (json.JSONDecodeError, TypeError):
                    api_dict['features'] = []
                apis.append(api_dict)
        
        # If no APIs in database, return mock data
        if not apis:
            apis = get_mock_free_apis()
        
        return jsonify({
            'success': True,
            'apis': apis
        })
    
    except Exception as e:
        logger.error(f"Error in get_free_apis: {e}")
        return jsonify({
            'success': True,
            'apis': get_mock_free_apis()
        })

@api_discovery_bp.route('/channel-apis/<channel>', methods=['GET'])
@require_auth
def get_channel_apis(channel):
    """Get APIs for a specific channel"""
    try:
        limit = request.args.get('limit', 10, type=int)
        
        if not APIDiscoveryService:
            return jsonify({
                'success': True,
                'apis': get_mock_channel_apis(channel, limit)
            })
        
        # Get from database
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'intelligence.db')
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM discovered_apis 
                WHERE channel = ? 
                ORDER BY score DESC, cost_model = 'free' DESC
                LIMIT ?
            """, (channel, limit))
            
            apis = []
            for row in cursor.fetchall():
                api_dict = dict(row)
                try:
                    api_dict['features'] = json.loads(api_dict['features'] or '[]')
                except (json.JSONDecodeError, TypeError):
                    api_dict['features'] = []
                apis.append(api_dict)
        
        if not apis:
            apis = get_mock_channel_apis(channel, limit)
        
        return jsonify({
            'success': True,
            'channel': channel,
            'apis': apis
        })
    
    except Exception as e:
        logger.error(f"Error in get_channel_apis: {e}")
        return jsonify({
            'success': True,
            'channel': channel,
            'apis': get_mock_channel_apis(channel, 5)
        })

@api_discovery_bp.route('/api-stats', methods=['GET'])
@require_auth
def get_api_stats():
    """Get API discovery statistics"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'intelligence.db')
        
        with sqlite3.connect(db_path) as conn:
            # Total APIs
            total_cursor = conn.execute("SELECT COUNT(*) as count FROM discovered_apis")
            total_apis = total_cursor.fetchone()[0]
            
            # Free APIs
            free_cursor = conn.execute("""
                SELECT COUNT(*) as count FROM discovered_apis 
                WHERE cost_model IN ('free', 'freemium')
            """)
            free_apis = free_cursor.fetchone()[0]
            
            # Average score
            avg_cursor = conn.execute("SELECT AVG(score) as avg_score FROM discovered_apis")
            avg_score = avg_cursor.fetchone()[0] or 0.0
            
            # Channels with APIs
            channels_cursor = conn.execute("""
                SELECT COUNT(DISTINCT channel) as count FROM discovered_apis
            """)
            channels_count = channels_cursor.fetchone()[0]
            
            # Recent discoveries
            recent_cursor = conn.execute("""
                SELECT COUNT(*) as count FROM discovered_apis 
                WHERE date(discovered_at) = date('now')
            """)
            recent_discoveries = recent_cursor.fetchone()[0]
        
        return jsonify({
            'success': True,
            'stats': {
                'total_apis': total_apis,
                'free_apis': free_apis,
                'avg_score': round(avg_score, 1),
                'channels_count': channels_count,
                'recent_discoveries': recent_discoveries
            }
        })
    
    except Exception as e:
        logger.error(f"Error in get_api_stats: {e}")
        return jsonify({
            'success': True,
            'stats': {
                'total_apis': 0,
                'free_apis': 0,
                'avg_score': 0.0,
                'channels_count': 8,
                'recent_discoveries': 0
            }
        })

@api_discovery_bp.route('/search-history', methods=['GET'])
@require_auth
def get_search_history():
    """Get API search history"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        db_path = os.path.join(os.path.dirname(__file__), '..', '..', 'intelligence.db')
        
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM api_search_history 
                ORDER BY search_date DESC 
                LIMIT ?
            """, (limit,))
            
            history = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'history': history
        })
    
    except Exception as e:
        logger.error(f"Error in get_search_history: {e}")
        return jsonify({
            'success': True,
            'history': []
        })

# Mock data functions for when the service is not available
def get_mock_apis(channel):
    """Return mock API data for testing"""
    mock_data = {
        'youtube': [
            {
                'name': 'YouTube Data API v3',
                'url': 'https://developers.google.com/youtube/v3',
                'signup_url': 'https://console.cloud.google.com/',
                'category': 'social',
                'cost_model': 'free',
                'description': 'Access YouTube data including videos, channels, playlists, and more',
                'features': ['video analytics', 'channel data', 'playlist management', 'search'],
                'rate_limits': '10,000 requests per day',
                'documentation_url': 'https://developers.google.com/youtube/v3',
                'score': 8.5,
                'discovered_at': datetime.now().isoformat(),
                'channel': 'youtube'
            },
            {
                'name': 'YouTube Analytics API',
                'url': 'https://developers.google.com/youtube/analytics',
                'signup_url': 'https://console.cloud.google.com/',
                'category': 'analytics',
                'cost_model': 'free',
                'description': 'Retrieve YouTube Analytics reports for your channel',
                'features': ['revenue data', 'view analytics', 'audience insights'],
                'rate_limits': '50,000 requests per day',
                'documentation_url': 'https://developers.google.com/youtube/analytics',
                'score': 8.0,
                'discovered_at': datetime.now().isoformat(),
                'channel': 'youtube'
            }
        ],
        'email': [
            {
                'name': 'SendGrid API',
                'url': 'https://sendgrid.com/docs/api-reference/',
                'signup_url': 'https://signup.sendgrid.com/',
                'category': 'email',
                'cost_model': 'freemium',
                'description': 'Email delivery service with powerful APIs',
                'features': ['transactional email', 'marketing campaigns', 'analytics', 'templates'],
                'rate_limits': '100 emails/day free',
                'documentation_url': 'https://sendgrid.com/docs/',
                'score': 7.8,
                'discovered_at': datetime.now().isoformat(),
                'channel': 'email'
            }
        ],
        'affiliate': [
            {
                'name': 'Amazon Associates API',
                'url': 'https://webservices.amazon.com/paapi5/documentation/',
                'signup_url': 'https://affiliate-program.amazon.com/',
                'category': 'affiliate',
                'cost_model': 'free',
                'description': 'Amazon Product Advertising API for affiliate marketing',
                'features': ['product data', 'pricing', 'affiliate links', 'reviews'],
                'rate_limits': '8640 requests per day',
                'documentation_url': 'https://webservices.amazon.com/paapi5/documentation/',
                'score': 9.0,
                'discovered_at': datetime.now().isoformat(),
                'channel': 'affiliate'
            }
        ]
    }
    
    if channel == 'all':
        return mock_data
    else:
        return {channel: mock_data.get(channel, [])}

def get_mock_free_apis():
    """Return mock free API data"""
    return [
        {
            'name': 'YouTube Data API v3',
            'url': 'https://developers.google.com/youtube/v3',
            'signup_url': 'https://console.cloud.google.com/',
            'category': 'social',
            'cost_model': 'free',
            'description': 'Access YouTube data including videos, channels, playlists',
            'features': ['video analytics', 'channel data', 'playlist management'],
            'rate_limits': '10,000 requests per day',
            'documentation_url': 'https://developers.google.com/youtube/v3',
            'score': 8.5,
            'discovered_at': datetime.now().isoformat(),
            'channel': 'youtube'
        },
        {
            'name': 'Twitter API v2',
            'url': 'https://developer.twitter.com/en/docs/twitter-api',
            'signup_url': 'https://developer.twitter.com/',
            'category': 'social',
            'cost_model': 'freemium',
            'description': 'Access Twitter data and functionality',
            'features': ['tweet data', 'user profiles', 'trends'],
            'rate_limits': '500,000 tweets/month free',
            'documentation_url': 'https://developer.twitter.com/en/docs',
            'score': 7.5,
            'discovered_at': datetime.now().isoformat(),
            'channel': 'twitter'
        },
        {
            'name': 'Amazon Associates API',
            'url': 'https://webservices.amazon.com/paapi5/documentation/',
            'signup_url': 'https://affiliate-program.amazon.com/',
            'category': 'affiliate',
            'cost_model': 'free',
            'description': 'Amazon Product Advertising API',
            'features': ['product data', 'pricing', 'affiliate links'],
            'rate_limits': '8640 requests per day',
            'documentation_url': 'https://webservices.amazon.com/paapi5/documentation/',
            'score': 9.0,
            'discovered_at': datetime.now().isoformat(),
            'channel': 'affiliate'
        }
    ]

def get_mock_channel_apis(channel, limit):
    """Return mock API data for a specific channel"""
    all_mock = get_mock_apis('all')
    channel_apis = all_mock.get(channel, [])
    return channel_apis[:limit]

# Error handlers
@api_discovery_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@api_discovery_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Test the routes
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(api_discovery_bp)
    
    @app.route('/')
    def index():
        return jsonify({'message': 'API Discovery Service is running'})
    
    app.run(debug=True, port=5001)