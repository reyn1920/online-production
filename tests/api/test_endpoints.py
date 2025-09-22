"""
API endpoint tests for Trae AI FastAPI Application
"""

import pytest
from fastapi import status


@pytest.mark.api
def test_health_endpoint(client, health_response):
    """Test the health check endpoint."""
    response = client.get("/api/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == health_response


@pytest.mark.api
def test_agents_status_endpoint(client, agents_status_response):
    """Test the agents status endpoint."""
    response = client.get("/api/agents/status")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "agents" in data
    assert "overall" in data
    assert data["overall"] == "ready"
    assert len(data["agents"]) == 3

    # Check each agent has required fields
    for agent in data["agents"]:
        assert "name" in agent
        assert "status" in agent


@pytest.mark.api
def test_run_workflow_endpoint(client, sample_workflow_payload):
    """Test the workflow execution endpoint."""
    workflow_name = "test_workflow"
    response = client.post(
        f"/api/workflows/{workflow_name}", json=sample_workflow_payload
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()

    assert data["ok"] is True
    assert data["workflow"] == workflow_name
    assert "task_id" in data
    assert data["task_id"].startswith(f"wf_{workflow_name}_")
    assert data["message"] == "queued"


@pytest.mark.api
def test_run_workflow_endpoint_empty_payload(client):
    """Test the workflow execution endpoint with empty payload."""
    workflow_name = "empty_workflow"
    response = client.post(f"/api/workflows/{workflow_name}", json={})

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()

    assert data["ok"] is True
    assert data["workflow"] == workflow_name


@pytest.mark.api
def test_run_workflow_endpoint_no_payload(client):
    """Test the workflow execution endpoint without payload."""
    workflow_name = "no_payload_workflow"
    response = client.post(f"/api/workflows/{workflow_name}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.api
def test_nonexistent_endpoint(client):
    """Test accessing a non-existent endpoint."""
    response = client.get("/api/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.api
def test_cors_headers(client):
    """Test CORS headers are properly set."""
    response = client.get("/api/health")

    # Check that CORS headers are present (they should be set by the middleware)
    assert response.status_code == status.HTTP_200_OK
