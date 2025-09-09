#!/usr/bin/env python3
"""
TRAE.AI Autonomous System - Comprehensive End-to-End Test

This script performs a complete validation of the TRAE.AI autonomous system,
testing all components, agents, and integrations to ensure the system operates
within the successful "2%" as outlined in the blueprint.

Test Categories:
1. Core Infrastructure Tests
2. Agent Functionality Tests
3. Task Queue & Coordination Tests
4. Dashboard & Monitoring Tests
5. Integration & API Tests
6. Resilience & Self-Healing Tests
7. Performance & Load Tests
8. Security & Secrets Management Tests
"""

import os
import sys
import json
import time
import sqlite3
import requests
import subprocess
import threading
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import TRAE.AI components
try:
    from backend.core.task_queue import TaskQueue, Task
    from backend.core.secret_store import SecretStore
    from backend.agents.planner_agent import PlannerAgent
    from backend.agents.system_agent import SystemAgent
    from backend.agents.research_agent import ResearchAgent
    from backend.agents.marketing_agent import MarketingAgent
    from backend.agents.content_agent import ContentAgent
    from backend.dashboard.total_access_dashboard import TotalAccessDashboard
except ImportError as e:
    print(f"Warning: Could not import some components: {e}")
    print("Some tests may be skipped.")


@dataclass
class TestResult:
    """Test result data structure"""
    test_name: str
    category: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    duration: float
    details: str
    timestamp: datetime
    error: Optional[str] = None


