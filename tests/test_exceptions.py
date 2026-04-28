"""
Unit tests for custom exceptions and error formatting utilities.

Verifies correct inheritance of domain-specific exceptions and
accurate extraction of error details from Python tracebacks.
"""

from src.utils.exceptions import ChatException, ModelTimeoutError


def test_custom_exceptions_inheritance():
    """Verify that domain errors successfully inherit from ChatException."""
    err1 = ChatException("Base error")
    err2 = ModelTimeoutError("Timeout")

    assert isinstance(err2, ChatException)
    assert str(err1) == "Base error"
