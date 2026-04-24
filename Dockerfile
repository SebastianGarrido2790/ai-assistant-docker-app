# Stage 1: builder
FROM python:3.12-slim AS builder
RUN pip install uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 2: runtime
FROM python:3.12-slim AS runtime
RUN adduser --disabled-password appuser
WORKDIR /app
COPY --from=builder /app/.venv ./.venv
COPY src/ ./src/

# Ensure the appuser can write the checkpoints.sqlite database
RUN chown -R appuser:appuser /app

USER appuser

# Set PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

CMD ["streamlit", "run", "src/ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]