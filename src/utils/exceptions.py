"""
Custom exception definitions for the AI Assistant.
Provides structured error context for both developers and AI agents.
"""


class ChatException(Exception):
    """Base exception for all chat-related errors."""

    pass


class ModelTimeoutError(ChatException):
    """Raised when the language model takes too long to respond."""

    pass
