# main.py - FastAPI application with integrations hub
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from integrations_hub import wire_integrations, _state, _petfinder_token, lifespan
from content_sources import router as content_router
from typing import Optional
import httpx
from shared_utils import get_secret
import logging
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import API routers
try:
    from backend.api.pet_endpoints import router as pet_router
except ImportError:
    # Fallback for development
    try:
        from api.pet_endpoints import router as pet_router
    except ImportError:
        pet_router = None
        logging.warning("Pet endpoints not available - check backend structure")

# Import places router
try:
    from app.routers.places import router as places_router
except ImportError:
    places_router = None
    logging.warning("Places router not available - check app structure")

# Import new social media and analytics routers
try:
    from backend.routers.social import router as social_router
except ImportError:
    social_router = None
    logging.warning("Social media router not available - check backend structure")

try:
    from backend.routers.payment_webhooks import router as webhooks_router
except ImportError:
    webhooks_router = None
    logging.warning("Payment webhooks router not available - check backend structure")

try:
    from backend.routers.analytics_hub import router as analytics_router
except ImportError:
    analytics_router = None
    logging.warning("Analytics hub router not available - check backend structure")

# Import integrations max router
try:
    from app.routers.integrations_max import router as integrations_max_router
except ImportError:
    integrations_max_router = None
    logging.warning("Integrations max router not available - check app structure")

# Import OAuth router
try:
    from app.routers.oauth import router as oauth_router
except ImportError:
    oauth_router = None
    logging.warning("OAuth router not available - check app structure")

# Import configuration validator
try:
    from config.validator import validate_startup_config
    from config.environment import config
except ImportError:
    validate_startup_config = None
    config = None
    logging.warning("Configuration modules not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Validate configuration at startup
if validate_startup_config:
    logger.info("Validating application configuration...")
    config_valid = validate_startup_config()
    if not config_valid:
        logger.error("❌ Configuration validation failed - check logs above")
        logger.error("Application startup aborted due to configuration errors")
        exit(1)
    logger.info("✅ Configuration validation passed")
else:
    logger.warning("Configuration validator not available - skipping validation")

# Create FastAPI app
app = FastAPI(
    title="Online Production API",
    description="Production-ready API with pet care services and affiliate processing",
    version="1.0.0",
    docs_url="/docs" if __name__ == "__main__" else None,  # Disable docs in production
    redoc_url="/redoc" if __name__ == "__main__" else None,
    lifespan=lifespan
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1", "*.netlify.app"]  # Configure for production
)

# Configure CORS with security considerations
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.netlify.app"  # Configure appropriately for production
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=600  # Cache preflight requests for 10 minutes
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")
wire_integrations(app)  # mounts /integrations + starts background health checker
app.include_router(content_router)  # mounts /content endpoints

# Include pet endpoints if available
if pet_router:
    app.include_router(pet_router, prefix="/api/v1", tags=["pets"])
    logger.info("Pet endpoints mounted at /api/v1")
else:
    logger.warning("Pet endpoints not mounted - router not available")

# Include places router if available
if places_router:
    app.include_router(places_router, prefix="/places", tags=["places"])
    logger.info("Places endpoints mounted at /places")
else:
    logger.warning("Places endpoints not mounted - router not available")

# Include social media router if available
if social_router:
    app.include_router(social_router, tags=["social"])
    logger.info("Social media endpoints mounted at /social")
else:
    logger.warning("Social media endpoints not mounted - router not available")

# Include payment webhooks router if available
if webhooks_router:
    app.include_router(webhooks_router, tags=["webhooks"])
    logger.info("Payment webhook endpoints mounted at /webhooks")
else:
    logger.warning("Payment webhook endpoints not mounted - router not available")

# Include analytics hub router if available
if analytics_router:
    app.include_router(analytics_router, tags=["analytics"])
    logger.info("Analytics hub endpoints mounted at /analytics")
else:
    logger.warning("Analytics hub endpoints not mounted - router not available")

# Mount integrations max router
if integrations_max_router:
    app.include_router(integrations_max_router, tags=["integrations"])
    logger.info("Integrations max endpoints mounted at /integrations")
else:
    logger.warning("Integrations max endpoints not mounted - router not available")

# Mount OAuth router
if oauth_router:
    app.include_router(oauth_router, tags=["oauth"])
    logger.info("OAuth endpoints mounted at /oauth")
else:
    logger.warning("OAuth endpoints not mounted - router not available")

# Add pets search endpoint
@app.get("/pets/search")
async def pets_search(
    animal: str = Query("dog", pattern="^(dog|cat)$"),
    location: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
):
    """Search for pets using TheDogAPI or TheCatAPI"""
    if animal == "dog":
        try:
            key = get_secret("DOG_API_KEY")
            headers = {"x-api-key": key} if key else {}
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.get(f"https://api.thedogapi.com/v1/images/search?limit={limit}&has_breeds=1", headers=headers)
                r.raise_for_status()
                return {"provider": "thedogapi", "data": r.json()}
        except Exception as e:
            raise HTTPException(500, f"Failed to fetch dog data: {str(e)}")
    else:
        try:
            key = get_secret("CAT_API_KEY")
            headers = {"x-api-key": key} if key else {}
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.get(f"https://api.thecatapi.com/v1/images/search?limit={limit}&has_breeds=1", headers=headers)
                r.raise_for_status()
                return {"provider": "thecatapi", "data": r.json()}
        except Exception as e:
            raise HTTPException(500, f"Failed to fetch cat data: {str(e)}")

# Add configuration status endpoint
@app.get("/api/status")
async def get_configuration_status():
    """Get current configuration status including geocoding APIs"""
    try:
        if config:
            status_data = config.get_api_status()
            return {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "configuration": status_data,
                "message": "Configuration status retrieved successfully"
            }
        else:
            return {
                "success": False,
                "timestamp": datetime.now().isoformat(),
                "message": "Configuration not available"
            }
    except Exception as e:
        logger.error(f"Configuration status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Configuration status service unavailable")

@app.get("/pets/types")
async def pets_types():
    """Get pet types from Petfinder API with fallback to static data"""
    # Try Petfinder (if enabled + creds)
    pf = _state["providers"].get("petfinder")
    if pf and pf.enabled and pf.status == "green":
        token = await _petfinder_token()
        if token:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.get("https://api.petfinder.com/v2/types",
                                     headers={"Authorization": f"Bearer {token}"})
                if r.status_code < 400:
                    return {"provider": "petfinder", "types": r.json().get("types", [])}
    # Fallback static set
    return {
        "provider": "static",
        "types": [
            {"name": "Dog"}, {"name": "Cat"}, {"name": "Bird"}, {"name": "Rabbit"},
            {"name": "Small & Furry"}, {"name": "Scales, Fins & Other"},
            {"name": "Horse"}, {"name": "Barnyard"}
        ],
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for Docker healthcheck"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "fastapi-api"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)