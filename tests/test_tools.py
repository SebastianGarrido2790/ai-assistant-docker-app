"""
Unit tests for the agentic tools.

Verifies the deterministic behavior of the mathematical, web search,
and memory-related tools used by the AI assistant.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.tools.tools import (
    calculate_tool,
    save_memory_tool,
    search_memory_tool,
    search_web_tool,
    summarize_document_tool,
)


def test_calculate_tool():
    """Verify that the calculate tool accurately evaluates math expressions."""
    # LangChain tool.invoke returns the tool output
    assert calculate_tool.invoke({"expression": "2 + 2"}) == "4"
    assert "Error" in calculate_tool.invoke({"expression": "1 / 0"})


def test_summarize_document_tool():
    """Verify that the summarization tool extracts relevant chunks from text."""
    text = "The quick brown fox jumps over the lazy dog."
    query = "fox"
    result = summarize_document_tool.invoke({"text": text, "query": query})
    assert "quick brown fox" in result

    assert (
        summarize_document_tool.invoke({"text": "", "query": "fox"})
        == "No text provided to summarize."
    )


@patch("src.tools.tools.DDGS")
def test_search_web_tool(mock_ddgs):
    """Verify that the web search tool correctly parses DuckDuckGo results."""
    mock_instance = MagicMock()
    mock_ddgs.return_value = mock_instance

    mock_instance.text.return_value = [{"href": "http://test", "body": "test result"}]
    result = search_web_tool.invoke({"query": "test"})
    assert "Source: http://test" in result

    mock_instance.text.return_value = []
    assert search_web_tool.invoke({"query": "empty"}) == "No results found."


@patch("src.tools.tools.save_memory")
def test_save_memory_tool(mock_save_memory):
    """Verify that the save memory tool reports success/failure correctly."""
    mock_save_memory.return_value = True
    assert "Successfully saved" in save_memory_tool.invoke({"fact": "test fact"})

    mock_save_memory.return_value = False
    assert "Failed to save" in save_memory_tool.invoke({"fact": "test fact"})


@patch("src.tools.tools.search_memory")
def test_search_memory_tool(mock_search_memory):
    """Verify that the search memory tool returns results or a fallback message."""
    mock_search_memory.return_value = "Test memory"
    assert "Test memory" in search_memory_tool.invoke({"query": "test"})

    mock_search_memory.return_value = []
    assert "No relevant facts" in search_memory_tool.invoke({"query": "test"})
