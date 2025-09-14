#!/usr/bin/env python3
"""
Monetization Bundle Service
Comprehensive revenue generation and tracking system
"""

import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import redis
import stripe
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from celery import Celery
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel
from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/monetization_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)

# Celery setup
celery_app = Celery(
    "monetization",
    broker=os.getenv("CELERY_BROKER", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_BACKEND", "redis://localhost:6379/0"),
)

# Metrics
revenue_counter = Counter("revenue_total", "Total revenue generated", ["source", "type"])
order_counter = Counter("orders_total", "Total orders processed", ["status", "product_type"])
conversion_rate = Gauge("conversion_rate", "Conversion rate percentage", ["funnel_stage"])
revenue_gauge = Gauge("revenue_current", "Current revenue", ["period", "source"])
processing_time = Histogram(
    "processing_time_seconds", "Time spent processing requests", ["endpoint"]
)

# Database Models


class RevenueStream(Base):
    __tablename__ = "revenue_streams"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # affiliate, product, service, subscription
    platform = Column(String, nullable=False)
    status = Column(String, default="active")
    commission_rate = Column(Float, default=0.0)
    monthly_target = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    revenue_stream_id = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(String, nullable=False)  # pending, completed, failed, refunded
    transaction_type = Column(String, nullable=False)  # sale, commission, refund
    customer_id = Column(String)
    product_id = Column(String)
    platform_transaction_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    metadata = Column(JSON, default={})


class Product(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    product_type = Column(String, nullable=False)  # digital,
    physical,
    service,
    course
    platform = Column(String, nullable=False)
    platform_product_id = Column(String)
    status = Column(String, default="active")
    inventory_count = Column(Integer, default=-1)  # -1 for unlimited
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    original_url = Column(String, nullable=False)
    affiliate_url = Column(String, nullable=False)
    commission_rate = Column(Float, default=0.0)
    clicks = Column(Integer, default=0)
    conversions = Column(Integer, default=0)
    revenue = Column(Float, default=0.0)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=False)
    product_id = Column(String, nullable=False)
    platform = Column(String, nullable=False)
    platform_subscription_id = Column(String)
    status = Column(String, nullable=False)  # active, cancelled, paused, expired
    billing_cycle = Column(String, nullable=False)  # monthly, yearly, weekly
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    next_billing_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})


# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models


class RevenueStreamCreate(BaseModel):
    name: str
    type: str
    platform: str
    commission_rate: float = 0.0
    monthly_target: float = 0.0
    metadata: Dict[str, Any] = {}


class TransactionCreate(BaseModel):
    revenue_stream_id: str
    amount: float
    currency: str = "USD"
    transaction_type: str
    customer_id: Optional[str] = None
    product_id: Optional[str] = None
    platform_transaction_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    currency: str = "USD"
    product_type: str
    platform: str
    platform_product_id: Optional[str] = None
    inventory_count: int = -1
    metadata: Dict[str, Any] = {}


class AffiliateLinkCreate(BaseModel):
    name: str
    platform: str
    original_url: str
    affiliate_url: str
    commission_rate: float = 0.0
    metadata: Dict[str, Any] = {}


class SubscriptionCreate(BaseModel):
    customer_id: str
    product_id: str
    platform: str
    platform_subscription_id: Optional[str] = None
    billing_cycle: str
    amount: float
    currency: str = "USD"
    next_billing_date: Optional[datetime] = None
    metadata: Dict[str, Any] = {}


class PaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"
    payment_method: str
    customer_email: str
    product_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class RevenueReport(BaseModel):
    period: str
    total_revenue: float
    revenue_by_source: Dict[str, float]
    revenue_by_type: Dict[str, float]
    transaction_count: int
    conversion_rate: float
    top_products: List[Dict[str, Any]]
    growth_rate: float


# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Payment Processors


