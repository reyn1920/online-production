#!/usr/bin/env python3
"""
Financial Agent Router

Integrates the financial agent service with the main FastAPI application.
Provides endpoints for financial analysis, resource allocation, and ROI optimization.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import uuid
import asyncio

# Try to import financial agent
try:
    from backend.agents.financial_agent import FinancialAgent
except ImportError:
    try:
        from copy_of_code.agents.financial_agent import FinancialAgent
    except ImportError:
        FinancialAgent = None
        logging.warning("Financial agent not available - check backend structure")

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response Models


class FinancialAnalysisRequest(BaseModel):
    channel_id: str = Field(..., description="Channel identifier")
    revenue: float = Field(..., description="Revenue amount")
    costs: float = Field(..., description="Cost amount")
    time_period: Optional[str] = Field("monthly", description="Analysis time period")
    include_forecast: Optional[bool] = Field(
        False, description="Include forecast analysis")


class ResourceAllocationRequest(BaseModel):
    total_budget: float = Field(..., description="Total budget to allocate")
    channels: List[str] = Field(..., description="List of channels")
    strategy: Optional[str] = Field(
        "profit_maximization",
        description="Allocation strategy")
    risk_tolerance: Optional[float] = Field(0.3, description="Risk tolerance (0-1)")


class ROIOptimizationRequest(BaseModel):
    current_allocations: Dict[str,
                              float] = Field(...,
                                             description="Current resource allocations")
    performance_data: Dict[str, Any] = Field(..., description="Performance metrics")
    optimization_target: Optional[str] = Field("roi", description="Optimization target")


class FinancialReportRequest(BaseModel):
    start_date: datetime = Field(..., description="Report start date")
    end_date: datetime = Field(..., description="Report end date")
    channels: Optional[List[str]] = Field(
        None, description="Specific channels to include")
    report_type: Optional[str] = Field("comprehensive", description="Type of report")


class FinancialResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    job_id: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# In-memory job tracking
financial_jobs = {}

# Initialize financial agent
financial_agent = None
if FinancialAgent:
    try:
        financial_agent = FinancialAgent(
            agent_id="main_financial_agent",
            name="Financial Management Agent",
            config={
                'analysis_interval': 3600,
                'reallocation_threshold': 0.15,
                'min_roi_threshold': 0.1,
                'risk_tolerance': 0.3,
                'strategy': 'profit_maximization'
            }
        )
        logger.info("Financial agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize financial agent: {e}")
        financial_agent = None


@router.get("/")
async def financial_interface():
    """Get financial management interface status"""
    return {
        "service": "Financial Agent",
        "status": "active" if financial_agent else "unavailable",
        "features": [
            "Profitability Analysis",
            "Resource Allocation",
            "ROI Optimization",
            "Financial Forecasting",
            "Performance Monitoring"
        ]
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy" if financial_agent else "unavailable",
        "agent_available": financial_agent is not None,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/analyze", response_model=FinancialResponse)
async def analyze_profitability(
        request: FinancialAnalysisRequest,
        background_tasks: BackgroundTasks):
    """Analyze channel profitability"""
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial agent not available")

    try:
        job_id = str(uuid.uuid4())

        # Store job info
        financial_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "profitability_analysis"
        }

        # Start analysis in background
        background_tasks.add_task(
            run_profitability_analysis,
            job_id,
            request.dict()
        )

        return FinancialResponse(
            success=True,
            job_id=job_id,
            message="Profitability analysis started"
        )

    except Exception as e:
        logger.error(f"Error starting profitability analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/allocate", response_model=FinancialResponse)
async def optimize_resource_allocation(
        request: ResourceAllocationRequest,
        background_tasks: BackgroundTasks):
    """Optimize resource allocation across channels"""
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial agent not available")

    try:
        job_id = str(uuid.uuid4())

        # Store job info
        financial_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "resource_allocation"
        }

        # Start allocation in background
        background_tasks.add_task(
            run_resource_allocation,
            job_id,
            request.dict()
        )

        return FinancialResponse(
            success=True,
            job_id=job_id,
            message="Resource allocation optimization started"
        )

    except Exception as e:
        logger.error(f"Error starting resource allocation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-roi", response_model=FinancialResponse)
async def optimize_roi(
        request: ROIOptimizationRequest,
        background_tasks: BackgroundTasks):
    """Optimize ROI based on current performance"""
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial agent not available")

    try:
        job_id = str(uuid.uuid4())

        # Store job info
        financial_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "roi_optimization"
        }

        # Start optimization in background
        background_tasks.add_task(
            run_roi_optimization,
            job_id,
            request.dict()
        )

        return FinancialResponse(
            success=True,
            job_id=job_id,
            message="ROI optimization started"
        )

    except Exception as e:
        logger.error(f"Error starting ROI optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report", response_model=FinancialResponse)
async def generate_financial_report(
        request: FinancialReportRequest,
        background_tasks: BackgroundTasks):
    """Generate comprehensive financial report"""
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial agent not available")

    try:
        job_id = str(uuid.uuid4())

        # Store job info
        financial_jobs[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "type": "financial_report"
        }

        # Start report generation in background
        background_tasks.add_task(
            run_financial_report,
            job_id,
            request.dict()
        )

        return FinancialResponse(
            success=True,
            job_id=job_id,
            message="Financial report generation started"
        )

    except Exception as e:
        logger.error(f"Error starting financial report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get financial job status"""
    if job_id not in financial_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = financial_jobs[job_id]
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        updated_at=job["updated_at"]
    )


