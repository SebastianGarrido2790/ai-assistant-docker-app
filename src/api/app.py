"""
Hardened FastAPI Microservice backend for the AI Assistant.

This module exposes the main REST API endpoints (/v1/chat, /v1/health) with
production-grade hardening:
1. Global exception handling for sanitized JSON error responses.
2. Rate limiting via slowapi to prevent resource exhaustion.
3. Resource lifecycle management (SQLite connections) via lifespan context.
4. API Key authentication for secure access.

Usage:
    uv run uvicorn src.api.app:app --reload --port 8000
"""

import sqlite3
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from langchain_core.messages import HumanMessage
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.agents.graph import build_graph
from src.config.configuration import ConfigurationManager
from src.constants import PROJECT_ROOT
from src.entity.schema import ChatRequest, ChatResponse, HealthResponse
from src.utils.logger import get_logger
from src.utils.telemetry import tracer

logger = get_logger(__name__, headline="api")

# Load configuration once at module level for middleware setup
config_mgr = ConfigurationManager()
config = config_mgr.get_config()

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """
    Verify the provided API key against the configured one.

    Args:
        api_key: The API key from the X-API-Key header.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    if api_key != config.app_api_key:
        raise HTTPException(status_code=403, detail="Invalid API Key.")

    return api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the lifecycle of the API resources (DB connections, graph initialization)."""
    logger.info("Initializing Agent Graph and Configuration State...")

    # 1. Setup persistent memory checkpointing (managed by app lifecycle)
    db_path = str(PROJECT_ROOT / "checkpoints.sqlite")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    app.state.db_conn = conn

    # 2. Build graph with the shared connection
    app.state.config = config
    app.state.agent_graph = build_graph(conn=conn)

    logger.info("Agent Graph initialized.")
    yield

    # 3. Teardown
    logger.info("Shutting down API...")
    if hasattr(app.state, "db_conn"):
        app.state.db_conn.close()
        logger.info("SQLite connection closed.")


app = FastAPI(
    title="AI Assistant API",
    description="API for the Agentic AI Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# Attach limiter and handlers
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions to prevent leaking internal state."""
    logger.error("Unhandled exception: {}", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "type": exc.__class__.__name__,
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=config.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    config = app.state.config
    return HealthResponse(
        status="healthy",
        model=config.remote_model_name,
        memory_backend="SQLite + ChromaDB",
    )


@app.post(
    "/v1/chat", response_model=ChatResponse, dependencies=[Depends(verify_api_key)]
)
@limiter.limit("10/minute")
async def chat(chat_request: ChatRequest, request: Request):
    """
    Chat endpoint interacting with the LangGraph agent.

    Args:
        chat_request: The chat request containing prompt and session ID.
        request: The raw FastAPI request (required for slowapi).
    """
    logger.info(f"Received chat request for session: {chat_request.session_id}")

    config = {
        "configurable": {
            "thread_id": chat_request.session_id,
            "use_cloud": chat_request.use_cloud,
        }
    }

    user_message = HumanMessage(content=chat_request.prompt)

    with tracer.start_as_current_span("agent_invocation") as span:
        start_time = time.time()

        result = app.state.agent_graph.invoke(
            {"messages": [user_message]}, config=config
        )

        latency_ms = (time.time() - start_time) * 1000

        prompt_tokens = 0
        completion_tokens = 0

        for msg in reversed(result["messages"]):
            if (
                hasattr(msg, "response_metadata")
                and "token_usage" in msg.response_metadata
            ):
                usage = msg.response_metadata["token_usage"]
                prompt_tokens += usage.get("prompt_tokens", 0)
                completion_tokens += usage.get("completion_tokens", 0)
                break

        span.set_attribute("tokens.prompt", prompt_tokens)
        span.set_attribute("tokens.completion", completion_tokens)
        span.set_attribute("latency_ms", latency_ms)

    final_message = result["messages"][-1].content
    model_used = "cloud" if chat_request.use_cloud else "local"

    logger.bind(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        latency_ms=round(latency_ms, 2),
    ).info(f"Graph executed successfully, responding with {model_used} model")

    return ChatResponse(response=final_message, model_used=model_used)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
