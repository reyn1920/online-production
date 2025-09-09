#!/usr/bin/env python3
"""
Monetization Services Agent

Provides direct monetization services including:
- AI-Powered SEO Audit Service
- Automated Social Media Graphics Service
- Content Strategy Consulting
- Performance Analytics Reports

This agent creates revenue-generating services that can be offered to clients
while leveraging the existing AI infrastructure.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import base64
import io
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Optional dependencies for image generation and PDF creation
try:
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    GRAPHICS_AVAILABLE = True
except ImportError:
    # Mock classes for type hints when PIL is not available
    class Image:
        class Image:
            pass
    class ImageDraw:
        class Draw:
            pass
    GRAPHICS_AVAILABLE = False

from .base_agents import BaseAgent, AgentCapability
from .research_tools import SEOAuditService, MarketValidator
from .marketing_tools import CommunityEngagementManager
from ..integrations.ollama_integration import OllamaIntegration


class ServiceType(Enum):
    """Available monetization services."""
    SEO_AUDIT = "seo_audit"
    SOCIAL_GRAPHICS = "social_graphics"
    CONTENT_STRATEGY = "content_strategy"
    PERFORMANCE_REPORT = "performance_report"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    KEYWORD_RESEARCH = "keyword_research"


class ServiceTier(Enum):
    """Service pricing tiers."""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DeliveryStatus(Enum):
    """Service delivery status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class ServicePackage:
    """Defines a monetization service package."""
    service_type: ServiceType
    tier: ServiceTier
    name: str
    description: str
    price: float
    delivery_time_hours: int
    features: List[str]
    requirements: List[str]
    deliverables: List[str]


@dataclass
class ServiceOrder:
    """Represents a service order from a client."""
    order_id: str
    client_email: str
    service_package: ServicePackage
    requirements: Dict[str, Any]
    status: DeliveryStatus
    created_at: datetime
    due_date: datetime
    completed_at: Optional[datetime] = None
    deliverables_path: Optional[str] = None
    client_feedback: Optional[str] = None
    rating: Optional[int] = None


@dataclass
class SEOAuditResult:
    """Results from an SEO audit service."""
    domain: str
    overall_score: float
    technical_issues: List[Dict[str, Any]]
    content_recommendations: List[str]
    keyword_opportunities: List[Dict[str, Any]]
    competitor_insights: List[Dict[str, Any]]
    action_plan: List[Dict[str, Any]]
    estimated_impact: Dict[str, float]


@dataclass
class GraphicsPackage:
    """Social media graphics package."""
    package_id: str
    theme: str
    platforms: List[str]
    graphics_count: int
    file_formats: List[str]
    brand_colors: List[str]
    font_preferences: List[str]
    graphics_urls: List[str]
    generated_images: List[str] = None  # Paths to actual generated images
    pdf_package_path: Optional[str] = None  # Path to PDF package
    usage_guide_path: Optional[str] = None  # Path to usage guide
    brand_guidelines_path: Optional[str] = None  # Path to brand guidelines


