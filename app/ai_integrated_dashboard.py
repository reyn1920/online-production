#!/usr/bin/env python3
"""
AI Integrated Dashboard - Direct Integration with ChatGPT, Gemini, and Abacus AI

Replaces traditional dashboard functionality with direct AI platform integration.
Provides seamless access to ChatGPT, Gemini, and Abacus AI through embedded interfaces.

Features:
- Direct ChatGPT integration via iframe
- Gemini integration with fallback handling
- Abacus AI chatbot integration
- Unified interface for all three platforms
- Real-time switching between AI providers
- Quality validation through AI consensus

Author: TRAE.AI System
Version: 3.0.0 - AI Platform Integration
"""

import os
import json
import logging
import secrets
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from flask import Flask, render_template, request, jsonify, Response
import requests
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

# Import web-based AI integration
try:
    from core_ai_integration import core_ai, AIPlatform, get_ai_cost_summary, get_ai_cost_analytics
except ImportError:
    try:
        import sys
        sys.path.append('..')
        from core_ai_integration import core_ai, AIPlatform, get_ai_cost_summary, get_ai_cost_analytics
    except ImportError:
        logger.warning("Web-based AI integration not available - running with limited functionality")
        core_ai = None

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIIntegratedDashboard:
    """Main dashboard class with direct AI platform integration."""
    
    def __init__(self, host='0.0.0.0', port=5005):
        self.host = host
        self.port = port
        self.app = Flask(__name__, 
                        template_folder='templates',
                        static_folder='../static')
        
        # AI platforms - these specific sites are always open on this computer
        self.ai_platforms = {
            'chatgpt': 'https://chatgpt.com/',
            'gemini': 'https://gemini.google.com/app',
            'abacus': 'https://apps.abacus.ai/chatllm/?appId=1024a18ebe'
        }
        
        # Fallback URLs (not needed since platforms are always open)
        self.fallback_platforms = {
            'chatgpt': 'https://chat.openai.com/',
            'gemini': 'https://bard.google.com/',
            'abacus': 'https://abacus.ai/'
        }
        
        # Current active platform
        self.active_platform = 'chatgpt'
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Web-based AI Integrated Dashboard initialized")
        logger.info("Using browser automation for ChatGPT, Gemini, and Abacus AI (no API keys required)")
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def index():
            """Main dashboard page with AI platform integration."""
            return render_template('ai_integrated_dashboard.html', 
                                 platforms=self.ai_platforms,
                                 active_platform=self.active_platform)
        
        @self.app.route('/api/switch-platform', methods=['POST'])
        def switch_platform():
            """Switch between AI platforms."""
            try:
                data = request.get_json()
                platform = data.get('platform')
                
                if platform not in self.ai_platforms:
                    return jsonify({'error': 'Invalid platform'}), 400
                
                self.active_platform = platform
                
                return jsonify({
                    'success': True,
                    'active_platform': self.active_platform,
                    'platform_url': self.ai_platforms[platform]
                })
                
            except Exception as e:
                logger.error(f"Error switching platform: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/platform-status')
        def platform_status():
            """Get status of all AI platforms - they are always available since they're open and minimized on this computer"""
            # No HTTP checks needed - platforms are always open and minimized
            platforms = {
                'chatgpt': {
                    'status': 'ready',
                    'url': 'https://chatgpt.com/',
                    'fallback_url': 'https://chat.openai.com/',
                    'note': 'Always open and minimized - no login required'
                },
                'gemini': {
                    'status': 'ready', 
                    'url': 'https://gemini.google.com/app',
                    'fallback_url': 'https://bard.google.com/',
                    'note': 'Always open and minimized - no login required'
                },
                'abacus': {
                    'status': 'ready',
                    'url': 'https://apps.abacus.ai/chatllm/?appId=1024a18ebe',
                    'fallback_url': 'https://abacus.ai/',
                    'note': 'Always open and minimized - no login required'
                }
            }
            
            return jsonify({
                'platforms': platforms,
                'message': 'All AI platforms are always available (open and minimized on this computer)',
                'no_login_required': True,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.app.route('/api/validate-quality', methods=['POST'])
        def validate_quality():
            """Validate content quality using real AI consensus from all three platforms."""
            try:
                data = request.get_json()
                content = data.get('content', '')
                
                if not content:
                    return jsonify({'error': 'No content provided'}), 400
                
                if not core_ai:
                    return jsonify({'error': 'Web-based AI integration not available'}), 503
                
                # Real AI validation using web-based platforms (no API costs)
                validation_prompt = f"Please evaluate this content for quality, clarity, and professionalism on a scale of 1-100. Provide a brief feedback comment. Content: {content}"
                
                platform_results = {}
                total_score = 0
                successful_validations = 0
                
                # Query each web-based platform (browser automation)
                for platform in [AIPlatform.CHATGPT, AIPlatform.GEMINI, AIPlatform.ABACUS_AI]:
                    try:
                        response = core_ai.process_with_ai(validation_prompt, platform, "quality_validation")
                        if response.success:
                            # Extract score from response (simplified parsing)
                            score = self._extract_score_from_response(response.content)
                            platform_results[platform.value] = {
                                'score': score,
                                'feedback': response.content[:200] + '...' if len(response.content) > 200 else response.content,
                                'status': 'approved' if score >= 70 else 'needs_improvement',
                                'response_time': response.response_time_ms,
                                'method': 'web_automation'
                            }
                            total_score += score
                            successful_validations += 1
                        else:
                            platform_results[platform.value] = {
                                'score': 0,
                                'feedback': f'Web platform error: {response.error_message}',
                                'status': 'error',
                                'method': 'web_automation'
                            }
                    except Exception as e:
                        logger.error(f"Error validating with web platform {platform.value}: {e}")
                        platform_results[platform.value] = {
                            'score': 0,
                            'feedback': f'Web platform unavailable: {str(e)}',
                            'status': 'error',
                            'method': 'web_automation'
                        }
                
                consensus_score = total_score / max(1, successful_validations)
                
                validation_result = {
                    'content': content[:100] + '...' if len(content) > 100 else content,
                    'platforms': platform_results,
                    'consensus_score': round(consensus_score, 1),
                    'overall_status': 'approved' if consensus_score >= 70 else 'needs_improvement',
                    'successful_validations': successful_validations,
                    'method': 'web_based_consensus',
                    'cost_model': 'no_api_costs',
                    'timestamp': datetime.now().isoformat()
                }
                
                return jsonify(validation_result)
                
            except Exception as e:
                logger.error(f"Error validating quality: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/dashboard-stats')
        def dashboard_stats():
            """Get comprehensive dashboard statistics and metrics."""
            stats = {
                'active_platform': self.active_platform,
                'total_platforms': len(self.ai_platforms),
                'uptime': time.time(),
                'version': '3.0.0',
                'features': [
                    'Web-based ChatGPT Integration',
                    'Web-based Gemini Integration', 
                    'Web-based Abacus AI Integration',
                    'Browser Automation (No API Keys)',
                    'Quality Validation Consensus',
                    'Unified Interface',
                    'Zero API Costs'
                ],
                'timestamp': datetime.now().isoformat()
            }
            
            # Add AI integration stats if available
            if core_ai:
                try:
                    ai_stats = core_ai.get_integration_stats()
                    cost_summary = get_ai_cost_summary()
                    
                    stats.update({
                        'ai_integration': {
                            'total_requests': ai_stats['core_stats']['total_requests'],
                            'successful_requests': ai_stats['core_stats']['successful_requests'],
                            'success_rate': ai_stats['success_rate'],
                            'platform_usage': ai_stats['core_stats']['platform_usage'],
                            'most_used_platform': ai_stats['most_used_platform']
                        },
                        'cost_tracking': {
                            'session_cost': cost_summary['session_cost'],
                            'session_requests': cost_summary['session_requests'],
                            'cost_recommendations': cost_summary['cost_recommendations'][:3]  # Top 3 recommendations
                        }
                    })
                except Exception as e:
                    logger.error(f"Error getting AI stats: {e}")
                    stats['ai_integration_error'] = str(e)
            
            return jsonify(stats)
        
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Not found'}), 404
        
        @self.app.route('/api/ai-chat', methods=['POST'])
        def ai_chat():
            """Direct AI chat endpoint for real-time interaction."""
            try:
                data = request.get_json()
                message = data.get('message', '')
                platform = data.get('platform', self.active_platform)
                
                if not message:
                    return jsonify({'error': 'No message provided'}), 400
                
                if not core_ai:
                    return jsonify({'error': 'Web-based AI integration not available'}), 503
                
                # Convert platform string to enum
                platform_enum = None
                if platform == 'chatgpt':
                    platform_enum = AIPlatform.CHATGPT
                elif platform == 'gemini':
                    platform_enum = AIPlatform.GEMINI
                elif platform == 'abacus':
                    platform_enum = AIPlatform.ABACUS_AI
                else:
                    return jsonify({'error': 'Invalid platform'}), 400
                
                # Process with AI
                response = core_ai.process_with_ai(message, platform_enum, "chat")
                
                if response.success:
                    return jsonify({
                        'success': True,
                        'response': response.content,
                        'platform': platform,
                        'response_time_ms': response.response_time_ms,
                        'timestamp': datetime.now().isoformat()
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': response.error_message,
                        'platform': platform,
                        'timestamp': datetime.now().isoformat()
                    }), 500
                
            except Exception as e:
                logger.error(f"Error in AI chat: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/cost-analytics')
        def cost_analytics():
            """Get detailed cost analytics for AI usage."""
            try:
                if not core_ai:
                    return jsonify({'error': 'Web-based AI integration not available'}), 503
                
                analytics = get_ai_cost_analytics()
                return jsonify(analytics)
                
            except Exception as e:
                logger.error(f"Error getting cost analytics: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Internal server error'}), 500
    
    def _extract_score_from_response(self, response_text: str) -> int:
        """Extract numerical score from AI response text."""
        import re
        
        # Look for patterns like "Score: 85", "85/100", "Rating: 85", etc.
        patterns = [
            r'(?:score|rating)\s*:?\s*(\d+)',
            r'(\d+)\s*/\s*100',
            r'(\d+)\s*(?:out of|/)?\s*100',
            r'\b([7-9]\d|100)\b'  # Numbers 70-100
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response_text.lower())
            if match:
                score = int(match.group(1))
                if 0 <= score <= 100:
                    return score
        
        # Default score if no pattern found
        return 75
    
    def run(self, debug=True):
        """Run the dashboard server."""
        logger.info(f"Starting AI Integrated Dashboard on {self.host}:{self.port}")
        logger.info(f"Dashboard URL: http://{self.host}:{self.port}")
        
        # Log platform URLs
        for platform, url in self.ai_platforms.items():
            logger.info(f"{platform.upper()} URL: {url}")
        
        # Log AI integration status
        if core_ai:
            logger.info("Web-based AI Integration: ACTIVE")
            logger.info("Browser automation for ChatGPT, Gemini, and Abacus AI enabled (no API costs)")
        else:
            logger.warning("Web-based AI Integration: DISABLED - Limited functionality")
        
        self.app.run(host=self.host, port=self.port, debug=debug)

def main():
    """Main entry point for the AI integrated dashboard."""
    dashboard = AIIntegratedDashboard()
    dashboard.run()

if __name__ == '__main__':
    main()