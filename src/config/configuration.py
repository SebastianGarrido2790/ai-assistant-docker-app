"""
Configuration management system for the AI Assistant.

This module handles loading and validating settings from
YAML files and environment variables, mapping them into
a structured AppConfig dataclass.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from src.constants import PROJECT_ROOT


@dataclass(frozen=True)
class AppConfig:
    """Read-only container for application settings."""

    openrouter_api_key: str
    local_model_name: str
    remote_model_name: str
    local_base_url: str
    remote_base_url: str


class ConfigurationManager:
    """Manages application configuration, resolving from YAML and environment variables."""

    def __init__(self, config_file: str | Path = "config.yaml"):
        """
        Initialize the manager with a config file path.

        Args:
            config_file: Relative or absolute path to the configuration YAML file.
        """
        self.config_filepath = Path(config_file)
        if not self.config_filepath.is_absolute():
            self.config_filepath = PROJECT_ROOT / self.config_filepath

    def get_config(self) -> AppConfig:
        """
        Load configuration variables with precedence.

        Loads configurations giving precedence to active Environment
        Variables over what is stored in the YAML config.

        Returns:
            AppConfig: Frozen dataclass with final loaded configurations.
        """
        config_data: dict[str, Any] = {}
        if self.config_filepath.exists():
            with open(self.config_filepath, encoding="utf-8") as f:
                config_data = yaml.safe_load(f) or {}

        # Resolve config from environment variables
        # Priority:
        # 1. Docker-injected variables (LLM_URL, LLM_MODEL) - Ground truth in Docker AI environments
        # 2. Explicit LOCAL_*/REMOTE_* variables
        # 3. YAML config defaults
        return AppConfig(
            openrouter_api_key=str(
                os.environ.get(
                    "OPENROUTER_API_KEY", config_data.get("openrouter_api_key", "")
                )
            ),
            local_model_name=str(
                os.environ.get("LLM_MODEL")
                or os.environ.get("LOCAL_MODEL_NAME")
                or config_data.get("local_model_name", "ai/devstral-small-2")
            ),
            remote_model_name=str(
                os.environ.get(
                    "REMOTE_MODEL_NAME",
                    config_data.get("remote_model_name", "openai/gpt-oss-20b"),
                )
            ),
            local_base_url=str(
                os.environ.get("LLM_URL")
                or os.environ.get("LOCAL_BASE_URL")
                or config_data.get(
                    "local_base_url", "http://llm:8080/engines/llama.cpp/v1"
                )
            ),
            remote_base_url=str(
                os.environ.get(
                    "REMOTE_BASE_URL",
                    config_data.get("remote_base_url", "https://openrouter.ai/api/v1"),
                )
            ),
        )
