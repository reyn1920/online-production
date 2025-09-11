#!/usr/bin/env python3
"""
Monetization Router - Integrates monetization bundle services with main FastAPI app
Handles ebook generation, newsletter automation, merch design, and revenue tracking
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

# Import monetization bundle components
try:
    from monetization_bundle.main import (BlogPostRequest, EbookRequest, MerchRequest,
                                          MonetizationBundle, MonetizationConfig,
                                          NewsletterRequest)

    MONETIZATION_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Monetization bundle not available: {e}")
    MONETIZATION_AVAILABLE = False

# Request/Response Models


class EbookGenerationRequest(BaseModel):
    title: str = Field(..., description="Title of the ebook")
    content: str = Field(..., description="Content for the ebook")
    author: str = Field(default="TRAE.AI", description="Author name")
    price: float = Field(default=9.99, description="Price for the ebook")
    format: str = Field(default="pdf", description="Format: pdf, epub, docx")
    cover_image_url: Optional[str] = Field(None, description="URL for cover image")


class NewsletterCreationRequest(BaseModel):
    subject: str = Field(..., description="Newsletter subject line")
    content: str = Field(..., description="Newsletter content")
    subscriber_list: List[str] = Field(
        default=[], description="List of subscriber emails"
    )
    include_affiliate_links: bool = Field(
        default=True, description="Include affiliate links"
    )
    send_time: Optional[datetime] = Field(None, description="Scheduled send time")


class MerchDesignRequest(BaseModel):
    design_name: str = Field(..., description="Name of the design")
    product_type: str = Field(..., description="Product type: tshirt, mug, poster")
    design_prompt: str = Field(..., description="Design description/prompt")
    price: float = Field(default=19.99, description="Product price")
    platform: str = Field(default="printful", description="Publishing platform")


class BlogPostCreationRequest(BaseModel):
    title: str = Field(..., description="Blog post title")
    content: str = Field(..., description="Blog post content")
    platform: str = Field(default="wordpress", description="Publishing platform")
    seo_keywords: List[str] = Field(default=[], description="SEO keywords")
    include_affiliate_links: bool = Field(
        default=True, description="Include affiliate links"
    )


class MonetizationJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_completion: Optional[datetime] = None
    result_url: Optional[str] = None


class RevenueStatsResponse(BaseModel):
    total_revenue: float
    ebook_revenue: float
    merch_revenue: float
    affiliate_revenue: float
    newsletter_revenue: float
    products_sold: int
    active_campaigns: int
    last_updated: datetime


# Create router
router = APIRouter(prefix="/monetization", tags=["monetization"])

# In-memory job tracking
jobs = {}

# Initialize monetization bundle
if MONETIZATION_AVAILABLE:
    config = MonetizationConfig()
    monetization_bundle = MonetizationBundle(config)
else:
    monetization_bundle = None


@router.get("/health")
async def health_check():
    """Check monetization service health"""
    return {
        "status": "healthy" if MONETIZATION_AVAILABLE else "unavailable",
        "service": "monetization",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "ebook_generator": MONETIZATION_AVAILABLE,
            "newsletter_bot": MONETIZATION_AVAILABLE,
            "merch_bot": MONETIZATION_AVAILABLE,
            "seo_publisher": MONETIZATION_AVAILABLE,
        },
    }


@router.post("/ebook/generate", response_model=MonetizationJobResponse)
async def generate_ebook(
    request: EbookGenerationRequest, background_tasks: BackgroundTasks
):
    """Generate an ebook and publish it"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization service unavailable")

    job_id = f"ebook_{uuid4().hex[:8]}"

    # Initialize job
    jobs[job_id] = {
        "status": "pending",
        "type": "ebook_generation",
        "created_at": datetime.now(),
        "progress": 0,
        "result": None,
        "error": None,
    }

    # Start background task
    background_tasks.add_task(process_ebook_generation, job_id, request)

    return MonetizationJobResponse(
        job_id=job_id,
        status="pending",
        message="Ebook generation started",
        estimated_completion=datetime.now() + timedelta(minutes=5),
    )


