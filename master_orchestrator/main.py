#!/usr/bin/env python3
"""
Master Orchestrator

Central coordination system for managing various services and operations.
Provides unified interface for system management and monitoring.
"""

import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])

# In-memory storage for demo purposes
system_status: Dict[str, Any] = {
    "services": {},
    "health_checks": {},
    "last_updated": datetime.now().isoformat()
}

operations_log: List[Dict[str, Any]] = []
market_opportunities: List[Dict[str, Any]] = []

class ServiceStatus(BaseModel):
    service_name: str = Field(..., description="Name of the service")
    status: str = Field(..., description="Service status (active, inactive, error)")
    last_check: str = Field(..., description="Last health check timestamp")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional service metadata")

class OperationRequest(BaseModel):
    operation_type: str = Field(..., description="Type of operation to perform")
    target_service: Optional[str] = Field(None, description="Target service for operation")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Operation parameters")
    priority: Optional[str] = Field("medium", description="Operation priority")

class MarketOpportunity(BaseModel):
    trend_topic: str = Field(..., description="Trending topic or niche")
    niche: str = Field(..., description="Market niche")
    monetization_potential: float = Field(..., ge=0, le=10, description="Monetization potential (0-10)")
    competition_level: str = Field(..., description="Competition level (low, medium, high)")
    recommended_business_models: List[str] = Field(..., description="Recommended business models")
    market_size: Optional[str] = Field(None, description="Estimated market size")
    entry_barriers: Optional[str] = Field(None, description="Entry barriers")

def init_database():
    """Initialize the database with required tables."""
    # For demo purposes, we'll use in-memory storage
    # In production, this would set up actual database tables
    pass

def log_operation(operation_type: str, details: Dict[str, Any]):
    """Log an operation to the operations log."""
    operation = {
        "id": len(operations_log) + 1,
        "operation_type": operation_type,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "status": "completed"
    }
    operations_log.append(operation)
    
    # Keep only last 1000 operations
    if len(operations_log) > 1000:
        operations_log.pop(0)

