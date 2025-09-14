# tests/test_meta.py
import pytest
import httpx

@pytest.mark.parametrize("path", [
    "/api/version", "/api/system/status", "/api/services", "/ws/info",
    "/health", "/health/live", "/health/ready", "/api/health"
])
def test_meta_endpoints_live(path):
    """Test that all meta endpoints return 200 status"""
    r = httpx.get(f"http://localhost:8000{path}", timeout=3)
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text}"

def test_version_redirect():
    """Test that /version redirects to /api/version"""
    r = httpx.get("http://localhost:8000/version", follow_redirects=False, timeout=3)
    assert r.status_code == 301
    assert r.headers["location"] == "/api/version"

def test_api_version_structure():
    """Test that /api/version returns expected structure"""
    r = httpx.get("http://localhost:8000/api/version", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert "name" in data
    assert "version" in data
    assert "build" in data

def test_health_ready_structure():
    """Test that /health/ready returns expected structure"""
    r = httpx.get("http://localhost:8000/health/ready", timeout=3)
    assert r.status_code == 200
    data = r.json()
    assert "ready" in data
    assert "timestamp" in data
    assert "checks" in data
    assert isinstance(data["ready"], bool)