@router.post("/newsletter/create", response_model=MonetizationJobResponse)
async def create_newsletter(
    request: NewsletterCreationRequest, background_tasks: BackgroundTasks
):
    """Create and send newsletter"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization service unavailable")

    job_id = f"newsletter_{uuid4().hex[:8]}"

    # Initialize job
    jobs[job_id] = {
        "status": "pending",
        "type": "newsletter_creation",
        "created_at": datetime.now(),
        "progress": 0,
        "result": None,
        "error": None,
    }

    # Start background task
    background_tasks.add_task(process_newsletter_creation, job_id, request)

    return MonetizationJobResponse(
        job_id=job_id,
        status="pending",
        message="Newsletter creation started",
        estimated_completion=datetime.now() + timedelta(minutes=3),
    )


@router.post("/merch/design", response_model=MonetizationJobResponse)
async def create_merch_design(
    request: MerchDesignRequest, background_tasks: BackgroundTasks
):
    """Create merchandise design and publish"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization service unavailable")

    job_id = f"merch_{uuid4().hex[:8]}"

    # Initialize job
    jobs[job_id] = {
        "status": "pending",
        "type": "merch_design",
        "created_at": datetime.now(),
        "progress": 0,
        "result": None,
        "error": None,
    }

    # Start background task
    background_tasks.add_task(process_merch_design, job_id, request)

    return MonetizationJobResponse(
        job_id=job_id,
        status="pending",
        message="Merch design creation started",
        estimated_completion=datetime.now() + timedelta(minutes=10),
    )


@router.post("/blog/publish", response_model=MonetizationJobResponse)
async def publish_blog_post(
    request: BlogPostCreationRequest, background_tasks: BackgroundTasks
):
    """Publish SEO-optimized blog post"""
    if not MONETIZATION_AVAILABLE:
        raise HTTPException(status_code=503, detail="Monetization service unavailable")

    job_id = f"blog_{uuid4().hex[:8]}"

    # Initialize job
    jobs[job_id] = {
        "status": "pending",
        "type": "blog_publishing",
        "created_at": datetime.now(),
        "progress": 0,
        "result": None,
        "error": None,
    }

    # Start background task
    background_tasks.add_task(process_blog_publishing, job_id, request)

    return MonetizationJobResponse(
        job_id=job_id,
        status="pending",
        message="Blog post publishing started",
        estimated_completion=datetime.now() + timedelta(minutes=2),
    )


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a monetization job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "type": job["type"],
        "progress": job["progress"],
        "created_at": job["created_at"].isoformat(),
        "result": job["result"],
        "error": job["error"],
    }


@router.get("/revenue/stats", response_model=RevenueStatsResponse)
async def get_revenue_stats():
    """Get revenue statistics"""
    if not MONETIZATION_AVAILABLE or not monetization_bundle:
        # Return empty stats when service unavailable
        return RevenueStatsResponse(
            total_revenue=0.0,
            ebook_revenue=0.0,
            merch_revenue=0.0,
            affiliate_revenue=0.0,
            newsletter_revenue=0.0,
            products_sold=0,
            active_campaigns=0,
            last_updated=datetime.now(),
        )

    try:
        # Get real stats from monetization bundle
        stats = await asyncio.to_thread(monetization_bundle.get_revenue_stats)

        return RevenueStatsResponse(
            total_revenue=stats.get("total_revenue", 0.0),
            ebook_revenue=stats.get("ebook_revenue", 0.0),
            merch_revenue=stats.get("merch_revenue", 0.0),
            affiliate_revenue=stats.get("affiliate_revenue", 0.0),
            newsletter_revenue=stats.get("newsletter_revenue", 0.0),
            products_sold=stats.get("products_sold", 0),
            active_campaigns=stats.get("active_campaigns", 0),
            last_updated=datetime.now(),
        )
    except Exception as e:
        logger.error(f"Error getting revenue stats: {e}")
        # Return fallback data on error
        return RevenueStatsResponse(
            total_revenue=0.0,
            ebook_revenue=0.0,
            merch_revenue=0.0,
            affiliate_revenue=0.0,
            newsletter_revenue=0.0,
            products_sold=0,
            active_campaigns=0,
            last_updated=datetime.now(),
        )


