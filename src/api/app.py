"""
FastAPI Microservice backend for the AI Assistant.

This module exposes the main REST API endpoints (/v1/chat, /v1/health).
It proxies requests directly to the LangGraph execution engine, serving
as the deterministic outer shell surrounding the probabilistic AI.

Usage:
    uv run uvicorn src.api.app:app --reload --port 8000
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage

from src.agents.graph import build_graph
from src.config.configuration import ConfigurationManager
from src.entity.schema import ChatRequest, ChatResponse, HealthResponse
from src.utils.logger import get_logger
from src.utils.telemetry import tracer

logger = get_logger(__name__, headline="api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing Agent Graph...")
    app.state.agent_graph = build_graph()
    logger.info("Agent Graph initialized.")
    yield
    logger.info("Shutting down API...")


app = FastAPI(
    title="AI Assistant API",
    description="API for the Agentic AI Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    config_mgr = ConfigurationManager()
    config = config_mgr.get_config()
    return HealthResponse(
        status="healthy",
        model=config.remote_model_name,
        memory_backend="SQLite + ChromaDB",
    )


@app.post("/v1/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint interacting with the LangGraph agent."""
    logger.info(f"Received chat request for session: {request.session_id}")
    try:
        config = {
            "configurable": {
                "thread_id": request.session_id,
                "use_cloud": request.use_cloud,
            }
        }

        user_message = HumanMessage(content=request.prompt)

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
        model_used = "cloud" if request.use_cloud else "local"

        logger.bind(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            latency_ms=round(latency_ms, 2),
        ).info(f"Graph executed successfully, responding with {model_used} model")

        return ChatResponse(response=final_message, model_used=model_used)

    except Exception as e:
        logger.error(f"Error processing chat request: {e!s}")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
