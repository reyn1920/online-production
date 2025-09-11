import sqlite3
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class WorldBible:
    """SQLite-based data persistence for niche discovery and trend analysis"""
    
    def __init__(self, db_path: str = "world_bible.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database with required tables"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Niches table - core niche tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS niches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    category TEXT,
                    discovery_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    viability_score REAL DEFAULT 0.0,
                    market_size_estimate INTEGER DEFAULT 0,
                    competition_level TEXT DEFAULT 'unknown',
                    metadata TEXT  -- JSON field for additional data
                )
            """)
            
            # Trends table - trend data from various sources
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trends (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    source TEXT NOT NULL,  -- 'google_trends', 'reddit', 'github', 'arxiv', 'youtube'
                    keyword TEXT NOT NULL,
                    trend_score REAL DEFAULT 0.0,
                    volume INTEGER DEFAULT 0,
                    growth_rate REAL DEFAULT 0.0,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_snapshot TEXT,  -- JSON field for raw data
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Market analysis table - comprehensive market data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_addressable_market REAL DEFAULT 0.0,
                    serviceable_addressable_market REAL DEFAULT 0.0,
                    competition_density REAL DEFAULT 0.0,
                    entry_barriers TEXT,
                    monetization_potential REAL DEFAULT 0.0,
                    risk_factors TEXT,  -- JSON array
                    opportunities TEXT,  -- JSON array
                    analysis_data TEXT,  -- JSON field for detailed analysis
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Content opportunities table - specific content ideas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS content_opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    content_type TEXT NOT NULL,  -- 'video', 'article', 'course', 'product'
                    title TEXT NOT NULL,
                    description TEXT,
                    target_keywords TEXT,  -- JSON array
                    estimated_demand INTEGER DEFAULT 0,
                    difficulty_score REAL DEFAULT 0.0,
                    monetization_potential REAL DEFAULT 0.0,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'identified',
                    metadata TEXT,  -- JSON field
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Competitor analysis table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS competitors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    name TEXT NOT NULL,
                    platform TEXT NOT NULL,  -- 'youtube', 'website', 'etsy', etc.
                    url TEXT,
                    follower_count INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    content_frequency TEXT,
                    strengths TEXT,  -- JSON array
                    weaknesses TEXT,  -- JSON array
                    last_analyzed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_data TEXT,  -- JSON field
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Revenue streams table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS revenue_streams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    stream_type TEXT NOT NULL,  -- 'affiliate', 'product', 'service', 'ads', 'sponsorship'
                    platform TEXT,  -- 'etsy', 'gumroad', 'youtube', etc.
                    estimated_revenue REAL DEFAULT 0.0,
                    setup_difficulty REAL DEFAULT 0.0,
                    time_to_revenue INTEGER DEFAULT 0,  -- days
                    requirements TEXT,  -- JSON array
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT,  -- JSON field
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Analytics snapshots table - periodic data snapshots
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS analytics_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    niche_id INTEGER,
                    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    google_trends_data TEXT,  -- JSON
                    reddit_data TEXT,  -- JSON
                    github_data TEXT,  -- JSON
                    arxiv_data TEXT,  -- JSON
                    youtube_data TEXT,  -- JSON
                    combined_score REAL DEFAULT 0.0,
                    trend_direction TEXT DEFAULT 'stable',  -- 'rising', 'falling', 'stable'
                    FOREIGN KEY (niche_id) REFERENCES niches (id)
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_niches_name ON niches (name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_niches_category ON niches (category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_niches_viability ON niches (viability_score DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_niche_source ON trends (niche_id, source)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trends_timestamp ON trends (timestamp DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_opportunities_niche ON content_opportunities (niche_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_competitors_niche ON competitors (niche_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analytics_snapshots_date ON analytics_snapshots (snapshot_date DESC)")
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    # Niche management methods
    def create_niche(
        self,
        name: str,
        description: str = "",
        category: str = "",
        metadata: Dict[str, Any] = None
    ) -> int:
        """Create a new niche entry"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO niches (name, description, category, metadata)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                description,
                category,
                json.dumps(metadata or {})
            ))
            
            niche_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Created niche '{name}' with ID {niche_id}")
            return niche_id
    
    def get_niche(self, niche_id: int) -> Optional[Dict[str, Any]]:
        """Get niche by ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM niches WHERE id = ?", (niche_id,))
            row = cursor.fetchone()
            
            if row:
                niche = dict(row)
                niche['metadata'] = json.loads(niche['metadata'] or '{}')
                return niche
            
            return None
    
    def get_niche_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get niche by name"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM niches WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                niche = dict(row)
                niche['metadata'] = json.loads(niche['metadata'] or '{}')
                return niche
            
            return None
    
    def update_niche_viability(
        self,
        niche_id: int,
        viability_score: float,
        market_size_estimate: int = None,
        competition_level: str = None
    ) -> bool:
        """Update niche viability metrics"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            update_fields = ["viability_score = ?", "last_updated = CURRENT_TIMESTAMP"]
            params = [viability_score]
            
            if market_size_estimate is not None:
                update_fields.append("market_size_estimate = ?")
                params.append(market_size_estimate)
            
            if competition_level is not None:
                update_fields.append("competition_level = ?")
                params.append(competition_level)
            
            params.append(niche_id)
            
            cursor.execute(f"""
                UPDATE niches 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, params)
            
            success = cursor.rowcount > 0
            conn.commit()
            
            return success
    
    def list_niches(
        self,
        category: str = None,
        min_viability: float = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List niches with optional filtering"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM niches WHERE 1=1"
            params = []
            
            if category:
                query += " AND category = ?"
                params.append(category)
            
            if min_viability is not None:
                query += " AND viability_score >= ?"
                params.append(min_viability)
            
            query += " ORDER BY viability_score DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            niches = []
            for row in rows:
                niche = dict(row)
                niche['metadata'] = json.loads(niche['metadata'] or '{}')
                niches.append(niche)
            
            return niches
    
    # Trend data methods
    def record_trend_data(
        self,
        niche_id: int,
        source: str,
        keyword: str,
        trend_score: float,
        volume: int = 0,
        growth_rate: float = 0.0,
        data_snapshot: Dict[str, Any] = None
    ) -> int:
        """Record trend data for a niche"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO trends (
                    niche_id, source, keyword, trend_score, volume, 
                    growth_rate, data_snapshot
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                niche_id,
                source,
                keyword,
                trend_score,
                volume,
                growth_rate,
                json.dumps(data_snapshot or {})
            ))
            
            trend_id = cursor.lastrowid
            conn.commit()
            
            return trend_id
    
    def get_trend_data(
        self,
        niche_id: int,
        source: str = None,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """Get trend data for a niche"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = f"""
                SELECT * FROM trends 
                WHERE niche_id = ? AND timestamp >= datetime('now', '-{days_back} days')
            """
            
            params = [niche_id]
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            trends = []
            for row in rows:
                trend = dict(row)
                trend['data_snapshot'] = json.loads(trend['data_snapshot'] or '{}')
                trends.append(trend)
            
            return trends
    
    # Market analysis methods
    def record_market_analysis(
        self,
        niche_id: int,
        tam: float = 0.0,
        sam: float = 0.0,
        competition_density: float = 0.0,
        entry_barriers: str = "",
        monetization_potential: float = 0.0,
        risk_factors: List[str] = None,
        opportunities: List[str] = None,
        analysis_data: Dict[str, Any] = None
    ) -> int:
        """Record market analysis for a niche"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO market_analysis (
                    niche_id, total_addressable_market, serviceable_addressable_market,
                    competition_density, entry_barriers, monetization_potential,
                    risk_factors, opportunities, analysis_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                niche_id,
                tam,
                sam,
                competition_density,
                entry_barriers,
                monetization_potential,
                json.dumps(risk_factors or []),
                json.dumps(opportunities or []),
                json.dumps(analysis_data or {})
            ))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            
            return analysis_id
    
    def get_market_analysis(self, niche_id: int) -> Optional[Dict[str, Any]]:
        """Get latest market analysis for a niche"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM market_analysis 
                WHERE niche_id = ? 
                ORDER BY analysis_date DESC 
                LIMIT 1
            """, (niche_id,))
            
            row = cursor.fetchone()
            
            if row:
                analysis = dict(row)
                analysis['risk_factors'] = json.loads(analysis['risk_factors'] or '[]')
                analysis['opportunities'] = json.loads(analysis['opportunities'] or '[]')
                analysis['analysis_data'] = json.loads(analysis['analysis_data'] or '{}')
                return analysis
            
            return None
    
    # Content opportunities methods
    def add_content_opportunity(
        self,
        niche_id: int,
        content_type: str,
        title: str,
        description: str = "",
        target_keywords: List[str] = None,
        estimated_demand: int = 0,
        difficulty_score: float = 0.0,
        monetization_potential: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> int:
        """Add a content opportunity"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO content_opportunities (
                    niche_id, content_type, title, description, target_keywords,
                    estimated_demand, difficulty_score, monetization_potential, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                niche_id,
                content_type,
                title,
                description,
                json.dumps(target_keywords or []),
                estimated_demand,
                difficulty_score,
                monetization_potential,
                json.dumps(metadata or {})
            ))
            
            opportunity_id = cursor.lastrowid
            conn.commit()
            
            return opportunity_id
    
    def get_content_opportunities(
        self,
        niche_id: int,
        content_type: str = None,
        min_potential: float = None
    ) -> List[Dict[str, Any]]:
        """Get content opportunities for a niche"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM content_opportunities WHERE niche_id = ?"
            params = [niche_id]
            
            if content_type:
                query += " AND content_type = ?"
                params.append(content_type)
            
            if min_potential is not None:
                query += " AND monetization_potential >= ?"
                params.append(min_potential)
            
            query += " ORDER BY monetization_potential DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            opportunities = []
            for row in rows:
                opportunity = dict(row)
                opportunity['target_keywords'] = json.loads(opportunity['target_keywords'] or '[]')
                opportunity['metadata'] = json.loads(opportunity['metadata'] or '{}')
                opportunities.append(opportunity)
            
            return opportunities
    
    # Analytics and reporting methods
    def create_analytics_snapshot(
        self,
        niche_id: int,
        google_trends_data: Dict[str, Any] = None,
        reddit_data: Dict[str, Any] = None,
        github_data: Dict[str, Any] = None,
        arxiv_data: Dict[str, Any] = None,
        youtube_data: Dict[str, Any] = None,
        combined_score: float = 0.0,
        trend_direction: str = 'stable'
    ) -> int:
        """Create an analytics snapshot"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO analytics_snapshots (
                    niche_id, google_trends_data, reddit_data, github_data,
                    arxiv_data, youtube_data, combined_score, trend_direction
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                niche_id,
                json.dumps(google_trends_data or {}),
                json.dumps(reddit_data or {}),
                json.dumps(github_data or {}),
                json.dumps(arxiv_data or {}),
                json.dumps(youtube_data or {}),
                combined_score,
                trend_direction
            ))
            
            snapshot_id = cursor.lastrowid
            conn.commit()
            
            return snapshot_id
    
    def get_niche_dashboard(self, niche_id: int) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a niche"""
        niche = self.get_niche(niche_id)
        if not niche:
            return {}
        
        # Get latest trends
        recent_trends = self.get_trend_data(niche_id, days_back=7)
        
        # Get market analysis
        market_analysis = self.get_market_analysis(niche_id)
        
        # Get content opportunities
        content_opportunities = self.get_content_opportunities(niche_id)
        
        # Get latest analytics snapshot
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM analytics_snapshots 
                WHERE niche_id = ? 
                ORDER BY snapshot_date DESC 
                LIMIT 1
            """, (niche_id,))
            
            snapshot_row = cursor.fetchone()
            latest_snapshot = None
            
            if snapshot_row:
                latest_snapshot = dict(snapshot_row)
                for field in ['google_trends_data', 'reddit_data', 'github_data', 'arxiv_data', 'youtube_data']:
                    latest_snapshot[field] = json.loads(latest_snapshot[field] or '{}')
        
        return {
            'niche': niche,
            'recent_trends': recent_trends,
            'market_analysis': market_analysis,
            'content_opportunities': content_opportunities,
            'latest_snapshot': latest_snapshot,
            'dashboard_generated': datetime.utcnow().isoformat()
        }
    
    def get_top_niches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing niches by viability score"""
        return self.list_niches(min_viability=0.0, limit=limit)
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Clean up old data to maintain database performance"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean old trends
            cursor.execute(
                "DELETE FROM trends WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            trends_deleted = cursor.rowcount
            
            # Clean old analytics snapshots
            cursor.execute(
                "DELETE FROM analytics_snapshots WHERE snapshot_date < ?",
                (cutoff_date.isoformat(),)
            )
            snapshots_deleted = cursor.rowcount
            
            conn.commit()
            
            return {
                'trends_deleted': trends_deleted,
                'snapshots_deleted': snapshots_deleted,
                'cutoff_date': cutoff_date.isoformat()
            }