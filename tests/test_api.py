"""
Integration tests for the FastAPI application endpoints.

This module uses the FastAPI TestClient to verify health checks
and chat endpoint interactions, mocking the underlying LangGraph
agent execution.
"""

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.api.app import app

client = TestClient(app)

def test_health_check():
    """Verify that the FastAPI app runs properly and responds successfully to Health Checks."""
    response = client.get("/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch("src.api.app.agent_graph")
def test_chat_endpoint_success(mock_agent_graph):
    """Verify that requests successfully send inputs to the agent_graph LangGraph pipeline."""
    mock_msg = MagicMock()
    mock_msg.content = "Mocked AI response"
    mock_agent_graph.invoke.return_value = {"messages": [mock_msg]}

    payload = {
        "prompt": "Hello test user",
        "use_cloud": False,
        "session_id": "session-123"
    }
    
    response = client.post("/v1/chat", json=payload)
    
    assert response.status_code == 200
    assert response.json() == {
        "response": "Mocked AI response",
        "model_used": "local"
    }

@patch("src.api.app.agent_graph")
def test_chat_endpoint_failure(mock_agent_graph):
    """Verify that errors during agent graph executions correctly fallback to 500 error ranges without leaking internal structures."""
    mock_agent_graph.invoke.side_effect = Exception("LangGraph failed unpredictably")

    payload = {
        "prompt": "Hello test",
        "use_cloud": False,
        "session_id": "session"
    }

    response = client.post("/v1/chat", json=payload)
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
