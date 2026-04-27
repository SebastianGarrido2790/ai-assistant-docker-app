"""
Centralized test configuration and shared fixtures for the AI Assistant.

This module provides mocks for the core agentic infrastructure, including
the LangGraph execution engine, configuration management, and telemetry stubs,
ensuring tests are deterministic, fast, and isolated from external side effects.
"""

from unittest.mock import MagicMock, patch

import pytest
from langgraph.graph.state import CompiledStateGraph

from src.config.configuration import AppConfig, ConfigurationManager


@pytest.fixture
def mock_app_config() -> AppConfig:
    """Provides a controlled configuration for testing."""
    return AppConfig(
        openrouter_api_key="test-openrouter-key",
        local_model_name="test-local-model",
        remote_model_name="test-remote-model",
        local_base_url="http://test-local-url",
        remote_base_url="https://test-remote-url",
        app_api_key="test-app-key",
        allowed_origins=["*"],
    )


@pytest.fixture
def mock_config_manager(mock_app_config: AppConfig) -> MagicMock:
    """Provides a mocked ConfigurationManager returning the test config."""
    mock_mgr = MagicMock(spec=ConfigurationManager)
    mock_mgr.get_config.return_value = mock_app_config
    return mock_mgr


@pytest.fixture
def mock_graph() -> MagicMock:
    """Mocks the compiled LangGraph to avoid LLM calls or DB side effects."""
    # We use spec=CompiledStateGraph to ensure it has the correct interface
    mock = MagicMock(spec=CompiledStateGraph)

    # Setup a default return value for invoke to simulate a successful response
    mock.invoke.return_value = {
        "messages": [
            MagicMock(
                content="Mocked response",
                response_metadata={
                    "token_usage": {"prompt_tokens": 10, "completion_tokens": 20}
                },
            )
        ]
    }
    return mock


@pytest.fixture(autouse=True)
def otel_tracer_stub():
    """Stub for OpenTelemetry tracer to prevent real telemetry export during tests."""
    with patch("src.utils.telemetry.trace.get_tracer") as mock_get_tracer:
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer

        # Patch the global tracer in the telemetry module if it's already initialized
        with patch("src.utils.telemetry.tracer", mock_tracer):
            yield mock_tracer


@pytest.fixture
def patch_build_graph(mock_graph: MagicMock):
    """Fixture to patch build_graph with the mock graph."""
    # We patch it in both locations to be safe, especially in the API app where it's used in lifespan
    with (
        patch("src.agents.graph.build_graph", return_value=mock_graph),
        patch("src.api.app.build_graph", return_value=mock_graph),
    ):
        yield mock_graph


@pytest.fixture
def patch_config_manager(mock_config_manager: MagicMock):
    """Fixture to patch ConfigurationManager globally."""
    with patch(
        "src.config.configuration.ConfigurationManager",
        return_value=mock_config_manager,
    ):
        yield mock_config_manager
