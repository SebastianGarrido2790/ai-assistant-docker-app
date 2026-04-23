"""
Unit tests for custom exceptions and error formatting utilities.

Verifies correct inheritance of domain-specific exceptions and
accurate extraction of error details from Python tracebacks.
"""

import sys

from src.utils.exceptions import ChatException, ModelTimeoutError, error_message_detail


def test_custom_exceptions_inheritance():
    """Verify that domain errors successfully inherit from ChatException."""
    err1 = ChatException("Base error")
    err2 = ModelTimeoutError("Timeout")

    assert isinstance(err2, ChatException)
    assert str(err1) == "Base error"


def test_error_message_detail():
    """Verify that custom exception string formatting captures the file and python traceback precisely."""
    try:
        _ = 1 / 0
    except Exception as e:
        detail = error_message_detail(e, sys)
        assert "division by zero" in detail
        assert "test_exceptions.py" in detail