@router.get("/metrics")
async def get_financial_metrics():
    """Get current financial metrics"""
    if not financial_agent:
        raise HTTPException(status_code=503, detail="Financial agent not available")

    try:
        # Get current metrics from agent
        metrics = {
            "total_revenue": 0.0,
            "total_costs": 0.0,
            "net_profit": 0.0,
            "roi": 0.0,
            "active_channels": 0,
            "last_updated": datetime.now().isoformat()
        }

        if hasattr(financial_agent, 'financial_metrics'):
            agent_metrics = financial_agent.financial_metrics
            if hasattr(agent_metrics, 'total_revenue'):
                metrics["total_revenue"] = float(agent_metrics.total_revenue)
            if hasattr(agent_metrics, 'total_costs'):
                metrics["total_costs"] = float(agent_metrics.total_costs)
            if hasattr(agent_metrics, 'net_profit'):
                metrics["net_profit"] = float(agent_metrics.net_profit)
            if hasattr(agent_metrics, 'overall_roi'):
                metrics["roi"] = float(agent_metrics.overall_roi)

        return metrics

    except Exception as e:
        logger.error(f"Error getting financial metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def list_financial_jobs():
    """List all financial jobs"""
    return {
        "jobs": [
            {
                "job_id": job_id,
                "status": job_info["status"],
                "type": job_info["type"],
                "created_at": job_info["created_at"].isoformat(),
                "progress": job_info.get("progress", 0.0)
            }
            for job_id, job_info in financial_jobs.items()
        ]
    }

# Background task functions


async def run_profitability_analysis(job_id: str, request_data: Dict[str, Any]):
    """Run profitability analysis in background"""
    try:
        financial_jobs[job_id]["progress"] = 25.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        # Simulate analysis
        await asyncio.sleep(2)

        # Calculate basic profitability metrics
        revenue = request_data.get("revenue", 0)
        costs = request_data.get("costs", 0)
        profit = revenue - costs
        roi = (profit / costs * 100) if costs > 0 else 0

        financial_jobs[job_id]["progress"] = 75.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        # Simulate more processing
        await asyncio.sleep(1)

        result = {
            "channel_id": request_data.get("channel_id"),
            "revenue": revenue,
            "costs": costs,
            "profit": profit,
            "roi_percentage": roi,
            "profitability_score": min(100, max(0, roi)),
            "recommendations": [
                "Monitor cost efficiency",
                "Optimize resource allocation",
                "Consider scaling successful strategies"
            ]
        }

        financial_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "result": result,
            "updated_at": datetime.now()
        })

    except Exception as e:
        financial_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now()
        })


