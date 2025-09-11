#!/usr/bin/env python3
"""
Cloud Software Integration Manager

This module manages the integration and monitoring of cloud software products
including Lingo Blaster, Captionizer, Thumbnail Blaster, Speechelo, Voice Generator,
Background Music, Voiceover Cash Machine, Training, and Scriptelo.

Features:
- Database integration management
- Software status monitoring
- Usage tracking and analytics
- Health checks and diagnostics
- Integration testing
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SoftwareStatus:
    """Data class for software status information"""
    software_name: str
    display_name: str
    category: str
    status: str
    integration_type: str
    health_status: str
    last_health_check: Optional[datetime]
    installation_status: str
    license_type: str
    subscription_status: Optional[str]
    capabilities: List[str]
    notes: str

class CloudSoftwareManager:
    """Manages cloud software integration and monitoring"""
    
    def __init__(self, db_path: str = "right_perspective.db"):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Ensure the database and cloud software tables exist"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if cloud_software table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='cloud_software'
                """)
                
                if not cursor.fetchone():
                    logger.info("Cloud software table not found. Creating from schema...")
                    self.create_cloud_software_tables(conn)
                else:
                    logger.info("Cloud software tables already exist")
                    
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def create_cloud_software_tables(self, conn: sqlite3.Connection):
        """Create cloud software tables directly"""
        try:
            # Create cloud_software table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cloud_software (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL CHECK (category IN ('voice_generation', 'video_editing', 'thumbnail_creation', 'script_writing', 'background_music', 'training', 'automation', 'bonus_tools')),
                    provider TEXT,
                    version TEXT,
                    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance', 'deprecated')),
                    integration_type TEXT CHECK (integration_type IN ('api', 'rpa', 'manual', 'webhook', 'cli')),
                    api_endpoint TEXT,
                    authentication_method TEXT CHECK (authentication_method IN ('api_key', 'oauth2', 'username_password', 'token', 'none')),
                    credentials_stored BOOLEAN DEFAULT FALSE,
                    rate_limit_per_hour INTEGER,
                    rate_limit_per_day INTEGER,
                    current_usage_hour INTEGER DEFAULT 0,
                    current_usage_day INTEGER DEFAULT 0,
                    last_usage_reset TIMESTAMP,
                    configuration JSON,
                    capabilities JSON,
                    dependencies JSON,
                    installation_status TEXT DEFAULT 'not_installed' CHECK (installation_status IN ('not_installed', 'installing', 'installed', 'failed', 'updating')),
                    installation_path TEXT,
                    license_type TEXT CHECK (license_type IN ('free', 'paid', 'subscription', 'one_time', 'trial')),
                    license_expires_at TIMESTAMP,
                    subscription_status TEXT CHECK (subscription_status IN ('active', 'expired', 'cancelled', 'trial', 'none')),
                    monthly_cost DECIMAL(10,2),
                    annual_cost DECIMAL(10,2),
                    usage_metrics JSON,
                    performance_metrics JSON,
                    last_health_check TIMESTAMP,
                    health_status TEXT DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
                    documentation_url TEXT,
                    support_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by TEXT,
                    notes TEXT,
                    metadata JSON
                )
            """)
            
            # Create software_usage_logs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS software_usage_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    usage_type TEXT NOT NULL,
                    operation TEXT,
                    input_data JSON,
                    output_data JSON,
                    execution_time_ms INTEGER,
                    status TEXT CHECK (status IN ('success', 'failed', 'timeout', 'cancelled')),
                    error_message TEXT,
                    cost DECIMAL(10,4),
                    user_id TEXT,
                    session_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSON,
                    FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
                )
            """)
            
            # Create software_integration_status table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS software_integration_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    software_id INTEGER NOT NULL,
                    check_type TEXT NOT NULL,
                    status TEXT CHECK (status IN ('pass', 'fail', 'warning', 'skip')),
                    message TEXT,
                    response_time_ms INTEGER,
                    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checked_by TEXT,
                    details JSON,
                    FOREIGN KEY (software_id) REFERENCES cloud_software(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_name ON cloud_software(software_name)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_category ON cloud_software(category)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_status ON cloud_software(status)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_integration_type ON cloud_software(integration_type)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_installation ON cloud_software(installation_status)",
                "CREATE INDEX IF NOT EXISTS idx_cloud_software_health ON cloud_software(health_status)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_software_id ON software_usage_logs(software_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_type ON software_usage_logs(usage_type)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_timestamp ON software_usage_logs(timestamp)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_status ON software_usage_logs(status)",
                "CREATE INDEX IF NOT EXISTS idx_software_usage_user ON software_usage_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_software_id ON software_integration_status(software_id)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_type ON software_integration_status(check_type)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_status ON software_integration_status(status)",
                "CREATE INDEX IF NOT EXISTS idx_software_integration_checked ON software_integration_status(checked_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(index_sql)
            
            # Insert the cloud software products
            software_products = [
                ('lingo_blaster', 'Lingo Blaster', 'automation', 'Lingo Blaster Inc', 'active', 'rpa', 'username_password', 
                 '["language_processing", "content_translation", "multilingual_support"]', 'subscription', 'system', 'Language processing and translation tool'),
                
                ('captionizer', 'Captionizer', 'video_editing', 'Captionizer Pro', 'active', 'api', 'api_key', 
                 '["subtitle_generation", "caption_creation", "video_processing"]', 'subscription', 'system', 'Automated caption and subtitle generation'),
                
                ('thumbnail_blaster', 'Thumbnail Blaster', 'thumbnail_creation', 'Thumbnail Blaster', 'active', 'rpa', 'username_password', 
                 '["thumbnail_creation", "image_editing", "template_processing"]', 'subscription', 'system', 'Automated thumbnail creation and editing'),
                
                ('speechelo', 'Speechelo', 'voice_generation', 'Speechelo', 'active', 'rpa', 'username_password', 
                 '["text_to_speech", "voice_synthesis", "audio_generation"]', 'one_time', 'system', 'Text-to-speech voice generation software'),
                
                ('voice_generator', 'Voice Generator', 'voice_generation', 'Voice Generator Pro', 'active', 'api', 'api_key', 
                 '["voice_synthesis", "custom_voices", "audio_processing"]', 'subscription', 'system', 'Advanced voice generation and synthesis'),
                
                ('background_music', 'Background Music', 'background_music', 'Music Library Pro', 'active', 'api', 'api_key', 
                 '["music_library", "royalty_free_music", "audio_mixing"]', 'subscription', 'system', 'Royalty-free background music library'),
                
                ('voiceover_cash_machine', 'Voiceover Cash Machine', 'bonus_tools', 'Voiceover Cash Machine', 'active', 'manual', 'none', 
                 '["voiceover_training", "business_strategies", "monetization"]', 'one_time', 'system', 'BONUS: Voiceover business training and strategies'),
                
                ('training', 'Training', 'training', 'Training Academy', 'active', 'manual', 'none', 
                 '["video_training", "tutorials", "skill_development"]', 'subscription', 'system', 'Comprehensive training modules and tutorials'),
                
                ('scriptelo', 'Scriptelo', 'script_writing', 'Scriptelo', 'active', 'rpa', 'username_password', 
                 '["script_generation", "content_writing", "template_processing"]', 'subscription', 'system', 'Automated script writing and content generation')
            ]
            
            conn.executemany("""
                INSERT OR REPLACE INTO cloud_software (
                    software_name, display_name, category, provider, status, integration_type, 
                    authentication_method, capabilities, license_type, created_by, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, software_products)
            
            conn.commit()
            logger.info("Cloud software tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating cloud software tables: {e}")
            raise
    
    def get_all_software(self) -> List[SoftwareStatus]:
        """Get all cloud software with their current status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT software_name, display_name, category, status, 
                           integration_type, health_status, last_health_check,
                           installation_status, license_type, subscription_status,
                           capabilities, notes
                    FROM cloud_software
                    ORDER BY category, display_name
                """)
                
                software_list = []
                for row in cursor.fetchall():
                    capabilities = json.loads(row[10]) if row[10] else []
                    last_check = datetime.fromisoformat(row[6]) if row[6] else None
                    
                    software_list.append(SoftwareStatus(
                        software_name=row[0],
                        display_name=row[1],
                        category=row[2],
                        status=row[3],
                        integration_type=row[4],
                        health_status=row[5],
                        last_health_check=last_check,
                        installation_status=row[7],
                        license_type=row[8],
                        subscription_status=row[9],
                        capabilities=capabilities,
                        notes=row[11]
                    ))
                
                return software_list
                
        except Exception as e:
            logger.error(f"Error retrieving software list: {e}")
            return []
    
    def update_software_status(self, software_name: str, status: str, 
                             health_status: str = None, notes: str = None):
        """Update software status and health information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                update_fields = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
                params = [status]
                
                if health_status:
                    update_fields.append("health_status = ?")
                    update_fields.append("last_health_check = CURRENT_TIMESTAMP")
                    params.append(health_status)
                
                if notes:
                    update_fields.append("notes = ?")
                    params.append(notes)
                
                params.append(software_name)
                
                cursor.execute(f"""
                    UPDATE cloud_software 
                    SET {', '.join(update_fields)}
                    WHERE software_name = ?
                """, params)
                
                conn.commit()
                logger.info(f"Updated status for {software_name}: {status}")
                
        except Exception as e:
            logger.error(f"Error updating software status: {e}")
    
    def log_software_usage(self, software_name: str, usage_type: str, 
                          operation: str, status: str = "success", 
                          execution_time_ms: int = None, error_message: str = None):
        """Log software usage for tracking and analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get software ID
                cursor.execute("SELECT id FROM cloud_software WHERE software_name = ?", (software_name,))
                result = cursor.fetchone()
                if not result:
                    logger.error(f"Software {software_name} not found")
                    return
                
                software_id = result[0]
                
                cursor.execute("""
                    INSERT INTO software_usage_logs 
                    (software_id, usage_type, operation, status, execution_time_ms, error_message)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (software_id, usage_type, operation, status, execution_time_ms, error_message))
                
                conn.commit()
                logger.info(f"Logged usage for {software_name}: {operation}")
                
        except Exception as e:
            logger.error(f"Error logging software usage: {e}")
    
    def perform_health_checks(self) -> Dict[str, str]:
        """Perform health checks on all active software"""
        results = {}
        software_list = self.get_all_software()
        
        for software in software_list:
            if software.status == 'active':
                health_status = self._check_software_health(software)
                results[software.software_name] = health_status
                self.update_software_status(
                    software.software_name, 
                    software.status, 
                    health_status
                )
        
        return results
    
    def _check_software_health(self, software: SoftwareStatus) -> str:
        """Check health of individual software"""
        try:
            # Basic health check logic based on integration type
            if software.integration_type == 'api':
                # For API integrations, we would check endpoint availability
                # This is a placeholder - actual implementation would make HTTP requests
                return 'healthy'  # Placeholder
            
            elif software.integration_type == 'rpa':
                # For RPA integrations, check if automation tools are accessible
                # This is a placeholder - actual implementation would check RPA status
                return 'healthy'  # Placeholder
            
            elif software.integration_type == 'manual':
                # Manual integrations are always considered healthy if active
                return 'healthy'
            
            else:
                return 'unknown'
                
        except Exception as e:
            logger.error(f"Health check failed for {software.software_name}: {e}")
            return 'unhealthy'
    
    def get_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration status report"""
        software_list = self.get_all_software()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_software': len(software_list),
            'by_category': {},
            'by_status': {},
            'by_integration_type': {},
            'health_summary': {},
            'software_details': []
        }
        
        for software in software_list:
            # Count by category
            if software.category not in report['by_category']:
                report['by_category'][software.category] = 0
            report['by_category'][software.category] += 1
            
            # Count by status
            if software.status not in report['by_status']:
                report['by_status'][software.status] = 0
            report['by_status'][software.status] += 1
            
            # Count by integration type
            if software.integration_type not in report['by_integration_type']:
                report['by_integration_type'][software.integration_type] = 0
            report['by_integration_type'][software.integration_type] += 1
            
            # Count by health status
            if software.health_status not in report['health_summary']:
                report['health_summary'][software.health_status] = 0
            report['health_summary'][software.health_status] += 1
            
            # Add software details
            report['software_details'].append({
                'name': software.display_name,
                'category': software.category,
                'status': software.status,
                'integration_type': software.integration_type,
                'health_status': software.health_status,
                'capabilities': software.capabilities,
                'license_type': software.license_type
            })
        
        return report
    
    def print_integration_status(self):
        """Print formatted integration status to console"""
        software_list = self.get_all_software()
        
        print("\n" + "="*80)
        print("CLOUD SOFTWARE INTEGRATION STATUS")
        print("="*80)
        
        if not software_list:
            print("No cloud software found in database.")
            return
        
        # Group by category
        by_category = {}
        for software in software_list:
            if software.category not in by_category:
                by_category[software.category] = []
            by_category[software.category].append(software)
        
        for category, software_items in by_category.items():
            print(f"\n{category.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for software in software_items:
                status_icon = "✅" if software.status == 'active' else "❌"
                health_icon = {
                    'healthy': "🟢",
                    'degraded': "🟡", 
                    'unhealthy': "🔴",
                    'unknown': "⚪"
                }.get(software.health_status, "⚪")
                
                print(f"  {status_icon} {health_icon} {software.display_name}")
                print(f"      Integration: {software.integration_type}")
                print(f"      License: {software.license_type}")
                print(f"      Capabilities: {', '.join(software.capabilities)}")
                if software.notes:
                    print(f"      Notes: {software.notes}")
                print()
        
        # Summary
        active_count = sum(1 for s in software_list if s.status == 'active')
        healthy_count = sum(1 for s in software_list if s.health_status == 'healthy')
        
        print(f"\nSUMMARY:")
        print(f"  Total Software: {len(software_list)}")
        print(f"  Active: {active_count}")
        print(f"  Healthy: {healthy_count}")
        print("="*80)

def main():
    """Main function to demonstrate cloud software management"""
    manager = CloudSoftwareManager()
    
    print("Cloud Software Integration Manager")
    print("Initializing database and checking integration status...")
    
    # Print current status
    manager.print_integration_status()
    
    # Perform health checks
    print("\nPerforming health checks...")
    health_results = manager.perform_health_checks()
    
    for software_name, health_status in health_results.items():
        print(f"  {software_name}: {health_status}")
    
    # Generate report
    report = manager.get_integration_report()
    print(f"\nIntegration report generated at {report['timestamp']}")
    print(f"Total software products: {report['total_software']}")
    
    # Save report to file
    report_path = f"cloud_software_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Detailed report saved to: {report_path}")

if __name__ == "__main__":
    main()