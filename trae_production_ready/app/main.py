from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .utils.metrics import PrometheusMiddleware, get_metrics
from .api.v1 import health, websocket, paste
# Import models to register them with Base
from .models import user, base

# Create database tables
# Base.metadata.create_all(bind=engine)  # Temporarily disabled

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="Production-ready FastAPI application with WebSockets, metrics, and database",
        version="1.0.0",
        debug=settings.debug
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)
    
    # Include routers
    app.include_router(health.router, tags=["health"])
    app.include_router(websocket.router, tags=["websocket"])
    app.include_router(paste.router, prefix="/api/v1/paste", tags=["paste"])
    
    # Metrics endpoint
    app.get("/metrics")(get_metrics)
    
    return app

app = create_app()
