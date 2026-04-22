"""
Pydantic schemas for Agent Tools.

These models define the input contracts for the deterministic tools
used by the agentic workflow, ensuring type safety and structured validation.
"""

from pydantic import BaseModel, Field


class SearchWebInput(BaseModel):
    """Input schema for the web search tool."""
    query: str = Field(..., description="The search query to look up on the web.")


class CalculateInput(BaseModel):
    """Input schema for the math calculation tool."""
    expression: str = Field(
        ..., 
        description="A simple mathematical expression to evaluate (e.g., '12 * 45', '100 / 3'). Supported operations: +, -, *, /, **"
    )


class SummarizeDocumentInput(BaseModel):
    """Input schema for the document summarization tool."""
    text: str = Field(..., description="The large document text to chunk, retrieve from, and summarize.")
    query: str = Field(..., description="The query to search for within the document to summarize.")


class SaveMemoryInput(BaseModel):
    """Input schema for saving facts to long-term memory."""
    fact: str = Field(..., description="The user fact to save into long-term memory (e.g., 'User loves Python').")


class SearchMemoryInput(BaseModel):
    """Input schema for searching long-term memory."""
    query: str = Field(..., description="The query to search the long-term memory (e.g., 'What are the user's hobbies?').")