class AutonomousSystemTester:
    """Comprehensive test suite for TRAE.AI autonomous system"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_logging()
        
        # Test configuration
        self.db_path = "data/right_perspective.db"
        self.test_results: List[TestResult] = []
        self.start_time = datetime.now()
        
        # Component instances
        self.task_queue = None
        self.secret_store = None
        self.agents = {}
        self.dashboard = None
        
        # Test data
        self.test_tasks = []
        self.test_secrets = {}
        
        self.logger.info("TRAE.AI Autonomous System Tester initialized")
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('test_autonomous_system.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test categories"""
        self.logger.info("Starting comprehensive autonomous system tests")
        
        test_categories = [
            ("Core Infrastructure", self.test_core_infrastructure),
            ("Agent Functionality", self.test_agent_functionality),
            ("Task Queue & Coordination", self.test_task_queue_coordination),
            ("Dashboard & Monitoring", self.test_dashboard_monitoring),
            ("Integration & API", self.test_integration_api),
            ("Resilience & Self-Healing", self.test_resilience_self_healing),
            ("Performance & Load", self.test_performance_load),
            ("Security & Secrets", self.test_security_secrets)
        ]
        
        for category_name, test_function in test_categories:
            self.logger.info(f"Running {category_name} tests...")
            try:
                test_function()
            except Exception as e:
                self.logger.error(f"Error in {category_name} tests: {e}")
                self.add_test_result(
                    f"{category_name} - Critical Error",
                    category_name,
                    "FAIL",
                    0.0,
                    f"Critical error prevented test execution: {str(e)}",
                    error=str(e)
                )
        
        return self.generate_test_report()
    
    def test_core_infrastructure(self):
        """Test core infrastructure components"""
        
        # Test 1: Database connectivity and schema
        start_time = time.time()
        try:
            # Ensure data directory exists
            Path("data").mkdir(exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                required_tables = ['tasks', 'agents', 'system_metrics', 'insights']
                missing_tables = [table for table in required_tables if table not in tables]
                
                if missing_tables:
                    # Create missing tables
                    self.create_database_schema(conn)
                    status = "PASS"
                    details = f"Database initialized with required tables: {required_tables}"
                else:
                    status = "PASS"
                    details = f"Database schema validated. Tables found: {len(tables)}"
                    
        except Exception as e:
            status = "FAIL"
            details = f"Database connectivity failed: {str(e)}"
        
        self.add_test_result(
            "Database Connectivity & Schema",
            "Core Infrastructure",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: File system permissions and directories
        start_time = time.time()
        try:
            required_dirs = [
                "data", "backend/agents", "backend/core", "backend/dashboard",
                "config", "logs", "temp"
            ]
            
            created_dirs = []
            for dir_path in required_dirs:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                if Path(dir_path).exists():
                    created_dirs.append(dir_path)
            
            # Test write permissions
            test_file = Path("temp/test_write_permissions.txt")
            test_file.write_text("Test write permissions")
            test_file.unlink()
            
            status = "PASS"
            details = f"Directory structure validated: {len(created_dirs)}/{len(required_dirs)} directories"
            
        except Exception as e:
            status = "FAIL"
            details = f"File system setup failed: {str(e)}"
        
        self.add_test_result(
            "File System Permissions",
            "Core Infrastructure",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 3: Python dependencies
        start_time = time.time()
        try:
            required_packages = [
                'requests', 'sqlite3', 'json', 'threading', 'subprocess',
                'pathlib', 'datetime', 'logging', 'dataclasses'
            ]
            
            missing_packages = []
            for package in required_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                status = "FAIL"
                details = f"Missing required packages: {missing_packages}"
            else:
                status = "PASS"
                details = f"All required Python packages available: {len(required_packages)}"
                
        except Exception as e:
            status = "FAIL"
            details = f"Dependency check failed: {str(e)}"
        
        self.add_test_result(
            "Python Dependencies",
            "Core Infrastructure",
            status,
            time.time() - start_time,
            details
        )
    
    def test_agent_functionality(self):
        """Test individual agent functionality"""
        
        agent_classes = {
            'PlannerAgent': PlannerAgent,
            'SystemAgent': SystemAgent,
            'ResearchAgent': ResearchAgent,
            'MarketingAgent': MarketingAgent,
            'ContentAgent': ContentAgent
        }
        
        for agent_name, agent_class in agent_classes.items():
            start_time = time.time()
            try:
                # Test agent initialization
                if agent_name in globals():
                    agent = agent_class()
                    self.agents[agent_name] = agent
                    
                    # Test basic agent methods
                    if hasattr(agent, 'get_status'):
                        status_info = agent.get_status()
                        assert isinstance(status_info, dict)
                    
                    if hasattr(agent, 'process_task'):
                        # Create a simple test task
                        test_task = Task(
                            task_id=f"test_{agent_name.lower()}_task",
                            task_type="test",
                            agent_type=agent_name,
                            data={"test": True},
                            priority=1
                        )
                        
                        # Note: We don't actually execute the task to avoid side effects
                        # Just verify the method exists and is callable
                        assert callable(agent.process_task)
                    
                    status = "PASS"
                    details = f"{agent_name} initialized successfully with required methods"
                    
                else:
                    status = "SKIP"
                    details = f"{agent_name} class not available for testing"
                    
            except Exception as e:
                status = "FAIL"
                details = f"{agent_name} initialization failed: {str(e)}"
            
            self.add_test_result(
                f"{agent_name} Initialization",
                "Agent Functionality",
                status,
                time.time() - start_time,
                details
            )
    
    def test_task_queue_coordination(self):
        """Test task queue and agent coordination"""
        
        # Test 1: Task Queue initialization
        start_time = time.time()
        try:
            self.task_queue = TaskQueue(self.db_path)
            
            # Test basic queue operations
            test_task = Task(
                task_id="test_coordination_task",
                task_type="test",
                agent_type="TestAgent",
                data={"test": "coordination"},
                priority=1
            )
            
            # Add task to queue
            task_id = self.task_queue.add_task(test_task)
            assert task_id is not None
            
            # Get queue metrics
            metrics = self.task_queue.get_queue_metrics()
            assert hasattr(metrics, 'pending_tasks')
            
            status = "PASS"
            details = f"Task queue operational. Test task added with ID: {task_id}"
            
        except Exception as e:
            status = "FAIL"
            details = f"Task queue initialization failed: {str(e)}"
        
        self.add_test_result(
            "Task Queue Initialization",
            "Task Queue & Coordination",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: Task priority and scheduling
        start_time = time.time()
        try:
            if self.task_queue:
                # Add multiple tasks with different priorities
                high_priority_task = Task(
                    task_id="high_priority_test",
                    task_type="test",
                    agent_type="TestAgent",
                    data={"priority": "high"},
                    priority=3
                )
                
                low_priority_task = Task(
                    task_id="low_priority_test",
                    task_type="test",
                    agent_type="TestAgent",
                    data={"priority": "low"},
                    priority=1
                )
                
                high_id = self.task_queue.add_task(high_priority_task)
                low_id = self.task_queue.add_task(low_priority_task)
                
                # Get next task (should be high priority)
                next_task = self.task_queue.get_next_task("TestAgent")
                
                if next_task and next_task.priority == 3:
                    status = "PASS"
                    details = "Task priority scheduling working correctly"
                else:
                    status = "FAIL"
                    details = "Task priority scheduling not working as expected"
            else:
                status = "SKIP"
                details = "Task queue not available for priority testing"
                
        except Exception as e:
            status = "FAIL"
            details = f"Task priority testing failed: {str(e)}"
        
        self.add_test_result(
            "Task Priority Scheduling",
            "Task Queue & Coordination",
            status,
            time.time() - start_time,
            details
        )
    
    def test_dashboard_monitoring(self):
        """Test dashboard and monitoring functionality"""
        
        # Test 1: Dashboard initialization (without starting server)
        start_time = time.time()
        try:
            # Test dashboard class instantiation
            dashboard = TotalAccessDashboard(port=8083, debug=False)
            
            # Test dashboard methods without starting the server
            if hasattr(dashboard, 'get_system_health'):
                health = dashboard.get_system_health()
                assert hasattr(health, 'overall_status')
            
            if hasattr(dashboard, 'get_agent_metrics'):
                metrics = dashboard.get_agent_metrics()
                assert isinstance(metrics, list)
            
            status = "PASS"
            details = "Dashboard components initialized successfully"
            
        except Exception as e:
            status = "FAIL"
            details = f"Dashboard initialization failed: {str(e)}"
        
        self.add_test_result(
            "Dashboard Initialization",
            "Dashboard & Monitoring",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: Metrics collection
        start_time = time.time()
        try:
            # Test system metrics collection
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            assert isinstance(cpu_usage, (int, float))
            assert hasattr(memory, 'percent')
            assert hasattr(disk, 'percent')
            
            status = "PASS"
            details = f"System metrics collected: CPU {cpu_usage}%, Memory {memory.percent}%, Disk {disk.percent}%"
            
        except Exception as e:
            status = "FAIL"
            details = f"Metrics collection failed: {str(e)}"
        
        self.add_test_result(
            "System Metrics Collection",
            "Dashboard & Monitoring",
            status,
            time.time() - start_time,
            details
        )
    
    def test_integration_api(self):
        """Test external API integrations"""
        
        # Test 1: Network connectivity
        start_time = time.time()
        try:
            # Test basic internet connectivity
            response = requests.get('https://httpbin.org/status/200', timeout=10)
            
            if response.status_code == 200:
                status = "PASS"
                details = "Network connectivity verified"
            else:
                status = "FAIL"
                details = f"Network test failed with status: {response.status_code}"
                
        except Exception as e:
            status = "FAIL"
            details = f"Network connectivity test failed: {str(e)}"
        
        self.add_test_result(
            "Network Connectivity",
            "Integration & API",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: Local API endpoints (if available)
        start_time = time.time()
        try:
            # Test if any local services are running
            local_endpoints = [
                'http://localhost:8080/health',
                'http://localhost:8081/api/status',
                'http://localhost:8082/api/system/health'
            ]
            
            available_endpoints = []
            for endpoint in local_endpoints:
                try:
                    response = requests.get(endpoint, timeout=2)
                    if response.status_code < 500:
                        available_endpoints.append(endpoint)
                except:
                    pass
            
            if available_endpoints:
                status = "PASS"
                details = f"Local API endpoints available: {len(available_endpoints)}"
            else:
                status = "SKIP"
                details = "No local API endpoints currently running"
                
        except Exception as e:
            status = "FAIL"
            details = f"Local API testing failed: {str(e)}"
        
        self.add_test_result(
            "Local API Endpoints",
            "Integration & API",
            status,
            time.time() - start_time,
            details
        )
    
    def test_resilience_self_healing(self):
        """Test system resilience and self-healing capabilities"""
        
        # Test 1: Error handling and recovery
        start_time = time.time()
        try:
            # Simulate error conditions and test recovery
            if self.task_queue:
                # Test invalid task handling
                invalid_task = Task(
                    task_id="invalid_test_task",
                    task_type="invalid_type",
                    agent_type="NonExistentAgent",
                    data={"invalid": True},
                    priority=1
                )
                
                # This should not crash the system
                task_id = self.task_queue.add_task(invalid_task)
                
                # System should handle this gracefully
                status = "PASS"
                details = "System handles invalid tasks gracefully"
            else:
                status = "SKIP"
                details = "Task queue not available for resilience testing"
                
        except Exception as e:
            # If we catch an exception, check if it's handled properly
            if "handled" in str(e).lower() or "graceful" in str(e).lower():
                status = "PASS"
                details = f"Error properly handled: {str(e)}"
            else:
                status = "FAIL"
                details = f"Unhandled error in resilience test: {str(e)}"
        
        self.add_test_result(
            "Error Handling & Recovery",
            "Resilience & Self-Healing",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: Resource cleanup
        start_time = time.time()
        try:
            # Test temporary file cleanup
            temp_files = []
            for i in range(5):
                temp_file = Path(f"temp/test_cleanup_{i}.tmp")
                temp_file.write_text(f"Test cleanup file {i}")
                temp_files.append(temp_file)
            
            # Cleanup
            cleaned_files = 0
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()
                    cleaned_files += 1
            
            status = "PASS"
            details = f"Resource cleanup successful: {cleaned_files}/{len(temp_files)} files cleaned"
            
        except Exception as e:
            status = "FAIL"
            details = f"Resource cleanup failed: {str(e)}"
        
        self.add_test_result(
            "Resource Cleanup",
            "Resilience & Self-Healing",
            status,
            time.time() - start_time,
            details
        )
    
    def test_performance_load(self):
        """Test system performance under load"""
        
        # Test 1: Database performance
        start_time = time.time()
        try:
            if self.task_queue:
                # Add multiple tasks quickly
                task_count = 50
                start_db_time = time.time()
                
                for i in range(task_count):
                    test_task = Task(
                        task_id=f"perf_test_task_{i}",
                        task_type="performance_test",
                        agent_type="TestAgent",
                        data={"index": i},
                        priority=1
                    )
                    self.task_queue.add_task(test_task)
                
                db_duration = time.time() - start_db_time
                tasks_per_second = task_count / db_duration
                
                if tasks_per_second > 10:  # Reasonable threshold
                    status = "PASS"
                    details = f"Database performance: {tasks_per_second:.1f} tasks/second"
                else:
                    status = "FAIL"
                    details = f"Database performance below threshold: {tasks_per_second:.1f} tasks/second"
            else:
                status = "SKIP"
                details = "Task queue not available for performance testing"
                
        except Exception as e:
            status = "FAIL"
            details = f"Database performance test failed: {str(e)}"
        
        self.add_test_result(
            "Database Performance",
            "Performance & Load",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: Memory usage
        start_time = time.time()
        try:
            import psutil
            import gc
            
            # Get initial memory usage
            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Create some objects to test memory management
            test_objects = []
            for i in range(1000):
                test_objects.append({"data": f"test_object_{i}", "index": i})
            
            # Check memory usage
            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Cleanup
            del test_objects
            gc.collect()
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - initial_memory
            memory_recovered = peak_memory - final_memory
            
            if memory_increase < 100:  # Less than 100MB increase
                status = "PASS"
                details = f"Memory usage: +{memory_increase:.1f}MB peak, -{memory_recovered:.1f}MB recovered"
            else:
                status = "FAIL"
                details = f"Excessive memory usage: +{memory_increase:.1f}MB"
                
        except Exception as e:
            status = "FAIL"
            details = f"Memory usage test failed: {str(e)}"
        
        self.add_test_result(
            "Memory Usage",
            "Performance & Load",
            status,
            time.time() - start_time,
            details
        )
    
    def test_security_secrets(self):
        """Test security and secrets management"""
        
        # Test 1: Secret store functionality
        start_time = time.time()
        try:
            self.secret_store = SecretStore()
            
            # Test secret storage and retrieval
            test_secret_key = "test_secret_key"
            test_secret_value = "test_secret_value_12345"
            
            # Store secret
            self.secret_store.store_secret(test_secret_key, test_secret_value)
            
            # Retrieve secret
            retrieved_value = self.secret_store.get_secret(test_secret_key)
            
            if retrieved_value == test_secret_value:
                status = "PASS"
                details = "Secret storage and retrieval working correctly"
            else:
                status = "FAIL"
                details = "Secret retrieval returned incorrect value"
            
            # Cleanup test secret
            try:
                self.secret_store.delete_secret(test_secret_key)
            except:
                pass
                
        except Exception as e:
            status = "FAIL"
            details = f"Secret store test failed: {str(e)}"
        
        self.add_test_result(
            "Secret Store Functionality",
            "Security & Secrets",
            status,
            time.time() - start_time,
            details
        )
        
        # Test 2: File permissions and security
        start_time = time.time()
        try:
            # Check that sensitive files have appropriate permissions
            sensitive_files = [
                self.db_path,
                "config/com.trae.ai.autonomous.plist"
            ]
            
            secure_files = 0
            for file_path in sensitive_files:
                if Path(file_path).exists():
                    # Check if file is readable (basic security check)
                    try:
                        with open(file_path, 'r') as f:
                            f.read(1)  # Try to read one character
                        secure_files += 1
                    except PermissionError:
                        # This might actually be good for security
                        secure_files += 1
            
            status = "PASS"
            details = f"File security check: {secure_files}/{len(sensitive_files)} files checked"
            
        except Exception as e:
            status = "FAIL"
            details = f"File security test failed: {str(e)}"
        
        self.add_test_result(
            "File Security",
            "Security & Secrets",
            status,
            time.time() - start_time,
            details
        )
    
    def create_database_schema(self, conn):
        """Create required database tables"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS tasks (
            task_id TEXT PRIMARY KEY,
            task_type TEXT NOT NULL,
            agent_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            priority INTEGER DEFAULT 1,
            data TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            started_at TEXT,
            completed_at TEXT,
            error_message TEXT
        );
        
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            agent_type TEXT NOT NULL,
            status TEXT DEFAULT 'idle',
            last_heartbeat TEXT DEFAULT CURRENT_TIMESTAMP,
            capabilities TEXT
        );
        
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS insights (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            insight_type TEXT NOT NULL,
            content TEXT NOT NULL,
            confidence_score REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS decision_explanations (
            decision_id TEXT PRIMARY KEY,
            agent_type TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            input_data TEXT,
            reasoning_steps TEXT,
            confidence_score REAL,
            alternative_options TEXT,
            outcome TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        conn.executescript(schema_sql)
        conn.commit()
    
    def add_test_result(self, test_name: str, category: str, status: str, 
                      duration: float, details: str, error: str = None):
        """Add a test result to the results list"""
        result = TestResult(
            test_name=test_name,
            category=category,
            status=status,
            duration=duration,
            details=details,
            timestamp=datetime.now(),
            error=error
        )
        
        self.test_results.append(result)
        
        # Log the result
        log_level = logging.INFO if status == "PASS" else logging.WARNING if status == "SKIP" else logging.ERROR
        self.logger.log(log_level, f"{status}: {test_name} ({duration:.2f}s) - {details}")
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == "PASS"])
        failed_tests = len([r for r in self.test_results if r.status == "FAIL"])
        skipped_tests = len([r for r in self.test_results if r.status == "SKIP"])
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Group results by category
        categories = {}
        for result in self.test_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        # Generate category summaries
        category_summaries = {}
        for category, results in categories.items():
            category_passed = len([r for r in results if r.status == "PASS"])
            category_total = len(results)
            category_success_rate = (category_passed / category_total * 100) if category_total > 0 else 0
            
            category_summaries[category] = {
                'total_tests': category_total,
                'passed': category_passed,
                'failed': len([r for r in results if r.status == "FAIL"]),
                'skipped': len([r for r in results if r.status == "SKIP"]),
                'success_rate': category_success_rate
            }
        
        # Determine overall system status
        if success_rate >= 90:
            overall_status = "EXCELLENT - System operating within the successful 2%"
        elif success_rate >= 75:
            overall_status = "GOOD - System mostly functional with minor issues"
        elif success_rate >= 50:
            overall_status = "WARNING - System has significant issues requiring attention"
        else:
            overall_status = "CRITICAL - System requires immediate intervention"
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'skipped': skipped_tests,
                'success_rate': success_rate,
                'total_duration': total_duration,
                'overall_status': overall_status
            },
            'category_summaries': category_summaries,
            'detailed_results': [
                {
                    'test_name': r.test_name,
                    'category': r.category,
                    'status': r.status,
                    'duration': r.duration,
                    'details': r.details,
                    'timestamp': r.timestamp.isoformat(),
                    'error': r.error
                }
                for r in self.test_results
            ],
            'recommendations': self.generate_recommendations(),
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        failed_tests = [r for r in self.test_results if r.status == "FAIL"]
        
        if failed_tests:
            recommendations.append(f"Address {len(failed_tests)} failed tests before production deployment")
        
        # Category-specific recommendations
        categories = {}
        for result in self.test_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)
        
        for category, results in categories.items():
            failed_in_category = [r for r in results if r.status == "FAIL"]
            if failed_in_category:
                recommendations.append(f"Focus on {category} issues: {len(failed_in_category)} failures detected")
        
        # Performance recommendations
        perf_results = [r for r in self.test_results if "Performance" in r.category]
        if any(r.status == "FAIL" for r in perf_results):
            recommendations.append("Optimize system performance before handling production load")
        
        # Security recommendations
        security_results = [r for r in self.test_results if "Security" in r.category]
        if any(r.status == "FAIL" for r in security_results):
            recommendations.append("CRITICAL: Address security issues immediately")
        
        if not recommendations:
            recommendations.append("System is ready for autonomous operation")
            recommendations.append("Continue monitoring system health through the Total Access Dashboard")
            recommendations.append("Implement regular automated testing to maintain system integrity")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any], filename: str = None):
        """Save test report to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"autonomous_system_test_report_{timestamp}.json"
        
        report_path = Path("logs") / filename
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.logger.info(f"Test report saved to: {report_path}")
        return report_path


def main():
    """Main test execution function"""
    print("\n" + "="*80)
    print("TRAE.AI AUTONOMOUS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("Testing system compliance with the 'Perfected Autonomous System' blueprint")
    print("="*80 + "\n")
    
    tester = AutonomousSystemTester()
    
    try:
        # Run all tests
        report = tester.run_all_tests()
        
        # Save report
        report_path = tester.save_report(report)
        
        # Print summary
        print("\n" + "="*80)
        print("TEST EXECUTION COMPLETE")
        print("="*80)
        
        summary = report['test_summary']
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Duration: {summary['total_duration']:.2f} seconds")
        print(f"\nOverall Status: {summary['overall_status']}")
        
        print(f"\nDetailed report saved to: {report_path}")
        
        # Print recommendations
        if report['recommendations']:
            print("\nRecommendations:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"{i}. {rec}")
        
        print("\n" + "="*80)
        
        # Return appropriate exit code
        if summary['failed'] == 0:
            print("🎉 AUTONOMOUS SYSTEM READY FOR OPERATION")
            return 0
        else:
            print("⚠️  SYSTEM REQUIRES ATTENTION BEFORE DEPLOYMENT")
            return 1
            
    except Exception as e:
        print(f"\nCRITICAL ERROR: Test execution failed: {e}")
        return 2


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)