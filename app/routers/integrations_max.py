from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import json
import os
from datetime import datetime, timedelta
import httpx
from utils.http import http_get_with_backoff

router = APIRouter(prefix="/integrations", tags=["integrations"])

# File paths
PROVIDERS_FILE = "data/providers.json"
AFFILIATES_FILE = "data/affiliates.json"
KEYS_FILE = "data/keys.json"
METRICS_FILE = "data/metrics.json"
POLICY_FILE = "data/policy.json"

# Optional secret store functions (implement if needed)
def get_secret(key: str) -> Optional[str]:
    """Get secret from environment or secret store"""
    return os.getenv(key)

def set_secret(key: str, value: str) -> bool:
    """Set secret in secret store (placeholder)"""
    # In production, implement proper secret storage
    return True

# JSON load/save helpers
def load_json(filepath: str, default: Any = None) -> Any:
    """Load JSON file with default fallback"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}

def save_json(filepath: str, data: Any) -> bool:
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False

# Models
class ProviderIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=30)
    docs_url: str = Field(..., pattern=r'^https?://')
    enabled: bool = False
    auto_disable: bool = True
    priority: int = Field(default=1, ge=1, le=10)

class CredentialIn(BaseModel):
    provider_id: str
    key_name: str
    key_value: str

class ReportIn(BaseModel):
    provider_id: str
    success: bool
    error_message: Optional[str] = None
    response_time_ms: Optional[int] = None

class AffiliateIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    vertical: str = Field(..., min_length=1, max_length=30)
    affiliate_id: str = Field(..., min_length=1, max_length=100)
    enabled: bool = False

# Default providers
DEFAULT_PROVIDERS = {
    "images_unsplash": {
        "name": "Unsplash",
        "category": "images",
        "docs_url": "https://unsplash.com/developers",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True
    },
    "images_pixabay": {
        "name": "Pixabay",
        "category": "images",
        "docs_url": "https://pixabay.com/api/docs/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True
    },
    "news_guardian": {
        "name": "Guardian",
        "category": "news",
        "docs_url": "https://open-platform.theguardian.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True
    },
    "news_newsapi": {
        "name": "NewsAPI",
        "category": "news",
        "docs_url": "https://newsapi.org/docs",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True
    },
    "geo_openstreet": {
        "name": "OpenStreetMap",
        "category": "geo",
        "docs_url": "https://nominatim.org/",
        "enabled": True,
        "auto_disable": False,
        "priority": 1,
        "requires_key": False,
        "free_tier": True
    },
    "pets_catapi": {
        "name": "TheCatAPI",
        "category": "pets",
        "docs_url": "https://thecatapi.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True
    },
    "pets_dogapi": {
        "name": "TheDogAPI",
        "category": "pets",
        "docs_url": "https://thedogapi.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True
    },
    "weather_openmeteo": {
        "name": "Open-Meteo",
        "category": "weather",
        "docs_url": "https://open-meteo.com/",
        "enabled": True,
        "auto_disable": False,
        "priority": 1,
        "requires_key": False,
        "free_tier": True
    },
    "weather_openweather": {
        "name": "OpenWeather",
        "category": "weather",
        "docs_url": "https://openweathermap.org/api",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True
    },
    "social_instagram": {
        "name": "Instagram",
        "category": "social",
        "docs_url": "https://developers.facebook.com/docs/instagram-api/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": False,
        "oauth_required": True
    },
    "social_tiktok": {
        "name": "TikTok",
        "category": "social",
        "docs_url": "https://developers.tiktok.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": False,
        "oauth_required": True
    },
    "ai_openai": {
        "name": "OpenAI",
        "category": "ai",
        "docs_url": "https://platform.openai.com/docs",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": False
    },
    "email_sendgrid": {
        "name": "SendGrid",
        "category": "email",
        "docs_url": "https://docs.sendgrid.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True
    }
}

# Default affiliates (all disabled)
DEFAULT_AFFILIATES = {
    "general_amazon": {
        "name": "Amazon Associates",
        "vertical": "general",
        "affiliate_id": "",
        "enabled": False
    },
    "tech_bestbuy": {
        "name": "Best Buy",
        "vertical": "tech",
        "affiliate_id": "",
        "enabled": False
    },
    "wellness_iherb": {
        "name": "iHerb",
        "vertical": "wellness",
        "affiliate_id": "",
        "enabled": False
    },
    "ai_openai_partner": {
        "name": "OpenAI Partner",
        "vertical": "ai",
        "affiliate_id": "",
        "enabled": False
    },
    "pets_chewy": {
        "name": "Chewy",
        "vertical": "pets",
        "affiliate_id": "",
        "enabled": False
    },
    "restricted_gambling": {
        "name": "Gambling Site",
        "vertical": "restricted",
        "affiliate_id": "",
        "enabled": False
    },
    "restricted_crypto": {
        "name": "Crypto Exchange",
        "vertical": "restricted",
        "affiliate_id": "",
        "enabled": False
    },
    "restricted_adult": {
        "name": "Adult Content",
        "vertical": "restricted",
        "affiliate_id": "",
        "enabled": False
    }
}

# Default policy (all restricted verticals disabled)
DEFAULT_POLICY = {
    "restricted_verticals_enabled": False,
    "gambling_enabled": False,
    "crypto_enabled": False,
    "adult_enabled": False,
    "last_updated": datetime.now().isoformat()
}

# State loaders
def load_registry() -> Dict:
    """Load provider registry with defaults"""
    registry = load_json(PROVIDERS_FILE, DEFAULT_PROVIDERS.copy())
    # Merge with defaults to ensure new providers are added
    for key, default_provider in DEFAULT_PROVIDERS.items():
        if key not in registry:
            registry[key] = default_provider
    return registry

def load_affiliates() -> Dict:
    """Load affiliates with defaults"""
    affiliates = load_json(AFFILIATES_FILE, DEFAULT_AFFILIATES.copy())
    # Merge with defaults
    for key, default_affiliate in DEFAULT_AFFILIATES.items():
        if key not in affiliates:
            affiliates[key] = default_affiliate
    return affiliates

def load_keys() -> Dict:
    """Load API keys"""
    return load_json(KEYS_FILE, {})

def load_metrics() -> Dict:
    """Load usage metrics"""
    return load_json(METRICS_FILE, {})

def load_policy() -> Dict:
    """Load policy settings"""
    return load_json(POLICY_FILE, DEFAULT_POLICY.copy())

# Status light logic
def get_provider_status_color(provider_id: str, provider: Dict) -> str:
    """Get status color for provider"""
    if not provider.get("enabled", False):
        return "gray"  # Disabled
    
    # Check credentials
    if provider.get("requires_key", False):
        keys = load_keys()
        if provider_id not in keys or not keys[provider_id]:
            return "red"  # Missing credentials
    
    # Check auto-disable status
    if provider.get("auto_disable", False):
        metrics = load_metrics()
        provider_metrics = metrics.get(provider_id, {})
        
        # Check recent errors (last 24 hours)
        recent_errors = provider_metrics.get("recent_errors", 0)
        if recent_errors >= 5:
            return "red"  # Too many recent errors
    
    return "green"  # All good

def get_affiliate_status_color(affiliate_id: str, affiliate: Dict) -> str:
    """Get status color for affiliate"""
    if not affiliate.get("enabled", False):
        return "gray"  # Disabled
    
    # Check policy for restricted verticals
    vertical = affiliate.get("vertical")
    if vertical == "restricted":
        policy = load_policy()
        if not policy.get("restricted_verticals_enabled", False):
            return "red"  # Policy disabled
    
    # Check affiliate ID
    if not affiliate.get("affiliate_id", "").strip():
        return "red"  # Missing affiliate ID
    
    return "green"  # All good

# Provider routes
@router.get("/providers/categories")
async def list_categories():
    """List all provider categories"""
    registry = load_registry()
    categories = list(set(p.get("category", "unknown") for p in registry.values()))
    return {"categories": sorted(categories)}

@router.get("/providers")
async def list_providers():
    """List all providers with status"""
    registry = load_registry()
    result = []
    
    for provider_id, provider in registry.items():
        status_color = get_provider_status_color(provider_id, provider)
        result.append({
            "id": provider_id,
            "name": provider["name"],
            "category": provider["category"],
            "enabled": provider.get("enabled", False),
            "status_color": status_color,
            "docs_url": provider["docs_url"],
            "priority": provider.get("priority", 1),
            "free_tier": provider.get("free_tier", False),
            "requires_key": provider.get("requires_key", False),
            "oauth_required": provider.get("oauth_required", False)
        })
    
    return {"providers": sorted(result, key=lambda x: (x["category"], x["priority"]))}

@router.post("/providers")
async def add_provider(provider: ProviderIn):
    """Add a new provider"""
    registry = load_registry()
    
    # Generate ID from name
    provider_id = f"{provider.category}_{provider.name.lower().replace(' ', '_')}"
    
    if provider_id in registry:
        raise HTTPException(status_code=400, detail="Provider already exists")
    
    registry[provider_id] = {
        "name": provider.name,
        "category": provider.category,
        "docs_url": provider.docs_url,
        "enabled": provider.enabled,
        "auto_disable": provider.auto_disable,
        "priority": provider.priority,
        "requires_key": True,  # Assume new providers need keys
        "free_tier": False     # Assume paid by default
    }
    
    if not save_json(PROVIDERS_FILE, registry):
        raise HTTPException(status_code=500, detail="Failed to save provider")
    
    return {"message": "Provider added", "id": provider_id}

@router.post("/providers/{provider_id}/enable")
async def enable_provider(provider_id: str, enabled: bool = True):
    """Enable/disable a provider"""
    registry = load_registry()
    
    if provider_id not in registry:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    registry[provider_id]["enabled"] = enabled
    
    if not save_json(PROVIDERS_FILE, registry):
        raise HTTPException(status_code=500, detail="Failed to update provider")
    
    return {"message": f"Provider {'enabled' if enabled else 'disabled'}"}

@router.post("/providers/{provider_id}/credentials")
async def upsert_credentials(provider_id: str, credential: CredentialIn):
    """Add/update provider credentials"""
    registry = load_registry()
    
    if provider_id not in registry:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    keys = load_keys()
    if provider_id not in keys:
        keys[provider_id] = {}
    
    keys[provider_id][credential.key_name] = credential.key_value
    
    if not save_json(KEYS_FILE, keys):
        raise HTTPException(status_code=500, detail="Failed to save credentials")
    
    return {"message": "Credentials updated"}

@router.get("/providers/active")
async def get_active_providers():
    """Get active providers by category"""
    registry = load_registry()
    active = {}
    
    for provider_id, provider in registry.items():
        if provider.get("enabled", False):
            category = provider["category"]
            if category not in active:
                active[category] = []
            
            status_color = get_provider_status_color(provider_id, provider)
            if status_color == "green":  # Only include healthy providers
                active[category].append({
                    "id": provider_id,
                    "name": provider["name"],
                    "priority": provider.get("priority", 1)
                })
    
    # Sort by priority
    for category in active:
        active[category].sort(key=lambda x: x["priority"])
    
    return {"active_providers": active}

@router.post("/providers/{provider_id}/rotate")
async def rotate_provider(provider_id: str):
    """Rotate to next provider in category"""
    registry = load_registry()
    
    if provider_id not in registry:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    current_provider = registry[provider_id]
    category = current_provider["category"]
    
    # Find next provider in same category
    category_providers = [
        (pid, p) for pid, p in registry.items() 
        if p["category"] == category and p.get("enabled", False)
    ]
    
    if len(category_providers) <= 1:
        raise HTTPException(status_code=400, detail="No alternative providers available")
    
    # Sort by priority and find next
    category_providers.sort(key=lambda x: x[1].get("priority", 1))
    current_index = next((i for i, (pid, _) in enumerate(category_providers) if pid == provider_id), -1)
    
    if current_index == -1:
        next_provider_id = category_providers[0][0]
    else:
        next_provider_id = category_providers[(current_index + 1) % len(category_providers)][0]
    
    return {
        "message": "Rotated to next provider",
        "from": provider_id,
        "to": next_provider_id,
        "provider_name": registry[next_provider_id]["name"]
    }

@router.post("/providers/{provider_id}/report")
async def report_usage(provider_id: str, report: ReportIn):
    """Report provider usage and errors"""
    registry = load_registry()
    
    if provider_id not in registry:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    metrics = load_metrics()
    if provider_id not in metrics:
        metrics[provider_id] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "recent_errors": 0,
            "last_success": None,
            "last_error": None,
            "avg_response_time": 0
        }
    
    provider_metrics = metrics[provider_id]
    provider_metrics["total_requests"] += 1
    
    if report.success:
        provider_metrics["successful_requests"] += 1
        provider_metrics["last_success"] = datetime.now().isoformat()
        provider_metrics["recent_errors"] = max(0, provider_metrics["recent_errors"] - 1)
    else:
        provider_metrics["failed_requests"] += 1
        provider_metrics["last_error"] = datetime.now().isoformat()
        provider_metrics["recent_errors"] += 1
        
        # Auto-disable if too many recent errors
        if (provider_metrics["recent_errors"] >= 5 and 
            registry[provider_id].get("auto_disable", False)):
            registry[provider_id]["enabled"] = False
            save_json(PROVIDERS_FILE, registry)
    
    if report.response_time_ms:
        # Simple moving average
        current_avg = provider_metrics.get("avg_response_time", 0)
        provider_metrics["avg_response_time"] = (
            (current_avg * (provider_metrics["total_requests"] - 1) + report.response_time_ms) /
            provider_metrics["total_requests"]
        )
    
    if not save_json(METRICS_FILE, metrics):
        raise HTTPException(status_code=500, detail="Failed to save metrics")
    
    return {"message": "Usage reported"}

# Health/test ping route
@router.get("/test-call")
async def test_call(provider_id: str):
    """Test call to provider's documentation URL"""
    registry = load_registry()
    
    if provider_id not in registry:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider = registry[provider_id]
    docs_url = provider["docs_url"]
    
    try:
        start_time = datetime.now()
        response = await http_get_with_backoff(docs_url, method="HEAD")
        end_time = datetime.now()
        
        response_time = int((end_time - start_time).total_seconds() * 1000)
        
        # Report successful test
        await report_usage(provider_id, ReportIn(
            provider_id=provider_id,
            success=True,
            response_time_ms=response_time
        ))
        
        return {
            "provider_id": provider_id,
            "provider_name": provider["name"],
            "status": "healthy",
            "response_time_ms": response_time,
            "docs_url": docs_url
        }
        
    except Exception as e:
        # Report failed test
        await report_usage(provider_id, ReportIn(
            provider_id=provider_id,
            success=False,
            error_message=str(e)
        ))
        
        return {
            "provider_id": provider_id,
            "provider_name": provider["name"],
            "status": "unhealthy",
            "error": str(e),
            "docs_url": docs_url
        }

