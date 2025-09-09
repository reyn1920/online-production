#!/usr/bin/env python3
"""
TRAE.AI Research Agent - The Intelligence Officer

The system's eyes and ears that runs the "Hypocrisy Engine," finds new
zero-cost APIs and affiliates, and incorporates Autonomous Trend Forecasting
using pytrends to preempt market shifts.
"""

import json
import sqlite3
import logging
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import queue
import re
from urllib.parse import urljoin, urlparse

try:
    from pytrends.request import TrendReq
except ImportError:
    TrendReq = None
    print("Warning: pytrends not installed. Install with: pip install pytrends")

from .base_agents import BaseAgent


@dataclass
class TrendData:
    """Trend analysis data"""
    keyword: str
    interest_score: int
    trend_direction: str  # 'rising', 'falling', 'stable'
    related_queries: List[str]
    geographic_data: Dict[str, int]
    timestamp: datetime
    confidence: float


@dataclass
class APIDiscovery:
    """Discovered API information"""
    api_name: str
    base_url: str
    description: str
    endpoints: List[str]
    authentication_type: str
    cost_model: str  # 'free', 'freemium', 'paid'
    rate_limits: Dict[str, Any]
    discovered_at: datetime
    quality_score: float


@dataclass
class HypocrisyAlert:
    """Hypocrisy detection result"""
    target: str
    statement_1: str
    statement_2: str
    contradiction_type: str
    confidence: float
    evidence_urls: List[str]
    detected_at: datetime


@dataclass
class MarketIntelligence:
    """Market intelligence report"""
    sector: str
    key_trends: List[str]
    opportunities: List[str]
    threats: List[str]
    competitor_analysis: Dict[str, Any]
    market_sentiment: float
    generated_at: datetime


