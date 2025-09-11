#!/usr/bin/env python3
"""
RouteLL Rate Limiter and Usage Optimizer
Implements intelligent rate limiting and credit optimization strategies
"""

import time
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
import logging

class RateLimiter:
    """
    Advanced rate limiter with multiple strategies for credit optimization
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or "/Users/thomasbrianreynolds/online production/config/routellm_config.json"
        self.config = self._load_config()
        
        # Rate limiting state
        self.request_history = deque(maxlen=1000)  # Last 1000 requests
        self.credit_usage_history = deque(maxlen=1000)
        self.model_performance = defaultdict(lambda: {'avg_response_time': 0, 'success_rate': 1.0, 'cost_per_token': 0})
        
        # Thread safety
        self.lock = threading.Lock()
        
        # Rate limiting windows
        self.windows = {
            'minute': deque(maxlen=100),
            'hour': deque(maxlen=3600),
            'day': deque(maxlen=86400)
        }
        
        # Optimization strategies
        self.optimization_strategies = {
            'conservative': {'max_rpm': 30, 'max_rph': 1000, 'max_rpd': 10000},
            'balanced': {'max_rpm': 60, 'max_rph': 2000, 'max_rpd': 20000},
            'aggressive': {'max_rpm': 100, 'max_rph': 3000, 'max_rpd': 30000}
        }
        
        self.current_strategy = 'balanced'
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self) -> Dict:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration"""
        return {
            "rate_limiting": {
                "requests_per_minute": 60,
                "requests_per_hour": 2000,
                "requests_per_day": 20000,
                "burst_allowance": 10,
                "backoff_strategy": "exponential"
            },
            "optimization": {
                "auto_model_selection": True,
                "cost_optimization": True,
                "performance_tracking": True,
                "adaptive_rate_limiting": True
            }
        }
    
    def can_make_request(self, model: str = None, estimated_tokens: int = 100) -> Tuple[bool, str, float]:
        """
        Check if a request can be made based on rate limits and optimization
        
        Returns:
            Tuple[bool, str, float]: (can_proceed, reason, wait_time_seconds)
        """
        with self.lock:
            now = time.time()
            
            # Clean old entries
            self._cleanup_windows(now)
            
            # Check rate limits
            rate_check = self._check_rate_limits(now)
            if not rate_check[0]:
                return rate_check
            
            # Check credit optimization
            credit_check = self._check_credit_optimization(model, estimated_tokens)
            if not credit_check[0]:
                return credit_check
            
            # Check model-specific limits
            model_check = self._check_model_limits(model, now)
            if not model_check[0]:
                return model_check
            
            return True, "Request approved", 0.0
    
    def _cleanup_windows(self, now: float):
        """Remove old entries from rate limiting windows"""
        # Clean minute window (keep last 60 seconds)
        while self.windows['minute'] and now - self.windows['minute'][0] > 60:
            self.windows['minute'].popleft()
        
        # Clean hour window (keep last 3600 seconds)
        while self.windows['hour'] and now - self.windows['hour'][0] > 3600:
            self.windows['hour'].popleft()
        
        # Clean day window (keep last 86400 seconds)
        while self.windows['day'] and now - self.windows['day'][0] > 86400:
            self.windows['day'].popleft()
    
    def _check_rate_limits(self, now: float) -> Tuple[bool, str, float]:
        """Check if request is within rate limits"""
        strategy = self.optimization_strategies[self.current_strategy]
        
        # Check requests per minute
        if len(self.windows['minute']) >= strategy['max_rpm']:
            wait_time = 60 - (now - self.windows['minute'][0])
            return False, f"Rate limit exceeded: {strategy['max_rpm']} requests per minute", max(0, wait_time)
        
        # Check requests per hour
        if len(self.windows['hour']) >= strategy['max_rph']:
            wait_time = 3600 - (now - self.windows['hour'][0])
            return False, f"Rate limit exceeded: {strategy['max_rph']} requests per hour", max(0, wait_time)
        
        # Check requests per day
        if len(self.windows['day']) >= strategy['max_rpd']:
            wait_time = 86400 - (now - self.windows['day'][0])
            return False, f"Rate limit exceeded: {strategy['max_rpd']} requests per day", max(0, wait_time)
        
        return True, "Rate limits OK", 0.0
    
    def _check_credit_optimization(self, model: str, estimated_tokens: int) -> Tuple[bool, str, float]:
        """Check credit usage optimization"""
        if not self.config.get('optimization', {}).get('cost_optimization', True):
            return True, "Cost optimization disabled", 0.0
        
        # Estimate cost for this request
        estimated_cost = self._estimate_request_cost(model, estimated_tokens)
        
        # Check if we have enough credits for the day
        daily_usage = sum(entry.get('credits', 0) for entry in self.credit_usage_history 
                         if time.time() - entry.get('timestamp', 0) < 86400)
        
        daily_limit = self.config.get('credit_system', {}).get('daily_limit', 1000)
        
        if daily_usage + estimated_cost > daily_limit:
            return False, f"Daily credit limit would be exceeded. Used: {daily_usage}, Limit: {daily_limit}", 3600
        
        return True, "Credit optimization OK", 0.0
    
    def _check_model_limits(self, model: str, now: float) -> Tuple[bool, str, float]:
        """Check model-specific rate limits"""
        if not model:
            return True, "No model specified", 0.0
        
        # Check if model is in high-cost category
        high_cost_models = self.config.get('credit_system', {}).get('high_cost_models', [])
        
        if model in high_cost_models:
            # More restrictive limits for expensive models
            model_requests = [entry for entry in self.request_history 
                            if entry.get('model') == model and now - entry.get('timestamp', 0) < 3600]
            
            if len(model_requests) >= 100:  # Max 100 requests per hour for expensive models
                return False, f"Model-specific rate limit exceeded for {model}", 1800
        
        return True, "Model limits OK", 0.0
    
    def _estimate_request_cost(self, model: str, estimated_tokens: int) -> float:
        """Estimate the cost of a request"""
        # Default cost per token (this would be model-specific in production)
        cost_per_token = 0.001
        
        # Adjust based on model
        if model in self.config.get('credit_system', {}).get('high_cost_models', []):
            cost_per_token *= 3  # 3x cost for premium models
        elif model in self.config.get('credit_system', {}).get('unlimited_models', []):
            cost_per_token = 0  # Free models
        
        return estimated_tokens * cost_per_token
    
    def record_request(self, model: str, tokens_used: int, response_time: float, success: bool, credits_used: float = 0):
        """Record a completed request for analytics and optimization"""
        with self.lock:
            now = time.time()
            
            # Record in all windows
            for window in self.windows.values():
                window.append(now)
            
            # Record detailed request info
            request_info = {
                'timestamp': now,
                'model': model,
                'tokens_used': tokens_used,
                'response_time': response_time,
                'success': success,
                'credits_used': credits_used
            }
            
            self.request_history.append(request_info)
            
            if credits_used > 0:
                self.credit_usage_history.append({
                    'timestamp': now,
                    'credits': credits_used,
                    'model': model
                })
            
            # Update model performance metrics
            self._update_model_performance(model, response_time, success, credits_used, tokens_used)
            
            # Adaptive rate limiting
            if self.config.get('optimization', {}).get('adaptive_rate_limiting', True):
                self._adjust_rate_limiting_strategy()
    
    def _update_model_performance(self, model: str, response_time: float, success: bool, credits_used: float, tokens_used: int):
        """Update performance metrics for a model"""
        perf = self.model_performance[model]
        
        # Update average response time (exponential moving average)
        alpha = 0.1
        perf['avg_response_time'] = (1 - alpha) * perf['avg_response_time'] + alpha * response_time
        
        # Update success rate (exponential moving average)
        perf['success_rate'] = (1 - alpha) * perf['success_rate'] + alpha * (1.0 if success else 0.0)
        
        # Update cost per token
        if tokens_used > 0:
            cost_per_token = credits_used / tokens_used
            perf['cost_per_token'] = (1 - alpha) * perf['cost_per_token'] + alpha * cost_per_token
    
    def _adjust_rate_limiting_strategy(self):
        """Dynamically adjust rate limiting strategy based on performance"""
        recent_requests = [req for req in self.request_history 
                          if time.time() - req.get('timestamp', 0) < 3600]  # Last hour
        
        if len(recent_requests) < 10:
            return  # Not enough data
        
        # Calculate success rate
        success_rate = sum(1 for req in recent_requests if req.get('success', False)) / len(recent_requests)
        
        # Calculate average response time
        avg_response_time = sum(req.get('response_time', 0) for req in recent_requests) / len(recent_requests)
        
        # Adjust strategy based on performance
        if success_rate > 0.95 and avg_response_time < 2.0:
            # High success rate and fast responses - can be more aggressive
            if self.current_strategy != 'aggressive':
                self.current_strategy = 'aggressive'
                self.logger.info("Switched to aggressive rate limiting strategy")
        elif success_rate < 0.85 or avg_response_time > 5.0:
            # Low success rate or slow responses - be more conservative
            if self.current_strategy != 'conservative':
                self.current_strategy = 'conservative'
                self.logger.info("Switched to conservative rate limiting strategy")
        else:
            # Balanced performance
            if self.current_strategy != 'balanced':
                self.current_strategy = 'balanced'
                self.logger.info("Switched to balanced rate limiting strategy")
    
    def get_optimal_model(self, task_type: str = "general", max_cost: float = None) -> str:
        """Get the optimal model based on performance and cost"""
        if not self.config.get('optimization', {}).get('auto_model_selection', True):
            return self.config.get('api_settings', {}).get('default_model', 'route-llm')
        
        # Score models based on performance and cost
        model_scores = {}
        
        for model, perf in self.model_performance.items():
            if max_cost and perf['cost_per_token'] > max_cost:
                continue
            
            # Calculate composite score (higher is better)
            # Factors: success rate (40%), speed (30%), cost (30%)
            speed_score = max(0, 1 - (perf['avg_response_time'] / 10))  # Normalize to 0-1
            cost_score = max(0, 1 - (perf['cost_per_token'] / 0.01))  # Normalize to 0-1
            
            composite_score = (
                perf['success_rate'] * 0.4 +
                speed_score * 0.3 +
                cost_score * 0.3
            )
            
            model_scores[model] = composite_score
        
        if not model_scores:
            return self.config.get('api_settings', {}).get('default_model', 'route-llm')
        
        # Return the highest scoring model
        return max(model_scores.items(), key=lambda x: x[1])[0]
    
    def get_usage_stats(self) -> Dict:
        """Get comprehensive usage statistics"""
        now = time.time()
        
        # Recent requests (last hour)
        recent_requests = [req for req in self.request_history 
                          if now - req.get('timestamp', 0) < 3600]
        
        # Daily stats
        daily_requests = [req for req in self.request_history 
                         if now - req.get('timestamp', 0) < 86400]
        
        daily_credits = sum(entry.get('credits', 0) for entry in self.credit_usage_history 
                           if now - entry.get('timestamp', 0) < 86400)
        
        return {
            'current_strategy': self.current_strategy,
            'requests_last_hour': len(recent_requests),
            'requests_today': len(daily_requests),
            'credits_used_today': daily_credits,
            'success_rate_last_hour': sum(1 for req in recent_requests if req.get('success', False)) / max(1, len(recent_requests)),
            'avg_response_time_last_hour': sum(req.get('response_time', 0) for req in recent_requests) / max(1, len(recent_requests)),
            'model_performance': dict(self.model_performance),
            'rate_limits': self.optimization_strategies[self.current_strategy],
            'windows_status': {
                'minute': len(self.windows['minute']),
                'hour': len(self.windows['hour']),
                'day': len(self.windows['day'])
            }
        }
    
    def reset_limits(self):
        """Reset all rate limiting counters (for testing or manual override)"""
        with self.lock:
            for window in self.windows.values():
                window.clear()
            self.logger.info("Rate limiting counters reset")
    
    def set_strategy(self, strategy: str):
        """Manually set rate limiting strategy"""
        if strategy in self.optimization_strategies:
            self.current_strategy = strategy
            self.logger.info(f"Rate limiting strategy set to: {strategy}")
        else:
            raise ValueError(f"Invalid strategy: {strategy}. Available: {list(self.optimization_strategies.keys())}")


