# integrations_hub.py

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from utils.common import get_secret as shared_get_secret
from utils.common import http_with_fallback as shared_http_with_fallback

from content_sources import router as content_router


def _affiliate_status(entry: Dict[str, str]) -> str:
    # green if ID present \
    and enabled; purple if missing ID; red if enabled but we detect problems later
    has_id = entry.get("id_env") and get_secret(entry["id_env"])
    if not has_id:
        return "purple"
    return "green" if entry.get("enabled") else "purple"


class AffiliatePatch(BaseModel):
    enabled: Optional[bool] = None
    id_value: Optional[str] = None

# --- Storage paths
CONFIG_DIR = Path("config")
CONFIG_DIR.mkdir(exist_ok = True)
PROVIDERS_PATH = CONFIG_DIR / "integrations.providers.json"
AFFILIATES_PATH = CONFIG_DIR / "integrations.affiliates.json"

# --- Status colors per user spec
# Status constants removed - now using string literals directly

@dataclass


class RateLimit:
    limit: Optional[int] = None
    remaining: Optional[int] = None
    reset_epoch: Optional[int] = None

@dataclass


class Provider:
    id: str
    kind: str
    name: str
    enabled: bool
    requires_key: bool
    key_env: Optional[str]
    base_url: str
    docs_url: str
    health: Dict[str, Any] = field(default_factory = dict)
    usage: Dict[str, Any] = field(default_factory = dict)
    status: str = "purple"  # default "needs key" until proven
    last_error: Optional[str] = None
    required_envs: List[str] = field(default_factory = list)  # NEW
    health_url: Optional[str] = None
    last_ok: Optional[str] = None


    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProviderUpdate(BaseModel):
    enabled: Optional[bool] = None
    key: Optional[str] = None  # plaintext key (stored via secret_store if available)
    status: Optional[str] = None


class NewProvider(BaseModel):
    id: str
    kind: str
    name: str
    enabled: bool = False
    requires_key: bool = True
    key_env: Optional[str] = None
    base_url: str
    docs_url: str
    signup_url: str = ""
    required_envs: List[str] = []

# --- Optional secret store hook (non - fatal if absent)


def set_secret(name: str, value: str) -> None:
    """
    Stores the secret using your project's secret_store.py if present.
    Fallback: writes to config/.secrets.json (dev only).
    """
    try:
        # pragma: no cover

        from secret_store import SecretStore  # type: ignore

        SecretStore().set(name, value)
        return
    except Exception:
        pass

    # fallback file (dev)
    secrets_path = CONFIG_DIR / ".secrets.json"
    secrets = {}
    if secrets_path.exists():
        try:
            secrets = json.loads(secrets_path.read_text())
        except Exception:
            secrets = {}
    secrets[name] = value
    secrets_path.write_text(json.dumps(secrets, indent = 2))

# Use shared get_secret function from utils.common
get_secret = shared_get_secret


def _now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

# Track common rate - limit headers


def _update_rl_from_headers(p: Provider, headers: Dict[str, str]) -> None:
    h = {k.lower(): v for k, v in headers.items()}
    try:
        if "x - ratelimit - remaining" in h:
            p.rl.remaining = int(h["x - ratelimit - remaining"])
        if "x - ratelimit - limit" in h:
            p.rl.limit = int(h["x - ratelimit - limit"])
        # try several common spellings
        rt = (
            h.get("x - ratelimit - reset")
            or h.get("ratelimit - reset")
            or h.get("x - rate - limit - reset")
        )
        if rt:
            p.rl.reset_epoch = int(float(rt))
    except Exception:
        pass


def _load_json(path: Path, default: Any) -> Any:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            return default
    return default


def _save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent = 2))


def hydrate_providers() -> Dict[str, Provider]:
    raw = _load_json(PROVIDERS_PATH, default={"providers": []})
    providers: Dict[str, Provider] = {}
    for p in raw.get("providers", []):
        provider = Provider(
            id = p["id"],
                kind = p.get("kind",
    p.get("category", "misc")),  # fallback for migration
            name = p["name"],
                enabled = p.get("enabled", False),
                requires_key = p.get(
                "requires_key", p.get("needs_key", True)
            ),  # fallback for migration
            key_env = p.get("key_env"),
                base_url = p.get("base_url", ""),
                docs_url = p["docs_url"],
                health = p.get("health", {}),
                usage = p.get("usage", {}),
                status = p.get("status", "purple"),
                last_error = p.get("last_error"),
                required_envs = p.get("required_envs", []),
                )
        if provider.requires_key and not get_secret(provider.key_env or ""):
            provider.status = "purple"
        providers[provider.id] = provider
    return providers


def persist_providers(providers: Dict[str, Provider]) -> None:
    data = {"providers": [p.to_dict() for p in providers.values()]}
    _save_json(PROVIDERS_PATH, data)

