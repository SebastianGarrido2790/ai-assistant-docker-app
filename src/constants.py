"""
Core application constants and path definitions.

This module provides absolute paths to key project directories
(e.g., source code, logs) to ensure reliable file operations
across the entire application suite.
"""

from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Log directories
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)
