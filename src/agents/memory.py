"""
Long-term semantic memory module.

Leverages ChromaDB to persist user facts across multiple disconnected sessions,
forming the third layer of the 3-Layer Memory Architecture.
"""

import uuid
import chromadb
from src.constants import PROJECT_ROOT

# Initialize ChromaDB persistent client
CHROMA_DB_PATH = str(PROJECT_ROOT / "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

# Use a default collection for user memory facts
MEMORY_COLLECTION_NAME = "user_memory"
memory_collection = chroma_client.get_or_create_collection(name=MEMORY_COLLECTION_NAME)


def save_memory(fact: str) -> bool:
    """Save a user fact into the vector store."""
    try:
        memory_collection.add(
            documents=[fact],
            ids=[str(uuid.uuid4())]
        )
        return True
    except Exception as e:
        print(f"Error saving memory: {e}")
        return False


def search_memory(query: str, n_results: int = 3) -> list[str]:
    """Search for relevant facts based on a semantic query."""
    try:
        # Check if collection is empty
        if memory_collection.count() == 0:
            return []
            
        # Ensure we don't request more results than we have in the DB
        n_results = min(n_results, memory_collection.count())
        if n_results == 0:
            return []
            
        results = memory_collection.query(
            query_texts=[query],
            n_results=n_results
        )
        if results and results.get("documents") and len(results["documents"]) > 0:
            return results["documents"][0]
        return []
    except Exception as e:
        print(f"Error searching memory: {e}")
        return []
