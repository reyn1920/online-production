import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

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
# BRACKET_SURGEON: disabled
#     ]
    return all(header.lower() in [h.lower() for h in headers.keys()] for header in required_headers)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="stripe - signature"),
# BRACKET_SURGEON: disabled
# ):
    """Handle Stripe webhook events with signature verification and idempotency"""
    try:
        # Get raw payload
        payload = await request.body()

        # Verify signature
        stripe_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if stripe_secret and not verify_stripe_signature(
            payload, stripe_signature or "", stripe_secret
# BRACKET_SURGEON: disabled
#         ):
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
# BRACKET_SURGEON: disabled
#         }

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
# BRACKET_SURGEON: disabled
#         }

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
    try:
        # Extract payment information
        payment_id = payment_data.get("id", "unknown")
        amount = payment_data.get("amount", 0)
        currency = payment_data.get("currency", "USD")
        customer_id = payment_data.get("customer_id")

        # Log successful payment
        print(f"Payment successful: {provider} - {payment_id} - {amount} {currency}")

        # Update user subscription status (database integration)
        if customer_id:
            print(f"Updating subscription for customer: {customer_id}")
            try:
                # Update subscription status in database
                from backend.database.models import User, Subscription
                from backend.database.connection import get_db_session

                with get_db_session() as session:
                    user = session.query(User).filter(User.customer_id == customer_id).first()
                    if user:
                        subscription = (
                            session.query(Subscription)
                            .filter(
                                Subscription.user_id == user.id,
                                Subscription.payment_id == payment_id,
# BRACKET_SURGEON: disabled
#                             )
                            .first()
# BRACKET_SURGEON: disabled
#                         )
                        if subscription:
                            subscription.status = "active"
                            subscription.last_payment_date = datetime.utcnow()
                            session.commit()
                            print(f"Subscription updated for user {user.id}")
            except Exception as db_error:
                print(f"Database update failed: {db_error}")

        # Send confirmation email (email service integration)
        print(f"Sending confirmation email for payment: {payment_id}")
        try:
            from backend.services.email_service import EmailService

            email_service = EmailService()

            if customer_id:
                email_data = {
                    "payment_id": payment_id,
                    "amount": amount,
                    "currency": currency,
                    "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
# BRACKET_SURGEON: disabled
#                 }
                await email_service.send_payment_confirmation(customer_id, email_data)
                print(f"Confirmation email sent to customer {customer_id}")
        except Exception as email_error:
            print(f"Email service failed: {email_error}")

        # Log transaction for audit trail (persistent storage)
        transaction_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "payment_id": payment_id,
            "amount": amount,
            "currency": currency,
            "customer_id": customer_id,
            "status": "completed",
# BRACKET_SURGEON: disabled
#         }
        print(f"Transaction logged: {transaction_log}")
        try:
            from backend.database.models import TransactionLog
            from backend.database.connection import get_db_session

            with get_db_session() as session:
                log_entry = TransactionLog(
                    timestamp=datetime.utcnow(),
                    provider=provider,
                    payment_id=payment_id,
                    amount=float(amount),
                    currency=currency,
                    customer_id=customer_id,
                    status="completed",
                    raw_data=json.dumps(payment_data),
# BRACKET_SURGEON: disabled
#                 )
                session.add(log_entry)
                session.commit()
                print(f"Transaction logged to database: {payment_id}")
        except Exception as log_error:
            print(f"Transaction logging failed: {log_error}")

    except Exception as e:
        print(f"Error processing successful payment: {e}")
        return {"status": "error", "message": f"Failed to process payment: {str(e)}"}

    return {
        "action": "payment_success",
        "provider": provider,
        "payment_id": payment_data.get("id"),
        "amount": payment_data.get("amount")
        or payment_data.get("amount_with_breakdown", {}).get("gross_amount", {}).get("value"),
        "processed_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


async def handle_failed_payment(provider: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle failed payment - notify user, retry logic, etc."""
    try:
        # Extract failure information
        payment_id = payment_data.get("id", "unknown")
        failure_reason = payment_data.get("failure_reason", "Unknown error")
        customer_id = payment_data.get("customer_id")
        amount = payment_data.get("amount", 0)

        # Log failed payment
        print(f"Payment failed: {provider} - {payment_id} - Reason: {failure_reason}")

        # Notify user of failed payment
        if customer_id:
            print(f"Notifying customer {customer_id} of payment failure")
            try:
                from backend.services.email_service import EmailService

                email_service = EmailService()

                failure_data = {
                    "payment_id": payment_id,
                    "failure_reason": failure_reason,
                    "amount": amount,
                    "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
# BRACKET_SURGEON: disabled
#                 }
                await email_service.send_payment_failure_notification(customer_id, failure_data)
                print(f"Failure notification sent to customer {customer_id}")
            except Exception as email_error:
                print(f"Email notification failed: {email_error}")

        # Update subscription status if needed
        print(f"Updating subscription status for failed payment: {payment_id}")
        try:
            from backend.database.models import User, Subscription
            from backend.database.connection import get_db_session

            with get_db_session() as session:
                if customer_id:
                    user = session.query(User).filter(User.customer_id == customer_id).first()
                    if user:
                        subscription = (
                            session.query(Subscription)
                            .filter(
                                Subscription.user_id == user.id,
                                Subscription.payment_id == payment_id,
# BRACKET_SURGEON: disabled
#                             )
                            .first()
# BRACKET_SURGEON: disabled
#                         )
                        if subscription:
                            subscription.status = "payment_failed"
                            subscription.failure_reason = failure_reason
                            subscription.failed_at = datetime.utcnow()
                            session.commit()
                            print(f"Subscription marked as payment_failed for user {user.id}")
        except Exception as db_error:
            print(f"Database update failed: {db_error}")

        # Log failure for analysis (persistent storage)
        failure_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "payment_id": payment_id,
            "failure_reason": failure_reason,
            "customer_id": customer_id,
            "amount": amount,
            "status": "failed",
# BRACKET_SURGEON: disabled
#         }
        print(f"Failure logged: {failure_log}")
        try:
            from backend.database.models import PaymentFailureLog
            from backend.database.connection import get_db_session

            with get_db_session() as session:
                failure_entry = PaymentFailureLog(
                    timestamp=datetime.utcnow(),
                    provider=provider,
                    payment_id=payment_id,
                    failure_reason=failure_reason,
                    customer_id=customer_id,
                    amount=float(amount) if amount else 0.0,
                    raw_data=json.dumps(payment_data),
# BRACKET_SURGEON: disabled
#                 )
                session.add(failure_entry)
                session.commit()
                print(f"Payment failure logged to database: {payment_id}")
        except Exception as log_error:
            print(f"Failure logging failed: {log_error}")

    except Exception as e:
        print(f"Error processing failed payment: {e}")
        return {
            "status": "error",
            "message": f"Failed to process payment failure: {str(e)}",
# BRACKET_SURGEON: disabled
#         }

    return {
        "action": "payment_failed",
        "provider": provider,
        "payment_id": payment_data.get("id"),
        "processed_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


async def handle_subscription_created(
    provider: str, subscription_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle new subscription creation"""
    try:
        # Extract subscription information
        subscription_id = subscription_data.get("id", "unknown")
        customer_id = subscription_data.get("customer_id")
        plan_id = subscription_data.get("plan_id")
        status = subscription_data.get("status", "active")

        # Log subscription creation
        print(f"Subscription created: {provider} - {subscription_id} - Plan: {plan_id}")

        # Create or update user account
        if customer_id:
            print(f"Setting up account for customer: {customer_id}")
            try:
                from backend.database.models import User, Subscription
                from backend.database.connection import get_db_session

                with get_db_session() as session:
                    # Create user account if it doesn't exist
                    user = session.query(User).filter(User.customer_id == customer_id).first()
                    if not user:
                        user = User(
                            customer_id=customer_id,
                            email=subscription_data.get("customer_email", ""),
                            created_at=datetime.utcnow(),
                            status="active",
# BRACKET_SURGEON: disabled
#                         )
                        session.add(user)
                        session.flush()  # Get user.id
                        print(f"Created new user account for customer {customer_id}")

                    # Link subscription to user account
                    subscription = Subscription(
                        subscription_id=subscription_id,
                        user_id=user.id,
                        provider=provider,
                        plan_id=plan_id,
                        status=status,
                        created_at=datetime.utcnow(),
# BRACKET_SURGEON: disabled
#                     )
                    session.add(subscription)
                    session.commit()
                    print(f"Subscription linked to user {user.id}")
            except Exception as db_error:
                print(f"Database setup failed: {db_error}")

        # Set up subscription in database (already handled above)
        subscription_record = {
            "subscription_id": subscription_id,
            "provider": provider,
            "customer_id": customer_id,
            "plan_id": plan_id,
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
# BRACKET_SURGEON: disabled
#         }
        print(f"Subscription record: {subscription_record}")

        # Send welcome email
        if customer_id:
            print(f"Sending welcome email to customer: {customer_id}")
            try:
                from backend.services.email_service import EmailService

                email_service = EmailService()

                welcome_data = {
                    "subscription_id": subscription_id,
                    "plan_id": plan_id,
                    "status": status,
                    "created_date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
# BRACKET_SURGEON: disabled
#                 }
                await email_service.send_welcome_email(customer_id, welcome_data)
                print(f"Welcome email sent to customer {customer_id}")
            except Exception as email_error:
                print(f"Welcome email failed: {email_error}")

    except Exception as e:
        print(f"Error processing subscription creation: {e}")
        return {
            "status": "error",
            "message": f"Failed to process subscription creation: {str(e)}",
# BRACKET_SURGEON: disabled
#         }

    return {
        "action": "subscription_created",
        "provider": provider,
        "subscription_id": subscription_data.get("id"),
        "processed_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


async def handle_subscription_cancelled(
    provider: str, subscription_data: Dict[str, Any]
) -> Dict[str, Any]:
    """Handle subscription cancellation"""
    try:
        # Extract cancellation information
        subscription_id = subscription_data.get("id", "unknown")
        customer_id = subscription_data.get("customer_id")
        cancellation_reason = subscription_data.get("cancellation_reason", "User requested")
        effective_date = subscription_data.get("cancelled_at", datetime.utcnow().isoformat())

        # Log subscription cancellation
        print(
            f"Subscription cancelled: {provider} - {subscription_id} - Reason: {cancellation_reason}"
# BRACKET_SURGEON: disabled
#         )

        # Update subscription status
        print(f"Updating subscription status to cancelled: {subscription_id}")
        refund_amount = 0.0
        try:
            from backend.database.models import User, Subscription
            from backend.database.connection import get_db_session

            with get_db_session() as session:
                if customer_id:
                    user = session.query(User).filter(User.customer_id == customer_id).first()
                    if user:
                        subscription = (
                            session.query(Subscription)
                            .filter(
                                Subscription.user_id == user.id,
                                Subscription.subscription_id == subscription_id,
# BRACKET_SURGEON: disabled
#                             )
                            .first()
# BRACKET_SURGEON: disabled
#                         )
                        if subscription:
                            subscription.status = "cancelled"
                            subscription.cancelled_at = (
                                datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
                                if isinstance(effective_date, str)
                                else effective_date
# BRACKET_SURGEON: disabled
#                             )
                            subscription.cancellation_reason = cancellation_reason
                            session.commit()
                            print(f"Subscription {subscription_id} marked as cancelled")
        except Exception as db_error:
            print(f"Database update failed: {db_error}")

        # Calculate refunds if applicable
        print(f"Checking refund eligibility for subscription: {subscription_id}")
        try:
            from backend.services.refund_service import RefundService

            refund_service = RefundService()

            # Calculate refund based on cancellation policy
            refund_calculation = await refund_service.calculate_refund(
                subscription_id=subscription_id,
                cancellation_date=effective_date,
                cancellation_reason=cancellation_reason,
# BRACKET_SURGEON: disabled
#             )

            if refund_calculation.get("eligible", False):
                refund_amount = refund_calculation.get("amount", 0.0)
                if refund_amount > 0:
                    # Process refund
                    refund_result = await refund_service.process_refund(
                        subscription_id=subscription_id,
                        amount=refund_amount,
                        reason=cancellation_reason,
# BRACKET_SURGEON: disabled
#                     )
                    print(f"Refund processed: {refund_amount} - Result: {refund_result}")
        except Exception as refund_error:
            print(f"Refund processing failed: {refund_error}")

        # Send cancellation confirmation
        if customer_id:
            print(f"Sending cancellation confirmation to customer: {customer_id}")
            try:
                from backend.services.email_service import EmailService

                email_service = EmailService()

                cancellation_data = {
                    "subscription_id": subscription_id,
                    "cancellation_reason": cancellation_reason,
                    "effective_date": effective_date,
                    "refund_amount": refund_amount,
                    "final_billing_date": datetime.utcnow().strftime("%Y-%m-%d"),
# BRACKET_SURGEON: disabled
#                 }
                await email_service.send_cancellation_confirmation(customer_id, cancellation_data)
                print(f"Cancellation confirmation sent to customer {customer_id}")
            except Exception as email_error:
                print(f"Cancellation email failed: {email_error}")

        # Log cancellation for analytics
        cancellation_log = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": provider,
            "subscription_id": subscription_id,
            "customer_id": customer_id,
            "cancellation_reason": cancellation_reason,
            "effective_date": effective_date,
            "refund_amount": refund_amount,
# BRACKET_SURGEON: disabled
#         }
        print(f"Cancellation logged: {cancellation_log}")
        try:
            from backend.database.models import CancellationLog
            from backend.database.connection import get_db_session

            with get_db_session() as session:
                cancellation_entry = CancellationLog(
                    timestamp=datetime.utcnow(),
                    provider=provider,
                    subscription_id=subscription_id,
                    customer_id=customer_id,
                    cancellation_reason=cancellation_reason,
                    effective_date=(
                        datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
                        if isinstance(effective_date, str)
                        else effective_date
# BRACKET_SURGEON: disabled
#                     ),
                    refund_amount=refund_amount,
                    raw_data=json.dumps(subscription_data),
# BRACKET_SURGEON: disabled
#                 )
                session.add(cancellation_entry)
                session.commit()
                print(f"Cancellation logged to analytics database: {subscription_id}")
        except Exception as log_error:
            print(f"Cancellation logging failed: {log_error}")

    except Exception as e:
        print(f"Error processing subscription cancellation: {e}")
        return {
            "status": "error",
            "message": f"Failed to process subscription cancellation: {str(e)}",
# BRACKET_SURGEON: disabled
#         }

    return {
        "action": "subscription_cancelled",
        "provider": provider,
        "subscription_id": subscription_data.get("id"),
        "processed_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook service"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "processed_webhooks_count": len(load_processed_webhooks()),
# BRACKET_SURGEON: disabled
#     }