# Affiliate routes
@router.get("/affiliates/verticals")
async def list_verticals():
    """List all affiliate verticals"""
    affiliates = load_affiliates()
    verticals = list(set(a.get("vertical", "unknown") for a in affiliates.values()))
    return {"verticals": sorted(verticals)}

@router.get("/affiliates")
async def list_affiliates():
    """List all affiliates with status"""
    affiliates = load_affiliates()
    result = []
    
    for affiliate_id, affiliate in affiliates.items():
        status_color = get_affiliate_status_color(affiliate_id, affiliate)
        result.append({
            "id": affiliate_id,
            "name": affiliate["name"],
            "vertical": affiliate["vertical"],
            "enabled": affiliate.get("enabled", False),
            "status_color": status_color,
            "affiliate_id": affiliate.get("affiliate_id", "")
        })
    
    return {"affiliates": sorted(result, key=lambda x: x["vertical"])}

@router.post("/affiliates")
async def add_affiliate(affiliate: AffiliateIn):
    """Add a new affiliate"""
    affiliates = load_affiliates()
    
    # Generate ID from vertical and name
    affiliate_key = f"{affiliate.vertical}_{affiliate.name.lower().replace(' ', '_')}"
    
    if affiliate_key in affiliates:
        raise HTTPException(status_code=400, detail="Affiliate already exists")
    
    affiliates[affiliate_key] = {
        "name": affiliate.name,
        "vertical": affiliate.vertical,
        "affiliate_id": affiliate.affiliate_id,
        "enabled": affiliate.enabled
    }
    
    if not save_json(AFFILIATES_FILE, affiliates):
        raise HTTPException(status_code=500, detail="Failed to save affiliate")
    
    return {"message": "Affiliate added", "id": affiliate_key}

