"""
Tools for the agentic workflow.

These tools demonstrate the separation of concerns between the LLM (brain)
and deterministic execution (brawn).
"""

import math

import simpleeval
from duckduckgo_search import DDGS
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.agents.memory import save_memory, search_memory
from src.entity.agent_tools import (
    CalculateInput,
    SaveMemoryInput,
    SearchMemoryInput,
    SearchWebInput,
    SummarizeDocumentInput,
)
from src.utils.telemetry import tracer


@tool("search_web_tool", args_schema=SearchWebInput)
def search_web_tool(query: str) -> str:
    """
    Search the web for real-world context using DuckDuckGo.

    Args:
        query: The search query.

    Returns:
        A string containing the concatenated search results.
    """
    with tracer.start_as_current_span("search_web_tool") as span:
        span.set_attribute("tool.input", query)
        try:
            results = DDGS().text(query, max_results=3)
            if not results:
                span.set_attribute("tool.output", "No results found.")
                return "No results found."
            output = "\n".join(
                [
                    f"Source: {res.get('href')}\nSnippet: {res.get('body')}"
                    for res in results
                ]
            )
            span.set_attribute("tool.output", output)
            return output
        except Exception as e:
            span.record_exception(e)
            return f"Error performing web search: {e}"


@tool("calculate_tool", args_schema=CalculateInput)
def calculate_tool(expression: str) -> str:
    """
    Evaluate a deterministic mathematical expression.

    Args:
        expression: The mathematical expression.

    Returns:
        The evaluated result as a string.
    """
    with tracer.start_as_current_span("calculate_tool") as span:
        span.set_attribute("tool.input", expression)
        # Restrict evaluation to basic math operations for safety
        functions = {
            k: v
            for k, v in math.__dict__.items()
            if callable(v) and not k.startswith("__")
        }
        functions["abs"] = abs
        functions["round"] = round

        constants = {
            k: v
            for k, v in math.__dict__.items()
            if not callable(v) and not k.startswith("__")
        }

        try:
            # Use simple_eval for safe mathematical evaluation
            result = simpleeval.simple_eval(
                expression, functions=functions, names=constants
            )
            output = str(result)
            span.set_attribute("tool.output", output)
            return output
        except Exception as e:
            span.record_exception(e)
            return f"Error evaluating expression: {e}"


@tool("summarize_document_tool", args_schema=SummarizeDocumentInput)
def summarize_document_tool(text: str, query: str) -> str:
    """
    Demonstrate retrieval-augmented generation (RAG) by chunking a document
    and finding the most relevant chunk for a query.

    Args:
        text: The source document text.
        query: The query to search for within the document to summarize.

    Returns:
        A relevant summary extracted from the text.
    """
    with tracer.start_as_current_span("summarize_document_tool") as span:
        span.set_attribute("tool.input_query", query)
        try:
            # Chunk the document
            splitter = RecursiveCharacterTextSplitter(chunk_size=200, chunk_overlap=20)
            chunks = splitter.split_text(text)

            if not chunks:
                return "No text provided to summarize."

            # Simple string-matching/overlap heuristic for semantic search
            # In a real RAG, we would embed 'query' and 'chunks' and compute cosine similarity.
            # Here we simulate retrieval by term overlap to prove the concept without relying on heavy local embedding models.
            query_terms = set(query.lower().split())
            best_chunk = chunks[0]
            max_overlap = -1

            for chunk in chunks:
                chunk_terms = set(chunk.lower().split())
                overlap = len(query_terms.intersection(chunk_terms))
                if overlap > max_overlap:
                    max_overlap = overlap
                    best_chunk = chunk

            output = f"Most relevant excerpt based on query: '{best_chunk}'"
            span.set_attribute("tool.output", output)
            return output
        except Exception as e:
            span.record_exception(e)
            return f"Error summarizing document: {e}"


@tool("save_memory_tool", args_schema=SaveMemoryInput)
def save_memory_tool(fact: str) -> str:
    """
    Save a user fact into long-term semantic memory (ChromaDB).

    Args:
        fact: The user fact to save.

    Returns:
        A confirmation string.
    """
    with tracer.start_as_current_span("save_memory_tool") as span:
        span.set_attribute("tool.input", fact)
        success = save_memory(fact)
        if success:
            output = f"Successfully saved fact to long-term memory: '{fact}'"
        else:
            output = "Failed to save fact to long-term memory."
        span.set_attribute("tool.output", output)
        return output


@tool("search_memory_tool", args_schema=SearchMemoryInput)
def search_memory_tool(query: str) -> str:
    """
    Search the long-term semantic memory (ChromaDB) for user facts.

    Args:
        query: The search query.

    Returns:
        A string containing relevant facts, or a message if none are found.
    """
    with tracer.start_as_current_span("search_memory_tool") as span:
        span.set_attribute("tool.input", query)
        facts = search_memory(query)
        if not facts:
            output = "No relevant facts found in long-term memory."
        else:
            output = f"Retrieved from long-term memory:\n{facts}"
        span.set_attribute("tool.output", output)
        return output
