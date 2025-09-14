import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request
from pydantic import BaseModel

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Simple file - based storage for processed webhook IDs (idempotency)
PROCESSED_WEBHOOKS_FILE = "processed_webhooks.json"


def load_processed_webhooks() -> Dict[str, float]:
    """Load processed webhook IDs with timestamps"""
    if os.path.exists(PROCESSED_WEBHOOKS_FILE):
        with open(PROCESSED_WEBHOOKS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_processed_webhooks(processed: Dict[str, float]):
    """Save processed webhook IDs with cleanup of old entries"""
    # Clean up entries older than 24 hours
    cutoff = time.time() - (24 * 60 * 60)
    cleaned = {k: v for k, v in processed.items() if v > cutoff}

    with open(PROCESSED_WEBHOOKS_FILE, "w") as f:
        json.dump(cleaned, f, indent=2)


def is_webhook_processed(webhook_id: str) -> bool:
    """Check if webhook has already been processed"""
    processed = load_processed_webhooks()
    return webhook_id in processed


def mark_webhook_processed(webhook_id: str):
    """Mark webhook as processed"""
    processed = load_processed_webhooks()
    processed[webhook_id] = time.time()
    save_processed_webhooks(processed)


def verify_stripe_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Stripe webhook signature"""
    if not signature or not secret:
        return False

    try:
        # Extract timestamp and signature from header
        elements = signature.split(",")
        timestamp = None
        v1_signature = None

        for element in elements:
            key, value = element.split("=")
            if key == "t":
                timestamp = value
            elif key == "v1":
                v1_signature = value

        if not timestamp or not v1_signature:
            return False

        # Check timestamp (reject if older than 5 minutes)
        if abs(time.time() - int(timestamp)) > 300:
            return False

        # Verify signature
        signed_payload = f"{timestamp}.{payload.decode('utf - 8')}"
        expected_signature = hmac.new(
            secret.encode("utf - 8"), signed_payload.encode("utf - 8"), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(v1_signature, expected_signature)

    except Exception:
        return False


def verify_paypal_signature(payload: bytes, headers: Dict[str, str]) -> bool:
    """Verify PayPal webhook signature (simplified)"""
    # In production, implement full PayPal webhook verification
    # This is a placeholder that checks for required headers
    required_headers = [
        "paypal - transmission - id",
        "paypal - cert - id",
        "paypal - transmission - sig",
    ]
    return all(header.lower() in [h.lower() for h in headers.keys()] for header in required_headers)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe - signature"),
):
    """Handle Stripe webhook events with signature verification and idempotency"""
    try:
        # Get raw payload
        payload = await request.body()

        # Verify signature
        stripe_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if stripe_secret and not verify_stripe_signature(
            payload, stripe_signature or "", stripe_secret
        ):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse event
        event = json.loads(payload.decode("utf - 8"))
        event_id = event.get("id")
        event_type = event.get("type")

        if not event_id:
            raise HTTPException(status_code=400, detail="Missing event ID")

        # Check idempotency
        if is_webhook_processed(f"stripe_{event_id}"):
            return {"status": "already_processed", "event_id": event_id}

        # Process event based on type
        result = await process_stripe_event(event_type, event.get("data", {}))

        # Mark as processed
        mark_webhook_processed(f"stripe_{event_id}")

        return {
            "status": "success",
            "event_id": event_id,
            "event_type": event_type,
            "result": result,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


@router.post("/paypal")
async def paypal_webhook(request: Request):
    """Handle PayPal webhook events with signature verification and idempotency"""
    try:
        # Get raw payload and headers
        payload = await request.body()
        headers = dict(request.headers)

        # Verify signature (simplified)
        if not verify_paypal_signature(payload, headers):
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Parse event
        event = json.loads(payload.decode("utf - 8"))
        event_id = event.get("id")
        event_type = event.get("event_type")

        if not event_id:
            raise HTTPException(status_code=400, detail="Missing event ID")

        # Check idempotency
        if is_webhook_processed(f"paypal_{event_id}"):
            return {"status": "already_processed", "event_id": event_id}

        # Process event based on type
        result = await process_paypal_event(event_type, event.get("resource", {}))

        # Mark as processed
        mark_webhook_processed(f"paypal_{event_id}")

        return {
            "status": "success",
            "event_id": event_id,
            "event_type": event_type,
            "result": result,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")


async def process_stripe_event(event_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Stripe webhook events"""
    if event_type == "payment_intent.succeeded":
        payment_intent = data.get("object", {})
        return await handle_successful_payment("stripe", payment_intent)

    elif event_type == "payment_intent.payment_failed":
        payment_intent = data.get("object", {})
        return await handle_failed_payment("stripe", payment_intent)

    elif event_type == "customer.subscription.created":
        subscription = data.get("object", {})
        return await handle_subscription_created("stripe", subscription)

    elif event_type == "customer.subscription.deleted":
        subscription = data.get("object", {})
        return await handle_subscription_cancelled("stripe", subscription)

    else:
        return {"message": f"Unhandled event type: {event_type}"}


async def process_paypal_event(event_type: str, resource: Dict[str, Any]) -> Dict[str, Any]:
    """Process PayPal webhook events"""
    if event_type == "PAYMENT.CAPTURE.COMPLETED":
        return await handle_successful_payment("paypal", resource)

    elif event_type == "PAYMENT.CAPTURE.DENIED":
        return await handle_failed_payment("paypal", resource)

    elif event_type == "BILLING.SUBSCRIPTION.CREATED":
        return await handle_subscription_created("paypal", resource)

    elif event_type == "BILLING.SUBSCRIPTION.CANCELLED":
        return await handle_subscription_cancelled("paypal", resource)

    else:
        return {"message": f"Unhandled event type: {event_type}"}


# Business logic handlers (stubs)


async def handle_successful_payment(provider: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle successful payment - update user account, send confirmation, etc."""
    # TODO: Implement actual business logic
    # - Update user subscription status
    # - Send confirmation email
    # - Log transaction
    return {
        "action": "payment_success",
        "provider": provider,
        "payment_id": payment_data.get("id"),
        "amount": payment_data.get("amount")
        or payment_data.get("amount_with_breakdown", {}).get("gross_amount", {}).get("value"),
        "processed_at": datetime.now().isoformat(),
    }


async def handle_failed_payment(provider: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle failed payment - notify user, retry logic, etc."""
    # TODO: Implement actual business logic
    # - Notify user of failed payment
    # - Implement retry logic
    # - Update subscription status if needed
    return {
        "action": "payment_failed",
        "provider": provider,
        "payment_id": payment_data.get("id"),
        "processed_at": datetime.now().isoformat(),
    }


async def handle_subscription_created(
    provider: str, subscription_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle new subscription creation"""
    # TODO: Implement actual business logic
    # - Activate user account
    # - Send welcome email
    # - Set up user permissions
    return {
        "action": "subscription_created",
        "provider": provider,
        "subscription_id": subscription_data.get("id"),
        "processed_at": datetime.now().isoformat(),
    }


async def handle_subscription_cancelled(
    provider: str, subscription_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle subscription cancellation"""
    # TODO: Implement actual business logic
    # - Update user access
    # - Send cancellation confirmation
    # - Schedule data retention cleanup
    return {
        "action": "subscription_cancelled",
        "provider": provider,
        "subscription_id": subscription_data.get("id"),
        "processed_at": datetime.now().isoformat(),
    }


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "processed_webhooks_count": len(load_processed_webhooks()),
    }
