# =============================================================================
# AI Assistant with Persistent Memory — Dockerfile
# Provides the production-ready runtime environment for the agentic system.
# =============================================================================

# Stage 1: builder
FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: runtime
FROM python:3.12-slim AS runtime
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    adduser --disabled-password appuser
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY src/ ./src/

# Ensure the appuser can write the checkpoints.sqlite database
RUN chown -R appuser:appuser /app

USER appuser

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Health check for the backend API service.
# Uses stdlib only — no extra deps required.
# Note: This targets the FastAPI backend on port 8000.
# The docker-compose frontend service overrides CMD, so this healthcheck
# is most relevant to the backend service entry.
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c \
    "import urllib.request, sys; \
     r = urllib.request.urlopen('http://localhost:8000/v1/health', timeout=5); \
     sys.exit(0 if r.status == 200 else 1)"

CMD ["streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]