class PaymentProcessor:
    def __init__(self):
        self.stripe_key = os.getenv("STRIPE_SECRET_KEY")
        if self.stripe_key:
            stripe.api_key = self.stripe_key

    async def process_stripe_payment(self, payment_data: PaymentRequest) -> Dict[str, Any]:
        """Process payment through Stripe"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(payment_data.amount * 100),  # Convert to cents
                currency=payment_data.currency.lower(),
                metadata=payment_data.metadata,
            )
            return {
                "status": "success",
                "payment_intent_id": intent.id,
                "client_secret": intent.client_secret,
            }
        except Exception as e:
            logger.error(f"Stripe payment failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process_paypal_payment(self, payment_data: PaymentRequest) -> Dict[str, Any]:
        """Process payment through PayPal"""
        # PayPal integration would go here
        return {"status": "success", "transaction_id": f"pp_{uuid.uuid4()}"}


# Analytics Engine


class AnalyticsEngine:
    def __init__(self, db: Session):
        self.db = db

    async def calculate_revenue_metrics(self, period: str = "month") -> Dict[str, Any]:
        """Calculate comprehensive revenue metrics"""
        end_date = datetime.utcnow()
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(weeks=1)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        elif period == "year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        transactions = (
            self.db.query(Transaction)
            .filter(Transaction.created_at >= start_date, Transaction.status == "completed")
            .all()
        )

        total_revenue = sum(t.amount for t in transactions)
        revenue_by_source = {}
        revenue_by_type = {}

        for transaction in transactions:
            # Get revenue stream info
            stream = (
                self.db.query(RevenueStream)
                .filter(RevenueStream.id == transaction.revenue_stream_id)
                .first()
            )

            if stream:
                revenue_by_source[stream.platform] = (
                    revenue_by_source.get(stream.platform, 0) + transaction.amount
                )
                revenue_by_type[stream.type] = (
                    revenue_by_type.get(stream.type, 0) + transaction.amount
                )

        return {
            "period": period,
            "total_revenue": total_revenue,
            "revenue_by_source": revenue_by_source,
            "revenue_by_type": revenue_by_type,
            "transaction_count": len(transactions),
            "average_transaction": (total_revenue / len(transactions) if transactions else 0),
        }

    async def get_top_performing_products(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing products by revenue"""
        # This would involve complex queries to aggregate product performance
        return []

    async def calculate_conversion_rates(self) -> Dict[str, float]:
        """Calculate conversion rates for different funnels"""
        # Implementation for conversion rate calculation
        return {"overall": 0.05, "email": 0.03, "social": 0.02}


# Affiliate Marketing Manager


class AffiliateManager:
    def __init__(self, db: Session):
        self.db = db

    async def track_click(self, affiliate_link_id: str, user_data: Dict[str, Any]) -> bool:
        """Track affiliate link click"""
        link = self.db.query(AffiliateLink).filter(AffiliateLink.id == affiliate_link_id).first()
        if link:
            link.clicks += 1
            link.updated_at = datetime.utcnow()
            self.db.commit()

            # Store click data in Redis for conversion tracking
            click_data = {
                "affiliate_link_id": affiliate_link_id,
                "timestamp": datetime.utcnow().isoformat(),
                "user_data": user_data,
            }
            redis_client.setex(
                f"click:{user_data.get('session_id', uuid.uuid4())}",
                3600,
                json.dumps(click_data),
            )
            return True
        return False

    async def track_conversion(self, session_id: str, transaction_id: str, amount: float) -> bool:
        """Track affiliate conversion"""
        click_data = redis_client.get(f"click:{session_id}")
        if click_data:
            click_info = json.loads(click_data)
            affiliate_link_id = click_info["affiliate_link_id"]

            link = (
                self.db.query(AffiliateLink).filter(AffiliateLink.id == affiliate_link_id).first()
            )
            if link:
                link.conversions += 1
                link.revenue += amount
                link.updated_at = datetime.utcnow()
                self.db.commit()

                # Create commission transaction
                commission_amount = amount * (link.commission_rate / 100)
                commission_transaction = Transaction(
                    revenue_stream_id=affiliate_link_id,
                    amount=commission_amount,
                    status="completed",
                    transaction_type="commission",
                    platform_transaction_id=transaction_id,
                    metadata={
                        "original_amount": amount,
                        "commission_rate": link.commission_rate,
                    },
                )
                self.db.add(commission_transaction)
                self.db.commit()

                return True
        return False


