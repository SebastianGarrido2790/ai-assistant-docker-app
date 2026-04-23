"""
Custom exception definitions for the AI Assistant.
Provides structured error context for both developers and AI agents.
"""

from types import ModuleType


def error_message_detail(error: Exception | str, error_detail: ModuleType) -> str:
    """
    Extracts the detailed error message including file name and line number.

    Args:
        error (Exception | str): The exception or error message.
        error_detail (ModuleType): The sys module to access execution info.

    Returns:
        str: A formatted error message string.
    """
    _, _, exc_tb = error_detail.exc_info()

    # Safety check to prevent crashes in edge cases where the traceback might be incomplete.
    if exc_tb is not None and exc_tb.tb_frame is not None:
        file_name = exc_tb.tb_frame.f_code.co_filename
        line_number = exc_tb.tb_lineno
    else:
        file_name = "unknown"
        line_number = 0

    error_message = f"Error occurred in python script: [{file_name}] line number: [{line_number}] error message: [{error!s}]"

    return error_message


class ChatException(Exception):
    """Base exception for all chat-related errors."""

    pass


class ModelTimeoutError(ChatException):
    """Raised when the language model takes too long to respond."""

    pass
