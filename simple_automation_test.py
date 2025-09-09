#!/usr/bin/env python3
"""
Simple Automation Systems Validation Test

This script performs focused tests on the core automation systems:
- Database integrity checks
- Agent initialization validation
- Core functionality testing

Author: TRAE.AI System
Version: 1.0.0
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

class SimpleAutomationValidator:
    """Simple validation for automation systems"""
    
    def __init__(self):
        self.test_results = []
        self.passed = 0
        self.failed = 0
        
        # Set environment for testing
        os.environ['TRAE_MASTER_KEY'] = 'test123'
        
    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        if success:
            self.passed += 1
            logger.info(f"✅ {test_name}: PASSED - {message}")
        else:
            self.failed += 1
            logger.error(f"❌ {test_name}: FAILED - {message}")
    
    def test_database_files(self):
        """Test database file existence and integrity"""
        databases = [
            "/Users/thomasbrianreynolds/online production/data/performance_analytics.db",
            "/Users/thomasbrianreynolds/online production/collaboration_outreach.db"
        ]
        
        for db_path in databases:
            db_name = Path(db_path).name
            try:
                if not Path(db_path).exists():
                    self.log_result(f"database_exists_{db_name}", False, f"Database file not found: {db_path}")
                    continue
                
                # Test database integrity
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                result = cursor.fetchone()[0]
                
                # Get table count
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                conn.close()
                
                if result == "ok":
                    self.log_result(f"database_integrity_{db_name}", True, f"Database OK with {len(tables)} tables")
                else:
                    self.log_result(f"database_integrity_{db_name}", False, f"Integrity check failed: {result}")
                    
            except Exception as e:
                self.log_result(f"database_test_{db_name}", False, f"Database test failed: {e}")
    
    def test_agent_imports(self):
        """Test critical agent imports"""
        agents_to_test = [
            ('base_agents', 'backend.agents.base_agents'),
            ('specialized_agents', 'backend.agents.specialized_agents'),
            ('monetization_services', 'backend.agents.monetization_services_agent'),
            ('collaboration_outreach', 'backend.agents.collaboration_outreach_agent'),
            ('evolution_agent', 'backend.agents.evolution_agent'),
            ('financial_agent', 'backend.agents.financial_agent')
        ]
        
        for agent_name, module_path in agents_to_test:
            try:
                __import__(module_path)
                self.log_result(f"import_{agent_name}", True, f"Successfully imported {module_path}")
            except ImportError as e:
                self.log_result(f"import_{agent_name}", False, f"Import failed: {e}")
            except Exception as e:
                self.log_result(f"import_{agent_name}", False, f"Unexpected error: {e}")
    
    def test_collaboration_agent_basic(self):
        """Test basic collaboration agent functionality"""
        try:
            from backend.agents.collaboration_outreach_agent import CollaborationOutreachAgent
            
            agent = CollaborationOutreachAgent()
            
            # Test capabilities
            capabilities = [cap.value for cap in agent.capabilities]
            if 'marketing' in capabilities and 'execution' in capabilities:
                self.log_result("collaboration_capabilities", True, f"Agent has required capabilities: {capabilities}")
            else:
                self.log_result("collaboration_capabilities", False, f"Missing required capabilities: {capabilities}")
            
            # Test creator discovery (non-async)
            creators = agent.discover_creators('tech', 'youtube', 10000)
            if creators and len(creators) > 0:
                self.log_result("collaboration_discovery", True, f"Found {len(creators)} creators")
            else:
                self.log_result("collaboration_discovery", False, "No creators found")
                
        except Exception as e:
            self.log_result("collaboration_agent_test", False, f"Agent test failed: {e}")
    
    def test_monetization_agent_basic(self):
        """Test basic monetization agent functionality"""
        try:
            print("DEBUG: Starting monetization agent test")
            from backend.agents.monetization_services_agent import MonetizationServicesAgent
            
            print("DEBUG: Imported MonetizationServicesAgent")
            # Initialize agent
            try:
                agent = MonetizationServicesAgent()
                print(f"DEBUG: Agent initialized successfully, type: {type(agent)}, agent: {agent}")
                print(f"DEBUG: Agent has attributes: {dir(agent) if agent else 'None'}")
            except Exception as init_error:
                print(f"DEBUG: Error during agent initialization: {init_error}")
                raise init_error
            
            # Test capabilities
            print("DEBUG: Testing capabilities")
            try:
                capabilities = agent.capabilities
                print(f"DEBUG: capabilities type: {type(capabilities)}, value: {capabilities}")
            except Exception as cap_error:
                print(f"DEBUG: Error getting capabilities: {cap_error}")
                raise cap_error
            if capabilities and len(capabilities) > 0:
                self.log_result("monetization_capabilities", True, f"Agent has {len(capabilities)} capabilities")
            else:
                self.log_result("monetization_capabilities", False, "No capabilities found")
            
            # Test service packages
            try:
                packages = agent.get_service_packages()
                print(f"DEBUG: packages type: {type(packages)}, value: {packages}")
                if packages and isinstance(packages, dict) and packages.get('packages'):
                    package_count = packages.get('total_packages', 0)
                    self.log_result("monetization_packages", True, f"Found {package_count} service packages")
                else:
                    self.log_result("monetization_packages", False, f"No service packages found. Got: {packages}")
            except Exception as pkg_error:
                print(f"DEBUG: Error in get_service_packages: {pkg_error}")
                self.log_result("monetization_packages", False, f"Error getting packages: {pkg_error}")
                
        except Exception as e:
            self.log_result("monetization_agent_test", False, f"Agent test failed: {e}")
    
    def test_evolution_agent_basic(self):
        """Test basic evolution agent functionality"""
        try:
            from backend.agents.evolution_agent import EvolutionAgent
            
            agent = EvolutionAgent(config={})
            
            # Test capabilities
            capabilities = agent.capabilities
            expected_caps = ['trend_monitoring', 'format_detection', 'self_improvement']
            
            found_caps = [cap for cap in expected_caps if cap in capabilities]
            if len(found_caps) >= 2:
                self.log_result("evolution_capabilities", True, f"Agent has key capabilities: {found_caps}")
            else:
                self.log_result("evolution_capabilities", False, f"Missing key capabilities. Found: {capabilities}")
            
            # Test status
            status = agent.get_status()
            if status and 'agent_type' in status:
                self.log_result("evolution_status", True, f"Agent status available: {status.get('agent_type')}")
            else:
                self.log_result("evolution_status", False, "Agent status not available")
                
        except Exception as e:
            self.log_result("evolution_agent_test", False, f"Agent test failed: {e}")
    
    def test_file_structure(self):
        """Test critical file structure"""
        critical_files = [
            "/Users/thomasbrianreynolds/online production/backend/agents/base_agents.py",
            "/Users/thomasbrianreynolds/online production/backend/agents/specialized_agents.py",
            "/Users/thomasbrianreynolds/online production/backend/agents/monetization_services_agent.py",
            "/Users/thomasbrianreynolds/online production/backend/agents/collaboration_outreach_agent.py",
            "/Users/thomasbrianreynolds/online production/backend/agents/evolution_agent.py",
            "/Users/thomasbrianreynolds/online production/backend/agents/financial_agent.py"
        ]
        
        for file_path in critical_files:
            file_name = Path(file_path).name
            if Path(file_path).exists():
                file_size = Path(file_path).stat().st_size
                self.log_result(f"file_exists_{file_name}", True, f"File exists ({file_size} bytes)")
            else:
                self.log_result(f"file_exists_{file_name}", False, f"File missing: {file_path}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        logger.info("🚀 Starting Simple Automation Systems Validation")
        logger.info("=" * 60)
        
        # Run tests in order
        self.test_file_structure()
        self.test_database_files()
        self.test_agent_imports()
        self.test_collaboration_agent_basic()
        self.test_monetization_agent_basic()
        self.test_evolution_agent_basic()
        
        # Generate summary and return results
        return self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📊 VALIDATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Tests: {total}")
        logger.info(f"Passed: {self.passed} ✅")
        logger.info(f"Failed: {self.failed} ❌")
        logger.info(f"Success Rate: {success_rate:.1f}%")
        logger.info("")
        
        if self.failed > 0:
            logger.info("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    logger.info(f"  - {result['test']}: {result['message']}")
            logger.info("")
        
        # Production readiness assessment
        if success_rate >= 90:
            logger.info("🎉 PRODUCTION READINESS: EXCELLENT")
            status = "READY"
        elif success_rate >= 75:
            logger.info("⚠️  PRODUCTION READINESS: GOOD - Minor issues")
            status = "MOSTLY_READY"
        elif success_rate >= 50:
            logger.info("🔧 PRODUCTION READINESS: NEEDS WORK")
            status = "NEEDS_WORK"
        else:
            logger.info("🚨 PRODUCTION READINESS: CRITICAL ISSUES")
            status = "NOT_READY"
        
        logger.info("=" * 60)
        
        return {
            'total_tests': total,
            'passed': self.passed,
            'failed': self.failed,
            'success_rate': success_rate,
            'status': status,
            'production_ready': success_rate >= 75
        }

def main():
    """Main validation execution"""
    validator = SimpleAutomationValidator()
    results = validator.run_all_tests()
    
    # Exit with appropriate code
    if results['production_ready']:
        print(f"\n✅ Automation systems validation completed successfully!")
        print(f"Status: {results['status']} ({results['success_rate']:.1f}% success rate)")
        sys.exit(0)
    else:
        print(f"\n❌ Automation systems validation found issues.")
        print(f"Status: {results['status']} ({results['success_rate']:.1f}% success rate)")
        sys.exit(1)

if __name__ == "__main__":
    main()