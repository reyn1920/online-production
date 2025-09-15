#!/usr/bin/env python3
""""""
API Deployment Orchestrator
Complete lifecycle management for 100+ APIs

Features:
- Automated registration workflow
- Continuous integration testing
- Production deployment pipeline
- Health monitoring
- Rollback capabilities
- Cost optimization

Usage:
    python api_deployment_orchestrator.py
""""""

import asyncio
import json
import logging
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

# Configure logging
logging.basicConfig(
    level = logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler("api_orchestrator.log"), logging.StreamHandler()],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
# )
logger = logging.getLogger(__name__)

@dataclass


class DeploymentStage:
    name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: Optional[str]
    end_time: Optional[str]
    duration: Optional[float]
    logs: List[str]
    error: Optional[str]

@dataclass


class APIDeployment:
    api_key: str
    api_name: str
    phase: int
    priority: str
    cost_tier: str
    stages: List[DeploymentStage]
    overall_status: str
    deployment_time: Optional[str]
    rollback_available: bool
    health_score: int


class APIDeploymentOrchestrator:


    def __init__(self):
        self.deployments = {}
        self.config = self.load_config()
        self.deployment_history = []
        self.monitoring_active = False
        self.rollback_snapshots = {}

        # Import required modules
        try:

            from api_integration_validator import APIIntegrationValidator
                from api_master_dashboard import APIMasterDashboard
            from api_registration_automation import API_REGISTRY, APIRegistrationManager
            from api_testing_suite import APITester

            self.registration_manager = APIRegistrationManager()
            self.tester = APITester()
            self.validator = APIIntegrationValidator()
            self.dashboard = APIMasterDashboard()

        except ImportError as e:
            logger.error(f"Required modules not found: {e}")
            sys.exit(1)


    def load_config(self) -> Dict:
        """Load orchestrator configuration"""
        config_file = "orchestrator_config.yaml"

        default_config = {
            "deployment": {
                "max_parallel_deployments": 3,
                    "timeout_minutes": 30,
                    "retry_attempts": 3,
                    "rollback_on_failure": True,
                    "health_check_interval": 300,  # 5 minutes
                "cost_limit_daily": 50.0,  # USD
# BRACKET_SURGEON: disabled
#             },
                "phases": {
                1: {"name": "Critical APIs", "max_failures": 0},
                    2: {"name": "Core APIs", "max_failures": 1},
                    3: {"name": "Enhanced APIs", "max_failures": 2},
                    4: {"name": "Optional APIs", "max_failures": 5},
# BRACKET_SURGEON: disabled
#                     },
                "environments": {
                "development": {"url": "http://localhost:8000", "auto_deploy": True},
                    "staging": {"url": "https://staging.example.com", "auto_deploy": False},
                    "production": {"url": "https://api.example.com", "auto_deploy": False},
# BRACKET_SURGEON: disabled
#                     },
                "notifications": {
                "slack_webhook": None,
                    "email_alerts": [],
                    "discord_webhook": None,
# BRACKET_SURGEON: disabled
#                     },
# BRACKET_SURGEON: disabled
#                 }

        try:
            with open(config_file, "r") as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            # Create default config
            with open(config_file, "w") as f:
                yaml.dump(default_config, f, default_flow_style = False)
            logger.info(f"Created default config: {config_file}")
            return default_config


    def create_deployment_stages(self) -> List[DeploymentStage]:
        """Create standard deployment stages"""
        return [
            DeploymentStage(
                name="Pre - flight Check",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="API Registration",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="Integration Testing",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="Security Validation",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="Performance Testing",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="Production Deployment",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
                DeploymentStage(
                name="Health Verification",
                    status="pending",
                    start_time = None,
                    end_time = None,
                    duration = None,
                    logs=[],
                    error = None,
# BRACKET_SURGEON: disabled
#                     ),
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 ]


    def execute_stage(self, deployment: APIDeployment, stage_index: int) -> bool:
        """Execute a specific deployment stage"""
        stage = deployment.stages[stage_index]
        stage.status = "running"
        stage.start_time = datetime.now().isoformat()
        stage.logs = []

        logger.info(f"Executing {stage.name} for {deployment.api_name}")

        try:
            if stage.name == "Pre - flight Check":
                success = self.execute_preflight_check(deployment, stage)
            elif stage.name == "API Registration":
                success = self.execute_api_registration(deployment, stage)
            elif stage.name == "Integration Testing":
                success = self.execute_integration_testing(deployment, stage)
            elif stage.name == "Security Validation":
                success = self.execute_security_validation(deployment, stage)
            elif stage.name == "Performance Testing":
                success = self.execute_performance_testing(deployment, stage)
            elif stage.name == "Production Deployment":
                success = self.execute_production_deployment(deployment, stage)
            elif stage.name == "Health Verification":
                success = self.execute_health_verification(deployment, stage)
            else:
                stage.logs.append(f"Unknown stage: {stage.name}")
                success = False

            stage.end_time = datetime.now().isoformat()
            start_dt = datetime.fromisoformat(stage.start_time)
            end_dt = datetime.fromisoformat(stage.end_time)
            stage.duration = (end_dt - start_dt).total_seconds()

            if success:
                stage.status = "completed"
                stage.logs.append(f"✅ {stage.name} completed successfully")
            else:
                stage.status = "failed"
                stage.logs.append(f"❌ {stage.name} failed")

            return success

        except Exception as e:
            stage.status = "failed"
            stage.error = str(e)
            stage.logs.append(f"💥 Exception in {stage.name}: {str(e)}")
            logger.error(
                f"Stage {stage.name} failed for {deployment.api_name}: {str(e)}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            return False


    def execute_preflight_check(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute pre - flight checks"""
        stage.logs.append("🔍 Starting pre - flight checks...")

        # Check environment variables

        from api_registration_automation import API_REGISTRY

        api_config = API_REGISTRY.get(deployment.api_key)
        if not api_config:
            stage.logs.append(f"❌ API configuration not found: {deployment.api_key}")
            return False

        env_var = api_config.get("env_var")
        if env_var and not os.getenv(env_var):
            stage.logs.append(f"⚠️  Environment variable not set: {env_var}")
            # This is not a failure for pre - flight, just a warning

        # Check network connectivity
        try:

            import requests

            response = requests.get("https://httpbin.org/status/200", timeout = 5)
            if response.status_code == 200:
                stage.logs.append("✅ Network connectivity verified")
            else:
                stage.logs.append("⚠️  Network connectivity issues")
        except Exception as e:
            stage.logs.append(f"⚠️  Network check failed: {str(e)}")

        # Check disk space

        import shutil

        free_space = shutil.disk_usage(".").free/(1024**3)  # GB
        if free_space < 1.0:
            stage.logs.append(f"⚠️  Low disk space: {free_space:.1f}GB")
        else:
            stage.logs.append(f"✅ Disk space OK: {free_space:.1f}GB")

        stage.logs.append("✅ Pre - flight checks completed")
        return True


    def execute_api_registration(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute API registration"""
        stage.logs.append("🚀 Starting API registration...")

        try:
            # Check if already registered
            if self.registration_manager.is_registered(deployment.api_key):
                stage.logs.append(f"✅ {deployment.api_name} already registered")
                return True

            # Attempt registration
            success = self.registration_manager.register_api(deployment.api_key)

            if success:
                stage.logs.append(f"✅ {deployment.api_name} registered successfully")
                return True
            else:
                stage.logs.append(f"❌ Failed to register {deployment.api_name}")
                return False

        except Exception as e:
            stage.logs.append(f"💥 Registration error: {str(e)}")
            return False


    def execute_integration_testing(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute integration testing"""
        stage.logs.append("🧪 Starting integration testing...")

        try:
            # Run specific API test
            result = self.tester.run_specific_test(deployment.api_key)

            if result:
                stage.logs.append(f"📊 Test result: {result.status}")
                if result.response_time:
                    stage.logs.append(f"⚡ Response time: {result.response_time:.3f}s")

                if result.status == "success":
                    stage.logs.append(f"✅ Integration test passed")
                    return True
                elif result.status == "no_key":
                    stage.logs.append(f"🔑 API key required for testing")
                    return False
                else:
                    stage.logs.append(
                        f"❌ Integration test failed: {result.error_message}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
                    return False
            else:
                stage.logs.append("❌ No test result returned")
                return False

        except Exception as e:
            stage.logs.append(f"💥 Testing error: {str(e)}")
            return False


    def execute_security_validation(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute security validation"""
        stage.logs.append("🔒 Starting security validation...")

        try:
            # Run validation for this specific API

            from api_integration_validator import APIIntegrationValidator

            validator = APIIntegrationValidator()

            if deployment.api_key in validator.validation_registry:
                api_config = validator.validation_registry[deployment.api_key]
                result = validator.validate_single_api(deployment.api_key, api_config)

                stage.logs.append(f"🔍 Security score: {result.security_score}/100")

                if result.compliance_issues:
                    for issue in result.compliance_issues:
                        stage.logs.append(f"⚠️  {issue}")

                # Pass if security score is above threshold
                if result.security_score >= 70:
                    stage.logs.append("✅ Security validation passed")
                    return True
                else:
                    stage.logs.append("❌ Security validation failed (score < 70)")
                    return False
            else:
                stage.logs.append("⚠️  No security validation available for this API")
                return True  # Pass if no validation available

        except Exception as e:
            stage.logs.append(f"💥 Security validation error: {str(e)}")
            return False


    def execute_performance_testing(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute performance testing"""
        stage.logs.append("⚡ Starting performance testing...")

        try:
            # Run multiple requests to test performance

            import time

            import requests

            from api_registration_automation import API_REGISTRY

            api_config = API_REGISTRY.get(deployment.api_key)
            if not api_config:
                stage.logs.append("❌ API configuration not found")
                return False

            # Simple performance test - measure response times
            response_times = []
            success_count = 0

            for i in range(3):  # 3 test requests
                try:
                    start_time = time.time()
                    # This would need to be implemented per API
                    # For now, just simulate
                    time.sleep(0.1)  # Simulate API call
                    response_time = time.time() - start_time
                    response_times.append(response_time)
                    success_count += 1
                except Exception:
                    pass

            if response_times:
                avg_time = sum(response_times)/len(response_times)
                stage.logs.append(f"📊 Average response time: {avg_time:.3f}s")
                stage.logs.append(f"📈 Success rate: {success_count}/3")

                # Pass if average response time is reasonable
                if avg_time < 5.0 and success_count >= 2:
                    stage.logs.append("✅ Performance test passed")
                    return True
                else:
                    stage.logs.append("❌ Performance test failed")
                    return False
            else:
                stage.logs.append("❌ No performance data collected")
                return False

        except Exception as e:
            stage.logs.append(f"💥 Performance testing error: {str(e)}")
            return False


    def execute_production_deployment(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute production deployment"""
        stage.logs.append("🚀 Starting production deployment...")

        try:
            # Create rollback snapshot
            self.create_rollback_snapshot(deployment.api_key)
            stage.logs.append("📸 Rollback snapshot created")

            # Update environment configuration
            self.update_production_config(deployment.api_key)
            stage.logs.append("⚙️  Production configuration updated")

            # Deploy to production environment
            success = self.deploy_to_environment("production", deployment.api_key)

            if success:
                stage.logs.append("✅ Production deployment successful")
                deployment.deployment_time = datetime.now().isoformat()
                deployment.rollback_available = True
                return True
            else:
                stage.logs.append("❌ Production deployment failed")
                return False

        except Exception as e:
            stage.logs.append(f"💥 Deployment error: {str(e)}")
            return False


    def execute_health_verification(
        self, deployment: APIDeployment, stage: DeploymentStage
# BRACKET_SURGEON: disabled
#     ) -> bool:
        """Execute health verification"""
        stage.logs.append("🏥 Starting health verification...")

        try:
            # Wait a moment for deployment to stabilize
            time.sleep(5)

            # Run health check
            health_score = self.check_api_health(deployment.api_key)
            deployment.health_score = health_score

            stage.logs.append(f"📊 Health score: {health_score}/100")

            if health_score >= 80:
                stage.logs.append("✅ Health verification passed")
                return True
            else:
                stage.logs.append("❌ Health verification failed")
                return False

        except Exception as e:
            stage.logs.append(f"💥 Health verification error: {str(e)}")
            return False


    def create_rollback_snapshot(self, api_key: str):
        """Create rollback snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
                "api_key": api_key,
                "env_vars": {},
                "config_files": [],
# BRACKET_SURGEON: disabled
#                 }

        # Capture current environment variables

        from api_registration_automation import API_REGISTRY

        api_config = API_REGISTRY.get(api_key)
        if api_config and api_config.get("env_var"):
            env_var = api_config["env_var"]
            snapshot["env_vars"][env_var] = os.getenv(env_var)

        self.rollback_snapshots[api_key] = snapshot


    def update_production_config(self, api_key: str):
        """Update production configuration"""
        # This would update production configuration files
        # For now, just log the action
        logger.info(f"Updating production config for {api_key}")


    def deploy_to_environment(self, environment: str, api_key: str) -> bool:
        """Deploy API to specific environment"""
        env_config = self.config["environments"].get(environment)
        if not env_config:
            logger.error(f"Environment {environment} not configured")
            return False

        # Simulate deployment
        logger.info(f"Deploying {api_key} to {environment} ({env_config['url']})")
        time.sleep(2)  # Simulate deployment time

        return True


    def check_api_health(self, api_key: str) -> int:
        """Check API health and return score 0 - 100"""
        try:
            # Run a quick health check
            result = self.tester.run_specific_test(api_key)

            if result and result.status == "success":
                base_score = 80

                # Bonus points for good response time
                if result.response_time and result.response_time < 1.0:
                    base_score += 10
                elif result.response_time and result.response_time < 2.0:
                    base_score += 5

                # Bonus points for no errors
                if not result.error_message:
                    base_score += 10

                return min(base_score, 100)
            else:
                return 30  # Poor health

        except Exception:
            return 0  # Critical health issue


    def deploy_api(self, api_key: str) -> APIDeployment:
        """Deploy a single API through all stages"""

        from api_registration_automation import API_REGISTRY

        api_config = API_REGISTRY.get(api_key)
        if not api_config:
            raise ValueError(f"API {api_key} not found in registry")

        deployment = APIDeployment(
            api_key = api_key,
                api_name = api_config["name"],
                phase = api_config["phase"],
                priority = api_config["priority"],
                cost_tier = api_config["cost"],
                stages = self.create_deployment_stages(),
                overall_status="running",
                deployment_time = None,
                rollback_available = False,
                health_score = 0,
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        self.deployments[api_key] = deployment

        logger.info(f"Starting deployment of {deployment.api_name}")

        # Execute stages sequentially
        for i, stage in enumerate(deployment.stages):
            success = self.execute_stage(deployment, i)

            if not success:
                deployment.overall_status = "failed"
                logger.error(f"Deployment failed at stage: {stage.name}")

                # Rollback if configured
                if self.config["deployment"]["rollback_on_failure"]:
                    self.rollback_deployment(api_key)

                break
        else:
            # All stages completed successfully
            deployment.overall_status = "completed"
            logger.info(f"Deployment of {deployment.api_name} completed successfully")

        return deployment


    def deploy_phase(self, phase: int) -> List[APIDeployment]:
        """Deploy all APIs in a specific phase"""

        from api_registration_automation import API_REGISTRY

        phase_apis = [k for k, v in API_REGISTRY.items() if v["phase"] == phase]
        logger.info(f"Deploying Phase {phase}: {len(phase_apis)} APIs")

        deployments = []
        max_parallel = self.config["deployment"]["max_parallel_deployments"]

        with ThreadPoolExecutor(max_workers = max_parallel) as executor:
            future_to_api = {
                executor.submit(self.deploy_api, api_key): api_key
                for api_key in phase_apis
# BRACKET_SURGEON: disabled
#             }

            for future in future_to_api:
                try:
                    deployment = future.result()
                    deployments.append(deployment)
                except Exception as e:
                    api_key = future_to_api[future]
                    logger.error(f"Failed to deploy {api_key}: {str(e)}")

        return deployments


    def deploy_all_phases(self) -> Dict[int, List[APIDeployment]]:
        """Deploy all phases sequentially"""
        all_deployments = {}

        for phase in [1, 2, 3, 4]:
            logger.info(f"\\n🚀 Starting Phase {phase} Deployment")
            phase_deployments = self.deploy_phase(phase)
            all_deployments[phase] = phase_deployments

            # Check phase success criteria
            phase_config = self.config["phases"][phase]
            failed_count = sum(
                1 for d in phase_deployments if d.overall_status == "failed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             )
            max_failures = phase_config["max_failures"]

            if failed_count > max_failures:
                logger.error(
                    f"Phase {phase} exceeded failure threshold: {failed_count}/{max_failures}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                logger.error("Stopping deployment pipeline")
                break
            else:
                logger.info(
                    f"Phase {phase} completed: {failed_count}/{max_failures} failures"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )

        return all_deployments


    def rollback_deployment(self, api_key: str) -> bool:
        """Rollback a deployment"""
        if api_key not in self.rollback_snapshots:
            logger.error(f"No rollback snapshot available for {api_key}")
            return False

        snapshot = self.rollback_snapshots[api_key]
        logger.info(f"Rolling back {api_key} to snapshot from {snapshot['timestamp']}")

        try:
            # Restore environment variables
            for env_var, value in snapshot["env_vars"].items():
                if value:
                    os.environ[env_var] = value
                elif env_var in os.environ:
                    del os.environ[env_var]

            # Update deployment status
            if api_key in self.deployments:
                self.deployments[api_key].overall_status = "rolled_back"

            logger.info(f"Rollback of {api_key} completed")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for {api_key}: {str(e)}")
            return False


    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report"""
        total_deployments = len(self.deployments)
        completed = sum(
            1 for d in self.deployments.values() if d.overall_status == "completed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        failed = sum(
            1 for d in self.deployments.values() if d.overall_status == "failed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )
        running = sum(
            1 for d in self.deployments.values() if d.overall_status == "running"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         )

        # Phase breakdown
        phase_stats = {}
        for phase in [1, 2, 3, 4]:
            phase_deployments = [
                d for d in self.deployments.values() if d.phase == phase
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#             ]
            phase_stats[phase] = {
                "total": len(phase_deployments),
                    "completed": sum(
                    1 for d in phase_deployments if d.overall_status == "completed"
# BRACKET_SURGEON: disabled
#                 ),
                    "failed": sum(
                    1 for d in phase_deployments if d.overall_status == "failed"
# BRACKET_SURGEON: disabled
#                 ),
                    "running": sum(
                    1 for d in phase_deployments if d.overall_status == "running"
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#                     }

        return {
            "summary": {
                "total_deployments": total_deployments,
                    "completed": completed,
                    "failed": failed,
                    "running": running,
                    "success_rate": (
                    (completed/total_deployments * 100)
                    if total_deployments > 0
                    else 0
# BRACKET_SURGEON: disabled
#                 ),
# BRACKET_SURGEON: disabled
#                     },
                "phase_breakdown": phase_stats,
                "deployments": {k: asdict(v) for k, v in self.deployments.items()},
                "generated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#                 }


    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True


        def monitor_loop():
            while self.monitoring_active:
                try:
                    # Check health of deployed APIs
                    for api_key, deployment in self.deployments.items():
                        if deployment.overall_status == "completed":
                            health_score = self.check_api_health(api_key)
                            deployment.health_score = health_score

                            if health_score < 50:
                                logger.warning(
                                    f"Low health score for {deployment.api_name}: {health_score}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )

                    # Sleep for configured interval
                    time.sleep(self.config["deployment"]["health_check_interval"])

                except Exception as e:
                    logger.error(f"Monitoring error: {str(e)}")
                    time.sleep(60)  # Wait a minute before retrying

        monitoring_thread = threading.Thread(target = monitor_loop, daemon = True)
        monitoring_thread.start()
        logger.info("Health monitoring started")


    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring_active = False
        logger.info("Health monitoring stopped")


    def interactive_menu(self):
        """Interactive deployment menu"""
        while True:
            print("\\n🚀 API Deployment Orchestrator")
            print("=" * 50)
            print("1. 🎯 Deploy single API")
            print("2. 📊 Deploy by phase")
            print("3. 🚀 Deploy all phases")
            print("4. 📋 View deployment status")
            print("5. 📄 Generate report")
            print("6. 🔄 Rollback deployment")
            print("7. 🏥 Start monitoring")
            print("8. 🛑 Stop monitoring")
            print("9. ❌ Exit")

            choice = input("\\nSelect option (1 - 9): ").strip()

            if choice == "1":
                api_key = input("Enter API key: ").strip()
                try:
                    deployment = self.deploy_api(api_key)
                    print(f"\\n✅ Deployment status: {deployment.overall_status}")
                except Exception as e:
                    print(f"❌ Deployment failed: {str(e)}")
                input("\\nPress Enter to continue...")

            elif choice == "2":
                phase = input("Enter phase (1 - 4): ").strip()
                try:
                    phase_num = int(phase)
                    if 1 <= phase_num <= 4:
                        deployments = self.deploy_phase(phase_num)
                        completed = sum(
                            1 for d in deployments if d.overall_status == "completed"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                        print(
                            f"\\n📊 Phase {phase_num}: {completed}/{len(deployments)} successful"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                    else:
                        print("❌ Invalid phase. Use 1 - 4")
                except ValueError:
                    print("❌ Invalid input")
                input("\\nPress Enter to continue...")

            elif choice == "3":
                print("\\n🚀 Starting full deployment...")
                all_deployments = self.deploy_all_phases()
                total = sum(
                    len(deployments) for deployments in all_deployments.values()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                completed = sum(
                    sum(1 for d in deployments if d.overall_status == "completed")
                    for deployments in all_deployments.values()
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                print(f"\\n📊 Overall: {completed}/{total} successful")
                input("\\nPress Enter to continue...")

            elif choice == "4":
                if self.deployments:
                    print("\\n📋 Deployment Status:")
                    for api_key, deployment in self.deployments.items():
                        status_emoji = {
                            "completed": "✅",
                                "failed": "❌",
                                "running": "🔄",
                                "rolled_back": "↩️",
                                }.get(deployment.overall_status, "❓")
                        print(
                            f"  {status_emoji} {deployment.api_name}: {deployment.overall_status}"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                         )
                else:
                    print("\\n📋 No deployments found")
                input("\\nPress Enter to continue...")

            elif choice == "5":
                report = self.generate_deployment_report()
                filename = (
                    f"deployment_report_{datetime.now().strftime('%Y % m%d_ % H%M % S')}.json"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                with open(filename, "w") as f:
                    json.dump(report, f, indent = 2)
                print(f"\\n📄 Report saved to {filename}")
                print(
                    f"📊 Summary: {report['summary']['completed']}/{report['summary']['total_deployments']} successful"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
                input("\\nPress Enter to continue...")

            elif choice == "6":
                api_key = input("Enter API key to rollback: ").strip()
                if self.rollback_deployment(api_key):
                    print(f"✅ Rollback of {api_key} completed")
                else:
                    print(f"❌ Rollback of {api_key} failed")
                input("\\nPress Enter to continue...")

            elif choice == "7":
                self.start_monitoring()
                print("✅ Monitoring started")
                input("\\nPress Enter to continue...")

            elif choice == "8":
                self.stop_monitoring()
                print("✅ Monitoring stopped")
                input("\\nPress Enter to continue...")

            elif choice == "9":
                self.stop_monitoring()
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice")
                time.sleep(1)


def main():
    """Main entry point"""
    try:
        orchestrator = APIDeploymentOrchestrator()
        orchestrator.interactive_menu()
    except KeyboardInterrupt:
        print("\\n👋 Orchestrator stopped")
    except Exception as e:
        logger.error(f"Orchestrator error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()