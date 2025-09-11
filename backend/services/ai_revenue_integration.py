#!/usr/bin/env python3
"""
AI Revenue Integration Service

Integrates AI platform costs and usage metrics with the existing revenue tracking system.
Provides comprehensive cost analysis, ROI calculations, and budget management for
ChatGPT, Gemini, and Abacus AI platforms.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal

# Import existing services
try:
    from backend.services.cost_tracking_service import CostTrackingService
except ImportError:
    CostTrackingService = None

try:
    from core_ai_integration import CoreAIIntegration, core_ai
except ImportError:
    CoreAIIntegration = None
    core_ai = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class AIRevenueMetrics:
    """AI platform revenue and cost metrics"""
    
    platform: str
    total_requests: int
    total_cost: float
    cost_per_request: float
    monthly_usage: int
    monthly_cost: float
    roi_percentage: float
    revenue_generated: float
    profit_margin: float
    last_updated: datetime


@dataclass
class AIBudgetAlert:
    """AI budget alert configuration"""
    
    platform: str
    alert_type: str  # 'cost_threshold', 'usage_limit', 'roi_decline'
    threshold_value: float
    current_value: float
    alert_triggered: bool
    message: str
    created_at: datetime


class AIRevenueIntegration:
    """Service for integrating AI platform costs with revenue tracking"""
    
    def __init__(self, cost_tracker: Optional[CostTrackingService] = None):
        self.cost_tracker = cost_tracker or (CostTrackingService() if CostTrackingService else None)
        self.core_ai = core_ai
        self.logger = logging.getLogger(__name__)
        
        # AI platform configurations
        self.ai_platforms = {
            'chatgpt': {
                'name': 'ChatGPT',
                'url': 'https://chatgpt.com/',
                'cost_per_request': 0.002,
                'monthly_budget': 50.0,
                'revenue_multiplier': 15.0  # Expected revenue per dollar spent
            },
            'gemini': {
                'name': 'Gemini',
                'url': 'https://gemini.google.com/app',
                'cost_per_request': 0.001,
                'monthly_budget': 30.0,
                'revenue_multiplier': 20.0
            },
            'abacus': {
                'name': 'Abacus AI',
                'url': 'https://apps.abacus.ai/chatllm/?appId=1024a18ebe',
                'cost_per_request': 0.0015,
                'monthly_budget': 40.0,
                'revenue_multiplier': 18.0
            }
        }
        
        # Initialize budget alerts
        self.budget_alerts = []
        self._setup_default_alerts()
    
    def _setup_default_alerts(self):
        """Setup default budget alerts for AI platforms"""
        for platform_key, config in self.ai_platforms.items():
            # Cost threshold alert (80% of budget)
            self.budget_alerts.append(AIBudgetAlert(
                platform=platform_key,
                alert_type='cost_threshold',
                threshold_value=config['monthly_budget'] * 0.8,
                current_value=0.0,
                alert_triggered=False,
                message=f"{config['name']} approaching monthly budget limit",
                created_at=datetime.now()
            ))
            
            # ROI decline alert
            self.budget_alerts.append(AIBudgetAlert(
                platform=platform_key,
                alert_type='roi_decline',
                threshold_value=10.0,  # ROI below 10x
                current_value=0.0,
                alert_triggered=False,
                message=f"{config['name']} ROI declining below threshold",
                created_at=datetime.now()
            ))
    
    async def track_ai_usage(self, platform: str, requests_count: int = 1, 
                           revenue_generated: float = 0.0) -> Dict[str, Any]:
        """Track AI platform usage and calculate costs"""
        try:
            if platform not in self.ai_platforms:
                raise ValueError(f"Unknown AI platform: {platform}")
            
            platform_config = self.ai_platforms[platform]
            cost = requests_count * platform_config['cost_per_request']
            
            # Track with cost tracking service
            if self.cost_tracker:
                self.cost_tracker.track_api_usage(
                    api_name=f"ai_{platform}",
                    requests_count=requests_count,
                    cost=cost
                )
            
            # Update core AI integration if available
            if self.core_ai:
                # This would update the core AI system's metrics
                pass
            
            # Calculate ROI
            roi = (revenue_generated / cost) if cost > 0 else 0
            
            # Check budget alerts
            await self._check_budget_alerts(platform, cost, roi)
            
            return {
                'platform': platform,
                'requests_tracked': requests_count,
                'cost_incurred': cost,
                'revenue_generated': revenue_generated,
                'roi': roi,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error tracking AI usage for {platform}: {e}")
            return {'error': str(e)}
    
    async def _check_budget_alerts(self, platform: str, current_cost: float, current_roi: float):
        """Check and trigger budget alerts if necessary"""
        for alert in self.budget_alerts:
            if alert.platform != platform:
                continue
            
            if alert.alert_type == 'cost_threshold':
                monthly_cost = await self._get_monthly_cost(platform)
                if monthly_cost >= alert.threshold_value and not alert.alert_triggered:
                    alert.alert_triggered = True
                    alert.current_value = monthly_cost
                    await self._send_alert(alert)
            
            elif alert.alert_type == 'roi_decline':
                if current_roi < alert.threshold_value and not alert.alert_triggered:
                    alert.alert_triggered = True
                    alert.current_value = current_roi
                    await self._send_alert(alert)
    
    async def _get_monthly_cost(self, platform: str) -> float:
        """Get monthly cost for a specific AI platform"""
        try:
            if self.cost_tracker:
                # Get cost data from cost tracking service
                # This would need to be implemented in the cost tracking service
                pass
            
            # Fallback: calculate from core AI integration
            if self.core_ai:
                cost_analytics = self.core_ai.get_cost_analytics()
                platform_costs = cost_analytics.get('platform_breakdown', {})
                platform_data = platform_costs.get(platform, {})
                return platform_data.get('total_cost', 0.0)
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error getting monthly cost for {platform}: {e}")
            return 0.0
    
    async def _send_alert(self, alert: AIBudgetAlert):
        """Send budget alert notification"""
        try:
            self.logger.warning(f"AI Budget Alert: {alert.message} - {alert.platform} - Current: {alert.current_value}")
            
            # Here you could integrate with email notifications, Slack, etc.
            # For now, just log the alert
            
        except Exception as e:
            self.logger.error(f"Error sending alert: {e}")
    
    async def get_ai_revenue_metrics(self) -> Dict[str, AIRevenueMetrics]:
        """Get comprehensive AI revenue metrics for all platforms"""
        metrics = {}
        
        try:
            for platform_key, config in self.ai_platforms.items():
                # Get cost data
                monthly_cost = await self._get_monthly_cost(platform_key)
                
                # Get usage data from core AI integration
                usage_data = {}
                if self.core_ai:
                    cost_analytics = self.core_ai.get_cost_analytics()
                    platform_costs = cost_analytics.get('platform_breakdown', {})
                    usage_data = platform_costs.get(platform_key, {})
                
                total_requests = usage_data.get('usage_count', 0)
                total_cost = usage_data.get('total_cost', 0.0)
                cost_per_request = usage_data.get('cost_per_request', config['cost_per_request'])
                
                # Calculate revenue (estimated based on multiplier)
                revenue_generated = total_cost * config['revenue_multiplier']
                profit_margin = ((revenue_generated - total_cost) / revenue_generated * 100) if revenue_generated > 0 else 0
                roi_percentage = (revenue_generated / total_cost * 100) if total_cost > 0 else 0
                
                metrics[platform_key] = AIRevenueMetrics(
                    platform=config['name'],
                    total_requests=total_requests,
                    total_cost=total_cost,
                    cost_per_request=cost_per_request,
                    monthly_usage=total_requests,  # Assuming current period is monthly
                    monthly_cost=monthly_cost,
                    roi_percentage=roi_percentage,
                    revenue_generated=revenue_generated,
                    profit_margin=profit_margin,
                    last_updated=datetime.now()
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error getting AI revenue metrics: {e}")
            return {}
    
    async def get_ai_cost_summary(self) -> Dict[str, Any]:
        """Get AI cost summary for revenue tracking integration"""
        try:
            metrics = await self.get_ai_revenue_metrics()
            
            total_cost = sum(m.total_cost for m in metrics.values())
            total_revenue = sum(m.revenue_generated for m in metrics.values())
            total_requests = sum(m.total_requests for m in metrics.values())
            
            return {
                'total_ai_cost': total_cost,
                'total_ai_revenue': total_revenue,
                'total_ai_requests': total_requests,
                'net_profit': total_revenue - total_cost,
                'overall_roi': (total_revenue / total_cost * 100) if total_cost > 0 else 0,
                'platform_breakdown': {k: asdict(v) for k, v in metrics.items()},
                'cost_efficiency': total_cost / max(1, total_requests),
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AI cost summary: {e}")
            return {'error': str(e)}
    
    async def optimize_ai_spending(self) -> Dict[str, Any]:
        """Provide AI spending optimization recommendations"""
        try:
            metrics = await self.get_ai_revenue_metrics()
            recommendations = []
            
            for platform_key, metric in metrics.items():
                config = self.ai_platforms[platform_key]
                
                # Check if platform is over budget
                if metric.monthly_cost > config['monthly_budget']:
                    recommendations.append({
                        'platform': metric.platform,
                        'type': 'budget_exceeded',
                        'message': f"{metric.platform} has exceeded monthly budget by ${metric.monthly_cost - config['monthly_budget']:.2f}",
                        'action': 'Consider reducing usage or increasing budget'
                    })
                
                # Check ROI efficiency
                if metric.roi_percentage < 1000:  # Less than 10x ROI
                    recommendations.append({
                        'platform': metric.platform,
                        'type': 'low_roi',
                        'message': f"{metric.platform} ROI is {metric.roi_percentage:.1f}%, below optimal threshold",
                        'action': 'Review usage patterns and optimize prompts'
                    })
                
                # Check cost efficiency
                avg_cost_per_request = sum(m.cost_per_request for m in metrics.values()) / len(metrics)
                if metric.cost_per_request > avg_cost_per_request * 1.5:
                    recommendations.append({
                        'platform': metric.platform,
                        'type': 'high_cost_per_request',
                        'message': f"{metric.platform} cost per request is above average",
                        'action': 'Consider switching to more cost-effective platform for similar tasks'
                    })
            
            return {
                'recommendations': recommendations,
                'total_potential_savings': sum(m.monthly_cost * 0.1 for m in metrics.values()),  # 10% potential savings
                'optimization_score': len([r for r in recommendations if r['type'] != 'budget_exceeded']),
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error optimizing AI spending: {e}")
            return {'error': str(e)}
    
    async def export_ai_revenue_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Export comprehensive AI revenue report for specified date range"""
        try:
            metrics = await self.get_ai_revenue_metrics()
            cost_summary = await self.get_ai_cost_summary()
            optimization = await self.optimize_ai_spending()
            
            return {
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'executive_summary': {
                    'total_ai_investment': cost_summary.get('total_ai_cost', 0),
                    'total_ai_revenue': cost_summary.get('total_ai_revenue', 0),
                    'net_profit': cost_summary.get('net_profit', 0),
                    'roi_percentage': cost_summary.get('overall_roi', 0)
                },
                'platform_performance': metrics,
                'cost_analysis': cost_summary,
                'optimization_recommendations': optimization,
                'budget_alerts': [asdict(alert) for alert in self.budget_alerts if alert.alert_triggered],
                'generated_at': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error exporting AI revenue report: {e}")
            return {'error': str(e)}


# Global AI revenue integration instance
ai_revenue_integration = AIRevenueIntegration()


# Convenience functions for easy integration
async def track_ai_platform_usage(platform: str, requests: int = 1, revenue: float = 0.0):
    """Track AI platform usage"""
    return await ai_revenue_integration.track_ai_usage(platform, requests, revenue)


async def get_ai_revenue_summary():
    """Get AI revenue summary"""
    return await ai_revenue_integration.get_ai_cost_summary()


async def get_ai_optimization_recommendations():
    """Get AI spending optimization recommendations"""
    return await ai_revenue_integration.optimize_ai_spending()


if __name__ == "__main__":
    # CLI interface for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="AI Revenue Integration CLI")
    parser.add_argument("--action", choices=["track", "summary", "optimize", "report"], required=True)
    parser.add_argument("--platform", choices=["chatgpt", "gemini", "abacus"], help="AI platform")
    parser.add_argument("--requests", type=int, default=1, help="Number of requests")
    parser.add_argument("--revenue", type=float, default=0.0, help="Revenue generated")
    
    args = parser.parse_args()
    
    async def main():
        integration = AIRevenueIntegration()
        
        if args.action == "track" and args.platform:
            result = await integration.track_ai_usage(args.platform, args.requests, args.revenue)
            print(json.dumps(result, indent=2, default=str))
        
        elif args.action == "summary":
            result = await integration.get_ai_cost_summary()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.action == "optimize":
            result = await integration.optimize_ai_spending()
            print(json.dumps(result, indent=2, default=str))
        
        elif args.action == "report":
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            result = await integration.export_ai_revenue_report(start_date, end_date)
            print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())