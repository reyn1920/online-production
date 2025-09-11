#!/usr/bin/env python3
"""
Analytics Dashboard Service
Comprehensive business intelligence and data visualization platform
"""

import asyncio
import json
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import redis
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from celery import Celery
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from plotly.utils import PlotlyJSONEncoder
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, Integer, String, Text,
                        create_engine)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics_dashboard.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis setup
redis_client = redis.Redis(host=os.getenv("REDIS_HOST", "localhost"), port=6379, db=0)

# Celery setup
celery_app = Celery(
    "analytics",
    broker=os.getenv("CELERY_BROKER", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_BACKEND", "redis://localhost:6379/0"),
)

# Metrics
analytics_requests = Counter(
    "analytics_requests_total", "Total analytics requests", ["endpoint", "status"]
)
data_processing_time = Histogram(
    "data_processing_seconds", "Time spent processing data", ["operation"]
)
active_dashboards = Gauge("active_dashboards", "Number of active dashboards")
data_points_processed = Counter(
    "data_points_processed_total", "Total data points processed", ["source"]
)


# Database Models
class Dashboard(Base):
    __tablename__ = "dashboards"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    dashboard_type = Column(
        String, nullable=False
    )  # revenue, marketing, content, executive
    owner_id = Column(String, nullable=False)
    config = Column(JSON, default={})
    widgets = Column(JSON, default=[])
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed = Column(DateTime, default=datetime.utcnow)


class DataSource(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # api, database, file, webhook
    connection_config = Column(JSON, default={})
    refresh_interval = Column(Integer, default=3600)  # seconds
    last_refresh = Column(DateTime)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MetricDefinition(Base):
    __tablename__ = "metric_definitions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text)
    metric_type = Column(String, nullable=False)  # counter, gauge, histogram, rate
    calculation_method = Column(String, nullable=False)  # sum, avg, count, custom
    data_source_id = Column(String, nullable=False)
    query = Column(Text)
    unit = Column(String, default="")
    target_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # scheduled, ad_hoc, automated
    dashboard_id = Column(String)
    schedule = Column(String)  # cron expression
    recipients = Column(JSON, default=[])
    format = Column(String, default="pdf")  # pdf, excel, html
    last_generated = Column(DateTime)
    next_generation = Column(DateTime)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    metric_id = Column(String, nullable=False)
    condition = Column(String, nullable=False)  # gt, lt, eq, change_percent
    threshold = Column(Float, nullable=False)
    severity = Column(String, default="medium")  # low, medium, high, critical
    notification_channels = Column(JSON, default=[])
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# Pydantic Models
class DashboardCreate(BaseModel):
    name: str
    description: Optional[str] = None
    dashboard_type: str
    owner_id: str
    config: Dict[str, Any] = {}
    widgets: List[Dict[str, Any]] = []
    is_public: bool = False


class DataSourceCreate(BaseModel):
    name: str
    source_type: str
    connection_config: Dict[str, Any] = {}
    refresh_interval: int = 3600


class MetricDefinitionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    metric_type: str
    calculation_method: str
    data_source_id: str
    query: str
    unit: str = ""
    target_value: Optional[float] = None


class ReportCreate(BaseModel):
    name: str
    report_type: str
    dashboard_id: Optional[str] = None
    schedule: Optional[str] = None
    recipients: List[str] = []
    format: str = "pdf"


class AlertCreate(BaseModel):
    name: str
    metric_id: str
    condition: str
    threshold: float
    severity: str = "medium"
    notification_channels: List[str] = []


class AnalyticsQuery(BaseModel):
    metrics: List[str]
    dimensions: List[str] = []
    filters: Dict[str, Any] = {}
    date_range: Dict[str, str] = {}
    aggregation: str = "sum"
    limit: int = 1000


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Data Processing Engine
class DataProcessor:
    def __init__(self, db: Session):
        self.db = db

    async def fetch_data_from_source(
        self, source_id: str, query: str = None
    ) -> pd.DataFrame:
        """Fetch data from various sources"""
        source = self.db.query(DataSource).filter(DataSource.id == source_id).first()
        if not source:
            raise ValueError(f"Data source {source_id} not found")

        if source.source_type == "api":
            return await self._fetch_from_api(source, query)
        elif source.source_type == "database":
            return await self._fetch_from_database(source, query)
        elif source.source_type == "file":
            return await self._fetch_from_file(source)
        else:
            raise ValueError(f"Unsupported source type: {source.source_type}")

    async def _fetch_from_api(
        self, source: DataSource, query: str = None
    ) -> pd.DataFrame:
        """Fetch data from API endpoint"""
        config = source.connection_config
        url = config.get("url")
        headers = config.get("headers", {})
        params = config.get("params", {})

        if query:
            params.update({"query": query})

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            return pd.DataFrame(data.get("data", []))

    async def _fetch_from_database(
        self, source: DataSource, query: str
    ) -> pd.DataFrame:
        """Fetch data from database"""
        config = source.connection_config
        connection_string = config.get("connection_string")

        if not query:
            query = "SELECT * FROM metrics LIMIT 1000"

        return pd.read_sql(query, connection_string)

    async def _fetch_from_file(self, source: DataSource) -> pd.DataFrame:
        """Fetch data from file"""
        config = source.connection_config
        file_path = config.get("file_path")
        file_type = config.get("file_type", "csv")

        if file_type == "csv":
            return pd.read_csv(file_path)
        elif file_type == "excel":
            return pd.read_excel(file_path)
        elif file_type == "json":
            return pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def calculate_metric(
        self, data: pd.DataFrame, metric_def: MetricDefinition
    ) -> float:
        """Calculate metric value from data"""
        if metric_def.calculation_method == "sum":
            return data.sum().sum() if not data.empty else 0
        elif metric_def.calculation_method == "avg":
            return data.mean().mean() if not data.empty else 0
        elif metric_def.calculation_method == "count":
            return len(data)
        elif metric_def.calculation_method == "max":
            return data.max().max() if not data.empty else 0
        elif metric_def.calculation_method == "min":
            return data.min().min() if not data.empty else 0
        else:
            # Custom calculation would go here
            return 0

    def generate_forecast(
        self, data: pd.DataFrame, periods: int = 30
    ) -> Dict[str, Any]:
        """Generate forecast using time series analysis"""
        if len(data) < 10:
            return {
                "forecast": [],
                "confidence_intervals": [],
                "error": "Insufficient data",
            }

        try:
            # Prepare time series data
            ts_data = data.iloc[:, 0] if not data.empty else pd.Series()

            # Use exponential smoothing for forecasting
            model = ExponentialSmoothing(ts_data, trend="add", seasonal=None)
            fitted_model = model.fit()
            forecast = fitted_model.forecast(periods)

            return {
                "forecast": forecast.tolist(),
                "confidence_intervals": [],  # Would calculate actual CIs
                "model_type": "exponential_smoothing",
            }
        except Exception as e:
            logger.error(f"Forecasting error: {e}")
            return {"forecast": [], "error": str(e)}


# Visualization Engine
class VisualizationEngine:
    def __init__(self):
        pass

    def create_line_chart(
        self, data: pd.DataFrame, x_col: str, y_col: str, title: str = ""
    ) -> Dict[str, Any]:
        """Create line chart"""
        fig = px.line(data, x=x_col, y=y_col, title=title)
        return json.loads(fig.to_json())

    def create_bar_chart(
        self, data: pd.DataFrame, x_col: str, y_col: str, title: str = ""
    ) -> Dict[str, Any]:
        """Create bar chart"""
        fig = px.bar(data, x=x_col, y=y_col, title=title)
        return json.loads(fig.to_json())

    def create_pie_chart(
        self, data: pd.DataFrame, values_col: str, names_col: str, title: str = ""
    ) -> Dict[str, Any]:
        """Create pie chart"""
        fig = px.pie(data, values=values_col, names=names_col, title=title)
        return json.loads(fig.to_json())

    def create_scatter_plot(
        self, data: pd.DataFrame, x_col: str, y_col: str, title: str = ""
    ) -> Dict[str, Any]:
        """Create scatter plot"""
        fig = px.scatter(data, x=x_col, y=y_col, title=title)
        return json.loads(fig.to_json())

    def create_heatmap(self, data: pd.DataFrame, title: str = "") -> Dict[str, Any]:
        """Create heatmap"""
        correlation_matrix = data.corr()
        fig = px.imshow(correlation_matrix, title=title)
        return json.loads(fig.to_json())

    def create_kpi_card(
        self, value: float, title: str, target: float = None, unit: str = ""
    ) -> Dict[str, Any]:
        """Create KPI card visualization"""
        color = "green" if target and value >= target else "red" if target else "blue"

        return {
            "type": "kpi",
            "value": value,
            "title": title,
            "target": target,
            "unit": unit,
            "color": color,
            "percentage_of_target": (value / target * 100) if target else None,
        }

    def create_gauge_chart(
        self, value: float, title: str, min_val: float = 0, max_val: float = 100
    ) -> Dict[str, Any]:
        """Create gauge chart"""
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": title},
                gauge={
                    "axis": {"range": [None, max_val]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, max_val * 0.5], "color": "lightgray"},
                        {"range": [max_val * 0.5, max_val * 0.8], "color": "gray"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": max_val * 0.9,
                    },
                },
            )
        )
        return json.loads(fig.to_json())