@router.post("/affiliates/{affiliate_key}/enable")
async def enable_affiliate(affiliate_key: str, enabled: bool = True):
    """Enable/disable an affiliate"""
    affiliates = load_affiliates()
    
    if affiliate_key not in affiliates:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    affiliates[affiliate_key]["enabled"] = enabled
    
    if not save_json(AFFILIATES_FILE, affiliates):
        raise HTTPException(status_code=500, detail="Failed to update affiliate")
    
    return {"message": f"Affiliate {'enabled' if enabled else 'disabled'}"}

@router.post("/affiliates/{affiliate_key}/credentials")
async def upsert_affiliate_id(affiliate_key: str, affiliate_id: str):
    """Update affiliate ID"""
    affiliates = load_affiliates()
    
    if affiliate_key not in affiliates:
        raise HTTPException(status_code=404, detail="Affiliate not found")
    
    affiliates[affiliate_key]["affiliate_id"] = affiliate_id
    
    if not save_json(AFFILIATES_FILE, affiliates):
        raise HTTPException(status_code=500, detail="Failed to update affiliate")
    
    return {"message": "Affiliate ID updated"}

# Policy controls
@router.get("/policy")
async def get_policy():
    """Get current policy settings"""
    return load_policy()

@router.post("/policy")
async def set_policy(policy_updates: Dict[str, Any]):
    """Update policy settings"""
    policy = load_policy()
    
    # Update allowed fields
    allowed_fields = [
        "restricted_verticals_enabled",
        "gambling_enabled", 
        "crypto_enabled",
        "adult_enabled"
    ]
    
    for field in allowed_fields:
        if field in policy_updates:
            policy[field] = policy_updates[field]
    
    policy["last_updated"] = datetime.now().isoformat()
    
    if not save_json(POLICY_FILE, policy):
        raise HTTPException(status_code=500, detail="Failed to save policy")
    
    return {"message": "Policy updated", "policy": policy}

