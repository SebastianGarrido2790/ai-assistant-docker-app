"""
Long-term semantic memory module.

Leverages ChromaDB to persist user facts across multiple disconnected sessions,
forming the third layer of the 3-Layer Memory Architecture.
"""

import uuid

import chromadb

from src.constants import PROJECT_ROOT

# This ensures that every time the agent even thinks about memory, we see it in the logs
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize ChromaDB persistent client
CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Use a default collection for user memory facts
MEMORY_COLLECTION_NAME = "user_memory"
memory_collection = chroma_client.get_or_create_collection(name=MEMORY_COLLECTION_NAME)


def save_memory(fact: str) -> bool:
    """Save a user fact into the vector store."""
    try:
        logger.info(f"Saving fact to long-term memory: {fact}")
        memory_collection.add(documents=[fact], ids=[str(uuid.uuid4())])
        logger.info("Fact saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving memory to ChromaDB: {e}")
        return False


def search_memory(query: str, n_results: int = 3) -> list[str]:
    """Search for relevant facts based on a semantic query."""
    try:
        logger.info(f"Searching long-term memory for: {query}")
        # Check if collection is empty
        if memory_collection.count() == 0:
            return []

        # Ensure we don't request more results than we have in the DB
        n_results = min(n_results, memory_collection.count())
        if n_results == 0:
            return []

        results = memory_collection.query(query_texts=[query], n_results=n_results)
        documents = results.get("documents")
        if results and documents is not None and len(documents) > 0:
            logger.info(f"Found {len(documents[0])} relevant facts.")
            return documents[0]  # type: ignore
        logger.info("No relevant facts found.")
        return []
    except Exception as e:
        logger.error(f"Error searching memory in ChromaDB: {e}")
        return []
