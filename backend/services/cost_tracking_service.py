#!/usr/bin/env python3
"""""""""
Cost Tracking Service
""""""
Manages API costs, tracks usage, \
"""

#     and provides budget controls for the marketing automation system.


Helps keep paid services off until affordable and monitors free API usage limits.

"""""""""
Cost Tracking Service
"""




import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class APIUsage:
    
"""Represents API usage data."""


    api_name: str
    service_type: str  # 'free', 'freemium', 'paid'
    requests_made: int
    requests_limit: int
    cost_per_request: float
    monthly_cost: float
    last_used: datetime
   

    
   
"""
    status: str  # 'active', 'disabled', 'limit_reached'
   """

    
   

@dataclass
class BudgetAlert:
    
"""Represents budget alert configuration."""


    alert_id: str
    api_name: str
    threshold_type: str  # 'cost', 'usage', 'percentage'
    threshold_value: float
    current_value: float
    alert_triggered: bool
   

    
   
"""
    created_at: datetime
   """

    
   

class CostTrackingService:
    """
    Service for tracking API costs and managing budgets.
    """
    
    def __init__(self, db_path: str = "cost_tracking.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()

        # Default budget limits
        self.monthly_budget = 100.0  # $100 default monthly budget
        self.free_tier_preferences = True  # Prefer free APIs when available

    def init_database(self):
        """
Initialize the cost tracking database.

        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
               
""""""

                CREATE TABLE IF NOT EXISTS api_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_name TEXT NOT NULL,
                        service_type TEXT NOT NULL,
                        requests_made INTEGER DEFAULT 0,
                        requests_limit INTEGER DEFAULT 0,
                        cost_per_request REAL DEFAULT 0.0,
                        monthly_cost REAL DEFAULT 0.0,
                        last_used TIMESTAMP,
                        status TEXT DEFAULT 'active',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP


#                 );

"""

                CREATE TABLE IF NOT EXISTS budget_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE NOT NULL,
                        api_name TEXT NOT NULL,
                        threshold_type TEXT NOT NULL,
                        threshold_value REAL NOT NULL,
                        current_value REAL DEFAULT 0.0,
                        alert_triggered BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 );
