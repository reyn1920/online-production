#!/usr/bin/env python3
"""
Financial Agent Router

Integrates the financial agent service with the main FastAPI application.
Provides endpoints for financial analysis, resource allocation, and ROI optimization.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/financial", tags=["financial"])

# In-memory storage for simplified implementation
financial_data = {}
analysis_results = {}
budget_allocations = {}

# Pydantic Models
class FinancialRequest(BaseModel):
    """Request model for financial analysis."""
    project_id: str
    budget: float = Field(gt=0, description="Total budget amount")
    timeframe: str = Field(default="monthly", description="Analysis timeframe")
    categories: List[str] = Field(default_factory=list, description="Budget categories")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FinancialResponse(BaseModel):
    """Response model for financial operations."""
    id: str
    project_id: str
    budget: float
    allocated_budget: float
    remaining_budget: float
    roi_projection: float
    recommendations: List[str]
    created_at: str
    status: str

class BudgetAllocation(BaseModel):
    """Model for budget allocation."""
    category: str
    amount: float = Field(gt=0)
    percentage: float = Field(ge=0, le=100)
    priority: str = Field(default="medium")

class ROIAnalysis(BaseModel):
    """Model for ROI analysis results."""
    id: str
    project_id: str
    investment: float
    projected_return: float
    roi_percentage: float
    payback_period: str
    risk_level: str
    created_at: str

# Helper functions
def calculate_roi(investment: float, projected_return: float) -> float:
    """Calculate ROI percentage."""
    if investment <= 0:
        return 0.0
    return ((projected_return - investment) / investment) * 100

def generate_recommendations(budget: float, categories: List[str]) -> List[str]:
    """Generate financial recommendations."""
    recommendations = [
        "Consider diversifying budget allocation across categories",
        "Monitor spending regularly to stay within budget",
        "Set aside 10-15% for unexpected expenses"
    ]
    
    if budget > 10000:
        recommendations.append("Consider investing in automation tools for better ROI")
    
    if len(categories) > 5:
        recommendations.append("Consolidate similar categories to simplify tracking")
    
    return recommendations

# API Endpoints
@router.post("/analyze", response_model=FinancialResponse)
async def create_financial_analysis(request: FinancialRequest):
    """Create a new financial analysis."""
    try:
        analysis_id = str(uuid4())
        
        # Simulate financial analysis
        allocated_budget = request.budget * 0.85  # 85% allocation
        remaining_budget = request.budget - allocated_budget
        roi_projection = calculate_roi(request.budget, request.budget * 1.2)  # 20% ROI projection
        
        analysis_data = {
            "id": analysis_id,
            "project_id": request.project_id,
            "budget": request.budget,
            "allocated_budget": allocated_budget,
            "remaining_budget": remaining_budget,
            "roi_projection": roi_projection,
            "recommendations": generate_recommendations(request.budget, request.categories),
            "created_at": datetime.now().isoformat(),
            "status": "completed"
        }
        
        financial_data[analysis_id] = analysis_data
        logger.info(f"Created financial analysis: {analysis_id}")
        
        return FinancialResponse(
            id=str(analysis_data["id"]),
            project_id=str(analysis_data["project_id"]),
            budget=float(analysis_data["budget"]) if isinstance(analysis_data["budget"], (int, float, str)) else 0.0,
            allocated_budget=float(analysis_data["allocated_budget"]) if isinstance(analysis_data["allocated_budget"], (int, float, str)) else 0.0,
            remaining_budget=float(analysis_data["remaining_budget"]) if isinstance(analysis_data["remaining_budget"], (int, float, str)) else 0.0,
            roi_projection=float(analysis_data["roi_projection"]) if isinstance(analysis_data["roi_projection"], (int, float, str)) else 0.0,
            recommendations=analysis_data["recommendations"] if isinstance(analysis_data["recommendations"], list) else [],
            created_at=str(analysis_data["created_at"]),
            status=str(analysis_data["status"])
        )
        
    except Exception as e:
        logger.error(f"Error creating financial analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create financial analysis")

@router.get("/analyze/{analysis_id}", response_model=FinancialResponse)
async def get_financial_analysis(analysis_id: str):
    """Get a specific financial analysis."""
    if analysis_id not in financial_data:
        raise HTTPException(status_code=404, detail="Financial analysis not found")
    
    data = financial_data[analysis_id]
    return FinancialResponse(
        id=str(data["id"]),
        project_id=str(data["project_id"]),
        budget=float(data["budget"]) if isinstance(data["budget"], (int, float, str)) else 0.0,
        allocated_budget=float(data["allocated_budget"]) if isinstance(data["allocated_budget"], (int, float, str)) else 0.0,
        remaining_budget=float(data["remaining_budget"]) if isinstance(data["remaining_budget"], (int, float, str)) else 0.0,
        roi_projection=float(data["roi_projection"]) if isinstance(data["roi_projection"], (int, float, str)) else 0.0,
        recommendations=data["recommendations"] if isinstance(data["recommendations"], list) else [],
        created_at=str(data["created_at"]),
        status=str(data["status"])
    )

@router.get("/analyze", response_model=List[FinancialResponse])
async def list_financial_analyses(project_id: Optional[str] = None):
    """List all financial analyses, optionally filtered by project."""
    analyses = list(financial_data.values())
    
    if project_id:
        analyses = [a for a in analyses if a["project_id"] == project_id]
    
    result = []
    for analysis in analyses:
        result.append(FinancialResponse(
            id=str(analysis["id"]),
            project_id=str(analysis["project_id"]),
            budget=float(analysis["budget"]) if isinstance(analysis["budget"], (int, float, str)) else 0.0,
            allocated_budget=float(analysis["allocated_budget"]) if isinstance(analysis["allocated_budget"], (int, float, str)) else 0.0,
            remaining_budget=float(analysis["remaining_budget"]) if isinstance(analysis["remaining_budget"], (int, float, str)) else 0.0,
            roi_projection=float(analysis["roi_projection"]) if isinstance(analysis["roi_projection"], (int, float, str)) else 0.0,
            recommendations=analysis["recommendations"] if isinstance(analysis["recommendations"], list) else [],
            created_at=str(analysis["created_at"]),
            status=str(analysis["status"])
        ))
    return result

@router.post("/allocate", response_model=Dict[str, Any])
async def allocate_budget(project_id: str, allocations: List[BudgetAllocation]):
    """Allocate budget across categories."""
    try:
        allocation_id = str(uuid4())
        total_percentage = sum(alloc.percentage for alloc in allocations)
        
        if total_percentage > 100:
            raise HTTPException(status_code=400, detail="Total allocation exceeds 100%")
        
        allocation_data = {
            "id": allocation_id,
            "project_id": project_id,
            "allocations": [alloc.dict() for alloc in allocations],
            "total_percentage": total_percentage,
            "created_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        budget_allocations[allocation_id] = allocation_data
        logger.info(f"Created budget allocation: {allocation_id}")
        
        return allocation_data
        
    except Exception as e:
        logger.error(f"Error creating budget allocation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create budget allocation")

@router.post("/roi-analysis", response_model=ROIAnalysis)
async def create_roi_analysis(project_id: str, investment: float, projected_return: float):
    """Create ROI analysis."""
    try:
        analysis_id = str(uuid4())
        roi_percentage = calculate_roi(investment, projected_return)
        
        # Simple payback period calculation (in months)
        monthly_return = (projected_return - investment) / 12
        payback_months = investment / monthly_return if monthly_return > 0 else 0
        payback_period = f"{payback_months:.1f} months"
        
        # Risk assessment based on ROI
        if roi_percentage > 50:
            risk_level = "high"
        elif roi_percentage > 20:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        roi_data = {
            "id": analysis_id,
            "project_id": project_id,
            "investment": investment,
            "projected_return": projected_return,
            "roi_percentage": roi_percentage,
            "payback_period": payback_period,
            "risk_level": risk_level,
            "created_at": datetime.now().isoformat()
        }
        
        analysis_results[analysis_id] = roi_data
        logger.info(f"Created ROI analysis: {analysis_id}")
        
        return ROIAnalysis(
            id=str(roi_data["id"]),
            project_id=str(roi_data["project_id"]),
            investment=float(roi_data["investment"]) if isinstance(roi_data["investment"], (int, float, str)) else 0.0,
            projected_return=float(roi_data["projected_return"]) if isinstance(roi_data["projected_return"], (int, float, str)) else 0.0,
            roi_percentage=float(roi_data["roi_percentage"]) if isinstance(roi_data["roi_percentage"], (int, float, str)) else 0.0,
            payback_period=str(roi_data["payback_period"]),
            risk_level=str(roi_data["risk_level"]),
            created_at=str(roi_data["created_at"])
        )
        
    except Exception as e:
        logger.error(f"Error creating ROI analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create ROI analysis")

@router.get("/roi-analysis/{analysis_id}", response_model=ROIAnalysis)
async def get_roi_analysis(analysis_id: str):
    """Get a specific ROI analysis."""
    if analysis_id not in analysis_results:
        raise HTTPException(status_code=404, detail="ROI analysis not found")
    
    data = analysis_results[analysis_id]
    return ROIAnalysis(
        id=str(data["id"]),
        project_id=str(data["project_id"]),
        investment=float(data["investment"]) if isinstance(data["investment"], (int, float, str)) else 0.0,
        projected_return=float(data["projected_return"]) if isinstance(data["projected_return"], (int, float, str)) else 0.0,
        roi_percentage=float(data["roi_percentage"]) if isinstance(data["roi_percentage"], (int, float, str)) else 0.0,
        payback_period=str(data["payback_period"]),
        risk_level=str(data["risk_level"]),
        created_at=str(data["created_at"])
    )

@router.get("/health")
async def financial_health_check():
    """Health check endpoint for financial service."""
    return {
        "status": "healthy",
        "service": "financial",
        "analyses_count": len(financial_data),
        "roi_analyses_count": len(analysis_results),
        "allocations_count": len(budget_allocations),
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/analyze/{analysis_id}")
async def delete_financial_analysis(analysis_id: str):
    """Delete a financial analysis."""
    if analysis_id not in financial_data:
        raise HTTPException(status_code=404, detail="Financial analysis not found")
    
    del financial_data[analysis_id]
    logger.info(f"Deleted financial analysis: {analysis_id}")
    
    return {"message": "Financial analysis deleted successfully"}

# Background task for periodic cleanup
async def cleanup_old_analyses():
    """Clean up old financial analyses (placeholder for future implementation)."""
    logger.info("Cleanup task executed")

@router.post("/cleanup")
async def trigger_cleanup(background_tasks: BackgroundTasks):
    """Trigger cleanup of old analyses."""
    background_tasks.add_task(cleanup_old_analyses)
    return {"message": "Cleanup task scheduled"}