# Channel-specific top affiliate suggestions
CHANNEL_MAP = {
    "tech": ["tech_bestbuy", "general_amazon"],
    "wellness": ["wellness_iherb", "general_amazon"],
    "pets": ["pets_chewy", "general_amazon"],
    "ai": ["ai_openai_partner", "tech_bestbuy"],
    "general": ["general_amazon"]
}

@router.get("/affiliates/suggestions/{channel}")
async def get_top_affiliates(channel: str):
    """Get top affiliate suggestions for channel"""
    if channel not in CHANNEL_MAP:
        raise HTTPException(status_code=404, detail="Channel not found")
    
    affiliates = load_affiliates()
    suggestions = []
    
    for affiliate_key in CHANNEL_MAP[channel]:
        if affiliate_key in affiliates:
            affiliate = affiliates[affiliate_key]
            status_color = get_affiliate_status_color(affiliate_key, affiliate)
            
            suggestions.append({
                "id": affiliate_key,
                "name": affiliate["name"],
                "vertical": affiliate["vertical"],
                "status_color": status_color,
                "enabled": affiliate.get("enabled", False)
            })
    
    return {"channel": channel, "suggestions": suggestions}

# Admin UI
@router.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    """Admin interface for managing integrations"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Integrations Admin</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .section { margin-bottom: 30px; }
        .status-light { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-green { background-color: #4CAF50; }
        .status-red { background-color: #f44336; }
        .status-gray { background-color: #9E9E9E; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        button { padding: 6px 12px; margin: 2px; cursor: pointer; }
        .btn-primary { background-color: #007bff; color: white; border: none; }
        .btn-success { background-color: #28a745; color: white; border: none; }
        .btn-danger { background-color: #dc3545; color: white; border: none; }
        .btn-secondary { background-color: #6c757d; color: white; border: none; }
        input, select { padding: 4px; margin: 2px; }
        .form-group { margin: 10px 0; }
        .policy-controls { background-color: #f8f9fa; padding: 15px; border-radius: 5px; }
        .rotate-buttons { margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Integrations Admin</h1>
        
        <!-- Providers Section -->
        <div class="section">
            <h2>Providers</h2>
            <div class="rotate-buttons">
                <button class="btn-secondary" onclick="rotateCategory('images')">Rotate Images</button>
                <button class="btn-secondary" onclick="rotateCategory('news')">Rotate News</button>
                <button class="btn-secondary" onclick="rotateCategory('weather')">Rotate Weather</button>
                <button class="btn-secondary" onclick="rotateCategory('pets')">Rotate Pets</button>
            </div>
            <table id="providers-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Priority</th>
                        <th>Free Tier</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
        
        <!-- Affiliates Section -->
        <div class="section">
            <h2>Affiliates</h2>
            <table id="affiliates-table">
                <thead>
                    <tr>
                        <th>Status</th>
                        <th>Name</th>
                        <th>Vertical</th>
                        <th>Affiliate ID</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
        
        <!-- Policy Controls -->
        <div class="section">
            <h2>Policy Controls</h2>
            <div class="policy-controls">
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="restricted-verticals"> Enable Restricted Verticals
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="gambling-enabled"> Enable Gambling
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="crypto-enabled"> Enable Crypto
                    </label>
                </div>
                <div class="form-group">
                    <label>
                        <input type="checkbox" id="adult-enabled"> Enable Adult Content
                    </label>
                </div>
                <button class="btn-primary" onclick="updatePolicy()">Update Policy</button>
            </div>
        </div>
        
        <!-- Top Affiliates Section -->
        <div class="section">
            <h2>Top Affiliates by Channel</h2>
            <select id="channel-select" onchange="loadChannelAffiliates()">
                <option value="tech">Tech</option>
                <option value="wellness">Wellness</option>
                <option value="pets">Pets</option>
                <option value="ai">AI</option>
                <option value="general">General</option>
            </select>
            <div id="channel-affiliates"></div>
        </div>
        
        <!-- Forms -->
        <div class="section">
            <h3>Add Provider Credentials</h3>
            <div class="form-group">
                <input type="text" id="cred-provider-id" placeholder="Provider ID">
                <input type="text" id="cred-key-name" placeholder="Key Name (e.g., api_key)">
                <input type="password" id="cred-key-value" placeholder="Key Value">
                <button class="btn-primary" onclick="addCredentials()">Add Credentials</button>
            </div>
        </div>
        
        <div class="section">
            <h3>Quick Actions</h3>
            <div class="form-group">
                <input type="text" id="test-provider-id" placeholder="Provider ID">
                <button class="btn-success" onclick="testProvider()">Test Provider</button>
            </div>
        </div>
    </div>
    
    <script>
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadProviders();
            loadAffiliates();
            loadPolicy();
            loadChannelAffiliates();
        });
        
        async function loadProviders() {
            try {
                const response = await fetch('/integrations/providers');
                const data = await response.json();
                const tbody = document.querySelector('#providers-table tbody');
                tbody.innerHTML = '';
                
                data.providers.forEach(provider => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><span class="status-light status-${provider.status_color}"></span></td>
                        <td>${provider.name}</td>
                        <td>${provider.category}</td>
                        <td>${provider.priority}</td>
                        <td>${provider.free_tier ? 'Yes' : 'No'}</td>
                        <td>
                            <button class="btn-${provider.enabled ? 'danger' : 'success'}" 
                                    onclick="toggleProvider('${provider.id}', ${!provider.enabled})">
                                ${provider.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button class="btn-secondary" onclick="testProvider('${provider.id}')">Test</button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Error loading providers:', error);
            }
        }
        
        async function loadAffiliates() {
            try {
                const response = await fetch('/integrations/affiliates');
                const data = await response.json();
                const tbody = document.querySelector('#affiliates-table tbody');
                tbody.innerHTML = '';
                
                data.affiliates.forEach(affiliate => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td><span class="status-light status-${affiliate.status_color}"></span></td>
                        <td>${affiliate.name}</td>
                        <td>${affiliate.vertical}</td>
                        <td>${affiliate.affiliate_id || 'Not set'}</td>
                        <td>
                            <button class="btn-${affiliate.enabled ? 'danger' : 'success'}" 
                                    onclick="toggleAffiliate('${affiliate.id}', ${!affiliate.enabled})">
                                ${affiliate.enabled ? 'Disable' : 'Enable'}
                            </button>
                        </td>
                    `;
                    tbody.appendChild(row);
                });
            } catch (error) {
                console.error('Error loading affiliates:', error);
            }
        }
        
        async function loadPolicy() {
            try {
                const response = await fetch('/integrations/policy');
                const policy = await response.json();
                
                document.getElementById('restricted-verticals').checked = policy.restricted_verticals_enabled;
                document.getElementById('gambling-enabled').checked = policy.gambling_enabled;
                document.getElementById('crypto-enabled').checked = policy.crypto_enabled;
                document.getElementById('adult-enabled').checked = policy.adult_enabled;
            } catch (error) {
                console.error('Error loading policy:', error);
            }
        }
        
        async function loadChannelAffiliates() {
            const channel = document.getElementById('channel-select').value;
            try {
                const response = await fetch(`/integrations/affiliates/suggestions/${channel}`);
                const data = await response.json();
                const container = document.getElementById('channel-affiliates');
                
                container.innerHTML = data.suggestions.map(affiliate => `
                    <div style="margin: 10px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
                        <span class="status-light status-${affiliate.status_color}"></span>
                        <strong>${affiliate.name}</strong> (${affiliate.vertical})
                        <span style="margin-left: 10px; color: ${affiliate.enabled ? 'green' : 'red'};">
                            ${affiliate.enabled ? 'Enabled' : 'Disabled'}
                        </span>
                    </div>
                `).join('');
            } catch (error) {
                console.error('Error loading channel affiliates:', error);
            }
        }
        
        async function toggleProvider(providerId, enabled) {
            try {
                const response = await fetch(`/integrations/providers/${providerId}/enable?enabled=${enabled}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadProviders();
                }
            } catch (error) {
                console.error('Error toggling provider:', error);
            }
        }
        
        async function toggleAffiliate(affiliateId, enabled) {
            try {
                const response = await fetch(`/integrations/affiliates/${affiliateId}/enable?enabled=${enabled}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadAffiliates();
                    loadChannelAffiliates();
                }
            } catch (error) {
                console.error('Error toggling affiliate:', error);
            }
        }
        
        async function rotateCategory(category) {
            // Find first enabled provider in category and rotate it
            try {
                const response = await fetch('/integrations/providers');
                const data = await response.json();
                const categoryProviders = data.providers.filter(p => p.category === category && p.enabled);
                
                if (categoryProviders.length > 0) {
                    const rotateResponse = await fetch(`/integrations/providers/${categoryProviders[0].id}/rotate`, {
                        method: 'POST'
                    });
                    if (rotateResponse.ok) {
                        const result = await rotateResponse.json();
                        alert(`Rotated from ${result.from} to ${result.provider_name}`);
                        loadProviders();
                    }
                } else {
                    alert(`No enabled providers in ${category} category`);
                }
            } catch (error) {
                console.error('Error rotating category:', error);
            }
        }
        
        async function addCredentials() {
            const providerId = document.getElementById('cred-provider-id').value;
            const keyName = document.getElementById('cred-key-name').value;
            const keyValue = document.getElementById('cred-key-value').value;
            
            if (!providerId || !keyName || !keyValue) {
                alert('Please fill all credential fields');
                return;
            }
            
            try {
                const response = await fetch(`/integrations/providers/${providerId}/credentials`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        provider_id: providerId,
                        key_name: keyName,
                        key_value: keyValue
                    })
                });
                
                if (response.ok) {
                    alert('Credentials added successfully');
                    document.getElementById('cred-provider-id').value = '';
                    document.getElementById('cred-key-name').value = '';
                    document.getElementById('cred-key-value').value = '';
                    loadProviders();
                }
            } catch (error) {
                console.error('Error adding credentials:', error);
            }
        }
        
        async function testProvider(providerId) {
            if (!providerId) {
                providerId = document.getElementById('test-provider-id').value;
            }
            
            if (!providerId) {
                alert('Please enter a provider ID');
                return;
            }
            
            try {
                const response = await fetch(`/integrations/test-call?provider_id=${providerId}`);
                const result = await response.json();
                
                if (result.status === 'healthy') {
                    alert(`✅ ${result.provider_name} is healthy (${result.response_time_ms}ms)`);
                } else {
                    alert(`❌ ${result.provider_name} is unhealthy: ${result.error}`);
                }
                
                loadProviders();
            } catch (error) {
                console.error('Error testing provider:', error);
                alert('Error testing provider');
            }
        }
        
        async function updatePolicy() {
            const policy = {
                restricted_verticals_enabled: document.getElementById('restricted-verticals').checked,
                gambling_enabled: document.getElementById('gambling-enabled').checked,
                crypto_enabled: document.getElementById('crypto-enabled').checked,
                adult_enabled: document.getElementById('adult-enabled').checked
            };
            
            try {
                const response = await fetch('/integrations/policy', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(policy)
                });
                
                if (response.ok) {
                    alert('Policy updated successfully');
                    loadAffiliates(); // Reload to update status colors
                    loadChannelAffiliates();
                }
            } catch (error) {
                console.error('Error updating policy:', error);
            }
        }
    </script>
</body>
</html>
    """