class CreditOptimizer:
    """
    Advanced credit optimization and budget management
    """
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(__name__)
    
    def optimize_request(self, messages: List[Dict], preferences: Dict = None) -> Dict:
        """
        Optimize a request for maximum credit efficiency
        
        Args:
            messages: The conversation messages
            preferences: User preferences (speed, cost, quality)
        
        Returns:
            Dict with optimized parameters
        """
        preferences = preferences or {'cost': 0.7, 'speed': 0.2, 'quality': 0.1}
        
        # Estimate token count
        estimated_tokens = self._estimate_tokens(messages)
        
        # Get optimal model
        max_cost_per_token = 0.01 if preferences.get('cost', 0) > 0.5 else None
        optimal_model = self.rate_limiter.get_optimal_model(max_cost=max_cost_per_token)
        
        # Optimize parameters based on preferences
        optimized_params = {
            'model': optimal_model,
            'messages': messages,
            'max_tokens': min(estimated_tokens * 2, 4000),  # Conservative token limit
            'temperature': 0.7 if preferences.get('quality', 0) > 0.5 else 0.3,
            'stream': preferences.get('speed', 0) > 0.5
        }
        
        # Add cost-saving measures if cost is prioritized
        if preferences.get('cost', 0) > 0.6:
            optimized_params['max_tokens'] = min(optimized_params['max_tokens'], 2000)
            optimized_params['temperature'] = 0.3  # More deterministic = fewer retries
        
        return optimized_params
    
    def _estimate_tokens(self, messages: List[Dict]) -> int:
        """Rough token estimation for messages"""
        total_chars = sum(len(msg.get('content', '')) for msg in messages)
        # Rough approximation: 1 token ≈ 4 characters
        return max(100, total_chars // 4)
    
    def get_budget_recommendations(self, monthly_budget: float) -> Dict:
        """Get budget allocation recommendations"""
        stats = self.rate_limiter.get_usage_stats()
        
        # Calculate current burn rate
        daily_credits = stats['credits_used_today']
        monthly_projection = daily_credits * 30
        
        recommendations = {
            'current_daily_usage': daily_credits,
            'monthly_projection': monthly_projection,
            'budget_status': 'on_track' if monthly_projection <= monthly_budget else 'over_budget',
            'recommended_daily_limit': monthly_budget / 30,
            'savings_opportunities': []
        }
        
        # Add specific recommendations
        if monthly_projection > monthly_budget:
            overage = monthly_projection - monthly_budget
            recommendations['savings_opportunities'].extend([
                f"Reduce daily usage by {overage/30:.1f} credits to stay within budget",
                "Consider using more unlimited models for routine tasks",
                "Implement stricter rate limiting during peak hours"
            ])
        
        # Model-specific recommendations
        model_perf = stats['model_performance']
        if model_perf:
            most_expensive = max(model_perf.items(), key=lambda x: x[1]['cost_per_token'])
            recommendations['savings_opportunities'].append(
                f"Consider alternatives to {most_expensive[0]} (highest cost per token)"
            )
        
        return recommendations


# Usage example and testing
if __name__ == "__main__":
    # Initialize rate limiter
    limiter = RateLimiter()
    optimizer = CreditOptimizer(limiter)
    
    print("🚀 RouteLL Rate Limiter and Optimizer initialized")
    print(f"📊 Current strategy: {limiter.current_strategy}")
    
    # Test rate limiting
    for i in range(5):
        can_proceed, reason, wait_time = limiter.can_make_request("route-llm", 100)
        print(f"Request {i+1}: {'✅' if can_proceed else '❌'} {reason}")
        
        if can_proceed:
            # Simulate request
            limiter.record_request(
                model="route-llm",
                tokens_used=150,
                response_time=1.5,
                success=True,
                credits_used=0.15
            )
        else:
            print(f"   Wait time: {wait_time:.1f} seconds")
    
    # Show usage stats
    stats = limiter.get_usage_stats()
    print("\n📈 Usage Statistics:")
    for key, value in stats.items():
        if key != 'model_performance':
            print(f"   {key}: {value}")
    
    # Test optimization
    messages = [{"role": "user", "content": "What is the meaning of life?"}]
    optimized = optimizer.optimize_request(messages, {'cost': 0.8, 'speed': 0.1, 'quality': 0.1})
    print(f"\n🎯 Optimized request: {optimized}")
    
    # Budget recommendations
    budget_rec = optimizer.get_budget_recommendations(1000.0)
    print(f"\n💰 Budget recommendations: {budget_rec}")