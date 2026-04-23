"""
Unit tests for the ConfigurationManager system.

Verifies that application settings are correctly loaded from
environment variables and YAML files with the appropriate precedence.
"""

from src.config.configuration import ConfigurationManager


def test_configuration_loads_from_env_vars(monkeypatch):
    """Test that environment variables take precedence over defaults."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-123")
    monkeypatch.setenv("LOCAL_MODEL_NAME", "test-local-model")

    manager = ConfigurationManager()
    config = manager.get_config()

    assert config.openrouter_api_key == "test-key-123"
    assert config.local_model_name == "test-local-model"


def test_configuration_defaults(monkeypatch):
    """Test default config setup without active environment variables."""
    # Ensure environment variables won't interfere for this specific test
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("LOCAL_MODEL_NAME", raising=False)
    monkeypatch.delenv("REMOTE_MODEL_NAME", raising=False)
    monkeypatch.delenv("LOCAL_BASE_URL", raising=False)
    monkeypatch.delenv("REMOTE_BASE_URL", raising=False)

    manager = ConfigurationManager(
        config_file="non_existent_config.yaml"
    )  # Ensure no yaml overrides
    config = manager.get_config()

    assert config.local_model_name == "ai/devstral-small-2"
    assert config.remote_model_name == "openai/gpt-oss-20b"