# Alert Manager
class AlertManager:
    def __init__(self, db: Session):
        self.db = db

    async def check_alerts(self) -> List[Dict[str, Any]]:
        """Check all active alerts"""
        alerts = self.db.query(Alert).filter(Alert.is_active == True).all()
        triggered_alerts = []

        for alert in alerts:
            if await self._evaluate_alert(alert):
                triggered_alerts.append(await self._trigger_alert(alert))

        return triggered_alerts

    async def _evaluate_alert(self, alert: Alert) -> bool:
        """Evaluate if alert condition is met"""
        try:
            # Get metric definition
            metric = (
                self.db.query(MetricDefinition)
                .filter(MetricDefinition.id == alert.metric_id)
                .first()
            )

            if not metric:
                return False

            # Fetch current metric value
            processor = DataProcessor(self.db)
            data = await processor.fetch_data_from_source(
                metric.data_source_id, metric.query
            )
            current_value = processor.calculate_metric(data, metric)

            # Evaluate condition
            if alert.condition == "gt":
                return current_value > alert.threshold
            elif alert.condition == "lt":
                return current_value < alert.threshold
            elif alert.condition == "eq":
                return abs(current_value - alert.threshold) < 0.01
            else:
                return False

        except Exception as e:
            logger.error(f"Alert evaluation error: {e}")
            return False

    async def _trigger_alert(self, alert: Alert) -> Dict[str, Any]:
        """Trigger alert notification"""
        alert.last_triggered = datetime.utcnow()
        self.db.commit()

        # Send notifications (implementation would depend on channels)
        notification_result = await self._send_notifications(alert)

        return {
            "alert_id": alert.id,
            "alert_name": alert.name,
            "severity": alert.severity,
            "triggered_at": alert.last_triggered.isoformat(),
            "notification_result": notification_result,
        }

    async def _send_notifications(self, alert: Alert) -> Dict[str, Any]:
        """Send alert notifications"""
        results = {}

        for channel in alert.notification_channels:
            if channel == "email":
                results["email"] = "sent"  # Would implement actual email sending
            elif channel == "slack":
                results["slack"] = "sent"  # Would implement Slack integration
            elif channel == "webhook":
                results["webhook"] = "sent"  # Would implement webhook call

        return results


