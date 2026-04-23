"""
Unit tests for Pydantic models and data validation schemas.

Ensures that ChatRequest, ChatResponse, and HealthResponse models
correctly validate input data and handle default values or missing fields.
"""

import pytest
from pydantic import ValidationError

from src.entity.schema import ChatRequest, ChatResponse, HealthResponse


def test_chat_request_valid():
    """Test that valid fields successfully instantiate ChatRequest."""
    request = ChatRequest(prompt="Hello", use_cloud=True, session_id="test-123")
    assert request.prompt == "Hello"
    assert request.use_cloud is True
    assert request.session_id == "test-123"


def test_chat_request_defaults():
    """Test that valid Request fallback to proper default values."""
    request = ChatRequest(prompt="Just a prompt")
    assert request.prompt == "Just a prompt"
    assert request.use_cloud is False
    assert request.session_id == "default"


def test_chat_request_missing_prompt():
    """Should raise ValidationError if prompt is absent."""
    with pytest.raises(ValidationError):
        ChatRequest(use_cloud=True)  # type: ignore


def test_chat_response_valid():
    """Test ChatResponse properties."""
    response = ChatResponse(response="Hi there!", model_used="cloud")
    assert response.response == "Hi there!"
    assert response.model_used == "cloud"


def test_health_response_valid():
    """Test that Health responses correctly assign to status."""
    response = HealthResponse(
        status="healthy", model="test-model", memory_backend="test-backend"
    )
    assert response.status == "healthy"
    assert response.model == "test-model"
    assert response.memory_backend == "test-backend"