class MonetizationServicesAgent(BaseAgent):
    """Agent that provides direct monetization services."""
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__()
        self.agent_type = "MonetizationServicesAgent"
        # Ensure config is always a dictionary
        config = config or {}
        self.seo_analyzer = SEOAuditService(config)
        self.market_validator = MarketValidator(config)
        self.social_manager = CommunityEngagementManager(config)
        self.ollama = OllamaIntegration(config)
        
        # Service packages configuration
        self.service_packages = self._initialize_service_packages()
        
        # Database paths
        self.orders_db_path = Path("data/monetization/orders.json")
        self.deliverables_path = Path("data/monetization/deliverables")
        
        # Ensure directories exist
        self.orders_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.deliverables_path.mkdir(parents=True, exist_ok=True)
        
        self._init_database()
    
    @property
    def capabilities(self) -> List[AgentCapability]:
        """Return the list of capabilities this agent possesses."""
        return [
            AgentCapability.MARKETING,
            AgentCapability.CONTENT_CREATION,
            AgentCapability.RESEARCH
        ]
    
    def _initialize_service_packages(self) -> Dict[str, ServicePackage]:
        """Initialize available service packages."""
        packages = {}
        
        # SEO Audit Services
        packages["seo_basic"] = ServicePackage(
            service_type=ServiceType.SEO_AUDIT,
            tier=ServiceTier.BASIC,
            name="Basic SEO Audit",
            description="Comprehensive SEO analysis with actionable recommendations",
            price=97.0,
            delivery_time_hours=24,
            features=[
                "Technical SEO analysis",
                "On-page optimization review",
                "Keyword gap analysis",
                "Basic competitor comparison",
                "Action plan with priorities"
            ],
            requirements=["Website URL", "Target keywords (up to 10)"],
            deliverables=["PDF report", "Excel action plan", "Video walkthrough"]
        )
        
        packages["seo_pro"] = ServicePackage(
            service_type=ServiceType.SEO_AUDIT,
            tier=ServiceTier.PROFESSIONAL,
            name="Professional SEO Audit",
            description="In-depth SEO analysis with competitor intelligence",
            price=297.0,
            delivery_time_hours=48,
            features=[
                "Everything in Basic",
                "Advanced competitor analysis",
                "Content strategy recommendations",
                "Link building opportunities",
                "Local SEO analysis",
                "Performance tracking setup"
            ],
            requirements=["Website URL", "Target keywords (up to 25)", "Top 5 competitors"],
            deliverables=["Comprehensive PDF report", "Excel action plan", "Video walkthrough", "30-day follow-up"]
        )
        
        # Social Media Graphics Services
        packages["graphics_basic"] = ServicePackage(
            service_type=ServiceType.SOCIAL_GRAPHICS,
            tier=ServiceTier.BASIC,
            name="Social Media Graphics Pack",
            description="Professional social media graphics for your brand",
            price=67.0,
            delivery_time_hours=48,
            features=[
                "10 custom graphics",
                "3 platform formats (Instagram, Facebook, Twitter)",
                "Brand color integration",
                "High-resolution files",
                "Commercial usage rights"
            ],
            requirements=["Brand colors", "Logo/brand assets", "Content themes"],
            deliverables=["ZIP file with graphics", "Usage guidelines", "Source files"]
        )
        
        packages["graphics_pro"] = ServicePackage(
            service_type=ServiceType.SOCIAL_GRAPHICS,
            tier=ServiceTier.PROFESSIONAL,
            name="Premium Graphics Suite",
            description="Complete social media graphics solution",
            price=197.0,
            delivery_time_hours=72,
            features=[
                "25 custom graphics",
                "All major platform formats",
                "Animated versions",
                "Story templates",
                "Brand style guide",
                "Monthly refresh option"
            ],
            requirements=["Brand guidelines", "Logo/brand assets", "Content calendar", "Target audience info"],
            deliverables=["Complete graphics suite", "Brand style guide", "Animation files", "Template library"]
        )
        
        return packages
    
    def _init_database(self):
        """Initialize the orders database."""
        if not self.orders_db_path.exists():
            with open(self.orders_db_path, 'w') as f:
                json.dump({"orders": [], "stats": {"total_revenue": 0, "completed_orders": 0}}, f)
    
    async def process_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Process monetization service tasks."""
        if not self.is_action_allowed('direct_monetization'):
            return {
                'status': 'skipped',
                'reason': 'Direct monetization services disabled in configuration'
            }
        
        task_type = task.get('type', '')
        
        try:
            if task_type == 'create_service_order':
                return await self._create_service_order(task.get('order_data', {}))
            elif task_type == 'process_seo_audit':
                return await self._process_seo_audit(task.get('order_id', ''))
            elif task_type == 'generate_social_graphics':
                return await self._generate_social_graphics(task.get('order_id', ''))
            elif task_type == 'deliver_service':
                return await self._deliver_service(task.get('order_id', ''))
            elif task_type == 'get_service_packages':
                return self._get_service_packages()
            elif task_type == 'get_order_status':
                return self._get_order_status(task.get('order_id', ''))
            else:
                return {
                    'status': 'error',
                    'message': f'Unknown task type: {task_type}'
                }
        
        except Exception as e:
            self.logger.error(f"Error processing monetization task: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    async def _create_service_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service order."""
        try:
            package_id = order_data.get('package_id')
            if package_id not in self.service_packages:
                return {'status': 'error', 'message': 'Invalid service package'}
            
            package = self.service_packages[package_id]
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            order = ServiceOrder(
                order_id=order_id,
                client_email=order_data.get('client_email', ''),
                service_package=package,
                requirements=order_data.get('requirements', {}),
                status=DeliveryStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc).replace(
                    hour=datetime.now().hour + package.delivery_time_hours
                )
            )
            
            # Save order to database
            await self._save_order(order)
            
            # Start processing automatically
            asyncio.create_task(self._auto_process_order(order_id))
            
            return {
                'status': 'success',
                'order_id': order_id,
                'estimated_delivery': order.due_date.isoformat(),
                'price': package.price
            }
        
        except Exception as e:
            self.logger.error(f"Error creating service order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _auto_process_order(self, order_id: str):
        """Automatically process an order based on its type."""
        try:
            order = await self._get_order(order_id)
            if not order:
                return
            
            # Update status to in progress
            order.status = DeliveryStatus.IN_PROGRESS
            await self._save_order(order)
            
            # Process based on service type
            if order.service_package.service_type == ServiceType.SEO_AUDIT:
                await self._process_seo_audit(order_id)
            elif order.service_package.service_type == ServiceType.SOCIAL_GRAPHICS:
                await self._generate_social_graphics(order_id)
            
            # Mark as completed and deliver
            await self._deliver_service(order_id)
            
        except Exception as e:
            self.logger.error(f"Error auto-processing order {order_id}: {e}")
    
    async def _process_seo_audit(self, order_id: str) -> Dict[str, Any]:
        """Process an SEO audit service."""
        try:
            order = await self._get_order(order_id)
            if not order:
                return {'status': 'error', 'message': 'Order not found'}
            
            website_url = order.requirements.get('website_url', '')
            target_keywords = order.requirements.get('target_keywords', [])
            
            if not website_url:
                return {'status': 'error', 'message': 'Website URL required'}
            
            # Perform SEO analysis
            seo_results = await self.seo_analyzer.analyze_website(website_url)
            
            # Analyze keywords
            keyword_analysis = await self.seo_analyzer.analyze_keywords(target_keywords)
            
            # Generate competitor insights if competitors provided
            competitor_insights = []
            competitors = order.requirements.get('competitors', [])
            for competitor in competitors[:5]:  # Limit to 5 competitors
                try:
                    comp_analysis = await self.seo_analyzer.analyze_website(competitor)
                    competitor_insights.append({
                        'domain': competitor,
                        'score': comp_analysis.get('overall_score', 0),
                        'strengths': comp_analysis.get('strengths', []),
                        'opportunities': comp_analysis.get('opportunities', [])
                    })
                except Exception as e:
                    self.logger.warning(f"Could not analyze competitor {competitor}: {e}")
            
            # Generate action plan using AI
            action_plan = await self._generate_seo_action_plan(
                seo_results, keyword_analysis, competitor_insights
            )
            
            # Create audit result
            audit_result = SEOAuditResult(
                domain=website_url,
                overall_score=seo_results.get('overall_score', 0),
                technical_issues=seo_results.get('technical_issues', []),
                content_recommendations=seo_results.get('content_recommendations', []),
                keyword_opportunities=keyword_analysis.get('opportunities', []),
                competitor_insights=competitor_insights,
                action_plan=action_plan,
                estimated_impact=self._calculate_seo_impact(seo_results, action_plan)
            )
            
            # Save deliverables
            deliverables_path = await self._save_seo_deliverables(order_id, audit_result)
            
            # Update order
            order.status = DeliveryStatus.COMPLETED
            order.deliverables_path = str(deliverables_path)
            order.completed_at = datetime.now(timezone.utc)
            await self._save_order(order)
            
            return {
                'status': 'success',
                'audit_result': asdict(audit_result),
                'deliverables_path': str(deliverables_path)
            }
        
        except Exception as e:
            self.logger.error(f"Error processing SEO audit: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _generate_social_graphics(self, order_id: str) -> Dict[str, Any]:
        """Generate social media graphics service."""
        try:
            order = await self._get_order(order_id)
            if not order:
                return {'status': 'error', 'message': 'Order not found'}
            
            # Extract requirements
            brand_colors = order.requirements.get('brand_colors', ['#1DA1F2', '#FFFFFF'])
            content_themes = order.requirements.get('content_themes', ['general'])
            platforms = order.requirements.get('platforms', ['instagram', 'facebook', 'twitter'])
            
            # Generate graphics using AI
            graphics_package = await self._create_graphics_package(
                order_id, brand_colors, content_themes, platforms, order.service_package.tier
            )
            
            # Save deliverables
            deliverables_path = await self._save_graphics_deliverables(order_id, graphics_package)
            
            # Update order
            order.status = DeliveryStatus.COMPLETED
            order.deliverables_path = str(deliverables_path)
            order.completed_at = datetime.now(timezone.utc)
            await self._save_order(order)
            
            return {
                'status': 'success',
                'graphics_package': asdict(graphics_package),
                'deliverables_path': str(deliverables_path)
            }
        
        except Exception as e:
            self.logger.error(f"Error generating social graphics: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _generate_seo_action_plan(self, seo_results: Dict, keyword_analysis: Dict, competitor_insights: List) -> List[Dict[str, Any]]:
        """Generate AI-powered SEO action plan."""
        try:
            prompt = f"""
            Based on the following SEO analysis, create a prioritized action plan:
            
            SEO Results: {json.dumps(seo_results, indent=2)}
            Keyword Analysis: {json.dumps(keyword_analysis, indent=2)}
            Competitor Insights: {json.dumps(competitor_insights, indent=2)}
            
            Create a JSON array of action items with the following structure:
            {{
                "priority": "high|medium|low",
                "category": "technical|content|keywords|links",
                "action": "specific action to take",
                "impact": "expected impact description",
                "effort": "low|medium|high",
                "timeline": "immediate|1-2 weeks|1 month|ongoing"
            }}
            
            Focus on actionable, specific recommendations that will have measurable impact.
            """
            
            response = await self.ollama.generate_response(prompt, model="llama3.1")
            
            # Parse JSON response
            try:
                action_plan = json.loads(response)
                if isinstance(action_plan, list):
                    return action_plan
            except json.JSONDecodeError:
                pass
            
            # Fallback action plan
            return [
                {
                    "priority": "high",
                    "category": "technical",
                    "action": "Fix critical technical SEO issues",
                    "impact": "Improve crawlability and indexing",
                    "effort": "medium",
                    "timeline": "1-2 weeks"
                },
                {
                    "priority": "high",
                    "category": "content",
                    "action": "Optimize existing content for target keywords",
                    "impact": "Increase organic rankings",
                    "effort": "medium",
                    "timeline": "ongoing"
                }
            ]
        
        except Exception as e:
            self.logger.error(f"Error generating SEO action plan: {e}")
            return []
    
    async def _create_graphics_package(self, order_id: str, brand_colors: List[str], 
                                     content_themes: List[str], platforms: List[str], 
                                     tier: ServiceTier) -> GraphicsPackage:
        """Create a social media graphics package with actual image generation."""
        try:
            # Determine graphics count based on tier
            graphics_count = 10 if tier == ServiceTier.BASIC else 25
            
            # Create deliverables directory
            deliverables_dir = self.deliverables_path / order_id
            deliverables_dir.mkdir(exist_ok=True)
            images_dir = deliverables_dir / "images"
            images_dir.mkdir(exist_ok=True)
            
            # Generate actual graphics if PIL is available
            generated_images = []
            graphics_urls = []
            
            if GRAPHICS_AVAILABLE:
                generated_images = await self._generate_actual_graphics(
                    order_id, brand_colors, content_themes, platforms, graphics_count, images_dir
                )
                graphics_urls = [str(img_path) for img_path in generated_images]
            else:
                # Fallback to placeholder URLs
                for i in range(graphics_count):
                    graphics_urls.append(f"https://placeholder.graphics/{order_id}_{i+1}.png")
            
            package = GraphicsPackage(
                package_id=order_id,
                theme="professional",
                platforms=platforms,
                graphics_count=graphics_count,
                file_formats=["PNG", "JPG", "PDF"],
                brand_colors=brand_colors,
                font_preferences=["Arial", "Helvetica", "Open Sans"],
                graphics_urls=graphics_urls,
                generated_images=[str(img) for img in generated_images] if generated_images else None
            )
            
            return package
        
        except Exception as e:
            self.logger.error(f"Error creating graphics package: {e}")
            raise
    
    def _calculate_seo_impact(self, seo_results: Dict, action_plan: List) -> Dict[str, float]:
        """Calculate estimated SEO impact."""
        base_score = seo_results.get('overall_score', 50)
        high_priority_actions = len([a for a in action_plan if a.get('priority') == 'high'])
        
        return {
            'traffic_increase_percent': min(high_priority_actions * 15, 100),
            'ranking_improvement': min(high_priority_actions * 5, 30),
            'technical_score_improvement': min(base_score * 0.3, 25)
        }
    
    async def _generate_actual_graphics(self, order_id: str, brand_colors: List[str], 
                                      content_themes: List[str], platforms: List[str], 
                                      graphics_count: int, images_dir: Path) -> List[Path]:
        """Generate actual social media graphics using PIL."""
        if not GRAPHICS_AVAILABLE:
            return []
        
        generated_images = []
        
        # Platform-specific dimensions
        platform_sizes = {
            'instagram': [(1080, 1080), (1080, 1350), (1920, 1080)],  # Square, Portrait, Story
            'facebook': [(1200, 630), (1080, 1080), (1920, 1080)],    # Cover, Post, Story
            'twitter': [(1200, 675), (1080, 1080)],                   # Header, Post
            'linkedin': [(1200, 627), (1080, 1080)],                  # Article, Post
            'pinterest': [(1000, 1500), (735, 1102)]                  # Standard, Optimal
        }
        
        try:
            # Generate graphics for each platform and theme combination
            for i in range(graphics_count):
                platform = platforms[i % len(platforms)]
                theme = content_themes[i % len(content_themes)]
                sizes = platform_sizes.get(platform, [(1080, 1080)])
                size = sizes[i % len(sizes)]
                
                # Create image
                img = Image.new('RGB', size, color=brand_colors[0] if brand_colors else '#1DA1F2')
                draw = ImageDraw.Draw(img)
                
                # Add gradient background
                await self._add_gradient_background(img, draw, brand_colors)
                
                # Add text content
                await self._add_text_content(img, draw, theme, platform, size)
                
                # Add design elements
                await self._add_design_elements(img, draw, brand_colors, size)
                
                # Save image
                filename = f"{platform}_{theme}_{i+1}_{size[0]}x{size[1]}.png"
                img_path = images_dir / filename
                img.save(img_path, 'PNG', quality=95)
                generated_images.append(img_path)
                
                self.logger.info(f"Generated graphic: {filename}")
            
            return generated_images
            
        except Exception as e:
            self.logger.error(f"Error generating graphics: {e}")
            return []
    
    async def _add_gradient_background(self, img: Image.Image, draw: ImageDraw.Draw, brand_colors: List[str]):
        """Add gradient background to image."""
        try:
            width, height = img.size
            if len(brand_colors) >= 2:
                # Simple gradient simulation
                color1 = brand_colors[0]
                color2 = brand_colors[1] if len(brand_colors) > 1 else brand_colors[0]
                
                # Create vertical gradient effect
                for y in range(height):
                    # Simple linear interpolation between colors
                    ratio = y / height
                    # For simplicity, just use solid colors in sections
                    if ratio < 0.5:
                        draw.rectangle([(0, y), (width, y+1)], fill=color1)
                    else:
                        draw.rectangle([(0, y), (width, y+1)], fill=color2)
        except Exception as e:
            self.logger.error(f"Error adding gradient: {e}")
    
    async def _add_text_content(self, img: Image.Image, draw: ImageDraw.Draw, theme: str, platform: str, size: Tuple[int, int]):
        """Add text content to image."""
        try:
            width, height = size
            
            # Generate theme-appropriate text
            text_content = await self._generate_text_for_theme(theme, platform)
            
            # Try to load a font, fallback to default
            try:
                font_size = max(24, min(width, height) // 20)
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (centered)
            bbox = draw.textbbox((0, 0), text_content, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # Add text with shadow effect
            draw.text((x+2, y+2), text_content, fill='black', font=font)  # Shadow
            draw.text((x, y), text_content, fill='white', font=font)      # Main text
            
        except Exception as e:
            self.logger.error(f"Error adding text: {e}")
    
    async def _add_design_elements(self, img: Image.Image, draw: ImageDraw.Draw, brand_colors: List[str], size: Tuple[int, int]):
        """Add design elements to image."""
        try:
            width, height = size
            accent_color = brand_colors[1] if len(brand_colors) > 1 else '#FFFFFF'
            
            # Add corner decorations
            corner_size = min(width, height) // 10
            
            # Top-left corner
            draw.rectangle([(0, 0), (corner_size, corner_size)], fill=accent_color)
            
            # Bottom-right corner
            draw.rectangle([(width-corner_size, height-corner_size), (width, height)], fill=accent_color)
            
            # Add border
            border_width = max(2, min(width, height) // 200)
            draw.rectangle([(0, 0), (width, border_width)], fill=accent_color)  # Top
            draw.rectangle([(0, height-border_width), (width, height)], fill=accent_color)  # Bottom
            draw.rectangle([(0, 0), (border_width, height)], fill=accent_color)  # Left
            draw.rectangle([(width-border_width, 0), (width, height)], fill=accent_color)  # Right
            
        except Exception as e:
            self.logger.error(f"Error adding design elements: {e}")
    
    async def _generate_text_for_theme(self, theme: str, platform: str) -> str:
        """Generate appropriate text content for theme and platform."""
        theme_texts = {
            'motivational': ['BELIEVE', 'ACHIEVE', 'INSPIRE', 'SUCCEED', 'DREAM BIG'],
            'business': ['GROWTH', 'SUCCESS', 'STRATEGY', 'INNOVATION', 'RESULTS'],
            'lifestyle': ['BALANCE', 'WELLNESS', 'MINDFUL', 'AUTHENTIC', 'THRIVE'],
            'tech': ['DIGITAL', 'FUTURE', 'INNOVATION', 'SMART', 'CONNECTED'],
            'general': ['QUALITY', 'EXCELLENCE', 'PROFESSIONAL', 'PREMIUM', 'ELITE']
        }
        
        texts = theme_texts.get(theme, theme_texts['general'])
        import random
        return random.choice(texts)
    
    async def _save_seo_deliverables(self, order_id: str, audit_result: SEOAuditResult) -> Path:
        """Save SEO audit deliverables."""
        deliverables_dir = self.deliverables_path / order_id
        deliverables_dir.mkdir(exist_ok=True)
        
        # Save JSON report
        report_path = deliverables_dir / "seo_audit_report.json"
        with open(report_path, 'w') as f:
            json.dump(asdict(audit_result), f, indent=2, default=str)
        
        # Create summary report
        summary_path = deliverables_dir / "executive_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(f"SEO Audit Report for {audit_result.domain}\n")
            f.write(f"Overall Score: {audit_result.overall_score}/100\n\n")
            f.write(f"Key Issues Found: {len(audit_result.technical_issues)}\n")
            f.write(f"Action Items: {len(audit_result.action_plan)}\n\n")
            f.write("Top Recommendations:\n")
            for i, rec in enumerate(audit_result.content_recommendations[:5], 1):
                f.write(f"{i}. {rec}\n")
        
        return deliverables_dir
    
    async def _save_graphics_deliverables(self, order_id: str, graphics_package: GraphicsPackage) -> Path:
        """Save social media graphics deliverables with PDF packaging."""
        deliverables_dir = self.deliverables_path / order_id
        deliverables_dir.mkdir(exist_ok=True)
        
        # Create images directory
        images_dir = deliverables_dir / 'images'
        images_dir.mkdir(exist_ok=True)
        
        # Generate actual graphics if PIL is available
        if GRAPHICS_AVAILABLE and graphics_package.generated_images:
            # Copy generated images to deliverables directory
            for img_path_str in graphics_package.generated_images:
                img_path = Path(img_path_str)
                if img_path.exists():
                    dest_path = images_dir / img_path.name
                    import shutil
                    shutil.copy2(img_path, dest_path)
        
        # Save package info
        package_path = deliverables_dir / "graphics_package.json"
        with open(package_path, 'w') as f:
            json.dump(asdict(graphics_package), f, indent=2)
        
        # Create usage guidelines
        guidelines_path = deliverables_dir / "usage_guidelines.txt"
        with open(guidelines_path, 'w') as f:
            f.write(f"Social Media Graphics Package - {order_id}\n")
            f.write(f"Total Graphics: {graphics_package.graphics_count}\n")
            f.write(f"Platforms: {', '.join(graphics_package.platforms)}\n")
            f.write(f"Brand Colors: {', '.join(graphics_package.brand_colors)}\n\n")
            f.write("Usage Guidelines:\n")
            f.write("- Use graphics consistently across platforms\n")
            f.write("- Maintain brand color scheme\n")
            f.write("- Include your logo/branding as needed\n")
            f.write("- Commercial usage rights included\n")
            f.write("- Resize appropriately for each platform\n")
            f.write("- Test graphics on different devices\n")
        
        graphics_package.usage_guide_path = str(guidelines_path)
        
        # Create PDF package if reportlab is available
        if GRAPHICS_AVAILABLE:
            pdf_path = await self._create_graphics_pdf_package(order_id, graphics_package, deliverables_dir)
            graphics_package.pdf_package_path = str(pdf_path)
        
        # Create brand guidelines document
        brand_guidelines_path = await self._create_brand_guidelines(order_id, graphics_package, deliverables_dir)
        graphics_package.brand_guidelines_path = str(brand_guidelines_path)
        
        return deliverables_dir
    
    async def _create_graphics_pdf_package(self, order_id: str, graphics_package: GraphicsPackage, deliverables_dir: Path) -> Path:
        """Create a PDF package containing all graphics and guidelines."""
        try:
            pdf_path = deliverables_dir / f"graphics_package_{order_id}.pdf"
            
            # Create PDF document
            doc = SimpleDocTemplate(str(pdf_path), pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=HexColor('#1DA1F2')
            )
            story.append(Paragraph(f"Social Media Graphics Package", title_style))
            story.append(Paragraph(f"Order ID: {order_id}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Package details
            story.append(Paragraph("Package Details", styles['Heading2']))
            story.append(Paragraph(f"Graphics Count: {graphics_package.graphics_count}", styles['Normal']))
            story.append(Paragraph(f"Platforms: {', '.join(graphics_package.platforms)}", styles['Normal']))
            story.append(Paragraph(f"Brand Colors: {', '.join(graphics_package.brand_colors)}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Usage guidelines
            story.append(Paragraph("Usage Guidelines", styles['Heading2']))
            guidelines = [
                "Use graphics consistently across all platforms",
                "Maintain brand color scheme for consistency",
                "Add your logo/branding as needed",
                "Commercial usage rights included",
                "Resize appropriately for each platform",
                "Test graphics on different devices"
            ]
            for guideline in guidelines:
                story.append(Paragraph(f"• {guideline}", styles['Normal']))
            
            story.append(Spacer(1, 20))
            
            # Platform specifications
            story.append(Paragraph("Platform Specifications", styles['Heading2']))
            platform_specs = {
                'instagram': 'Square: 1080x1080, Portrait: 1080x1350, Story: 1920x1080',
                'facebook': 'Cover: 1200x630, Post: 1080x1080, Story: 1920x1080',
                'twitter': 'Header: 1200x675, Post: 1080x1080',
                'linkedin': 'Article: 1200x627, Post: 1080x1080',
                'pinterest': 'Standard: 1000x1500, Optimal: 735x1102'
            }
            
            for platform in graphics_package.platforms:
                if platform in platform_specs:
                    story.append(Paragraph(f"<b>{platform.title()}:</b> {platform_specs[platform]}", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            self.logger.error(f"Error creating PDF package: {e}")
            # Return a placeholder path
            return deliverables_dir / "graphics_package_placeholder.pdf"
    
    async def _create_brand_guidelines(self, order_id: str, graphics_package: GraphicsPackage, deliverables_dir: Path) -> Path:
        """Create brand guidelines document."""
        try:
            guidelines_path = deliverables_dir / "brand_guidelines.md"
            
            with open(guidelines_path, 'w') as f:
                f.write(f"# Brand Guidelines - {order_id}\n\n")
                f.write(f"## Color Palette\n")
                for i, color in enumerate(graphics_package.brand_colors, 1):
                    f.write(f"- **Color {i}:** {color}\n")
                
                f.write(f"\n## Typography\n")
                for font in graphics_package.font_preferences:
                    f.write(f"- {font}\n")
                
                f.write(f"\n## Platform Guidelines\n")
                for platform in graphics_package.platforms:
                    f.write(f"\n### {platform.title()}\n")
                    f.write(f"- Maintain consistent branding\n")
                    f.write(f"- Use appropriate dimensions\n")
                    f.write(f"- Follow platform best practices\n")
                
                f.write(f"\n## Usage Rights\n")
                f.write(f"- Commercial usage permitted\n")
                f.write(f"- Modification allowed\n")
                f.write(f"- Attribution not required\n")
                f.write(f"- Resale prohibited\n")
            
            return guidelines_path
            
        except Exception as e:
            self.logger.error(f"Error creating brand guidelines: {e}")
            return deliverables_dir / "brand_guidelines_placeholder.md"
    
    async def _deliver_service(self, order_id: str) -> Dict[str, Any]:
        """Mark service as delivered and update stats."""
        try:
            order = await self._get_order(order_id)
            if not order:
                return {'status': 'error', 'message': 'Order not found'}
            
            order.status = DeliveryStatus.DELIVERED
            order.completed_at = datetime.now(timezone.utc)
            await self._save_order(order)
            
            # Send delivery email if deliverables exist
            email_sent = False
            if order.deliverables_path:
                deliverables_path = Path(order.deliverables_path)
                if deliverables_path.exists():
                    email_sent = await self._send_delivery_email(order, deliverables_path)
            
            # Update revenue stats
            await self._update_revenue_stats(order.service_package.price)
            
            return {
                'status': 'success',
                'order_id': order_id,
                'delivered_at': order.completed_at.isoformat(),
                'email_sent': email_sent
            }
        
        except Exception as e:
            self.logger.error(f"Error delivering service: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_service_packages(self) -> Dict[str, Any]:
        """Get available service packages.
        
        Returns:
            Dict[str, Any]: Always returns a dictionary with 'packages' and 'total_packages' keys.
                           Never returns None to prevent TypeError when calling .get() on the result.
        """
        result = self._get_service_packages()
        # Extra safety check to ensure we never return None
        if result is None:
            self.logger.error("_get_service_packages returned None, returning empty dict")
            return {'packages': {}, 'total_packages': 0, 'error': 'Service packages unavailable'}
        return result
    
    def _get_service_packages(self) -> Dict[str, Any]:
        """Get available service packages.
        
        Returns:
            Dict[str, Any]: Always returns a dictionary, never None.
        """
        try:
            # Ensure service_packages is initialized
            if self.service_packages is None:
                self.logger.warning("Service packages not initialized, reinitializing...")
                try:
                    self.service_packages = self._initialize_service_packages()
                except Exception as init_error:
                    self.logger.error(f"Failed to initialize service packages: {init_error}")
                    return {'packages': {}, 'total_packages': 0, 'error': f'Initialization failed: {init_error}'}
            
            # Handle empty service packages
            if not self.service_packages:
                self.logger.warning("Service packages is empty")
                return {'packages': {}, 'total_packages': 0, 'error': 'No service packages available'}
            
            # Convert service packages to dictionary format
            packages_dict = {}
            for k, v in self.service_packages.items():
                try:
                    if v is None:
                        self.logger.warning(f"Service package {k} is None, skipping")
                        packages_dict[k] = {'error': 'Package data is None'}
                        continue
                    packages_dict[k] = asdict(v)
                except Exception as e:
                    self.logger.error(f"Error converting package {k} to dict: {e}")
                    packages_dict[k] = {'error': str(e)}
            
            result = {
                'packages': packages_dict,
                'total_packages': len(self.service_packages)
            }
            
            # Final safety check
            if result is None:
                self.logger.error("Result is None, this should never happen")
                return {'packages': {}, 'total_packages': 0, 'error': 'Unexpected None result'}
                
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting service packages: {e}")
            # Always return a dictionary, never None
            return {'packages': {}, 'total_packages': 0, 'error': str(e)}
    
    def _get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get order status."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            for order_data in data['orders']:
                if order_data['order_id'] == order_id:
                    return {
                        'status': 'found',
                        'order': order_data
                    }
            
            return {'status': 'not_found'}
        
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _get_order(self, order_id: str) -> Optional[ServiceOrder]:
        """Get order by ID."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            for order_data in data['orders']:
                if order_data['order_id'] == order_id:
                    # Convert back to ServiceOrder object
                    order_data['created_at'] = datetime.fromisoformat(order_data['created_at'])
                    order_data['due_date'] = datetime.fromisoformat(order_data['due_date'])
                    if order_data.get('completed_at'):
                        order_data['completed_at'] = datetime.fromisoformat(order_data['completed_at'])
                    
                    # Reconstruct service package
                    pkg_data = order_data['service_package']
                    service_package = ServicePackage(
                        service_type=ServiceType(pkg_data['service_type']),
                        tier=ServiceTier(pkg_data['tier']),
                        name=pkg_data['name'],
                        description=pkg_data['description'],
                        price=pkg_data['price'],
                        delivery_time_hours=pkg_data['delivery_time_hours'],
                        features=pkg_data['features'],
                        requirements=pkg_data['requirements'],
                        deliverables=pkg_data['deliverables']
                    )
                    
                    return ServiceOrder(
                        order_id=order_data['order_id'],
                        client_email=order_data['client_email'],
                        service_package=service_package,
                        requirements=order_data['requirements'],
                        status=DeliveryStatus(order_data['status']),
                        created_at=order_data['created_at'],
                        due_date=order_data['due_date'],
                        completed_at=order_data.get('completed_at'),
                        deliverables_path=order_data.get('deliverables_path'),
                        client_feedback=order_data.get('client_feedback'),
                        rating=order_data.get('rating')
                    )
            
            return None
        
        except Exception as e:
            self.logger.error(f"Error getting order: {e}")
            return None
    
    async def _save_order(self, order: ServiceOrder):
        """Save order to database."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            # Convert order to dict for JSON serialization
            order_dict = asdict(order)
            order_dict['created_at'] = order.created_at.isoformat()
            order_dict['due_date'] = order.due_date.isoformat()
            if order.completed_at:
                order_dict['completed_at'] = order.completed_at.isoformat()
            
            # Update or add order
            updated = False
            for i, existing_order in enumerate(data['orders']):
                if existing_order['order_id'] == order.order_id:
                    data['orders'][i] = order_dict
                    updated = True
                    break
            
            if not updated:
                data['orders'].append(order_dict)
            
            with open(self.orders_db_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error saving order: {e}")
    
    async def _update_revenue_stats(self, amount: float):
        """Update revenue statistics."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            data['stats']['total_revenue'] += amount
            data['stats']['completed_orders'] += 1
            
            with open(self.orders_db_path, 'w') as f:
                json.dump(data, f, indent=2)
        
        except Exception as e:
            self.logger.error(f"Error updating revenue stats: {e}")
    
    def get_revenue_stats(self) -> Dict[str, Any]:
        """Get revenue statistics."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            return data.get('stats', {'total_revenue': 0, 'completed_orders': 0})
        except Exception as e:
            self.logger.error(f"Error getting revenue stats: {e}")
            return {'total_revenue': 0, 'completed_orders': 0}
    
    def create_order(self, package_id: str, client_email: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new service order."""
        try:
            if package_id not in self.service_packages:
                return {'status': 'error', 'message': 'Invalid package ID'}
            
            package = self.service_packages[package_id]
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Calculate due date
            due_date = datetime.now(timezone.utc) + timedelta(hours=package.delivery_time_hours)
            
            order = ServiceOrder(
                order_id=order_id,
                client_email=client_email,
                service_package=package,
                requirements=requirements,
                status=DeliveryStatus.PENDING,
                created_at=datetime.now(timezone.utc),
                due_date=due_date
            )
            
            # Save order to file-based database
            self._save_order_to_file(order)
            
            self.logger.info(f"Created order {order_id} for {client_email}")
            
            return {
                'status': 'success',
                'order_id': order_id,
                'estimated_delivery': order.due_date.isoformat(),
                'price': package.price
            }
            
        except Exception as e:
            self.logger.error(f"Error creating order: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get the status of a specific order."""
        try:
            # Load orders from file
            if not os.path.exists(self.orders_db_path):
                return {'status': 'not_found'}
            
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            orders = data.get('orders', [])
            
            # Find the order
            for order_data in orders:
                if order_data.get('order_id') == order_id:
                    return {'status': 'found', 'order': order_data}
            
            return {'status': 'not_found'}
            
        except Exception as e:
            self.logger.error(f"Error getting order status: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def _save_order_to_file(self, order: ServiceOrder):
        """Save order to file-based database."""
        try:
            # Load existing data
            if os.path.exists(self.orders_db_path):
                with open(self.orders_db_path, 'r') as f:
                    data = json.load(f)
            else:
                data = {'orders': []}
            
            # Convert order to dict
            order_dict = {
                'order_id': order.order_id,
                'client_email': order.client_email,
                'service_package': {
                    'name': order.service_package.name,
                    'service_type': order.service_package.service_type.value,
                    'tier': order.service_package.tier.value,
                    'price': order.service_package.price,
                    'delivery_time_hours': order.service_package.delivery_time_hours,
                    'features': order.service_package.features
                },
                'requirements': order.requirements,
                'status': order.status.value,
                'created_at': order.created_at.isoformat(),
                'due_date': order.due_date.isoformat(),
                'completed_at': order.completed_at.isoformat() if order.completed_at else None,
                'deliverables_path': order.deliverables_path
            }
            
            # Add to orders list
            data['orders'].append(order_dict)
            
            # Save back to file
            with open(self.orders_db_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving order to file: {e}")
            raise
    
    async def _send_delivery_email(self, order: ServiceOrder, deliverables_path: Path) -> bool:
        """Send delivery email to client with attachments."""
        try:
            if not order.client_email:
                return False
            
            # Email configuration (should be in config)
            smtp_server = self.config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
            smtp_port = self.config.get('email', {}).get('smtp_port', 587)
            email_user = self.config.get('email', {}).get('username', '')
            email_pass = self.config.get('email', {}).get('password', '')
            
            if not email_user or not email_pass:
                self.logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = order.client_email
            msg['Subject'] = f"Your {order.service_package.name} is Ready - Order #{order.order_id}"
            
            # Email body
            body = f"""
            Dear Valued Client,
            
            Your {order.service_package.name} has been completed and is ready for download!
            
            Order Details:
            - Order ID: {order.order_id}
            - Service: {order.service_package.name}
            - Completed: {order.completed_at.strftime('%Y-%m-%d %H:%M UTC') if order.completed_at else 'N/A'}
            
            Your deliverables are attached to this email. Please review the included guidelines and documentation.
            
            If you have any questions or need revisions, please don't hesitate to contact us.
            
            Thank you for choosing our services!
            
            Best regards,
            AI Services Team
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach deliverables
            await self._attach_deliverables(msg, deliverables_path)
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_user, email_pass)
            text = msg.as_string()
            server.sendmail(email_user, order.client_email, text)
            server.quit()
            
            self.logger.info(f"Delivery email sent to {order.client_email} for order {order.order_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending delivery email: {e}")
            return False
    
    async def _attach_deliverables(self, msg: MIMEMultipart, deliverables_path: Path):
        """Attach deliverable files to email."""
        try:
            # Attach key files (limit size to avoid email limits)
            max_attachment_size = 10 * 1024 * 1024  # 10MB limit
            
            for file_path in deliverables_path.rglob('*'):
                if file_path.is_file() and file_path.stat().st_size < max_attachment_size:
                    # Skip very large files
                    if file_path.suffix.lower() in ['.json', '.txt', '.md', '.pdf']:
                        with open(file_path, 'rb') as f:
                            attachment = MIMEApplication(f.read())
                            attachment.add_header(
                                'Content-Disposition',
                                'attachment',
                                filename=file_path.name
                            )
                            msg.attach(attachment)
            
        except Exception as e:
            self.logger.error(f"Error attaching deliverables: {e}")
    
    def get_engagement_stats(self) -> Dict[str, Any]:
        """Get engagement statistics for monetization services."""
        try:
            with open(self.orders_db_path, 'r') as f:
                data = json.load(f)
            
            orders = data.get('orders', [])
            total_orders = len(orders)
            completed_orders = len([o for o in orders if o.get('status') == 'completed'])
            pending_orders = len([o for o in orders if o.get('status') == 'pending'])
            in_progress_orders = len([o for o in orders if o.get('status') == 'in_progress'])
            
            # Calculate average completion time
            completion_times = []
            for order in orders:
                if order.get('status') == 'completed' and order.get('completed_at') and order.get('created_at'):
                    try:
                        created = datetime.fromisoformat(order['created_at'])
                        completed = datetime.fromisoformat(order['completed_at'])
                        hours = (completed - created).total_seconds() / 3600
                        completion_times.append(hours)
                    except:
                        continue
            
            avg_completion_hours = sum(completion_times) / len(completion_times) if completion_times else 0
            
            # Get unique clients
            unique_clients = len(set(o.get('client_email', '') for o in orders if o.get('client_email')))
            
            # Calculate total revenue from completed orders
            total_revenue = sum(
                o.get('service_package', {}).get('price', 0) 
                for o in orders 
                if o.get('status') == 'completed'
            )
            
            completion_rate = (completed_orders / max(total_orders, 1)) * 100
            
            return {
                'total_orders': total_orders,
                'completed_orders': completed_orders,
                'pending_orders': pending_orders,
                'in_progress_orders': in_progress_orders,
                'avg_completion_hours': round(avg_completion_hours, 2),
                'total_revenue': total_revenue,
                'unique_clients': unique_clients,
                'completion_rate': round(completion_rate, 2)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting engagement stats: {e}")
            return {
                'total_orders': 0,
                'completed_orders': 0,
                'pending_orders': 0,
                'in_progress_orders': 0,
                'avg_completion_hours': 0,
                'total_revenue': 0,
                'unique_clients': 0,
                'completion_rate': 0
            }
    
    async def _execute_with_monitoring(self, task: Dict[str, Any], context) -> Dict[str, Any]:
        """Execute task with monitoring - required abstract method implementation"""
        try:
            # Process the task using existing process_task method
            result = await self.process_task(task)
            return result
        except Exception as e:
            self.logger.error(f"Error executing task with monitoring: {e}")
            return {
                'success': False,
                'error': str(e),
                'task_id': task.get('id', 'unknown')
            }
    
    async def _rephrase_task(self, task: Dict[str, Any], context) -> str:
        """Rephrase task - required abstract method implementation"""
        # For now, return the original task description
        task_type = task.get('type', 'unknown')
        task_description = task.get('description', f"Process {task_type} task")
        return f"Monetization Services: {task_description}"
    
    async def _validate_rephrase_accuracy(self, original_task: Dict[str, Any], rephrased: str, context) -> bool:
        """Validate rephrase accuracy - required abstract method implementation"""
        # For now, always return True as basic validation
        return True