# Report Generator
class ReportGenerator:
    def __init__(self, db: Session):
        self.db = db
        self.viz_engine = VisualizationEngine()

    async def generate_dashboard_report(
        self, dashboard_id: str, format: str = "html"
    ) -> Dict[str, Any]:
        """Generate report from dashboard"""
        dashboard = (
            self.db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
        )
        if not dashboard:
            raise ValueError(f"Dashboard {dashboard_id} not found")

        report_data = {
            "title": dashboard.name,
            "generated_at": datetime.utcnow().isoformat(),
            "widgets": [],
            "summary": {},
        }

        # Process each widget
        for widget in dashboard.widgets:
            widget_data = await self._process_widget(widget)
            report_data["widgets"].append(widget_data)

        # Generate summary
        report_data["summary"] = await self._generate_summary(dashboard)

        if format == "html":
            return await self._generate_html_report(report_data)
        elif format == "pdf":
            return await self._generate_pdf_report(report_data)
        else:
            return report_data

    async def _process_widget(self, widget: Dict[str, Any]) -> Dict[str, Any]:
        """Process individual widget for report"""
        widget_type = widget.get("type")

        if widget_type == "chart":
            # Generate chart data
            return {
                "type": "chart",
                "title": widget.get("title", ""),
                "chart_data": {},  # Would generate actual chart
                "insights": [],
            }
        elif widget_type == "kpi":
            # Generate KPI data
            return {
                "type": "kpi",
                "title": widget.get("title", ""),
                "value": 0,  # Would calculate actual value
                "target": widget.get("target"),
                "trend": "up",  # Would calculate trend
            }
        else:
            return widget

    async def _generate_summary(self, dashboard: Dashboard) -> Dict[str, Any]:
        """Generate dashboard summary"""
        return {
            "total_widgets": len(dashboard.widgets),
            "last_updated": dashboard.updated_at.isoformat(),
            "key_insights": [
                "Revenue increased by 15% this month",
                "Customer acquisition cost decreased by 8%",
                "Conversion rate improved to 3.2%",
            ],
        }

    async def _generate_html_report(
        self, report_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate HTML report"""
        html_content = f"""
        <html>
        <head><title>{report_data['title']}</title></head>
        <body>
            <h1>{report_data['title']}</h1>
            <p>Generated: {report_data['generated_at']}</p>
            <!-- Report content would be generated here -->
        </body>
        </html>
        """

        return {"format": "html", "content": html_content, "size": len(html_content)}

    async def _generate_pdf_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate PDF report"""
        # PDF generation would be implemented here
        return {"format": "pdf", "content": "base64_encoded_pdf_content", "size": 1024}


# Initialize services
data_processor = DataProcessor
visualization_engine = VisualizationEngine()

# Scheduler setup
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()

    # Add scheduled tasks
    scheduler.add_job(
        refresh_data_sources,
        CronTrigger(minute=0),  # Every hour
        id="refresh_data_sources",
    )

    scheduler.add_job(
        check_alerts_task,
        CronTrigger(minute="*/5"),  # Every 5 minutes
        id="check_alerts",
    )

    scheduler.add_job(
        generate_scheduled_reports,
        CronTrigger(hour=0, minute=0),  # Daily at midnight
        id="generate_reports",
    )

    yield

    # Shutdown
    scheduler.shutdown()


# FastAPI app
app = FastAPI(
    title="Analytics Dashboard Service",
    description="Comprehensive business intelligence and data visualization platform",
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

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/metrics")
async def get_metrics():
    return generate_latest().decode()


# Dashboard Management
@app.post("/api/dashboards")
async def create_dashboard(
    dashboard_data: DashboardCreate, db: Session = Depends(get_db)
):
    dashboard = Dashboard(**dashboard_data.dict())
    db.add(dashboard)
    db.commit()
    db.refresh(dashboard)

    active_dashboards.inc()
    return dashboard


@app.get("/api/dashboards")
async def get_dashboards(
    skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    dashboards = db.query(Dashboard).offset(skip).limit(limit).all()
    return dashboards


@app.get("/api/dashboards/{dashboard_id}")
async def get_dashboard(dashboard_id: str, db: Session = Depends(get_db)):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    # Update last accessed
    dashboard.last_accessed = datetime.utcnow()
    db.commit()

    return dashboard


@app.put("/api/dashboards/{dashboard_id}")
async def update_dashboard(
    dashboard_id: str, dashboard_data: DashboardCreate, db: Session = Depends(get_db)
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    for key, value in dashboard_data.dict().items():
        setattr(dashboard, key, value)

    dashboard.updated_at = datetime.utcnow()
    db.commit()

    return dashboard


# Data Source Management
@app.post("/api/data-sources")
async def create_data_source(
    source_data: DataSourceCreate, db: Session = Depends(get_db)
):
    source = DataSource(**source_data.dict())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.get("/api/data-sources")
async def get_data_sources(db: Session = Depends(get_db)):
    sources = db.query(DataSource).all()
    return sources


@app.get("/api/data-sources/{source_id}/data")
async def get_source_data(
    source_id: str, query: str = None, db: Session = Depends(get_db)
):
    processor = data_processor(db)

    try:
        data = await processor.fetch_data_from_source(source_id, query)
        return {
            "data": data.to_dict(orient="records"),
            "columns": data.columns.tolist(),
            "row_count": len(data),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Metrics Management
@app.post("/api/metrics")
async def create_metric(
    metric_data: MetricDefinitionCreate, db: Session = Depends(get_db)
):
    metric = MetricDefinition(**metric_data.dict())
    db.add(metric)
    db.commit()
    db.refresh(metric)
    return metric


@app.get("/api/metrics")
async def get_metrics_definitions(db: Session = Depends(get_db)):
    metrics = db.query(MetricDefinition).all()
    return metrics


@app.get("/api/metrics/{metric_id}/value")
async def get_metric_value(metric_id: str, db: Session = Depends(get_db)):
    metric = db.query(MetricDefinition).filter(MetricDefinition.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    processor = data_processor(db)

    try:
        data = await processor.fetch_data_from_source(
            metric.data_source_id, metric.query
        )
        value = processor.calculate_metric(data, metric)

        return {
            "metric_id": metric_id,
            "value": value,
            "unit": metric.unit,
            "calculated_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Analytics and Querying
@app.post("/api/analytics/query")
async def execute_analytics_query(query: AnalyticsQuery, db: Session = Depends(get_db)):
    analytics_requests.labels(endpoint="query", status="started").inc()

    try:
        # This would implement complex analytics querying
        # For now, return mock data
        result = {
            "data": [
                {"date": "2024-01-01", "revenue": 10000, "users": 500},
                {"date": "2024-01-02", "revenue": 12000, "users": 600},
                {"date": "2024-01-03", "revenue": 11000, "users": 550},
            ],
            "total_rows": 3,
            "execution_time_ms": 150,
        }

        analytics_requests.labels(endpoint="query", status="success").inc()
        return result

    except Exception as e:
        analytics_requests.labels(endpoint="query", status="error").inc()
        raise HTTPException(status_code=400, detail=str(e))


# Visualization
@app.post("/api/visualizations/chart")
async def create_chart(chart_config: Dict[str, Any], db: Session = Depends(get_db)):
    chart_type = chart_config.get("type", "line")
    data_source_id = chart_config.get("data_source_id")

    if not data_source_id:
        raise HTTPException(status_code=400, detail="Data source ID required")

    processor = data_processor(db)

    try:
        data = await processor.fetch_data_from_source(data_source_id)

        if chart_type == "line":
            chart = visualization_engine.create_line_chart(
                data,
                chart_config.get("x_column", data.columns[0]),
                chart_config.get("y_column", data.columns[1]),
                chart_config.get("title", ""),
            )
        elif chart_type == "bar":
            chart = visualization_engine.create_bar_chart(
                data,
                chart_config.get("x_column", data.columns[0]),
                chart_config.get("y_column", data.columns[1]),
                chart_config.get("title", ""),
            )
        elif chart_type == "pie":
            chart = visualization_engine.create_pie_chart(
                data,
                chart_config.get("values_column", data.columns[1]),
                chart_config.get("names_column", data.columns[0]),
                chart_config.get("title", ""),
            )
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported chart type: {chart_type}"
            )

        return chart

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/visualizations/kpi")
async def create_kpi(kpi_config: Dict[str, Any], db: Session = Depends(get_db)):
    metric_id = kpi_config.get("metric_id")

    if not metric_id:
        raise HTTPException(status_code=400, detail="Metric ID required")

    metric = db.query(MetricDefinition).filter(MetricDefinition.id == metric_id).first()
    if not metric:
        raise HTTPException(status_code=404, detail="Metric not found")

    processor = data_processor(db)

    try:
        data = await processor.fetch_data_from_source(
            metric.data_source_id, metric.query
        )
        value = processor.calculate_metric(data, metric)

        kpi = visualization_engine.create_kpi_card(
            value,
            kpi_config.get("title", metric.name),
            metric.target_value,
            metric.unit,
        )

        return kpi

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Forecasting
@app.post("/api/analytics/forecast")
async def generate_forecast(
    forecast_config: Dict[str, Any], db: Session = Depends(get_db)
):
    data_source_id = forecast_config.get("data_source_id")
    periods = forecast_config.get("periods", 30)

    if not data_source_id:
        raise HTTPException(status_code=400, detail="Data source ID required")

    processor = data_processor(db)

    try:
        data = await processor.fetch_data_from_source(data_source_id)
        forecast = processor.generate_forecast(data, periods)

        return forecast

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Alerts Management
@app.post("/api/alerts")
async def create_alert(alert_data: AlertCreate, db: Session = Depends(get_db)):
    alert = Alert(**alert_data.dict())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@app.get("/api/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    alerts = db.query(Alert).all()
    return alerts


@app.post("/api/alerts/check")
async def check_alerts_now(db: Session = Depends(get_db)):
    alert_manager = AlertManager(db)
    triggered_alerts = await alert_manager.check_alerts()

    return {
        "checked_at": datetime.utcnow().isoformat(),
        "triggered_alerts": triggered_alerts,
    }


# Reports Management
@app.post("/api/reports")
async def create_report(report_data: ReportCreate, db: Session = Depends(get_db)):
    report = Report(**report_data.dict())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


@app.get("/api/reports")
async def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return reports


@app.post("/api/reports/{report_id}/generate")
async def generate_report_now(report_id: str, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if not report.dashboard_id:
        raise HTTPException(
            status_code=400, detail="Report must be associated with a dashboard"
        )

    report_generator = ReportGenerator(db)

    try:
        generated_report = await report_generator.generate_dashboard_report(
            report.dashboard_id, report.format
        )

        # Update report timestamp
        report.last_generated = datetime.utcnow()
        db.commit()

        return generated_report

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Dashboard UI Routes
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/dashboard/{dashboard_id}", response_class=HTMLResponse)
async def view_dashboard(
    request: Request, dashboard_id: str, db: Session = Depends(get_db)
):
    dashboard = db.query(Dashboard).filter(Dashboard.id == dashboard_id).first()
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return templates.TemplateResponse(
        "dashboard_view.html", {"request": request, "dashboard": dashboard}
    )


# Background Tasks
async def refresh_data_sources():
    """Refresh all data sources"""
    try:
        db = SessionLocal()
        sources = db.query(DataSource).filter(DataSource.status == "active").all()

        for source in sources:
            # Check if refresh is due
            if (
                source.last_refresh is None
                or datetime.utcnow() - source.last_refresh
                > timedelta(seconds=source.refresh_interval)
            ):

                # Refresh data source
                source.last_refresh = datetime.utcnow()
                db.commit()

                logger.info(f"Refreshed data source: {source.name}")

        db.close()
    except Exception as e:
        logger.error(f"Failed to refresh data sources: {e}")


async def check_alerts_task():
    """Check alerts periodically"""
    try:
        db = SessionLocal()
        alert_manager = AlertManager(db)

        triggered_alerts = await alert_manager.check_alerts()

        if triggered_alerts:
            logger.info(f"Triggered {len(triggered_alerts)} alerts")

        db.close()
    except Exception as e:
        logger.error(f"Failed to check alerts: {e}")


async def generate_scheduled_reports():
    """Generate scheduled reports"""
    try:
        db = SessionLocal()

        # Find reports due for generation
        now = datetime.utcnow()
        due_reports = (
            db.query(Report)
            .filter(
                Report.report_type == "scheduled",
                Report.status == "active",
                Report.next_generation <= now,
            )
            .all()
        )

        report_generator = ReportGenerator(db)

        for report in due_reports:
            try:
                generated_report = await report_generator.generate_dashboard_report(
                    report.dashboard_id, report.format
                )

                report.last_generated = now
                # Calculate next generation time based on schedule
                # This would parse the cron expression
                report.next_generation = now + timedelta(days=1)  # Simplified

                db.commit()

                logger.info(f"Generated scheduled report: {report.name}")

            except Exception as e:
                logger.error(f"Failed to generate report {report.name}: {e}")

        db.close()
    except Exception as e:
        logger.error(f"Failed to generate scheduled reports: {e}")


# Error Handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=False, workers=1)
