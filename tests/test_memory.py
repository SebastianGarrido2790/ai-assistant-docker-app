"""
Unit tests for the long-term memory module.

Verifies the persistence and retrieval of user facts from the
ChromaDB-backed memory system.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.agents.memory import save_memory, search_memory


@patch("src.agents.memory.memory_collection")
def test_save_memory(mock_collection):
    """Verify that facts are correctly passed to the vector store for persistence."""
    assert save_memory("Test fact")
    mock_collection.add.assert_called_once()

    mock_collection.add.side_effect = Exception("DB error")
    assert not save_memory("Test fact")


@patch("src.agents.memory.memory_collection")
def test_search_memory(mock_collection):
    """Verify that semantic search handles empty states and returns results correctly."""
    mock_collection.count.return_value = 0
    assert search_memory("test") == []

    mock_collection.count.return_value = 1
    mock_collection.query.return_value = {"documents": [["Test result"]]}
    assert search_memory("test") == ["Test result"]

    mock_collection.query.side_effect = Exception("DB error")
    assert search_memory("test") == []
