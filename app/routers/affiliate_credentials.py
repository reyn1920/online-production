#!/usr/bin/env python3
"""
Affiliate Credentials Router

Manages affiliate dashboard credentials and authentication.
"""

import logging
import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, EmailStr

router = APIRouter(prefix="/affiliate", tags=["affiliate"])
security = HTTPBearer()

# In-memory storage for demo purposes
affiliate_credentials: Dict[str, Dict[str, Any]] = {}
affiliate_sessions: Dict[str, Dict[str, Any]] = {}
affiliate_earnings: Dict[str, List[Dict[str, Any]]] = {}

class AffiliateCredentials(BaseModel):
    username: str = Field(..., description="Affiliate username")
    email: EmailStr = Field(..., description="Affiliate email address")
    password: str = Field(..., description="Affiliate password")
    platform: str = Field(..., description="Affiliate platform (etsy, amazon, etc.)")
    api_key: Optional[str] = Field(None, description="Platform API key")
    commission_rate: Optional[float] = Field(0.05, ge=0, le=1, description="Commission rate (0-1)")
    status: Optional[str] = Field("active", description="Account status")

class AffiliateLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")
    platform: Optional[str] = Field(None, description="Target platform")

class AffiliateUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(None, description="New password")
    api_key: Optional[str] = Field(None, description="New API key")
    commission_rate: Optional[float] = Field(None, ge=0, le=1, description="New commission rate")
    status: Optional[str] = Field(None, description="New account status")

class EarningsRecord(BaseModel):
    affiliate_id: str = Field(..., description="Affiliate identifier")
    amount: float = Field(..., ge=0, description="Earnings amount")
    currency: str = Field("USD", description="Currency code")
    source: str = Field(..., description="Earnings source")
    transaction_id: Optional[str] = Field(None, description="Transaction identifier")
    commission_rate: Optional[float] = Field(None, description="Applied commission rate")

def generate_session_token() -> str:
    """Generate a simple session token."""
    import secrets
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    """Simple password hashing (use proper hashing in production)."""
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == hashed