# Subscription Manager


class SubscriptionManager:
    def __init__(self, db: Session):
        self.db = db

    async def create_subscription(self, subscription_data: SubscriptionCreate) -> Subscription:
        """Create new subscription"""
        subscription = Subscription(**subscription_data.dict())
        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)
        return subscription

    async def process_recurring_billing(self) -> List[Dict[str, Any]]:
        """Process recurring billing for active subscriptions"""
        today = datetime.utcnow().date()
        due_subscriptions = (
            self.db.query(Subscription)
            .filter(Subscription.status == "active", Subscription.next_billing_date <= today)
            .all()
        )

        results = []
        for subscription in due_subscriptions:
            # Process billing
            result = await self._process_subscription_billing(subscription)
            results.append(result)

        return results

    async def _process_subscription_billing(self, subscription: Subscription) -> Dict[str, Any]:
        """Process billing for a single subscription"""
        try:
            # Create transaction record
            transaction = Transaction(
                revenue_stream_id=subscription.product_id,
                amount=subscription.amount,
                currency=subscription.currency,
                status="completed",
                transaction_type="subscription",
                customer_id=subscription.customer_id,
                product_id=subscription.product_id,
                platform_transaction_id=f"sub_{subscription.id}_{datetime.utcnow().strftime('%Y % m%d')}",
            )
            self.db.add(transaction)

            # Update next billing date
            if subscription.billing_cycle == "monthly":
                subscription.next_billing_date = subscription.next_billing_date + timedelta(days=30)
            elif subscription.billing_cycle == "yearly":
                subscription.next_billing_date = subscription.next_billing_date + timedelta(
                    days=365
                )
            elif subscription.billing_cycle == "weekly":
                subscription.next_billing_date = subscription.next_billing_date + timedelta(days=7)

            subscription.updated_at = datetime.utcnow()
            self.db.commit()

            return {
                "status": "success",
                "subscription_id": subscription.id,
                "amount": subscription.amount,
            }
        except Exception as e:
            logger.error(f"Subscription billing failed for {subscription.id}: {e}")
            return {
                "status": "error",
                "subscription_id": subscription.id,
                "error": str(e),
            }


# Initialize services
payment_processor = PaymentProcessor()

# Scheduler setup
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()

    # Add scheduled tasks
    scheduler.add_job(
        update_revenue_metrics,
        CronTrigger(minute=0),  # Every hour
        id="update_revenue_metrics",
    )

    scheduler.add_job(
        process_recurring_subscriptions,
        CronTrigger(hour=0, minute=0),  # Daily at midnight
        id="process_recurring_subscriptions",
    )

    yield

    # Shutdown
    scheduler.shutdown()


