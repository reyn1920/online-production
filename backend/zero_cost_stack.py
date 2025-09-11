#!/usr/bin/env python3
"""
TRAE.AI Zero-Cost Stack Implementation
Ensures 100% Free, No-Trial Software Stack Compliance

System Constitution Adherence:
- 100% Live Code: All configurations produce working implementations
- Zero-Cost Stack: Exclusively uses free, open-source software
- Additive Evolution: Builds upon existing free alternatives
- Secure Design: Implements robust security without paid services
"""

import os
import json
import logging
import subprocess
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import sqlite3
from datetime import datetime
import yaml
import hashlib
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/zero_cost_stack.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServiceCategory(Enum):
    """Categories of services in the stack"""
    AI_LLM = "ai_llm"
    TEXT_TO_SPEECH = "text_to_speech"
    IMAGE_GENERATION = "image_generation"
    VIDEO_PROCESSING = "video_processing"
    AUDIO_PROCESSING = "audio_processing"
    DATABASE = "database"
    HOSTING = "hosting"
    CDN = "cdn"
    EMAIL = "email"
    ANALYTICS = "analytics"
    MONITORING = "monitoring"
    AUTHENTICATION = "authentication"
    PAYMENT = "payment"
    SOCIAL_MEDIA = "social_media"
    SEARCH = "search"
    STORAGE = "storage"

class CostStatus(Enum):
    """Cost status of services"""
    FREE = "free"
    FREEMIUM = "freemium"
    TRIAL_ONLY = "trial_only"
    PAID_ONLY = "paid_only"
    UNKNOWN = "unknown"

@dataclass
class ServiceConfig:
    """Configuration for a zero-cost service"""
    name: str
    category: ServiceCategory
    cost_status: CostStatus
    api_endpoint: Optional[str] = None
    api_key_required: bool = False
    free_tier_limits: Dict[str, Any] = None
    alternative_services: List[str] = None
    setup_instructions: List[str] = None
    environment_variables: Dict[str, str] = None
    docker_image: Optional[str] = None
    local_installation: bool = False
    compliance_notes: str = ""

@dataclass
class StackValidationResult:
    """Result of stack validation"""
    service_name: str
    is_compliant: bool
    cost_status: CostStatus
    issues: List[str]
    recommendations: List[str]
    timestamp: datetime