def get_current_affiliate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated affiliate."""
    token = credentials.credentials
    
    if not token or token not in affiliate_sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    session = affiliate_sessions[token]
    
    # Check if session is expired
    if datetime.fromisoformat(session["expires_at"]) < datetime.now():
        del affiliate_sessions[token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    return session["affiliate_id"]

@router.post("/register")
async def register_affiliate(credentials: AffiliateCredentials):
    """Register a new affiliate."""
    affiliate_id = f"{credentials.platform}_{credentials.username}"
    
    if affiliate_id in affiliate_credentials:
        raise HTTPException(status_code=400, detail="Affiliate already exists")
    
    # Store credentials
    affiliate_credentials[affiliate_id] = {
        "username": credentials.username,
        "email": credentials.email,
        "password_hash": hash_password(credentials.password),
        "platform": credentials.platform,
        "api_key": credentials.api_key,
        "commission_rate": credentials.commission_rate,
        "status": credentials.status,
        "created_at": datetime.now().isoformat(),
        "last_login": None,
        "total_earnings": 0.0
    }
    
    # Initialize earnings record
    affiliate_earnings[affiliate_id] = []
    
    return {
        "message": "Affiliate registered successfully",
        "affiliate_id": affiliate_id,
        "platform": credentials.platform,
        "commission_rate": credentials.commission_rate,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/login")
async def login_affiliate(login_data: AffiliateLogin):
    """Authenticate affiliate and create session."""
    # Find affiliate by username or email
    affiliate_id = None
    affiliate_data = None
    
    for aid, data in affiliate_credentials.items():
        if (data["username"] == login_data.username or 
            data["email"] == login_data.username):
            if login_data.platform is None or data["platform"] == login_data.platform:
                affiliate_id = aid
                affiliate_data = data
                break
    
    if not affiliate_data:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, affiliate_data["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if affiliate_data["status"] != "active":
        raise HTTPException(status_code=403, detail="Account is not active")
    
    # Create session
    session_token = generate_session_token()
    session_expires = datetime.now() + timedelta(hours=24)
    
    affiliate_sessions[session_token] = {
        "affiliate_id": affiliate_id,
        "created_at": datetime.now().isoformat(),
        "expires_at": session_expires.isoformat(),
        "platform": affiliate_data["platform"]
    }
    
    # Update last login
    affiliate_credentials[affiliate_id]["last_login"] = datetime.now().isoformat()
    
    return {
        "message": "Login successful",
        "session_token": session_token,
        "expires_at": session_expires.isoformat(),
        "affiliate_id": affiliate_id,
        "platform": affiliate_data["platform"],
        "commission_rate": affiliate_data["commission_rate"]
    }

@router.post("/logout")
async def logout_affiliate(current_affiliate: str = Depends(get_current_affiliate)):
    """Logout affiliate and invalidate session."""
    # Find and remove session
    token_to_remove = None
    for token, session in affiliate_sessions.items():
        if session["affiliate_id"] == current_affiliate:
            token_to_remove = token
            break
    
    if token_to_remove:
        del affiliate_sessions[token_to_remove]
    
    return {
        "message": "Logout successful",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/profile")
async def get_affiliate_profile(current_affiliate: str = Depends(get_current_affiliate)):
    """Get affiliate profile information."""
    if current_affiliate not in affiliate_credentials:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    profile = affiliate_credentials[current_affiliate].copy()
    
    # Remove sensitive information
    profile.pop("password_hash", None)
    profile.pop("api_key", None)
    
    # Add earnings summary
    earnings = affiliate_earnings.get(current_affiliate, [])
    total_earnings = sum(record["amount"] for record in earnings)
    
    profile.update({
        "total_earnings": total_earnings,
        "total_transactions": len(earnings),
        "average_earning": total_earnings / len(earnings) if earnings else 0
    })
    
    return profile

@router.put("/profile")
async def update_affiliate_profile(
    update_data: AffiliateUpdate,
    current_affiliate: str = Depends(get_current_affiliate)
):
    """Update affiliate profile."""
    if current_affiliate not in affiliate_credentials:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    profile = affiliate_credentials[current_affiliate]
    
    # Update fields if provided
    if update_data.email:
        profile["email"] = update_data.email
    
    if update_data.password:
        profile["password_hash"] = hash_password(update_data.password)
    
    if update_data.api_key is not None:
        profile["api_key"] = update_data.api_key
    
    if update_data.commission_rate is not None:
        profile["commission_rate"] = update_data.commission_rate
    
    if update_data.status:
        profile["status"] = update_data.status
    
    profile["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": "Profile updated successfully",
        "timestamp": datetime.now().isoformat()
    }

@router.post("/earnings")
async def record_earnings(
    earnings: EarningsRecord,
    current_affiliate: str = Depends(get_current_affiliate)
):
    """Record new earnings for affiliate."""
    if current_affiliate not in affiliate_credentials:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    # Create earnings record
    earnings_record = {
        "id": len(affiliate_earnings.get(current_affiliate, [])) + 1,
        "amount": earnings.amount,
        "currency": earnings.currency,
        "source": earnings.source,
        "transaction_id": earnings.transaction_id,
        "commission_rate": earnings.commission_rate or affiliate_credentials[current_affiliate]["commission_rate"],
        "recorded_at": datetime.now().isoformat(),
        "status": "confirmed"
    }
    
    # Add to earnings list
    if current_affiliate not in affiliate_earnings:
        affiliate_earnings[current_affiliate] = []
    
    affiliate_earnings[current_affiliate].append(earnings_record)
    
    # Update total earnings
    affiliate_credentials[current_affiliate]["total_earnings"] += earnings.amount
    
    return {
        "message": "Earnings recorded successfully",
        "earnings_id": earnings_record["id"],
        "amount": earnings.amount,
        "currency": earnings.currency,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/earnings")
async def get_affiliate_earnings(
    current_affiliate: str = Depends(get_current_affiliate),
    limit: int = 50,
    currency: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Get affiliate earnings history."""
    if current_affiliate not in affiliate_earnings:
        return {
            "earnings": [],
            "total_amount": 0,
            "total_count": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    earnings = affiliate_earnings[current_affiliate]
    
    # Apply filters
    if currency:
        earnings = [e for e in earnings if e["currency"] == currency]
    
    if start_date:
        start_dt = datetime.fromisoformat(start_date)
        earnings = [e for e in earnings if datetime.fromisoformat(e["recorded_at"]) >= start_dt]
    
    if end_date:
        end_dt = datetime.fromisoformat(end_date)
        earnings = [e for e in earnings if datetime.fromisoformat(e["recorded_at"]) <= end_dt]
    
    # Sort by date (newest first)
    earnings.sort(key=lambda x: x["recorded_at"], reverse=True)
    
    # Calculate totals
    total_amount = sum(e["amount"] for e in earnings)
    
    return {
        "earnings": earnings[:limit],
        "total_amount": total_amount,
        "total_count": len(earnings),
        "currency_breakdown": {},  # Could add currency breakdown here
        "timestamp": datetime.now().isoformat()
    }

@router.get("/earnings/summary")
async def get_earnings_summary(
    current_affiliate: str = Depends(get_current_affiliate),
    period: str = "month"  # day, week, month, year
):
    """Get earnings summary for specified period."""
    if current_affiliate not in affiliate_earnings:
        return {
            "period": period,
            "total_earnings": 0,
            "transaction_count": 0,
            "average_transaction": 0,
            "timestamp": datetime.now().isoformat()
        }
    
    earnings = affiliate_earnings[current_affiliate]
    
    # Calculate period start
    now = datetime.now()
    if period == "day":
        period_start = now - timedelta(days=1)
    elif period == "week":
        period_start = now - timedelta(weeks=1)
    elif period == "month":
        period_start = now - timedelta(days=30)
    elif period == "year":
        period_start = now - timedelta(days=365)
    else:
        period_start = datetime.min
    
    # Filter earnings by period
    period_earnings = [
        e for e in earnings 
        if datetime.fromisoformat(e["recorded_at"]) >= period_start
    ]
    
    total_earnings = sum(e["amount"] for e in period_earnings)
    transaction_count = len(period_earnings)
    average_transaction = total_earnings / transaction_count if transaction_count > 0 else 0
    
    return {
        "period": period,
        "period_start": period_start.isoformat(),
        "total_earnings": total_earnings,
        "transaction_count": transaction_count,
        "average_transaction": average_transaction,
        "timestamp": datetime.now().isoformat()
    }

@router.get("/dashboard")
async def get_affiliate_dashboard(current_affiliate: str = Depends(get_current_affiliate)):
    """Get comprehensive affiliate dashboard data."""
    if current_affiliate not in affiliate_credentials:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    profile = affiliate_credentials[current_affiliate]
    earnings = affiliate_earnings.get(current_affiliate, [])
    
    # Calculate metrics
    total_earnings = sum(e["amount"] for e in earnings)
    recent_earnings = [
        e for e in earnings 
        if datetime.fromisoformat(e["recorded_at"]) > datetime.now() - timedelta(days=30)
    ]
    monthly_earnings = sum(e["amount"] for e in recent_earnings)
    
    # Active sessions count
    active_sessions = sum(
        1 for session in affiliate_sessions.values() 
        if session["affiliate_id"] == current_affiliate and 
           datetime.fromisoformat(session["expires_at"]) > datetime.now()
    )
    
    return {
        "affiliate_info": {
            "username": profile["username"],
            "email": profile["email"],
            "platform": profile["platform"],
            "status": profile["status"],
            "commission_rate": profile["commission_rate"],
            "member_since": profile["created_at"],
            "last_login": profile.get("last_login")
        },
        "earnings_summary": {
            "total_earnings": total_earnings,
            "monthly_earnings": monthly_earnings,
            "total_transactions": len(earnings),
            "monthly_transactions": len(recent_earnings),
            "average_transaction": total_earnings / len(earnings) if earnings else 0
        },
        "account_status": {
            "active_sessions": active_sessions,
            "account_status": profile["status"],
            "api_key_configured": bool(profile.get("api_key"))
        },
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/account")
async def delete_affiliate_account(current_affiliate: str = Depends(get_current_affiliate)):
    """Delete affiliate account and all associated data."""
    if current_affiliate not in affiliate_credentials:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    # Remove all sessions for this affiliate
    sessions_to_remove = [
        token for token, session in affiliate_sessions.items() 
        if session["affiliate_id"] == current_affiliate
    ]
    
    for token in sessions_to_remove:
        del affiliate_sessions[token]
    
    # Remove credentials and earnings
    del affiliate_credentials[current_affiliate]
    if current_affiliate in affiliate_earnings:
        del affiliate_earnings[current_affiliate]
    
    return {
        "message": "Account deleted successfully",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def affiliate_health():
    """Check affiliate service health."""
    return {
        "ok": True,
        "service": "affiliate_credentials",
        "total_affiliates": len(affiliate_credentials),
        "active_sessions": len(affiliate_sessions),
        "total_earnings_records": sum(len(earnings) for earnings in affiliate_earnings.values()),
        "timestamp": datetime.now().isoformat()
    }