# FastAPI app
app = FastAPI(
    title="Monetization Bundle Service",
    description="Comprehensive revenue generation and tracking system",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def get_metrics():
    return generate_latest().decode()


# Revenue Stream Management
@app.post("/api/revenue - streams")
async def create_revenue_stream(stream_data: RevenueStreamCreate, db: Session = Depends(get_db)):
    stream = RevenueStream(**stream_data.dict())
    db.add(stream)
    db.commit()
    db.refresh(stream)
    return stream


@app.get("/api/revenue - streams")
async def get_revenue_streams(db: Session = Depends(get_db)):
    streams = db.query(RevenueStream).all()
    return streams


@app.get("/api/revenue - streams/{stream_id}")
async def get_revenue_stream(stream_id: str, db: Session = Depends(get_db)):
    stream = db.query(RevenueStream).filter(RevenueStream.id == stream_id).first()
    if not stream:
        raise HTTPException(status_code=404, detail="Revenue stream not found")
    return stream


# Transaction Management
@app.post("/api/transactions")
async def create_transaction(transaction_data: TransactionCreate, db: Session = Depends(get_db)):
    transaction = Transaction(**transaction_data.dict())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # Update metrics
    revenue_counter.labels(
        source=transaction.revenue_stream_id, type=transaction.transaction_type
    ).inc()

    return transaction


@app.get("/api/transactions")
async def get_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transactions = db.query(Transaction).offset(skip).limit(limit).all()
    return transactions


# Payment Processing
@app.post("/api/payments/stripe")
async def process_stripe_payment(payment_data: PaymentRequest, db: Session = Depends(get_db)):
    result = await payment_processor.process_stripe_payment(payment_data)

    if result["status"] == "success":
        # Create transaction record
        transaction = Transaction(
            revenue_stream_id="stripe_payments",
            amount=payment_data.amount,
            currency=payment_data.currency,
            status="pending",
            transaction_type="sale",
            platform_transaction_id=result["payment_intent_id"],
            metadata=payment_data.metadata,
        )
        db.add(transaction)
        db.commit()

    return result


@app.post("/api/payments/paypal")
async def process_paypal_payment(payment_data: PaymentRequest, db: Session = Depends(get_db)):
    result = await payment_processor.process_paypal_payment(payment_data)

    if result["status"] == "success":
        transaction = Transaction(
            revenue_stream_id="paypal_payments",
            amount=payment_data.amount,
            currency=payment_data.currency,
            status="completed",
            transaction_type="sale",
            platform_transaction_id=result["transaction_id"],
            metadata=payment_data.metadata,
        )
        db.add(transaction)
        db.commit()

    return result


# Product Management
@app.post("/api/products")
async def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@app.get("/api/products")
async def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@app.get("/api/products/{product_id}")
async def get_product(product_id: str, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# Affiliate Marketing
@app.post("/api/affiliate - links")
async def create_affiliate_link(link_data: AffiliateLinkCreate, db: Session = Depends(get_db)):
    link = AffiliateLink(**link_data.dict())
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@app.get("/api/affiliate - links")
async def get_affiliate_links(db: Session = Depends(get_db)):
    links = db.query(AffiliateLink).all()
    return links


@app.post("/api/affiliate - links/{link_id}/click")
async def track_affiliate_click(link_id: str, request: Request, db: Session = Depends(get_db)):
    affiliate_manager = AffiliateManager(db)
    user_data = {
        "ip_address": request.client.host,
        "user_agent": request.headers.get("user - agent"),
        "session_id": request.headers.get("x - session - id", str(uuid.uuid4())),
    }

    success = await affiliate_manager.track_click(link_id, user_data)
    if success:
        return {"status": "success", "message": "Click tracked"}
    else:
        raise HTTPException(status_code=404, detail="Affiliate link not found")


@app.post("/api/affiliate - links/conversion")
async def track_affiliate_conversion(
    session_id: str, transaction_id: str, amount: float, db: Session = Depends(get_db)
):
    affiliate_manager = AffiliateManager(db)
    success = await affiliate_manager.track_conversion(session_id, transaction_id, amount)

    if success:
        return {"status": "success", "message": "Conversion tracked"}
    else:
        return {"status": "error", "message": "No matching click found"}


# Subscription Management
@app.post("/api/subscriptions")
async def create_subscription(subscription_data: SubscriptionCreate, db: Session = Depends(get_db)):
    subscription_manager = SubscriptionManager(db)
    subscription = await subscription_manager.create_subscription(subscription_data)
    return subscription


@app.get("/api/subscriptions")
async def get_subscriptions(db: Session = Depends(get_db)):
    subscriptions = db.query(Subscription).all()
    return subscriptions


@app.get("/api/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@app.put("/api/subscriptions/{subscription_id}/cancel")
async def cancel_subscription(subscription_id: str, db: Session = Depends(get_db)):
    subscription = db.query(Subscription).filter(Subscription.id == subscription_id).first()
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    subscription.status = "cancelled"
    subscription.updated_at = datetime.utcnow()
    db.commit()

    return {"status": "success", "message": "Subscription cancelled"}


# Analytics and Reporting
@app.get("/api/analytics/revenue")
async def get_revenue_analytics(period: str = "month", db: Session = Depends(get_db)):
    analytics_engine = AnalyticsEngine(db)
    metrics = await analytics_engine.calculate_revenue_metrics(period)
    return metrics


@app.get("/api/analytics/products/top")
async def get_top_products(limit: int = 10, db: Session = Depends(get_db)):
    analytics_engine = AnalyticsEngine(db)
    top_products = await analytics_engine.get_top_performing_products(limit)
    return top_products


@app.get("/api/analytics/conversion - rates")
async def get_conversion_rates(db: Session = Depends(get_db)):
    analytics_engine = AnalyticsEngine(db)
    rates = await analytics_engine.calculate_conversion_rates()
    return rates


@app.get("/api/reports/revenue")
async def generate_revenue_report(period: str = "month", db: Session = Depends(get_db)):
    analytics_engine = AnalyticsEngine(db)

    # Get basic metrics
    metrics = await analytics_engine.calculate_revenue_metrics(period)

    # Get additional data
    top_products = await analytics_engine.get_top_performing_products(5)
    conversion_rates = await analytics_engine.calculate_conversion_rates()

    # Calculate growth rate (simplified)
    growth_rate = 0.15  # This would be calculated based on historical data

    report = RevenueReport(
        period=period,
        total_revenue=metrics["total_revenue"],
        revenue_by_source=metrics["revenue_by_source"],
        revenue_by_type=metrics["revenue_by_type"],
        transaction_count=metrics["transaction_count"],
        conversion_rate=conversion_rates.get("overall", 0.0),
        top_products=top_products,
        growth_rate=growth_rate,
    )

    return report


# Webhook Handlers
@app.post("/api/webhooks/stripe")
async def handle_stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe - signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv("STRIPE_WEBHOOK_SECRET")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle the event
    if event["type"] == "payment_intent.succeeded":
        payment_intent = event["data"]["object"]

        # Update transaction status
        transaction = (
            db.query(Transaction)
            .filter(Transaction.platform_transaction_id == payment_intent["id"])
            .first()
        )

        if transaction:
            transaction.status = "completed"
            transaction.processed_at = datetime.utcnow()
            db.commit()

    return {"status": "success"}


@app.post("/api/webhooks/paypal")
async def handle_paypal_webhook(request: Request, db: Session = Depends(get_db)):
    # PayPal webhook handling would go here
    return {"status": "success"}


# Background Tasks


async def update_revenue_metrics():
    """Update revenue metrics periodically"""
    try:
        db = SessionLocal()
        analytics_engine = AnalyticsEngine(db)

        # Update daily metrics
        daily_metrics = await analytics_engine.calculate_revenue_metrics("day")
        revenue_gauge.labels(period="day", source="total").set(daily_metrics["total_revenue"])

        # Update monthly metrics
        monthly_metrics = await analytics_engine.calculate_revenue_metrics("month")
        revenue_gauge.labels(period="month", source="total").set(monthly_metrics["total_revenue"])

        # Update conversion rates
        conversion_rates = await analytics_engine.calculate_conversion_rates()
        for funnel, rate in conversion_rates.items():
            conversion_rate.labels(funnel_stage=funnel).set(rate)

        db.close()
        logger.info("Revenue metrics updated successfully")
    except Exception as e:
        logger.error(f"Failed to update revenue metrics: {e}")


async def process_recurring_subscriptions():
    """Process recurring subscription billing"""
    try:
        db = SessionLocal()
        subscription_manager = SubscriptionManager(db)

        results = await subscription_manager.process_recurring_billing()

        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])

        logger.info(
            f"Processed {len(results)} subscriptions: {successful} successful, {failed} failed"
        )

        db.close()
    except Exception as e:
        logger.error(f"Failed to process recurring subscriptions: {e}")


# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=False, workers=1)