class ResearchAgent(BaseAgent):
    """The Intelligence Officer - Autonomous research and trend analysis"""
    
    def __init__(self, db_path: str = "data/right_perspective.db"):
        super().__init__("ResearchAgent")
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.initialize_database()
        
        # Initialize pytrends
        self.pytrends = None
        if TrendReq:
            try:
                self.pytrends = TrendReq(hl='en-US', tz=360)
            except Exception as e:
                self.logger.warning(f"Failed to initialize pytrends: {e}")
        
        # Research parameters
        self.trend_check_interval = 3600  # 1 hour
        self.api_discovery_interval = 86400  # 24 hours
        self.hypocrisy_scan_interval = 7200  # 2 hours
        
        # Monitoring threads
        self.monitoring_active = False
        self.trend_thread = None
        self.api_thread = None
        self.hypocrisy_thread = None
        
        # Research queues
        self.research_queue = queue.Queue()
        
        # Known API directories
        self.api_directories = [
            "https://api.publicapis.org/entries",
            "https://github.com/public-apis/public-apis",
            "https://rapidapi.com/search/"
        ]
        
        # Hypocrisy detection patterns
        self.contradiction_patterns = [
            (r"never\s+\w+", r"always\s+\w+"),
            (r"impossible", r"definitely\s+possible"),
            (r"will\s+never", r"will\s+definitely"),
            (r"completely\s+against", r"fully\s+support")
        ]
    
    def initialize_database(self):
        """Initialize research database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS trend_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    interest_score INTEGER NOT NULL,
                    trend_direction TEXT NOT NULL,
                    related_queries TEXT NOT NULL,
                    geographic_data TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    confidence REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_discoveries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_name TEXT NOT NULL,
                    base_url TEXT NOT NULL,
                    description TEXT NOT NULL,
                    endpoints TEXT NOT NULL,
                    authentication_type TEXT NOT NULL,
                    cost_model TEXT NOT NULL,
                    rate_limits TEXT NOT NULL,
                    discovered_at TIMESTAMP NOT NULL,
                    quality_score REAL NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS hypocrisy_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target TEXT NOT NULL,
                    statement_1 TEXT NOT NULL,
                    statement_2 TEXT NOT NULL,
                    contradiction_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    evidence_urls TEXT NOT NULL,
                    detected_at TIMESTAMP NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS market_intelligence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sector TEXT NOT NULL,
                    key_trends TEXT NOT NULL,
                    opportunities TEXT NOT NULL,
                    threats TEXT NOT NULL,
                    competitor_analysis TEXT NOT NULL,
                    market_sentiment REAL NOT NULL,
                    generated_at TIMESTAMP NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS research_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_type TEXT NOT NULL,
                    target_value TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    last_researched TIMESTAMP,
                    created_at TIMESTAMP NOT NULL
                )
            """)
    
    def start_monitoring(self):
        """Start autonomous research monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        # Start trend monitoring
        self.trend_thread = threading.Thread(target=self._trend_monitor, daemon=True)
        self.trend_thread.start()
        
        # Start API discovery
        self.api_thread = threading.Thread(target=self._api_discovery_monitor, daemon=True)
        self.api_thread.start()
        
        # Start hypocrisy scanning
        self.hypocrisy_thread = threading.Thread(target=self._hypocrisy_monitor, daemon=True)
        self.hypocrisy_thread.start()
        
        self.logger.info("Research monitoring started")
    
    def stop_monitoring(self):
        """Stop research monitoring"""
        self.monitoring_active = False
        self.logger.info("Research monitoring stopped")
    
    def analyze_trends(self, keywords: List[str], timeframe: str = 'today 3-m') -> List[TrendData]:
        """Analyze trends for given keywords"""
        if not self.pytrends:
            self.logger.warning("pytrends not available")
            return []
        
        trend_data = []
        
        try:
            # Build payload
            self.pytrends.build_payload(keywords, cat=0, timeframe=timeframe, geo='', gprop='')
            
            # Get interest over time
            interest_over_time = self.pytrends.interest_over_time()
            
            # Get related queries
            related_queries = self.pytrends.related_queries()
            
            # Get interest by region
            interest_by_region = self.pytrends.interest_by_region(resolution='COUNTRY')
            
            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    # Calculate trend direction
                    values = interest_over_time[keyword].values
                    if len(values) >= 2:
                        recent_avg = values[-5:].mean() if len(values) >= 5 else values[-1]
                        older_avg = values[:-5].mean() if len(values) >= 10 else values[0]
                        
                        if recent_avg > older_avg * 1.1:
                            trend_direction = 'rising'
                        elif recent_avg < older_avg * 0.9:
                            trend_direction = 'falling'
                        else:
                            trend_direction = 'stable'
                    else:
                        trend_direction = 'stable'
                    
                    # Get related queries for this keyword
                    related = []
                    if keyword in related_queries and related_queries[keyword]['top'] is not None:
                        related = related_queries[keyword]['top']['query'].tolist()[:10]
                    
                    # Get geographic data
                    geo_data = {}
                    if keyword in interest_by_region.columns:
                        geo_data = interest_by_region[keyword].to_dict()
                    
                    trend_data.append(TrendData(
                        keyword=keyword,
                        interest_score=int(values[-1]) if len(values) > 0 else 0,
                        trend_direction=trend_direction,
                        related_queries=related,
                        geographic_data=geo_data,
                        timestamp=datetime.now(),
                        confidence=0.8
                    ))
            
            # Save trend data
            self._save_trend_data(trend_data)
            
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {e}")
        
        return trend_data
    
    def discover_apis(self, search_terms: List[str] = None) -> List[APIDiscovery]:
        """Discover new APIs based on search terms"""
        if search_terms is None:
            search_terms = ['free api', 'public api', 'rest api', 'json api']
        
        discoveries = []
        
        try:
            # Search public API directory
            response = requests.get("https://api.publicapis.org/entries", timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                for entry in data.get('entries', [])[:50]:  # Limit to 50 entries
                    # Filter for free APIs
                    if entry.get('Auth', '').lower() in ['', 'no', 'none'] or 'free' in entry.get('Description', '').lower():
                        discovery = APIDiscovery(
                            api_name=entry.get('API', 'Unknown'),
                            base_url=entry.get('Link', ''),
                            description=entry.get('Description', ''),
                            endpoints=[],  # Would need to discover these
                            authentication_type=entry.get('Auth', 'none'),
                            cost_model='free' if entry.get('Auth', '').lower() in ['', 'no', 'none'] else 'unknown',
                            rate_limits={},
                            discovered_at=datetime.now(),
                            quality_score=self._calculate_api_quality_score(entry)
                        )
                        discoveries.append(discovery)
            
            # Save discoveries
            self._save_api_discoveries(discoveries)
            
        except Exception as e:
            self.logger.error(f"Error discovering APIs: {e}")
        
        return discoveries
    
    def run_hypocrisy_engine(self, targets: List[str]) -> List[HypocrisyAlert]:
        """Run hypocrisy detection on targets"""
        alerts = []
        
        for target in targets:
            try:
                # Search for statements by target
                statements = self._collect_statements(target)
                
                # Analyze for contradictions
                contradictions = self._detect_contradictions(statements)
                
                for contradiction in contradictions:
                    alert = HypocrisyAlert(
                        target=target,
                        statement_1=contradiction['statement_1'],
                        statement_2=contradiction['statement_2'],
                        contradiction_type=contradiction['type'],
                        confidence=contradiction['confidence'],
                        evidence_urls=contradiction['evidence_urls'],
                        detected_at=datetime.now()
                    )
                    alerts.append(alert)
                
            except Exception as e:
                self.logger.error(f"Error running hypocrisy engine for {target}: {e}")
        
        # Save alerts
        self._save_hypocrisy_alerts(alerts)
        
        return alerts
    
    def generate_market_intelligence(self, sector: str) -> MarketIntelligence:
        """Generate comprehensive market intelligence report"""
        try:
            # Analyze trends for sector
            sector_keywords = self._get_sector_keywords(sector)
            trends = self.analyze_trends(sector_keywords)
            
            # Extract key trends
            key_trends = []
            opportunities = []
            threats = []
            
            for trend in trends:
                if trend.trend_direction == 'rising' and trend.interest_score > 50:
                    key_trends.append(f"{trend.keyword} (↑{trend.interest_score})")
                    opportunities.append(f"Growing interest in {trend.keyword}")
                elif trend.trend_direction == 'falling' and trend.interest_score < 30:
                    threats.append(f"Declining interest in {trend.keyword}")
            
            # Analyze competitors (placeholder)
            competitor_analysis = {
                'top_competitors': [],
                'market_share': {},
                'competitive_advantages': []
            }
            
            # Calculate market sentiment
            market_sentiment = self._calculate_market_sentiment(trends)
            
            intelligence = MarketIntelligence(
                sector=sector,
                key_trends=key_trends,
                opportunities=opportunities,
                threats=threats,
                competitor_analysis=competitor_analysis,
                market_sentiment=market_sentiment,
                generated_at=datetime.now()
            )
            
            # Save intelligence
            self._save_market_intelligence(intelligence)
            
            return intelligence
            
        except Exception as e:
            self.logger.error(f"Error generating market intelligence: {e}")
            return MarketIntelligence(
                sector=sector,
                key_trends=[],
                opportunities=[],
                threats=[],
                competitor_analysis={},
                market_sentiment=0.5,
                generated_at=datetime.now()
            )
    
    def _trend_monitor(self):
        """Monitor trends continuously"""
        while self.monitoring_active:
            try:
                # Get research targets
                targets = self._get_research_targets('trend')
                
                if targets:
                    keywords = [target['target_value'] for target in targets]
                    self.analyze_trends(keywords)
                
                time.sleep(self.trend_check_interval)
                
            except Exception as e:
                self.logger.error(f"Trend monitor error: {e}")
                time.sleep(self.trend_check_interval)
    
    def _api_discovery_monitor(self):
        """Monitor for new API discoveries"""
        while self.monitoring_active:
            try:
                # Discover new APIs
                self.discover_apis()
                
                time.sleep(self.api_discovery_interval)
                
            except Exception as e:
                self.logger.error(f"API discovery monitor error: {e}")
                time.sleep(self.api_discovery_interval)
    
    def _hypocrisy_monitor(self):
        """Monitor for hypocrisy detection"""
        while self.monitoring_active:
            try:
                # Get hypocrisy targets
                targets = self._get_research_targets('hypocrisy')
                
                if targets:
                    target_names = [target['target_value'] for target in targets]
                    self.run_hypocrisy_engine(target_names)
                
                time.sleep(self.hypocrisy_scan_interval)
                
            except Exception as e:
                self.logger.error(f"Hypocrisy monitor error: {e}")
                time.sleep(self.hypocrisy_scan_interval)
    
    def _collect_statements(self, target: str) -> List[Dict[str, Any]]:
        """Collect statements from a target (placeholder)"""
        # This would integrate with social media APIs, news APIs, etc.
        # Placeholder implementation
        return [
            {
                'text': f"Sample statement 1 from {target}",
                'url': 'https://example.com/1',
                'date': datetime.now() - timedelta(days=30)
            },
            {
                'text': f"Sample statement 2 from {target}",
                'url': 'https://example.com/2',
                'date': datetime.now() - timedelta(days=1)
            }
        ]
    
    def _detect_contradictions(self, statements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect contradictions in statements"""
        contradictions = []
        
        for i, stmt1 in enumerate(statements):
            for j, stmt2 in enumerate(statements[i+1:], i+1):
                # Check for pattern-based contradictions
                for pattern1, pattern2 in self.contradiction_patterns:
                    if (re.search(pattern1, stmt1['text'], re.IGNORECASE) and 
                        re.search(pattern2, stmt2['text'], re.IGNORECASE)):
                        
                        contradictions.append({
                            'statement_1': stmt1['text'],
                            'statement_2': stmt2['text'],
                            'type': 'direct',  # Fixed: use valid constraint value instead of 'pattern_contradiction'
                            'confidence': 0.7,
                            'evidence_urls': [stmt1['url'], stmt2['url']]
                        })
        
        return contradictions
    
    def _calculate_api_quality_score(self, api_entry: Dict[str, Any]) -> float:
        """Calculate quality score for discovered API"""
        score = 0.5  # Base score
        
        # Check for HTTPS
        if api_entry.get('Link', '').startswith('https://'):
            score += 0.2
        
        # Check for good description
        if len(api_entry.get('Description', '')) > 50:
            score += 0.1
        
        # Check for no auth (easier to use)
        if api_entry.get('Auth', '').lower() in ['', 'no', 'none']:
            score += 0.2
        
        return min(1.0, score)
    
    def _get_sector_keywords(self, sector: str) -> List[str]:
        """Get relevant keywords for a sector"""
        sector_keywords = {
            'technology': ['AI', 'machine learning', 'blockchain', 'cloud computing', 'cybersecurity'],
            'finance': ['fintech', 'cryptocurrency', 'digital banking', 'robo advisor', 'payment'],
            'health': ['telemedicine', 'digital health', 'wearables', 'health app', 'medical AI'],
            'education': ['edtech', 'online learning', 'e-learning', 'educational app', 'remote education'],
            'retail': ['e-commerce', 'online shopping', 'retail tech', 'omnichannel', 'digital retail']
        }
        
        return sector_keywords.get(sector.lower(), [sector])
    
    def _calculate_market_sentiment(self, trends: List[TrendData]) -> float:
        """Calculate overall market sentiment from trends"""
        if not trends:
            return 0.5
        
        rising_count = sum(1 for t in trends if t.trend_direction == 'rising')
        falling_count = sum(1 for t in trends if t.trend_direction == 'falling')
        total_count = len(trends)
        
        # Sentiment score based on trend directions
        sentiment = (rising_count - falling_count) / total_count
        return max(0, min(1, 0.5 + sentiment * 0.5))
    
    def _get_research_targets(self, target_type: str) -> List[Dict[str, Any]]:
        """Get research targets from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT target_value, priority, last_researched
                FROM research_targets
                WHERE target_type = ?
                ORDER BY priority DESC, last_researched ASC
                LIMIT 10
            """, (target_type,))
            
            return [{
                'target_value': row[0],
                'priority': row[1],
                'last_researched': row[2]
            } for row in cursor.fetchall()]
    
    def add_research_target(self, target_type: str, target_value: str, priority: int = 1):
        """Add research target"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO research_targets
                (target_type, target_value, priority, created_at)
                VALUES (?, ?, ?, ?)
            """, (target_type, target_value, priority, datetime.now().isoformat()))
    
    def _save_trend_data(self, trends: List[TrendData]):
        """Save trend data to database"""
        with sqlite3.connect(self.db_path) as conn:
            for trend in trends:
                conn.execute("""
                    INSERT INTO trend_data
                    (keyword, interest_score, trend_direction, related_queries,
                     geographic_data, timestamp, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    trend.keyword,
                    trend.interest_score,
                    trend.trend_direction,
                    json.dumps(trend.related_queries),
                    json.dumps(trend.geographic_data),
                    trend.timestamp.isoformat(),
                    trend.confidence
                ))
    
    def _save_api_discoveries(self, discoveries: List[APIDiscovery]):
        """Save API discoveries to database"""
        with sqlite3.connect(self.db_path) as conn:
            for discovery in discoveries:
                conn.execute("""
                    INSERT OR REPLACE INTO api_discoveries
                    (api_name, base_url, description, endpoints, authentication_type,
                     cost_model, rate_limits, discovered_at, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    discovery.api_name,
                    discovery.base_url,
                    discovery.description,
                    json.dumps(discovery.endpoints),
                    discovery.authentication_type,
                    discovery.cost_model,
                    json.dumps(discovery.rate_limits),
                    discovery.discovered_at.isoformat(),
                    discovery.quality_score
                ))
    
    def _save_hypocrisy_alerts(self, alerts: List[HypocrisyAlert]):
        """Save hypocrisy alerts to database"""
        with sqlite3.connect(self.db_path) as conn:
            for alert in alerts:
                conn.execute("""
                    INSERT INTO hypocrisy_alerts
                    (target, statement_1, statement_2, contradiction_type,
                     confidence, evidence_urls, detected_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.target,
                    alert.statement_1,
                    alert.statement_2,
                    alert.contradiction_type,
                    alert.confidence,
                    json.dumps(alert.evidence_urls),
                    alert.detected_at.isoformat()
                ))
    
    def _save_market_intelligence(self, intelligence: MarketIntelligence):
        """Save market intelligence to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO market_intelligence
                (sector, key_trends, opportunities, threats, competitor_analysis,
                 market_sentiment, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                intelligence.sector,
                json.dumps(intelligence.key_trends),
                json.dumps(intelligence.opportunities),
                json.dumps(intelligence.threats),
                json.dumps(intelligence.competitor_analysis),
                intelligence.market_sentiment,
                intelligence.generated_at.isoformat()
            ))
    
    def execute_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute research task"""
        task_type = task_data.get('type')
        
        if task_type == 'analyze_trends':
            keywords = task_data.get('keywords', [])
            trends = self.analyze_trends(keywords)
            return {
                'success': True,
                'trends': [asdict(t) for t in trends]
            }
        
        elif task_type == 'discover_apis':
            discoveries = self.discover_apis(task_data.get('search_terms'))
            return {
                'success': True,
                'discoveries': [asdict(d) for d in discoveries]
            }
        
        elif task_type == 'hypocrisy_scan':
            targets = task_data.get('targets', [])
            alerts = self.run_hypocrisy_engine(targets)
            return {
                'success': True,
                'alerts': [asdict(a) for a in alerts]
            }
        
        elif task_type == 'market_intelligence':
            sector = task_data.get('sector', 'technology')
            intelligence = self.generate_market_intelligence(sector)
            return {
                'success': True,
                'intelligence': asdict(intelligence)
            }
        
        elif task_type == 'start_monitoring':
            self.start_monitoring()
            return {'success': True}
        
        return {'success': False, 'error': f'Unknown task type: {task_type}'}


if __name__ == "__main__":
    # Test the Research Agent
    research_agent = ResearchAgent()
    
    # Add some research targets
    research_agent.add_research_target('trend', 'artificial intelligence', 3)
    research_agent.add_research_target('trend', 'machine learning', 2)
    research_agent.add_research_target('hypocrisy', 'tech_ceo_example', 1)
    
    # Test trend analysis
    if research_agent.pytrends:
        trends = research_agent.analyze_trends(['AI', 'machine learning'])
        print(f"Analyzed {len(trends)} trends")
        for trend in trends:
            print(f"- {trend.keyword}: {trend.interest_score} ({trend.trend_direction})")
    
    # Test API discovery
    apis = research_agent.discover_apis()
    print(f"Discovered {len(apis)} APIs")
    
    # Test market intelligence
    intelligence = research_agent.generate_market_intelligence('technology')
    print(f"Market Intelligence for {intelligence.sector}:")
    print(f"- Key trends: {len(intelligence.key_trends)}")
    print(f"- Opportunities: {len(intelligence.opportunities)}")
    print(f"- Market sentiment: {intelligence.market_sentiment:.2f}")
    
    # Start monitoring
    research_agent.start_monitoring()
    
    try:
        time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        research_agent.stop_monitoring()