async def run_resource_allocation(job_id: str, request_data: Dict[str, Any]):
    """Run resource allocation optimization in background"""
    try:
        financial_jobs[job_id]["progress"] = 20.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        # Simulate allocation optimization
        await asyncio.sleep(3)

        total_budget = request_data.get("total_budget", 0)
        channels = request_data.get("channels", [])

        # Simple equal allocation for demo
        allocation_per_channel = total_budget / len(channels) if channels else 0

        financial_jobs[job_id]["progress"] = 80.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        await asyncio.sleep(1)

        result = {
            "total_budget": total_budget,
            "allocations": {channel: allocation_per_channel for channel in channels},
            "strategy": request_data.get("strategy", "profit_maximization"),
            "expected_roi": 15.5,  # Mock value
            "risk_score": request_data.get("risk_tolerance", 0.3) * 100
        }

        financial_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "result": result,
            "updated_at": datetime.now()
        })

    except Exception as e:
        financial_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now()
        })


async def run_roi_optimization(job_id: str, request_data: Dict[str, Any]):
    """Run ROI optimization in background"""
    try:
        financial_jobs[job_id]["progress"] = 30.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        # Simulate ROI optimization
        await asyncio.sleep(2)

        current_allocations = request_data.get("current_allocations", {})

        financial_jobs[job_id]["progress"] = 70.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        await asyncio.sleep(1)

        # Mock optimization results
        optimized_allocations = {}
        for channel, allocation in current_allocations.items():
            # Simulate optimization by adjusting allocations
            optimized_allocations[channel] = allocation * 1.1  # 10% increase

        result = {
            "current_allocations": current_allocations,
            "optimized_allocations": optimized_allocations,
            "expected_roi_improvement": 12.5,  # Mock percentage
            "optimization_confidence": 85.0,
            "recommendations": [
                "Increase investment in high-performing channels",
                "Reduce allocation to underperforming areas",
                "Monitor performance closely after changes"
            ]
        }

        financial_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "result": result,
            "updated_at": datetime.now()
        })

    except Exception as e:
        financial_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now()
        })


async def run_financial_report(job_id: str, request_data: Dict[str, Any]):
    """Generate financial report in background"""
    try:
        financial_jobs[job_id]["progress"] = 25.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        # Simulate report generation
        await asyncio.sleep(3)

        financial_jobs[job_id]["progress"] = 75.0
        financial_jobs[job_id]["updated_at"] = datetime.now()

        await asyncio.sleep(2)

        result = {
            "report_period": f"{
                request_data.get('start_date')} to {
                request_data.get('end_date')}",
            "summary": {
                "total_revenue": 50000.0,
                "total_costs": 35000.0,
                "net_profit": 15000.0,
                "roi_percentage": 42.86},
            "channel_performance": {
                "youtube": {
                    "revenue": 20000,
                    "costs": 12000,
                    "roi": 66.67},
                "tiktok": {
                    "revenue": 15000,
                    "costs": 10000,
                    "roi": 50.0},
                "instagram": {
                    "revenue": 15000,
                    "costs": 13000,
                    "roi": 15.38}},
            "trends": [
                "YouTube showing strongest ROI growth",
                "TikTok maintaining steady performance",
                "Instagram needs optimization"],
            "generated_at": datetime.now().isoformat()}

        financial_jobs[job_id].update({
            "status": "completed",
            "progress": 100.0,
            "result": result,
            "updated_at": datetime.now()
        })

    except Exception as e:
        financial_jobs[job_id].update({
            "status": "failed",
            "error": str(e),
            "updated_at": datetime.now()
        })

__all__ = ["router"]