"""

#                 );



                CREATE TABLE IF NOT EXISTS cost_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                        api_name TEXT NOT NULL,
                        date DATE NOT NULL,
                        requests_count INTEGER DEFAULT 0,
                        cost_amount REAL DEFAULT 0.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 );

                CREATE INDEX IF NOT EXISTS idx_api_usage_name ON api_usage(api_name);
                CREATE INDEX IF NOT EXISTS idx_budget_alerts_api ON budget_alerts(api_name);
                CREATE INDEX IF NOT EXISTS idx_cost_history_date ON cost_history(date);
           
""""""

            

             
            
"""
             )
            """

             
            

    def track_api_usage(self, api_name: str, requests_count: int = 1, cost: float = 0.0):
        
"""Track API usage and update costs."""

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Update usage
                conn.execute(
                   

                    
                   
"""
                    INSERT OR REPLACE INTO api_usage
                    (api_name, requests_made, monthly_cost, last_used, updated_at)
                    VALUES (?,
                        COALESCE((SELECT requests_made FROM api_usage WHERE api_name = ?),
#     0) + ?,
                            COALESCE((SELECT monthly_cost FROM api_usage WHERE api_name = ?),
#     0) + ?,
#                             ?, ?)
                """
,

                    (
                        api_name,
                        api_name,
                        requests_count,
                        api_name,
                        cost,
                        datetime.now(),
                        datetime.now(),
                     ),
                
""""""

                 )
                

                 
                
""""""


                

               

                # Record daily history
               
""""""

                

                 
                
"""
                 )
                """

                 
                

                today = datetime.now().date()
                conn.execute(
                   
""""""

                    INSERT OR REPLACE INTO cost_history
                    (api_name, date, requests_count, cost_amount)
                    VALUES (?, ?,
                        COALESCE((SELECT requests_count FROM cost_history WHERE api_name = ? AND date = ?),
#     0) + ?,
                            COALESCE((SELECT cost_amount FROM cost_history WHERE api_name = ? AND date = ?),
#     0) + ?)
                
,
"""
                    (
                        api_name,
                        today,
                        api_name,
                        today,
                        requests_count,
                        api_name,
                        today,
                        cost,
                     ),
                """

                 
                

                 )
                
""""""

                # Check budget alerts
                self._check_budget_alerts(api_name)
                

                 
                
"""
                 )
                """"""
        except Exception as e:
            self.logger.error(f"Error tracking API usage for {api_name}: {e}")

    def get_monthly_costs(self) -> Dict[str, Any]:
        """
Get current monthly costs breakdown.

        try:
            
"""
            with sqlite3.connect(self.db_path) as conn:
            """

                cursor = conn.execute(
                   

                    
                   
"""
                    SELECT api_name, service_type, monthly_cost, requests_made, status
                    FROM api_usage
                    ORDER BY monthly_cost DESC
                """"""

                

                 
                
"""
                 )
                """"""
            with sqlite3.connect(self.db_path) as conn:
            """"""
                apis = []
                total_cost = 0.0
                free_apis = 0
                paid_apis = 0

                for row in cursor.fetchall():
                    api_data = {
                        "api_name": row[0],
                        "service_type": row[1],
                        "monthly_cost": row[2],
                        "requests_made": row[3],
                        "status": row[4],
                     }
                    apis.append(api_data)
                    total_cost += row[2]

                    if row[1] == "free":
                        free_apis += 1
                    else:
                        paid_apis += 1

                return {
                    "total_monthly_cost": total_cost,
                    "budget_remaining": max(0, self.monthly_budget - total_cost),
                    "budget_utilization": min(100, (total_cost / self.monthly_budget) * 100),
                    "free_apis_count": free_apis,
                    "paid_apis_count": paid_apis,
                    "apis": apis,
                 }

        except Exception as e:
            self.logger.error(f"Error getting monthly costs: {e}")
            return {"total_monthly_cost": 0, "apis": []}

    def get_free_alternatives(self, service_category: str) -> List[Dict[str, Any]]:
        """Get free API alternatives for a service category."""
        free_alternatives = {
            "ai_language": [
                {
                    "name": "Hugging Face Transformers",
                    "type": "free",
                    "limit": "1000 requests/month",
                 },
                {"name": "Ollama Local", "type": "free", "limit": "unlimited (local)"},
                {"name": "OpenAI Free Tier", "type": "freemium", "limit": "$5 credit"},
             ],
            "social_media": [
                {
                    "name": "YouTube Data API",
                    "type": "free",
                    "limit": "10000 units/day",
                 },
                {"name": "Twitter Basic", "type": "free", "limit": "500k tweets/month"},
                {
                    "name": "Instagram Basic Display",
                    "type": "free",
                    "limit": "200 requests/hour",
                 },
             ],
            "email": [
                {"name": "Mailgun Free", "type": "free", "limit": "5000 emails/month"},
                {"name": "SendGrid Free", "type": "free", "limit": "100 emails/day"},
                {
                    "name": "SMTP.js",
                    "type": "free",
                    "limit": "unlimited (self - hosted)",
                 },
             ],
            "analytics": [
                {"name": "Google Analytics", "type": "free", "limit": "10M hits/month"},
                {
                    "name": "Plausible Community",
                    "type": "free",
                    "limit": "unlimited (self - hosted)",
                 },
                {
                    "name": "Matomo Cloud Free",
                    "type": "free",
                    "limit": "30k actions/month",
                 },
             ],
         }

        return free_alternatives.get(service_category, [])

    def set_budget_alert(self, api_name: str, threshold_type: str, threshold_value: float):
        """
Set up budget alert for an API.

        
"""
        try:
        """
            alert_id = f"{api_name}_{threshold_type}_{int(threshold_value)}"
        """

        try:
        

       
""""""

            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                   

                    
                   
"""
                    INSERT OR REPLACE INTO budget_alerts
                    (alert_id, api_name, threshold_type, threshold_value, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """
,

                    (
                        alert_id,
                        api_name,
                        threshold_type,
                        threshold_value,
                        datetime.now(),
                     ),
                
""""""

                 )
                

                 
                
"""
            self.logger.info(
                f"Budget alert set for {api_name}: {threshold_type} >= {threshold_value}"
             )
                """

                 
                

                 )
                
""""""
        except Exception as e:
            self.logger.error(f"Error setting budget alert: {e}")

    def _check_budget_alerts(self, api_name: str):
        """
Check if any budget alerts should be triggered.

        try:
            with sqlite3.connect(self.db_path) as conn:
               
""""""

                # Get current usage
               

                
               
"""
                cursor = conn.execute(
                    "SELECT monthly_cost, requests_made FROM api_usage WHERE api_name = ?",
                    (api_name,),
                 )
               """

                
               

                # Get current usage
               
""""""
                usage_data = cursor.fetchone()
                if not usage_data:
                    return

                monthly_cost, requests_made = usage_data

                # Check alerts
                cursor = conn.execute(
                    "SELECT alert_id, threshold_type, threshold_value FROM budget_alerts WHERE api_name = ? AND alert_triggered = FALSE",
                    (api_name,),
                 )

                for alert_id, threshold_type, threshold_value in cursor.fetchall():
                    should_trigger = False
                    current_value = 0

                    if threshold_type == "cost" and monthly_cost >= threshold_value:
                        should_trigger = True
                        current_value = monthly_cost
                    elif threshold_type == "usage" and requests_made >= threshold_value:
                        should_trigger = True
                        current_value = requests_made
                    elif threshold_type == "percentage":
                        budget_percentage = (monthly_cost / self.monthly_budget) * 100
                        if budget_percentage >= threshold_value:
                            should_trigger = True
                            current_value = budget_percentage

                    if should_trigger:
                        # Trigger alert
                        conn.execute(
                            "UPDATE budget_alerts SET alert_triggered = TRUE, current_value = ?, updated_at = ? WHERE alert_id = ?",
                            (current_value, datetime.now(), alert_id),
                         )

                        self.logger.warning(
                            f"Budget alert triggered for {api_name}: {threshold_type} reached {current_value} (threshold: {threshold_value})"
                         )

                        # Disable API if cost threshold exceeded
                        if threshold_type == "cost" and current_value >= threshold_value:
                            self.disable_api(
                                api_name,
                                f"Cost threshold exceeded: ${current_value:.2f}",
                             )

        except Exception as e:
            self.logger.error(f"Error checking budget alerts: {e}")

    def disable_api(self, api_name: str, reason: str = "Budget exceeded"):
        """Disable an API due to budget constraints."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE api_usage SET status = 'disabled', updated_at = ? WHERE api_name = ?",
                    (datetime.now(), api_name),
                 )

            self.logger.warning(f"API {api_name} disabled: {reason}")

        except Exception as e:
            self.logger.error(f"Error disabling API {api_name}: {e}")

    def enable_api(self, api_name: str):
        """Re - enable a disabled API."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE api_usage SET status = 'active', updated_at = ? WHERE api_name = ?",
                    (datetime.now(), api_name),
                 )

            self.logger.info(f"API {api_name} enabled")

        except Exception as e:
            self.logger.error(f"Error enabling API {api_name}: {e}")

    def get_cost_recommendations(self) -> List[Dict[str, Any]]:
        """
Get cost optimization recommendations.

       
""""""

        recommendations = []
       

        
       
"""
        try:
       """

        
       

        recommendations = []
       
""""""
            costs = self.get_monthly_costs()

            # High cost APIs
            for api in costs["apis"]:
                if api["monthly_cost"] > 20:
                    recommendations.append(
                        {
                            "type": "cost_reduction",
                            "api_name": api["api_name"],
                            "message": f"Consider switching to free alternative for {api['api_name']} (current cost: ${api['monthly_cost']:.2f}/month)",
                            "priority": "high",
                         }
                     )

            # Budget utilization
            if costs["budget_utilization"] > 80:
                recommendations.append(
                    {
                        "type": "budget_warning",
                        "message": f"Budget utilization at {costs['budget_utilization']:.1f}% - consider disabling non - essential paid APIs",
                        "priority": "high",
                     }
                 )

            # Free tier suggestions
            if costs["paid_apis_count"] > costs["free_apis_count"]:
                recommendations.append(
                    {
                        "type": "free_tier",
                        "message": "Consider using more free tier APIs to reduce costs",
                        "priority": "medium",
                     }
                 )

        except Exception as e:
            self.logger.error(f"Error generating cost recommendations: {e}")

        return recommendations

    def export_cost_report(self) -> Dict[str, Any]:
        """
Export comprehensive cost report.

        
"""
        try:
        """

            costs = self.get_monthly_costs()
        

        try:
        
""""""

            
           

            recommendations = self.get_cost_recommendations()
           
""""""

            # Get historical data
            with sqlite3.connect(self.db_path) as conn:
           

            
           
"""
            recommendations = self.get_cost_recommendations()
           """

            
           

                cursor = conn.execute(
                   
""""""
                    SELECT date, SUM(cost_amount) as daily_cost
                    FROM cost_history
                    WHERE date >= date('now', '-30 days')
                    GROUP BY date
                    ORDER BY date
                """"""

                

                 
                
"""
                 )
                """"""
                daily_costs = [{"date": row[0], "cost": row[1]} for row in cursor.fetchall()]

            return {
                "report_date": datetime.now().isoformat(),
                "monthly_summary": costs,
                "recommendations": recommendations,
                "daily_costs": daily_costs,
                "budget_status": {
                    "monthly_budget": self.monthly_budget,
                    "spent": costs["total_monthly_cost"],
                    "remaining": costs["budget_remaining"],
                    "utilization_percentage": costs["budget_utilization"],
                 },
             }

        except Exception as e:
            self.logger.error(f"Error exporting cost report: {e}")
            return {}


# CLI interface for cost tracking
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Cost Tracking Service CLI")
    parser.add_argument(
        "--action",
        choices=["track", "report", "alert", "disable", "enable"],
        required=True,
     )
    parser.add_argument("--api - name", help="API name")
    parser.add_argument("--requests", type=int, default=1, help="Number of requests")
    parser.add_argument("--cost", type=float, default=0.0, help="Cost amount")
    parser.add_argument(
        "--threshold - type",
        choices=["cost", "usage", "percentage"],
        help="Alert threshold type",
     )
    parser.add_argument("--threshold - value", type=float, help="Alert threshold value")

    args = parser.parse_args()

    service = CostTrackingService()

    if args.action == "track" and args.api_name:
        service.track_api_usage(args.api_name, args.requests, args.cost)
        print(f"Tracked usage for {args.api_name}: {args.requests} requests, ${args.cost}")

    elif args.action == "report":
        report = service.export_cost_report()
        print(json.dumps(report, indent=2, default=str))

    elif args.action == "alert" and args.api_name and args.threshold_type and args.threshold_value:
        service.set_budget_alert(args.api_name, args.threshold_type, args.threshold_value)
        print(f"Budget alert set for {args.api_name}")

    elif args.action == "disable" and args.api_name:
        service.disable_api(args.api_name)
        print(f"API {args.api_name} disabled")

    elif args.action == "enable" and args.api_name:
        service.enable_api(args.api_name)
        print(f"API {args.api_name} enabled")

    else:
        parser.print_help()