@router.post("/services/register")
async def register_service(service: ServiceStatus):
    """Register a new service with the orchestrator."""
    system_status["services"][service.service_name] = {
        "status": service.status,
        "last_check": service.last_check,
        "uptime": service.uptime,
        "metadata": service.metadata or {},
        "registered_at": datetime.now().isoformat()
    }
    
    system_status["last_updated"] = datetime.now().isoformat()
    
    log_operation("service_registration", {
        "service_name": service.service_name,
        "status": service.status
    })
    
    return {
        "message": "Service registered successfully",
        "service_name": service.service_name,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/services/status")
async def get_services_status():
    """Get status of all registered services."""
    return {
        "services": system_status["services"],
        "total_services": len(system_status["services"]),
        "last_updated": system_status["last_updated"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/services/{service_name}/status")
async def get_service_status(service_name: str):
    """Get status of a specific service."""
    if service_name not in system_status["services"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    service_data = system_status["services"][service_name]
    
    return {
        "service_name": service_name,
        "status": service_data["status"],
        "last_check": service_data["last_check"],
        "uptime": service_data.get("uptime"),
        "metadata": service_data.get("metadata", {}),
        "registered_at": service_data.get("registered_at"),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/services/{service_name}/health-check")
async def perform_health_check(service_name: str):
    """Perform health check on a specific service."""
    if service_name not in system_status["services"]:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Simulate health check
    health_status = "healthy"  # In real implementation, this would check actual service
    
    system_status["health_checks"][service_name] = {
        "status": health_status,
        "checked_at": datetime.now().isoformat(),
        "response_time": 0.05  # Simulated response time
    }
    
    # Update service status
    system_status["services"][service_name]["last_check"] = datetime.now().isoformat()
    system_status["services"][service_name]["status"] = "active" if health_status == "healthy" else "error"
    
    log_operation("health_check", {
        "service_name": service_name,
        "health_status": health_status
    })
    
    return {
        "service_name": service_name,
        "health_status": health_status,
        "checked_at": datetime.now().isoformat(),
        "response_time": 0.05
    }

@router.post("/operations/execute")
async def execute_operation(operation: OperationRequest):
    """Execute a system operation."""
    operation_id = len(operations_log) + 1
    
    # Simulate operation execution
    result = {
        "operation_id": operation_id,
        "operation_type": operation.operation_type,
        "target_service": operation.target_service,
        "status": "completed",
        "started_at": datetime.now().isoformat(),
        "completed_at": datetime.now().isoformat(),
        "result": f"Operation {operation.operation_type} completed successfully"
    }
    
    log_operation(operation.operation_type, {
        "operation_id": operation_id,
        "target_service": operation.target_service,
        "parameters": operation.parameters,
        "priority": operation.priority
    })
    
    return result

@router.get("/operations/log")
async def get_operations_log(
    limit: int = 50,
    operation_type: Optional[str] = None
):
    """Get operations log."""
    filtered_operations = operations_log
    
    if operation_type:
        filtered_operations = [
            op for op in operations_log 
            if op["operation_type"] == operation_type
        ]
    
    # Sort by timestamp (newest first)
    filtered_operations.sort(
        key=lambda x: x["timestamp"], 
        reverse=True
    )
    
    return {
        "operations": filtered_operations[:limit],
        "total_count": len(filtered_operations),
        "timestamp": datetime.now().isoformat()
    }

@router.post("/market/opportunities")
async def add_market_opportunity(opportunity: MarketOpportunity):
    """Add a new market opportunity."""
    opportunity_data = {
        "id": len(market_opportunities) + 1,
        "trend_topic": opportunity.trend_topic,
        "niche": opportunity.niche,
        "monetization_potential": opportunity.monetization_potential,
        "competition_level": opportunity.competition_level,
        "recommended_business_models": opportunity.recommended_business_models,
        "market_size": opportunity.market_size,
        "entry_barriers": opportunity.entry_barriers,
        "created_at": datetime.now().isoformat(),
        "status": "active"
    }
    
    market_opportunities.append(opportunity_data)
    
    log_operation("market_opportunity_added", {
        "opportunity_id": opportunity_data["id"],
        "trend_topic": opportunity.trend_topic,
        "niche": opportunity.niche
    })
    
    return {
        "message": "Market opportunity added successfully",
        "opportunity_id": opportunity_data["id"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/market/opportunities")
async def get_market_opportunities(
    limit: int = 20,
    competition_level: Optional[str] = None,
    min_potential: Optional[float] = None
):
    """Get market opportunities."""
    filtered_opportunities = market_opportunities
    
    if competition_level:
        filtered_opportunities = [
            opp for opp in filtered_opportunities 
            if opp["competition_level"] == competition_level
        ]
    
    if min_potential is not None:
        filtered_opportunities = [
            opp for opp in filtered_opportunities 
            if opp["monetization_potential"] >= min_potential
        ]
    
    # Sort by monetization potential (highest first)
    filtered_opportunities.sort(
        key=lambda x: x["monetization_potential"], 
        reverse=True
    )
    
    return {
        "opportunities": filtered_opportunities[:limit],
        "total_count": len(filtered_opportunities),
        "timestamp": datetime.now().isoformat()
    }

@router.get("/market/opportunities/{opportunity_id}")
async def get_market_opportunity(opportunity_id: int):
    """Get a specific market opportunity."""
    opportunity = None
    for opp in market_opportunities:
        if opp["id"] == opportunity_id:
            opportunity = opp
            break
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Market opportunity not found")
    
    return opportunity

@router.put("/market/opportunities/{opportunity_id}")
async def update_market_opportunity(opportunity_id: int, opportunity: MarketOpportunity):
    """Update a market opportunity."""
    existing_opportunity = None
    for i, opp in enumerate(market_opportunities):
        if opp["id"] == opportunity_id:
            existing_opportunity = opp
            break
    
    if not existing_opportunity:
        raise HTTPException(status_code=404, detail="Market opportunity not found")
    
    # Update the opportunity
    existing_opportunity.update({
        "trend_topic": opportunity.trend_topic,
        "niche": opportunity.niche,
        "monetization_potential": opportunity.monetization_potential,
        "competition_level": opportunity.competition_level,
        "recommended_business_models": opportunity.recommended_business_models,
        "market_size": opportunity.market_size,
        "entry_barriers": opportunity.entry_barriers,
        "updated_at": datetime.now().isoformat()
    })
    
    log_operation("market_opportunity_updated", {
        "opportunity_id": opportunity_id,
        "trend_topic": opportunity.trend_topic
    })
    
    return {
        "message": "Market opportunity updated successfully",
        "opportunity_id": opportunity_id,
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/market/opportunities/{opportunity_id}")
async def delete_market_opportunity(opportunity_id: int):
    """Delete a market opportunity."""
    opportunity_index = None
    for i, opp in enumerate(market_opportunities):
        if opp["id"] == opportunity_id:
            opportunity_index = i
            break
    
    if opportunity_index is None:
        raise HTTPException(status_code=404, detail="Market opportunity not found")
    
    deleted_opportunity = market_opportunities.pop(opportunity_index)
    
    log_operation("market_opportunity_deleted", {
        "opportunity_id": opportunity_id,
        "trend_topic": deleted_opportunity["trend_topic"]
    })
    
    return {
        "message": "Market opportunity deleted successfully",
        "opportunity_id": opportunity_id,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/system/overview")
async def get_system_overview():
    """Get comprehensive system overview."""
    # Calculate system metrics
    total_services = len(system_status["services"])
    active_services = sum(
        1 for service in system_status["services"].values() 
        if service["status"] == "active"
    )
    
    recent_operations = len([
        op for op in operations_log 
        if datetime.fromisoformat(op["timestamp"]) > datetime.now() - timedelta(hours=24)
    ])
    
    high_potential_opportunities = len([
        opp for opp in market_opportunities 
        if opp["monetization_potential"] >= 7.0
    ])
    
    return {
        "system_health": {
            "total_services": total_services,
            "active_services": active_services,
            "service_uptime_percentage": (active_services / total_services * 100) if total_services > 0 else 0
        },
        "operations": {
            "total_operations": len(operations_log),
            "recent_operations_24h": recent_operations
        },
        "market_intelligence": {
            "total_opportunities": len(market_opportunities),
            "high_potential_opportunities": high_potential_opportunities
        },
        "last_updated": system_status["last_updated"],
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def orchestrator_health():
    """Check orchestrator service health."""
    return {
        "ok": True,
        "service": "master_orchestrator",
        "total_services": len(system_status["services"]),
        "total_operations": len(operations_log),
        "total_opportunities": len(market_opportunities),
        "timestamp": datetime.now().isoformat()
    }

# Initialize database on module load
init_database()