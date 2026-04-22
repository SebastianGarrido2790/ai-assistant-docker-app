"""
Tools for the agentic workflow.

These tools demonstrate the separation of concerns between the LLM (brain)
and deterministic execution (brawn).
"""

import math

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


@tool("search_web_tool", args_schema=SearchWebInput)
def search_web_tool(query: str) -> str:
    """
    Search the web for real-world context using DuckDuckGo.

    Args:
        query: The search query.

    Returns:
        A string containing the concatenated search results.
    """
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        return "\n".join(
            [
                f"Source: {res.get('href')}\nSnippet: {res.get('body')}"
                for res in results
            ]
        )
    except Exception as e:
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
    # Restrict evaluation to basic math operations for safety
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names["abs"] = abs
    allowed_names["round"] = round
    try:
        # Use eval safely by restricting the scope
        result = eval(expression, {"__builtins__": {}}, allowed_names)
        return str(result)
    except Exception as e:
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

        return f"Most relevant excerpt based on query: '{best_chunk}'"
    except Exception as e:
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
    success = save_memory(fact)
    if success:
        return f"Successfully saved fact to long-term memory: '{fact}'"
    return "Failed to save fact to long-term memory."


@tool("search_memory_tool", args_schema=SearchMemoryInput)
def search_memory_tool(query: str) -> str:
    """
    Search the long-term semantic memory (ChromaDB) for user facts.
    
    Args:
        query: The search query.
        
    Returns:
        A string containing relevant facts, or a message if none are found.
    """
    facts = search_memory(query)
    if not facts:
        return "No relevant facts found in long-term memory."
    return f"Retrieved from long-term memory:\n{facts}"