@router.get("/products")
async def list_products():
    """List all monetization products"""
    if not MONETIZATION_AVAILABLE or not monetization_bundle:
        return {"products": [], "total": 0}

    try:
        # Get real product data from monetization bundle
        products_data = await asyncio.to_thread(monetization_bundle.get_products)
        products = products_data.get("products", [])

        return {
            "products": products,
            "total": len(products),
            "last_updated": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        # Return empty list on error
        return {"products": [], "total": 0}


@router.get("/campaigns")
async def list_campaigns():
    """List active marketing campaigns"""
    if not MONETIZATION_AVAILABLE:
        return {"campaigns": [], "total": 0}

    # Mock campaign data
    campaigns = [
        {
            "id": "camp_001",
            "name": "Holiday Ebook Promotion",
            "type": "email",
            "status": "active",
            "subscribers": 2450,
            "open_rate": 0.24,
            "click_rate": 0.08,
            "revenue": 1250.75,
        },
        {
            "id": "camp_002",
            "name": "Merch Launch Campaign",
            "type": "social",
            "status": "active",
            "reach": 15600,
            "engagement_rate": 0.12,
            "conversions": 34,
            "revenue": 849.66,
        },
    ]

    return {"campaigns": campaigns, "total": len(campaigns)}


# Background task functions


async def process_ebook_generation(job_id: str, request: EbookGenerationRequest):
    """Background task to generate ebook"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 25

        if monetization_bundle:
            # Generate ebook using monetization bundle
            file_path = await monetization_bundle.ebook_generator.generate_ebook(
                title=request.title,
                content=request.content,
                author=request.author,
                format=request.format,
            )

            jobs[job_id]["progress"] = 75

            # Publish to Gumroad
            publish_result = (
                await monetization_bundle.gumroad_publisher.publish_product(
                    name=request.title,
                    price=request.price,
                    file_path=file_path,
                    description=f"Ebook by {request.author}",
                )
            )

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "file_path": file_path,
                "publish_result": publish_result,
                "download_url": f"/monetization/download/{job_id}",
            }
        else:
            # Mock completion
            await asyncio.sleep(2)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "file_path": f"mock_ebook_{job_id}.pdf",
                "publish_result": {"success": True, "product_id": f"mock_{job_id}"},
                "download_url": f"/monetization/download/{job_id}",
            }

    except Exception as e:
        logger.error(f"Ebook generation failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def process_newsletter_creation(job_id: str, request: NewsletterCreationRequest):
    """Background task to create and send newsletter"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 30

        if monetization_bundle:
            # Create and send newsletter
            result = (
                await monetization_bundle.newsletter_bot.create_and_send_newsletter(
                    subject=request.subject,
                    content=request.content,
                    subscribers=request.subscriber_list,
                    include_affiliate_links=request.include_affiliate_links,
                )
            )

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = result
        else:
            # Mock completion
            await asyncio.sleep(1)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "success": True,
                "sent_count": len(request.subscriber_list),
                "campaign_id": f"mock_campaign_{job_id}",
            }

    except Exception as e:
        logger.error(f"Newsletter creation failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def process_merch_design(job_id: str, request: MerchDesignRequest):
    """Background task to create merch design"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 20

        if monetization_bundle:
            # Create design
            design_path = await monetization_bundle.merch_bot.create_merch_design(
                design_name=request.design_name,
                product_type=request.product_type,
                design_prompt=request.design_prompt,
            )

            jobs[job_id]["progress"] = 70

            # Publish to platform
            publish_result = await monetization_bundle.merch_bot.publish_to_printful(
                design_path=design_path,
                product_type=request.product_type,
                price=request.price,
            )

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "design_path": design_path,
                "publish_result": publish_result,
            }
        else:
            # Mock completion
            await asyncio.sleep(3)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "design_path": f"mock_design_{job_id}.png",
                "publish_result": {
                    "success": True,
                    "product_id": f"mock_merch_{job_id}",
                },
            }

    except Exception as e:
        logger.error(f"Merch design creation failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


async def process_blog_publishing(job_id: str, request: BlogPostCreationRequest):
    """Background task to publish blog post"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 40

        if monetization_bundle:
            # Publish blog post
            result = await monetization_bundle.seo_publisher.publish_blog_post(
                title=request.title,
                content=request.content,
                platform=request.platform,
                seo_keywords=request.seo_keywords,
                include_affiliate_links=request.include_affiliate_links,
            )

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = result
        else:
            # Mock completion
            await asyncio.sleep(1)
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["result"] = {
                "success": True,
                "post_url": f"https://mock-blog.com/posts/{job_id}",
                "post_id": f"mock_post_{job_id}",
            }

    except Exception as e:
        logger.error(f"Blog publishing failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


@router.get("/download/{job_id}")
async def download_file(job_id: str):
    """Download generated file"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    if job["status"] != "completed" or not job["result"]:
        raise HTTPException(status_code=400, detail="File not ready")

    # Return file download info
    return {"job_id": job_id, "file_info": job["result"], "download_ready": True}
