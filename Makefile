# =============================================================================
# Makefile — AI Assistant Docker App
# Standardizes common development tasks across Linux/macOS/CI environments.
#
# Windows users: Use validate_system.bat and launch_system.bat instead.
# These targets mirror the 4-pillar validation defined in validate_system.bat
# and the CI pipeline in .github/workflows/ci.yml.
#
# Usage:
#   make install        # Sync all dependencies
#   make lint           # Run ruff (lint + format check)
#   make typecheck      # Run pyright
#   make bandit         # Run bandit security scan
#   make test           # Run pytest with coverage gate (>= 70%)
#   make quality        # Full quality gate (lint + typecheck + bandit)
#   make docker-build   # Build the production Docker image
#   make clean          # Remove cache artifacts
# =============================================================================

.PHONY: install lint typecheck bandit test quality docker-build clean

# --- Dependency Management ---

install:
	uv sync

# --- Static Analysis ---

lint:
	uv run ruff check .
	uv run ruff format --check .

typecheck:
	uv run pyright

bandit:
	uv run bandit -r src/ -ll

# --- Testing ---

test:
	uv run pytest --cov=src --cov-fail-under=70

# --- Combined Quality Gate (mirrors CI Pillar 1 + 2) ---

quality: lint typecheck bandit test

# --- Docker ---

docker-build:
	docker build -t ai-assistant:latest .

# --- Cleanup ---

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
