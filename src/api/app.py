"""
FastAPI Microservice backend for the AI Assistant.

This module exposes the main REST API endpoints (/v1/chat, /v1/health).
It proxies requests directly to the LangGraph execution engine, serving
as the deterministic outer shell surrounding the probabilistic AI.

Usage:
    uv run uvicorn src.api.app:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.entity.schema import ChatRequest, ChatResponse, HealthResponse
from src.agents.graph import agent_graph
from src.utils.logger import get_logger
from langchain_core.messages import HumanMessage

logger = get_logger(__name__, headline="api")

app = FastAPI(
    title="AI Assistant API",
    description="API for the Agentic AI Assistant",
    version="1.0.0",
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
    return HealthResponse(status="ok")


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
        result = agent_graph.invoke({"messages": [user_message]}, config=config)

        final_message = result["messages"][-1].content
        model_used = "cloud" if request.use_cloud else "local"

        logger.info(f"Graph executed successfully, responding with {model_used} model")
        return ChatResponse(response=final_message, model_used=model_used)

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
