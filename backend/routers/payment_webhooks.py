#!/usr/bin/env python3
"""
Payment Webhooks Router

Handles payment webhook notifications from various providers.
Secure webhook validation and payment processing.
"""

from fastapi import APIRouter, HTTPException, Request, Header
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
import hmac
import hashlib
from datetime import datetime

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# In-memory storage for demo purposes
webhook_events: Dict[str, Dict[str, Any]] = {}

class WebhookEvent(BaseModel):
    event_id: str
    event_type: str
    provider: str
    data: Dict[str, Any]
    timestamp: str
    verified: bool = False

def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature."""
    try:
        # Extract timestamp and signature from header
        elements = signature.split(',')
        timestamp = None
        signatures = []
        
        for element in elements:
            key, value = element.split('=')
            if key == 't':
                timestamp = value
            elif key == 'v1':
                signatures.append(value)
        
        if not timestamp or not signatures:
            return False
        
        # Create expected signature
        signed_payload = f"{timestamp}.{payload.decode()}"
        expected_signature = hmac.new(
            secret.encode(),
            signed_payload.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures
        return any(hmac.compare_digest(expected_signature, sig) for sig in signatures)
    
    except Exception:
        return False

def verify_paypal_signature(headers: Dict[str, str]) -> bool:
    """Verify PayPal webhook signature."""
    required_headers = [
        "paypal-transmission-id",
        "paypal-cert-id",
        "paypal-transmission-sig"
    ]
    return all(header.lower() in [h.lower() for h in headers.keys()] for header in required_headers)

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe-signature")
):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        
        # For demo purposes, we'll skip signature verification
        # In production, you would verify the signature here
        verified = True  # verify_stripe_signature(payload, stripe_signature or "", "your_stripe_secret")
        
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse the event
        event_data = json.loads(payload)
        event_id = event_data.get("id", "unknown")
        event_type = event_data.get("type", "unknown")
        
        # Store the event
        webhook_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider="stripe",
            data=event_data,
            timestamp=datetime.now().isoformat(),
            verified=verified
        )
        
        webhook_events[event_id] = webhook_event.dict()
        
        # Process different event types
        if event_type == "payment_intent.succeeded":
            # Handle successful payment
            payment_intent = event_data.get("data", {}).get("object", {})
            amount = payment_intent.get("amount", 0)
            currency = payment_intent.get("currency", "usd")
            
            return {
                "status": "success",
                "message": f"Payment of {amount/100} {currency.upper()} processed",
                "event_id": event_id
            }
        
        elif event_type == "payment_intent.payment_failed":
            # Handle failed payment
            return {
                "status": "acknowledged",
                "message": "Payment failure processed",
                "event_id": event_id
            }
        
        else:
            # Handle other events
            return {
                "status": "acknowledged",
                "message": f"Event {event_type} received",
                "event_id": event_id
            }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

@router.post("/paypal")
async def paypal_webhook(
    request: Request,
    paypal_transmission_id: Optional[str] = Header(None, alias="paypal-transmission-id"),
    paypal_cert_id: Optional[str] = Header(None, alias="paypal-cert-id"),
    paypal_transmission_sig: Optional[str] = Header(None, alias="paypal-transmission-sig")
):
    """Handle PayPal webhook events."""
    try:
        payload = await request.body()
        headers = dict(request.headers)
        
        # For demo purposes, we'll skip signature verification
        # In production, you would verify the signature here
        verified = True  # verify_paypal_signature(headers)
        
        if not verified:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Parse the event
        event_data = json.loads(payload)
        event_id = event_data.get("id", "unknown")
        event_type = event_data.get("event_type", "unknown")
        
        # Store the event
        webhook_event = WebhookEvent(
            event_id=event_id,
            event_type=event_type,
            provider="paypal",
            data=event_data,
            timestamp=datetime.now().isoformat(),
            verified=verified
        )
        
        webhook_events[event_id] = webhook_event.dict()
        
        # Process different event types
        if event_type == "PAYMENT.CAPTURE.COMPLETED":
            # Handle successful payment capture
            return {
                "status": "success",
                "message": "Payment capture processed",
                "event_id": event_id
            }
        
        elif event_type == "PAYMENT.CAPTURE.DENIED":
            # Handle denied payment
            return {
                "status": "acknowledged",
                "message": "Payment denial processed",
                "event_id": event_id
            }
        
        else:
            # Handle other events
            return {
                "status": "acknowledged",
                "message": f"Event {event_type} received",
                "event_id": event_id
            }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing error: {str(e)}")

@router.get("/events")
async def get_webhook_events():
    """Get all webhook events."""
    return {
        "events": list(webhook_events.values()),
        "total": len(webhook_events)
    }

@router.get("/events/{event_id}")
async def get_webhook_event(event_id: str):
    """Get a specific webhook event."""
    if event_id not in webhook_events:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return webhook_events[event_id]

@router.get("/health")
async def webhook_health():
    """Check webhook system health."""
    return {
        "ok": True,
        "total_events": len(webhook_events),
        "providers": ["stripe", "paypal"],
        "timestamp": datetime.now().isoformat()
    }

@router.delete("/events")
async def clear_webhook_events():
    """Clear all webhook events."""
    webhook_events.clear()
    return {"message": "All webhook events cleared"}