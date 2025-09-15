#!/usr/bin/env python3
""""""
Integrations Max Router - API integrations and affiliate management
""""""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

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
            with open(filepath, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}


def save_json(filepath: str, data: Any) -> bool:
    """Save data to JSON file"""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


# Models


class ProviderIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    category: str = Field(..., min_length=1, max_length=30)
    docs_url: str = Field(..., pattern=r"^https?://")
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
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "images_pixabay": {
        "name": "Pixabay",
        "category": "images",
        "docs_url": "https://pixabay.com/api/docs/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "news_guardian": {
        "name": "Guardian",
        "category": "news",
        "docs_url": "https://open-platform.theguardian.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "news_newsapi": {
        "name": "NewsAPI",
        "category": "news",
        "docs_url": "https://newsapi.org/docs",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "geo_openstreet": {
        "name": "OpenStreetMap",
        "category": "geo",
        "docs_url": "https://nominatim.org/",
        "enabled": True,
        "auto_disable": False,
        "priority": 1,
        "requires_key": False,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "pets_catapi": {
        "name": "TheCatAPI",
        "category": "pets",
        "docs_url": "https://thecatapi.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "pets_dogapi": {
        "name": "TheDogAPI",
        "category": "pets",
        "docs_url": "https://thedogapi.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "weather_openmeteo": {
        "name": "Open-Meteo",
        "category": "weather",
        "docs_url": "https://open-meteo.com/",
        "enabled": True,
        "auto_disable": False,
        "priority": 1,
        "requires_key": False,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "weather_openweather": {
        "name": "OpenWeather",
        "category": "weather",
        "docs_url": "https://openweathermap.org/api",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
    "social_instagram": {
        "name": "Instagram",
        "category": "social",
        "docs_url": "https://developers.facebook.com/docs/instagram-api/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": False,
        "oauth_required": True,
# BRACKET_SURGEON: disabled
#     },
    "social_tiktok": {
        "name": "TikTok",
        "category": "social",
        "docs_url": "https://developers.tiktok.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 2,
        "requires_key": True,
        "free_tier": False,
        "oauth_required": True,
# BRACKET_SURGEON: disabled
#     },
    "ai_openai": {
        "name": "OpenAI",
        "category": "ai",
        "docs_url": "https://platform.openai.com/docs",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": False,
# BRACKET_SURGEON: disabled
#     },
    "email_sendgrid": {
        "name": "SendGrid",
        "category": "email",
        "docs_url": "https://docs.sendgrid.com/",
        "enabled": False,
        "auto_disable": True,
        "priority": 1,
        "requires_key": True,
        "free_tier": True,
# BRACKET_SURGEON: disabled
#     },
# BRACKET_SURGEON: disabled
# }

# Default affiliates
DEFAULT_AFFILIATES = {
    "general_amazon": {
        "name": "Amazon Associates",
        "vertical": "general",
        "affiliate_id": "",
        "enabled": False,
# BRACKET_SURGEON: disabled
#     },
    "tech_bestbuy": {
        "name": "Best Buy",
        "vertical": "tech",
        "affiliate_id": "",
        "enabled": False,
# BRACKET_SURGEON: disabled
#     },
    "wellness_iherb": {
        "name": "iHerb",
        "vertical": "wellness",
        "affiliate_id": "",
        "enabled": False,
# BRACKET_SURGEON: disabled
#     },
    "ai_openai_partner": {
        "name": "OpenAI Partner",
        "vertical": "ai",
        "affiliate_id": "",
        "enabled": False,
# BRACKET_SURGEON: disabled
#     },
    "pets_chewy": {
        "name": "Chewy",
        "vertical": "pets",
        "affiliate_id": "",
        "enabled": False,
# BRACKET_SURGEON: disabled
#     },
# BRACKET_SURGEON: disabled
# }

# Default policy
DEFAULT_POLICY = {
    "restricted_verticals_enabled": False,
    "gambling_enabled": False,
    "crypto_enabled": False,
    "adult_enabled": False,
    "last_updated": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
# }

# Helper functions


def load_registry() -> Dict:
    """Load provider registry"""
    providers = load_json(PROVIDERS_FILE, DEFAULT_PROVIDERS)
    return providers


def load_affiliates() -> Dict:
    """Load affiliate registry"""
    affiliates = load_json(AFFILIATES_FILE, DEFAULT_AFFILIATES)
    return affiliates


def load_keys() -> Dict:
    """Load API keys"""
    return load_json(KEYS_FILE, {})


def load_metrics() -> Dict:
    """Load usage metrics"""
    return load_json(METRICS_FILE, {})


def load_policy() -> Dict:
    """Load content policy"""
    return load_json(POLICY_FILE, DEFAULT_POLICY)


def get_provider_status_color(provider_id: str, provider: Dict) -> str:
    """Get status color for provider"""
    if not provider.get("enabled", False):
        return "gray"

    keys = load_keys()
    if provider.get("requires_key", False) and provider_id not in keys:
        return "orange"

    metrics = load_metrics()
    provider_metrics = metrics.get(provider_id, {})

    if provider_metrics.get("error_count", 0) > 5:
        return "red"
    elif provider_metrics.get("success_rate", 100) < 80:
        return "yellow"

    return "green"


def get_affiliate_status_color(affiliate_id: str, affiliate: Dict) -> str:
    """Get status color for affiliate"""
    if not affiliate.get("enabled", False):
        return "gray"

    if not affiliate.get("affiliate_id", "").strip():
        return "purple"

    policy = load_policy()
    vertical = affiliate.get("vertical", "")

    if vertical == "restricted" and not policy.get("restricted_verticals_enabled", False):
        return "red"

    return "green"


# API Routes


@router.get("/providers/categories")
async def list_categories():
    """Get all provider categories"""
    providers = load_registry()
    categories = list(set(p.get("category", "unknown") for p in providers.values()))
    return {"categories": sorted(categories)}


@router.get("/providers")
async def list_providers():
    """Get all providers with status"""
    providers = load_registry()
    result = []

    for provider_id, provider in providers.items():
        result.append(
            {
                "id": provider_id,
                "name": provider.get("name", provider_id),
                "category": provider.get("category", "unknown"),
                "enabled": provider.get("enabled", False),
                "requires_key": provider.get("requires_key", False),
                "free_tier": provider.get("free_tier", False),
                "status_color": get_provider_status_color(provider_id, provider),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    return {"providers": result}


@router.post("/providers")
async def add_provider(provider: ProviderIn):
    """Add new provider"""
    providers = load_registry()
    provider_id = f"{provider.category}_{provider.name.lower().replace(' ', '_')}"

    if provider_id in providers:
        raise HTTPException(status_code=400, detail="Provider already exists")

    providers[provider_id] = {
        "name": provider.name,
        "category": provider.category,
        "docs_url": provider.docs_url,
        "enabled": provider.enabled,
        "auto_disable": provider.auto_disable,
        "priority": provider.priority,
        "requires_key": True,
        "free_tier": False,
# BRACKET_SURGEON: disabled
#     }

    save_json(PROVIDERS_FILE, providers)

    return {
        "message": "Provider added successfully",
        "provider_id": provider_id,
# BRACKET_SURGEON: disabled
#     }


@router.post("/providers/{provider_id}/enable")
async def enable_provider(provider_id: str, enabled: bool = True):
    """Enable/disable provider"""
    providers = load_registry()

    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")

    providers[provider_id]["enabled"] = enabled
    save_json(PROVIDERS_FILE, providers)

    return {"message": f"Provider {'enabled' if enabled else 'disabled'} successfully"}


@router.post("/providers/{provider_id}/credentials")
async def upsert_credentials(provider_id: str, credential: CredentialIn):
    """Add or update provider credentials"""
    providers = load_registry()

    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")

    keys = load_keys()
    keys[provider_id] = {
        "key_name": credential.key_name,
        "key_value": credential.key_value,
        "updated_at": datetime.now().isoformat(),
# BRACKET_SURGEON: disabled
#     }

    save_json(KEYS_FILE, keys)

    return {"message": "Credentials updated successfully"}


@router.get("/providers/active")
async def get_active_providers():
    """Get all active providers"""
    providers = load_registry()
    keys = load_keys()

    active = []
    for provider_id, provider in providers.items():
        if provider.get("enabled", False):
            has_key = provider_id in keys if provider.get("requires_key", False) else True

            active.append(
                {
                    "id": provider_id,
                    "name": provider.get("name", provider_id),
                    "category": provider.get("category", "unknown"),
                    "has_credentials": has_key,
                    "status_color": get_provider_status_color(provider_id, provider),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

    return {"active_providers": active}


@router.post("/providers/{provider_id}/rotate")
async def rotate_provider(provider_id: str):
    """Rotate provider to next priority"""
    providers = load_registry()

    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")

    category = providers[provider_id].get("category")
    category_providers = [
        (pid, p)
        for pid, p in providers.items()
        if p.get("category") == category and p.get("enabled", False)
# BRACKET_SURGEON: disabled
#     ]

    if len(category_providers) <= 1:
        return {"message": "No alternative providers available"}

    # Sort by priority
    category_providers.sort(key=lambda x: x[1].get("priority", 999))

    # Find current provider index
    current_index = next(
        (i for i, (pid, _) in enumerate(category_providers) if pid == provider_id), 0
# BRACKET_SURGEON: disabled
#     )

    # Get next provider
    next_index = (current_index + 1) % len(category_providers)
    next_provider_id, next_provider = category_providers[next_index]

    return {
        "message": "Rotated to next provider",
        "current_provider": provider_id,
        "next_provider": next_provider_id,
        "next_provider_name": next_provider.get("name", next_provider_id),
# BRACKET_SURGEON: disabled
#     }


@router.post("/providers/{provider_id}/report")
async def report_usage(provider_id: str, report: ReportIn):
    """Report provider usage metrics"""
    metrics = load_metrics()

    if provider_id not in metrics:
        metrics[provider_id] = {
            "total_calls": 0,
            "success_count": 0,
            "error_count": 0,
            "avg_response_time": 0,
            "last_used": None,
# BRACKET_SURGEON: disabled
#         }

    provider_metrics = metrics[provider_id]
    provider_metrics["total_calls"] += 1
    provider_metrics["last_used"] = datetime.now().isoformat()

    if report.success:
        provider_metrics["success_count"] += 1
    else:
        provider_metrics["error_count"] += 1

    if report.response_time_ms:
        current_avg = provider_metrics.get("avg_response_time", 0)
        total_calls = provider_metrics["total_calls"]
        provider_metrics["avg_response_time"] = (
            current_avg * (total_calls - 1) + report.response_time_ms
# BRACKET_SURGEON: disabled
#         ) / total_calls

    # Calculate success rate
    provider_metrics["success_rate"] = (
        provider_metrics["success_count"] / provider_metrics["total_calls"] * 100
# BRACKET_SURGEON: disabled
#     )

    save_json(METRICS_FILE, metrics)

    # Auto-disable if error rate is too high
    if provider_metrics["error_count"] >= 10 and provider_metrics["success_rate"] < 50:
        providers = load_registry()
        if provider_id in providers and providers[provider_id].get("auto_disable", False):
            providers[provider_id]["enabled"] = False
            save_json(PROVIDERS_FILE, providers)

    return {"message": "Usage reported successfully"}


@router.get("/test-call")
async def test_call(provider_id: str):
    """Test API call to provider"""
    providers = load_registry()

    if provider_id not in providers:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider = providers[provider_id]

    if not provider.get("enabled", False):
        raise HTTPException(status_code=400, detail="Provider is disabled")

    # Simple test based on category
    category = provider.get("category", "unknown")

    try:
        if category == "weather":
            # Test weather API
            if provider_id == "weather_openmeteo":
                url = "https://api.open-meteo.com/v1/forecast?latitude=40.7128&longitude=-74.0060&current_weather=true"
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=10)
                    response.raise_for_status()
                    return {"status": "success", "data": response.json()}

        elif category == "geo":
            # Test geo API
            if provider_id == "geo_openstreet":
                url = "https://nominatim.openstreetmap.org/search?q=New+York&format=json&limit=1"
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=10)
                    response.raise_for_status()
                    return {"status": "success", "data": response.json()}

        return {"status": "success", "message": "Test call completed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# Affiliate routes


@router.get("/affiliates/verticals")
async def list_verticals():
    """Get all affiliate verticals"""
    affiliates = load_affiliates()
    verticals = list(set(a.get("vertical", "unknown") for a in affiliates.values()))
    return {"verticals": sorted(verticals)}


@router.get("/affiliates")
async def list_affiliates():
    """Get all affiliates with status"""
    affiliates = load_affiliates()
    result = []

    for affiliate_id, affiliate in affiliates.items():
        result.append(
            {
                "id": affiliate_id,
                "name": affiliate.get("name", affiliate_id),
                "vertical": affiliate.get("vertical", "unknown"),
                "enabled": affiliate.get("enabled", False),
                "has_affiliate_id": bool(affiliate.get("affiliate_id", "").strip()),
                "status_color": get_affiliate_status_color(affiliate_id, affiliate),
# BRACKET_SURGEON: disabled
#             }
# BRACKET_SURGEON: disabled
#         )

    return {"affiliates": result}


@router.post("/affiliates")
async def add_affiliate(affiliate: AffiliateIn):
    """Add new affiliate"""
    affiliates = load_affiliates()
    affiliate_key = f"{affiliate.vertical}_{affiliate.name.lower().replace(' ', '_')}"

    if affiliate_key in affiliates:
        raise HTTPException(status_code=400, detail="Affiliate already exists")

    affiliates[affiliate_key] = {
        "name": affiliate.name,
        "vertical": affiliate.vertical,
        "affiliate_id": affiliate.affiliate_id,
        "enabled": affiliate.enabled,
# BRACKET_SURGEON: disabled
#     }

    save_json(AFFILIATES_FILE, affiliates)

    return {
        "message": "Affiliate added successfully",
        "affiliate_key": affiliate_key,
# BRACKET_SURGEON: disabled
#     }


@router.post("/affiliates/{affiliate_key}/enable")
async def enable_affiliate(affiliate_key: str, enabled: bool = True):
    """Enable/disable affiliate"""
    affiliates = load_affiliates()

    if affiliate_key not in affiliates:
        raise HTTPException(status_code=404, detail="Affiliate not found")

    affiliates[affiliate_key]["enabled"] = enabled
    save_json(AFFILIATES_FILE, affiliates)

    return {"message": f"Affiliate {'enabled' if enabled else 'disabled'} successfully"}


@router.post("/affiliates/{affiliate_key}/credentials")
async def upsert_affiliate_id(affiliate_key: str, affiliate_id: str):
    """Update affiliate ID"""
    affiliates = load_affiliates()

    if affiliate_key not in affiliates:
        raise HTTPException(status_code=404, detail="Affiliate not found")

    affiliates[affiliate_key]["affiliate_id"] = affiliate_id
    affiliates[affiliate_key]["updated_at"] = datetime.now().isoformat()

    save_json(AFFILIATES_FILE, affiliates)

    return {"message": "Affiliate ID updated successfully"}


@router.get("/policy")
async def get_policy():
    """Get content policy"""
    return load_policy()


@router.post("/policy")
async def set_policy(policy_updates: Dict[str, Any]):
    """Update content policy"""
    policy = load_policy()

    # Update allowed fields
    allowed_fields = [
        "restricted_verticals_enabled",
        "gambling_enabled",
        "crypto_enabled",
        "adult_enabled",
# BRACKET_SURGEON: disabled
#     ]

    for field in allowed_fields:
        if field in policy_updates:
            policy[field] = policy_updates[field]

    policy["last_updated"] = datetime.now().isoformat()

    save_json(POLICY_FILE, policy)

    return {"message": "Policy updated successfully", "policy": policy}


# Channel mapping for suggestions
CHANNEL_MAP = {
    "tech": ["tech_bestbuy", "general_amazon"],
    "wellness": ["wellness_iherb", "general_amazon"],
    "pets": ["pets_chewy", "general_amazon"],
    "ai": ["ai_openai_partner", "tech_bestbuy"],
    "general": ["general_amazon"],
# BRACKET_SURGEON: disabled
# }


@router.get("/affiliates/suggestions/{channel}")
async def get_top_affiliates(channel: str):
    """Get top affiliate suggestions for channel"""
    affiliates = load_affiliates()
    policy = load_policy()

    suggested_keys = CHANNEL_MAP.get(channel, ["general_amazon"])
    suggestions = []

    for key in suggested_keys:
        if key in affiliates:
            affiliate = affiliates[key]
            vertical = affiliate.get("vertical", "")

            # Check policy restrictions
            if vertical == "restricted" and not policy.get("restricted_verticals_enabled", False):
                continue

            suggestions.append(
                {
                    "id": key,
                    "name": affiliate.get("name", key),
                    "vertical": vertical,
                    "enabled": affiliate.get("enabled", False),
                    "has_affiliate_id": bool(affiliate.get("affiliate_id", "").strip()),
                    "status_color": get_affiliate_status_color(key, affiliate),
# BRACKET_SURGEON: disabled
#                 }
# BRACKET_SURGEON: disabled
#             )

    return {"suggestions": suggestions}


@router.get("/admin", response_class=HTMLResponse)
async def admin_ui():
    """Admin interface for integrations"""
    return """"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Integrations Admin</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
            .provider, .affiliate { margin: 10px 0; padding: 10px; background: #f5f5f5; }
            .status-green { color: green; }
            .status-yellow { color: orange; }
            .status-red { color: red; }
            .status-gray { color: gray; }
            .status-purple { color: purple; }
            button { margin: 5px; padding: 5px 10px; }
        </style>
    </head>
    <body>
        <h1>Integrations Admin Panel</h1>

        <div class="section">
            <h2>API Providers</h2>
            <div id="providers"></div>
        </div>

        <div class="section">
            <h2>Affiliate Programs</h2>
            <div id="affiliates"></div>
        </div>

        <div class="section">
            <h2>Content Policy</h2>
            <div id="policy"></div>
        </div>

        <script>
            async function loadProviders() {
                const response = await fetch('/integrations/providers');
                const data = await response.json();
                const container = document.getElementById('providers');

                container.innerHTML = data.providers.map(p => `
                    <div class="provider">
                        <strong>${p.name}</strong> (${p.category})
                        <span class="status-${p.status_color}">●</span>
                        ${p.enabled ? 'ENABLED' : 'DISABLED'}
                        ${p.requires_key ? (p.status_color === 'orange' ? ' - NEEDS KEY' : ' - HAS KEY') : ''}
                        <button onclick="toggleProvider('${p.id}', ${!p.enabled})">
                            ${p.enabled ? 'Disable' : 'Enable'}
                        </button>
                        <button onclick="testProvider('${p.id}')">Test</button>
                    </div>
                `).join('');
# BRACKET_SURGEON: disabled
#             }

            async function loadAffiliates() {
                const response = await fetch('/integrations/affiliates');
                const data = await response.json();
                const container = document.getElementById('affiliates');

                container.innerHTML = data.affiliates.map(a => `
                    <div class="affiliate">
                        <strong>${a.name}</strong> (${a.vertical})
                        <span class="status-${a.status_color}">●</span>
                        ${a.enabled ? 'ENABLED' : 'DISABLED'}
                        ${a.has_affiliate_id ? ' - HAS ID' : ' - NEEDS ID'}
                        <button onclick="toggleAffiliate('${a.id}', ${!a.enabled})">
                            ${a.enabled ? 'Disable' : 'Enable'}
                        </button>
                    </div>
                `).join('');
# BRACKET_SURGEON: disabled
#             }

            async function loadPolicy() {
                const response = await fetch('/integrations/policy');
                const data = await response.json();
                const container = document.getElementById('policy');

                container.innerHTML = `
                    <label>
                        <input type="checkbox" ${data.restricted_verticals_enabled ? 'checked' : ''}
                               onchange="updatePolicy('restricted_verticals_enabled', this.checked)">
                        Enable Restricted Verticals
                    </label><br>
                    <label>
                        <input type="checkbox" ${data.gambling_enabled ? 'checked' : ''}
                               onchange="updatePolicy('gambling_enabled', this.checked)">
                        Enable Gambling
                    </label><br>
                    <label>
                        <input type="checkbox" ${data.crypto_enabled ? 'checked' : ''}
                               onchange="updatePolicy('crypto_enabled', this.checked)">
                        Enable Crypto
                    </label><br>
                    <label>
                        <input type="checkbox" ${data.adult_enabled ? 'checked' : ''}
                               onchange="updatePolicy('adult_enabled', this.checked)">
                        Enable Adult Content
                    </label><br>
                    <small>Last updated: ${data.last_updated}</small>
                `;
# BRACKET_SURGEON: disabled
#             }

            async function toggleProvider(id, enabled) {
                await fetch(`/integrations/providers/${id}/enable`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({enabled})
# BRACKET_SURGEON: disabled
#                 });
                loadProviders();
# BRACKET_SURGEON: disabled
#             }

            async function toggleAffiliate(id, enabled) {
                await fetch(`/integrations/affiliates/${id}/enable`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({enabled})
# BRACKET_SURGEON: disabled
#                 });
                loadAffiliates();
# BRACKET_SURGEON: disabled
#             }

            async function testProvider(id) {
                const response = await fetch(`/integrations/test-call?provider_id=${id}`);
                const data = await response.json();
                alert(`Test result: ${data.status}\n${data.message || JSON.stringify(data.data)}`);
# BRACKET_SURGEON: disabled
#             }

            async function updatePolicy(field, value) {
                await fetch('/integrations/policy', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({[field]: value})
# BRACKET_SURGEON: disabled
#                 });
                loadPolicy();
# BRACKET_SURGEON: disabled
#             }

            // Load initial data
            loadProviders();
            loadAffiliates();
            loadPolicy();
        </script>
    </body>
    </html>
    """"""