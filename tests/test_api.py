"""
Integration tests for the FastAPI application endpoints.

This module uses the FastAPI TestClient to verify health checks
and chat endpoint interactions, mocking the underlying LangGraph
agent execution with lifespan support.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.api.app import app


@pytest.fixture
def client_and_mock():
    """Fixture that mocks build_graph and returns a TestClient with lifespan support."""
    with patch("src.api.app.build_graph") as mock_build:
        mock_graph = MagicMock()
        mock_build.return_value = mock_graph
        with TestClient(app) as client:
            # Re-ensure app.state has the mock in case lifespan set it differently
            app.state.agent_graph = mock_graph
            yield client, mock_graph


def test_health_check(client_and_mock):
    """Verify that the FastAPI app runs properly and responds successfully to Health Checks."""
    client, _ = client_and_mock
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model" in data
    assert "memory_backend" in data


def test_chat_endpoint_success(client_and_mock):
    """Verify that requests successfully send inputs to the agent_graph LangGraph pipeline."""
    client, mock_agent_graph = client_and_mock

    mock_msg = MagicMock()
    mock_msg.content = "Mocked AI response"
    mock_agent_graph.invoke.return_value = {"messages": [mock_msg]}

    payload = {
        "prompt": "Hello test user",
        "use_cloud": False,
        "session_id": "session-123",
    }

    response = client.post("/v1/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"response": "Mocked AI response", "model_used": "local"}


def test_chat_endpoint_failure(client_and_mock):
    """Verify that errors during agent graph executions correctly fallback to 500 error ranges."""
    client, mock_agent_graph = client_and_mock
    mock_agent_graph.invoke.side_effect = Exception("LangGraph failed unpredictably")

    payload = {"prompt": "Hello test", "use_cloud": False, "session_id": "session"}

    response = client.post("/v1/chat", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