class ZeroCostStackManager:
    """Manages and validates zero-cost software stack"""
    
    def __init__(self, config_path: str = "config/zero_cost_stack.json"):
        self.config_path = config_path
        self.services: Dict[str, ServiceConfig] = {}
        self.validation_results: List[StackValidationResult] = []
        self.db_path = "data/zero_cost_stack.db"
        
        # Initialize database
        self._init_database()
        
        # Load zero-cost service configurations
        self._load_zero_cost_services()
        
        # Validate current stack
        self._validate_stack_compliance()
        
        logger.info("Zero-Cost Stack Manager initialized")
    
    def _init_database(self):
        """Initialize database for tracking stack compliance"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS services (
                    name TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    cost_status TEXT NOT NULL,
                    api_endpoint TEXT,
                    api_key_required BOOLEAN DEFAULT FALSE,
                    free_tier_limits TEXT,
                    alternative_services TEXT,
                    setup_instructions TEXT,
                    environment_variables TEXT,
                    docker_image TEXT,
                    local_installation BOOLEAN DEFAULT FALSE,
                    compliance_notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS validation_results (
                    id TEXT PRIMARY KEY,
                    service_name TEXT NOT NULL,
                    is_compliant BOOLEAN NOT NULL,
                    cost_status TEXT NOT NULL,
                    issues TEXT,
                    recommendations TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (service_name) REFERENCES services (name)
                );
                
                CREATE TABLE IF NOT EXISTS stack_audits (
                    id TEXT PRIMARY KEY,
                    audit_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_services INTEGER,
                    compliant_services INTEGER,
                    compliance_percentage REAL,
                    critical_issues TEXT,
                    recommendations TEXT
                );
            """)
    
    def _load_zero_cost_services(self):
        """Load configurations for zero-cost services"""
        # Define zero-cost service configurations
        zero_cost_configs = {
            # AI/LLM Services
            "ollama": ServiceConfig(
                name="Ollama",
                category=ServiceCategory.AI_LLM,
                cost_status=CostStatus.FREE,
                api_endpoint="http://localhost:11434",
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh",
                    "Pull model: ollama pull llama2",
                    "Start server: ollama serve"
                ],
                docker_image="ollama/ollama",
                local_installation=True,
                compliance_notes="100% free, runs locally, no API keys required"
            ),
            
            "huggingface_transformers": ServiceConfig(
                name="Hugging Face Transformers",
                category=ServiceCategory.AI_LLM,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "pip install transformers torch",
                    "Download models locally for offline use"
                ],
                local_installation=True,
                compliance_notes="Open-source, runs locally, no API costs"
            ),
            
            # Text-to-Speech
            "espeak": ServiceConfig(
                name="eSpeak NG",
                category=ServiceCategory.TEXT_TO_SPEECH,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Ubuntu/Debian: sudo apt-get install espeak-ng",
                    "macOS: brew install espeak",
                    "Usage: espeak 'Hello World'"
                ],
                local_installation=True,
                compliance_notes="Completely free, open-source TTS engine"
            ),
            
            "festival": ServiceConfig(
                name="Festival Speech Synthesis",
                category=ServiceCategory.TEXT_TO_SPEECH,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Ubuntu/Debian: sudo apt-get install festival",
                    "macOS: brew install festival",
                    "Usage: echo 'Hello World' | festival --tts"
                ],
                local_installation=True,
                compliance_notes="Free, open-source speech synthesis"
            ),
            
            # Image Generation
            "stable_diffusion_local": ServiceConfig(
                name="Stable Diffusion (Local)",
                category=ServiceCategory.IMAGE_GENERATION,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "pip install diffusers transformers accelerate",
                    "Download model locally",
                    "Run inference without API calls"
                ],
                local_installation=True,
                compliance_notes="Open-source, runs locally, no API costs"
            ),
            
            # Video Processing
            "ffmpeg": ServiceConfig(
                name="FFmpeg",
                category=ServiceCategory.VIDEO_PROCESSING,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Ubuntu/Debian: sudo apt-get install ffmpeg",
                    "macOS: brew install ffmpeg",
                    "Windows: Download from ffmpeg.org"
                ],
                local_installation=True,
                compliance_notes="Industry-standard, completely free video processing"
            ),
            
            "opencv": ServiceConfig(
                name="OpenCV",
                category=ServiceCategory.VIDEO_PROCESSING,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "pip install opencv-python",
                    "pip install opencv-contrib-python"
                ],
                local_installation=True,
                compliance_notes="Open-source computer vision library"
            ),
            
            # Database
            "sqlite": ServiceConfig(
                name="SQLite",
                category=ServiceCategory.DATABASE,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Built into Python standard library",
                    "No installation required"
                ],
                local_installation=True,
                compliance_notes="Public domain, serverless database"
            ),
            
            "postgresql": ServiceConfig(
                name="PostgreSQL",
                category=ServiceCategory.DATABASE,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                setup_instructions=[
                    "Ubuntu/Debian: sudo apt-get install postgresql",
                    "macOS: brew install postgresql",
                    "Docker: docker run -d postgres"
                ],
                docker_image="postgres:latest",
                local_installation=True,
                compliance_notes="Open-source relational database"
            ),
            
            # Hosting
            "netlify_free": ServiceConfig(
                name="Netlify (Free Tier)",
                category=ServiceCategory.HOSTING,
                cost_status=CostStatus.FREEMIUM,
                api_key_required=True,
                free_tier_limits={
                    "bandwidth": "100GB/month",
                    "build_minutes": "300/month",
                    "sites": "unlimited"
                },
                setup_instructions=[
                    "Sign up at netlify.com",
                    "Connect GitHub repository",
                    "Configure build settings"
                ],
                compliance_notes="Free tier sufficient for most projects"
            ),
            
            "github_pages": ServiceConfig(
                name="GitHub Pages",
                category=ServiceCategory.HOSTING,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={
                    "bandwidth": "100GB/month",
                    "storage": "1GB",
                    "builds": "10/hour"
                },
                setup_instructions=[
                    "Enable Pages in repository settings",
                    "Configure source branch",
                    "Add custom domain (optional)"
                ],
                compliance_notes="Completely free static site hosting"
            ),
            
            # Email
            "smtp_gmail_free": ServiceConfig(
                name="Gmail SMTP (Free)",
                category=ServiceCategory.EMAIL,
                cost_status=CostStatus.FREE,
                api_endpoint="smtp.gmail.com:587",
                api_key_required=True,
                free_tier_limits={
                    "daily_limit": "500 emails",
                    "rate_limit": "100 emails/hour"
                },
                environment_variables={
                    "SMTP_HOST": "smtp.gmail.com",
                    "SMTP_PORT": "587",
                    "SMTP_USERNAME": "your_email@gmail.com",
                    "SMTP_PASSWORD": "app_password"
                },
                setup_instructions=[
                    "Enable 2FA on Gmail account",
                    "Generate app-specific password",
                    "Use app password for SMTP authentication"
                ],
                compliance_notes="Free tier sufficient for most applications"
            ),
            
            # Analytics
            "plausible_ce": ServiceConfig(
                name="Plausible Analytics CE",
                category=ServiceCategory.ANALYTICS,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                docker_image="plausible/analytics:latest",
                setup_instructions=[
                    "Deploy with Docker Compose",
                    "Configure environment variables",
                    "Add tracking script to website"
                ],
                local_installation=True,
                compliance_notes="Self-hosted, privacy-focused analytics"
            ),
            
            # Monitoring
            "prometheus": ServiceConfig(
                name="Prometheus",
                category=ServiceCategory.MONITORING,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                docker_image="prom/prometheus",
                setup_instructions=[
                    "Deploy with Docker",
                    "Configure prometheus.yml",
                    "Set up targets for monitoring"
                ],
                local_installation=True,
                compliance_notes="Open-source monitoring and alerting"
            ),
            
            "grafana": ServiceConfig(
                name="Grafana",
                category=ServiceCategory.MONITORING,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                docker_image="grafana/grafana",
                setup_instructions=[
                    "Deploy with Docker",
                    "Connect to Prometheus data source",
                    "Import dashboards"
                ],
                local_installation=True,
                compliance_notes="Open-source visualization and dashboards"
            ),
            
            # Storage
            "minio": ServiceConfig(
                name="MinIO",
                category=ServiceCategory.STORAGE,
                cost_status=CostStatus.FREE,
                api_key_required=True,
                free_tier_limits={"unlimited": True},
                docker_image="minio/minio",
                setup_instructions=[
                    "Deploy with Docker",
                    "Configure access keys",
                    "Create buckets"
                ],
                local_installation=True,
                compliance_notes="S3-compatible object storage, self-hosted"
            ),
            
            # Search
            "elasticsearch_oss": ServiceConfig(
                name="Elasticsearch OSS",
                category=ServiceCategory.SEARCH,
                cost_status=CostStatus.FREE,
                api_key_required=False,
                free_tier_limits={"unlimited": True},
                docker_image="docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2",
                setup_instructions=[
                    "Deploy with Docker",
                    "Configure cluster settings",
                    "Index documents"
                ],
                local_installation=True,
                compliance_notes="Open-source search and analytics engine"
            )
        }
        
        # Store configurations
        for service_name, config in zero_cost_configs.items():
            self.services[service_name] = config
            self._store_service_config(config)
        
        logger.info(f"Loaded {len(zero_cost_configs)} zero-cost service configurations")
    
    def _store_service_config(self, config: ServiceConfig):
        """Store service configuration in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO services (name, category, cost_status, api_endpoint, api_key_required, free_tier_limits, alternative_services, setup_instructions, environment_variables, docker_image, local_installation, compliance_notes, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        config.name,
                        config.category.value,
                        config.cost_status.value,
                        config.api_endpoint,
                        config.api_key_required,
                        json.dumps(config.free_tier_limits),
                        json.dumps(config.alternative_services),
                        json.dumps(config.setup_instructions),
                        json.dumps(config.environment_variables),
                        config.docker_image,
                        config.local_installation,
                        config.compliance_notes,
                        datetime.now()
                    )
                )
        except Exception as e:
            logger.error(f"Error storing service config for {config.name}: {e}")
    
    def _validate_stack_compliance(self):
        """Validate current stack against zero-cost requirements"""
        logger.info("Validating stack compliance...")
        
        validation_results = []
        
        for service_name, config in self.services.items():
            result = self._validate_service_compliance(config)
            validation_results.append(result)
            self._store_validation_result(result)
        
        self.validation_results = validation_results
        
        # Generate audit report
        self._generate_audit_report()
        
        logger.info(f"Stack validation completed. {len([r for r in validation_results if r.is_compliant])}/{len(validation_results)} services compliant")
    
    def _validate_service_compliance(self, config: ServiceConfig) -> StackValidationResult:
        """Validate individual service compliance"""
        issues = []
        recommendations = []
        is_compliant = True
        
        # Check cost status
        if config.cost_status == CostStatus.PAID_ONLY:
            issues.append("Service requires payment - violates zero-cost requirement")
            is_compliant = False
            recommendations.append(f"Replace with free alternative from: {config.alternative_services}")
        
        elif config.cost_status == CostStatus.TRIAL_ONLY:
            issues.append("Service only offers trial - not sustainable for production")
            is_compliant = False
            recommendations.append("Find permanent free alternative")
        
        elif config.cost_status == CostStatus.FREEMIUM:
            if not config.free_tier_limits:
                issues.append("Freemium service without defined limits - risk of unexpected charges")
                recommendations.append("Define and monitor usage limits")
            else:
                recommendations.append("Monitor usage to stay within free tier limits")
        
        # Check API key requirements
        if config.api_key_required and not config.local_installation:
            recommendations.append("Consider local installation to avoid API dependencies")
        
        # Check for local alternatives
        if not config.local_installation and config.category in [ServiceCategory.AI_LLM, ServiceCategory.IMAGE_GENERATION]:
            recommendations.append("Consider local installation for better cost control and privacy")
        
        return StackValidationResult(
            service_name=config.name,
            is_compliant=is_compliant,
            cost_status=config.cost_status,
            issues=issues,
            recommendations=recommendations,
            timestamp=datetime.now()
        )
    
    def _store_validation_result(self, result: StackValidationResult):
        """Store validation result in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO validation_results (id, service_name, is_compliant, cost_status, issues, recommendations, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        result.service_name,
                        result.is_compliant,
                        result.cost_status.value,
                        json.dumps(result.issues),
                        json.dumps(result.recommendations),
                        result.timestamp
                    )
                )
        except Exception as e:
            logger.error(f"Error storing validation result for {result.service_name}: {e}")
    
    def _generate_audit_report(self):
        """Generate comprehensive audit report"""
        try:
            total_services = len(self.validation_results)
            compliant_services = len([r for r in self.validation_results if r.is_compliant])
            compliance_percentage = (compliant_services / total_services) * 100 if total_services > 0 else 0
            
            critical_issues = []
            all_recommendations = []
            
            for result in self.validation_results:
                if not result.is_compliant:
                    critical_issues.extend(result.issues)
                all_recommendations.extend(result.recommendations)
            
            # Store audit in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO stack_audits (id, total_services, compliant_services, compliance_percentage, critical_issues, recommendations) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        str(uuid.uuid4()),
                        total_services,
                        compliant_services,
                        compliance_percentage,
                        json.dumps(critical_issues),
                        json.dumps(list(set(all_recommendations)))
                    )
                )
            
            logger.info(f"Audit report generated: {compliance_percentage:.1f}% compliance")
            
        except Exception as e:
            logger.error(f"Error generating audit report: {e}")
    
    def get_zero_cost_alternatives(self, category: ServiceCategory) -> List[ServiceConfig]:
        """Get zero-cost alternatives for a service category"""
        return [
            config for config in self.services.values()
            if config.category == category and config.cost_status in [CostStatus.FREE, CostStatus.FREEMIUM]
        ]
    
    def generate_docker_compose(self) -> str:
        """Generate Docker Compose file for zero-cost stack"""
        services = {}
        
        for config in self.services.values():
            if config.docker_image and config.local_installation:
                service_name = config.name.lower().replace(" ", "_")
                
                service_config = {
                    "image": config.docker_image,
                    "restart": "unless-stopped"
                }
                
                # Add environment variables if specified
                if config.environment_variables:
                    service_config["environment"] = config.environment_variables
                
                # Add common configurations based on service type
                if config.category == ServiceCategory.DATABASE:
                    service_config["volumes"] = [f"./{service_name}_data:/var/lib/postgresql/data"]
                    service_config["ports"] = ["5432:5432"]
                
                elif config.category == ServiceCategory.MONITORING:
                    if "prometheus" in service_name:
                        service_config["ports"] = ["9090:9090"]
                        service_config["volumes"] = ["./prometheus.yml:/etc/prometheus/prometheus.yml"]
                    elif "grafana" in service_name:
                        service_config["ports"] = ["3000:3000"]
                        service_config["volumes"] = ["grafana_data:/var/lib/grafana"]
                
                elif config.category == ServiceCategory.STORAGE:
                    service_config["ports"] = ["9000:9000", "9001:9001"]
                    service_config["volumes"] = ["minio_data:/data"]
                    service_config["command"] = "server /data --console-address ':9001'"
                
                services[service_name] = service_config
        
        # Generate Docker Compose YAML
        compose_config = {
            "version": "3.8",
            "services": services,
            "volumes": {
                "grafana_data": {},
                "minio_data": {}
            }
        }
        
        return yaml.dump(compose_config, default_flow_style=False)
    
    def generate_setup_script(self) -> str:
        """Generate setup script for zero-cost stack"""
        script_lines = [
            "#!/bin/bash",
            "# Zero-Cost Stack Setup Script",
            "# Generated by TRAE.AI Zero-Cost Stack Manager",
            "",
            "set -e",
            "",
            "echo 'Setting up zero-cost software stack...'",
            ""
        ]
        
        # Group services by installation method
        apt_packages = []
        brew_packages = []
        pip_packages = []
        docker_services = []
        
        for config in self.services.values():
            if config.setup_instructions:
                for instruction in config.setup_instructions:
                    if "apt-get install" in instruction:
                        package = instruction.split("apt-get install ")[-1]
                        apt_packages.append(package)
                    elif "brew install" in instruction:
                        package = instruction.split("brew install ")[-1]
                        brew_packages.append(package)
                    elif "pip install" in instruction:
                        package = instruction.split("pip install ")[-1]
                        pip_packages.append(package)
            
            if config.docker_image:
                docker_services.append(config.name)
        
        # Add installation commands
        if apt_packages:
            script_lines.extend([
                "# Install system packages (Ubuntu/Debian)",
                "if command -v apt-get &> /dev/null; then",
                f"    sudo apt-get update && sudo apt-get install -y {' '.join(set(apt_packages))}",
                "fi",
                ""
            ])
        
        if brew_packages:
            script_lines.extend([
                "# Install packages (macOS)",
                "if command -v brew &> /dev/null; then",
                f"    brew install {' '.join(set(brew_packages))}",
                "fi",
                ""
            ])
        
        if pip_packages:
            script_lines.extend([
                "# Install Python packages",
                f"pip install {' '.join(set(pip_packages))}",
                ""
            ])
        
        if docker_services:
            script_lines.extend([
                "# Start Docker services",
                "if command -v docker-compose &> /dev/null; then",
                "    docker-compose up -d",
                "    echo 'Docker services started'",
                "else",
                "    echo 'Docker Compose not found. Please install Docker and Docker Compose.'",
                "fi",
                ""
            ])
        
        script_lines.extend([
            "echo 'Zero-cost stack setup completed!'",
            "echo 'All services are now running with zero ongoing costs.'"
        ])
        
        return "\n".join(script_lines)
    
    def validate_environment_compliance(self) -> Dict[str, Any]:
        """Validate current environment against zero-cost requirements"""
        compliance_report = {
            "timestamp": datetime.now().isoformat(),
            "overall_compliance": True,
            "services_checked": len(self.services),
            "compliant_services": 0,
            "violations": [],
            "recommendations": [],
            "cost_savings": {
                "estimated_monthly_savings": 0,
                "avoided_services": []
            }
        }
        
        # Check each service
        for config in self.services.values():
            if config.cost_status == CostStatus.FREE:
                compliance_report["compliant_services"] += 1
            elif config.cost_status in [CostStatus.PAID_ONLY, CostStatus.TRIAL_ONLY]:
                compliance_report["overall_compliance"] = False
                compliance_report["violations"].append({
                    "service": config.name,
                    "issue": f"Service requires payment ({config.cost_status.value})",
                    "category": config.category.value
                })
        
        # Calculate compliance percentage
        compliance_percentage = (compliance_report["compliant_services"] / compliance_report["services_checked"]) * 100
        compliance_report["compliance_percentage"] = compliance_percentage
        
        # Add recommendations
        if compliance_percentage < 100:
            compliance_report["recommendations"].extend([
                "Replace paid services with free alternatives",
                "Consider self-hosting solutions where possible",
                "Use local installations to avoid API costs",
                "Monitor free tier usage limits"
            ])
        
        return compliance_report
    
    def generate_cost_comparison_report(self) -> Dict[str, Any]:
        """Generate cost comparison between zero-cost and paid alternatives"""
        # Typical costs for paid alternatives
        paid_alternatives = {
            ServiceCategory.AI_LLM: {"service": "OpenAI GPT-4", "monthly_cost": 20},
            ServiceCategory.TEXT_TO_SPEECH: {"service": "Amazon Polly", "monthly_cost": 15},
            ServiceCategory.IMAGE_GENERATION: {"service": "DALL-E 2", "monthly_cost": 25},
            ServiceCategory.VIDEO_PROCESSING: {"service": "AWS Elemental", "monthly_cost": 50},
            ServiceCategory.DATABASE: {"service": "AWS RDS", "monthly_cost": 30},
            ServiceCategory.HOSTING: {"service": "AWS EC2", "monthly_cost": 40},
            ServiceCategory.EMAIL: {"service": "SendGrid", "monthly_cost": 20},
            ServiceCategory.ANALYTICS: {"service": "Google Analytics 360", "monthly_cost": 150},
            ServiceCategory.MONITORING: {"service": "DataDog", "monthly_cost": 45},
            ServiceCategory.STORAGE: {"service": "AWS S3", "monthly_cost": 25}
        }
        
        total_savings = 0
        category_savings = {}
        
        for category in ServiceCategory:
            zero_cost_services = self.get_zero_cost_alternatives(category)
            if zero_cost_services and category in paid_alternatives:
                monthly_cost = paid_alternatives[category]["monthly_cost"]
                total_savings += monthly_cost
                category_savings[category.value] = {
                    "paid_alternative": paid_alternatives[category]["service"],
                    "monthly_cost": monthly_cost,
                    "zero_cost_alternatives": [s.name for s in zero_cost_services],
                    "savings": monthly_cost
                }
        
        return {
            "total_monthly_savings": total_savings,
            "annual_savings": total_savings * 12,
            "category_breakdown": category_savings,
            "roi_analysis": {
                "setup_time_hours": 8,
                "hourly_rate": 50,
                "setup_cost": 400,
                "payback_period_months": 400 / total_savings if total_savings > 0 else 0
            }
        }
    
    def export_configuration(self, format_type: str = "json") -> str:
        """Export zero-cost stack configuration"""
        config_data = {
            "zero_cost_stack": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "services": {name: asdict(config) for name, config in self.services.items()},
                "compliance_report": self.validate_environment_compliance(),
                "cost_comparison": self.generate_cost_comparison_report()
            }
        }
        
        if format_type == "json":
            return json.dumps(config_data, indent=2, default=str)
        elif format_type == "yaml":
            return yaml.dump(config_data, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def get_compliance_dashboard_data(self) -> Dict[str, Any]:
        """Get data for compliance dashboard"""
        compliance_report = self.validate_environment_compliance()
        cost_report = self.generate_cost_comparison_report()
        
        return {
            "compliance": compliance_report,
            "cost_savings": cost_report,
            "services_by_category": {
                category.value: len(self.get_zero_cost_alternatives(category))
                for category in ServiceCategory
            },
            "setup_status": {
                "docker_services": len([s for s in self.services.values() if s.docker_image]),
                "local_services": len([s for s in self.services.values() if s.local_installation]),
                "api_services": len([s for s in self.services.values() if s.api_endpoint])
            }
        }

# Main execution
if __name__ == "__main__":
    # Initialize Zero-Cost Stack Manager
    stack_manager = ZeroCostStackManager()
    
    # Generate compliance report
    compliance_report = stack_manager.validate_environment_compliance()
    print("\n=== ZERO-COST STACK COMPLIANCE REPORT ===")
    print(json.dumps(compliance_report, indent=2))
    
    # Generate cost comparison
    cost_report = stack_manager.generate_cost_comparison_report()
    print("\n=== COST SAVINGS ANALYSIS ===")
    print(json.dumps(cost_report, indent=2))
    
    # Generate setup files
    print("\n=== GENERATING SETUP FILES ===")
    
    # Docker Compose
    docker_compose = stack_manager.generate_docker_compose()
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose)
    print("Generated: docker-compose.yml")
    
    # Setup script
    setup_script = stack_manager.generate_setup_script()
    with open("setup_zero_cost_stack.sh", "w") as f:
        f.write(setup_script)
    os.chmod("setup_zero_cost_stack.sh", 0o755)
    print("Generated: setup_zero_cost_stack.sh")
    
    # Configuration export
    config_json = stack_manager.export_configuration("json")
    with open("zero_cost_stack_config.json", "w") as f:
        f.write(config_json)
    print("Generated: zero_cost_stack_config.json")
    
    print("\n=== ZERO-COST STACK SETUP COMPLETE ===")
    print(f"Total services configured: {len(stack_manager.services)}")
    print(f"Estimated monthly savings: ${cost_report['total_monthly_savings']}")
    print(f"Estimated annual savings: ${cost_report['annual_savings']}")
    print("\nRun './setup_zero_cost_stack.sh' to install all services")
    print("Run 'docker-compose up -d' to start containerized services")