# --- Curated starter catalog (free - first; paid OFF by default)
DEFAULT_CATALOG: List[Dict[str, Any]] = [
    # News & Knowledge
    {
        "id": "guardian",
            "name": "The Guardian Open Platform",
            "category": "news",
            "docs_url": "https://open - platform.theguardian.com / documentation/",
            "signup_url": "https://bonobo.capi.gutools.co.uk / register / developer",
            "key_env": "GUARDIAN_API_KEY",
            },
        {
        "id": "gdelt",
            "name": "GDELT Project",
            "category": "news",
            "docs_url": "https://blog.gdeltproject.org / gdelt - 2 - 0 - our - global - world - in - realtime/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "wikimedia",
            "name": "Wikipedia / MediaWiki API",
            "category": "knowledge",
            "docs_url": "https://www.mediawiki.org / wiki / API:Main_page",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "hackernews",
            "name": "Hacker News (Firebase API)",
            "category": "news",
            "docs_url": "https://github.com / HackerNews / API",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "newsapi",
            "name": "NewsAPI",
            "category": "news",
            "docs_url": "https://newsapi.org / docs",
            "signup_url": "https://newsapi.org / register",
            "key_env": "NEWSAPI_KEY",
            },
        {
        "id": "mediastack",
            "name": "Mediastack",
            "category": "news",
            "docs_url": "https://mediastack.com / documentation",
            "signup_url": "https://mediastack.com / signup",
            "key_env": "MEDIASTACK_KEY",
            },
        # Images & Video
    {
        "id": "unsplash",
            "name": "Unsplash",
            "category": "images",
            "docs_url": "https://unsplash.com / documentation",
            "signup_url": "https://unsplash.com / developers",
            "key_env": "UNSPLASH_KEY",
            "enabled": True,
            },
        {
        "id": "pexels",
            "name": "Pexels",
            "category": "images",
            "docs_url": "https://www.pexels.com / api / documentation/",
            "signup_url": "https://www.pexels.com / api / new/",
            "key_env": "PEXELS_KEY",
            "enabled": True,
            },
        {
        "id": "pixabay",
            "name": "Pixabay",
            "category": "images",
            "docs_url": "https://pixabay.com / api / docs/",
            "signup_url": "https://pixabay.com / api / docs/",
            "key_env": "PIXABAY_KEY",
            "enabled": True,
            },
        {
        "id": "openverse",
            "name": "Openverse (CC Search)",
            "category": "images",
            "docs_url": "https://api.openverse.org/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "lorempicsum",
            "name": "Lorem Picsum (no key)",
            "category": "images",
            "docs_url": "https://picsum.photos/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        # Social & Video Platforms
    {
        "id": "youtube",
            "name": "YouTube Data API v3",
            "category": "social",
            "docs_url": "https://developers.google.com / youtube / v3",
            "signup_url": "https://console.cloud.google.com / apis / library / youtube.googleapis.com",
            "key_env": "YOUTUBE_API_KEY",
            },
        {
        "id": "reddit",
            "name": "Reddit API",
            "category": "social",
            "docs_url": "https://www.reddit.com / dev / api/",
            "signup_url": "https://www.reddit.com / prefs / apps",
            "key_env": "REDDIT_CLIENT_ID",
            },
        # Weather & Geo
    {
        "id": "openweather",
            "name": "OpenWeatherMap",
            "category": "weather",
            "docs_url": "https://openweathermap.org / api",
            "signup_url": "https://home.openweathermap.org / users / sign_up",
            "key_env": "OPENWEATHER_KEY",
            "enabled": True,
            },
        {
        "id": "weatherapi",
            "name": "WeatherAPI.com",
            "category": "weather",
            "docs_url": "https://www.weatherapi.com / docs/",
            "signup_url": "https://www.weatherapi.com / signup.aspx",
            "key_env": "WEATHERAPI_KEY",
            },
        {
        "id": "openmeteo",
            "name": "Open - Meteo (no key)",
            "category": "weather",
            "docs_url": "https://open - meteo.com / en / docs",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "opencage",
            "name": "OpenCage Geocoding",
            "category": "geocoding",
            "docs_url": "https://opencagedata.com / api",
            "signup_url": "https://opencagedata.com / users / sign_up",
            "key_env": "OPENCAGE_KEY",
            },
        {
        "id": "nominatim",
            "name": "OpenStreetMap Nominatim",
            "category": "geocoding",
            "docs_url": "https://nominatim.org / release - docs / latest / api / Overview/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "openmeteo_geo",
            "name": "Open - Meteo Geocoding (no key)",
            "category": "geocoding",
            "docs_url": "https://open - meteo.com / en / docs / geocoding - api",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "geojs",
            "name": "GeoJS IP (no key)",
            "category": "geocoding",
            "docs_url": "https://www.geojs.io / docs/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        # Finance
    {
        "id": "coingecko",
            "name": "CoinGecko",
            "category": "finance",
            "docs_url": "https://www.coingecko.com / en / api",
            "signup_url": "https://www.coingecko.com / api",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        {
        "id": "alphavantage",
            "name": "Alpha Vantage",
            "category": "finance",
            "docs_url": "https://www.alphavantage.co / documentation/",
            "signup_url": "https://www.alphavantage.co / support/#api - key",
            "key_env": "ALPHAVANTAGE_KEY",
            },
        {
        "id": "finnhub",
            "name": "Finnhub",
            "category": "finance",
            "docs_url": "https://finnhub.io / docs / api",
            "signup_url": "https://finnhub.io / register",
            "key_env": "FINNHUB_KEY",
            },
        {
        "id": "coinapi",
            "name": "CoinAPI (freemium)",
            "category": "finance",
            "docs_url": "https://docs.coinapi.io/",
            "signup_url": "https://www.coinapi.io / pricing",
            "key_env": "COINAPI_KEY",
            },
        {
        "id": "coindesk",
            "name": "CoinDesk (no key)",
            "category": "finance",
            "docs_url": "https://www.coindesk.com / coindesk - api/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        # AI / ML (OFF by default; keep paid off until you're ready)
    {
        "id": "hf_inference",
            "name": "Hugging Face Inference API",
            "category": "ai",
            "docs_url": "https://huggingface.co / docs / api - inference / index",
            "signup_url": "https://huggingface.co / join",
            "key_env": "HF_API_TOKEN",
            },
        {
        "id": "openai",
            "name": "OpenAI (off by default)",
            "category": "ai",
            "docs_url": "https://platform.openai.com / docs / overview",
            "signup_url": "https://platform.openai.com / signup",
            "key_env": "OPENAI_API_KEY",
            "enabled": False,
            },
        {
        "id": "google_gemini",
            "name": "Google AI Studio (off by default)",
            "category": "ai",
            "docs_url": "https://ai.google.dev / gemini - api",
            "signup_url": "https://aistudio.google.com/",
            "key_env": "GOOGLE_API_KEY",
            "enabled": False,
            },
        {
        "id": "anthropic",
            "name": "Anthropic (off by default)",
            "category": "ai",
            "docs_url": "https://docs.anthropic.com / claude / reference / getting - started - with - the - api",
            "signup_url": "https://console.anthropic.com/",
            "key_env": "ANTHROPIC_API_KEY",
            "enabled": False,
            },
        # News / Politics
    {
        "id": "newscatcher",
            "name": "Newscatcher (freemium)",
            "category": "news",
            "docs_url": "https://docs.newscatcherapi.com/",
            "signup_url": "https://newscatcherapi.com / signup",
            "key_env": "NEWSCATCHER_KEY",
            },
        {
        "id": "newsdata",
            "name": "Newsdata.io (freemium)",
            "category": "news",
            "docs_url": "https://newsdata.io / documentation",
            "signup_url": "https://newsdata.io / register",
            "key_env": "NEWSDATA_KEY",
            },
        {
        "id": "currents",
            "name": "Currents API (freemium)",
            "category": "news",
            "docs_url": "https://currentsapi.services / en / docs",
            "signup_url": "https://currentsapi.services / en / register",
            "key_env": "CURRENTS_KEY",
            },
        {
        "id": "gnews",
            "name": "GNews (freemium)",
            "category": "news",
            "docs_url": "https://gnews.io / docs / v4",
            "signup_url": "https://gnews.io/",
            "key_env": "GNEWS_KEY",
            },
        {
        "id": "arxiv",
            "name": "arXiv (no key)",
            "category": "knowledge",
            "docs_url": "https://info.arxiv.org / help / api / index.html",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        # Tech / Dev
    {
        "id": "github",
            "name": "GitHub REST (no key for public)",
            "category": "tech",
            "docs_url": "https://docs.github.com / en / rest",
            "signup_url": "https://github.com / settings / tokens",
            "key_env": "GITHUB_TOKEN",
            "enabled": True,
            "requires_key": False,
            },
        {
        "id": "producthunt",
            "name": "Product Hunt (freemium)",
            "category": "tech",
            "docs_url": "https://api.producthunt.com / v2 / docs",
            "signup_url": "https://www.producthunt.com / v2 / oauth / applications",
            "key_env": "PRODUCTHUNT_TOKEN",
            },
        # Wellness / Food / Health
    {
        "id": "usda_fdc",
            "name": "USDA FoodData Central (free)",
            "category": "wellness",
            "docs_url": "https://fdc.nal.usda.gov / api - guide.html",
            "signup_url": "https://api.nal.usda.gov/",
            "key_env": "USDA_FDC_KEY",
            },
        {
        "id": "openfda",
            "name": "OpenFDA (no key)",
            "category": "wellness",
            "docs_url": "https://open.fda.gov / apis/",
            "signup_url": "",
            "key_env": None,
            "requires_key": False,
            "enabled": True,
            },
        # Pets
    {
        "id": "petfinder",
            "name": "Petfinder API",
            "category": "pets",
            "docs_url": "https://www.petfinder.com / developers / v2 / docs/",
            "signup_url": "https://www.petfinder.com / developers/",
            "key_env": "PETFINDER_KEY",
            "required_envs": ["PETFINDER_KEY", "PETFINDER_SECRET"],
            "base_url": "https://api.petfinder.com",
            "enabled": False,
            },
        {
        "id": "thedogapi",
            "name": "TheDogAPI",
            "category": "pets",
            "docs_url": "https://thedogapi.com/",
            "signup_url": "https://thedogapi.com / signup",
            "key_env": "DOG_API_KEY",
            "base_url": "https://api.thedogapi.com",
            "enabled": True,
            "needs_key": False,
            },
        {
        "id": "thecatapi",
            "name": "TheCatAPI",
            "category": "pets",
            "docs_url": "https://thecatapi.com/",
            "signup_url": "https://thecatapi.com / signup",
            "key_env": "CAT_API_KEY",
            "base_url": "https://api.thecatapi.com",
            "enabled": True,
            "needs_key": False,
            },
        # Education / AI Research
    {
        "id": "paperswithcode",
            "name": "Papers with Code (no key)",
            "category": "knowledge",
            "docs_url": "https://paperswithcode.com / about",
            "signup_url": "",
            "key_env": None,
            "needs_key": False,
            "enabled": True,
            },
        {
        "id": "metaculus",
            "name": "Metaculus API (no key)",
            "category": "knowledge",
            "docs_url": "https://www.metaculus.com / api/",
            "signup_url": "",
            "key_env": None,
            "needs_key": False,
            "enabled": True,
            },
]


def ensure_seed_catalog(providers: Dict[str, Provider]) -> Dict[str, Provider]:
    changed = False
    for item in DEFAULT_CATALOG:
        if item["id"] not in providers:
            p = Provider(
                id = item["id"],
                    kind = item.get("kind", item.get("category", "misc")),
                    name = item["name"],
                    enabled = item.get("enabled", False),
                    requires_key = item.get("requires_key",
    item.get("needs_key",
    True)),
                    key_env = item.get("key_env"),
                    base_url = item.get("base_url", ""),
                    docs_url = item["docs_url"],
                    health = item.get("health", {}),
                    usage = item.get("usage", {}),
                    status=(
                    "green"
                    if not item.get("requires_key", item.get("needs_key", True))
                    else "purple"
                ),
                    last_error = item.get("last_error"),
                    required_envs = item.get("required_envs", []),
                    )
            if p.requires_key and p.key_env and get_secret(p.key_env):
                p.status = "green"
            providers[p.id] = p
            changed = True
    if changed:
        persist_providers(providers)
    return providers

# --- Router
router = APIRouter(prefix="/integrations", tags=["integrations"])
_state = {"providers": ensure_seed_catalog(hydrate_providers())}

@router.get("/providers")


async def list_providers():
    return {"providers": [p.to_dict() for p in _state["providers"].values()]}

@router.post("/providers", status_code = 201)


async def add_provider(new: NewProvider):
    if new.id in _state["providers"]:
        raise HTTPException(409, "Provider id already exists")
    p = Provider(
        id = new.id,
            name = new.name,
            category = new.category,
            docs_url = new.docs_url,
            signup_url = new.signup_url,
            key_env = new.key_env,
            requires_key = new.requires_key,
            enabled = new.enabled,
            status="purple" if new.requires_key else "green",
            health_url = new.health_url,
            )
    if p.requires_key and p.key_env and get_secret(p.key_env):
        p.status = "green"
    _state["providers"][p.id] = p
    persist_providers(_state["providers"])
    return {"ok": True, "provider": p.to_dict()}


async def update_provider_status(p: Provider) -> Provider:
    """Update provider status based on health check"""
    # Enforce required envs (supports multi - key providers like Petfinder)
    if p.required_envs:
        missing = [env for env in p.required_envs if not get_secret(env)]
        if missing:
            p.status, p.last_error = "purple", f"missing keys: {', '.join(missing)}"
            return p

    # Single - key mode (legacy providers)
    if p.requires_key and not p.required_envs and not get_secret(p.key_env or ""):
        p.status, p.last_error = "purple", "missing key"
        return p

    if not p.enabled:
        p.status, p.last_error = "purple", "disabled"
        return p

    try:
        method = p.health.get("method", "GET").upper()
        path = p.health.get("path", "/")

        # Build headers
        headers = {}
        # TheDogAPI / TheCatAPI optional key
        if p.health.get("auth", {}).get("header") and p.key_env:
            token = get_secret(p.key_env) or ""
            if token:
                headers[p.health["auth"]["header"]] = token

        # Generic Bearer header (e.g., Calendly)
        if p.health.get("auth", {}).get("header") == "Authorization" and p.key_env:
            token = get_secret(p.key_env) or ""
            if token:
                headers["Authorization"] = f"Bearer {token}"

        url = p.base_url.rstrip("/") + path

        async with httpx.AsyncClient(timeout = 10) as client:
            # Petfinder OAuth flow for health check
            if p.health.get("auth", {}).get("type") == "petfinder_oauth":
                pf_key = get_secret("PETFINDER_KEY") or ""
                pf_secret = get_secret("PETFINDER_SECRET") or ""
                if not pf_key or not pf_secret:
                    p.status, p.last_error = "purple", "missing Petfinder credentials"
                    return p
                token_resp = await client.post(
                    f"{p.base_url}/v2 / oauth2 / token",
                        data={
                        "grant_type": "client_credentials",
                            "client_id": pf_key,
                            "client_secret": pf_secret,
                            },
                        headers={"Content - Type": "application / x - www - form - urlencoded"},
                        )
                if token_resp.status_code >= 400:
                    p.status, p.last_error = "red", f"oauth {token_resp.status_code}"
                    return p
                bearer = token_resp.json().get("access_token")
                if not bearer:
                    p.status, p.last_error = "red", "oauth: no token"
                    return p
                headers["Authorization"] = f"Bearer {bearer}"

            resp = await client.request(method, url, headers = headers)
            if resp.status_code == 429 and p.usage.get("rotate_on_429"):
                p.status, p.last_error = "red", "rate limited (429)"
                return p
            if resp.status_code >= 400:
                p.status, p.last_error = "red", f"http {resp.status_code}"
                return p

            ok_paths = p.health.get("ok_json_paths") or []
            if ok_paths:
                try:
                    data = resp.json()
                except Exception:
                    p.status, p.last_error = "red", "invalid json"
                    return p
                ok = False
                for path_expr in ok_paths:
                    try:
                        cur = data
                        for part in path_expr.split("."):
                            if part.isdigit():
                                cur = cur[int(part)]
                            else:
                                cur = cur.get(part)
                        if cur is not None:
                            ok = True
                            break
                    except Exception:
                        continue
                p.status = "green" if ok else "red"
                p.last_error = None if ok else "missing ok field(s)"
            else:
                p.status, p.last_error = "green", None

            return p

    except Exception as e:
        p.status, p.last_error = "red", str(e)
        return p

@router.patch("/providers/{pid}")


async def update_provider(
    pid: str,
        patch: ProviderUpdate = Body(
        ..., description="Provider update data with validation metadata"
    ),
):
    p = _state["providers"].get(pid)
    if not p:
        raise HTTPException(404, "Unknown provider")
    if patch.enabled is not None:
        p.enabled = patch.enabled
    if patch.key is not None:
        if not p.key_env:
            raise HTTPException(400, "This provider does not accept a key")
        set_secret(p.key_env, patch.key)
    if patch.status is not None:
        if patch.status not in {"green", "purple", "red"}:
            raise HTTPException(400, "Invalid status")
        p.status = patch.status

    # Update status based on current state
    p = await update_provider_status(p)

    persist_providers(_state["providers"])
    return {"ok": True, "provider": p.to_dict()}

@router.post("/providers/{pid}/test")


async def test_provider(pid: str):
    p = _state["providers"].get(pid)
    if not p:
        raise HTTPException(404, "Unknown provider")
    url = p.health_url or p.docs_url
    headers = {}
    if p.key_env:
        key = get_secret(p.key_env)
        if key:
            if p.id in ("unsplash", "pexels", "pixabay"):
                headers["Authorization"] = f"Bearer {key}" if p.id != "pixabay" else ""
            elif p.id == "openweather":
                pass
            elif p.id == "youtube":
                pass
            else:
                headers["Authorization"] = f"Bearer {key}"

    try:
        async with httpx.AsyncClient(timeout = 10) as client:
            resp = await client.get(url, headers = headers, params = None)
        ok = 200 <= resp.status_code < 300
        p.status = "green" if ok else "red"
        if ok:
            p.last_ok = _now_iso()
            p.last_error = None
        else:
            p.last_error = f"{resp.status_code} {resp.text[:160]}"
        persist_providers(_state["providers"])
        return {"ok": ok, "status": p.status, "error": p.last_error}
    except Exception as e:
        p.status = "red"
        p.last_error = str(e)[:160]
        persist_providers(_state["providers"])
        return {"ok": False, "status": "red", "error": str(e)}

@router.post("/providers/{pid}/configure")


async def configure_provider(
    pid: str,
        config_data: dict = Body(
        ...,
            description="Advanced provider configuration",
            example={
            "health_check": {
                "method": "GET",
                    "path": "/health",
                    "headers": {"User - Agent": "IntegrationsHub / 1.0"},
                    },
                "rate_limits": {"requests_per_minute": 60, "burst_limit": 10},
                "auth_config": {"type": "bearer", "header_name": "Authorization"},
                },
            ),
):
    """Configure advanced provider settings using Body with embedded validation."""
    p = _state["providers"].get(pid)
    if not p:
        raise HTTPException(404, "Unknown provider")

    # Update health check configuration
    if "health_check" in config_data:
        health_config = config_data["health_check"]
        if "method" in health_config:
            p.health["method"] = health_config["method"]
        if "path" in health_config:
            p.health["path"] = health_config["path"]
        if "headers" in health_config:
            p.health["headers"] = health_config["headers"]

    # Update rate limit configuration
    if "rate_limits" in config_data:
        rate_config = config_data["rate_limits"]
        p.usage.update(rate_config)

    persist_providers(_state["providers"])
    return {"ok": True, "provider": p.to_dict(), "configured": list(config_data.keys())}


async def _petfinder_token() -> Optional[str]:
    """Get OAuth2 token for Petfinder API"""
    k = get_secret("PETFINDER_KEY")
    s = get_secret("PETFINDER_SECRET")
    if not (k and s):
        return None
    try:
        async with httpx.AsyncClient(timeout = 12) as client:
            r = await client.post(
                "https://api.petfinder.com / v2 / oauth2 / token",
                    data={
                    "grant_type": "client_credentials",
                        "client_id": k,
                        "client_secret": s,
                        },
                    headers={"Content - Type": "application / x - www - form - urlencoded"},
                    )
            if r.status_code >= 400:
                return None
            return r.json().get("access_token")
    except Exception:
        return None

@router.get("/pets / search")


async def pets_search(
    animal: str = Query("dog", pattern="^(dog|cat)$"),
        location: Optional[str] = None,
        limit: int = Query(20, ge = 1, le = 100),
        page: int = Query(1, ge = 1),
):
    """Search for pets using Petfinder API with fallback to breed images"""
    # Prefer Petfinder if enabled and credentials provided
    pf = _state["providers"].get("petfinder")
    if pf and pf.enabled and pf.status == "green":
        token = await _petfinder_token()
        if token:
            try:
                params = {"type": animal.capitalize(), "limit": limit, "page": page}
                if location:
                    params["location"] = location
                async with httpx.AsyncClient(timeout = 15) as client:
                    r = await client.get(
                        "https://api.petfinder.com / v2 / animals",
                            headers={"Authorization": f"Bearer {token}"},
                            params = params,
                            )
                    r.raise_for_status()
                    data = r.json()
                    return {"provider": "petfinder", "data": data}
            except Exception:
                pass  # Fall through to breed images

    # Fallback: species images with breed info
    if animal == "dog":
        p = _state["providers"].get("thedogapi")
        if p:
            key = get_secret(p.key_env or "")
            headers = {"x - api - key": key} if key else {}
            try:
                async with httpx.AsyncClient(timeout = 12) as client:
                    r = await client.get(
                        f"{p.base_url}/v1 / images / search?limit={limit}&has_breeds = 1",
                            headers = headers,
                            )
                    r.raise_for_status()
                    return {"provider": "thedogapi", "data": r.json()}
            except Exception as e:
                raise HTTPException(500, f"Failed to fetch dog data: {str(e)}")
    else:
        p = _state["providers"].get("thecatapi")
        if p:
            key = get_secret(p.key_env or "")
            headers = {"x - api - key": key} if key else {}
            try:
                async with httpx.AsyncClient(timeout = 12) as client:
                    r = await client.get(
                        f"{p.base_url}/v1 / images / search?limit={limit}&has_breeds = 1",
                            headers = headers,
                            )
                    r.raise_for_status()
                    return {"provider": "thecatapi", "data": r.json()}
            except Exception as e:
                raise HTTPException(500, f"Failed to fetch cat data: {str(e)}")

    raise HTTPException(404, f"No {animal} API provider configured")

@router.get("/pets / breeds")


async def pets_breeds(animal: str = Query("dog", pattern="^(dog|cat)$")):
    """Get pet breeds from TheDogAPI or TheCatAPI with Query parameter validation."""
    # Prefer the matching species API
    base = None
    header_name = None
    key = None
    if animal == "dog":
        p = _state["providers"].get("thedogapi")
        if p:
            base = p.base_url
            header_name = p.health.get("auth", {}).get("header")
            key = get_secret(p.key_env or "")
        url = f"{base}/v1 / breeds?limit = 1000" if base else None
    else:
        p = _state["providers"].get("thecatapi")
        if p:
            base = p.base_url
            header_name = p.health.get("auth", {}).get("header")
            key = get_secret(p.key_env or "")
        url = f"{base}/v1 / breeds?limit = 1000" if base else None

    if not url:
        raise HTTPException(404, f"No {animal} API provider configured")

    headers = {header_name: key} if header_name and key else {}
    try:
        async with httpx.AsyncClient(timeout = 12) as client:
            r = await client.get(url, headers = headers)
            r.raise_for_status()
            data = r.json()
            breeds = [{"id": str(i.get("id")), "name": i.get("name")} for i in data]
            return {"animal": animal, "count": len(breeds), "breeds": breeds}
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch {animal} breeds: {str(e)}")

# --- Fallback HTTP helper (use inside your services)
# Use shared http_with_fallback function from utils.common
http_with_fallback = shared_http_with_fallback

# --- Affiliates (starter suggestions; edit in config file)
DEFAULT_AFFILIATES = {
    "The Right Perspective": [
        {
            "id": "expressvpn",
                "name": "ExpressVPN",
                "url": "https://www.expressvpn.com / affiliates",
                "id_env": "AFFIL_EXPRESSVPN_ID",
                "enabled": False,
                },
            {
            "id": "nordvpn",
                "name": "NordVPN",
                "url": "https://nordvpn.com / affiliate - program/",
                "id_env": "AFFIL_NORDVPN_ID",
                "enabled": False,
                },
            {
            "id": "mps",
                "name": "My Patriot Supply",
                "url": "https://www.mypatriotsupply.com / pages / affiliate",
                "id_env": "AFFIL_MPS_ID",
                "enabled": False,
                },
            {
            "id": "goldco",
                "name": "Goldco",
                "url": "https://www.goldco.com / affiliate - program/",
                "id_env": "AFFIL_GOLDCO_ID",
                "enabled": False,
                },
            {
            "id": "audible",
                "name": "Audible",
                "url": "https://www.audible.com / affiliates",
                "id_env": "AFFIL_AUDIBLE_ID",
                "enabled": False,
                },
            ],
        "Next Gen Tech Today": [
        {
            "id": "amazon",
                "name": "Amazon Associates",
                "url": "https://affiliate - program.amazon.com/",
                "id_env": "AFFIL_AMAZON_TAG",
                "enabled": False,
                },
            {
            "id": "bestbuy",
                "name": "Best Buy",
                "url": "https://www.bestbuy.com / site / misc / affiliates / pcmcat316000050005.c?id = pcmcat316000050005",
                "id_env": "AFFIL_BESTBUY_ID",
                "enabled": False,
                },
            {
            "id": "bh",
                "name": "B&H Photo",
                "url": "https://www.bhphotovideo.com / find / HelpCenter / affiliate.jsp",
                "id_env": "AFFIL_BH_ID",
                "enabled": False,
                },
            {
            "id": "epn",
                "name": "eBay Partner Network",
                "url": "https://partnernetwork.ebay.com/",
                "id_env": "AFFIL_EBAY_ID",
                "enabled": False,
                },
            {
            "id": "newegg",
                "name": "Newegg",
                "url": "https://newegg.io / affiliate",
                "id_env": "AFFIL_NEWEGG_ID",
                "enabled": False,
                },
            ],
        "EcoWell Living": [
        {
            "id": "thrive",
                "name": "Thrive Market",
                "url": "https://thrivemarket.com / affiliate",
                "id_env": "AFFIL_THRIVE_ID",
                "enabled": False,
                },
            {
            "id": "iherb",
                "name": "iHerb",
                "url": "https://www.iherb.com / info / affiliates",
                "id_env": "AFFIL_IHERB_ID",
                "enabled": False,
                },
            {
            "id": "earthhero",
                "name": "EarthHero",
                "url": "https://earthhero.com / affiliate - program/",
                "id_env": "AFFIL_EARTHHERO_ID",
                "enabled": False,
                },
            {
            "id": "grove",
                "name": "Grove Collaborative",
                "url": "https://www.grove.co / affiliate",
                "id_env": "AFFIL_GROVE_ID",
                "enabled": False,
                },
            {
            "id": "pact",
                "name": "Pact Apparel",
                "url": "https://wearpact.com / pages / affiliate - program",
                "id_env": "AFFIL_PACT_ID",
                "enabled": False,
                },
            ],
        "AI Trend Reports": [
        {
            "id": "canva",
                "name": "Canva",
                "url": "https://www.canva.com / affiliates/",
                "id_env": "AFFIL_CANVA_ID",
                "enabled": False,
                },
            {
            "id": "grammarly",
                "name": "Grammarly",
                "url": "https://www.grammarly.com / affiliates",
                "id_env": "AFFIL_GRAMMARLY_ID",
                "enabled": False,
                },
            {
            "id": "descript",
                "name": "Descript",
                "url": "https://www.descript.com / affiliate - program",
                "id_env": "AFFIL_DESCRIPT_ID",
                "enabled": False,
                },
            {
            "id": "coursera",
                "name": "Coursera",
                "url": "https://www.coursera.org / affiliates",
                "id_env": "AFFIL_COURSERA_ID",
                "enabled": False,
                },
            {
            "id": "udemy",
                "name": "Udemy",
                "url": "https://www.udemy.com / affiliate/",
                "id_env": "AFFIL_UDEMY_ID",
                "enabled": False,
                },
            ],
}


def hydrate_affiliates() -> Dict[str, List[Dict[str, str]]]:
    data = _load_json(AFFILIATES_PATH, default = DEFAULT_AFFILIATES)
    if not AFFILIATES_PATH.exists():
        _save_json(AFFILIATES_PATH, data)
    return data

_affiliates = hydrate_affiliates()

@router.get("/affiliates")


async def list_affiliates():
    return _affiliates

@router.get("/affiliates / rich")


async def list_affiliates_rich():
    out = {}
    for channel, items in _affiliates.items():
        out[channel] = []
        for e in items:
            status = _affiliate_status(e)
            out[channel].append({**e, "status": status})
    return out

@router.patch("/affiliates/{channel}/{affil_id}")


async def update_affiliate(channel: str, affil_id: str, patch: AffiliatePatch):
    items = _affiliates.get(channel)
    if not items:
        raise HTTPException(404, "Unknown channel")
    entry = next((i for i in items if i["id"] == affil_id), None)
    if not entry:
        raise HTTPException(404, "Unknown affiliate id")
    if patch.enabled is not None:
        entry["enabled"] = patch.enabled
    if patch.id_value is not None:
        if not entry.get("id_env"):
            raise HTTPException(400, "This affiliate has no ID env configured")
        set_secret(entry["id_env"], patch.id_value)
    _save_json(AFFILIATES_PATH, _affiliates)
    return {"ok": True}

# --- Simple HTML UI: colored dots + key entry + quick add
HTML_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf - 8"/>
  <title > Integrations Hub</title>
  <style>
    body { font - family: system - ui, -apple - system, Segoe UI, Roboto, sans - serif; margin: 24px; color: #e2e8f0; background:#0f172a; }
    h1 { color:#a3e635 }
    a { color:#60a5fa }
    table { width:100%; border - collapse: collapse; margin - top: 12px; }
    th, td { padding: 8px 10px; border - bottom: 1px solid #1f2937; }
    tr:hover { background:#111827 }
    .dot { width:10px; height:10px; border - radius:9999px; display:inline - block; margin - right:8px; vertical - align: middle; }
    .green { background:#22c55e }
    .purple { background:#a855f7 }
    .red { background:#ef4444 }
    .pill { display:inline - block; padding:2px 8px; border - radius:9999px; background:#1f2937; font - size:12px; }
    .affiliate - table { margin - bottom: 24px; }
    .affiliate - table th:first - child { background:#1e293b; color:#a3e635; }
    input[type="password"], input[type="text"] { background:#0b1220; border:1px solid #1f2937; color:#e2e8f0; padding:6px 8px; border - radius:6px; width: 100%; }
    button { background:#334155; color:#e2e8f0; border:0; padding:6px 10px; border - radius:6px; cursor:pointer }
    button:hover { filter:brightness(1.1) }
    .row - actions { display:flex; gap:8px; }
    .note { color:#94a3b8; font - size: 12px; }
    .grid { display:grid; grid - template - columns: 1fr 1fr; gap: 24px; }
    .card { background:#0b1220; border:1px solid #1f2937; border - radius:12px; padding:16px; }
  </style>
</head>
<body>
  <h1 > Integrations Hub</h1>
  <p class="note">Green = working, Purple = needs key, Red = not working. Toggle enabled, add keys, \
    and test providers below. Use the <b > Add Provider</b> card to add new ones quickly.</p>

  <div class="grid">
    <div class="card">
      <h2 > Providers</h2>
      <table id="providers">
        <thead>
          <tr><th > Status</th><th > Name</th><th > Category</th><th > Docs</th><th > Signup</th><th > Key</th><th > Enabled</th><th > Test</th></tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="card">
      <h2 > Add Provider</h2>
      <div>
        <label > Name < br/><input id="np_name" type="text"/></label><br/><br/>
        <label > ID (unique)<br/><input id="np_id" type="text"/></label><br/><br/>
        <label > Category < br/><input id="np_cat" type="text" placeholder="news / images / ai / weather/..."/></label><br/><br/>
        <label > Docs URL < br/><input id="np_docs" type="text"/></label><br/><br/>
        <label > Signup URL (optional)<br/><input id="np_signup" type="text"/></label><br/><br/>
        <label > Secret Name (e.g.,
    OPENWEATHER_KEY) <span class="note">(optional)</span><br/><input id="np_keyenv" type="text"/></label><br/><br/>
        <label><input id="np_needskey" type="checkbox" checked/> Needs Key</label><br/><br/>
        <button onclick="addProvider()">Add</button>
        <p id="np_msg" class="note"></p>
      </div>

      <h2 style="margin - top:24px;">Top Affiliates (by channel)</h2>
      <div id="affiliates"></div>
    </div>
  </div>

<script>
async function fetchProviders(){
    const res = await fetch('/integrations / providers');
  const data = await res.json();
  const tbody = document.querySelector('#providers tbody');
  tbody.innerHTML = '';
  data.providers.forEach(p => {
      const tr = document.createElement('tr');
    const status = `<span class="dot ${p.status}"></span><span class="pill">${p.status}</span>`;
    const docs = `<a href="${p.docs_url}" target="_blank">Docs</a>`;
    const signup = p.signup_url ? `<a href="${p.signup_url}" target="_blank">Get Key</a>` : '<span class="note">n / a</span>';
    const keyCell = p.key_env ? `<input type="password" placeholder="${p.key_env}" onblur="saveKey('${p.id}',
    this.value)" />` : '<span class="note">none</span>';
    const enabled = `<input type="checkbox" ${p.enabled?'checked':''} onchange="toggleEnabled('${p.id}',
    this.checked)" />`;
    const testBtn = `<button onclick="testProvider('${p.id}')">Test</button>`;
    tr.innerHTML = `<td>${status}</td><td>${p.name}</td><td>${p.category}</td><td>${docs}</td><td>${signup}</td><td>${keyCell}</td><td>${enabled}</td><td class="row - actions">${testBtn}</td>`;
    tbody.appendChild(tr);
  });
}

async function toggleEnabled(id, enabled){
    await fetch('/integrations / providers/'+id, {method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({enabled})});
  fetchProviders();
}
async function saveKey(id, key){
    if(!key) return;
  await fetch('/integrations / providers/'+id, {method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({key})});
  fetchProviders();
}
async function testProvider(id){
    await fetch('/integrations / providers/'+id+'/test', {method:'POST'});
  fetchProviders();
}
async function addProvider(){
    const id = document.getElementById('np_id').value.trim();
  const name = document.getElementById('np_name').value.trim();
  const category = document.getElementById('np_cat').value.trim();
  const docs_url = document.getElementById('np_docs').value.trim();
  const signup_url = document.getElementById('np_signup').value.trim();
  const key_env = document.getElementById('np_keyenv').value.trim();
  const requires_key = document.getElementById('np_needskey').checked;
  const msg = document.getElementById('np_msg');
  msg.textContent = '';
  if(!id || !name || !category || !docs_url){
      msg.textContent = 'Please fill id, name, category, docs_url';
    return;
  }
  const res = await fetch('/integrations / providers', {method:'POST',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({id,
    name,
    category,
    docs_url,
    signup_url,
    key_env,
    requires_key})});
  if(res.ok){
      msg.textContent = 'Added!';
    document.getElementById('np_id').value='';
    document.getElementById('np_name').value='';
    document.getElementById('np_cat').value='';
    document.getElementById('np_docs').value='';
    document.getElementById('np_signup').value='';
    document.getElementById('np_keyenv').value='';
    document.getElementById('np_needskey').checked = true;
    fetchProviders();
  } else {
      msg.textContent = 'Failed: '+res.status;
  }
}

async function loadAffiliates(){
    const res = await fetch('/integrations / affiliates / rich');
  const data = await res.json();
  const root = document.getElementById('affiliates');
  root.innerHTML = '';
  Object.keys(data).forEach(channel => {
      const table = document.createElement('table');
    table.innerHTML = `
        <thead><tr><th colspan="6" style="text - align:left">${channel}</th></tr>
        <tr><th > Status</th><th > Name</th><th > Program</th><th > ID</th><th > Enabled</th><th > Visit</th></tr></thead>
        <tbody></tbody>`;
    const tbody = table.querySelector('tbody');
    data[channel].forEach(a => {
        const dot = `<span class="dot ${a.status}"></span><span class="pill">${a.status}</span>`;
        const idCell = a.id_env ? `<input type="text" placeholder="${a.id_env}" onblur="saveAffilId('${channel}','${a.id}',
    this.value)" />` : '<span class="note">n / a</span>';
        const enabled = `<input type="checkbox" ${a.enabled?'checked':''} onchange="toggleAffil('${channel}','${a.id}',
    this.checked)" />`;
        const signup = `<a href="${a.url}" target="_blank">Join / Get ID</a>`;
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${dot}</td><td>${a.name}</td><td>${a.id}</td><td>${idCell}</td><td>${enabled}</td><td>${signup}</td>`;
        tbody.appendChild(tr);
    });
    root.appendChild(table);
  });
}
async function saveAffilId(channel, id, id_value){
    if(!id_value) return;
    await fetch(`/integrations / affiliates/${encodeURIComponent(channel)}/${id}`, {
        method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({id_value})
    });
    loadAffiliates();
}
async function toggleAffil(channel, id, enabled){
    await fetch(`/integrations / affiliates/${encodeURIComponent(channel)}/${id}`, {
        method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({enabled})
    });
    loadAffiliates();
}
fetchProviders();
loadAffiliates();
</script>
</body>
</html>
"""

@router.get("/", response_class = HTMLResponse)


async def integrations_home(request: Request):
    return HTMLResponse(HTML_PAGE)

@router.get("/affiliates - only", response_class = HTMLResponse)


async def affiliates_only_page(request: Request):
    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head>
        <title > Affiliate Management</title>
        <style>
            body { font - family: Arial, sans - serif; margin: 40px; background: #f5f5f5; }
            h1 { color: #333; }
            .status { margin: 20px 0; }
            .status - item { margin: 10px 0; }
            table { border - collapse: collapse; width: 100%; margin: 20px 0; background: white; }
            th, td { border: 1px solid #ddd; padding: 8px; text - align: left; }
            th { background - color: #f2f2f2; font - weight: bold; }
            .dot { display: inline - block; width: 10px; height: 10px; border - radius: 50%; margin - right: 5px; }
            .dot.green { background - color: #4CAF50; }
            .dot.purple { background - color: #9C27B0; }
            .dot.red { background - color: #F44336; }
            .pill { background - color: #e0e0e0; padding: 2px 6px; border - radius: 10px; font - size: 12px; }
            .note { color: #888; font - style: italic; }
            input[type="text"] { width: 120px; padding: 4px; }
            input[type="checkbox"] { transform: scale(1.2); }
            a { color: #1976D2; text - decoration: none; }
            a:hover { text - decoration: underline; }
        </style>
    </head>
    <body>
        <h1 > Affiliate Management</h1>
        <div class="status">
            <div class="status - item">Server Status: ✅ Running</div>
            <div class="status - item">Affiliate Programs: 📊 Available</div>
        </div>
        <h2 style="margin - top:24px;">Affiliates (by channel)</h2>
        <div id="affiliates"></div>
        <script>
        async function loadAffiliates(){
            const res = await fetch('/integrations / affiliates / rich');
            const data = await res.json();
            const root = document.getElementById('affiliates');
            root.innerHTML = '';
            Object.keys(data).forEach(channel => {
                const table = document.createElement('table');
                table.innerHTML = `
                    <thead><tr><th colspan="6" style="text - align:left">${channel}</th></tr>
                    <tr><th > Status</th><th > Name</th><th > Program</th><th > ID</th><th > Enabled</th><th > Visit</th></tr></thead>
                    <tbody></tbody>`;
                const tbody = table.querySelector('tbody');
                data[channel].forEach(a => {
                    const dot = `<span class="dot ${a.status}"></span><span class="pill">${a.status}</span>`;
                    const idCell = a.id_env ? `<input type="text" placeholder="${a.id_env}" onblur="saveAffilId('${channel}','${a.id}',
    this.value)" />` : '<span class="note">n / a</span>';
                    const enabled = `<input type="checkbox" ${a.enabled?'checked':''} onchange="toggleAffil('${channel}','${a.id}',
    this.checked)" />`;
                    const signup = `<a href="${a.url}" target="_blank">Join / Get ID</a>`;
                    const tr = document.createElement('tr');
                    tr.innerHTML = `<td>${dot}</td><td>${a.name}</td><td>${a.id}</td><td>${idCell}</td><td>${enabled}</td><td>${signup}</td>`;
                    tbody.appendChild(tr);
                });
                root.appendChild(table);
            });
        }
        async function saveAffilId(channel, id, id_value){
            if(!id_value) return;
            await fetch(`/integrations / affiliates/${encodeURIComponent(channel)}/${id}`, {
                method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({id_value})
            });
            loadAffiliates();
        }
        async function toggleAffil(channel, id, enabled){
            await fetch(`/integrations / affiliates/${encodeURIComponent(channel)}/${id}`, {
                method:'PATCH',
    headers:{'Content - Type':'application / json'},
    body: JSON.stringify({enabled})
            });
            loadAffiliates();
        }
        // Load affiliates on page load
        loadAffiliates();
        </script>
    </body>
    </html>
    """
    )

# --- Background health monitor

import logging

logger = logging.getLogger(__name__)


async def _health_worker():
    while True:
        await asyncio.sleep(60)  # every minute
        try:
            for p in list(_state["providers"].values()):
                try:
                    if not getattr(p, "enabled", False):
                        continue

                    # Defensive attribute access
                    requires_key = getattr(p, "requires_key", False)
                    key_env = getattr(p, "key_env", None)

                    if requires_key and key_env and not get_secret(key_env):
                        p.status = "purple"
                        persist_providers(_state["providers"])
                        continue

                    health_url = getattr(p, "health_url", None)
                    docs_url = getattr(p, "docs_url", None)

                    if not health_url and not docs_url:
                        continue

                    try:
                        async with httpx.AsyncClient(timeout = 8) as client:
                            r = await client.get(health_url or docs_url)
                            if 200 <= r.status_code < 300:
                                p.status = "green"
                                p.last_ok = _now_iso()
                                p.last_error = None
                            else:
                                p.status = "red"
                                p.last_error = f"{r.status_code}"
                        persist_providers(_state["providers"])
                    except Exception as e:
                        p.status = "red"
                        p.last_error = str(e)
                        persist_providers(_state["providers"])
                except Exception as provider_error:
                    logger.exception(
                        f"Error processing provider {getattr(p, 'id', 'unknown')}: {provider_error}"
                    )
                    continue
        except Exception as worker_error:
            logger.exception(
                f"Health worker crashed; continuing (handled): {worker_error}"
            )

@asynccontextmanager


async def lifespan(app: FastAPI):
    # STARTUP
    health_task = asyncio.create_task(_health_worker())
    try:
        yield
    finally:
        # SHUTDOWN
        health_task.cancel()
        try:
            await health_task
        except asyncio.CancelledError:
            pass


def wire_integrations(app: FastAPI) -> None:
    app.include_router(router)
    app.include_router(content_router)

# --- Optional standalone server for quick test
if __name__ == "__main__":

    import uvicorn

    test_app = FastAPI()
    wire_integrations(test_app)
    uvicorn.run(test_app, host="127.0.0.1", port = 8010)