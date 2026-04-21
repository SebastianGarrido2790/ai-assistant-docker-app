"""
Pydantic schemas for data validation and request/response structures.

These models enforce structured I/O throughout the FastAPI application
and ensure the downstream LLM processing pipeline receives validated
and type-safe inputs.
"""

from pydantic import BaseModel, Field
from typing import Optional

class ChatRequest(BaseModel):
    """Schema for chat input requests."""
    prompt: str = Field(..., description="The user's prompt message.")
    use_cloud: bool = Field(False, description="Whether to use the cloud model.")
    session_id: Optional[str] = Field("default", description="Session ID for persisting memory.")

class ChatResponse(BaseModel):
    """Schema for chat output responses."""
    response: str = Field(..., description="The AI's generated response.")
    model_used: str = Field(..., description="The model tier used ('local' or 'cloud').")

class HealthResponse(BaseModel):
    """Schema for API health endpoint."""
    status: str = Field(..., description="Health status (e.g., 'ok').")
